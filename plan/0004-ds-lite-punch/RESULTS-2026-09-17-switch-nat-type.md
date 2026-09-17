# RESULTS-2026-09-17-switch-nat-type: NAT type A on the Virgin Media line, and what earned it

Status: the milestone's open question on the Switch's NAT type is answered
from a live session, with the mechanism visible in packet captures.

## The question

The Open questions section carried this as the "big if": is the Switch's
workload satisfied by EIM+EIF, or does it truly need source-port
preservation? It cannot be settled from sources, so it was left to a
measurement on the hardware, with the Virgin Media line and the vdsl4 line
as the two arms.

## What was measured

- The console: a Nintendo Switch behind a USB Ethernet adapter
  (`80:d2:e5:6d:d1:00`, 192.168.21.68), IPv4 only. It holds no IPv6
  address and sent no IPv6 packets in the captures, so the console's IPv6
  behaviour is not part of this result.
- The line: the Virgin Media ds-lite path (`vm4`, dhcp on eth1, through the
  hub to the AFTR). The console was routed there by a source rule, and the
  Digiweb pppoe line (`vdsl4`, 84.203.115.61) carried none of its traffic.
- The verdict the console itself reported: **NAT type A**.

## The check, on the wire

At 21:46:57 on the VM side, the mapping queries and the filtering probe
that follows them are both on tape:

```text
21:46:57.2559  192.168.0.21.57216 > 3.74.50.213.33334    UDP, 16 bytes
21:46:57.2567  192.168.0.21.57216 > 3.74.50.213.10025    UDP, 16 bytes
21:46:57.2963  3.74.50.213.50920  > 192.168.21.68.57216  UDP, 16 bytes, five packets
```

The console never sent to port 50920 on that host, so the five inbound
packets are the filtering test, answered 40 milliseconds after the mapping
queries on the same mapping. Nothing of the sequence appears on the Digiweb
side.

## Why the A is earned

- **Mapping**, from the session rather than the probe: one local port,
  57216, served eight peers, and the per-peer volumes are symmetric.
  16,501 packets out against 16,554 in with one peer, 13,517 against
  13,081 with the next, 10,245 against 9,931 with a third. Mapping that
  ignores address and port is the behaviour on the wire.
- **Filtering**, from the probe above: inbound from a port the console had
  not written to was accepted and delivered to it.
- **What this does not establish.** The probe came from the same address as
  the mapping queries, on a different port, so it shows port-independent
  filtering toward an address the console had just contacted. Full
  address-independent filtering is what the relay's own STUN ground truth
  established, and this probe adds nothing to that. The strict form, an
  unrelated address sending first, is carried: the external vantage can be
  pointed at a mapping this project controls.

## The control arm

The Digiweb line carried none of the console's probe or peer traffic, so
the A belongs to the AFTR path rather than to the alternative uplink being
measured by accident.

## What the session did not reach

The window was one evening: about nineteen minutes of console UDP, with
four peers carrying the bulk of it, and a comparable run from the PS3
alongside. Every game peer seen in that window was contacted by the console
before it replied, so no peer established the first contact here; the only
unsolicited inbound in the capture is the console's own probe. Whether a
peer ever does send first, and how a wider peer set behaves, needs longer
runs than this session, and the peer census itself is one evening's
matchmaking rather than a stable set.

## Evidence

Raw captures live at `/mnt/nvme/captures` on the router, with a `MD5SUMS`
manifest alongside, mirrored on the workstation under
`~/captures-2026-09-17-final`. The interfaces captured were br-lan, eth1
(the VM side), `pppoe-vdsl4` (the Digiweb side) and the raw eth2 device.

One caveat on the timebase: the router's clock was corrected backwards by
about 38 minutes during the session, so packet timestamps written before
the correction read ahead of the wall clock that followed. Ordering and
intervals inside a capture are unaffected; the absolute times quoted here
are on the pre-correction clock.