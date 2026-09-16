# Deferred ssdp:all classification via bounded discovery bursts

- Status: accepted
- Scope: plan/0008 (the adaptive UPnP IGD v1/v2 compatibility facade),
  device discovery policy; the software's SSDP responder
- Date: 2026-09-16

## Context and Problem Statement

The original plan text held an absolute rule: a server MUST NOT make
the semantic result of an already received M-SEARCH depend on a future
M-SEARCH that has not yet arrived, and classification MUST be based on
the ST of the individual search. Under that rule, `ssdp:all` was fixed
to the v1 compatibility facade for every control point, and an IGD:2
response was reserved for explicit `IGD:2` searches.

Three facts changed the picture. The product research found the
Livebox Play (the Nokia/linux-IGD v2 lineage packaged by SoftAtHome)
serves `ssdp:all` from its PRIMARY v2 description in production, the
lower v1 description being reserved for explicit lower-version STs.
The Xbox-class evidence shows a demonstrably sensitive IGD1-first
control point succeeding against the v1 presentation. And the
practical split is otherwise binary: a modern client probes `IGD:2`
explicitly and can see v2 anyway, so keeping `ssdp:all` permanently at
v1 buys Xbox compatibility at the cost of presenting a weaker facade
to capable clients that happen to begin with a generic search.

## Decision

- `ssdp:all` response selection is deferred for a bounded,
  per-control-point discovery-coalescing window:
  `DISCOVERY_DEBOUNCE = 1 s`.
- One second is the UDA default for a missing MX, so the server may
  assume it as the MX floor; the window therefore never exceeds any
  valid MX of the pending `:all` search, and the deferred response
  always lands inside its own response window.
- If an explicit `IGD:2` search from the same control point is
  observed inside the window, the pending `:all` search AND the
  `IGD:2` search are both answered from the v2 facade. Otherwise the
  pending `:all` search is answered from the v1 compatibility facade
  at the window deadline.
- An explicit `IGD:1` search never influences the classification; it
  is answered from the v1 facade independently.
- Burst state is keyed by control point for the window's lifetime
  only; no long-lived client database is created, and no state
  survives the window.
- This is deliberate product behavior: the window makes `ssdp:all` a
  capability-probing request with the explicit `:2` search as the
  disambiguator. It is a recorded, bounded deviation from the strict
  no-cross-request-negotiation reading of UDA; the earlier absolute in
  plan/0008 section 12 is superseded accordingly.

## Consequences

- Deterministic within the window: a burst resolves to
  `seen_v2 ? v2 : v1`, and `:1` is provably inert in the decision.
- The test matrix gains the burst cases (ssdp:all alone,
  ssdp:all-then-IGD:2, ssdp:all-then-IGD:1) and a deadline assertion
  on every response.
- The bench phase records how Xbox-family and modern clients behave
  against the concrete one-second policy, and it records the
  Livebox-style v2-on-generic-discovery outcome for v2-capable bursts.