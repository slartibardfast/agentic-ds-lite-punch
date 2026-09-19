# The builder of record is the CI lane, and a deployment takes its artifact

- Status: accepted
- Scope: how ds-lite-punch is built and shipped. Which environment produces the
  artifact that may be deployed, what the recorded hash anchors, and what a
  local build is for
- Date: 2026-09-19

## Context and Problem Statement

The record in `.host-software` anchors an artifact hash, and the point of that
anchor is that the deployed binary can be rebuilt from the pin and compared
with it. Two environments were in a position to do the rebuilding, and they did
not agree.

The pinned toolchain is a digest-pinned container image
(`ghcr.io/rust-cross/rust-musl-cross@sha256:ce75e917...`), which the host's
`--verify-build` clause and the component's continuous integration lane both
run. This development host has no container runtime, so its builds use the
ambient toolchain, and the two produce different bytes: the record anchors
`ab0f9bd517ef...` while the development host's build of the same pin hashes
`8e21070e3a42c5240aed01900af3c451095bff263a28d36438e4aae403a814be`. On
2026-09-19 the binary on the test router was the second of those, because the
deployment had been made from the development host, so the record and the
running daemon disagreed about what was running and no receipt could tell.

The reproducibility lane had been failing on every push since it was written,
which is how that divergence survived: see the report filed as
`connollydavid/host#21`. One choice decides the alignment: lower the pinned
toolchain to whatever this host happens to have, or raise this host's output to
the pinned toolchain's. The operator ruled for the second, on the grounds that
reproducibility has to hold widely, and a build that depends on one machine's
ambient compiler holds only on that machine.

## Decision

- **The pinned toolchain is the only environment whose output may be
  deployed.** It is a digest-pinned container image, recorded in
  `.host-software`, and a target triple or an ambient compiler is not a
  substitute for it.
- **The component's lane builds it and publishes it.** The lane runs the test
  suite and the release build inside that image, prints the artifact line in
  the form the record uses, and uploads the binary and the line. A job whose
  upload produces nothing fails, because an upload that silently does nothing
  would read as success.
- **A deployment installs the artifact from a lane run, and checks its hash
  against the record before the daemon is started.** A mismatch refuses the
  deployment rather than replacing a running binary with bytes the record does
  not describe.
- **A local build is a development aid.** It is never a deployment source, and
  it is never the basis of a recorded hash. This development host having no
  container runtime is a property of the host, not a gap in the record.

## Consequences

- The record, the lane's output and the running daemon are the same bytes. That
  was verified on 2026-09-19: the pipeline's artifact hashes to the recorded
  anchor, the router was installed from it, and its datapath confirmed a slot
  tuple in the second it started.
- The artifact is retrievable rather than only described. A deployment takes
  the bytes from the run that built them, so the evidence that a release input
  is sound is a run and a hash rather than a claim.
- Rebuilding from the pin is possible for anyone with the repository and a
  container runtime, because the recipe names a public image by digest and a
  locked dependency graph. How widely that reaches is bounded by the
  repository's visibility, which is the operator's call rather than this
  decision's.
- A local build loses its authority. What it is good for is iteration, and the
  only way it becomes deployable is by producing the same bytes as the pinned
  toolchain, which on a host without a container runtime it does not.
- The cost is that a release step now depends on the forge being reachable, and
  a deployment carries a run identifier as part of its provenance.