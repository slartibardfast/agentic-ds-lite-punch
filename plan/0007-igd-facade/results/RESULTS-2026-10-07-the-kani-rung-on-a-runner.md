# The Kani rung on a runner: the tree's own harnesses verify, and the facade's are in flight

Date: 2026-10-07. Task: [call/0019](../../../call/0019-facade-kani-deferred-to-larger-host.md)'s deferral, and
[call/0050](../../../call/0050-the-kani-rung-runs-on-a-runner.md)'s lane.

## The lane

`workflow_dispatch` and weekly, in the component's CI, with Kani pinned at 0.67.0. The tree's own
harnesses gate, each under its own bound, so a harness whose search stops converging fails its own step
instead of holding the run. The facade's eight are measured in a second job, each bounded, and both
jobs upload a per-harness log.

## The compile break the lane found first

Nothing compiled the crate under `--cfg kani`, so the suite had been run by hand and nothing noticed
when it stopped building. `engine::verify::exit_due_matches_conditions` matched three arms and
[call/0030](../../../call/0030-a-mapping-ends-with-its-device.md) had added `ExitReason::DeviceGone`
afterwards, so the match was no longer exhaustive. The arm is added, and it carries a claim rather than
a silence: `exit_due` reports ownership or staleness, and a device that left is `release_reason`'s
finding.

## The tree's own harnesses, on a runner

Run [37589214079](https://github.com/slartibardfast/ds-lite-punch/actions/runs/37589214079), the
gating job `harnesses`:

```
32 VERIFICATION:- SUCCESSFUL
```

All thirty-two pass, and the slowest takes 22 seconds (`slot::verify::delete_removes_only_target_slot`);
most are under a second. The pre-facade record of 32 of 32 stands, and it is now a lane's verdict
rather than a memory's.

## The facade's eight, in flight

The `facade` job runs each of the eight under a 900-second bound and reports PASS or FAIL-OR-BOUND per
harness. Two runs were started on 2026-10-07 and both were still working when this record was written,
so their verdicts are read from the run's log or its uploaded `kani-facade-logs` artifact.
[call/0019](../../../call/0019-facade-kani-deferred-to-larger-host.md) therefore stays accepted: the
deferral is discharged by those verdicts, and a facade harness that bounds is a harness-shape finding
rather than a runtime defect.

## What the lane settles

- The crate compiles under `--cfg kani`, and a harness that stops compiling is news within a week.
- The tree's own set is cheap enough to gate on every weekly run, and its verdicts come from a run.
- The facade question has an instrument, and its answer lands in this room.