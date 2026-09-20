# An arrival at a slot port is translated to its client

- Date: 2026-09-20
- Milestone: plan/0010, the task `#inbound-translation`, found by `#eif-now`
- Component: `ds-lite-punch`, pins `56faf04` and `5214039b`, binary on the
  router `0abae591`
- Ground truth: `MEMORY.md` entries of this date win where this file and a plan
  document disagree

## The defect, and its root cause

The 2026-09-20 measurement of the carrier's filtering left one thing
unexplained: the stranger's datagrams reached the router's WAN and never
reached the client's socket, where the 2026-09-18 acceptance had delivered
every one.

The root cause is commit `4d31181`, "grant: stop pinning the client's own port,
which gave one game two tuples". That change was right on its own terms and
call/0014 records why: the pin made the client's own traffic egress through the
slot's port, so one game held two external tuples at once. What the change also
removed was the only thing that mapped an arrival at the slot port back to the
client, because the reverse translation had been done by the pinned flow's
conntrack entry. With the pin gone, an arrival reached the port, was accepted,
and stopped there.

Nothing was watching that, and the accept-set work of the same period kept the
removal in place without noticing what it had carried.

## The fix

The translation moved to the slot's ingress. The client's egress is untouched.

- a set of translated ports per protocol (`dslp_in_udp`, `dslp_in_tcp`) and a
  map holding the client tuple that owns each port (`dslp_dnat_udp`,
  `dslp_dnat_tcp`), both addressed by element;
- a prerouting chain at priority `-150`, ahead of fw4's own `dstnat`, carrying
  one rule per protocol:
  `iifname "eth1" udp dport @dslp_in_udp dnat ip to udp dport map @dslp_dnat_udp`,
  and the same rule for `tcp`;
- a grant adds the port to its set and its client tuple to the map, then the
  accept element as before;
- a revoke runs every element delete as its own statement, because a batch is
  all-or-nothing and an absent element (the arm's own pin, when it never made
  one) used to cancel the rest of the revoke. The revoke is read back, and a
  translation that survived is a warning, because a port can be reallocated and
  a stale translation would deliver another client's traffic.

The client's egress is untouched, which is the property call/0014 bought.

## What is proven

The component is at 210 tests. The lane built `0abae591` for pin `5214039b`,
the router was installed from those bytes after a hash check, and the previous
builds are parked beside them.

The datapath translation is proven on the box. A lease was taken for internal
port 41020, a stranger's datagram was sent to its external tuple, and the
translated packet appeared on the LAN at the client's own port:

```host-lint:ignore
13:06:36.907238 IP 170.9.238.141.41112 > 192.168.21.11.41020: UDP, length 12
```

The conntrack entry for that arrival names both halves of the translation:

```host-lint:ignore
src=170.9.238.141 dst=192.168.0.21 sport=41112 dport=40002 packets=1 bytes=49 [UNREPLIED] src=192.168.21.11 dst=170.9.238.141 sport=41020 dport=41112 packets=0 bytes=0
```

The reply tuple reads the client's own tuple, which is what the ingress
translation installs. Before the fix, that packet reached `192.168.0.21:40002`
and nothing carried it further.

**Not proven: delivery into a listening socket.** The client tool used for the
lease requests an internal port (`--int-port`) while its socket binds an
ephemeral one, so the arriving packet had no socket waiting on the port the
lease names. That is a property of the test client, and it is why the earlier
acceptances delivered into the socket: those runs had a listener on the
requested port. A listener was run for the last attempt, and the claim met the
second finding below.

## The second finding, recorded and not fixed

While proving the fix, leases began to disappear seconds after being granted.
The daemon's own log, for two leases granted at 13:09:09:

```host-lint:ignore
Sun Sep 20 13:09:09 2026 daemon.err ds-lite-punch[18969]: delete element inet fw4 dslp_ports_udp { 40002 }
Sun Sep 20 13:09:11 2026 daemon.err ds-lite-punch[18969]: delete element ip dslp snat_map { 192.168.21.11 . 3074 }
Sun Sep 20 13:09:11 2026 daemon.err ds-lite-punch[18969]: delete element inet fw4 dslp_ports_udp { 40003 }
```

Each delete names an element that is not there, and the inbound map and set end
empty while the leases are still live in the daemon's table. One revoke names
`192.168.21.11 . 3074`, an internal port no lease in this session used, so the
revoke is reading a key from somewhere other than the lease it is retiring. The
`snat_map` delete is the arm's pin path, which is expected to be absent; the
accept-element deletes for the newest slots are not.

This is a separate defect with its own root cause, it is not dispositioned
here, and the milestone carries it as a pending task (`#lease-churn`). It also
means the delivered-to-socket claim waits on it: a lease that is revoked two
seconds after it is granted cannot carry a measurement.

## Cleanup

The harness is gone: the leases' clients, the listener, the staged scripts and
the captures. The router runs `0abae591` with the archive of parked builds
beside it, and the consoles' holds are in force (`"ruleset_in_force":true`,
three devices).