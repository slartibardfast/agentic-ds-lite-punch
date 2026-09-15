# RESULTS-2026-09-15-ps3-facade: E6 console sign-off with the facade live

Status: closed. The E6 clause (NAT Type 2 / Open with the IGD facade
live) is attested by the operator: three consecutive MW2 games played
correctly on the mapped console while the facade ran the whole session.
The deferred note in RESULTS-2026-09-15-facade-review.md is superseded.

Redaction note: the console's LAN address and the AFTR tuples are
replaced with placeholders; the peer addresses are named only by their
ranges. Raw captures stay on the router under
/mnt/nvme/runs/2026-09-15-ps3-facade/ per the results size policy.

## Environment

- Deployed component: ds-lite-punch 34d48c1 (the review-fixed build),
  sha 3a030fd0, pid 20468, start 19:35:31. Daemon flat for the whole
  window (VmRSS ~1.1 MB), zero error or churn lines after the grant.
- The console requested and received UPnP mappings through the facade:
  requested 3074/UDP and 3658/UDP, both granted with infinite leases
  onto slots 40002 and 40001, the entry index recording
  (requested-port, console, internal-port) exactly as requested (E3).

## What was observed (trace window 19:55 onward, three games)

- The 3074 mapping was held alive and unrotated across three games: the
  AFTR tuple for slot 40001 (3658) stayed on the same port from the
  19:35:31 restart through the session; the 3074 slot confirmed its
  tuple at grant time and did not rotate afterward.
- Continuous bidirectional UDP on 3074 between the console and three
  external peers: one sustained peer carrying heartbeats and game data
  (inbound payloads up to 488 bytes), plus two additional peers that
  contacted the console inbound on the mapping and received replies.
- The inbound path is visible directly in the capture: external IPs
  sending to the console's 3074 through the AFTR line, delivered via
  the slot, on the port MW2 had requested.
- The daemon's log contained no sweep-worthy event after the grant: no
  churn, no errors, no panics through the whole multi-game window.

## Outcome

- Operator attestation: three games played perfectly with the facade
  live. The mapping was held, the peers reached the console inbound,
  and the datapath carried the session end to end. E6 is satisfied by
  the outcome attestation plus the held-alive and inbound-peer traces.

## Capture artifacts

- /mnt/nvme/runs/2026-09-15-ps3-facade/br-lan.pcap: console-side
  traffic (the console's LAN address).
- /mnt/nvme/runs/2026-09-15-ps3-facade/eth1.pcap: AFTR-side traffic
  (host filter on the AFTR public address); sizes finalized at session
  close.