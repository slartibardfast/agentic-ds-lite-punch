# Route the console's whole traffic through the Virgin line (eth1)

- Status: accepted
- Scope: console egress
- Date: 2026-09-13

## Context and Problem Statement

The A2 acceptance (plan/0006) needs the console's PSN traffic to present
on the relay line: eth1 to the Virgin hub (192.168.0.1), through the
ds-lite AFTR, on the pinned tuple. The router's default route egresses
the vdsl4 PPPoE (metric 16) and the eth1 path is fallback (metric 128),
so a default-routed console would ride the vdsl4 line and the relay
would never see its flows. Two mechanisms could put the console on the
Virgin line: a policy route for the console's whole traffic, or routing
for the PSN address ranges only.

PSN is served through fronting infrastructure whose address ranges churn;
the range-scoped approach depends on an external list this project does
not maintain. The policy-route approach needs one rule keyed on the
console's reserved source address and is robust to whatever PSN resolves
to.

## Decision

Route the console's entire traffic through eth1 with a pbr rule keyed on
the console's DHCP-reserved source address, following the fwmark idiom
already on the router (a marked lookup table whose default is via
192.168.0.1 dev eth1). The vdsl4 line stays the probe and oracle path
only. Non-folded console flows (PSN store, downloads, DNS) ride the
hub's normal CGNAT; the folded UDP flows (target 3478/3479) present as
the pin tuple.

## Consequences

- Positive: one static rule, no dependency on PSN infrastructure address
  lists; robust to range churn; the console's whole egress sits on the
  line the relay can pin; the identical pattern the router already uses
  for tagged clients.
- Negative: the console's NAT-probe flow may not be a folded port, in
  which case PSN's type reading reflects the hub's NAT, not the relay
  pin. The A2 verdict therefore attributes the probe's path from the
  captures (folded egress as 192.168.0.21:40000 versus hub-NAT egress)
  and records which path the type reading reflects, per plan/0006
  task #a2-verdict.
- Scope: the rule binds to the reserved console address only; other LAN
  clients keep their existing routing. Rollback is one rule deletion plus
  the relay retarget; the mapping resets by design, one port-reuse
  observation.