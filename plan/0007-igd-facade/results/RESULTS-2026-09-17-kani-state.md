# RESULTS-2026-09-17-kani-state: the Kani lane's true state and what is left in it

Status: the lane is open and handed to a peer over git. This record sets
out what is verified, what the milestone documents still claimed wrongly,
the steps that close the lane, and the branches the exchange runs on. It
is the RESULTS record that the 2026-09-15 relocation handoff expected in
this directory.

## What is verified on this host

- This development host cannot run the suite. `free -h` reports 3843 MiB
  total and `nproc` reports four cores; `cargo kani 0.67.0` is installed
  and starts, so the limit is memory rather than tooling. The operator
  confirmed the limit on 2026-09-17.
- The suite was relocated and it ran. On the andromeda workstation
  (192 GiB physical, WSL2 soft-limited to 96 GiB, twelve threads on a
  Xeon X5650) a fresh clone at component 34d48c1 produced 37 of 40
  verdicts: 35 SUCCESSFUL, 2 FAILED, and three harnesses still solving at
  four hours. The authority for that result is the 2026-09-15 handoff
  entry in `MEMORY.md`.
- The raw evidence is not reachable from this host. It lives at
  `C:\Users\dconnolly\Development\kani-evidence-2026-09-16\` on the
  workstation; `/mnt/c/Users` here carries a `david` profile and no
  `dconnolly`, and there is no `~/kani-relocation`.
- Both failures are in `src/upnp.rs`: `entry_at_bounds_proof`, an
  indexing assertion at `idx = 3` with maximal field values whose
  captured counterexample replays green in plain Rust, and
  `mpost_post_parity`, an unwinding assertion where the M-POST head
  needs about 132 bytes of unroll against `unwind(96)`. Neither is
  recorded as a code defect.
- The relocation's remediation attempt was a branch and not a merge:
  `kani-favourable` at component 22b9677, one commit on top of 34d48c1.
  It rewrites `put` to `copy_from_slice`, raises both parity harnesses to
  `unwind(200)`, and adds `cex_replay::entry_at_cex_replay_idx3`, which
  replays the captured counterexample in real Rust. Its fold-test timings
  were never taken.
- The harness inventory on current `main` (0cc2b04) is identical to
  34d48c1: 40 proofs across eight modules (stun 6, slot 9, upnp 8, obs 5,
  vote 5, mapping 3, engine 2, tcpslot 2). Nothing was added after
  34d48c1.
- The component carries no `.obligations` manifest, no `.allium` or
  `.tla` spec, and no CI workflow, so no declared rung turns on this lane
  and `software --check` cannot red on it. The lane is the facade
  clause's ledger, run by hand.

## What the 34d48c1 verdicts do and do not cover

The verdicts were earned against the 34d48c1 tree. Six of the eight
proof-bearing modules are byte-identical to it on `main`, so their 23
verdicts carry over as they stand. Two do not:

- `src/slot.rs` gained 211 lines: the last-seen lease policy added
  `stamp_activity_if_stale`, `gc_idle`, and `evict_idle_client`, and it
  stamps `last_activity_unix` on upsert, refresh, and restore. No harness
  covers any of the three new methods, and the nine slot proofs predate
  the policy.
- `src/upnp.rs` changed the code under proof, 274 lines added and 17
  removed for the WANIPConnection:2 surface: `ST_NAMES` and `st_name`
  gained the v2 targets, `SidSet`'s `Default` changed,
  `service_of_path`, `soap_action_name`, `parse_soap_action`, and
  `classify` grew cases, `UpnpErr` gained faults 730, 731, 733, and 704,
  and `msearch_response` and `notify_payload` changed.

So eight upnp proofs and nine slot proofs are stale against `main`, and
three live policy methods have no proof at all. Neither the milestone
ledger nor the Testing section recorded that before this record.

## How the hand-off runs over git

The exchange is branches and records, not messages.

- `kani-remediation` at component 408457a is based on `main` at 0cc2b04
  and is pushed. It carries 22b9677's three changes ported onto current
  code, and `cargo test` is 121 passed, 0 failed, 1 ignored. Nothing has
  run it under Kani yet. `main` has since moved to ad69a49 for the v2
  listing fix that the miniupnpc interop probe found, and that commit
  touches `src/upnpsvc.rs` alone: no proof-bearing module differs between
  the branch's base and it, and the branch rebases with no conflicts, so
  verdicts earned from the branch stay meaningful either way.
- `kani-favourable` at 22b9677 stays as the original artifact against
  34d48c1. Work from `kani-remediation`, which is its port onto current
  code, and leave `kani-favourable` unmerged.
- The peer's results come back the same way, as a component branch plus a
  revision of this record. The verdict counts live here, so the milestone
  ledger keeps one home for them.
- The pin moved to ad69a49 with that listing fix, so `software --check`
  attests a tree the proofs have not been run against. That is the honest
  state and this record says so.
- Run the suite with the component worktree on `kani-remediation`. While
  it sits there the host gate reports `DRIFT software/ds-lite-punch/main
  at <the worktree's HEAD> but pinned to ad69a4934494` and exits 1, which
  is the pin check doing its job. Return the worktree to `main` at the pin
  before you run `software --check`, or run the suite from a clone of your
  own and leave this worktree alone.

## The work, in order, each step with its check

1. Done: the port. Check met by `cargo test` at 121 passed on
   `kani-remediation`, and by both parity harnesses reading
   `unwind(200)`.
2. Re-derive on the andromeda workstation, the 192 GiB machine where the
   relocation ran, from `kani-remediation`. Check:
   `cargo kani --jobs=4 --output-format=terse` (the tool requires terse
   with `--jobs`) reports a verdict for each of the 40, and the counts
   are written into this record. Before committing hours to it, confirm
   the guest is stable: the 2026-09-16 entry in `MEMORY.md` records that
   workstation's WSL guest restart-looping at idle on a 60-90 s cadence,
   which killed three runs mid-solve, and that it was blocked on
   `wsl --update`, a Windows reboot, or a distro repair. That entry
   stands until a later one retires it.
3. Disposition the two known failures. Check: `entry_at_bounds_proof` is
   reshaped to concrete-index enumeration and passes, and the
   `mpost_post_parity` unwinding assertion is gone at the raised bound.
   If the counterexample replay is accepted in place of the reshape, say
   so here and name what the replay does not prove.
4. Add proofs for the three slot policy methods in `src/slot.rs`. Check:
   the inventory grows to 43 and each new proof has a verdict. The
   properties to state:
   - `stamp_activity_if_stale`: the stamp never moves backward, and it
     moves only to `now`, and only once the gap reached
     `min_interval_secs`. An absent bind port is a no-op.
   - `gc_idle`: exactly the granted UDP slots whose stamp is older than
     `backstop_secs` are freed, and statics and TCP grants never are.
   - `evict_idle_client`: the answer is none, or the longest-idle granted
     UDP slot of a client other than the requester. The requester's own
     grants are never the answer.
5. Decide the WIP2 surface's proof obligation. Check: either a harness
   per changed pure function, the parity harnesses' action list being the
   first candidate since `classify` and the action tables grew, or a
   recorded decision naming what is left to the unit suite.
6. Only then write the supersession of
   [call/0019](../../../call/0019-facade-kani-deferred-to-larger-host.md).
   Check: `host-lifecycle validate .` accepts the new decision and
   `call/0019` reads `Status: superseded`.

## Dispositions that are not owed

- `call/0019` stands in force. The 2026-09-15 entry expected a
  `call/0020` supersession; that number went to the SSDP-all decision,
  and a re-derivation with two failures and three missing verdicts does
  not meet the decision's own terms in any case. Supersede it after step
  6, not before.
- Do not re-run the suite on this host. The operator closed that on
  2026-09-17 and the measurement above agrees with the closure.
- `kani-favourable` sits 28 commits behind `main`, and `src/upnp.rs` has
  moved since. `kani-remediation` carries the port onto current code.
- Do not pass `--no-verify` past the commit gate to land any of this.

## Tooling note

After this host's reboot the built tools are not on PATH. They are in the
tree at `tools/host-lifecycle/target/release/host-lifecycle` and
`tools/host-lint/target/release/host-lint`.

No access route to the andromeda workstation is recorded in this
repository. The evidence path `C:\Users\dconnolly\Development\kani-evidence-2026-09-16\`
is the only handle on it that these records carry.