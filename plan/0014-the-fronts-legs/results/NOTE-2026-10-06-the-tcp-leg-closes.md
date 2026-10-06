# The TCP leg closes: the front door carried a TLS client to the service behind the line

Date: 2026-10-06. Task: `plan/0014#the-tcp-leg` and the TCP half of `#the-first-byte`.

## What was measured

Three TLS clients, each dialling the front's public port with the pass-through name, brought the
service's own certificate back through the front door:

```
subject=CN = the-service-behind-the-line
issuer=CN = the-service-behind-the-line
```

The front's log names each hop: an arrival on the public port, a proxy connection to the carrier
tuple, and a disconnect with bytes carried each way.

```
19:07:39 [info] client 170.9.238.141:39974 connected to 0.0.0.0:8443
19:07:39 [info] proxy 10.0.0.52:55806 connected to 37.228.213.83:59315
19:07:40 [info] client disconnected, bytes from/to client:127/1395, bytes from/to upstream:1395/441
```

## Where the chain stopped

The arrival crossed the carrier, and the box reset it. A capture on the box showed every SYN the
front dialled arriving on `eth1` for the slot's inner port, with the box answering each one:

```
eth1  In  IP 170.9.238.141.50140 > 192.168.0.21.40001: Flags [S]
eth1  Out IP 192.168.0.21.40001 > 170.9.238.141.50140: Flags [R.]
```

The reset came from `fw4`. The daemon accepts a slot's port on `eth1` by adding the port to a set
that one accept rule reads, and that rule stood behind `jump input_wan`, whose zone policy resets an
arrival it meets. A rule the chain reaches after the zone jump decides nothing, and a rule appended
at the chain's foot decides nothing either.

The first attempt at this measured the wrong thing twice, and both readings are worth keeping. A
capture grepped for the slot's external port while the carrier rewrites the destination to the inner
port before the wire, so the count read zero and the carrier looked guilty. The TLS client then
looked fine on a path that worked, because the target answers nothing and a silent service reads as
a broken path from the client alone.

## What the fix is

The daemon places each accept rule ahead of the first per-zone input jump, and after the
carrier-watch counter, so the arrival meets the accept and the counter still sees its probe. The
listing it reads carries each rule's handle, which `nft list` prints only with `-a`; without the
handles a rule can neither be found nor moved, and every rule the daemon meant to re-place stayed
where it was.

## Two more defects on the same path

The TCP poke threw its error away, so a dial that failed said nothing. It names the failure now, and
that name is what led to the rest. Its dial also ran only on a live STUN link, so the poke stopped whenever the
link dropped and the mapping lapsed with it; the poke leaves on every interval now. The
STUN-over-TCP attempt had no deadline, so a server that answers datagrams alone held the loop for the
kernel's whole SYN-retry budget and left its fold behind; the attempt is abandoned on time, and its
fold goes with it.

## The lane

The relay answered each poke with the marker the poke carried. No reader consumed that answer, and
the harness's own poke socket read the marker in place of the forwarded datagram, so one lane went
red for a reason that had nothing to do with the change beside it. The answer is gone, and the lane
is green again.