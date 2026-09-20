# Two datapath defects, written up

- Date: 2026-09-20
- Milestone: plan/0010, the tasks `#inbound-translation` and `#lease-churn`
- Component: `ds-lite-punch`, pins `56faf04`, `5214039b`, binary `0abae591`
- Ground truth: `MEMORY.md` entries of this date win where this file and a plan
  document disagree

Both defects live in the same machinery: what the daemon installs in `nft` when
it grants a slot, and what it removes when it retires one. The first was
silent for days and broke the promise the whole design rests on. The second was
found while proving the first, and it is why that proof cannot yet close.

---

# Defect one: an arrival at a slot port never reached its client

## Symptom

A stranger's datagram to a mapping's external tuple arrived at the router's WAN
and stopped there. The 2026-09-18 acceptance had delivered every arrival to the
client's own socket, so the measurement on 2026-09-20 was the first time the
difference showed.

## Evidence

The arrival is on eth1, and nothing on the LAN carries it further:

```host-lint:ignore
1789905112.873698 IP 170.9.238.141.54372 > 192.168.0.21.40002: UDP, length 14
```

```host-lint:ignore
snat_map: no elements
inet fw4 dslp_ports_udp: elements = { 40000, 40002 }
```

The accept element is there, so the packet was admitted. No translation existed,
so no rule sent it to a client. The client's own socket logged nothing, and the
LAN capture held nothing for it.

## Root cause

Commit `4d31181`, "grant: stop pinning the client's own port, which gave one
game two tuples". The pin was a `snat_map` element for the client's own tuple,
and it did two jobs. Its stated job was egress: it made the client's traffic
leave by the slot's port. Its unstated job was ingress: the conntrack entry of
that pinned flow was the only thing that translated an arrival at the slot port
back to the client. The commit removed both jobs with one deletion, and
call/0014 records only the first.

The accept-set work that followed kept the deletion in place. `grant_datapath`
carried the comment that "the inbound path needs nothing of the client's
egress", which was true of the *accept* element and false of the *translation*.

## Mechanism

An arrival at a slot port reaches the router's input path. The accept set lets
it in, the daemon holds no socket on that port, and with no pinned flow there is
no conntrack entry to reverse. The packet is therefore admitted and discarded,
and every local view reports the mapping alive.

## Blast radius

Every mapping whose client had no pinned flow: the facade's leases from PCP,
UPnP and NAT-PMP, and any static whose client was quiet. The arm's own hold was
unaffected, because the arm pins the console's flow itself, which is why the
2026-09-18 acceptance delivered its arrivals and the defect stayed invisible:
that run's second mapping rode the arm's hold.

## Disposition: fixed

The translation moved to the ingress, at pins `56faf04` and `5214039b`:

- `dslp_in_udp` and `dslp_in_tcp` hold the translated ports, and
  `dslp_dnat_udp` and `dslp_dnat_tcp` hold the client tuple that owns each one,
  all addressed by element;
- a prerouting chain at priority `-150`, ahead of fw4's own `dstnat`, carries
  one rule per protocol:
  `iifname "eth1" udp dport @dslp_in_udp dnat ip to udp dport map @dslp_dnat_udp`;
- a grant adds the two elements, and a revoke removes them along with the
  accept element.

The egress property call/0014 bought survives untouched.

## Verification

The datapath translation is proven on the box. A stranger's datagram to a
lease's external tuple appeared on the LAN at the client's own port, and the
conntrack entry names both halves:

```host-lint:ignore
13:06:36.907238 IP 170.9.238.141.41112 > 192.168.21.11.41020: UDP, length 12
src=170.9.238.141 dst=192.168.0.21 sport=41112 dport=40002 packets=1 bytes=49 [UNREPLIED] src=192.168.21.11 dst=170.9.238.141 sport=41020 dport=41112 packets=0 bytes=0
```

The component is at 210 tests, four of them new: the inbound rule's shape, the
grant's two elements, the revoke's separate statements, and the port-set parse
the read-back uses.

**Not yet proven: delivery into a listening socket.** The test client requests
an internal port with `--int-port` while its socket binds an ephemeral one, so
nothing waits on the port the lease names. The attempt with a listener bound to
the requested port met defect two.

## Two defects the deployment itself found

- **A rule with no chain.** The first build of this design installed the rule
  and never the prerouting chain. The install failed and the daemon refused to
  start, which is the right failure: it did not run with a datapath it could not
  build. procd respawn-looped it until the parked build was restored.
- **An all-or-nothing revoke.** The old revoke ran one `nft` batch of two
  deletes, so a missing element (the arm's pin, which most paths never make)
  cancelled the accept element's removal as well. Measured on the router, the
  batch failing on `snat_map` left the port accepted. The revoke now runs each
  statement on its own and reads the set back afterwards, because a translation
  that survives a revoke can deliver another client's traffic.

---

# Defect two: a revoke tears down a live slot's datapath

## Symptom

Leases disappeared seconds after being granted. A lease confirmed at 13:09:09
had its accept element deleted at 13:09:11, and the inbound set and map ended
empty while the leases were still in the daemon's table.

## Evidence

The daemon's log, in order, for three requests from one client on one afternoon:

```host-lint:ignore
Sun Sep 20 13:09:09 2026 daemon.err ds-lite-punch[18969]: delete element inet fw4 dslp_ports_udp { 40001 }
Sun Sep 20 13:09:09 2026 daemon.err ds-lite-punch[18969]: delete element ip dslp snat_map { 192.168.21.11 . 41040 }
Sun Sep 20 13:09:09 2026 daemon.err ds-lite-punch[18969]: delete element inet fw4 dslp_ports_udp { 40002 }
Sun Sep 20 13:09:09 2026 daemon.info ds-lite-punch[18969]: {"event":"collision-avoided","detail":"slot 40003 steered around the live tuple(s) [40001, 40002]"}
Sun Sep 20 13:09:09 2026 daemon.info ds-lite-punch[18969]: {"event":"churn","detail":"slot 40003 confirmed 37.228.213.83:59301"}
Sun Sep 20 13:09:11 2026 daemon.err ds-lite-punch[18969]: delete element ip dslp snat_map { 192.168.21.11 . 3074 }
Sun Sep 20 13:09:11 2026 daemon.err ds-lite-punch[18969]: delete element inet fw4 dslp_ports_udp { 40003 }
```

Read that as a sequence. Three ports are revoked in the same two seconds:
`40001` and `40002`, which the accept set no longer holds, and `40003`, which
was granted in the same second and is the newest live slot. Every delete names
an element that is not there. One revoke names internal port `3074`, which the
PCP legs of that client never used: those ran on `41010`, `41020` and `41040`.

## Root cause

Two facts, each correct alone, combine:

- **An entry is keyed by the internal tuple.** `apply_entry` indexes
  `(proto, owner, int_port)`, and its comment states the rule: "One entry per
  internal tuple". A re-Add that carries the same internal tuple refreshes the
  entry in place; a re-Add from the same client on a different internal port is
  a different entry and takes its own slot.
- **The probe asks more than once per run.** `deploy/pcp-probe.py` sends a PCP
  MAP for its `--int-port`, a second MAP for protocol 132, a FILTER-option
  request, and NAT-PMP legs. The NAT-PMP default internal port is `3074`, which
  is exactly the port the log names, so a run on `--int-port 41040` also asks
  for `3074`, and the next run surrenders it.

The surrender is deliberate: one client, one mapping per internal tuple, so a
new request takes the old one down. What makes it destructive is the bind port
the surrender hands to the revoke. The entry table has a known history here,
and the tree carries its regression test,
`apply_entry_keyed_per_client_lets_two_holders_share_a_port`, whose own note
says the index used to refresh on `(req_ext, proto)` and never updated
`bind_port`, so a re-Add that moved the mapping to a new slot left the entry
naming the old slot, and delete tore down the wrong datapath. That test guards
the *refresh* path. The evidence above is the same failure arriving through the
*surrender* path: the revoke receives a bind port that the pool has since
reallocated, so it removes a slot that belongs to a different, live lease.

## Mechanism

A request from a client whose earlier entry carried bind port `P` is granted on
a new slot. The surrender retires the old entry and revokes with `P`. The pool
has reassigned `P` in the meantime, so `delete element inet fw4 dslp_ports_udp
{ P }` removes the *current* owner's acceptance, and the same statement list
removes that owner's inbound set and map elements. The loser is a lease with no
part in the exchange. Every delete of the retired entry's own elements reports
"No such file", and that is the ordinary case: those keys were never installed,
because the entry never had elements under them.

## Blast radius

Any client that asks twice, which includes every PCP client that also speaks
NAT-PMP, every client whose library retries with a different internal port, and
every client that requests a port while an earlier entry for another internal
port is live. The house lost its own mapping this way during the 2026-09-20
work, twice, and the earlier accept-element deletions for the consoles'
re-Adds are the same shape.

## Disposition: pending

`plan/0010#lease-churn` carries it, and it is not fixed. The first step is the
one this write-up cannot settle from the outside: which bind port the surrender
path hands to `revoke_datapath`, and whether the entry it retires is the entry
the pool still believes owns that port. The failing test belongs at that
boundary in the shape the existing regression test uses: an entry whose bind
port has been reallocated, retired by a surrender, and the live owner's
elements asserted still present afterwards.

## Verification, when it is fixed

A lease granted from a named client keeps its accept element, its inbound set
element and its map element for the length of its lifetime, and no revoke names
an element another lease owns. A client asking three times in a row leaves
exactly one live lease, and that lease's elements survive the two surrenders.

## Why it blocks the other defect's closing claim

Delivery into a listening socket needs a lease that lives long enough to be
measured. A lease that is revoked two seconds after it is granted cannot carry
that claim, so defect one is proven at the datapath and open at the socket
until defect two is fixed.

---

# How both were found

Neither came from a review. The first came from making a measurement the
records asked for and reading its absence honestly: the arrivals were captured
at the WAN and the delivery to the client was not, and that gap was chased
until it named a cause. The second came from the first one's fix: its proof
needed a live lease, the lease kept dying, and the log named the element
deletes that killed it.