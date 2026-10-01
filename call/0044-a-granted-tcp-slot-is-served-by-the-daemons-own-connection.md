# A granted TCP slot is served by the daemon's own connection

- Status: accepted
- Scope: the ingress path of a granted TCP slot, and which of its two delivery paths carries the arrival
- Date: 2026-10-01

## Context and Problem Statement

The grant installs a translation: an arrival at the slot's port is forwarded to the client that asked for the mapping. The return-path record of 2026-09-27 measured where that ends for TCP. The SYN reaches the client, and the client's reply leaves by the other WAN, because the policy rule that sends traffic down the mapping's line matches the source address at the routing decision, and a forwarded reply's source is the client's own address. The peer discards a reset arriving from a different address, so the connection never completes. The same record named the two routes out: an egress rule for the service host, which the consoles carry, or the daemon presenting its own bind address, whose rule is already in place.

The listener that would serve the slot is already built and already spawned for every TCP grant. It binds the slot's port, splices what it accepts to the client's address and port, and holds the mapping with a STUN-over-TCP link and the poke. The translation is what keeps that listener from ever seeing an arrival.

## Decision

A granted TCP slot installs no translation. The grant admits the port, and the arrival reaches the daemon's listener on that port, which splices it to the client. The connection to the client originates from the daemon's bind address, and the line's policy rule already selects traffic from it, so the reply takes the mapping's line with no per-host configuration.

A granted UDP slot keeps its translation, and with it the peer's address as the target sees it, which the pinhole run measured on the line.

## Consequences

The front door's TCP leg needs no rule placed per service host, and the deployment's clause becomes a measurement.

A client on a TCP slot does not see the peer's address. The component's operator page already says this of a spliced connection: the daemon originates it, and PROXY protocol is the only way that address survives where the front terminates a name.

The translation rule and its map stay in the ruleset, and no grant inserts an element into them. Removing them would cost a ruleset change on every box that carries them, and a translation whose map lookup misses is inert.

## What this does not claim

The external handshake through a granted TCP slot is a deployment's measurement, and the milestone's `#hold-tcp-slot` task carries it.