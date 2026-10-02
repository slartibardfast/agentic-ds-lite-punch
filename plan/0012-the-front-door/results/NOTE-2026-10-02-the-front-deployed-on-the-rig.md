# The front, deployed on the rig

Date: 2026-10-02. What was put where, what the deployment proved, and the one wall
outside it.

## What is deployed

The front runs on the external vantage (`170.9.238.141`), from the shipped files:

- `deploy/front-door/nginx.conf`, rendered with the rig's own values, under
  `/etc/front-door/nginx.conf`, as the `front-door-nginx` systemd unit. It listens on
  `8443` (the stream listener that reads the name), `8446` (the local block that
  terminates the protected name) and `41002` (the UDP leg), and it reaches the control
  channel's route through `127.0.0.1:8448`.
- `deploy/front-door/poke-listener.py` as the `front-door-poke` unit, listening on
  `41001` for pokes and answering the daemon's push on `127.0.0.1:8448`, writing the
  routing include at `/etc/front-door/upstreams.map`.
- The authority is minted on the line, in `/etc/ds-lite-punch-tls` on the box, as
  `call/0040` requires: `ca.crt`, a `front.crt` for the front (`CN=front.rig`,
  `subjectAltName=DNS:front.rig`, serverAuth), and the daemon's own `client.crt`
  (clientAuth). The front receives the anchor and its own certificate; the daemon keeps
  its identity and the authority.

The daemon on the box runs the released bytes, `b21eaad3…` of `v0.5.0`, deployed with
`deploy/ds-lite-punch.init`, and carries the four settings the channel needs:
`CLIENT_IDENTITY`, `FRONT_ANCHOR`, `FRONT_ENDPOINT=192.168.224.1:8443` (the vantage over
the wireguard tunnel the box already has) and `FRONT_NAME=front.rig`.

## What the deployment proved

The control channel runs for real. The front's access log carries the daemon's push
every minute, and the front's own log carries the path it took:

```
POST /table HTTP/1.0" 200 1   (192.168.224.21, the box, over the tunnel)
client 192.168.224.21:59700 connected to 0.0.0.0:8443
proxy 127.0.0.1:58714 connected to 127.0.0.1:8446
```

So the daemon authenticated with its own identity, the front terminated the protected
name, verified the certificate against the anchor, and answered.

The protected class is proved from the box, with the daemon's certificate and without:

```
$ printf "GET / HTTP/1.0\r\nHost: front.rig\r\n\r\n" | openssl s_client \
    -connect 192.168.224.1:8443 -servername front.rig -CAfile ca.crt \
    -cert client.crt -key client.key -quiet
HTTP/1.1 200 OK
```

The same request without the certificate gets no response at all: the TLS layer demands
it, which is the split the harness asserts precisely in the lane.

## The wall outside it

The front has learned no tuple, and its answer is a single newline. The pokes leave the
line faithfully:

```
20:58:12.180977 IP 192.168.0.21.40000 > 170.9.238.141.41001: UDP, length 9
```

every two seconds, and they do not arrive. A fourteen-second capture on the vantage's
own interface holds **zero packets**, and a listener bound on the free port sees nothing
while they flow. The provider's NAT in front of the vantage drops them upstream of the
host, which is the same wall the TCP poke met: this vantage forwards TCP 22 and delivers
nothing else, and a host-level rule cannot change that.

So the deployment is complete and the channel is live, while the front's own learning
waits on a vantage whose inbound `41001` is delivered. The daemon reports nothing rather
than a stale tuple, which is what the report is for.

## What this leaves

Two ways forward, and the operator's to choose. A vantage whose provider forwards the
poke port finishes the deployment as designed. Or the front learns the table from the
push itself, which already carries it: the daemon's body is the routing table, the front
reads it today only to discard it, and the poke would keep its other office, which is
that the carrier admits a peer the line has spoken to.