# The spine moves to 4c8ae9fd, and the ledger claims it

- Status: accepted
- Scope: this host's upgrade event — the techniques revision, the tool pins, and the two checks the newer gate raised
- Date: 2026-11-11

## Context and Problem Statement

The host ran `host-lifecycle` 0.61.0 against a stamp whose ledger claimed nothing past
`RENAME-repro-waiver`, so the gate raised two checks the binary had grown and no record backed: the
component's sources carry `#[cfg(kani)]` code that no obligations manifest declared, and twenty-three
component source files appeared in no task's `- inputs:` line. The operator directed L to
[connollydavid/host](https://github.com/connollydavid/host), whose README owns the adopt/migrate/upgrade
procedure; this host is its case (c), and the procedure's steps are the ones taken here.

## Decision

- The **ledger is claimed, not re-fought**: the four pending entries
  (`REFS-a-number-resolves`, `GATE-refs-in-verify`, `LEM-pronoun-system`,
  `REFS-a-foreign-citation-names-its-repository`) were recorded through their `verify` post-conditions,
  each of which passed against the tree as it stood. The rules were already obeyed; the claims now say so.
- The **techniques are re-applied at `4c8ae9fd`**: the spine files are the template's verbatim
  (`AGENTS.md` carrying the address possessive, the goal loop, the `regen` recipe key and the
  lanes-are-receipts rule), and this host's `Project specifics` section is preserved at the end, as the
  spine requires. `STRUCTURE.md` and `UPGRADING.md` are the template's; `CLAUDE.md`, `MIGRATION.md`,
  `lifecycle.manifest`, `link-skills.sh` and `LICENSE` needed nothing.
- The **tool pins move with the template**: `tools/host-lifecycle` to `v0.63.0` (`9af1435`) and
  `tools/host-lint` to `v0.24.1` (`db4a0d2`). The binaries on PATH are the operator's installs and stay
  the operator's.
- The **inventory remedy is the exclusion file**: the twenty-three modules are named in
  `.host-inventory`, each with the milestone that owns it, because the work that built them lives in
  closed milestones and citing them into closed task graphs would rewrite recorded history.
- The **`kani:` disposition lands with the facade verdicts**: the weekly lane's per-harness loop had a
  stdin drain that silently skipped the last two facade harnesses, fixed the same day; the manifest is
  written when run [43063101075](https://github.com/slartibardfast/ds-lite-punch/actions/runs/43063101075)
  reports all eight, and the component release that carries it follows.

## Consequences

- The gate's remaining items are the two that wait on outside input: the facade verdicts and the
  operator's LAN proof for [plan/0015](../plan/0015-the-routers-name/README.md).
- Future component releases use the `regen` recipe key, which closes by construction the hand step this
  host performed twice in the `v0.6.0` and `v0.6.1` releases.
- The goal loop and its harness doors are available to the next milestone that wants them.

## What this does not claim

- That the four bounded facade harnesses converge anywhere; the restructure-or-waive decision stays with
  the operator, and [call/0050](0050-the-kani-rung-runs-on-a-runner.md)'s lane keeps measuring weekly.
- That the methodology changed here. It changed in the template; this host only claimed and copied it.