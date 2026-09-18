# Collision rules for ports nobody allocated: the punch and the lease table

- Status: accepted
- Scope: the ds-lite-punch daemon's port allocation, its punch admissions
  (the observation arm and the allowlist hold) and the datapath they share
  (plan/0009's task `#collisions`)
- Date: 2026-09-18

## Context and Problem Statement

Read this as a specification, because that is what it is: the daemon has two
ways to make a port its own, and until now only one of them had a rule.

The first way is an **allocation**. A control point asks for a mapping, the
slot engine picks a bind port out of its range, and a lease records that the
port is ours. The lease table is the authority, and everything about an
allocation is visible: who owns it, which internal port it carries, when it
expires.

The second way is a **punch**. A datagram leaves a LAN host, the AFTR sees an
inner tuple it has not mapped, and it makes one. Nothing asked us, nothing is
in the lease table, and the AFTR's mapping is keyed on that inner tuple alone,
`(192.168.0.21, R)`. A punch is therefore a claim on a port that no rule
recorded, and it is not visible the way an allocation is: the daemon can see
the post-NAT tuple in its change-data-capture mirror, and it can read the
pre-NAT origin from the connection table, and that is the whole of its view.

Two things follow, and both are collisions rather than cases.

The first is that an allocation can be created on a tuple a punch already
holds. The allocator hands out the lowest free port in its range, and the
range is not reserved from the kernel: a punched flow's port can land inside
it. The AFTR keys on the inner tuple, so a slot bound to the same tuple shares
the AFTR's one mapping with the flow that punched it, and the local inbound
path has two owners for one tuple. Whatever the datapath does then, one of the
two is silently wrong.

The second is what an allocation should do when it discovers a punch on a port
it holds, or when the AFTR answers one external port to two inner tuples. The
first is a race the daemon can lose; the second is an uplink that would be
violating the requirement that a carrier-grade NAT never overload one external
port across two mappings (RFC 6888).

The precedents are all in the RFC series, and none of them resolves a
collision by letting the newcomer displace the incumbent:

- **RFC 5227** (IPv4 address conflict detection) and **RFC 4862** (IPv6
  address autoconfiguration) resolve a collision by *probing before claiming*
  and by the *later* claimant taking another address. The incumbent keeps
  what it has.
- **RFC 4787** requires that an external port already in use is not displaced;
  the second mapping is given a different port, or refused.
- **RFC 6888** requires that one external address-and-port tuple belongs to one
  internal endpoint, so two inner tuples reading as one external port is a
  defect at the mapper rather than a situation to work around.
- **RFC 6887** settles the refusal idiom for the port a client asked for by
  name: refuse with the code that says the request cannot be honoured, rather
  than substituting silently.

## Decision

- **R1. One inner tuple, one local owner.** An allocation's inner tuple
  `(NAT, R)` MUST belong to it alone: a tuple another local flow already holds
  is not available, and no two of the daemon's mechanisms may hold one tuple
  at once. The AFTR keys its mapping on that tuple, so a shared tuple is a
  shared inbound path, which is the situation RFC 6888's no-overloading
  requirement rules out.
- **R2. The incumbent keeps the tuple.** A punch is an incumbent claim: the
  flow exists and the AFTR already maps it. An allocation MUST NOT be created
  on a live tuple that no lease owns. The prober yields; the holder does not
  move.
- **R3. Probe before allocating.** The allocator MUST consult the live
  post-NAT tuple set before it chooses a bind port, and MUST skip any port the
  set holds. This is RFC 5227's probe in the one form this datapath can carry:
  the set is the change-data-capture mirror, which is the same liveness the
  observation arm reads, so both mechanisms see one set of tuples and cannot
  disagree about what is in use.
- **R4. A late collision moves the allocation, never the punch.** When a punch
  appears on a tuple an allocation already holds, the slot MUST re-bind to a
  port the probe finds free, re-learn its tuple by its own write, and leave the
  client's reported port alone, because the reported port is the requested
  label (call/0022). The change MUST be signalled, so a control point that is
  watching learns the tuple moved.
- **R5. Detection is reported, and silence is the forbidden outcome.** A
  collision that the probe steered around, a collision discovered after the
  fact, and two inner tuples reading as one external port MUST each be logged
  with both claimants named. Where the mirror cannot tell two owners apart,
  because both appear as the same post-NAT tuple, the pre-NAT origin in the
  connection table is the tie-breaker.
- **R6. A requested port is a label, not a reservation.** A control point's
  requested external port MUST NOT be treated as a resource that can collide,
  and a second client asking for the same port MUST NOT be refused on that
  ground. This is call/0022's rule, restated here so the two meet: the label
  collides freely, and the datapath port never does.
- **R7. A punch is not an admission.** A live tuple MUST NOT be promoted into
  an allocation because it exists. Admission stays where call/0025 put it: the
  allowlist for the hold, and a control point's own request for a slot. A
  punched flow nobody asked for is left to its owner.
- **R8. The AFTR's assignment is not contestable.** Two inner tuples that read
  as one external port is an uplink defect, and the daemon MUST report it
  rather than accommodate it: a slot's own read is authoritative for that
  slot, and a read that returns a tuple another slot is using is evidence of
  the defect rather than a reason to renumber anything.

## Consequences

- The allocator's view grows by one set, and the two admissions become
  disjoint by that one probe. A port the mirror shows live is not allocated,
  so a punch and a slot cannot share a tuple by accident.
- The cost is a port skipped and, on a fresh allocation only, one read of the
  mirror. A renewal allocates nothing and reads nothing.
- The range stays a budget: 10000 ports against a live-tuple set of a few
  dozen, so steering around them cannot exhaust it.
- The log carries the evidence for R5, which means the rule is auditable
  without a packet capture.

## The two things this decision does not settle

Both are experiments rather than opinions, and both are named here so that
neither is settled by assumption:

- **Whether the local NAPT can punch a port a local socket already holds.**
  If it cannot, R4 is unreachable and the probe alone is complete. If it can,
  R4 is the rule that matters and the re-key path needs an acceptance of its
  own. The experiment: occupy one bind port with a slot, then drive a LAN
  host's new flow through the kernel's port selection, and read whether the
  chosen port is the occupied one.
- **Whether the AFTR ever overloads an external port.** Two slots whose own
  reads return the same external port is the observation R8 names. The
  experiment is passive: the existing per-slot read already records every
  learned tuple, so a repeat across two slots is visible in the log without
  any new probe.