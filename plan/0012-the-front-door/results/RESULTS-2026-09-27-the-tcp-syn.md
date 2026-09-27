# The TCP poke admits the SYN; the SYN-ACK is the fault that remains

**Date:** 2026-09-27. **Task:** `plan/0012#hold-tcp-slot`. **Status:** admission is
solved for TCP and measured; the handshake fails on the box, and the shape of that
failure is now isolated.

## The change under test

The TCP holder now pokes a nominated peer, the same peer the UDP slots poke, with
one difference in mechanism: it opens a connection from a fresh ephemeral port
folded to the slot, writes the marker, and removes the fold pin afterwards, so a
dial leaves as the slot's own tuple and no pin accumulates. It fires once per
keepalive interval while the holder is live. Committed on the component as
`38f9a9d`, with `cargo test --release --locked` at 223 passed.

## What the vantage saw

With the holder poking port 41001 on the vantage, the vantage then attempted a
connection to the slot's tuple `37.228.213.83:59237`, with its own source port set
to the port it had been poked on. The SYN arrived:

```
13:53:51.798388 IP 170.9.238.141.41001 > 192.168.0.21.40001: Flags [S], seq 3720419268, ...
13:53:52.809798 IP 170.9.238.141.41001 > 192.168.0.21.40001: Flags [S], seq 3720419268, ...
13:53:53.835232 IP 170.9.238.141.41001 > 192.168.0.21.40001: Flags [S], seq 3720419268, ...
```

Eight retransmissions, no reply. The same test before the poke produced nothing at
all on `eth1`, so the carrier's refusal was the whole story then, and it is not
any part of the story now.

The vantage's `connect_ex` returned 11 with a read timeout, which is a connection
still trying, and there is no SYN-ACK in the capture to answer it.

## What this isolates

Admission for TCP is done: a peer the line has spoken to reaches the slot, from
the exact port it was poked on. The remaining fault sits on the box, where a SYN
that the AFTR forwarded to an inner tuple gets no SYN-ACK. The datapath work of
2026-09-13 met the same wall from the other side and recorded its prime suspect
untested: the input path for a translated source, with `net.ipv4.conf.eth1.rp_filter`
and the route that source takes named as the things to check. That check is the
next step, and it is now the only thing between the front door and a served TCP
port.

## Two things this leaves on the record

A UDP-only front door works today: the UDP leg was measured end to end, with the
peer's address preserved through the forward. The TCP leg reaches the box and
stops there.

The holder rotates servers on error, and a server that cannot answer STUN over TCP
looks like an error, so a fresh TCP slot walks the list before it finds one that
works. The default list now ends with the server that answers, which means up to
three intervals before a tuple appears. Ordering the TCP-capable server first
would take that to one, and the list is shared with the UDP path, so the change
wants a moment's thought rather than a blind reorder.