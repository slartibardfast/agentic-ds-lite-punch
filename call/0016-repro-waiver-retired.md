# Repro waiver retired: the crate landed with its build recipe

- Status: accepted
- Scope: reproducibility
- Date: 2026-09-13

## Context and Problem Statement

call/0012 waived the reproducibility lane until the ds-lite-punch crate
migrated into the component repo. The migration landed (component
commit cb7bfb4): the crate is in software/ds-lite-punch with the
intended layout (src/, deploy/, Cargo.toml, .cargo, Cargo.lock), the
build recipe is recorded in .host-software (musl x86_64 toolchain and
build command), and the musl release build reproduces the deployed
artifact byte-identically: the local build's sha256 equals the artifact
hash recorded in the rig's run.json across the soak campaigns. The
migrated source is provably the deployed code.

## Decision

The reproducibility waiver retires. The component's reproducibility
lane is active from this pin: the recipe in .host-software, the artifact
hash recorded, and call/0012 superseded by this decision.

## Consequences

- Positive: the deployed binary trail now pins to a reproducible commit;
  the release lane gate-keeps the artifact hash; future changes to the
  crate flow through the pinned recipe.
- Negative: every future version bump requires the matching tag and the
  release flow; the pre-migration builds (the soak-campaign artifacts)
  are replaced on the next release.
- The crate version remains 0.1.0; a version bump is not part of this
  migration and will be tagged when it happens.