# The artifact lanes build the canonical recipe

- Status: accepted
- Scope: which build produces the bytes the release anchors, and what every lane in
  the component that publishes or prints that hash has to run
- Date: 2026-09-28

## Context and Problem Statement

`call/0039` recorded a `deps-bundle`, so the host's release stages the vendored
dependencies and builds with the network off, and the hash it records is that
build's. The component's lanes were never told. The v0.4.0 release published a
binary hashing `b7c3d042…` while `.host-software` recorded `59552c68…`, and the
measurement in plan/0012's results separates the two causes.

A dependency's source path reaches the binary, because Rust embeds the position of
every panicking call site: a build over `/src/vendor/tokio-1.53.1/src/lib.rs` cannot
match one over `/root/.cargo/registry/src/index.crates.io-…/tokio-1.53.1/src/lib.rs`,
and the vendored build is 16 bytes larger in this crate. The pinned image also names
the linker in its own cargo config
(`[target.x86_64-unknown-linux-musl] linker = "x86_64-unknown-linux-musl-gcc"`), so a
container run with `-e CARGO_HOME=/tmp/cargo-home` loses that config and links with
another driver: a third hash from the same source.

None of this is visible to the gate. `--verify-build` re-derives the recorded hash
from the pin and the worktree's artifact is compared beside it, so a lane that
publishes different bytes passes every check the host runs.

## Decision

The canonical recipe is the one the host's release performs: the recorded `build`
command, inside the digest-pinned image, over the dependency bundle the committed
`deps-bundle.lock` names, with the network off, and with `CARGO_HOME` untouched so the
image's own cargo config supplies the linker. A lane that publishes the release asset,
or that prints the hash `.host-software` records, runs that recipe and nothing else. A
lane whose subject is the bundle's completeness may empty `CARGO_HOME`, and it copies
the image's cargo config into it so its bytes stay canonical.

## Consequences

The release asset can be the recorded binary, which is what `call/0032` claims of it:
until the lanes matched, that claim held only for the host's own release build.

The component carries one recipe in three jobs rather than one shared script, so a
later change to the recipe has three places to change. The host's own `release` verb
owns the string in `.host-software`; the jobs mirror it by hand, and a divergence
shows up as a lane hash that differs from the record.

The v0.4.0 release keeps its published bytes, because the repository's releases are
immutable and the tag is published. The pin names that commit until a replacement
release from the corrected lanes moves it, which plan/0012 records.

## What this does not claim

It does not claim the gate can see a lane's bytes. The published asset's hash is
compared with the record by a reader, or by a rule the host tools do not have yet:
nothing in `software --check` or `--verify-build` reads a release asset.