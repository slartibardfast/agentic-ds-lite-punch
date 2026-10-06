# The TCP leg needs a tuple the front does not have

Date: 2026-10-06. Task: `plan/0014#the-tcp-leg`, and it is smaller than the milestone expected.

## The design is simpler than planned

The admission measurements and the daemon's splice between them remove the relay this task was going to
build. The carrier admits a peer by address, so a dialling source port does not matter, and on a TCP
slot the daemon already splices, so the daemon is the peer and carries both directions. nginx can
therefore route a named connection straight to the carrier tuple, which is what the shipped
configuration already does.

## What stops it

The front holds no TCP tuple. Its table reads:

```
8443 37.228.213.83:59348; # poke
```

The UDP line is there and the TCP name line is not, so a named connection falls to the reject default
and a client is refused before anything reaches the line. Two things could supply that tuple and
neither does yet:

- The control channel's push carries the daemon's table, which should hold the granted TCP slot and
  its tuple. The slot is live (`slot 40002 confirmed 37.228.213.83:59360`) and its tuple is published,
  so the push's own account of the table is what needs reading.
- The TCP poke is what would teach the front the tuple from its source, the way the datagram poke
  teaches it, and that dial fails with `Operation not permitted`, which the same log carries.

## The rig

The probe container runs a TLS service on 8099, which is the port the granted TCP slot's client uses,
so a named connection through the front should reach it and its certificate should come back. The
box runs the lane's relaying build and the datagram round trip stays proven.