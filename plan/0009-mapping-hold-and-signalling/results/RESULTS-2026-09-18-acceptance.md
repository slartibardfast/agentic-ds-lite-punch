# Results: the acceptance run on the router, and the two defects it found

Date: 2026-09-18. Component `ds-lite-punch` at `ee27c24`, deployed as
`9049ba4284b915d7fbc16c218b0cf301`. This record is the box work behind
plan/0009's `#allowlist`, `#snoop`, `#signal`, `#acceptance` and
`#udp-threshold`: what was measured, with what instrument, and what the
measurements falsified.

## The policy install, and the hook it must use

The conntrack policy is installed and read back from the live table:

```host-lint:ignore
{"event":"hold","devices":3,"ruleset_in_force":true}
{"event":"observe","cdc":"nft","max_rescues":8,"allowed":3,"hold":true}
```

The plan's own falsifier then fired. An allowlisted device's quiet flow read
**57 seconds** from `/proc/net/nf_conntrack` at t+3 s, which is the router's
default and not the policy. Isolating the statement in a throwaway table
settled it in one reading: the same `ct timeout set` at a pre-conntrack raw
priority gave 57, and one hook later (mangle priority, after the conntrack
hook has created the entry) gave **297**. The chain moved to mangle priority
and was renamed `hold`, because a name that described the old hook would have
been a lie in the table the operator reads.

The behaviour proof then read, on the same device and the same flow shape,
only the list membership differing:

| flow | device | t+3 s | t+65 s |
|------|--------|-------|--------|
| dport 9995/9996 | `192.168.21.97`, named | 296 s | **alive**, 236 s remaining |
| dport 9994 | `192.168.21.97`, one list edit later | 55 s | **gone** |

That is the task's verify line: the named device's quiet flow outlives the
default with a remaining timeout above the two-minute floor, and the same
device's flow without the entry is reaped at the default.

## The acceptance under silence

The flow under test was the workstation's, named for the run, gauged
bidirectional by its own STUN exchange so the arm would claim it. The
arm's own side is on the record:

```host-lint:ignore
{"event":"rescue","detail":"claim 192.168.21.97:54210 -> 74.125.250.129:19302 -> 54210 (cdc nft)"}
{"event":"observed-tuple","detail":"192.168.21.97:54210 -> 37.228.213.83:59296 (Churn((37.228.213.83, 59296)))"}
```

The learned tuple agreed with the client's own STUN reading, which is two
independent paths to one answer. The external vantage then sent to the
learned tuple at four windows of client silence, and the router's captures
show every one arriving on the WAN interface and being forwarded to the
client's address with the sender preserved:

| window | arrival on `eth1` | forwarded on `br-lan` |
|--------|-------------------|----------------------|
| +30 s | t0+31.4 s | yes |
| +60 s | t0+61.4 s | yes |
| +120 s | t0+121.4 s | yes |
| +300 s | t0+301.4 s | yes |

The client application did **not** receive them, and the reason is the test
client's own path rather than anything the daemon does: the workstation sits
behind a second NAT (the WSL host's), which has no mapping for a packet
arriving from a peer its own flow never spoke to, so it drops what the router
correctly delivered. The router's two hops are the ones under test and both
appear above; the end-client hop across the same datapath is proven by the
earlier milestone's slot measurement, where 4,852 inbound packets reached the
console. A client on the LAN, addressed directly, is the shape this hand-off
needs, and the run's list edit is the only reason it could not be a console.

The cost is measured too, and it is the plan's own figure: one held flow
spends about half a packet per second.

## The AFTR's threshold, measured

The same instrument, a fine ladder from the vantage, against an **unheld**
flow from the same device (the list edit removed the entry, so the arm
ignored the flow entirely):

| probe sent | arrival at the router |
|------------|----------------------|
| t0+1.34 s | yes |
| t0+1.98 s | yes |
| t0+4.29 s | yes |
| t0+9.29 s | yes |
| t0+13.29 s | yes |
| t0+21.29 s | **no** |

So the AFTR reaps an idle UDP mapping between **13 and 21 seconds** of client
silence on this line. The figure the milestone was written against was five to
ten seconds; the measured death point is later, and the difference matters in
one direction only: the two-second cadence the hold uses sits comfortably
inside it, with room for a slower one if the cost of the list ever argues for
it. An earlier reading of this same experiment said "dead by two seconds" and
was wrong: the capture behind it had never started, because the filter
expression was one busybox tcpdump refused. An instrument that has not
recorded a known event has not been shown to work, and this record's numbers
are from captures that had.

## The event surface, driven by a real control point

A subscription taken from the workstation, with the callback served by the
router itself:

- the initial event carried all four declared variables, with the count
  already scoped to the subscriber: `PortMappingNumberOfEntries` was 0 while
  the table held the consoles' mappings;
- a mapping created for the subscriber's own address moved the count to 1 and
  `SystemUpdateID` to 1, and the event carried **only those two** variables;
- the deletion reported the same two variables at their new values, with
  `SEQ` advancing to 2.

The contained subscriber's count is the task's own check: what it saw was its
own namespace alone. The mapping that produced the change was
made over PCP and was answered with a drop, because its discovery was still
in flight; the subscriber was told the table moved even though the client was
told nothing yet, which is the two views doing their separate jobs.

## The console run, which closes the client hop

The workstation's second NAT was the only reason the client-application hop
was unproven, so the acceptance was run again against a real device: the arm
was holding four of a console's flows (shadows bound on `65400`-`65403`, the
tuples `59251` and `59220` learned beside them), and the external vantage
probed those tuples after several minutes of the console's own silence. Both
arrived, and the router's connection table shows where they went:

```host-lint:ignore
170.9.238.141.39897 > 192.168.0.21.65401: UDP, length 9
192.168.0.21 > 170.9.238.141: ICMP 192.168.0.21 udp port 65401 unreachable
```

The probe reached the console. Two captures on opposite sides of the router
say so, and together they are the receipt rather than a reading of the
translation:

```host-lint:ignore
# br-lan, the LAN side
03:41:39.580260 IP 170.9.238.141.39897 > 192.168.21.138.65401: UDP, length 9
03:41:39.580449 IP 192.168.21.138 > 170.9.238.141: ICMP 192.168.21.138 udp port 65401 unreachable, length 36
```

The forward went to the device's address with the sender preserved, and the
ICMP's LAN-side source is the console itself, which the NAT rewrote to
`192.168.0.21` by the time the WAN capture saw it. ICMP has no ports of its
own: the `65401` above is tcpdump reading the quoted datagram inside the
error, which is how the message names the flow it is about, and it is also
what the router matched to translate the error back to the prober. So the port-unreachable is
the console's own stack answering a flow whose socket had closed: a
listener-less port is exactly what answers that way, and the router would
have had no reason to answer at all once the datagram had been translated to
another address. Nothing else in the path could have generated it, and the
milestone's client hop is closed with a real client.

That run also answered a question this milestone had left to measurement: a
shared tuple resolves in the incumbent's favour. `call/0028` records it,
together with the other measurement, that the NAPT will translate a flow into
a port a local socket already holds.

## What this run leaves open

- The last hop to a client application behind a second NAT. Nothing in the
  daemon depends on it, and the fix is a client on the LAN.
- Whether any device here needs the hold in the field. The list stands at the
  two consoles (call/0025's bootstrap pair) after the run's workstation entry
  was removed.
- The AFTR's threshold is measured as a window rather than a figure, and its
  stability over days is not measured at all.