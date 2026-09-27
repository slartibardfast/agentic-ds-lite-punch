# The TCP fault is the client's return path, not the box's input path

**Date:** 2026-09-27. **Task:** `plan/0012#hold-tcp-slot`. **Status:** the
external SYN is delivered; the handshake fails because the reply leaves by the
wrong line. This record also corrects the previous one.

## The input path is clean

The suspects carried from the datapath work of 2026-09-13 are refuted on this box:

```
all rp_filter=0   eth1 rp_filter=0   br-lan rp_filter=0   eth0 rp_filter=0
170.9.238.141 from 192.168.0.21 via 192.168.0.1 dev eth1 table 1001
LISTEN 0      128      0.0.0.0:40001      0.0.0.0:*
25100:  from 192.168.0.21 lookup 1001
```

Reverse-path filtering is off everywhere, the listener is bound, the reply route
for the slot's own address leaves by `eth1` through the table the daemon
maintains, and that table has a rule selecting it.

## What the previous record got wrong

It concluded that the box fails to answer a forwarded SYN. The measurement behind
that conclusion was a connection whose reply was never seen, and the reason is
now visible: the reply would have come from the *client* host, and the client
host's traffic has no DS-Lite egress rule.

```
25000:  from 192.168.21.68 lookup 1000     (a console)
25001:  from 192.168.21.138 lookup 1000    (a console)
25100:  from 192.168.0.21 lookup 1001      (the daemon's own address)
```

The address that answered for this test, `192.168.21.97`, appears in none of
them. Its reply therefore took the default route, which is the other WAN, and left
with that line's public address. The vantage had connected to `37.228.213.83:59237`
and a reset arriving from a different address is discarded, so the connection
stayed in progress and the capture showed the SYN and nothing else.

That is also why the consoles work and this host does not: their addresses carry
the rule that sends their traffic down the line the mapping is on.

## What this means for the front door

The slot's inbound delivery is proven for TCP: the SYN reaches the inner tuple
from the peer the line poked. What the front door needs in addition is that the
*service host's* replies leave by the DS-Lite line, since the peer will have
connected to the AFTR's address and will ignore a reset from anywhere else.

Two ways to get that, and the second is more self-contained. The operator can add
an egress rule for the service host, which is what the consoles have. Or the
daemon can rewrite a granted slot's onward traffic, presenting its own bind
address, which already carries the rule, so the peer sees the daemon and the reply
takes the right line with no per-host configuration.

## Loose ends this leaves

The listener on the slot's port is bound and the granted slot also DNATs an
arrival to the client's own port, so which of the two carries a granted slot's
arrival deserves to be settled by a capture on the LAN side rather than by
reading the code.

The lease in the second test had expired, which is why that attempt was refused at
the carrier with no mapping present. A fresh lease is needed for each attempt, and
the probe's own delete step runs whenever a MAP succeeds, so a test that wants a
live slot has to watch the clock.