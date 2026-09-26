# The control channel carries a TLS client, and the build carries a bundle

- Status: accepted
- Scope: what the daemon's control channel costs the binary: the dependency it
  adds, the hermeticity of the build, and the record that anchors both
- Date: 2026-09-26

## Context and Problem Statement

`call/0038` makes the daemon the control point of a front, so it opens HTTPS to an
endpoint on a public address, and it authenticates itself there with an identity
of its own. The crate depends on `tokio` and `libc` and nothing else, builds
musl-static for a router, and is anchored in `.host-software` by a pinned
toolchain image and an artifact hash that the host's lane re-derives on every
push.

Two facts decide the shape. A system TLS library is not available to a
musl-static router binary in any form worth having, so the client has to be a
crate compiled into it. And the recorded build runs
`cargo build --release --locked` inside the pinned image, with no `deps-bundle`
recorded anywhere: the dependency sources arrive from the network during the
build rather than from a pinned bundle. The methodology asks a component that
ships a static release binary to reproduce its artifact offline from pinned
inputs, and it gives that property one mechanism, a hash-pinned dependency
bundle. Hermeticity is a facet of reproducibility rather than a second property,
so one record covers both.

## Decision

The daemon carries its TLS client in the binary: a pure-Rust implementation,
pinned by the lock file and by the artifact record, rather than anything that
reaches for a system library at run time. It presents a client certificate and
its key, held as files that the environment names, so the front can be certain
who is pushing. The trust anchor for the front's own certificate is a file the
operator places, with the public roots as the fallback.

The build gains a hash-pinned dependency bundle, recorded in `.host-software` as
`deps-bundle = <url> <sha256>`. That is the mechanism the host's `--verify-build`
already performs for a component that carries one: a single download whose digest
is checked, the vendored sources staged, and the build run with the network off,
so a missing member of the bundle fails the build instead of being fetched
silently.

## Consequences

The artifact hash moves, and the ordinary release order carries it: bump the
version, commit, tag, and pin the tagged commit with the hash its build produced
(`call/0036`). The binary grows, which a router notices in flash and RAM, so the
size is a measured number in the release record rather than an expectation.

The help text and the manual page gain the new keys, and both come from the one
definition in `tools/argdoc`, so the generated pair moves with them and the
lane's diff check holds them together.

The bundle is not the waiver. `call/0016` retired this component's
`repro-waiver`, and the methodology offers a waiver to pre-existing software
converging on reproducibility. Vendoring a TLS crate and its dependencies offline
is feasible here, so this component takes the bundle.

The record's build line gains a bundle beside its command, which is a change to
`.host-software` and therefore to the anchor the host's reproducible lane
re-derives. The lane is the check: it rebuilds from the pin
inside the recorded image and compares the artifact against the hash the record
carries.