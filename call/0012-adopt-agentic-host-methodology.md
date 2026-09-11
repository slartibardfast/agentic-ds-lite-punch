# Adopt the agentic-host methodology (host-template 41ba4e1)

- Status: accepted
- Scope: adoption
- Date: 2026-09-11

## Context and Problem Statement

This repository was moved verbatim out of the rope-agentic monorepo as "plain
docs" with no agentic-host template adoption. The operator asked to keep it an
agentic project by following `https://github.com/connollydavid/host`. The
pre-adoption tree: one milestone (`plan/0004-ds-lite-punch/`), one accepted
decision (`call/0011`), an 844-line root investigation (`DSLITE.md`), and an
untracked clone of the software repo (`ds-lite-punch/`).

## Decision

Adopt the methodology at template revision `41ba4e108b4334e4eb89e6995a9fad8e1883742b`
by the case (a) path (no CLAUDE.md, no `.host` stamp existed).

- **Spine.** CLAUDE.md, AGENTS.md, STRUCTURE.md, UPGRADING.md, MIGRATION.md,
  LICENSE, lifecycle.manifest, link-skills.sh, `.gitignore`,
  `.host-lintignore`, and the `.github/workflows` (prose, site,
  reproducible-build) copied verbatim from the template. AGENTS.md gained a
  clearly marked "Project specifics" section for this repo's conventions
  (component identity, register continuation, legacy path mapping), left
  alone by future upgrades.
- **Rooms and stamp.** `host-lifecycle scaffold` wrote the `.host` stamp
  (template, revision, adopted 2026-09-11) and the comment-only LEXICON
  scaffold. `plan/` and `call/` existed and were left untouched; `cast/` and
  `plan/PLAN.md` were written new. `call/0000` (MADR format bootstrap) was
  inherited from the template. The template's example milestone and example
  personas were dropped.
- **Software embed.** The untracked clean clone became a canonical bare store
  with worktrees: `software/ds-lite-punch/.bare` plus gitdir link, canonical
  worktree `main/` at pin `f7e11e934e990bcaf43b0ed38d56bc21a9f71e6d`. The
  recipe in `.host-software` records url, pin, branch. The crate has not been
  migrated into the component repo yet, so reproducibility is waived:
  `repro-waiver = call/0012` (this decision). `software --materialize` and
  `software --check` both pass.
- **Tools.** The template's four tool pins were wired as submodules:
  host-lint (ff0516a, v0.19.0), host-lifecycle (1686a6e, v0.53.0), allium
  (2b7d66f), specula (6bb5857), plus the template itself at the adopted
  revision. `link-skills.sh` linked 24 skills from materialized tools.
- **The rename.** The root `DSLITE.md` was moved to
  `plan/0004-ds-lite-punch/INVESTIGATION.md` (the milestone room, its
  idiomatic home), and rewritten to zero prose tropes at the operator's
  direction. Preserved: the tested constraints, the EIM/EIF characterization,
  hole-punching mechanics, the VPS-relay fallback, and the probe table. The
  `.host-remap` dictionary was empty; the naming audit reports clean.
- **Prose layer.** All authored markdown now carries zero prose tropes
  (`host-lifecycle prose .` clean). call/0011 (eight decoration sites), the
  milestone README, and IMPLEMENTATION.md were cleaned in place, preserving
  every fact, code, and threshold; call/0011 additionally gained the
  `Scope: network` header the scope gate requires of accepted decisions.
- **Record layer.** MEMORY.md was created with the ground-truth entries the
  milestone docs reference ("UDP hole punching works", "CGNAT UDP timeout
  measured", the TCP EIF method). `.host-lintignore` extends the template's
  UPGRADING.md exclusion with the record layer (MEMORY.md, the receipt
  files), the generated book output, the template submodule, and the naming
  carve-out below.
- **Naming audit: content rename over carve-out.** The naming audit flags
  ordinal-shaped identifiers, and host-lint refuses LEXICON declarations for
  them (they are the tell shape itself: renamed, never allow-listed). The
  milestone docs' build-phase, measurement, and invariant codes (previously
  P0-P3, C1-C8, I1-I5) were therefore renamed to content anchors in plan/0004
  (for example "v1 core", "the rescue-timing rig", "the one-holder rule"),
  and the two milestone docs re-entered the naming audit; `remap --check` is
  clean (0 tells). The quirk ledger's cross-references became §-form
  addresses. The one flag-tier item, the position noun "cycle" in the A3 soak
  text, was reworded to "keepalive interval". The spine copy (AGENTS.md) is
  still excluded: its section numbers are template-authored and re-applied
  unchanged by `host-lifecycle upgrade`, so a local rename would fight the
  ledger. The prose gate covers every authored document, the excluded spine
  included.
- The LEXICON carries one declared entry, the version string "UPnP 1.0"
  (the sanctioned form for tell-shaped tokens that are genuine product
  versions).

## Consequences

- Good: the repo is now a host per the methodology: stamped, roomed,
  tool-wired, software-embedded, prose-clean, and auditable from a fresh
  session; registers continue cleanly (next plan 0005, next call 0012).
- Neutral: history is untouched (host default: immutable). Pre-adoption
  commits and the original DSLITE.md prose remain in the archive.
- Carried forward: the crate migration into the ds-lite-punch component repo
  and its reproducibility recipe; the PSN NAT-type and keepalive-pause soak
  acceptance items (plan/0004); allium/specula lanes stay dormant until a
  spec exists.