# The TCP leg is one fix away, and the front's log names it

Date: 2026-10-06. Task: `plan/0014#the-tcp-leg`. The chain, the tuple, and the single thing missing.

## The tuple is supplied

The front's table carries the name line now:

```
8443 37.228.213.83:59348; # poke
passthru.rig 37.228.213.83:59255; # push
```

The push was carrying it all along (`40001 6 37.228.213.83:59255` in the body the relay logged); the
slot's tuple had simply not been published before 18:05, so until then there was no TCP line to write.
Nothing was wrong with the control channel.

## The chain

A TLS client with the pass-through name reaches the front, and the front routes it to the tuple. Its
log says so, and it says where the chain stops:

```
[error] connect() failed (111: Connection refused) while connecting to upstream,
        client: 84.203.115.61, upstream: "37.228.213.83:59255"
```

So the name split works, nginx dials the carrier tuple, and the carrier refuses the dial.

## What is missing

The carrier admits a peer it has spoken to, and the spoke has a protocol. The line's datagram pokes
teach it to admit datagrams; a TCP arrival needs a TCP spoke, which is the poke's dial on the TCP side.
That dial is the one thing failing, with `Operation not permitted` in the daemon's log, so the line
never speaks TCP to the front and the front's dial is refused.

That makes the TCP leg's work a single daemon-side fix rather than the relay the milestone expected:
repair the TCP poke's dial, and the arrival it opens is already served by the splice that waits on the
slot.

## The rig

The probe container runs the TLS service on 8099, which the granted TCP slot's client names, so once
the poke's dial works the client's handshake should come back with that service's certificate. The box
runs the lane's relaying build, and the datagram round trip stays proven.