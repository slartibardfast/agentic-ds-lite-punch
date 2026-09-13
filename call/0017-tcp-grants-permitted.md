# TCP grants permitted: the C3 unlock and the protocol-dimension spike

- Status: accepted
- Scope: TCP datapath (constraint relaxation)
- Date: 2026-09-13

## Context and Problem Statement

plan/0004's binding constraints said "UDP only; no TCP grants until the
TCP idle-lifetime test is measured." Two measurements this session
discharge that gate:

- C3 (results/RESULTS-2026-09-13-c3.md): an idle AFTR TCP mapping
  expires in (120, 300] seconds on this node and session, alive at
  120 s of silence and dead by 300 s, double-confirmed by the eth1
  SYN-arrival capture and the probe refused. The AFTR RSTs a dead TCP
  mapping: the one hard dead-mapping signal the UDP path lacks.
- The protocol-dimension spike: the same inner port across UDP and TCP
  received two different external ports on the same session IP, so the
  AFTR keys mappings per (inner ip, inner port, protocol). The TCP pin
  cannot share the UDP pin's external port; the "one external port for
  both protocols" premise is refuted, and the TCP pin publishes its own
  external tuple.

## Decision

TCP grants are permitted. The TCP datapath: a TCP listener on the
slot's pin port accepts AFTR-forwarded inbound connections and splices
them to the slot target; the slot's TCP mapping is maintained by a
STUN-over-TCP keepalive cadence sized under the (120, 300] s bound
(default 60 s) with re-establish on demand; and the slot's external TCP
tuple is discovered and published per protocol. The constraint's "no
TCP grants until the TCP idle-lifetime test is measured" clause is
discharged by this decision.

## Consequences

- Positive: TCP grants enter the slot engine; the facade's paired
  TCP-and-UDP Adds resolve to a real path; the RST dead-signal gives TCP
  prompt death detection that the UDP path lacks.
- Negative: the TCP mapping is expected to expire within minutes of
  silence. Idle spliced connections need the under-120 s liveness the
  design sizes, and a dead mapping re-establishes on demand, publishing
  likely-changed external tuple as a churn event.
- Publication becomes per protocol: the UDP tuple record is unchanged,
  and the TCP tuple gets its own record keyed by the slot.
- Scope: this governing decision is the recorded relaxation; the slot
  range must include the pin port for the static pin to bind (the
  deployment widens the slot range).