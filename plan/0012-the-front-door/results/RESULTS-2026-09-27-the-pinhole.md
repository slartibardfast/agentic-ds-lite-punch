# The pinhole: a held port admits the peer the line has spoken to

**Date:** 2026-09-27. **Task:** `plan/0012#stranger-arrival`, second half. **Status:**
measured, and it confirms the mechanism the front door rests on.

## What was run

The daemon on the line carries `POKE=170.9.238.141:41001`, so each slot's own
socket sends a nine-byte datagram to the vantage on every keepalive interval. The
first deployment of it passed nothing, because the router's init script was the
previous release's and knew no `--poke`; the script travels with the binary.

The poke leaving, captured on `eth1` from the slot's own socket, every two
seconds:

```
12:02:32.385358 IP 192.168.0.21.40000 > 170.9.238.141.41001: UDP, length 9
12:02:34.385341 IP 192.168.0.21.40000 > 170.9.238.141.41001: UDP, length 9
12:02:36.385281 IP 192.168.0.21.40000 > 170.9.238.141.41001: UDP, length 9
```

The vantage then listened on that port and learned the tuple the pokes arrive
from, and answered it three times:

```
poke from ('37.228.213.83', 59348) payload b'dslp-poke'
replied to ('37.228.213.83', 59348)
```

Each reply arrived at the inner tuple and was forwarded to the LAN target, with
the vantage's own address and port intact:

```
12:02:36.512916 IP 170.9.238.141.41001 > 192.168.0.21.40000: UDP, length 13
12:02:36.512955 br-lan Out IP 170.9.238.141.41001 > 192.168.21.12.40002: UDP, length 13
12:02:37.512685 IP 170.9.238.141.41001 > 192.168.0.21.40000: UDP, length 13
12:02:37.512792 br-lan Out IP 170.9.238.141.41001 > 192.168.21.12.40002: UDP, length 13
```

## What it means

The peer relationship is made by the line. Once a slot's socket has spoken to a
peer, that peer's traffic to the held port is admitted, from the exact tuple it
came from. The earlier record's negative stands beside this one: unsolicited
traffic is refused, traffic from a peer the line has spoken to is not. Together
they are the whole admission rule, and the poke is what turns a stranger into a
peer.

The published tuple is the tuple the peer sees. The vantage observed the poke
arrive from `37.228.213.83:59348`, the same address and port the daemon republishes
from STUN, so a file that names the STUN server's destination names the right
target for a poked peer as well. The guess that the carrier hands out a port per
destination is refuted.

The UDP forward keeps the peer's own address and port, which `call/0038` asserted
from the code and this run measures on the line. The splice on the TCP side does
not, which the recipe has to say beside it.

## Method lessons

A capture started with `-w` and still running has not flushed, so its file reads
as zero bytes while its buffer holds the packets. This nearly hid the result: the
first reading of a live capture reported an empty file for a run that had
recorded everything. Kill the capture before reading it, or start it with `-U`.

An absent capture file is a different thing: it means the capture never ran. On
this router that happened through `timeout` not existing.

## What this unblocks

`plan/0012#hold-tcp-slot` builds on a port that can be reached, and
`plan/0012#control-channel` carries the tuple a peer reports back, since the
daemon can learn a peer's view of the mapping only from that peer.