# A held mapping answers the outside across its client's silence

- Date: 2026-09-18
- Milestone: plan/0009 (the mapping hold, its admission, the signalling, the
  shared port), the overnight goal's item (1)
- Component: `ds-lite-punch`, pin `68c2e2d`, deployed binary `ce6cc566`
- Ground truth: `MEMORY.md` entries of this date win where this file and a
  plan document disagree

## What was measured

Two mappings were asked for over PCP by a client inside the router's own
`dslp-probe` container (`192.168.21.11`), one at a time, with a 600 s
lifetime. The client then went completely silent: no datagram left it after
the MAP request, and nothing on the LAN sent on its behalf. An external
vantage (`170.9.238.141`) probed each mapping's learned external tuple at
four windows of that silence.

The schedule was armed from the silence's own epoch, with the delay to each
window computed from the silence already elapsed, so a probe landed *at* its
window rather than a fixed number of seconds after a schedule that started
late. Every probe sent was received at the router's WAN and forwarded to the
silent client. Nothing was lost at any window.

| # | slot | external tuple | client | window | silence at arrival | router WAN capture |
|---|---|---|---|---|---|---|
| 1 | 40001 | 37.228.213.83:59281 | 192.168.21.11:41010 | 30 s | **29.96 s** | `1789768953.039977 IP 170.9.238.141.58167 > 192.168.0.21.40001: UDP, length 10` |
| 1 | 40001 | 37.228.213.83:59281 | 192.168.21.11:41010 | 60 s | **59.97 s** | `1789768983.028587 IP 170.9.238.141.58167 > 192.168.0.21.40001: UDP, length 10` |
| 1 | 40001 | 37.228.213.83:59281 | 192.168.21.11:41010 | 120 s | **119.97 s** | `1789769043.028623 IP 170.9.238.141.58167 > 192.168.0.21.40001: UDP, length 11` |
| 1 | 40001 | 37.228.213.83:59281 | 192.168.21.11:41010 | 300 s | **299.97 s** | `1789769223.038820 IP 170.9.238.141.58167 > 192.168.0.21.40001: UDP, length 11` |
| 2 | 40002 | 37.228.213.83:59284 | 192.168.21.11:41020 | 30 s | **29.35 s** | `1789769002.352120 IP 170.9.238.141.37018 > 192.168.0.21.40002: UDP, length 10` |
| 2 | 40002 | 37.228.213.83:59284 | 192.168.21.11:41020 | 60 s | **59.34 s** | `1789769032.342153 IP 170.9.238.141.37018 > 192.168.0.21.40002: UDP, length 10` |
| 2 | 40002 | 37.228.213.83:59284 | 192.168.21.11:41020 | 120 s | **119.34 s** | `1789769092.344192 IP 170.9.238.141.37018 > 192.168.0.21.40002: UDP, length 11` |
| 2 | 40002 | 37.228.213.83:59284 | 192.168.21.11:41020 | 300 s | **299.34 s** | `1789769272.336206 IP 170.9.238.141.37018 > 192.168.0.21.40002: UDP, length 11` |

Each arrival was also forwarded to the client, read from the LAN capture:

```
1789768953.040059 IP 170.9.238.141.58167 > 192.168.21.11.41010: UDP, length 10
1789769002.352187 IP 170.9.238.141.37018 > 192.168.21.11.41020: UDP, length 10
1789769032.342259 IP 170.9.238.141.37018 > 192.168.21.11.41020: UDP, length 10
1789769092.344315 IP 170.9.238.141.37018 > 192.168.21.11.41020: UDP, length 11
1789769272.336262 IP 170.9.238.141.37018 > 192.168.21.11.41020: UDP, length 11
```

The daemon confirmed both slots when the leases were granted:

```
{"event":"churn","detail":"slot 40001 confirmed 37.228.213.83:59281"}
{"event":"churn","detail":"slot 40002 confirmed 37.228.213.83:59284"}
```

## Method, and the reading of the capture

- The client is the container, not the workstation. A container's flow is
  *forwarded* through the router, so the observation arm's `flow_obs` mirror
  sees it, and it has its own per-host admission budget that nothing else
  spends. The workstation's budget is spent by its own browser before any
  synthetic flow can be admitted.
- The probe tool was given `--lifetime`, because the granted lifetime is the
  ceiling the windows must fit in, and 600 s is asked for here so that the
  300 s window tests the hold rather than the lease. It was given `--hold`,
  which keeps the mapping and the socket and dissolves the socket's
  association so that probes from an unrelated address are delivered.
- **On eth1 the arrival's destination port is the router's own slot port**
  (`40001`/`40002`), not the CGNAT tuple the vantage sent to: the AFTR
  translates the destination back before the packet reaches this router. The
  capture's filter is by source host, and the destination port in it is the
  slot's. A capture read by the CGNAT port finds nothing, which cost a
  confusing round.

## What this settles

The AFTR's idle reaping, measured earlier at 13 s to 21 s, does not claim a
mapping the daemon holds. The daemon's own relay punch for the slot is more
frequent than the AFTR's reaping threshold, so the CGNAT mapping stays alive
across a client's total silence, and the inbound path stays open for at least
five minutes. This is the property the product exists for: a console in a
lobby, a paused game and a sleeping screen present as silence, and the
mapping must outlast all of them.

## Defects this run exposed

1. ~~**A named device's unreplied flow is refused.**~~ **RETRACTED the same
   evening; it was not the gate.** A policy route is what the mirror
   requires. The synthetic client inside the container went without one, so
   its packets left by `pppoe-vdsl4` (84.203.115.61), and the arm's mirror
   watches `oifname eth1`. With one `ip rule` added for the client's
   address, the same unreplied flow was claimed at once
   (`claim 192.168.21.11:47077 -> 192.0.2.1:45678 -> 47077 (cdc nft)`), and
   the gate passed because eth1's fullcone masquerade sets the NAT source to
   192.168.0.21 even with no reply. The predicate is correct as written.
2. **The `nft` CLI segfaults inside libnftables at daemon start.** Kernel
   traces (`segfault at 20040 … error 4 in libnftables.so.1.1.0[643d4,…]`,
   identical code bytes every time) coincide with daemon starts, which run
   `apply_hold` (`remove_hold`, then the `ct timeout` policy batch). The read
   commands all succeed when run by hand, so the suspect is the batch form.
   No user-visible harm tonight: the policy is in force after every start
   (`"ruleset_in_force":true`). Were such a failure on a call the daemon
   requires, it would be silent.
3. ~~**The shadow keepalive cannot write.**~~ **RETRACTED; the hold works.**
   The `warn: shadow keepalive … failed: Operation not permitted` lines all
   belong to earlier daemon pids (3026, 31093, 32114); the last is at
   21:57:53, and the daemon started at 21:57:59 has logged **none**, with no
   warnings of any kind. Two candidate mechanisms were tested and excluded by
   hand on the box: a socket bound to (192.168.0.21, port) sends to the STUN
   servers fine with and without a `snat_map` element pinning that tuple to
   itself. And the hold is *demonstrably* the daemon's own writes, measured in
   "The hold is the daemon's own writes" below.
4. **The collision rule would move the operator's static.** `collided()`
   includes every slot in the binding table, `Lease::Static` among them, so a
   device flow landing on a static's port would make the yield move a port
   the operator configured. call/0030 says a static mapping is the operator's
   configuration and presence never releases it; the collision rule should
   read the same way.

## The hold proper, proven the same way (the second run)

The acceptance above used a facade lease. The daemon's *hold* itself (the
observation arm claiming a named device's own flow) was then run the same
way, once the client's policy route was corrected: one datagram from
`192.168.21.11:47077`, after which the client was silent.

```
{"event":"rescue","detail":"claim 192.168.21.11:47077 -> 192.0.2.1:45678 -> 47077 (cdc nft)"}
{"event":"observed-tuple","detail":"192.168.21.11:47077 -> 37.228.213.83:59251 (Churn((37.228.213.83, 59251)))"}
```

| window | probe sent | arrived on eth1 (router's WAN capture) | client socket |
|---|---|---|---|
| 30 s | `1789770277.415` | `1789770277.491663 IP 170.9.238.141.57800 > 192.168.0.21.47077: UDP, length 10` | `RX 1 … at 1789770277.492` |
| 60 s | `1789770307.403` | `1789770307.479707 IP 170.9.238.141.57800 > 192.168.0.21.47077: UDP, length 10` | `RX 2 … at 1789770307.480` |
| 120 s | `1789770367.419` | `1789770367.496559 IP 170.9.238.141.57800 > 192.168.0.21.47077: UDP, length 11` | `RX 3 … at 1789770367.497` |
| 300 s | `1789770547.401` | `1789770547.481522 IP 170.9.238.141.57800 > 192.168.0.21.47077: UDP, length 11` | `RX 4 … at 1789770547.482` |

Every arrival reached the client's own socket, which is the strongest form of
the evidence: not only did the mapping answer at the router's WAN, the
datagram was delivered to a client that had sent nothing for five minutes.

## The hold is the daemon's own writes

The client was silent from 22:24:07. Its conntrack entry, read eight seconds
apart:

```
src=192.168.0.21 dst=74.125.250.129 sport=47077 dport=19302 packets=252 bytes=12096
src=74.125.250.129 dst=192.168.0.21 sport=19302 dport=47077 packets=252 bytes=15120 [ASSURED]
src=192.168.0.21 dst=74.125.250.129 sport=47077 dport=19302 packets=256 bytes=12288
src=74.125.250.129 dst=192.168.0.21 sport=19302 dport=47077 packets=256 bytes=15360 [ASSURED]
```

Four packets in eight seconds, both directions, all of them the shadow
keepalive to the STUN server and its replies. Nothing else could have
produced them: the client's socket has sent one datagram and no more. This is
the mechanism that lets an AFTR mapping outlive its client's silence. The
earlier measurement of 13 to 21 seconds of idle reaping describes a mapping
nobody writes for, and the two facts are consistent: without the daemon's
writes it dies in seconds, with them it lives past five minutes.

The cost, which an operator should know: the interval is two seconds, so a
silent console costs one small STUN exchange every two seconds for as long as
the daemon holds its tuple.

## Still open

- Goal item (2): **done, driven live**, in
  `results/RESULTS-2026-09-18-collision-yield.md`. The UDP door is closed by
  the slot's own conntrack entry (the kernel NATs a device's UDP flow to 1024)
  and by the allocator steering around live tuples; the TCP door was the one
  open, and through it the lease moved, 40001 becoming 40003, with the client
  still holding.
- Goal item (3): the soak. The sampler runs at one line per minute into
  `/mnt/nvme/captures/overnight/soak.log`; the clean window starts at the last
  restart, 21:57:59 (`1789768700 rss=1136 fds=13 ct=881 holds=1`). The after
  reading is owed in the morning; the last value tonight is
  `1789770921 rss=1332 fds=18 ct=504 holds=4`.
- Goal item (4): **done**, in `results/RESULTS-2026-09-18-tuple-analysis.md`,
  with `deploy/tuple-analysis.py`. No external tuple was in two inner tuples'
  hands at once; the mirror case (one inner, several externals, concurrent)
  was found and it is the split call/0014 fixed.
- Goal item (5): defect 4 is fixed with a failing test first
  (`a_static_is_the_operators_and_is_never_the_slot_that_moves`) and the pin
  bumped. Defects 1 and 3 are retracted above. Defect 2 (the `nft` segfault)
  and the stale accept rules are open, and they are the same family: the
  delete-by-handle path.
- Cleanup, at the end of the run and not before: the temporary ip rules
  `from 192.168.21.97 lookup 1000 priority 25002` and
  `from 192.168.21.11 lookup 1000 priority 25003`, `/tmp/synth*.py`,
  `/tmp/holdrun.sh`, and the harness files; the captures and the sampler stay
  while the soak runs. The other observer's capture (pid 14409) is not mine
  and is not touched. The two stale accept rules should be removed by hand
  once the fix lands.