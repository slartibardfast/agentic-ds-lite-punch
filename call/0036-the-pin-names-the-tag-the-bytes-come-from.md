# The release's bytes move with the version, so the pin names the tag

- Status: accepted
- Scope: how a release is cut for this component: the order of the bump, the
  tag, the pin and the recorded hash, and what a digest re-derivation describes
- Date: 2026-09-23

## Context and Problem Statement

The documentation shipped as `v0.2.0`, and that release exposed a change in
this component's build. Up to `0.1.5` a version bump did not move the artifact,
because nothing compiled the version in: the pinned commit and the tagged bump
commit produced the same bytes, and one recorded hash covered both. `v0.2.0`
added `--version`, which prints the crate version, so the string is compiled in
and the bytes now move with every bump.

The host's reproducible lane reported it as a drift when the pin ran ahead of
the recorded hash, in the line it printed:

```host-lint:ignore
DRIFT    ds-lite-punch rebuild is 0bdb6b926485 but recorded a452cf38c9c7 — NOT reproducible
```

## Decision

A release runs in one order: apply the bump, commit it, tag that commit, and pin
the tagged commit with the hash its build produced. The pin names the commit the
tag names, because a record that names a different commit than the artifact's
source describes bytes nobody ships.

The hash comes from the lane that builds the tagged commit, and it is checked
twice more before it is recorded: the component's own lane prints the hash for
the same commit, and an anonymous fetch of the release asset is hashed after
download. Three builds agreeing is stronger evidence than one re-derivation, and
all three ran inside the toolchain the record pins. For `v0.2.0` all three
produced `924281b2f6b544d6da6b17dddd312978560cdb467df58a96f15e9016bbe72db9`.

The release phase is one dispatch per release. Its version comes from the
manifest plus the change class, so a dispatch made after a release is complete
proposes the next version and derives the digest of a bump that exists only in
that run. A second dispatch made after `0.2.0` shipped reported
`0.2.0 -> 0.3.0` with a digest for a `0.3.0` source. That proposal was not
applied, and the release receipt was recorded from the release's own evidence.

## Consequences

The pin lags the working tree between a release and the next bump, which
`software --check` reports as DRIFT against the component's worktree. That
report is the record saying a release is owed, and it clears when the pin and
the hash are set in one commit.

A release that removes a flag or adds one is a minor bump, and the tool maps
either change class to one. Writing the pin and the artifact hash together is
what keeps the lane from ever reading a pair that describes two sources.