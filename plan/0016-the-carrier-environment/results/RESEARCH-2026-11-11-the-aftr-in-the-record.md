# Research: the carrier model, generalised

Date: 2026-11-11. Task: `plan/0016#fidelity-model`. The question: what must a
simulated carrier implement so the end-to-end environment is a faithful stand-in
for a carrier-grade NAT behind ds-lite, and for the lines that stop being one?
The answer is a parameterised model from the RFC behavioural taxonomy, with
carrier profiles as configurations. A fake built around one ISP's idioms would
be a fake of one machine on one day, and the record itself shows why that fails:
the measurements from two eras of the same line disagree about the mapping
model, and the disagreement is the kind of thing the harness should settle, not
hide.

## The general model: the knobs

An AFTR is a NAT44 device with an IPv6-extended binding table. RFC 6333 §6.6
extends the NAT binding table with the B4's source IPv6 address, and §8.2
requires an AFTR to conform to RFC 4787 (UDP), RFC 5382 (TCP) and RFC 5508
(ICMP). Those RFCs define the behavioural space the policy plane exposes as
configuration:

| Knob | Values | RFC |
|---|---|---|
| mapping behaviour | endpoint-independent (EIM), address-dependent (ADM), endpoint- and port-dependent (EDM, symmetric) | RFC 4787 REQ-1 and the definitions §4.1 |
| filtering behaviour | endpoint-independent (EIF), address-dependent (ADF), address- and port-dependent (APDF) | RFC 4787 §4.3 |
| port assignment | port preservation, random, sequential, per-destination | RFC 4787 REQ-3, REQ-4 |
| UDP idle timer | seconds; the RFC floor is two minutes (REQ-5) | RFC 4787 REQ-5 |
| TCP idle timer | seconds; the RFC floor is 2 h 4 m | RFC 5382 |
| refresh direction | outbound only | RFC 4787 REQ-6 |
| hairpinning | on, off | RFC 4787 REQ-9 |
| ICMP ends a mapping | never | RFC 4787 REQ-12 |
| mapping protocols | PCP, NAT-PMP, UPnP-IGD: each on or off | RFC 6333 §8.5; measured: none |
| extended binding | the binding keyed with the B4's source IPv6 | RFC 6333 §6.6 |
| the B4 | a transparent encapsulator, with martian-source policing | measured (plan/0004's hard constraints) |
| line mode | ds-lite tunnel, native NAT44 | measured (the November change) |

## The profiles

A profile is a configuration of the knobs, and the harness runs its scenarios
across profiles, because the daemon is used on one of these lines and should
behave correctly on the others inside its design envelope.

### `vm-dslite`, the measured profile and the default

The Virgin Media ds-lite line (`aftr01.upc.ie`), as measured across plan/0004,
plan/0010, and plan/0012 with plan/0014:

- UDP filtering: address-dependent, and port-independent toward a contacted
  address ([the 2026-09-17 session](../../../plan/0004-ds-lite-punch/RESULTS-2026-09-17-switch-nat-type.md):
  unsolicited inbound from a never-written port was delivered).
- Admission requires an answered spoke ([plan/0014's rule table](../../../plan/0014-the-fronts-legs/results/NOTE-2026-10-06-the-admission-rules.md):
  a refused or dropped poke admits nothing), scoped to the peer's address
  ([an arrival from a never-poked port crossed](../../../plan/0014-the-fronts-legs/results/NOTE-2026-10-06-the-admission-rules.md)).
- Protocol-scoped spokes: a UDP spoke admits UDP; a TCP arrival wants a TCP
  spoke ([the TCP leg](../../../plan/0014-the-fronts-legs/results/NOTE-2026-10-06-the-tcp-leg-closes.md)).
- The idle timer is an order of magnitude under the two-minute floor, expiry is
  silent, and the relay's cadence is built around it (plan/0004's measurement).
- No mapping protocol runs on the AFTR (plan/0004's closed doors).
- **The open conflict, recorded rather than resolved**: plan/0004's session
  characterises UDP mapping as EIM (one local port served eight peers with
  symmetric volume), while the front era measured an external tuple per
  destination. Both readings have evidence on tape, and the distinguishing
  variable is unestablished, and a candidate mechanism is sitting in the path:
  the path. The harness's differential run is the instrument that settles this:
  the same inner endpoint toward two destinations, with the fold out of the path,
  compared on the wire.

### `rfc-bcp`, the reference profile

RFC 4787's best case: EIM + EIF, the two-minute UDP floor, hairpinning on, no
protocol scoping, the RFC 5382 TCP floor. This is the profile the daemon's
documentation claims to serve.

### `symmetric`, the hardest profile

EDM + APDF with per-destination tuples and short timers: the shape plan/0004's
investigation named as the one that would have forced the VPS-relay fallback.
The daemon's own envelope is defined by how much of this profile it survives.

## Today's incident, as a scenario

The line left ds-lite mode on or before 10 November: the pppoe default route at
metric 16 beats the hub route, no tunnel interface is up, and the daemon's own
front-view reports `84.203.115.61:40000` from the poke. Two things follow:

- **Line mode is a knob** (ds-lite tunnel, native NAT44), and the harness runs
  both, because the daemon is now exercised under both.
- The native path's arrivals land on an interface the daemon's nft rules do not
  key on, and nothing answers them. That is a product finding: the WAN
  interface is a hard-coded assumption today, and the native scenario exists to
  reproduce it as a test, with the interface-name fix developed against it.
- The front's relay followed the poke's source across the change, which is the
  two-views design holding; the TCP half is unrouted because no TCP slot exists
  on the native path yet.

## The environment design this model implies

Kernel-real, in network namespaces, one per actor:

- **b4**: the real daemon binary, bound to its inside address, carrying its own
  nft datapath; its WAN interface is named as the scenario needs.
- **hub**: the transparent encapsulator: the ip6tnl encapsulation toward the
  AFTR namespace in the ds-lite scenario, plain routing in the native scenario,
  with the martian policing that was measured.
- **aftr**: the simulated carrier. The data plane is ip6tnl decapsulation plus
  an nftables NAT44 (the technique `jeduardo/dslite-server` uses, and the ISC
  AFTR implements in C); the policy plane reads a profile and implements the
  knobs: the mapping and filtering behaviours, the per-destination allocation,
  the timers with silent expiry, the answered-poke precondition where the
  profile sets it.
- **front**: the relay plus the rendered nginx from `test-local.sh`, deployed by
  the repository's own pipeline, on the carrier's public side.
- **service and internet**: the target service, and the external peers (the
  client, the stranger).

The harness asserts the exchange per scenario **and per profile**: both
protocols through the mapping, quiet survival across the timer, expiry without
signal, churn, tuple moves, the stranger's refusal, the line-mode switch, and
the differential probe that settles the open mapping conflict.

## What this research does not settle

The restructure-or-waive decision for the bounded facade harnesses is untouched.
The real AFTR's vendor and code are unknown, so the profiles are fitted to
measurements and to the RFCs, and where they disagree the record says so instead
of picking a winner by authorship. The open mapping conflict is settled by a run,
not by this document.