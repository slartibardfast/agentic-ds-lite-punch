# The TCP half of the hold: what can be held, and what can only be said

- Status: accepted
- Scope: the ds-lite-punch daemon's treatment of allowlisted TCP flows and
  the mappings it terminates (plan/0009's task `#tcp-answer`)
- Date: 2026-09-17

## Context and Problem Statement

The hold's local half follows the RFC figures, and for TCP that figure is
what the router already carries: `nf_conntrack_tcp_timeout_established` is
7440 seconds, two hours four minutes, which is the established interval the
mapping requirements set (RFC 5382). The remote half is the problem. On this
line the AFTR reaps an idle TCP mapping between 120 and 300 seconds, which
is inside any client's idea of a long-lived session.

For UDP the daemon writes the AFTR mapping from the flow's own post-NAT
tuple, because any datagram from that tuple refreshes it. A router cannot do
the equivalent for a client's TCP connection: a packet that belongs to that
connection cannot be forged without owning its sequence space, and the
source port is held by the client's own socket, so a second connection from
the same tuple is not available.

Two questions follow, and both need an answer rather than an assumption:
which TCP flows can this daemon actually hold, and what does a client whose
connection cannot be held get instead.

## Decision

- **A mapping the daemon terminates is held, and this is already built.**
  When the facade grants a TCP slot the relay owns the connection's sequence
  space from the client side, and the holder task that runs beside the slot
  dials out from the slot's own tuple on the cadence the mapping needs. That
  is the TCP form of the write the UDP arm makes, and it needs no new
  mechanism.
- **A client's own TCP connection is signalled, never held.** The daemon has
  no way to write into it, so the honest statement is that this mapping is
  maintained by the client's keepalive or by nothing. Claiming otherwise
  would be a promise the datapath cannot keep.
- **The local half applies to allowlisted TCP flows unchanged.** The
  established figure keeps the router's translation, and therefore the
  stateful inbound path, alive across an idle period far longer than the
  AFTR's. It is one dormant row per flow when the connection is idle, so it
  is cheap for the devices on the list.
- **The signal about a TCP mapping is the signal about any mapping.** A
  subscriber of the evented surface sees `PortMappingNumberOfEntries` and
  `SystemUpdateID` move when a mapping is reaped, and a PCP client learns
  that the server lost its state from the epoch in the next response or
  ANNOUNCE. A device's arbitrary connection is not a mapping this daemon
  knows about, so no event describes it, and this limit is stated rather
  than worked around.
- **The surrogate is deferred to its own milestone, and is not implied by
  this one.** Terminating a client's connection and re-originating it is a
  proxy: it changes what the peer sees, it needs its own decision about
  identity and encryption, and it is a different class of change from
  everything else in plan/0009. The machinery it would ride (`tcpslot.rs`
  and `forward.rs`) exists and is proven, so the work is scoped by what it
  would mean rather than by what it would take to build.
- **Nothing in this milestone terminates a connection it did not already
  terminate.** The rule keeps the blast radius where the verification is:
  a mapping the facade granted has a client that asked for it, and a
  client's own session is untouched by this daemon on every code path.

## Consequences

- An allowlisted device whose TCP keepalive is slower than the AFTR's
  measured lifetime loses its mapping mid-session, and no mechanism in this
  milestone prevents it. The device is not worse off than before the hold
  existed, because the local half is what makes the loss recoverable once
  the client sends again.
- A device that needs better than that requires either a client-side change
  or the surrogate, and the measurement that would justify the surrogate is
  a keepalive interval, which the snooping arm can read from the flow's own
  cadence.
- The cost of the local half is stated in the same terms as the UDP hold: a
  dormant conntrack row per idle flow, with no packets spent.
- The two honest limits stay on the record: the daemon cannot hold a
  connection it does not terminate, and a device's own connection has no
  subscriber, so it can be lost without an event that names it.