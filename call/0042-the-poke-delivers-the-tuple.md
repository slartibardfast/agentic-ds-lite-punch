# The poke delivers the tuple, so the push waits for a payload

- Status: accepted
- Scope: what the control channel is for, now that the front learns each tuple from the traffic the line sends it
- Date: 2026-09-27

## Context and Problem Statement

`call/0038` gives the daemon a control channel that pushes a routing table: each
held slot, its carrier tuple, the name the front routes, and whether the class is
pass-through or terminated. Two of those four the daemon cannot know, and a third
arrives by itself.

The names and the classes are the front's own configuration. The operator writes
them where nginx reads them, and `deploy/front-door/nginx.conf` routes on the name
it is given while `poke-listener.py` serves the name it is handed.

The tuple arrives with the poke. The carrier admits the peer the line has spoken
to, so the front receives the poke and takes its source as the line's tuple for
that protocol, which the component's harness proves end to end: a UDP datagram
sent to the front's port reaches the tuple the poke taught it.

The lease is the front's own timer. An entry whose pokes have stopped is
withdrawn, and the harness proves that too.

## Decision

The daemon keeps its client. The identity, the anchor, the push and the
whole-table retry are built and tested, and they are the channel the front will be
told through on the day there is something for it to say.

Today the front is not told the tuple, which it sees for itself; nor the name and
the class, which the operator owns; nor the lease, which its own timer keeps.

## Consequences

The wiring waits for a payload, since a channel that carries nothing is a running
cost with no reader. The candidates are the things a poke cannot carry: policy
that lives in the daemon and reaches the front as data, and a change of admission
the front should learn before a client presents a certificate.

What this leaves alone: the two halves of the exchange, the poke that opens the
port and discloses the tuple, and the lease that withdraws a forward. Those are
measured, and they already do the work this push was planned for.

## What this does not claim

The client is not idle scaffolding. It is the transport that `call/0039` decided
the binary would carry, it has a passing test against a server whose certificate
the anchor signed, and it holds the retry that makes a reconnect repair what was
missed. What it lacks is a reader, and that is a design question rather than a
coding one.