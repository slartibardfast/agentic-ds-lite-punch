# The front's legs ride the poked socket, and the firewall's place carries the TCP one

- Status: accepted
- Scope: the front door's two legs, and the daemon rule a slot's TCP arrival depends on
- Date: 2026-10-07

## Context and Problem Statement

The front holds one public port, and both of its legs had to be settled against what the carrier
actually does. The measurements are in `plan/0014-the-fronts-legs/results/`: the carrier admits a peer
the line has spoken to, and the admission reads the **address** alone, so a peer's source port is free;
the protocol of the spoke decides which protocol is admitted, so a datagram poke admits datagrams and a
TCP arrival needs a TCP spoke; and an arrival reaches a slot's listener only when the box's own
firewall accepts it.

[call/0048](0048-a-slot-that-pokes-a-front-answers-as-the-peer.md) settled how a slot that faces a
front answers its service. What was left was the shape of the two legs themselves, and the daemon rule
the TCP leg turned out to need.

## Decision

- The **UDP leg** holds the public port. One socket absorbs the poke, learns the tuple from the poke's
  source, and relays a client's datagram onward from that same socket, because the carrier admits the
  tuple the line spoke from. One datagram flow at a time holds the socket, and the operator page says
  so.
- The **TCP leg** holds the same port's TCP half in nginx. The name route proxies the connection
  straight to the carrier tuple, and the slot's listener splices it to the client. No relay stands
  between the two, which is the part the milestone expected and the measurement retired.
- The daemon **places a slot's accept rule ahead of the firewall's per-zone input jump**, and
  re-places it on every start. The zone's policy resets an arrival it meets first, so a rule the chain
  reaches afterwards decides nothing. The rule is one per protocol over a set of slot ports, and the
  listing it reads carries each rule's handle.
- The two views of [call/0046](0046-the-front-learns-from-the-poke-and-from-the-push.md) stand
  unchanged: the poke's own source is authoritative for its protocol, and a push fills what the poke
  has not reached and names itself as the view that did.

## Consequences

- One public port serves UDP and TCP, and the front's routing table carries a line per protocol.
- The outer tuple is the carrier's to choose. A lost mapping takes a new outer port, so the front
  follows the daemon's report rather than a remembered value.
- A TCP slot's liveness rides a STUN-over-TCP link that several public STUN servers cannot hold, so
  the poke leaves on every interval and the slot's mapping survives a dropped link.

## What this does not claim

- More than one datagram client at a time on the socket.
- An inbound TCP arrival for a slot whose port the firewall has not accepted; the placement runs at
  daemon start.
- A stable outer port across a mapping's loss.