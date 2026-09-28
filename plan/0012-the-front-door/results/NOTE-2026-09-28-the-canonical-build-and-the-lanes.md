# The canonical build, and the lanes that did not match it

Date: 2026-09-28. What was measured, why three builds of one commit disagreed, and what
changed.

## The numbers

The release bumped `0.3.5` to `0.4.0`, staged the published bundle, and built in the
recorded image. The tag's Release lane then built its own binary from the same commit.
Both are that commit's artifact, and they are not the same bytes.

| build | dependency source | `CARGO_HOME` | bytes | sha256 |
|---|---|---|---|---|
| the host's release, which is the canonical one | the staged bundle, `/src/vendor/…` | the image's own | 1,061,552 | `59552c68ac29e8c5ff184358d5e215ccdc30bf2f8b4954353d48470cdf1d2fd5` |
| the tag's Release lane, which published the asset | the registry, `/root/.cargo/registry/…` | the image's own | 1,061,552 | `b7c3d042aa9759a49809e701871e10634ad6117209bac07346879a55db424064` |
| a replication with `CARGO_HOME` overridden | the staged bundle | an empty `/tmp/cargo-home` | 1,061,568 | `1efc39c4d0846b80a4814800f10bda19076f71df50d7dfbbec1b4fcb1b36c07a` |

## The two causes

**The dependency source moves the bytes, as this milestone predicted.** The binaries carry
different dependency paths: the canonical one holds `/src/vendor/tokio-1.53.1/src/lib.rs`,
the lane's holds `/root/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/tokio-1.53.1/src/lib.rs`.
Rust embeds the source position of a panicking call site, a dependency's panics carry its
own path, and so a registry build and a vendored build cannot agree. The `#deps-bundle`
task recorded that the bundle is not byte-neutral; what it did not record is that adopting
it made every registry build stale.

**An overridden `CARGO_HOME` moves them a second time.** The image's
`/root/.cargo/config.toml` names the linker for the target:
`[target.x86_64-unknown-linux-musl] linker = "x86_64-unknown-linux-musl-gcc"`. A container
run with `-e CARGO_HOME=/tmp/cargo-home` reads no config from that path, so cargo links
with another driver: 16 bytes larger, and a third hash. The host's recipe overrides
nothing, which is part of why it is the canonical one.

## Proof that the recipe is a recipe

A fresh copy of the worktree, the bundle staged from the committed lock, and the recorded
command run in the image (`--network none`, the tree at `/src`, `CARGO_HOME` untouched)
reproduced `59552c68…` byte for byte. The same copy with an empty `CARGO_HOME` and the
image's own config copied into it reproduced that hash as well, which is what the bundle
job does now.

## What it changed

Three jobs built something other than the canonical bytes, and one of them published it.

- `release.yml` built from the registry and staged no bundle, so the v0.4.0 asset is not
  the binary the host record anchors.
- `ci.yml`'s `release-build` built from the registry and printed its hash as "the artifact
  hash as `.host-software` records it", for a number the record does not carry.
- `ci.yml`'s `bundle` staged the bundle but overrode `CARGO_HOME`, so its offline proof ran
  on bytes that were not the canonical ones.

All three now stage the bundle the committed lock names and run the recorded command with
the network off. The bundle job keeps the empty `CARGO_HOME`, because its subject is that a
crate absent from the bundle fails rather than arriving from the image's cache, and it
copies the image's cargo config in so the link stays canonical.

## The generated page

The same release left `deploy/man/ds-lite-punch.8` saying `ds-lite-punch 0.3.5`: the bump
changes the crate version, the page is generated from that version, and the release commit
carried the bump without regenerating the page. The tag's lane failed on the difference,
and the published manual page asset carries the old version string. The page in the tree is
regenerated, and the gap is in the release procedure rather than in the generator.

## The gap the record cannot see

Nothing compares the published asset's hash with the hash `.host-software` records. The
gate checks the worktree's artifact and `--verify-build` re-derives the canonical hash from
the pin, so a lane that publishes different bytes is invisible here: the v0.4.0 asset
hashed `b7c3d042…` while the record said `59552c68…` and every check stayed green. The rule
this suggests for the tools is that a component declaring a `deps-bundle` also declares its
artifact-producing lanes, and the gate holds each of them to the recorded recipe.

## What is left

The v0.4.0 release is immutable and its bytes are not the canonical ones, so the coherent
step is a replacement release from the corrected lanes. The pin names the v0.4.0 commit
until that lands, and the gate reports the later commit on `main` as drift.