# The admission rules, measured

Date: 2026-10-07. Task: `plan/0014#admission-rules`. The table the task asks for, with the evidence
each rule rests on.

## The rules

| Rule | What the carrier does | Evidence |
|---|---|---|
| A poke has to be answered | a poke that drew a refusal admitted nothing, at its own port and at another | [the first pass](NOTE-2026-10-06-the-admission-rules-so-far.md): the vantage answered each poke with ICMP port-unreachable, and no arrival crossed |
| The admission reads the address | an arrival from a port the line never spoke to crosses | [the datagram leg](NOTE-2026-10-06-corrected-the-datagram-leg-carries-traffic.md): the front relays from its own socket, and the client's datagram crossed |
| The spoke's protocol decides the protocol | a datagram poke admits datagrams, and a TCP arrival wants a TCP spoke | [the TCP leg](NOTE-2026-10-06-the-tcp-leg-closes.md): the TLS client crossed once the slot's TCP spoke left |
| A slot port wants the box's own accept | the arrival reaches the box, and the box's firewall decides it | the same note: the SYN arrived on `eth1` and the box reset it while the accept rule stood behind the per-zone jump |

## What the table decided

The relay's socket policy: one socket owns the public port, absorbs the poke, and relays a client's
datagram from that same socket, because the carrier admits the tuple the line spoke from.

The TCP side's port topology: nginx proxies the named connection to the carrier tuple from an
ephemeral source port, which the address-only rule allows, and the daemon's listener serves the
arrival once the firewall accepts it.

The single-flow limit: one datagram client at a time holds the front's socket, which the operator page
states, because the socket is the tuple the carrier admits.

## The method the later passes used

Read the slot's tuple immediately before the attempt and again after it, with one slot per protocol
live, so a mapping that moves mid-test becomes visible instead of silently fatal. The first pass
aimed at a tuple read twenty minutes earlier and measured nothing at all.