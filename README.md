# agentic-ds-lite-punch

The host repository for the **ds-lite-punch** software: a Rust daemon that keeps
a CGNAT UDP mapping alive on the Virgin Media Ireland ds-lite line and forwards
inbound UDP to a target behind br-lan, with zero ISP cooperation.

This is the *thought* home. The software itself, the *action*, is hosted beneath
the project as a bare store with worktrees (`software/`, recipe in
`.host-software`). Thought lives here, versioned and audited; action lives in
the component repo.

## Rooms

| Question | Room | Holds |
|----------|------|-------|
| Who  | `cast/` | personas: the human operator and the agentic LLM developer |
| When | `plan/` | the milestone index and `0004-ds-lite-punch/` (the active milestone) |
| Where | `software/ds-lite-punch` | the hosted software, a bare store with worktrees |
| Why  | `call/` | decisions in MADR format, from `0011` (the /57 redesign) and `0012` (this adoption) |
| How  | `AGENTS.md` + `tools/` | the operating manual and the verification tools |

`plan/0004-ds-lite-punch/INVESTIGATION.md` is the rewritten possibility-space
exploration of the Virgin Media AFTR that fed the milestone.

## Working here

Read `AGENTS.md` first: it is the operating manual and it is normative. `CLAUDE.md`
is a one-line pointer to it. `STRUCTURE.md` is the one-page map. `MEMORY.md` is the
append-only working memory.

## Status

- `plan/0004-ds-lite-punch/`: P1 built, deployed, formally verified. P2 (multi-
  instance) and P3 (UPnP-IGDv1 control plane) not started.
- `call/0011`: the VM line /57 + DHCPv6-PD decision, accepted.
- `call/0012`: adoption of the agentic-host methodology (this template revision),
  which moved the DSLITE.md investigation into the plan room as INVESTIGATION.md.
- The ds-lite-punch crate is being migrated into the `ds-lite-punch` component
  repo from the former rope-agentic monorepo; until then the component carries a
  `repro-waiver` recorded in `call/0012`.

## Provenance

The methodology is adopted from
[`connollydavid/host`](https://github.com/connollydavid/host), applied via
[`connollydavid/host-template`](https://github.com/connollydavid/host-template)
at the revision recorded in `.host`. This repository and the spine documents are
public domain (Unlicense); see `LICENSE`.