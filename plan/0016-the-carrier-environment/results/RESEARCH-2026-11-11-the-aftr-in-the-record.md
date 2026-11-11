# Research: the AFTR in the record, and what a high-fidelity fake must implement

Date: 2026-11-11. Task: `plan/0016#the-fidelity-model`. The question: what must a
simulated carrier do so the end-to-end environment is a faithful stand-in for the
Virgin Media ds-lite line? Every row below carries its source, because a fake
carrier is a claim about someone else's machine.

## The architecture, as measured and as specified

The hub (an F3896LG) is the RFC 6333 B4: a transparent encapsulator that NATs
nothing, polices martian IPv6 sources on the LAN (measured), and carries the
subscriber's single /128 softwire toward the provisioned AFTR
(`aftr01.upc.ie` → `2001:730:2000:2::353`). The AFTR is the sole NAT44 device;
its binding table is extended with the B4's source IPv6 address, which is how it
disambiguates overlapping customer IPv4 space (RFC 6333 §6.6). An AFTR MUST
conform to RFC 4787 (UDP), RFC 5382 (TCP) and RFC 5508 (ICMP) (RFC 6333 §8.2),
and the AFTR runs no PCP and no UPnP-IGD (measured; the possibility space's
closed doors).

## The fidelity model: every behaviour, with its source

| # | Behaviour | Value | Source |
|---|---|---|---|
| 1 | UDP mapping | endpoint-independent (EIM, RFC 4787 REQ-1) on the mapping the line holds; an external tuple also allocated per destination, and the tuple that matters to a peer is the one the line's poke toward *that peer* produced | measured (the front's tuple differs from the STUN tuple; the poke's source is authoritative per peer) |
| 2 | Admission | source-restricted: only from a peer address the line has spoken to on the same protocol, and the spoke must have been *answered*; a refused or dropped poke admits nothing | measured ([the rule table](../../../plan/0014-the-fronts-legs/results/NOTE-2026-10-06-the-admission-rules.md), [the first pass](../../../plan/0014-the-fronts-legs/results/NOTE-2026-10-06-the-admission-rules-so-far.md), [the stranger probe](../../../plan/0010-the-filtering-proved-and-watched/results/RESULTS-2026-09-20-stranger-probe.md)) |
| 3 | Admission scope | the peer's address, any of the peer's ports | measured (an arrival from a never-poked port of an admitted peer crossed) |
| 4 | Protocol scope | a UDP spoke admits UDP; a TCP arrival wants a TCP spoke | measured ([the TCP leg](../../../plan/0014-the-fronts-legs/results/NOTE-2026-10-06-the-tcp-leg-closes.md)) |
| 5 | Idle death | the mapping lapses with no signal, an order of magnitude under the RFC 4787 REQ-5 two-minute floor (the relay's 2 s cadence is built around it) | measured (plan/0004's timeout measurement); the floor is RFC 4787 REQ-5 |
| 6 | Silent expiry | no ICMP, no RST, no log: the watch exists because the lapse is invisible | measured ([the watch](../../../plan/0010-the-filtering-proved-and-watched/README.md)) |
| 7 | ICMP | receipt of ICMP does not terminate the mapping | RFC 4787 REQ-12 |
| 8 | Hairpinning | MUST be supported (REQ-9) | RFC 4787 |
| 9 | TCP filtering | endpoint-independent filtering proven end to end for TCP | measured + RFC 5382 (an AFTR MUST conform) |
| 10 | Extended binding | the binding is keyed with the B4's source IPv6 | RFC 6333 §6.6 |
| 11 | Port assignment | never "port overloading" per destination pair (REQ-3); sequential allocation observed but never built on | RFC 4787 REQ-3; measured (the zero-cost probe) |

The one deliberate divergence from the RFCs, and the most important row: the real
AFTR violates REQ-5's timer floor in normal operation, so a fake that honours the
two-minute floor would be a fake of a different carrier. The timer is a knob set
to the measured value.

## What today's incident adds to the model

The line left ds-lite mode on or before 10 November (the pppoe default route at
metric 16 beats the hub route; no tunnel interface is up; the daemon's own
front-view reports `84.203.115.61:40000` from the poke). Two things follow for
the environment and one for the product:

- The environment needs a **mode switch**: the same harness must simulate the
  ds-lite path and the native-NAT path, because the daemon is now exercised
  under both and the record must not assume either.
- The native path's arrivals land on a different interface than the daemon's
  nft rules key on (`eth1`), and nothing answers them. That is a product
  finding: the WAN interface is a hard-coded assumption today, and the
  environment should be able to reproduce the failure it causes.
- The front's relay followed the poke's source automatically, which is the
  two-views design working across a line-mode change; the TCP half is unrouted
  because no TCP slot exists on the native path yet.

## The environment design this model implies

Kernel-real, in network namespaces, one per actor:

- **b4**: the real daemon binary, bound to its inside address, carrying its own
  nft datapath; its WAN interface is named as the scenario needs.
- **hub**: the transparent encapsulator — ip6tnl toward the AFTR namespace in
  the ds-lite scenario, plain routing in the native scenario, with the martian
  policing that was measured.
- **aftr**: the simulated carrier. The data plane is Linux ip6tnl decapsulation
  plus an nftables NAT44 (the technique `jeduardo/dslite-server` uses, and the
  ISC AFTR implements in C); the policy plane is a small userspace control
  process implementing rows 1-6: per-destination tuple allocation, admission
  driven by an answered-poke table, and the short silent timer. The timer, the
  tuple policy (EIM versus per-destination) and the mode are scenario knobs,
  each defaulted to the measured value.
- **front**: the relay plus the rendered nginx from `test-local.sh`, on the
  AFTR's public side.
- **service and internet**: the target service, and the external peers
  (the client, the stranger).

The harness asserts the whole exchange per scenario: both protocols, quiet
survival across the timer, expiry without signal, churn, tuple moves, the
stranger's refusal, and the line-mode switch itself.

## What this research does not settle

The restructure-or-waive decision for the four bounded facade harnesses is
untouched by this. The real AFTR's vendor and code are unknown (only its FQDN is
provisioned), so the model is fitted to measurements, and where a measurement and
an RFC disagree, the measurement wins and the RFC row records the floor the real
device breaks.