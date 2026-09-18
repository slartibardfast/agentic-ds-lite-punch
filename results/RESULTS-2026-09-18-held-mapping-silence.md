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

1. **A named device's unreplied flow is refused.** `obs.rs`'s `should_rescue`
   ends with `if e.reply_dst != ctx.vm_nat { return false; }`, which requires
   the flow to have *seen a reply*: for an unreplied flow there is no reply
   tuple to carry the NAT address, so the gate refuses it. That contradicts
   call/0029 ("the named device is the admission") and the function's own
   comment ("for a named device our own writes are what let it care at all").
   Measured: an allowlisted client's flow to a black-hole peer was never
   claimed across 60 s with a freshly started daemon and an empty budget,
   while `.97`'s replied flows were claimed. A failing test first, then the
   gate admitted for a named source.
2. **The `nft` CLI segfaults inside libnftables at daemon start.** Kernel
   traces (`segfault at 20040 … error 4 in libnftables.so.1.1.0[643d4,…]`,
   identical code bytes every time) coincide with daemon starts, which run
   `apply_hold` (`remove_hold`, then the `ct timeout` policy batch). The read
   commands all succeed when run by hand, so the suspect is the batch form.
   No user-visible harm tonight: the policy is in force after every start
   (`"ruleset_in_force":true`). A call whose failure is not tolerated would
   fail silently instead.
3. **The shadow keepalive cannot write.** `warn: shadow keepalive
   <peer> failed: Operation not permitted (os error 1)`, repeatedly, for the
   observation arm's rescue of a device's flow. The arm's hold therefore
   rests on the *device's* own traffic, not on the daemon's writes, while the
   facade's slot holds by its own punch. The asymmetry is real and is why
   this acceptance used a lease: the facade path is the one that holds
   without its client.
4. **The collision rule would move the operator's static.** `collided()`
   includes every slot in the binding table, `Lease::Static` among them, so a
   device flow landing on a static's port would make the yield move a port
   the operator configured. call/0030 says a static mapping is the operator's
   configuration and presence never releases it; the collision rule should
   read the same way.

## Still open

- Goal item (2): a device flow onto a leased port making the daemon move the
  lease. The device-key pins are gone by design (call/0014), so a device
  cannot be *driven* onto an actively punched slot; the static pin
  (`.12 . 40002 : NAT . 40000`) is the remaining path, and it is also the
  route that would expose defect 4.
- Goal item (3): the soak. The sampler runs at one line per minute into
  `/mnt/nvme/captures/overnight/soak.log`; the before reading is
  `rss 1344–1472 kB, fds 17–18, ct 1651, holds 5` at 21:47, and the clean
  window starts at the last restart, 21:57:59. The after reading is owed.
- Goal item (4): the per-slot learned tuples analysed for one external port
  under two inner tuples. The smoking gun is in the log of 18:53
  (`3074 → 59343/59220/59211`), and the analysis is owed as a results file.
- Goal item (5): the fixes for defects 1 and 4, each behind a failing test.
- Cleanup, at the end of the run and not before: the temporary ip rule
  `from 192.168.21.97 lookup 1000 priority 25002`, `/tmp/synth*.py`,
  `/tmp/holdrun.sh`, and the harness files; the captures and the sampler stay
  while the soak runs. The other observer's capture (pid 14409) is not mine
  and is not touched.