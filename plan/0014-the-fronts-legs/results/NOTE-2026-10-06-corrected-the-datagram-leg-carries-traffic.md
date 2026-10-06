# Corrected: the datagram leg carries traffic, and the reply path is what is missing

Date: 2026-10-06. Corrects `results/NOTE-2026-10-06-the-datagram-leg-at-the-front.md`, whose verdict
was wrong.

## What was wrong

That note read "the edge will not carry it" from a capture grepped for the slot's **external** port.
The carrier un-NATs an arrival before it reaches the wire, so the packet carries the slot's **inner**
port, and the grep counted zero while the traffic was there. Two arrivals that the note called absent
were in the same file:

```
13:22:10.544774 IP 170.9.238.141.8445 > 192.168.0.21.40000: UDP, length 17   the unmatched arrival
13:22:30.985713 IP 170.9.238.141.8443 > 192.168.0.21.40000: UDP, length 16   the relayed client datagram
```

The second test's silence had a second cause: its target is the sink, which absorbs and does not
answer, so a client waiting for a reply timed out on a path that had worked.

## What is measured now

The vantage's provider preserves the source port: the front's own replies arrive at the line from
`170.9.238.141:8443`, one for each poke:

```
14:21:21.647968 IP 170.9.238.141.8443 > 192.168.0.21.40000: UDP, length 9
```

The carrier's admission does not ask for the arrival's source port to match the poke's destination:
the arrival from `8445`, which was never poked, crossed as well. Address alone is the test, so one
front's socket can carry several clients.

And the whole chain works. A datagram sent from this machine to the front's public port reached a
service behind the line and drew an answer:

```
14:26:57.516271 eth1  Out IP 192.168.0.21.40000 > 170.9.238.141.8443: UDP, length 9       the line's poke
14:26:57.645271 eth1  In  IP 170.9.238.141.8443 > 192.168.0.21.40000: UDP, length 9       the front's datagram
14:26:57.645370 br-lan Out IP 170.9.238.141.8443 > 192.168.21.12.40002: UDP, length 9     the daemon's forward
14:26:57.645441 veth  P   IP 192.168.21.12.40002 > 170.9.238.141.8443: UDP, length 31     the service's answer
```

The answer is 31 bytes: the service's own 21, which means it replied to the message it was given.

## What is actually missing

The service's answer leaves from the service's own address (`192.168.21.12:40002`) and goes out the
line that way, which is not the mapping's tuple. The carrier's outbound side does not carry it, and
the front's relay would not accept it either. The daemon's relay preserves the peer's address when it
forwards an arrival, which is the property the consoles depend on, and it does not fold the service's
reply back into the slot.

That is the next fix, and it is the daemon's: the slot that carries a front door's datagrams needs its
service's replies folded into the mapping's socket, the way a granted slot folds its client's egress.