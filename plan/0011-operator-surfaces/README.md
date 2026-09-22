# Milestone: the operator's surfaces

**Status:** done, 2026-09-22. The component's `--help` was one line of flag
names, and the repository had no page for its operators. Both are closed, and
the release `v0.2.0` carries the kit: the binary, the manual page, and the line
that records the hash. The record is
`results/RESULTS-2026-09-22-operator-surfaces.md`.

## What this milestone is

An operator who takes the release artifact has the binary and nothing else. The
daemon's real configuration surface is `/etc/ds-lite-punch.env`, and the
repository explains it in comments inside that file. Three keys the init script
honours, `SLOT_RANGE`, `MAX_SLOTS` and `MAX_MAPS_PER_CLIENT`, appear in no
shipped file at all. Nine log events arrive in syslog with names no page
explains, and the state directory holds four files whose meaning is in the
source. An operator also needs a supported upgrade path and a way to ask the
daemon what state it is in.

That is the gap this milestone closes. The work is documentation and packaging
around a program whose behaviour is settled: the help text, the manual page, the
operator pages, the site, and the lanes that keep the four together.

The register is the one the component's README already uses, ASD-STE100
Simplified Technical English, and the reader is a stranger who runs some other
ds-lite line. No page may assume this line's addresses.

The personas are the ones this host carries. The operator needs a page that
answers a question without a session, and the agent needs the pages held in step
with the program by a check it can re-run.

## Build sequence

Nine tasks. The first pins the CLI definition the rest of the milestone quotes,
the middle six produce the surfaces, and the last two hold them and record them.
Every task carries verify and inputs; the mechanical verifies re-run at the
gate.

### Pin the CLI definition and generate the surface {#argdoc}

- verify: the generator rewrites its two outputs and leaves the working tree
  clean, and the root `Cargo.toml` and `Cargo.lock` are byte-identical to their
  state before the crate was added
- inputs: the parser's flag set in `src/main.rs` (`parse_args_from`), the flag
  names in `deploy/ds-lite-punch.init`, the musl pin in `.cargo/config.toml`

A dev-only crate at `tools/argdoc/` carries a clap definition of the command
line, with `clap_mangen`. It is an authoring tool: it writes the help text and
`deploy/man/ds-lite-punch.8`, and nothing in it is linked into the binary the
router runs. The crate declares its own empty `[workspace]` table, so the
shipping crate's dependency graph and lock file do not move and the recorded
artifact hash cannot change for this reason alone. One trap is recorded because
it costs an hour: `.cargo/config.toml` sends every cargo command in the tree to
musl, so the generator names its target explicitly, which is
`x86_64-unknown-linux-gnu`.

### Ship the authored help and the version flag {#help}

- depends: #argdoc

- verify: `ds-lite-punch --help` prints the generated text with a description
  for every flag, `ds-lite-punch --version` prints the crate version, an
  unknown flag prints `error:` with the same text and exits 2, and a test
  asserts that the flags the parser accepts and the flags the help names are one
  set
- inputs: the generated help text, `usage()` and the error path in
  `src/main.rs`, the test seam `parse_args_from`

The binary prints the generated text through `include_str!`, so the help an
operator reads and the manual page come from one definition. The diagnostic flag
`--ct-probe` stays hidden on purpose. The coverage test is the seam that keeps
the definition and the parser honest, because the definition is a second copy of
the command line and a second copy drifts.

### Ship the manual page {#man}

- depends: #argdoc

- verify: `groff -man -ww -Tascii` reports nothing on
  `deploy/man/ds-lite-punch.8` and `man --warnings` agrees, the page names every
  flag the parser accepts, and the sections the generator appends survive a
  regeneration
- inputs: the `clap_mangen` output, the init script's flag mapping, the carrier
  numbers measured in plan/0009, the comments in `deploy/ds-lite-punch.env`

Four sections cannot come from a clap definition and are appended by the
generator so that regeneration keeps them. ENVIRONMENT carries every key of the
env file and the three keys only the init script reads. FILES names the env
file, the allowlist (call/0025), the DeviceProtection seed (call/0023) and the
state directory. LOG EVENTS gives each event name with its fields. LIMITS
carries the measured carrier behaviour and the one caveat an operator must know
about the ruleset.

### Install and release the operator kit {#packaging}

- depends: #man

- verify: `sh -n` accepts the installer, the page is placed at
  `/usr/share/man/man8/ds-lite-punch.8` with mode 644 and its contents intact,
  the release lane refuses an empty page and names it among the assets, and the
  rendering is checked on a workstation and in the lane, because the router
  carries no manual reader
- inputs: `deploy/install.sh`, `.github/workflows/release.yml`, the release
  lane's existing two assets, the router's applet list

The installer also prints the steps an operator takes after it: write the
allowlist, seed the first DeviceProtection identity, restart, and read the
mapping's tuple. The release attaches the page beside the binary and the
recorded hash line, so the bytes a stranger fetches and the manual for those
bytes travel together.

Measured while doing this, and it changes what the page is for: the router
carries no `man`, no `mandoc`, no `nroff` and no `/usr/share/man` directory at
all, so the page is placed for a reader who pulls it off the box or takes it from
the release. The reader the box itself has is `--help`, which prints the same
generated text. Its place at that path is still worth keeping, because it is
where an operator looks for it, and the operator pages say where the two readers
are.

### Write the operator pages {#operator-docs}

- depends: #packaging

- verify: `docs/operators/` carries the five pages, every command and path in
  them was run against the router during the work, every link resolves, and the
  prose lane reports clean over them
- inputs: the generated help and manual page, `deploy/ds-lite-punch.init`,
  `deploy/ds-lite-punch.env`, the state directory `/run/ds-lite-punch`, the
  event names in `src/obs.rs` and `src/carrier.rs`

The five pages are `install.md` (preconditions, the toolchain the bytes come
from, the hash check against the host record, the installer, the first start,
the DeviceProtection seed), `configure.md` (the env file key by key with units
and defaults, the three keys the shipped file omits, the single-map form, the
facade ports, the hold's packet budget), `operate.md` (the tuple file, the state
files, the log events, the datapath table, and how to check a mapping from
outside the line), `upgrade.md` (the release flow, the rollback, and the
uninstall the init script's stop path already supports) and `troubleshoot.md`
(the measured failure classes: a refused start under procd, a firewall reload
that takes the daemon's rules with it, a silent watch that is the helper, and a
mapping the carrier has dropped).

### Publish the component's site {#site}

- depends: #operator-docs

- verify: the component's Pages address answers 200, the home page links each
  operator page, and the repository's homepage field names the site
- inputs: `docs/index.md`, the Pages setting on the component repository, the
  site lane added to the component's workflows

The site is the component's own Pages, served from `docs/`. The UPnP service
transcriptions under `docs/upnp-dp1/` and `docs/upnp-wip2/` stay outside the
operator path and are linked as reference material.

### License and describe the repository {#metadata}

- depends: #site

- verify: `gh repo view` reports the Unlicense, the topics, and the site as the
  homepage
- inputs: the host's `LICENSE` text, the repository settings

The component publishes no license file today. This task adds the Unlicense,
which matches the host and the tools it references, so a reader has a grant to
reuse the code.

### Hold the docs with lanes {#lanes}

- depends: #operator-docs

- verify: the component's lane fails on a deliberate break in the help text, in
  the manual page, in a page link and in a page's register, and passes once each
  break is reverted
- inputs: `.github/workflows/ci.yml`, the man render check, the link check, the
  regenerate-and-diff step for the generated files, the prose audit and the
  `.host-lintignore` that names the archived transcriptions

Each new check is proven by breaking the thing it guards before it is committed. A
check that has never failed is a check nobody has tested.

### Record the pin and the milestone {#record}

- depends: #lanes, #metadata

- verify: the host's pin names the commit that carries the surfaces, the host's
  reproducible-build lane rebuilds from that pin and reproduces the artifact
  (the lane holds the container runtime, and this development host reports
  UNVERIFIABLE from its own `--verify-build`), every task above carries a
  receipt, and the results note names the release that carries the kit
- inputs: the component's lane output, the artifact record, the tagged release

## Verification

The milestone's mechanical checks are the repository's own sweep at every gate:
`validate`, `prose`, `refs --check`, `tasks --check`, `book --check` and
`software --check`. The checks this work adds live in the component's own lane,
because the docs describe that program and move with it.

Two of them are worth stating apart from the rest. The help text and the manual
page are generated from one definition, and the lane re-runs the generator and
fails on a difference, so neither can quietly leave the command line behind. The
flag-coverage test compares the definition with the real parser, which is what
keeps the second copy of the command line from drifting.

## Rollout

The stages are observable one at a time.

1. **The surfaces, locally.** The generator runs, the help text and the page
   exist, and `--help`, `--version` and `man` are read by hand on the
   workstation.
2. **The pages, unlinked.** `docs/operators/` is written and reviewed on the
   filesystem while the site is still off.
3. **The site.** Pages is enabled on the component repository, and the home
   page and the five pages are read through a browser.
4. **The release.** A version bump carries the kit, and the assets are checked
   from an anonymous fetch.
5. **The router.** The installer places the page and prints the steps, and the
   release bytes are compared with the artifact hash before the service starts.

The revert path is the previous release's binary, which the deploy procedure
already parks, and the site setting, which is one API call to turn off.

## Open questions

- Whether an opkg package belongs in a later milestone, which turns the
  installer into a supported upgrade path on the router.
- Whether the daemon should answer a state question of its own, since an
  operator who wants to know whether the mapping is alive has only the tuple
  file and the log.
- Whether the prose and naming lanes the host runs should also run in the
  component's lane, and how the component pins them if they should. The prose
  half runs there now, from a pinned checkout of host-lint. The naming half
  reports 86 findings over the component (measured 2026-09-22), every one in a
  source comment: an RFC section reference, a numbered clause of a UPnP service
  template, or a label from the pre-adoption plan. Clearing those needs a
  provenance-checked declaration pass of its own, which this milestone does not
  attempt.
- Whether the manual page should also be installed where a user command lookup
  finds it, since an operator may look for it in either place.
- Whether the lane should lint the page with `mandoc` as well. The lane renders
  with `groff`, which is the renderer installed on a workstation and the one
  whose warning path was exercised here, and `mandoc` is not installed anywhere
  this project builds.

## Results home

The evidence for this milestone is the component's own files and the output of
its lane. The host's record carries the pin and the artifact hash, and the
release page carries the kit. Where a check produced a line worth keeping, it
is written under `results/` in this room with the pin it was read against.