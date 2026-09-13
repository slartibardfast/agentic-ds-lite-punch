# Phase E priority: the IGD facade is not required for the console's NAT type on this line

- Status: accepted
- Scope: phase-E priority
- Date: 2026-09-13

## Context and Problem Statement

Plan/0004's phase E is a UPnP IGDv1 facade on br-lan (SSDP, SOAP,
WANIPConnection:1), contemplated in part for the console's NAT state.
The examined console on this line reports PSN NAT Type 2 and Modern
Warfare 2 NAT Open with its SSDP M-SEARCHs going unanswered: there is no
IGD on br-lan and the AFTR offers no UPnP or PCP (call/0011). The Type 2
reading came from hole punching alone through the router's fullcone NAT,
the hub's ds-lite CGNAT, and the AFTR's endpoint-independent
mapping and filtering.

## Decision

Phase E is not required for the console's NAT type on this line and is
deprioritised behind the other v2 work (multi-instance, slot-engine
hardening). It is re-evaluated only when a concrete IGD consumer appears
(a client that reads ExternalIPAddress or requests a static pin through
UPnP and cannot get what it needs another way).

## Consequences

- Positive: the facade stays scoped and unbuilt; the milestone's
  phase-E priority question closes with measured evidence instead of
  speculation.
- Negative: a client on this network that genuinely needs IGD semantics
  (rather than hole punching) will find none until phase E is built; the
  value of the facade for such a client is unchanged from plan/0004.
- Scope: this decides priority, not the facade's design; phase E's
  documented design (slot-0 behaviour, the requested-port lie, M-POST
  parity) remains the plan/0004 reference.