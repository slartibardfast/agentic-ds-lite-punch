# A device's flow onto a leased port makes the daemon move that lease

- Date: 2026-09-18
- Milestone: plan/0009; call/0027's late-collision rule (R4); the overnight
  goal's item (2)
- Component: `ds-lite-punch`, pin `0f150da`
- Ground truth: `MEMORY.md` of this date wins where this file and a plan
  document disagree

## What was driven

A lease was asked for over PCP from inside the router's `dslp-probe`
container (`192.168.21.11`, policy-routed as the consoles are), 600 s
lifetime:

```
MAP (retry): opcode 1 code 0 (SUCCESS) lifetime 600 … internal 41030 assigned 37.228.213.83:59255
{"event":"churn","detail":"slot 40001 confirmed 37.228.213.83:59255"}
```

So: slot **40001**, external tuple `37.228.213.83:59255`. The client then
went silent, and a device's flow was driven onto the leased port.

### The UDP door is closed

A datagram from `.11` bound to the leased port, to a peer that is not the
slot's own STUN server:

```
ipv4  2 udp 17 297 src=192.168.21.11 dst=192.0.2.7 sport=40001 dport=9999 packets=1 bytes=42 [UNREPLIED]
     src=192.0.2.7 dst=192.168.0.21 sport=9999 dport=1024 packets=0 bytes=0
```

The kernel refused to preserve the port: the slot's own live entry
(`src=192.168.0.21 dst=74.125.250.129 sport=40001 dport=19302 … [ASSURED]`)
holds `(192.168.0.21, 40001)` for UDP, so the device's flow was NAT'd to
**1024** instead. This reproduces the earlier measurement exactly, and it is
why the UDP route cannot produce this acceptance: while a slot's relay socket
is punching, its port is not available to be taken.

The arm then did what it is for: it claimed that flow as a tuple of its own
(`{"event":"observed-tuple","detail":"192.168.21.11:40001 -> 37.228.213.83:59218"}`),
so the device kept reachability by a different path.

### The TCP door is open

conntrack keeps its port space per protocol, so the same source port is free
for TCP even while the slot's UDP entry holds it:

```
ipv4  2 udp 17 176 src=192.168.21.11 dst=192.0.2.7 sport=40001 dport=9999 … dport=1024
ipv4  2 tcp  6 114 SYN_SENT src=192.168.21.11 dst=192.0.2.7 sport=40001 dport=9999 [UNREPLIED]
     src=192.0.2.7 dst=192.168.0.21 sport=9999 dport=40001
```

A device's TCP flow with source `.11:40001` and destination `192.0.2.7:9999` therefore landed on
`(192.168.0.21, 40001)`: **the leased port**, with a br-lan origin. That is
exactly what the collision rule reads.

## What the daemon did

`collided()` found it, `yield_port` moved the lease and rebuilt its datapath,
and the log carries the old and the new port:

```
Fri Sep 18 22:34:59 2026 ds-lite-punch[4496]: {"event":"collision-yield",
  "detail":"slot 40001 yielded to a device's flow and moved to 40003 (label 0 kept)"}
```

The move is complete and observable in four independent places, all at
22:34:59:

| where | evidence |
|---|---|
| the slot's new tuple | `{"event":"churn","detail":"slot 40003 confirmed 37.228.213.83:59241"}` |
| per-slot state | `/run/ds-lite-punch/tuple-40003` present, `tuple-40001` removed |
| the inbound accept | `dslitepunch-40003` installed, `dslitepunch-40001` gone |
| the client's lease | the client is still `HOLDING` on the same key (internal 41030), one external tuple changed |

The lease did not merely move: it came back up on the new port and confirmed
a *fresh* external tuple in the same second, which is what makes the rule a
continuity mechanism rather than a teardown.

## What it settles, and the question it raises

- The late-collision rule works end to end, driven from outside the daemon:
  a device's flow on a leased port, the daemon yields, the client's mapping
  continues on a new port, all four surfaces agree.
- **The rule is protocol-blind and the port space is not.** The trigger here
  was a device's *TCP* flow taking a *UDP* lease's port. At the router's
  conntrack that is a genuine conflict (one local port, two consumers, and
  the inbound side only accepts UDP for the lease), so yielding is the right
  answer. But the CGNAT mapping is per-protocol, so it is not the same
  collision the rule was written for (R2's "one external port, two inner
  tuples"). Worth a decision: scope the rule to the entry's protocol, or
  state that a cross-protocol port conflict is in scope too. It is recorded
  here rather than decided in code.
- The device-key pins that used to make the *UDP* case routine are gone by
  design (call/0014), and the allocator steers new slots around tuples the
  mirror shows (`collision-avoided`). So tonight's UDP case is closed by two
  independent guards, and the TCP case is the one door left open. That is
  worth knowing before treating the yield as dead code.

## A defect this run exposed: stale inbound accept rules

The daemon's accept rules for `fw4`'s input chain are deleted by *handle*,
found by parsing `nft -a list chain inet fw4 input`. Two rules from earlier
daemons are still installed with no slot to justify them:

```
1 dslitepunch-40002-tcp     (no TCP slot exists; the daemon runs without --tcp)
1 dslitepunch               (the legacy comment shape, at port 40000)
```

The move path itself revoked its rule correctly (`dslitepunch-40001` is
gone), so these predate it, and they are the same family as the `nft` CLI
segfault: the delete-by-handle path is the one that lists the chain and
parses handles, and a daemon that dies before its teardown leaves them
behind. Fix: delete the accept rule by *expression*, the way
`revoke_datapath` already does in its batch, so the rule's absence never
depends on parsing a listing.