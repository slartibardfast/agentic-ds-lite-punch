# The TCP slot: a tuple that needed a server speaking over TCP

**Date:** 2026-09-27. **Task:** `plan/0012#hold-tcp-slot`. **Status:** the slot is
held and its tuple is known; the external handshake is refused, with the cause
identified and one piece of code owed.

## What was asked for and what came back

A LAN client asked the facade for a TCP mapping of port 443. The PCP probe needed
`--client 192.168.21.97` first, because this client sits behind a second NAT and
the facade answers ADDRESS_MISMATCH until it names the address the facade sees.
The wire showed the address directly, taken from a capture on the bridge, so no
guess was made. The lease was granted and persisted:

```
40001   1       192.168.21.97   443     0       600     1790511683      1790511085      6
```

inner port 40001, kind 1, protocol 6, a lease of six hundred seconds.

The mapping's external tuple did not appear. Every MAP answered
`NETWORK_FAILURE, lifetime 30`, which `src/upnpsvc.rs:2714` explains: that is the
verdict while the mapping's tuple is unknown, and a client is meant to retry.

## The cause

A TCP slot learns its tuple by dialling a STUN server over TCP. Both servers in
the default list complete the connection and then never answer:

```
stun.l.google.com 19302 -> no reply over TCP: TimeoutError
stun.cloudflare.com 3478 -> no reply over TCP: TimeoutError
```

So the tuple stayed unknown, the chase of a retry loop came to nothing, and the
per-slot file was never written. One server does answer over TCP, with a binding
success:

```
ANSWERED: stun.nextcloud.com 443 -> 68 bytes, type 0x0101
```

## The fix, and what it proved

The default list now carries that server, in the code that defines it and in the
one definition the help text and the manual page are generated from, with the
reason written where each is read. The component's suite pins it, so an edit that
drops it fails a test.

With the server in the list, a TCP slot came up whole on the box:

```
/run/ds-lite-punch/tuple-40003 = 37.228.213.83:59355
{"event":"churn","detail":"slot 40003 confirmed 37.228.213.83:59355"}
```

That slot held a bound wildcard listener and a fold pin, so a TCP 443 slot now
exists on this line with a known external tuple.

## The handshake from outside, and why it is refused

The vantage connected to that tuple and got ECONNREFUSED, and nothing reached
`eth1` in the same window. The refusal came from the carrier, and it is the same
source restriction the UDP measurement found: the holder's only peer is the STUN
server, so the carrier has no reason to admit a stranger's SYN. A UDP slot solves
this with the poke, and the TCP holder needs the same thing in its own form: a
dial toward a nominated destination, sent over its folded tuple. That is the piece
still owed, and the front is the destination it will want, since the front is also
the party that can report the tuple it observes.

## What this leaves

`plan/0012#hold-tcp-slot` stays open until an external handshake through the slot
succeeds, which waits on the TCP poke. The observation worth carrying: the
carrier gave slot 40000 the port `59348` and slot 40003 the port `59355`, so each
slot has an external port of its own and the published file speaks for one slot
at a time.