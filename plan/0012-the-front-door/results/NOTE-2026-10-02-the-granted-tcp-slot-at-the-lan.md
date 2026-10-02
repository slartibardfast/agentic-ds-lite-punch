# The granted TCP slot at the LAN, and the wall outside it

Date: 2026-10-02. Task: `plan/0012#hold-tcp-slot`. What `call/0044`'s change was
measured to do on the box, and where the external handshake stopped.

## The deploy

The lane's artifact for `f3002f4`, hashing
`59ed3af1d51de80e38debabfb1646e521db4d5a33c8edbeb823a4d9fa46c665a`, replaced
`/usr/bin/ds-lite-punch` together with `deploy/ds-lite-punch.init`, and the service was
restarted. The running command line was read from `/proc/<pid>/cmdline` and carries
`--poke`, which the previous release's init script had dropped on this box once before.

## What the change does on the box

The datapath shows the change and nothing else does:

- `nft list map ip dslp dslp_dnat_tcp` carries no element, while `dslp_dnat_udp` still
  carries its grant (`{ 40000 : 192.168.21.12 . 40002 }`) and `dslp_in_tcp` carries the
  slot (`{ 40001 }`).
- A connection to the slot's port reached the daemon's own listener and was spliced to
  the client the grant names: the box's `curl http://192.168.0.21:40001/` returned that
  client's own page, an HTTP server in the probe container at `192.168.21.11:8099`.

That is what the decision claims. The arrival is served by the daemon's own connection,
which originates from the bind address the line's policy rule already selects.

## The poke works when the peer's port answers

The poke to a reachable port completes and the peer answers it:

```
09:24:14.490356 IP 170.9.238.141.22 > 192.168.0.21.40001: Flags [S.], seq ..., ack ...
09:24:14.624126 IP 170.9.238.141.22 > 192.168.0.21.40001: Flags [P.], ... SSH-2.0-OpenSSH_9.6p1
```

The vantage's sshd logged the same connection as `Connection closed by 37.228.213.83 port
59245`, which is the slot's own tuple as the carrier presents it. So the fold gives the
poke the slot's port and the line's spoke reaches the peer, both measured.

## Where the external handshake stopped

The peer's arrival never reached the line. Every attempt at the slot's published tuple
came back refused or with no answer, and no SYN for the slot's inner port appears
anywhere in the eth1 capture. Two limits on this vantage explain it, and both sit
upstream of the daemon:

- The vantage forwards TCP 22 and no other port. Its `INPUT` chain ends with
  `-j REJECT --reject-with icmp-host-prohibited`, and TCP 41001 is dropped before the
  vantage's own stack, so opening the host's port changed nothing: the provider's NAT in
  front of it does not forward that port.
- The vantage's outbound source port is rewritten upstream. The `POSTROUTING` SNAT that
  set the test's source port to the poked port 22 was applied (the counter shows one
  packet, 60 bytes), and the carrier still refused the arrival, which the provider's
  remapping of that source port accounts for.

The carrier admits a peer by the tuple it spoke to, so the poke must land on a port the
peer can also originate from, and this vantage offers none after the provider's NAT.

## What this leaves

`#hold-tcp-slot` stays open. Its half inside the box is measured, and its half outside
waits on a vantage whose poke port is forwarded one to one. The handshake remains the
deployment clause `call/0041` assigns.

The rig was restored: `POKE` back to `170.9.238.141:41001`, both captures stopped, the
container's listener stopped, and the two vantage rules removed.