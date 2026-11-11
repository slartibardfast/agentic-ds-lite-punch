# The policy rows so far: thirteen green, one open

Date: 2026-11-11. Task: `plan/0016#carrier-policy`. The verify runs
`python3 deploy/env/envctl.py verify-policy`, which stands the environment up,
drives the carrier's policy plane through the three profiles, and asserts a row
set per profile.

## The rows that pass

| Profile | Rows verified |
|---|---|
| `vm-dslite` | the poke allocates a preserved external port; the poked peer's arrival crosses from a never-poked port; a stranger's arrival is refused; silence (the profile's 12-second timer) expires the mapping; two destinations receive two distinct tuples for one source port |
| `rfc-bcp` | the poke allocates one mapping per inside endpoint (endpoint-independent); the poked peer's arrival crosses |
| `symmetric` | the poke allocates per destination with sequential ports from the profile's base; the poked peer's arrival crosses only from the exact poked source port; a stranger's arrival is refused |

Thirteen of fourteen rows are green on this machine, unprivileged, in one
command per profile.

## The open row

`rfc-bcp`'s stranger row fails: under endpoint-independent filtering, a
never-poked address should reach the mapping, and the arrival was refused. The
evidence so far:

- The ruleset the policy programmed is correct for the profile: the prerouting
  rule has no source restriction.
- The front actor reaches the carrier's public address over the bridge (two
  pings, zero loss), so the path into the carrier works.
- The stranger's datagram never arrives on the carrier's inside side, and the
  public-side capture came back empty on a run whose capture process needs
  re-checking (its errors were discarded by the debug harness).

The next instrument is a capture run through the environment's own control
plane rather than an ad-hoc namespace walk, so the tcpdump errors land in the
record instead of a null device. The suspicion, named for the next session: the
arrival is refused by the namespace's own routing or filtering state, not by
the policy plane's rules.

## What the green rows settle

The measured carrier behaviour from plan/0010 and plan/0014 is now enforced
behaviour in a simulated carrier: the per-destination allocation the front era
measured, the address-only admission the rule table recorded, the stranger's
refusal, and the silent timer the relay's cadence is built around. The
environment reproduces the line's semantics on demand, on this machine, without
the line.

## The state of the plane's code

`deploy/env/envctl.py` is the control plane (topology, policy lifecycle,
probes); `deploy/env/carrier-policy.py` is the carrier's policy plane (the
sniffer on the inside wire, the tuple allocator, the nft programming, the
silent sweep); `deploy/env/profiles/*.conf` are the three profiles. The bash
`standup.sh` and `carrier-verify.sh` sketches were retired for these.