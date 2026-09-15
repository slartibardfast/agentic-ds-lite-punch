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
  window (VmRSS ~1.1 MB).
- The console requested and received UPnP mappings through the facade:
  requested 3074/UDP and 3658/UDP, both granted with infinite leases
  onto slots 40002 and 40001, the entry index recording
  (requested-port, console, internal-port) exactly as requested (E3).

## What was observed (trace window 19:55 onward, three games)

- The 3074 mapping was held alive and unrotated across three games: the
  AFTR tuple for slot 40001 (3658) stayed on the same port from the
  19:35:31 restart through the session; the 3074 slot confirmed its
  tuple at grant time and did not rotate afterward.
- Continuous bidirectional UDP on 3074 between the console and several
  external peers: one sustained peer carrying heartbeats and game data
  (inbound payloads up to 752 bytes), plus additional peers that
  contacted the console inbound on the mapping and received replies.
- The inbound path is visible directly in the capture: external IPs
  sending to the console's 3074 through the AFTR line, delivered via
  the slot, on the port MW2 had requested.

## Daemon log during the session (all lines attributable)

- Post-deploy (19:35:31 onward) the daemon.err lines are: one
  `restore slot 40002 bind failed: Address in use` at startup (the C1
  degradation path logging a slot whose socket the overlapping old
  process still held during the procd restart; only the stale
  probe-sink grant was affected, and the console's 3074 later took
  that slot), the pin-conflict and element-delete noise from the
  battery runs over the leftover 14572 pin (19:36-19:37), and a
  routine GENA prune (19:43:31).
- In the game window itself (19:44:35 through session end): zero
  daemon.err and zero churn lines. The operator attestation of a
  clean session is fully corroborated by the log.

## Outcome

- Operator attestation: the session (three games, extended into a
  fourth) played perfectly with the facade live, "not a blip". The
  mapping was held, peers reached the console inbound, and the
  datapath carried the session end to end. E6 is satisfied by the
  outcome attestation plus the held-alive and inbound-peer traces.

## Capture artifacts

- /mnt/nvme/runs/2026-09-15-ps3-facade/br-lan.pcap: the complete
  record, 33,820 packets / 5.3 MB over the console's address. It
  carried the whole session: peers inbound on 3074, the console's
  flows, the game-data payloads.
- /mnt/nvme/runs/2026-09-15-ps3-facade/eth1.pcap: empty. The capture
  named the wrong interface: the live digest shows the AFTR-path
  traffic on eth0 on this box, so the eth1-named file never populated.
  The br-lan capture is the authoritative artifact; the eth1 file is
  retained as a 24-byte header.