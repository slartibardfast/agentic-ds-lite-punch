# The Kani rung runs on a runner, and the tree's own harnesses gate it

- Status: accepted
- Scope: the Kani verification rung's lane for the ds-lite-punch component, and the harness the crate's own set carries
- Date: 2026-10-07

## Context and Problem Statement

[call/0019](0019-facade-kani-deferred-to-larger-host.md) deferred the facade harnesses to a host where CBMC
converges, and left the pre-facade record standing. What that deferral did not say is that no lane existed
at all: nothing compiled the crate under `--cfg kani`, so the harnesses were run by hand, and by the time
this session looked, `engine::verify::exit_due_matches_conditions` no longer compiled, because
[call/0030](0030-a-mapping-ends-with-its-device.md) added `ExitReason::DeviceGone` after the harness was
written. A suite that cannot compile reports nothing, and a rung nobody runs is a claim held by memory
alone.

## Decision

- The Kani rung gets a lane in the component's CI: `workflow_dispatch` and weekly, on a runner.
- The **tree's own harnesses gate**. Each runs under its own bound, so a harness whose search stops
  converging fails its own step instead of holding the run.
- The **facade's eight are measured, not gated**, until a record carries their verdicts. The job reports
  PASS or FAIL-OR-BOUND for each, and the record names the run.
- The Kani version is **pinned** at 0.67.0, because a harness is written against a CBMC search strategy
  and a newer Kani is a new measurement.

## Consequences

- A harness that stops compiling is news within a week, which is what the compile break above needed.
- The facade verdicts that a supersession of call/0019 rests on come from a real run, and the record
  names it.
- The rung costs runner minutes, and the dev host's evenings stay its own.

## What this does not claim

- That the facade harnesses converge on a runner. The lane measures that question.
- That a bounded FAIL means a code defect. A bound is the harness shape's cost, which is what
  call/0019 recorded, and a fix to a shape is a harness change.