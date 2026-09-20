# Two datapath defects, written up

- Date: 2026-09-20
- Milestone: plan/0010, the tasks `#inbound-translation` and `#lease-churn`
- Component: `ds-lite-punch`, pins `56faf04`, `5214039b`, then `8f179c7`,
  `0b72060b` and `709e7668`, binaries `0abae591`, `f4499c2c` and `ddfe3903`
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

The component reached 210 tests with this fix, four of them new: the inbound
rule's shape, the grant's two elements, the revoke's separate statements, and
the port-set parse the read-back uses.

**Delivery into a listening socket is proven**, and the proof is in defect
two's verification below: a stranger's datagram to a lease's external tuple
arrived at a listener bound to the port the lease names, 72 ms after it was
sent. The first attempt failed for an instrument reason, because the test
client requests an internal port with `--int-port` while its socket binds an
ephemeral one, so nothing waited on the port the lease named.

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

# Defect two: a request that names no port takes the client's other mapping away

## Symptom

A client's mappings did not coexist. Asking twice while measuring left one
mapping where two were asked for. The log's own deletes were read at first as
the daemon tearing down a lease seconds after granting it; the instrument
accounts for part of that, and what it does not account for is the defect
below. The second request surrendered the first, and the client's earlier
mapping was gone while its new one lived.

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

Read that as a sequence, and then read it again with the instrument in view,
because the first reading was wrong and the correction matters. Three ports are
revoked in the same two seconds, and the deletes name elements that are not
there. What the log does not show is who asked. `deploy/pcp-probe.py` ends every
run by deleting its own mapping, so two of those revokes are the client's own
teardown of its own lease, and the errors that accompany them are the pin
statement below. The window proves less than it first appeared to, and the
defect it was made to carry is narrower than the first version of this record
claimed. The sections that follow are the corrected account.

## Root cause

Two facts, each correct alone, combine:

- **A refresh is keyed by the internal tuple, and a supersession is keyed by the
  requested port.** `apply_entry` refreshes in place when
  `(proto, owner, int_port)` matches, and otherwise lets a request surrender the
  same client's earlier entry at the same `(req_ext, proto, owner)`. Its comment
  states the rule for the second key: the requested port is the client's handle,
  and one client holds one mapping per handle.
- **A request that names no port carries `req_ext` 0, and 0 was treated as a
  handle like any other.** Two requests that both ask for "any port" therefore
  collided, and the second surrendered the first. `deploy/pcp-probe.py` shows
  this because every leg of a run asks for the same suggested port, and a client
  speaking PCP and NAT-PMP asks for "any port" twice by construction.

The failing test states it without the box in the way: the second request
returns `Some((40002, 192.168.21.11, 41010))`, which is the first lease's slot
handed to the revoke.

## Two further defects, both found here and both fixed

- **The restore path disagreed with the grant path.** The boot loop pinned every
  restored slot (`add_pin`) and accepted it, while a fresh grant installed an
  ingress translation and no pin. So a restored lease carried the exact egress
  consequence call/0014 settled against, its arrival was translated by the pin's
  conntrack instead of the ingress map, and the revoke of a restored slot then
  deleted elements the boot never installed.
- **The revoke deleted a pin the grant never creates.** With the ingress design,
  `snat_map` only ever holds the arm's self-pin, so the statement could only
  fail, and it put an error line in the log on every revoke while the design
  never created what it deleted: 54 of them in one session. The statement went
  in the churn fix, and the tolerant `del_pin` call beside it went after the
  same class showed once more: three lines at 21:58, one per lease that expired
  at that minute. The facade installs no pin, so both could only fail, and the
  paths that do pin, the arm and the TCP holder, clean their own. Measured
  after the removal: a lease created and deleted leaves the count unchanged, 57
  before the probe and 57 after, with the last line still the old 21:58 one.

## Mechanism

Two requests from one client that each name no port, on different internal
tuples. The first is granted its slot; the second takes a new slot, and its
supersession key `(0, proto, owner)` matches the first's entry, so that entry
is removed and its slot is revoked with its own bind port. The revoke is
correct for the entry it retires. The loss is that the client's first mapping
is gone while its second lives.

## Blast radius

Every client that asks twice without naming a port. NAT-PMP asks that way by
definition, and a PCP client that wants any port asks that way too, so a client
speaking both protocols lost one mapping per pair of requests. This house met
it while measuring, and read the result as the daemon's own churn until the
instrument was set aside and the failing test written.

## Disposition: fixed

Three changes, at pins `8f179c7` and `0b72060b`, artifact `f4499c2c`:

- `apply_entry` refuses to supersede when `req_ext` is 0: a request that names
  no port carries no handle, so it takes a new entry and leaves the client's
  other mappings alone. The failing test ran first, and its failure named the
  first lease's slot.
- the boot restore installs the grant datapath: the ingress translation and the
  accept element, with no pin. One definition of a slot's datapath, used by both
  paths.
- the revoke's statement list drops the pin delete and the revoke calls nothing
  else that removes a pin, so an expiry reports what it finds and leaves the log
  alone.

## Verification

On the router, at `f4499c2c`, 211 tests in the lane and the same count locally:

- **Coexistence.** Three holding clients from one address, each with its own
  internal port and no port named, leave three leases with three slots and three
  translations:

```host-lint:ignore
leases.tsv   40001 -> 192.168.21.11:41050, 40003 -> 192.168.21.11:41060, 40004 -> 192.168.21.11:41070
accept set   elements = { 40000, 40001, 40003, 40004 }
dnat map     elements = { 40000 : 192.168.21.12 . 40002, 40001 : 192.168.21.11 . 41050, 40003 : 192.168.21.11 . 41060, 40004 : 192.168.21.11 . 41070 }
```

- **Delivery into a listening socket.** A stranger's datagram to a lease's
  external tuple, with a listener bound to the port the lease names:

```host-lint:ignore
sent at 1789941059.793703
RX 19 bytes from 170.9.238.141:41122 at 1789941059.865
src=170.9.238.141 dst=192.168.0.21 sport=41122 dport=40001 packets=1 bytes=47 [UNREPLIED] src=192.168.21.11 dst=170.9.238.141 sport=41050 dport=41122 packets=0 bytes=0
```

That is defect one's socket half, closed.

- **The restore.** With those leases held, the daemon restarted. The restored
  slots came back with their accept elements, their inbound set elements and
  their map entries, `snat_map` stayed empty, and an arrival still landed in the
  listener:

```host-lint:ignore
RX 22 bytes from 170.9.238.141:41123 at 1789941118.179
```

No error line followed that restart, where the same restart used to produce one
for every restored slot.

---

# How both were found

Neither came from a review. The first came from making a measurement the
records asked for and reading its absence honestly: the arrivals were captured
at the WAN and the delivery to the client was not, and that gap was chased
until it named a cause. The second came from the first one's fix: its proof
needed a live lease, the lease kept dying, and the log named the element
deletes that killed it.