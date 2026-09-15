# The facade Kani structural proofs are deferred to a larger host

- Status: accepted
- Scope: the UPnP IGD facade (plan/0007 phase E), the Kani verification lane
- Date: 2026-09-15

## Context and Problem Statement

The E7 milestone clause requires the Kani suites to pass on the facade
tree. On this development host, the one that ran the pre-facade 32 of 32
suite, the facade structural harnesses do not converge under CBMC
0.67.0: the full-byte-space `mpost_post_parity` ran 17 minutes without a
verdict, the printable-byte restriction ran 10 minutes without a
verdict, and the concrete `mpost_post_parity_real_actions` ran 5 minutes
without a verdict. The 2026-09-13 Kani deferral precedent (the suite
moved to a larger host) covers exactly this class: CBMC search time, not
a code defect.

The 2026-09-13 review finding that the pre-fix `mpost_post_parity` claim
was false is closed on this tree: `classify` now runs the GENA markers on
both transports, and the multi-line fabrication corners are pinned by the
unit test `mpost_post_parity_multiline_corners`.

## Decision

- The facade Kani harnesses keep their honest claims: `mpost_post_parity`
  now proofs parity for clean action text (bytes at or above space), and
  the multi-line corners are unit-pinned rather than proof-claimed.
- No harness on this tree is claimed to have passed. The facade Kani
  receipt is re-derived on a host where CBMC converges, before any
  deploy that relies on it.
- Until that re-derivation, the E7 clause is discharged by the unit
  suite (86 tests), the pre-facade 32 of 32 record, and the timed-run
  evidence recorded in RESULTS-2026-09-15-facade-review.md.

## Consequences

- No green-Kani claim is made for the facade tree from this host.
- A full-suite re-derivation runs where CBMC converges; this decision is
  then superseded by a recorded update, never silently re-opened.