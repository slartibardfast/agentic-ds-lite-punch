# A port is served from outside the line by a front the daemon tells

- Status: accepted
- Scope: how a port inside this line is reached from outside it: the role of a
  front on a public address, what the daemon tells it, how long a forward lives,
  where a client certificate is validated, and what a front door does not buy
- Date: 2026-09-26

## Context and Problem Statement

The carrier's CGNAT means port forwarding does not reach this line, and a
published answer is a WireGuard bridge: a public VPS whose firewall rewrites the
destination of every arrival into a tunnel that ends on the LAN, at the cost of
encapsulation and the tunnel's round trip. David Álvarez Rosa's "Self-Hosting
Behind CGNAT" (https://david.alvarezrosa.com/posts/self-hosting-behind-cgnat/) is
that bridge measured at 39 ms, and it inspired the front-door use case this
decision settles. That post names no UPnP, PCP or IGD surface.

This component already holds a port on the carrier's side of the line: a slot's
mapping is kept alive by STUN sent from the slot's own tuple, the carrier's
assigned address and port are learned by STUN and re-published under a majority
vote, and an external arrival on a granted TCP slot is accepted and spliced to
the br-lan target. Everything outside the line was missing: a public endpoint, a
route to the held port, and a decision about who may use it.

## Decision

One public front serves the ports held on this line, and the daemon is its
control point:

- The front routes by name. A name whose service does its own TLS, including its
  own demand for a client certificate, is passed through untouched; a name that
  needs central protection terminates at the front and is proxied onward. The two
  classes sit in one front and are chosen per name.
- The daemon contacts the front; the front never contacts the line. The front
  hosts the service and the daemon calls it, which is the WANIPConnection:1
  relationship with the roles exchanged: our gateway asks a front to carry a
  port, where a device asks a gateway to open one. The vocabulary transplants:
  the front's port is the external port, the slot's carrier tuple is the external
  address, the slot is the internal port and internal client, and the forward's
  survival is a lease.
- The daemon speaks HTTPS itself, so the binary carries a TLS client. The cost is
  a dependency in a musl-static router binary, which moves its size and its
  recorded reproducible build.
- A forward is a lease the daemon renews. A line that stops renewing stops being
  routed, so a dead or stolen slot does not keep a forward alive.
- A client's admission is carried by its certificate, minted after a
  DeviceProtection-authenticated login, rather than mirrored outward as a copy of
  the identity store. One authority, one enforcement point. The daemon is a
  client of the same programme and holds its own identity for the control
  channel, so the front has to be certain who is pushing: an unauthenticated
  endpoint would let any caller point a slot at its own service.

## Consequences

The control path is soft, and that is the gain over a bridge. If the front is
unreachable the held port stays held, because the binding belongs to the carrier,
and only the routing table goes stale. The daemon therefore pushes the table
whole and idempotently rather than a stream of ordered changes, and a reconnect
repairs whatever was missed.

The carrier keeps the port. PREFER_FAILURE is refused by design, so a front
carries the port the carrier assigned and the tuple can move under a live
forward. The daemon is the party that knows the current tuple, and the front
learns it from the daemon rather than from its own configuration.

The two protocols differ in what the LAN service sees, and the recipe has to say
so. An external arrival on a granted TCP slot is spliced by the daemon, so the
target sees the router. The UDP path forwards with IP_TRANSPARENT, so the target
keeps the client's own address. Where the front terminates a name, the front is
the only party that sees the client, and PROXY protocol is the only way that
address survives to the target.

The front is the only gate on the public side. A held port sits on the carrier's
shared address inside a narrow range, so a stranger can find it, and the TLS
endpoint is the sole authentication point in the path. DeviceProtection's store
is not reachable by this route: the facade refuses callers outside the LAN.

## What this does not claim

A bridge still buys three things a front door does not: one address for
arbitrarily many ports, an address that does not move with the carrier's
assignment, and independence from the transport. This decision covers the case
where a small number of ports, reached by name over TLS, is what a self-hoster
needs.