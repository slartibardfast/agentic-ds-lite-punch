# The datagram leg at the front, and the edge that will not carry it

Date: 2026-10-06. Tasks: `plan/0014#the-legs` (datagram half) and part of `#admission-rules`.

## What the front does, measured

With the relay deployed (its unit owning `0.0.0.0:8443` for datagrams, nginx holding the port's TCP
half) and the daemon's `--poke` pointed at `170.9.238.141:8443`, the poke reaches the front and
teaches it:

```
/etc/front-door/upstreams.map: 8443 37.228.213.83:59348; # poke
journal: udp poke from 37.228.213.83:59348        (every two seconds)
```

An outside client's datagram, sent from this machine to the front's public port, drew this capture at
the front:

```
13:23:25.304645 IP 84.203.115.61.58649 > 10.0.0.52.8443: UDP, length 18   the client's datagram at the front
13:23:25.304786 IP 10.0.0.52.8443 > 37.228.213.83.59348: UDP, length 18   the relay's onward datagram, from the poked port
13:23:25.573954 IP 37.228.213.83.59348 > 10.0.0.52.8443: UDP, length 9    the line's poke at the front
```

The leg does what the design asks of it: the pokes land on its socket, it learns the tuple from them,
and the onward datagram leaves from the very port the poke was addressed to.

## Where it stops

Nothing reached the line. The eth1 capture holds zero packets for the slot's tuple, zero at the
target, and zero ICMP. The relay's datagram dies between the front and the carrier.

That separates the rules the earlier passes could not. An *absorbed* poke admits no more than a
refused one did, and the onward datagram's source port matched the poke's destination port, so
neither the poke's reception nor the port is the missing condition. What is left is the vantage's own
provider, which rewrites the source port of traffic the vantage sends. The front's datagrams then
arrive at the carrier from `170.9.238.141` with a port the carrier never saw poked, and the carrier
refuses them.

## What this means for the phase

The datagram half is built and measured at the front, and it cannot be finished from this vantage. A
front whose outbound source ports survive its own provider is what the carrier's rule asks for, and
the ingress rule the operator had to repair for this vantage is the mirror of the same class of
problem. Until that host exists, `#the-first-byte` waits, and the honest options are another vantage
or the provider's own configuration.

## The rig

The daemon keeps `POKE=170.9.238.141:8443`, because that is where the leg's socket is and the poke
view it feeds is real. The captures are stopped on both ends.

**Corrected 2026-10-06.** The verdict above is wrong. The greps looked for the slot's external port,
and the carrier un-NATs an arrival before it reaches the wire, so the traffic was present and
uncounted; the second test's target absorbs without answering, so its client timed out on a path that
had worked. [The correction](NOTE-2026-10-06-corrected-the-datagram-leg-carries-traffic.md) carries
what is measured now.