# A front-door slot folds its service's replies

- Status: accepted
- Scope: the return path of the datagram a front door's slot forwards to its service
- Date: 2026-10-06

## Context and Problem Statement

The run of 2026-10-06 measured the datagram leg carrying traffic: a client's datagram reaches the
front, the carrier admits it at the held port, the daemon forwards it onward, and the service answers.
The answer then leaves from the service's own address, which is not the mapping's tuple, so the
carrier will not carry it and the front's relay would not accept it. The leg carries one way.

The daemon's relay preserves the peer's address when it forwards an arrival, and the consoles depend
on that property: their peers see the console's own address. A front door's peer is a remote host, and
the service's answer has to leave as the slot's tuple for the carrier to carry it at all.

## Decision

A slot the operator points a front at folds its service's replies into the slot. Its egress toward the
peer leaves as the mapping's tuple, the way a granted slot folds its client's egress with a pin. The
service keeps seeing the peer's own address, and the peer keeps seeing the mapping's tuple, so the
property the consoles rely on stays where it belongs.

Granted slots and the daemon's other sockets keep their behaviour. The fold belongs to the slot a
front's traffic arrives on, which is the one the operator binds and targets.

## Consequences

The round trip closes: a datagram from outside reaches the service, and the service's answer reaches
the client through the front.

The fold is the pin the datapath already carries, so it is one element in a set and the statement that
revokes it, and the rendered nft script is what the tests can assert.

## What this does not claim

It does not show the service's address to the peer, which a carrier-mapped port cannot do, and it
leaves the return path a console's own mapping uses alone.