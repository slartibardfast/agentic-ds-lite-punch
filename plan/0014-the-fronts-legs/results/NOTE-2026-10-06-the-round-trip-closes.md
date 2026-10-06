# The round trip closes: the front door carried a datagram both ways

Date: 2026-10-06. Task: `plan/0014#the-relay` and the datagram half of `#the-first-byte`.

## What was measured

A datagram addressed to the front's public port reached a service behind the line, the service
answered its own message, and the answer returned to the client:

```
sent b'the front door, end to end'
ANSWER b'the service answered: the front door, end to end' from 170.9.238.141:8443
```

The box's capture holds every hop, and it is the shape
[call/0048](../../call/0048-a-slot-that-pokes-a-front-answers-as-the-peer.md) describes:

```
15:56:54.320486 br-lan Out IP 192.168.21.1.40445 > 192.168.21.12.40003: UDP, length 9    the relay hands it to the service
15:56:54.320565 veth   P   IP 192.168.21.12.40003 > 192.168.21.1.40445: UDP, length 31   the service answers the daemon
15:56:54.320628 eth1  Out IP 192.168.0.21.40000 > 170.9.238.141.8443: UDP, length 31     the answer leaves the slot's socket
15:56:54.421087 pppoe-vdsl4 In IP 170.9.238.141.8443 > 84.203.115.61.58592: UDP, length 31  the front relays it to the client
```

The answer's 31 bytes are the service's 21 plus the 10 the client sent, so the service replied to the
message it was given.

## What carried it

The relay the daemon runs for a slot with a poke: it answers the service from a socket of its own, so
the service's reply comes back to the daemon rather than to a peer it cannot reach, and it sends that
reply out of the slot's own socket, where the mapping lives. The pin the superseded decision asked for
is gone from the start-up path, and the transparent forward stays for every slot without a poke, which
keeps the consoles' property intact.

## What is still owed

The same run's capture shows the client's datagram arriving and the state of the box afterwards, but
the task `#the-first-byte` also asks for a TCP client, which belongs to `#the-tcp-leg`: the poke's dial
on the TCP side still fails with `Operation not permitted`, and that leg is unbuilt.