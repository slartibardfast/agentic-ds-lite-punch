# agentic-ds-lite-punch

**ds-lite-punch = DS-Lite Proxy UPnP NAT/CGNAT Holder.**

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

## State at 2026-09-19

| Milestone | State |
|---|---|
| [plan/0004](plan/0004-ds-lite-punch/README.md) | v1 core built, deployed and verified; multi-instance built; the UPnP control plane delivered by [plan/0007](plan/0007-igd-facade/README.md) and [plan/0008](plan/0008-adaptive-igd-v1v2-facade/README.md) |
| [plan/0005](plan/0005-test-rig/README.md) | the acceptance rig |
| [plan/0006](plan/0006-ps3-requirements/README.md) | the console requirements; closed by reframing ([call/0014](call/0014-a2-acceptance-reframe.md)) |
| [plan/0007](plan/0007-igd-facade/README.md) | the UPnP facade; closed 2026-09-15 |
| [plan/0008](plan/0008-adaptive-igd-v1v2-facade/README.md) | the adaptive v1 and v2 facade with DeviceProtection; 31 probes pass on the box |
| [plan/0009](plan/0009-mapping-hold-and-signalling/README.md) | the mapping hold and its signalling; done 2026-09-18 |

The component:

- The record in [`.host-software`](.host-software) names the pin, the toolchain
  and the artifact hash. The artifact hash today is
  `ab0f9bd517ef075885fd5b6e6a91b9fcc7e64ad9805e7d6450f2bd3eefd11a45`.
- The component lane runs the test suite and the release build inside the
  pinned toolchain image, and it publishes the binary from the run.
- The test router runs the bytes from that lane.
- The three host lanes pass: Reproducible build, Prose and Site.
- The adopted template revision is `41ba4e10`, recorded in [`.host`](.host).

## Future work

1. **The lobby case.** A console in a lobby sends no traffic. The hold must
   survive that silence on a real console. The operator runs this test
   ([plan/0009](plan/0009-mapping-hold-and-signalling/README.md)).
2. **The Kani suite on a larger host**
   ([call/0019](call/0019-facade-kani-deferred-to-larger-host.md)).
3. **The R4 rule.** A late collision moves an allocation, and it never moves a
   punch. Decide if the rule must follow the protocol of the entry
   ([call/0027](call/0027-collisions-for-punched-ports.md)).
4. **EIF loss.** Detect a change in the filtering behaviour of the carrier
   ([plan/0004](plan/0004-ds-lite-punch/README.md)).

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