# agentic-ds-lite-punch

**DS-Lite Proxy UPnP NAT/CGNAT Holder (ds-lite-punch).**

This repository holds the thought about that software: the plans and the
decisions for it. The software itself, the action, is a separate repository and
it lives beneath this one as a hosted component (`software/`, with the recipe in
`.host-software`).

- The software: [slartibardfast/ds-lite-punch](https://github.com/slartibardfast/ds-lite-punch).
- The job it does: a daemon on the router holds one mapping through the carrier
  CGNAT open, and it forwards inbound UDP and TCP to one host on the local
  network.

## Rooms

Each file belongs to one of five rooms. A room answers one question about the
work.

| Question | Room | Holds |
|---|---|---|
| Who | `cast/` | personas: the people the software serves |
| What | with the software | specifications, tested in the software's CI |
| When | `plan/` | the milestone index and one folder per milestone |
| Where | `software/` | the hosted software: a bare store with worktrees |
| Why | `call/` | decisions in MADR form |
| How | `AGENTS.md` + `tools/` | the manual and the verification lanes |

## State

[plan/PLAN.md](plan/PLAN.md) is the index, and each milestone's own README carries
its state; this table is the one-line view.

| Milestone | State |
|---|---|
| [plan/0004](plan/0004-ds-lite-punch/README.md) | the v1 core, deployed and verified; multi-instance built; the UPnP control plane delivered by [plan/0007](plan/0007-igd-facade/README.md) and [plan/0008](plan/0008-adaptive-igd-v1v2-facade/README.md) |
| [plan/0005](plan/0005-test-rig/README.md) | the acceptance rig |
| [plan/0006](plan/0006-ps3-requirements/README.md) | the console requirements; closed by reframing ([call/0014](call/0014-a2-acceptance-reframe.md)) |
| [plan/0007](plan/0007-igd-facade/README.md) | the UPnP facade; closed 2026-09-15 |
| [plan/0008](plan/0008-adaptive-igd-v1v2-facade/README.md) | the adaptive v1 and v2 facade with DeviceProtection; 31 probes pass on the box |
| [plan/0009](plan/0009-mapping-keepalive-and-signalling/README.md) | the mapping keepalive and its signalling; done 2026-09-18 |
| [plan/0010](plan/0010-the-filtering-proved-and-watched/README.md) | the carrier's filtering proved and watched; closed 2026-09-23 |
| [plan/0011](plan/0011-documentation/README.md) | the operator pages, the generated help and the manual page; done 2026-09-22 |
| [plan/0012](plan/0012-the-front-door/README.md) | the front door; done 2026-09-27, released `v0.5.0` |
| [plan/0013](plan/0013-the-fronts-two-views/README.md) | the front's two views; done, released `v0.5.1` |
| [plan/0014](plan/0014-the-fronts-legs/README.md) | the front's legs on the poked socket; built and released `v0.6.0`, with two receipts held for the operator's word |

The component:

- The record in [`.host-software`](.host-software) names the pin, the toolchain and
  the artifact hash, and the pin names the released `v0.6.0`, whose bytes the tag's
  lane published.
- The component lane runs the test suite and the release build inside the pinned
  toolchain image, publishes the binary from the run, and proves the vendored
  dependency bundle builds with the network off.
- The test router runs the released bytes, checked against the recorded hash before it
  starts.
- The repository's sweep is the gate: `host-lifecycle software --check .` over the
  rooms (validate, the naming and prose audits, the reference sweep, reconcile, the
  phase receipts and the task graph), with `book --check` for the site.
- The adopted template revision is in [`.host`](.host).

## Future work

1. **The lobby case.** The hold survives a quiet console
   ([call/0030](call/0030-a-mapping-ends-with-its-device.md)), and the run that
   confirms it on a real console is the operator's;
   [plan/0010](plan/0010-the-filtering-proved-and-watched/README.md) names what its
   own run leaves out.
2. **The Kani suite on a larger host**
   ([call/0019](call/0019-facade-kani-deferred-to-larger-host.md)).

## Working here

1. Read `AGENTS.md` first. It is the manual, and it is normative.
2. Read `STRUCTURE.md` for the one-page map of the same rooms.
3. Read `MEMORY.md` for the append-only memory of this project.
4. Record new work in `plan/`. Record new decisions in `call/`.

## Provenance

The method comes from [connollydavid/host](https://github.com/connollydavid/host)
and is applied through
[connollydavid/host-template](https://github.com/connollydavid/host-template).
This repository and the spine documents are in the public domain (Unlicense);
see `LICENSE`.