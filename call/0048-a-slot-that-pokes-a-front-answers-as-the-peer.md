# A slot that pokes a front answers its service as the peer

- Status: accepted
- Scope: how a slot that faces a front carries its service's replies
- Date: 2026-10-06

## Context and Problem Statement

[call/0047](0047-a-front-door-slot-folds-its-services-replies.md) asked a front-door slot to fold its
service's replies into the mapping with a pin. The datapath cannot do it. The pin is installed, the
rule is in the chain at two priorities, and the chain is traversed, but the lookup never matches a
service's own flow, so the reply leaves as the service's address and the carrier drops it.

The reason is structural. A carrier mapping's inner tuple belongs to one socket: the daemon's, on a
slot the operator points a front at. The daemon's relay preserves the peer's address, which is the
property a console's mapping depends on, so the service answers the peer directly, as a flow of its
own. No translation of that flow can make it the mapping's, because the mapping belongs to a socket
the service is not.

## Decision

A slot that pokes a front relays symmetrically: the daemon answers the service as the peer, and it
carries the service's datagrams back out of the slot's own socket, where the mapping lives. The
service's peer is the daemon, and the peer's is the mapping.

The rule follows the poke, because a poke names a remote peer: a slot with no poke keeps the
transparent forward it has, and the consoles' granted slots keep theirs. This is the shape the TCP
leg already has, where the daemon's splice originates the connection, so the two protocols finally
share it.

## Consequences

The round trip closes: a datagram from outside reaches the service, and the service's answer reaches
the client through the front.

The service no longer sees the peer's own address on such a slot, which is what call/0047 wanted, and
that is why this decision replaces it rather than amending it. The peer still sees the mapping, so
nothing an outsider observes changes.

The fold the daemon installs is dead weight and goes with the change, along with the pin statement
that only tested it.

## What this does not claim

It does not give a front-door slot more than one client at a time, which the relay's single remembered
peer keeps as it is, and it leaves every other slot's forwarding untouched.