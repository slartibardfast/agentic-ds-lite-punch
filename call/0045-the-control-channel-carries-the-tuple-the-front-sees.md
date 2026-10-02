# The control channel carries the tuple the front sees

- Status: accepted
- Scope: what the daemon's push is for, and which half of the exchange carries the front's view of the line
- Date: 2026-10-02

## Context and Problem Statement

[call/0039](0039-the-control-channel-carries-a-tls-client.md) gave the daemon a client certificate and a TLS client, and [call/0042](0042-the-poke-delivers-the-tuple.md) left that client idle: the front already learns the line's tuple from the poke, keeps its names in the operator's configuration, and expires its own lease. What the poke cannot carry is the front's own reading of the line. The front is the peer the line speaks to, its routing table is keyed on the tuple it observed, and the daemon learns that tuple from a STUN server instead, which is a third party and, over TCP, an unreliable one.

The transport was already built and tested: the daemon renders the table, opens the connection with its own identity, verifies the front against the operator's anchor, and sends the whole table again when a push fails.

## Decision

The push carries the table the front routes with, and the front's answer carries the tuple it sees, one line per protocol. The daemon pushes on a minute's interval, slower than the keepalive, because the front's view changes when the carrier moves a port and not on every refresh.

The channel is off unless `--front-endpoint` and `--front-name` are set together, and setting them requires the identity and the anchor; the daemon refuses to start with the set incomplete rather than running a channel that cannot authenticate.

## Consequences

The channel has a caller and a reader, which is what call/0042 was waiting for.

The front's report is a second source for a tuple the daemon learns from STUN, and it is the source the front's own routing uses. Where the two disagree, the front's reading is the one that decides whether an arrival reaches the held port, so a disagreement is a fact worth having on the record.

The daemon records what the front sees. The vote and the tuple files keep their shape, and feeding the report into a slot with no tuple of its own is left to the work that needs it.

## What this does not claim

It does not claim the report reaches the daemon when the front is unreachable: a failed push is a warning, and the channel repairs itself on the next interval.