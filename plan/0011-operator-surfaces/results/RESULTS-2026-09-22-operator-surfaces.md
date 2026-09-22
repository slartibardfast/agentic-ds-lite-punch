# The operator's surfaces, delivered

- Date: 2026-09-22
- Milestone: plan/0011, all nine tasks receipted
- Component: ds-lite-punch, tag `v0.2.0` at `f0c65e39`, artifact
  `924281b2f6b544d6da6b17dddd312978560cdb467df58a96f15e9016bbe72db9`
- Site: <https://slartibardfast.github.io/ds-lite-punch/>

## What shipped

An operator now has five surfaces where there was one README.

| Surface | Where it lives | What holds it |
|---|---|---|
| the help text, with `--version` | the binary | a test that reads the parser's own arms from the source |
| the manual page | the release asset `ds-lite-punch.8`, and `/usr/share/man/man8/` on the box | that test again, plus the appended sections |
| the operator pages | `docs/operators/` in the component, rendered at the site | a link check and the prose audit in the lane |
| the site | GitHub Pages, serving `docs/` | the lane, and the URL answers rather than a build log |
| the license | `LICENSE` | `gh repo view` reports the Unlicense |

The help text and the manual page come from one clap definition in
`tools/argdoc`, a crate of its own whose empty `[workspace]` table keeps it out
of the shipping crate's dependency graph. The daemon links none of it: it prints
the generated text through `include_str!`. The root `Cargo.toml` and
`Cargo.lock` never moved for it, which is what keeps the artifact from changing
because a documentation tool exists.

## The checks, and how each was shown to bite

A check that has never failed is a check nobody has tested, so each one was
broken before it was committed.

| Check | The break that was shown to fail it |
|---|---|
| the help names exactly the parser's flags | a flag added to the help text, and a flag removed from it |
| the manual names the flags and keeps its appended sections | an appended section renamed |
| the generated artifacts match their definition | a drifted help text staged, which the regenerate step reported with the diff |
| the manual page renders | an undefined roff macro, which groff reported on stderr while still exiting zero |
| a relative link resolves | a link target renamed |
| the register holds | a negative-parallelism sentence appended to a page |

The prose audit runs the host's own `host-lint`, pinned by a clone and build of
`v0.22.0`, which resolves to `0eeabc20`, the commit the host repository's
submodule pins. `.host-lintignore` names the two archived specification
transcriptions, which are records of another document.

## The release

The phase was run before the release and computed `0.1.5 -> 0.2.0` from the
change class, which is the bump that shipped. The tag's bytes were then built
three times in the recorded toolchain, and all three agree:

| Where the hash came from | Value |
|---|---|
| the component's own lane, for the tagged commit | `924281b2f6b544d6da6b17dddd312978560cdb467df58a96f15e9016bbe72db9` |
| the Release lane, which attached it to the release | the same, in `artifact-record.txt` |
| an anonymous fetch of the release asset | the same, hashed after download |

The release is published and immutable, and it carries the binary, the manual
page, and the line that records the hash. The host record was re-pinned to the
tagged commit with that hash, and the host's reproducible-build lane rebuilt from
the pin and reproduced it.

## Findings that outlived the milestone

**The router carries no manual reader.** It has no `man`, no `mandoc`, no
`nroff` and no `/usr/share/man` directory. The page is installed where an
operator looks for it, and on the box the reader is `--help`, which prints the
same generated text. The operator pages say so.

**A version bump now moves the artifact bytes.** `--version` prints the crate
version, so the string is compiled in, and the bytes change with it. The release
ordering that follows is: apply the bump, tag that commit, and pin the tagged
commit with the hash its build produced. Pinning a commit and bumping after it
leaves the record describing different bytes.

**The release phase is one dispatch per release.** Its version comes from the
manifest plus the change class, so a second dispatch after a completed release
proposes the next version and derives the digest of a bump that exists only in
that run. A dispatch made after `0.2.0` shipped reported `0.2.0 -> 0.3.0` with a
digest for a `0.3.0` source. That proposal was not applied, and this record is
why.

**The naming audit is separate work.** Over the component it reports 86
findings, every one in a source comment: an RFC section reference, a numbered
clause of a UPnP service template, or a label from the pre-adoption plan.
Clearing those needs a provenance-checked declaration pass of its own, and the
milestone leaves it.

## The transient red, and why it was expected

The host's reproducible-build lane went red once, on the commit that moved the
pin ahead of the recorded hash. Its own words:

```host-lint:ignore
DRIFT    ds-lite-punch rebuild is 0bdb6b926485 but recorded a452cf38c9c7 — NOT reproducible
```

That is the record saying the pin had moved while the hash still described the
previous release. The next commit set the pin and the hash together, and the
lane rebuilt from the pin and reproduced the artifact.

## Where the evidence lives

The component's commits are `856299c` through `f0c65e3`. The lane's runs are the
CI, Release, Reproducible build and Release phase runs of 2026-09-22. The task
receipts are in `.host-task-receipts`, and the release receipt names the tag and
the hash.