# The stranger's arrival: a held port admits its peers, not the world

**Date:** 2026-09-26. **Task:** `plan/0012#stranger-arrival`. **Status:** the
first half is measured, and the answer changes the premise. The task is not
discharged, and this record says exactly what remains.

## What was run

The line's state, read from the box rather than assumed:

```
$ cat /run/ds-lite-punch/tuple          -> 37.228.213.83:59348
$ cat /run/ds-lite-punch/tuple-40000    -> 37.228.213.83:59348
$ grep -v '^#' /etc/ds-lite-punch.env   -> BIND=192.168.0.21:40000  TARGET=192.168.21.12:40002
                                           STUN=stun.l.google.com:19302,stun.cloudflare.com:3478
                                           CARRIER_PROBE=1  CARRIER_PROBE_INTERVAL=900  KEEPALIVE=1
```

From the vantage (`170.9.238.141`, a source this line has never sent to, and not
a STUN server), three datagrams to the published tuple and one control to an
unmapped neighbour port, each from its own source port, while two captures ran on
the box: one on `eth1` filtered to the stranger, and one on every interface
filtered to the forward's destination port.

```
sent 1 from ('0.0.0.0', 41001) to ('37.228.213.83', 59348)
sent 2 from ('0.0.0.0', 41002) to ('37.228.213.83', 59348)
sent 3 from ('0.0.0.0', 41003) to ('37.228.213.83', 59348)
control sent to the unmapped port 59349

$ ls -l /tmp/c1.pcap /tmp/c2.pcap
-rw-r--r--  0 Sep 26 18:16 /tmp/c1.pcap
-rw-r--r--  0 Sep 26 18:16 /tmp/c2.pcap
$ tcpdump -n -r /tmp/c1.pcap | head      (nothing)
$ tcpdump -n -r /tmp/c2.pcap | head      (nothing)
```

Nothing arrived at the tunnel side, and nothing was forwarded toward
`192.168.21.12:40002`.

## The control that makes that result mean something

An empty capture is evidence only if the capture would have shown the traffic.
The same filter, on the same interface, while the daemon ran its keepalive:

```
18:19:20.048278 IP 192.168.0.21.40000 > 74.125.250.129.19302: UDP, length 20
18:19:20.069026 IP 74.125.250.129.19302 > 192.168.0.21.40000: UDP, length 32
18:19:21.891580 IP 192.168.0.21.57863 > 74.125.250.129.19302: UDP, length 20
18:19:21.912931 IP 74.125.250.129.19302 > 192.168.0.21.57863: UDP, length 32
```

The slot's STUN request leaves, and the server's reply **arrives on `eth1`
addressed to the inner tuple**. So `eth1` is the interface the AFTR delivers on,
the mapping is live, and inbound from a source the line has sent to works. The
difference between the two blocks is the source: `74.125.250.129:19302` is the
peer the slot talks to, and `170.9.238.141` is not.

## What this means

The carrier's filtering is **source-restricted**. A held port is open to the
peers the line has traffic with, and closed to a stranger, which is the same
property the console's own measurement shows: PSN reaches NAT Type 2, the
restricted-cone verdict, rather than an open NAT (`plan/0006`).

The consequence for the front door is direct. A front cannot reach the held port
by knowing its address and port alone; it becomes reachable when the line has
talked to it. That is the mechanism the TCP datapath already uses and this
record explains: the folded holder dials a STUN server so the server's replies,
and any SYNs from it, are admitted.

So the premise in `call/0038` needs one qualifier. A held port is open **to its
peers**, and the front has to become one.

## What remains, and why the task is not discharged

- The pinhole test is the decisive one. Have the slot's own socket send a
  datagram toward the front's address, and then have the front send to the
  published tuple: does the arrival now succeed? If it does, the front door works
  by making the front a known peer, and the daemon's keepalive arm gains a
  destination. Only the daemon's socket can create that state, because the
  carrier's mapping belongs to the inner tuple `192.168.0.21:40000`.
- The shape of the restriction: address alone, or address and port? The answer
  decides whether the front may reach from a new source port after one outbound
  toward its address.
- The TCP arm needs a held TCP slot and belongs with `plan/0012#hold-tcp-slot`.

## Lessons recorded

`timeout` is not on this router, so a capture started as
`setsid timeout 20 tcpdump ...` dies instantly and leaves a missing file. The
first attempt was read as an empty capture and was nothing of the kind: it failed
to start. A capture whose file is absent did not run, and an absent file must
never be read as a negative result. `setsid` is present, and a capture bounded by
`-c` with the packet count in hand is the shape that works here.