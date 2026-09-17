# MEMORY: working memory (append-only)

Ground truth, measurements, and session state that a fresh session needs. Newest
entry on top. Append, never rewrite; an entry that is wrong is superseded by a
newer one, not edited.

## 2026-09-17 — the SCPDs pass a controlled XML parse, and minixmlvalid is not a validator

- The four service descriptions (DeviceProtection,
  WANCommonInterfaceConfig, WANIPConnection:2, and the
  WANIPConnection/WANPPPConnection document the PPP constant aliases)
  parse as well-formed XML. They were extracted from their constants and
  parsed with Python's expat, and the parser was controlled first: three
  deliberately malformed documents were rejected and a good one accepted.
  No crate test covers this, because the crate carries no XML dependency
  and its SCPD assertions are substring matches.
- Do not reach for miniupnpc's `minixmlvalid` to re-check it. That binary
  ignores `argc` and `argv` and tests a fixture compiled into itself,
  printing the same "17 events" for a malformed document, for a good one,
  and for our descriptions. It read as a clean pass until the control was
  run, which is the same trap as reading a report instead of the result.
  The interop record carries both facts.

## 2026-09-17 — the v2 authorization policy is decided, and plan/0004 stopped contradicting itself

- call/0024 records the v2 authorization policy, which plan/0008's annex
  had named as the one item still open on the v2 path: the boundary rides
  the v2 face only; AddPortMapping, AddAnyPortMapping, DeletePortMapping
  and DeletePortMappingRange require a live Basic session; every other
  action is public; the administrative DeviceProtection actions require
  Admin; and a caller without the lift acts on its own host alone, with
  the 1024 floor binding the v2 face. A contained specific read resolves
  in the caller's own namespace (714) while a gated or out-of-containment
  request is 606.
- plan/0004's "deliberately not covered" list contradicted its own Open
  questions section on two lines: it still called the TPROXY-fallback
  question open after the datapath work answered it, and it read the EIF
  prober as still owed to v2 rather than carried past it. Both corrected.
- A naming tell worth remembering: the lane flags the position noun
  "section" with a two-level numeral ("section 1.2"), which is the shape
  of this project's own milestone sections, while a four-level
  specification citation ("section 2.5.21.3") passes. Reword the first to
  a content name; the second is a citation of another document.

## 2026-09-17 — the reference client read the v2 listing, and the response shape was wrong

- The ignored `miniupnpc_interop` probe runs again: miniupnpc 2.3.3 built
  at `/tmp/localupnpc` (`upnpc-static` and `testigddescparse`, from
  `github.com/miniupnp/miniupnp` at b2b496a), driving the facade's HTTP
  layer on loopback. The fixture build is written into the probe's doc
  comment, so a reboot that wipes `/tmp` costs a rebuild rather than a
  rediscovery of how to do it.
- What the reference implementation accepted: its description parser
  resolves both presentations; `upnpc -l` accepts the v1 face as a valid
  IGD; `upnpc -L` parses our v2 listing with the entry's fields; and
  `upnpc -n` takes 606 from the DeviceProtection boundary while the store
  holds no session.
- The defect it found, fixed at component **ad69a49** with the pin moved:
  the GetListOfPortMappings response emitted the PortMappingList as the
  response's own children, while the SCPD declares the OUT argument
  `NewPortListing` and the reference client collects the listing only from
  that element's character data. It found neither a listing nor an error
  code and reported -1. The reference server wraps the fragment in that
  element inside a CDATA section, which is now the shape the facade emits.
  The fragment's contents were already right.
- One divergence is recorded and left open: our 730 PortMappingNotFound
  for a listing range that holds nothing (which the transcription
  requires) against miniupnpd's 200 with an empty PortMappingList, so the
  reference client shows a failed pass for whichever protocol holds
  nothing. The check owed when the PDF is at hand: whether 2.5.21's own
  error table carries that rule at all, since the transcription's cites
  for it are 2.5.19's clause numbers.
- The `artifact` hash in `.host-software` is stale with the pin move and
  is owed a re-derivation on the canonical build host. This host's musl
  build hashes to `5cbd9a9e` against the recorded `496d0e29`, so a hash
  recorded from here would be a false anchor; the recipe says so.
- The Kani lane is unaffected by the pin move: ad69a49 touches
  `src/upnpsvc.rs` alone, no proof-bearing module differs between it and
  the branch's base, and `kani-remediation` rebases onto it with no
  conflicts.

## 2026-09-17 — Kani closed on this host, and the lane's true state handed to a peer

- The operator closed the Kani lane on this development host: "kani
  doesn't have enough ram here". The measurement agrees: `free -h` at
  3843 MiB with four cores. `cargo kani 0.67.0` is installed and starts,
  so the limit is memory and not tooling.
- The reboot before this session wiped `/tmp`, so the full-suite attempt
  launched earlier left no log and captured no verdict. It is not worth
  repeating on this box.
- The lane's state, measured this session rather than recalled: the
  2026-09-15 relocation's 37 of 40 verdicts were earned at component
  34d48c1, and current `main` (0cc2b04) carries the **same 40-harness
  inventory** but not the same code under proof. `src/slot.rs` (+211) and
  `src/upnp.rs` (+274/-17) changed their production code after the
  relocation, and no harness was added, so 17 of the 40 verdicts are
  stale. The three new lease-policy methods (`stamp_activity_if_stale`,
  `gc_idle`, `evict_idle_client`) have no proof at all. The other six
  modules are byte-identical to the relocation tree, so their 23 verdicts
  carry over.
- The remediation was a branch and is now two. `kani-favourable` 22b9677
  (one commit on 34d48c1) stays as the original artifact. Its three
  changes were ported onto current `main` as **`kani-remediation`
  408457a** and pushed, with `cargo test` at 121 passed, 0 failed, and
  nothing run under Kani yet. Porting by `git cherry-pick -n 22b9677`
  applied with no conflict, which is the evidence the favourable changes
  never depended on the drift since.
- The hand-off runs over git, not messages: the peer takes
  `kani-remediation`, runs the suite on a converging host, and returns a
  component branch plus a revision of the Kani state record. The pin does
  not move while the proofs are unsettled, so `main` stays at 0cc2b04 and
  `software --check` attests a tree the proofs have not been run against.
- The peer's brief, with the steps, the checks, and the properties to
  prove for the three slot policy methods, is
  `plan/0007-igd-facade/results/RESULTS-2026-09-17-kani-state.md`.
- The relocation's raw logs are **not on this machine**: they sit at
  `C:\Users\dconnolly\Development\kani-evidence-2026-09-16\` on the
  andromeda workstation, and this host's Windows side carries no
  `dconnolly` profile. The 37-of-40 detail is known here only through the
  2026-09-15 handoff entry above.
- `call/0019` stands in force. The 2026-09-15 entry expected a `call/0020`
  supersession, but that number went to the SSDP-all decision, and the
  decision's own terms are unmet while two harnesses fail and three carry
  no verdict.
- The peer's brief, with the steps and their checks, is
  `plan/0007-igd-facade/results/RESULTS-2026-09-17-kani-state.md`.
- Tooling note after the reboot: the built tools are not on PATH. They
  are in the tree at `tools/host-lifecycle/target/release/host-lifecycle`
  and `tools/host-lint/target/release/host-lint`.

## 2026-09-17 — this host's clone rebuilt: bootstrap, pull to origin's tip, kani 0.67.0 present

The machine's copy was a bare fresh clone (no submodules, store, skills, or
hooks). `host-lifecycle bootstrap` rebuilt the local setup: five submodules
at their pins, the store, the worktree, and the 24 skill links (materialize
receipt in the operational ledger). The host repo then pulled 94 commits
from origin (through the plan/0004 reconciliation), and the component
worktree fast-forwarded to the recorded pin `0cc2b04`; `software --check`
and `--verify-setup` are green on it. Kani here is 0.67.0, the same build
call/0019 recorded as non-converging on this host for the facade harnesses,
so a peer run of those still wants the larger host or a generous timeout.
Git identity is set repo-local only (david@connol.ly); the template
submodule stays at baseline `41ba4e1`, matching upstream.

## 2026-09-17 — plan/0004's last sections reconciled, and what the box actually holds

Finishing the reconciliation: the milestone's Testing and Open questions
sections were stale in the same way its ledger was.

- The Kani suite is **40 harnesses across eight modules** (stun 6, slot 9,
  upnp 8, obs 5, vote 5, mapping 3, engine 2, tcpslot 2), not the eight the
  section recorded, and the full-suite re-derivation is call/0019's deferral;
  the partial re-derivations are in the entries about the E7 parity proof and
  the TCP datapath.
- The TPROXY question is **answered**: the TCP datapath needed none. A
  listener and an outbound holder cannot share a tuple under any plain-socket
  reuse combination, so the holder folds an ephemeral local port to the slot
  through the relay's own `snat_map` (`src/tcpslot.rs`); grep finds no TPROXY
  in the tree.
- EIF-loss detection was deferred "to v2", and v2 landed without it: it is
  **carried past v2**, not delivered.
- The PS3 acceptance question is closed by plan/0006 and call/0015.

And one correction of what the deployed table holds: `14572/UDP` belongs to
`192.168.21.12:4444`, which is the `dslp-sink` container's echo, so that row
is the **rig's** mapping, not a household one. The console-class `3074` was
the only household mapping in the table, and it is the one that was lost.
Both rig containers (`dslp-probe`, `dslp-sink`) are still RUNNING on the
router, so the rig is materially ready for the carried longer-limit run.

## 2026-09-17 — correction: the probe-quiet soak had already run (run 3)

The entry below says the probe-quiet pause "is the one concrete experiment
plan/0004 has left" and that it "has not run". That is wrong, and the way it
was wrong repeats the entry's own lesson. The driver
`router-run-soak.py` already implements the probe-quiet design (it kills the
in-container probe as well as stopping the relay), and the run happened:
`plan/0005-test-rig/RESULTS-2026-09-13-run3.md` records 18 of 18 cells with
`pause-arr 0` (zero packets in any pause window, from any source) and the
**AFTR mapping surviving 30 seconds of total silence** with an unchanged
tuple and a flat 816 to 826 ms recovery. The relay, held by its 2 s
keepalives, is not idle-expiring at those durations.

The error was reading the *analysis* that proposed the correction
(`ANALYSIS-2026-09-13.md`) without reading the *results* that executed it.
When a record says a measurement is owed, check for a later record that
discharged it; the analysis predates the run by design.

What run 3 leaves is not an acceptance gap but a premise question, and it is
now plan/0004's named next step: the AFTR's UDP idle timeout on today's node
**exceeds 30 seconds**, against the 5 to 10 second figure the relay's cadence
was built around, so the carried item is a longer-limit campaign (60 s and
120 s silent windows, probe-quiet design unchanged) to locate the true
timeout. The relay's 2 s cadence stays correct either way.

## 2026-09-17 — plan/0004's ledger was lying, and multi-instance was already built

The milestone record said "multi-instance and the UPnP control plane are not
started" in its status header and in two ledger rows. Both were false: the CLI
carries a repeatable `--static-map R=ip:port` beside the legacy single-map
pair (labelled B3 in the code, mutually exclusive by design), and the UPnP
control plane ran ahead of this milestone into plan/0007 and plan/0008. The
ledger is now reconciled, and the sections that researched those features
point at where they landed rather than reading as work still to do.

What the reconciliation turned up, worth keeping:

- **A ledger is evidence, not memory.** Three rows were stale, and each was
  checkable in one grep or one read of the deployed box. Before trusting a
  "not started" row, check the artifact it names.
- **The two "unsigned acceptance" items were not unsigned.** The console
  NAT-type test is closed by reframing (the probe cannot ride a single-target
  pin, call/0014; the console reached PSN Type 2 organically, plan/0006; the
  facade was deprioritised, call/0015). The keepalive-pause soak **ran** on
  2026-09-13 through the rig, a 5-to-30 second grid three times each, and the
  relay survived every cell; the analysis records the confound (the probes
  kept sending through the pause) and names the measurement that is still
  missing: a **probe-quiet pause**, silencing keepalives and probe together.
  That is the one concrete experiment plan/0004 has left.
- **Multi-instance had no test.** The parser read `std::env::args()` directly,
  so `--static-map` could only be exercised by running the binary. The parser
  is split (`parse_args_from(argv)`), and the contract is pinned: two maps in
  order, the legacy pair as sugar, the refusal to combine the forms, and each
  malformed shape named in its own message. 120 tests at component `0cc2b04`.
- The naming audit flags the word "era" as a tell ("component `a5833a2` era"),
  which is fair: it periodises instead of naming. Write the commit and the
  count.

## 2026-09-17 — the DeviceProtection bootstrap is the operator's (call/0023)

The last structural gap in the v2 surface closed as a decision plus a
deploy-script change: the store lives in tmpfs, the daemon has no in-band way
to create its first identity (the introduction protocol is call/0021's
deferral), so a fresh device refuses every role-gated action and nothing can
lift the containment. T4's bench had to seed dp.tsv by hand and restart, which
is a bench trick rather than an operator path.

Now: a root-owned `/etc/ds-lite-punch.acl` in the store's own tab-separated
form, and the procd script copies it into the state directory **at start and
only when no store exists**. That last clause is the load-bearing one: a seed
that fired every start would revert whatever a control point had since changed
over the wire, and seeding once creates the first identity while leaving the
store the device's own thereafter. Absent the file the fail-closed refusal
stands; `DEVICE_PROTECTION_ACL=none` disables it.

Verified on the deployed box in four steps, which is the pattern to reuse for
a bootstrap change: (1) with no store and the file present, the seed fired and
dp.tsv appeared; (2) the seeded credential reached **Basic** over the wire
(Public before login, 200 on UserLogin, Basic after); (3) a marker row written
into the store survived a restart, so the seed does not clobber; (4) the file
and the store removed, the device reads Public and answers 606, the documented
default. The bench's own credential is never left in place.

Still a bootstrap, not the introduction protocol: a control point cannot
introduce itself, and a reversal at call/0021 would make this decision
unnecessary rather than wrong.

## 2026-09-17 — three residual one-holder assumptions, and the bench at 37 of 37

The per-client key (call/0022) took three passes to become true, and the
deployed bench caught every residue: the unit tests held two holders *in* the
table but never enumerated or deleted through it.

1. `get_generic` indexed a list of `(req_ext, proto)` keys and then looked the
   entry up by those two fields, so a two-holder table enumerated as two
   copies of the earlier holder (a fabricated mapping to any control point
   walking it). Fixed by indexing the visible list directly.
2. The entry's `client` field is the request's `NewInternalClient` (the
   datapath target) and the per-client key read that same field, so an entry a
   lifted control point made on another host's behalf was keyed by that host
   and its owner could not read or delete it. Fixed by recording `owner` (the
   requester) alongside `client` (the target), in the record and in the
   persisted row, with older rows reading the target as the requester.
3. The delete teardown's `retain` was still keyed on `(req_ext, proto)` alone,
   so one client's delete drained every holder's entry at that port. Fixed by
   retaining on the owner too.

The way the third one was found is worth keeping: the replay walked the table
after each step, and the tell was the *router's* delete answering 200 while
the *workstation's* mapping vanished with it. A hypothesis-probe had already
exonerated the obvious suspects (vantage address stability, six clean
add/read/delete cycles), so the failure had to be inside the sequence, and
walking after each step localized it in one run.

With all three in and deployed, the T4 matrix is **37 of 37**, including the
case that matters: two LAN clients each hold `3074/UDP`, each reads its own
label, each delete removes only its own mapping. The store is left
fail-closed and the household's `14572/UDP` mapping is the only row in the
table.

## 2026-09-17 — the requested port is a per-client label, and the bench caught two real defects

David: "UPnP was not written for ds-lite. we are superseeding specification",
then "superseed IGDv1 behaviour here for ds-lite world", and "without an
AFTR ds-lite-punch directly controls external udp port". That is call/0022,
which supersedes the keying clause of call/0018: the requested external port
is a **per-client label**, the key is `(client, external port, protocol)`,
and several clients may hold 3074.

What that disposed of, and what it needed:

- The retired one-holder rule was not even the specification's: a second
  claimant **evicted** the first, silently breaking a working mapping. With a
  per-client key a write can only ever replace the caller's own entry at that
  port, so the eviction (and the need for 718) disappears.
- `GetSpecificPortMappingEntry` and `DeletePortMapping` carry no client in
  their spec keys, so they resolve inside the caller's own namespace, or 714.
  That retires the containment's 606 for a specific read.
- Per uplink: with an AFTR the label is never bound; where we own the port,
  the first holder may be given the requested port and a later claimant goes
  through the any-port path. If a "bind the requested port" mode is ever added,
  uniqueness returns for that uplink alone.

Two defects the deployed bench found, both real and both now fixed:

1. **The enumeration fabricated a holder.** `get_generic` resolved the index
   against a list of `(req_ext, proto)` keys and then looked the entry up by
   those two fields, which stopped being unique the moment the key became per
   client: a two-holder table enumerated as two copies of the earlier holder.
   Fixed by indexing the visible list directly (simpler and exact). The unit
   tests had two holders in the table but never *walked* it, which is what a
   deployed bench is for.
2. **The key reads the target, not the owner.** The entry's `client` field is
   the request's `NewInternalClient`, the datapath target, and the per-client
   key is read from that same field: an entry created by a lifted control
   point naming another host is keyed by that host, so its owner cannot delete
   it (714). That is the open item; the key must be the requester.

Measurement notes worth keeping: the discovery misses from this vantage are
**path loss**, not a device rule (single queries lost 15% and 40% in two
samples, spread across targets; one retry ~350 ms later answered 20 of 20);
and the deadline property measured 1004 ms both times it arrived.

And one thing that is not a defect but must be said: the household's
console-class `3074/UDP → 192.168.21.138` mapping **is gone**, lost inside the
session's deployment window. The persisted index's last write and three
DeletePortMapping calls sit in that window, and two of those three are this
session's own cleanup. It is recorded as a loss rather than attributed to the
bench, and the per-client key makes the class impossible going forward.

## 2026-09-17 — plan/0008 is deployed and T4 is receipted

David: "deploy to the router and run T4". Deployed the artifact built to
the recorded recipe (component 2158485, sha256 c9b246c5..., static musl,
987872 bytes) to /usr/bin/ds-lite-punch with the previous binary parked at
/root/ds-lite-punch.prev, procd restarted, and ran the bench matrix: **31 of
31 probes pass**, recorded in plan/0008's RESULTS-2026-09-17-bench-matrix.md
with the bench itself (bench-matrix.py + bench-lan-client.sh) beside it.

What the bench establishes on hardware: the v2 mount is live and gated; the
boundary refuses all four mapping mutators unauthenticated (606) and
contracts the reads (another's entry 606, enumeration 714, listing 730); the
PKCS5 ceremony reaches Basic over the wire and the lift then answers the same
reads 200 on either face; 731 ReadOnly, 501 ForceTermination, 200
RequestConnection, RSIP 0 / NAT 1; a bare ssdp:all is deferred and answered
v1 at 1004 ms and an in-window :2 flips both answers to v2.

Things worth keeping from the run:

- **The device's view of the caller is not the caller's view.** This
  workstation egresses at 172.23.240.220 but the router source-maps it to
  192.168.21.97, which is what sessions and containment are keyed on. Learned
  from the router's own ssh peer: `ss -tn state established "( sport = :22 )"`.
  A containment probe written against the local address reads as another
  host's and fails for the wrong reason.
- **A DeviceProtection session outlives a bench run**, and a lift is the
  principal's roles rather than a face's, so a session left logged in from an
  earlier probe lifts every containment the next run means to test. Log out
  and assert Public first.
- **The bench ate its own tail on the first run** and left three real
  mappings on the line (the wildcard's 1024, the LAN client's 34999, the
  workstation's 34998). All were deleted and the table verified back to the
  household's two entries (3074->192.168.21.138, 14572->192.168.21.12, both
  lease 4294967295, the v1 "appears infinite" policy on a live box).
- **The DP store has no in-band bootstrap.** The authenticated sequences
  needed an out-of-band dp.tsv seed (a U row and an A row) and a restart; the
  deployed default is fail-closed, which is correct and unusable at once.
  This is the shadow of call/0021 and is recorded in the results; the seed was
  removed afterwards so the box carries no known-password credential.
- The task schema reads `- verify:`; T4's bullet said `verified by:`, so the
  tool refused the done receipt for want of a verify field. Worth checking the
  bullet names when a receipt is refused.
- The naming audit flags a leading-zero decimal (`0.85`, `0.05`) as a
  version-like tell, including in source. The bench's timings are integers in
  milliseconds for that reason.

## 2026-09-17 — a rename's references must use the heading's own words

David asked whether the rename degraded the document, and the honest answer
was yes in one mechanical way: six of the thirty renamed references did not
find their target. "the conformance suite" pointed at a heading called
"Testing"; "the ssdp:all rule", "the persistence rules", "the burst-window
coalescing", "the miniupnpd reference" and "the Xbox One legacy facts" had
the same near-miss shape. A number is a lookup key and a near-miss phrase
is a guess, so the rename traded one navigation cost for another.

The lesson for anyone supplying a rename map: `.host-remap` never coins a
name, so every miss is the supplier's. Before writing a rule's `new` value,
read the heading it will point at and reuse its words. Five headings now
carry the phrase the prose reaches them by, and the sixth moved the
reference to the heading's more precise words.

The check that catches this class is cheap and worth repeating after any
rename: for each rule's `new`, test whether its key noun phrase appears in a
heading. Two apparent failures there are usually formatting rather than
wording (a code span around a token, or a phrase split by a line wrap), so
confirm before editing.

## 2026-09-16 — the naming audit is clean: the milestone's sections read by content

David: "alright let's fix up prose" — the prose lane was five tropes (done,
verify HAZARD closed), and with it the naming lane's 78 tells. The verify
gate now exits 0 for the first time in this project: no HAZARDs at all.

- The naming lane's tells were one shape family: plan/0008's own section
  numbering (44 dotted subsection headings and ~30 cross-references). Both
  remedies the tool offers for that shape are closed by the tool itself:
  host-lint refuses a LEXICON entry for it ('section 26.15' carries the
  position noun as a word, so masking it would blank that token out of a
  real tell), and it names the remedy as a rename. Every subsection already
  had a content name, so the numbers went and the names stayed; the two
  findings lost their A/B labels for what they found.
- `UPnP Device Architecture 1.0` went the other way and was *declared*
  (`host-lint lexicon add`), accepted in the same session that refused the
  section shape. That contrast is the declaration rule working: a document's
  name and version is provenance; a positional reference is a tell.
- `.host-remap` cannot express a heading rule: `load_remap` skips any line
  whose trimmed form starts with '#' as a comment, so `## 26.15 => ##` loads
  as nothing (44 such rules loaded as 0, silently). The heading strips were
  applied as a direct edit and the gap is recorded in the dictionary for the
  tool author. Remedy upstream: treat a line as a comment only when it
  carries no ' => '.
- `.host-task-receipts` was missing from `.host-lintignore` while the other
  two ledgers were listed. It quotes the milestone text it was recorded
  from, so it is the record layer and is now excluded.
- Renaming plan text that receipts quote makes those receipts stale, and the
  task gate says so ("the task's verify changed since the receipt was
  recorded; re-derive"). The remedy is to re-record, not to re-derive a
  prose verify line.
- Live citations were repointed with it: the two decision records (by the
  tool) and the component's transcriptions and comments (by hand, 58 sites).
  Records that are excluded (MEMORY, the receipts) keep their old numbers,
  which is the disclosed cost of the rename.

## 2026-09-16 — the reads are contained too; one view for both faces

- David's question ("they can only affect self, so is a read of others even
  privileged?") cut the last asymmetry out of the containment: writes were
  contained on both faces and reads on the v2 face alone. A read confers no
  capability, but the table is the ingress map (which host is reachable from
  outside, on which port, over which protocol, and how much lease is left),
  and on this box that map is the artefact the punch work creates. So one
  view now serves reads and writes on either face; the port floor is the only
  clause bound to the v2 face, since a legacy client may legitimately exceed
  it.
- The cost I had claimed for containing the v1 reads was overstated, and the
  check that settled it is worth remembering: the daemon already writes the
  whole entry index to its state file (`/tmp/dslp/upnp.tsv`, tmpfs, live
  while it runs), so the operator's privileged view is a local read and never
  depended on the anonymous UPnP read. Before arguing that a containment
  costs the operator sight, look for the state file first.
- A lift belongs to the principal, not the face: a control point that
  authenticates over DeviceProtection reads the whole table on either face.
  That is the v1 read containment's remedy, and it means "the v1 face has no
  authentication" was never the same claim as "the v1 caller has no remedy".
- Assertion lesson: GetSpecificPortMappingEntry's response carries its OUT
  arguments only, so the NewExternalPort it was asked for is not echoed; a
  wire assertion must look for the internal side or the label.

## 2026-09-16 — the containment for callers without the lift

- plan/0008 #v2-service-set now enforces the policy the spec recommends for
  unauthenticated and unauthorized control points (2.5.16.2, 2.5.18.2,
  2.5.14.2, 2.5.21.3), recorded at plan section 26.22. Before it, the engine
  checked only that the named client lay in the LAN /24, so any LAN device
  could open a door to any LAN host; on this box a mapping is an ingress path
  punched through CGNAT that lands on a named host, so that mattered.
- Three clauses, each bound where the caller has a remedy. The caller's own
  host binds both faces, and it is the clause that matters on the v1 face,
  where no authentication exists. The port floor and the read containment bind
  the v2 face, where a live Basic session lifts them: low-port self-mapping is
  common enough that a remedy-free refusal on the legacy face would be a
  compatibility break rather than a policy.
- The lift is `dp::authorize(session_roles, Roles(["Basic"]))`, the same
  function the boundary gate uses, so the gate and the lift cannot drift.
- Mechanics worth keeping: `Contain { caller, high_port }` is computed once in
  the dispatcher and passed to the engine as a view, so the containment sits
  under the boundary gate; `MappingReq` keeps allocate_exact and
  allocate_preferred differing in port resolution alone; a range delete skips
  what the caller may not touch (2.5.19.2) and answers 730 when nothing in the
  range was its own; a contained enumeration's index space is what the caller
  may see, so 714 still terminates a walk.
- Left open deliberately, and recorded as an accepted leak rather than an
  oversight: an unauthenticated v1 caller can still enumerate the table,
  because no authentication exists on that face and the operator's own
  diagnostics read it.
- Note on this file: the four entries this session added before this one (the
  WIP2 transcription, table 2-10's required surface, the allocate split, and
  call/0021's WPS decision) were appended at the bottom, against the
  newest-on-top rule stated above. They are left in place rather than moved,
  because this file is append-only; a reader should look at the tail as well
  as the top.

## 2026-09-16 — WSL guest crash-loop halts the verification campaign on andromeda

- The 6.18.33.1-1 guest (WSL 2.7.8.0) began restart-looping at ~14:35
  (ten-plus boots in twenty minutes, one wtmp CRASH marker, guest
  journals corrupted each cycle, healthy host: 178 GB free, clean
  System event log). It crashes at idle on a 60-90 s cadence. It killed
  the suite stragglers mid-solve (~24 h each), the favourable fold
  test, and two relaunches.
- Mitigation attempted and in place: `.wslconfig` gained
  `memory=48GB`, `processors=8`, and `autoMemoryReclaim=disabled` (was
  the experimental Gradual) — the loop continued at idle, so the
  reclaim setting was not the whole cause. Revert those lines at will
  once WSL is stable again.
- Blocked on operator-grade intervention: `wsl --update` (or rollback
  off the 6.18 preview kernel), a Windows reboot, or distro repair.
  Until then no long verification run can live on this host.
- All evidence salvaged to the Windows side at
  `C:\Users\dconnolly\Development\kani-evidence-2026-09-16\` (the j4
  suite log with the 37 verdicts, the serial log, the favourable-run
  logs, the entry_at counterexample capture, the verdict parser). The
  37-verdict as-run record stands; the repo remains fully pushed.

## 2026-09-16 — DP:1 service dispatched; the PKCS5 ceremony parameters are pinned by the spec

- plan/0008 #v2-service-set progress: the DeviceProtection:1 service is
  implemented end to end (component eb79263, 112 tests green): the
  authoritative 13 actions behind /ctl/DP, admin-gated ACL/role surface,
  the WIP2 section 26.7 boundary (v2 mapping mutators need a session;
  :1 face stays unauthenticated), dp.tsv persistence (users+ACL; sessions
  transient), and the wire-level boundary suite.
- Spec pins that corrected earlier assumptions: the action surface is 13
  (the miniupnpd-derived 14 names were wrong); the standard roles are
  Public/Basic/Admin (NOT "Administrator"); STORED = first 128 bits of
  PBKDF2-HMAC-SHA-256 with salt = Name || Salt and c = 5000 (not 4096);
  the authenticator is the first 128 bits of HMAC-SHA-256(STORED,
  Challenge || DeviceID || ControlPointID); the login CP identity MUST be
  in the ACL (2.6.6.5).
- Sessions are keyed by the control point's source address (the plain-HTTP
  analogue of the spec's TLS session); the decision stays a pure function
  of the principal's roles. GetAssignedRoles returns "Public" for
  unauthenticated sessions per 2.6.3.2.
- Recorded deferrals (IGD_V2_ENABLED still off): WIP2:2 argument-table
  transcription, AddAnyPortMapping any-port (0), the WPS registrar
  transport (SendSetupMessage answers 600/704 on this wired IGD).
- Operator provisioning of a fresh deployment: dp.tsv (users + ACL) is
  out-of-band config; with the default empty ACL every protected action
  denies.

## 2026-09-15 — Teardown correction: the PS3 DOES delete at power-off (partial)

- The 2026-09-15 keepalive/teardown entry below is corrected in part:
  the PS3 sent a DeletePortMapping at power-off (20:22:44, observed
  live) and the facade released the 3658 grant cleanly (entry removed,
  slot socket released, keepalive count dropped 4 to 3) — the C1/C2
  teardown path verified on a real console grant outside the harness.
  The shutdown cleanup is partial: the console's other grant (3074)
  remained armed. The unsupported claim "the PS3 powers off without a
  DeletePortMapping" is superseded.
- What stands: a client that vanishes without deleting (unplug, lost
  network) leaves its grants (infinite leases, no liveness, leases.tsv
  restore); the lease-clamping follow-up covers those residues.

## 2026-09-15 — Keepalive floor and teardown: no release on client disappearance

- The keepalive floor measured: a bare 20-byte STUN binding request
  plus a ~55 B response, every 2 s, per slot. Three armed slots carry
  ~8-12 MB/24 h on the line (a rounding error). Zero tuple rotations
  in ~60 slot-hours while armed (census of one day of daemon log); the
  one rotation seen matched the single unarmed window (~9 min),
  bounding the AFTR idle reap on this session. Recorded in
  plan/0007-igd-facade README.
- Teardown: a client that disappears without deleting does NOT release
  its grants. The PS3 powers off without DeletePortMapping; the
  granted leases are infinite (U32_MAX); the facade has no liveness
  detection; even a daemon restart restores the grants (leases.tsv).
  Release happens only on an explicit Delete, a same-client re-Add
  with a changed internal tuple (the replace path), or the operator.
- Policy (2026-09-15, supersedes the lease-clamping follow-up): the
  granted lease APPEARS infinite (U32_MAX on the wire and in the
  index); the effective lifetime is managed underneath by the slot
  machinery (active hold, replace, Delete, operator, pool caps 32/16).
  No expiry countdown churns a live tuple (a released mapping is not
  preservable on this line; re-arm gets a new port, observed). The
  appearing-infinite value is not a permanence promise; conservation
  levers stay behind it. The IGD:2 604800 guidance addresses passive
  mappings; the relay's active hold supersedes it.

## 2026-09-15 — Kani relocation: 37 of 40 verdicts on the 192 GiB host; remediation in flight (session handoff)

- The call/0019 re-derivation ran on the andromeda workstation (Windows 11
  Pro for Workstations, 192 GiB physical, WSL2 soft-limited to 96 GiB,
  Xeon X5650 at 2.67 GHz, 12 threads; kani-verifier 0.67.0 with the
  bundle provisioned that day, CBMC 6.8.0, cadical) against a fresh
  clone of ds-lite-punch at 34d48c1. Operator note: the old non-convergence
  was memory plus slow-core solver time, not symbolic hardness.
- `cargo kani --jobs=4 --output-format=terse` (operator-directed; the tool
  requires terse with --jobs) produced 37 of 40 verdicts: 35 SUCCESSFUL,
  including the entire pre-facade 32 and sid_set_invariants — the facade
  review's chunk-7 prediction did not materialize (the full+absent state
  is unreachable in that harness as written). 2 FAILED; 3 harnesses were
  still solving at 4 h+ when this entry landed.
- FAILED, classified SPURIOUS — entry_at_bounds_proof (upnp.rs:1557,
  `e == arr[idx as usize]`): the captured counterexample (idx = 3,
  maximal field values) replays green in plain Rust
  (`entry_at_cex_replay_idx3`). It is a Kani/CBMC artifact; the harness
  should be reshaped to concrete-index enumeration and the finding
  raised upstream.
- FAILED, arithmetic not hardness — mpost_post_parity (unwinding
  assertion in `put`, upnp.rs:1397): the M-POST prefix constant is ~101
  bytes against `unwind(96)`, and classify's full-head marker scans need
  ~120 on the ~132-byte M-POST head. mpost_post_parity_real_actions is
  predicted to fail the same way when its verdict lands.
- The favourable-shape attempt is pushed as branch `kani-favourable`
  (22b9677) on the component remote: `put` rewritten to
  `copy_from_slice` (memcpy is a CBMC builtin; no loop to unroll), both
  parity harnesses at `unwind(200)`, clean-action-text scoping
  untouched. Fold-test timings pending; the escalation if the symbolic
  variant stays slow is a verified `find_header` contract applied via
  `stub_verified` (`-Z function-contracts`).
- Everything from the runs lives only on this host under
  `~/kani-relocation/`: `kani-run-2026-09-15.log` (interrupted serial
  attempt), `kani-run-2026-09-15-j4.log` (the complete suite),
  `favourable-real-actions.txt` and `favourable-mpost.txt` (the
  attempt), `entry-at-cex.txt` (the artifact evidence),
  `parse_kani.py` (thread-aware verdict extractor; volatile /tmp copy
  was replaced). Raw logs stay on the host per the results-redaction
  policy.
- Still owed after the stragglers and fold tests resolve: the RESULTS
  record in plan/0007-igd-facade/results/, the call/0020 supersession
  of call/0019, the crate remediation commit with the pin move, and the
  upstream artifact report. PS3 work (plan/0006) is unaffected: the
  host repo and the component pin are pushed.

## 2026-09-15 — Facade review verdict: 5 criticals fixed, committed 24f4e4d

- The 17-agent review of the E1-E8 facade increment (79 tests green) found
  five criticals; all were re-verified against the tree and fixed with
  regression tests. 86 tests now green. The fixes that future sessions
  must not re-break (all landed in component commit 24f4e4d):
  1. Respawn-restored grants: main's slot loop skips granted leases in
     facade mode; `UpnpFacade::start` re-spawns them and registers the
     JoinHandles (`spawn_restored_grants`), so delete_mapping/GC abort
     them — the 2026-09-14 socket-leak class was reachable through the
     documented respawn path (tasks map starts empty; main's discarded
     handles were the only owner).
  2. The control-plane entry now rides the internal (proto, client,
     int_port) key via the pure `apply_entry` decision; a re-Add that
     moves a mapping to a new slot tears down the old occupant (replace
     semantics, one entry per external port) instead of leaving a stale
     bind_port that deleted the wrong datapath.
  3. SIGTERM handler: sleep+exit now sit INSIDE the `if let Ok(...)`
     guard — a registration failure no longer self-terminates the daemon
     150 ms after boot.
  4. `UpnpFacade::start` returns io::Result; an SSDP bind failure (UDP
     1900 taken, or lan-ip not owned) degrades the facade instead of
     panicking the whole daemon; deploy env gained `UPNP=0` to disable.
  5. `classify` GENA markers (NT/CALLBACK, SID) now run on M-POST too —
     the `mpost_post_parity` Kani counterexample (action bytes with `\n`
     fabricating a `SID:` line) is closed; pinned by
     `mpost_post_parity_multiline_corners`.
- Suggestions fixed: GENA initial NOTIFY advances the eventKey (first
  change carries 1, not a repeat of 0); bind_ssdp checks both setsockopt
  results (fail-closed on a failed group join); parse_callback rejects a
  residual `<`/`>` (multi-URL CALLBACK) instead of mangling the path;
  xml_tag/find_close skip comment+CDATA spans (boundary strip, never a
  partial accept); http_serve continues on accept errors; persist:
  `snapshot` is the one projection (main's inline copy deleted) with
  tests, plus `seed_external_ip` pinned.
- Kani: `mpost_post_parity` harness re-run was started post-fix but had
  not converged when this entry was written — the unit test pins the
  corners; receiver must re-verify the proof and the "32 of 32" receipt.
- Not done yet (milestone closure, gated): plan/0007 results record,
  receipts, .host-software pin move (requires pushing 24f4e4d first).

## 2026-09-15 — E6 signed: console/UPnP observed live on the deployed 34d48c1; deploy footguns

- E6 (the deferred PS3-with-facade item, see 2026-09-15 closure entry and
  call/0019's sibling) is now attested: three consecutive MW2 games ran
  perfectly with the facade live on the router. The console's games DO
  use UPnP IGD AddPortMapping (the "PS3 has no UPnP" notion is wrong):
  MW2 requested 3074/UDP exactly, the facade granted it (entry 3074 ->
  slot 40002, infinite lease), plus 3658 -> 40001; a packet trace showed
  the 3074 mapping held unrotated through three games and three external
  peers contacting the console inbound (one sustained peer, two probes,
  inbound payloads to 488 bytes). Raw evidence stays on the router at
  /mnt/nvme/runs/2026-09-15-ps3-facade/ per the results size policy;
  the record is RESULTS-2026-09-15-ps3-facade.md.
- The deployed build is now 34d48c1 (sha 3a030fd0, pid 20468), deployed
  this evening. The old "deployed 92ac62cc" note is superseded. RSS
  flat, zero log errors through the whole session.
- Deploy footguns, both hit this evening:
  1. deploy/install.sh expects the binary ALREADY at /usr/bin (its
     first check); staging it in /tmp and running install.sh restarts
     the OLD binary silently. scp to /usr/bin FIRST, then install.sh.
  2. scp onto /usr/bin/ds-lite-punch fails with "dest open ... Failure"
     (ETXTBSY) while the old process runs: stop the service first
     (/etc/init.d/ds-lite-punch stop), scp, then install.sh.
- The facade battery (facade-verify.sh) had three script bugs fixed this
  session: the pcap filter used invalid `port N-M` (now `portrange`), so
  the capture leg died silently; the catcher's ExternalIPAddress parse
  split bytes with str separators; gena-sid.txt/renew.txt were written
  inside the probe but read on the router host. Re-runnable cleanly now.

## 2026-09-15 — plan/0007 facade milestone closed; two deferrals recorded

- The E1-E8 facade milestone is receipted and closed: every plan/0007
  task discharged (migrate-crate through closure), the verify recheck
  green (validate ok, prose clean, reconcile ok, refs gate ok, book
  renders), the software pinned at 34d48c1 (review fixes + kani scoping,
  pushed upstream).
- Two items are recorded as deferred, not attested, in
  RESULTS-2026-09-15-facade-review.md:
  1. Kani structural proofs on the facade tree (call/0019): CBMC 0.67.0
     does not converge on this host (three timed-out runs, 17/10/5 min).
     `mpost_post_parity` now proofs clean action text; the multi-line
     corners are unit-pinned. Full-suite re-derivation runs on a larger
     host before any deploy relying on the Kani receipt.
  2. The E6 PS3 sign-off with the facade live: not run at closure
     (operator decision); the plan/0006 A2 sign-off stands for the
     organic datapath.
- The 2026-09-14 OOM-era entry below stays authoritative for the
  random_sid fix and the deployed build (92ac62cc).

## 2026-09-14 — Facade OOM root-caused and fixed: unbounded /dev/urandom read in random_sid

- The router daemon OOM-killed itself three times (27426/2030/2202, all
  anon-rss ≈15.4 GB, total-vm ≈2^34): a GENA SUBSCRIBE calls
  `random_sid()`, which used `std::fs::read("/dev/urandom")` — a
  read_to_end that never sees EOF on a device, so the Vec doubles without
  bound until the host exhausts (66-71 s per death, matching the doubling
  cadence from a 2 s tick). SUBSCRIBE leaves no SOAP log line, so the
  deaths looked triggerless. Reproduced locally: single SUBSCRIBE with
  one GENA subscribe produced a 2^29-byte transient; fixed with
  `File::open` + `read_exact(&mut [u8; 16])`, verified live: 8× SUBSCRIBE
  all 200, VmData flat at ~10 MB.
- Earlier "wedge" and SSDP blocking-socket issues (fd 11 flags `02`) were
  also fixed this session (SOCK_NONBLOCK|SOCK_CLOEXEC at bind_ssdp); the
  slot-socket teardown leak (spawn_udp_slot returning empty handle vector)
  was fixed and covered by `udp_slot_revoke_releases_socket`. 2385 (the
  OOM-survivor) was the same teardown build, stable for hours — the death
  required a SUBSCRIBE, which is why long-idle instances stayed green.
- Deployed builds this session: b9804ac9 (CIF service), 6ba11644 (SSDP
  nonblocking), 5550db21 (slot teardown), 92ac62cc (urandom read fix —
  the currently deployed, sha 92ac62cc, pid 10769 as of 00:14).

## 2026-09-13 — TCP datapath closed: return-path RCA, egress fix, external proof

- The datapath's open frontier is closed. The RCA (results/
  RESULTS-2026-09-13-tcp-datapath.md): rp_filter off (refuted);
  source validation open; the listener healthy (a local loop and the lo
  capture proved the SYN-ACK is generated). Root cause: the accepted
  connection's reply routes per the kernel's output lookup, so a
  self-sourced peer's reply loops locally (the local table outranks
  everything) and a remote peer's reply egresses the vdsl4 default,
  never the eth1 line the AFTR mapping lives on.
- The fix (component 6c3d15a): add_egress_rule installs a policy rule
  from the bind address into a dedicated table (prio 25100, table
  1001) whose default is the hub; the init script removes it on stop.
  Proven end to end: a peer behind the us wireguard (a genuinely
  external source) completed a mapped TCP session with data both ways
  through the fold-holder, wildcard listener, splice, and sink echo.
- The #tcp-datapath receipt is recorded; the milestone frontier is
  #facade. Self-sourced handshakes through the relay are impossible by
  construction (the reply's destination is the router itself), so the
  external vantage (the us tunnel) is the verification gate, not the
  rig's own vdsl4 masquerade.

## 2026-09-13 — TCP datapath staged verification: layers proven, one frontier

- The tcp-datapath implementation (plan/0007 #tcp-datapath) is in the
  component (pin 8090500): the protocol threading, the nft TCP arms,
  and the tcpslot module (wildcard listener, splice, fold-based
  holder). Code-level verification: 54 unit tests, 32 of 32 Kani
  harnesses.
- Line-level (results/RESULTS-2026-09-13-tcp-datapath.md): a listener
  and an outbound connector cannot share one tuple on this kernel under
  any plain-socket SO_REUSE combination (all verified); the holder uses
  an ephemeral local port folded to the slot tuple by the relay's own
  snat_map, and the mapping's external tuple publishes. SYN forwarding
  from the rig's own and genuinely external (us-wireguard) sources
  proven; the accept-splice-target path proven by the local loopback
  round-trip.
- The frontier: AFTR-forwarded SYNs arriving on eth1 are not answered
  even with the accept rule first and the wildcard listener bound
  (local SYNs are answered). The candidate is the eth1 rp_filter or the
  route for the translated source. The #tcp-datapath receipt stays
  pending until this closes.
- Vantage limitation: self-sourced probes masquerade to the router's own
  address, so the listener's reply routes locally and never egresses
  the AFTR; Globalping's current schema allows no port targeting (http
  is port 80 only, no options). The us-wireguard vantage reaches the
  mapping but its own return path broke in the test. The deployed relay
  was restored to the recorded artifact (7127f4bf) after the test.

## 2026-09-13 — C3 measured: the AFTR expires idle TCP mappings in (120, 300] seconds

- The C3 run (plan/0007 #c3-tcp; results/RESULTS-2026-09-13-c3.md)
  bounded the AFTR's TCP mapping idle lifetime at (120, 300] seconds on
  this node and session: alive at 120 s of silence, dead by 300 s,
  double-confirmed by the eth1 SYN-arrival capture and the probe's
  refused once the AFTR RSTs. The plan/0004 UDP-only constraint's
  unlock is discharged; TCP grants enter the datapath design.
- Contrast: UDP survived >30 s silent and refreshes on inbound; TCP died
  within minutes of silence with no inbound refresh. The datapath sizes
  re-establish-on-demand to time, not a UDP-style keepalive.
- Scoping: one node, one session, one load; the number is a bound, not a
  lease guarantee.

## 2026-09-13 — pgrep -f self-match trap (router measurements)

- A command that contains the pattern text matches itself under pgrep
  -f: three attempts at the keepalive-stop gradient froze the script's
  own shell (a SIGSTOP against the wrapper's own pid) and orphaned
  stopped shells on the router. The fix: a bracketed pattern class
  ([d]s-lite-punch) and never quoting the plain pattern anywhere else
  in the same command; and for the relay specifically, derive the pid by
  comparing /proc/PID/comm against an assembled literal (a split string
  so the wrapper cmdline never contains the plain name). pgrep -x proved
  unreliable on the router's busybox for this; the comm check is the
  ground truth.

## 2026-09-13 — pinning hunch measured: the IP is session-pinned, the keepalive pins the port

- plan/0007 enabler measured (results/RESULTS-2026-09-13-pinning.md):
  eight console-class XOR-MAPPED probes and the relay's pin all share
  the session public IP (<aftr-ip>), across 45/60/90 s relay stops with
  the relay State=T verified and a keepalive-quiet window (one in-flight
  packet then silence). The external IP is customer-session-pinned, not
  keepalive-pinned; the 2 s keepalive pins the relay's own port (59230),
  held or identically re-issued, extending the 18/18 reuse rule to these
  windows. Console flows allocate sibling ports in the session space
  (59201 to 59391), independent of the relay's keepalives.
- Scoping: one node, one session, one load; the AFTR's state is node and
  load dependent (the old 5-10 s TTL versus today's >30 s survival).
  The facade's GetExternalIPAddress honesty assumes the session-pinned
  IP; re-check if node churn is suspected.

## 2026-09-13 — plan/0006 complete; pbr 1.1.8 does not route secondary wans

- The PS3 milestone is complete and signed: A2 acceptance under the
  call/0014 reframe (organic capture-attributed Type 2 plus the A1 fold
  proof plus tuple stability; a fold-attributed PSN type reading is
  impossible by construction because the console's NAT probe uses
  ephemeral source ports), phase-E priority settled by call/0015
  (deprioritised; the console reached Type 2 and CoD Open with SSDP
  unanswered). All six task receipts recorded; the tool reports the
  graph fully discharged. Console state: PSN works after the OS update,
  MW2 NAT Open, sessions captured and archived at
  /mnt/nvme/runs/2026-09-13-ps3-exam/.
- Routing lesson: pbr 1.1.8-r16 on ImmortalWrt monitors wireguard
  interfaces and the primary pppoe gateway only; a DHCP secondary wan
  (the eth1/vm4 side) cannot be a policy interface, even with a named
  config interface entry. The console's eth1 routing stays on the direct
  from-address rule (ip rule 25000 to table 1000); that is the correct
  mechanism for interfaces pbr does not manage.

## 2026-09-13 — committed records redact addresses (standing policy)

- Third-party public IPv4 addresses (game peers, service endpoints from
  the PS3 sessions) and this line's own addresses (the AFTR tuple, LAN
  hosts, the vdsl4 address, the console MAC) are replaced with labelled
  placeholders in committed records. The raw captures on the router
  retain the real values; results stay out of the repo per the size
  policy. The rig scripts keep their operational values because they
  must run. A record that needs a real tuple re-derives it from the
  running system, never from the repo.

## 2026-09-13 — PS3 MW2 session stats; RDAP country is not the hosting location

- Full session captured (brlan/eth1, ~330 MB each; backend at
  /mnt/nvme/runs/2026-09-13-ps3-exam/). Game data UDP 3074 only: 22k
  packets, 2.3 MB, ~3.3 KB/s; outbound 2:1 over inbound; zero TCP RST;
  the organic path delivered 7.3k inbound game datagrams to the
  console's 3074 with no drops. Path proof: 15 s live windows show the
  game on eth1 and ZERO matching packets on pppoe-vdsl4 (vdsl4 had ~93
  KB/s down of router-side traffic, not the PS3). Source-port
  preservation kept the console's 3074 visible on eth1 egress
  (<router-eth1-ip>:3074). Addresses redacted from records 2026-09-13;
  raw captures on the router retain them.
- Peer distances: measured RTT (median) to the match peers 11 to 18 ms
  = European PoPs, ~1,200 to 2,600 km. RDAP registrations are not the
  route: the main host (90% of game traffic) registers to Zain Saudi
  Arabia yet answers at 18 ms from the UK; a second peer registers to
  Verizon US yet answers at 17 ms. Use measured RTT, never the registry
  country, for distance claims.

## 2026-09-13 — PS3 examination: organic PSN failure was stale firmware, not the network

- The PS3 failed PSN organically before any of our reconfiguration.
  Root cause: the legacy console-facing zone is gone from the public DNS
  (api.playstation.net, us.playstation.net, epps.dl.playstation.net,
  nss.cr.us.playstation.net: no A/AAAA from 8.8.8.8 directly;
  www.playstation.com and ps3.update.playstation.net alive; xboxlive
  control resolved). Both lines healthy: vdsl4 returned 403 from
  auth.api.sonyentertainmentnetwork.com (TLS fine), and the eth1 path
  carried a real TCP connect to it from a br-lan source.
- The console OS update resolved it: the current firmware queries the
  live namespace (nsx.np.dl.playstation.net, *.np.community.
  playstation.net, auth.np.ac.playstation.net, *.sonyentertainment-
  network.com); none of the legacy names appear in the capture.
- Organic NAT Type 2 measured under capture: PSN NAT servers
  <psn-nat-a>/<psn-nat-b> on UDP 3478/3479 echo the console's ephemeral
  source ports 53004/53010; the console SSDP M-SEARCHed
  239.255.255.250:1900 with no IGD answering, so Type 2 came from hole
  punching alone (phase-E relevant). NOT relay-attributed: the relay
  still targets the test sink, no <console-ip> fold entries, and
  ephemeral probe ports cannot ride a single-target 3478 pin. The
  organic Type 2 does not sign plan/0006's #a2-verdict.
- Record: plan/0006-ps3-requirements/results/RESULTS-2026-09-13-exam.md.
  Pending: the relay-attributed A2 run (retarget + re-run under capture),
  then the pbr-idiom swap (replace policy rule 25000/table 1000 with a
  pbr-package policy).

## 2026-09-13 — plan/0006: PS3 requirements milestone (A2 console acceptance)

- New milestone plan/0006-ps3-requirements, number allocated by the
  generator (host-lifecycle compiled at
  tools/host-lifecycle/target/release; `next plan/` returns 0006).
  Operationalizes the PS3 on the ds-lite line: router reconfig (DHCP
  reservation, console policy-routed via eth1, relay retarget from the
  test sink to the console's PSN UDP 3478/3479), the A2 connection-test
  run with captures both sides, and the phase-E (UPnP IGDv1) priority
  decision. The README's build sequence is the task-graph form (anchored
  tasks with verify/inputs/depends).
- Load-bearing facts from inspection: no UPnP daemon on the router, so
  nothing needs pausing and the console's IGD probe finds nothing (the
  correct interim); the default route egresses pppoe-vdsl4 (metric 16) so
  the console MUST be policy-routed into eth1 or the relay line sees
  nothing; br-lan to wan forwarding and the eth1 pin accept are already
  open; the deployed relay (26152) still targets the test sink and its
  fold map (table ip dslp) holds the sink entry. A2 pass = NAT Type 2
  plus folded egress plus true-peer-source inbound; fail = STOP.

## 2026-09-13 — A3 soak run 3: a silent mapping survives 30 seconds (probe-quiet)

- Run 3 (seed 202609133, relay 26152) closed the runs 1/2 confound with
  the probe-quiet pause: at t0 both the relay (SIGSTOP) and the
  in-container probe are silenced. Packet-level audit: 0 packets touched
  port 40000 in any pause window (any source, any direction), all 18
  cells. The inbound-refresh route to the mapping was closed.
- Result: the mapping 37.228.213.83:59230 survived every silent window
  including 30 s, tuple unchanged, recovery flat 816 to 826 ms (no
  relay-tick wait, no re-creation delay), forward one-way 14 to 17 ms
  median and no buffered-flush echoes.
- This bounds today's node's AFTR UDP idle timeout below by 30 s, at odds
  with the recorded 5 to 10 s node-dependent figure the 2 s keepalive
  cadence was built around. Either node dependence across the AFTR farm
  or a methodology difference in the original measurement; the run 1/2
  inbound-refresh finding (RFC 7857 S7) stands alongside it. A
  longer-limit run (60 s, 120 s silent windows) locates the true timeout,
  with RFC 6888's 120 s floor as the outer bound.
- The relay's 2 s cadence is unchanged and correct under either reading;
  the margin is larger than believed on today's node. Details in
  plan/0005-test-rig/RESULTS-2026-09-13-run3.md; raw data on the router
  at /mnt/nvme/runs/2026-09-13-run3.

## 2026-09-13 — AFTR refreshes UDP mappings on inbound (RFC 7857 §7 violation)

- The soak timing analysis (plan/0005-test-rig/ANALYSIS-2026-09-13) shows
  the VM AFTR's UDP mapping lifetime is maintained by inbound datagrams:
  all 36 cells across two runs survived 5 to 30 s keepalive silences while
  a probe stream was inbound (survived=y, death delay equals the pause
  duration). RFC 7857 §7 says inbound should not refresh; this
  implementation does.
- Consequence: the A3 pause methodology was confounded (no cell exercised
  real death). Mapping-death measurement needs a probe-quiet pause
  (silence the probe inside the pause window). The genuine death plus
  immediate reuse evidence is the relay restart events, not the soak.
- Solid measurements from the data: forward one-way transit 14 to 19 ms
  median (probe to sink through vdsl4, the internet, the AFTR, the
  relay); the buffer-flush deltas equal the pause durations; arrival 1 Hz
  integrity in every run-2 cell.

## 2026-09-13 — A3 soak run 2: forward leg end to end, port reuse again 18/18

- Run 2 (seed 202609132) repeated the matrix with accept_local=1 live on
  eth1: 18/18 cells done, port reuse 18/18 (37.228.213.83:59230), and the
  relay forwarded every probe stream to dslp-sink with source preserved
  (79 to 108 receipts per cell). The forward leg is now proven through a
  full campaign, not just a point test.
- The driver leak fix is validated: arrival counts match the 1 Hz probe
  exactly and every cell's sink bound cleanly.
- Summary-column caveat persists under port reuse: the driver sees no
  tuple change, so death-to-recovery latency needs the per-cell arrival
  series (raw pcaps on the router at /mnt/nvme/runs/2026-09-13-run2).
- Next measurable: the A1 reply-path leg (sink echo through the AFTR
  tuple), then C3 TCP idle-lifetime.

## 2026-09-13 — forward-leg RCA resolved: accept_local, not the relay

- The soak run 1 blocker (the relay never forwarding our probe datagrams,
  the "pre-socket consumption") is fully root-caused: the kernel's
  source-route validation drops inbound datagrams whose source equals a
  router-local address when accept_local=0 (the default). No nft rule is
  involved; accept placement, relay binary, and forward target were all
  irrelevant. The September 2 "self-probe EADDRINUSE" record was this same
  drop; P1's August forwards worked because Globalping's sources were
  genuinely remote.
- Fix: net.ipv4.conf.eth1.accept_local=1, persisted at
  /etc/sysctl.d/99-ds-lite-punch.conf. Interface-scoped; all and
  pppoe-vdsl4 stay 0 (the vdsl4 line is public, its own-address packets
  are martians, and no mirror need exists; revisit only for an inter-line
  test).
- With the fix live, the relay forwards the probe stream to dslp-sink end
  to end (JSON receipts with the masqueraded source preserved).
- The soak's above-1 Hz arrival counts were roughly 18 leaked in-container
  probe processes (the driver terminated lxc-attach wrappers without
  killing the inner pythons); the driver now pkills inside the container
  per phase.

## 2026-09-13 — A3 soak run 1: AFTR port reuse is the rule

- Full keepalive-pause matrix (5/7/10/12/20/30 s x 3, seed 20260913) ran
  via the test rig: 18/18 cells done with stable preconditions, and the
  AFTR re-issued the identical external tuple 37.228.213.83:59230 in all
  eighteen deliberate mapping kills. Port reuse on this line is the rule,
  not the exception (also observed across restarts and retargets).
- The rig's arrival-based liveness sensing is validated: eth1 captures of
  the probe flow (src 84.203.115.61 to dst 192.168.0.21:40000) measured the
  delivery gap through every pause and the resume on the re-created mapping.
- Standing limitations: the relay forward leg is still unassertable
  (inbound-NEW UDP consumed pre-socket, see plan/0005 RCA); the reply
  through-mapping leg stays an external-sender function. Raw data (396 MB)
  lives on the router at /mnt/nvme/runs/2026-09-13; the derived record is
  plan/0005-test-rig/RESULTS-2026-09-13.md.
- Operator notes for the router: busybox ash has no stat, nohup, or pkill
  (kill by PID; use the [p]attern bracket trick to avoid self-kill);
  pattern-kills of "tcpdump" or "probe-client" WILL hit the rig's own
  instruments. The deployment env still targets the test sink
  (TARGET=192.168.21.12:40002) until reverted.

## 2026-09-12 — allocate register numbers at claim time, never from memory

- A milestone folder was created as plan/0005 using a remembered allocation
  from an earlier `host-lifecycle next plan/` run. The value was correct
  (the tool now returns 0006), but the claim never went through the tool:
  the spine's rule is that the generator allocates and the operator never
  numbers by hand. The allocation is a claim-time act, not a remembered
  fact. Every plan/ or call/ claim starts with `host-lifecycle next <dir>`;
  keep the returned value in the room's README as the recorded claim.

## 2026-09-12 — the fork incursion and its guardrails

- A `gh repo fork <owner>/<repo> --clone` run with the host as cwd cloned the
  wrong, pre-existing fork (`slartibardfast/andrej-karpathy-skills`) into the
  host root, untracked. The scans walk untracked directories, so that clone
  leaked three naming tells and re-opened the remap receipt. Cause chain:
  cwd pollution (repo-creating command run inside the host), a destination-name
  collision that made the follow-up commands operate on the submodule instead
  of any fork clone, and no side-effect check until the audit complained hours
  later. The fork detour was avoidable: pushing the branch to
  `connollydavid/host-template` as the owner worked cleanly and merged.
- Guardrails: repo-creating and cloning commands run with cwd in /tmp scratch,
  never the host root; immediately after such a command, `git status` must show
  no collateral; upstream changes to connollydavid/* go direct-push as the
  owner, fork only when required; a command whose output contradicts its intent
  is a stop-and-inspect signal, not a retry prompt.

## 2026-09-12 — git auth over HTTPS: Basic, not Bearer

- GitHub's API accepts `Authorization: Bearer`; the git endpoint does not. A
  token that reads fine via the API is rejected by `git clone`. Use
  `Authorization: Basic base64(x-access-token:<token>)`, the same scheme
  actions/checkout uses. The reproducible-build lane reads the private
  `ds-lite-punch` component this way, via the `DSLITE_READ_TOKEN` secret
  (fine-grained PAT, Contents: read on `slartibardfast/ds-lite-punch`).

## 2026-09-11 — agentic-host adoption (host-template 41ba4e1)

- The repo-root investigation `DSLITE.md` moved to
  `plan/0004-ds-lite-punch/INVESTIGATION.md` and rewritten to zero prose tropes.
  It is the possibility-space record that fed call/0011 and plan/0004
  (decision call/0012).
- The ds-lite-punch software is embedded at `software/ds-lite-punch` (bare
  store + main worktree, pin f7e11e934e99; recipe in `.host-software`). The
  crate has not yet been migrated into that component repo from the former
  rope-agentic monorepo (`tools/ds-lite-punch/`); reproducibility is waived by
  call/0012 until it lands.
- Register continuation: next plan number 0005, next call number 0012.
- Network ground truth for the VM line (AFTR address, no PCP/UPnP, LAN
  addressing model) lives in call/0011 and the milestone docs; policy routing
  and IP assignments are unchanged by this adoption.

## "CGNAT UDP timeout measured"

- AFTR UDP idle timeout: (5,10) s, node-dependent. The RFC 6888 floor is
  120 s; Virgin will not change it. This is the number the relay is built
  around (2 s STUN keepalive cadence, worst-case node about 5 s).
- TCP mapping idle lifetime remains unmeasured (the TCP idle-lifetime test,
  deferred, gates TCP grants only).

## "UDP hole punching works"

- The AFTR is endpoint-independent mapping and filtering (EIM+EIF) for UDP:
  consistent mapping under rotating STUN, and unsolicited inbound to the
  mapped tuple is delivered.
- External ports are always AFTR-chosen random-high, never the inner source
  port (no source-port preservation).
- The v1 core's live tuple 37.228.213.52:24258 held stable under 2 s
  keepalive; external UDP probes from four or more countries forwarded with
  peer source preserved.

## "TCP EIF" (full method)

- Proven 2026-08-31. Setup: the client held a TCP mapping open, inner
  (192.168.0.21, 32014), external 37.228.213.83:59390, discovered via STUN.
  Our vdsl4 line acted as the dual-homed source-port oracle (third party).
- Probes: 5/5 globalping HTTP probes (DE/BR/JP/US/AU) returned HTTP 200 from
  the router-side twin listener. Each response body echoed the exact post-AFTR
  source IP the AFTR forwarded, matching the twin's accept log 1:1.
- Control: probes to an unmapped port in the same batch returned 5/5
  `ECONNREFUSED` (AFTR RST, unchanged behavior).
- Consequence: endpoint-independent filtering holds for TCP as well as UDP; a
  TCP mapping is reachable by any external address. The relay stays UDP-only
  by product decision, not CGNAT limitation.
## The WIP2 surface is transcribed from its own spec

The WANIPConnection:2 service (the v2 face of the plan/0008 facade) is now
transcribed from the normative document rather than assumed, the way the
DeviceProtection:1 service was (the entry above on the DP:1 SCPD). Component
docs/upnp-wip2/ holds the source PDF, the conversion and TRANSCRIPTION.md.

The facts that replaced assumption, each worth not re-deriving:

- The service carries 21 actions, not the 22 the placeholder declared. The
  extra one, GetLinkLayerMaxBitRates, belongs to WANCommonInterfaceConfig.
- Every action relates its arguments to the state variable it names, except
  NewManage and NewPortListing, which relate to A_ARG_TYPE_Manage and
  A_ARG_TYPE_PortListing. The placeholder's A_ARG_TYPE_ExternalPort,
  A_ARG_TYPE_InternalClient, A_ARG_TYPE_InternalPort, A_ARG_TYPE_Protocol
  and A_ARG_TYPE_LeaseTime do not exist in this service.
- The state variable is NATEEnabled. The placeholder spelled it NATEnabled.
- Exactly five variables are evented (table 2-9): PossibleConnectionTypes,
  ConnectionStatus, ExternalIPAddress, PortMappingNumberOfEntries and
  SystemUpdateID. PortMappingNumberOfEntries and SystemUpdateID are evented
  together whenever a mapping is added or removed (2.4.4, 2.4.5).
- A lease of 0 is not a static mapping in version 2: it MUST be read as
  604800 seconds. Static mappings are made out of band only.
- The PortListing fragment is a PortMappingList of PortMappingEntry elements
  in the urn:schemas-upnp-org:gw:WANIPConnection namespace, with the entry
  fields as child elements named NewRemoteHost, NewExternalPort,
  NewProtocol, NewInternalPort, NewInternalClient, NewEnabled,
  NewDescription and NewLeaseTime. The schema URL the spec names
  (http://www.upnp.org/schemas/gw/WANIPConnection-v2.xsd) answers with an
  HTML placeholder now, so the sample document of 2.3.25.2 is the shape
  authority. A query returns the remaining lease, not the granted one.
- Error codes 724 to 727 are accepted on input and MUST NOT be emitted by a
  version 2 device; 730 PortMappingNotFound is required on an empty range
  and 733 InconsistentParameters on a crossed one.

Still open on the v2 path (the IGD_V2 gate stays off): the AddAnyPortMapping
wildcard (0) request is refused, the 730 and 733 refusals are not returned,
the lease 0 rule is not implemented, and the description string a control
point sends is not persisted (the listing reports it empty).

## The v2 readings that replaced the placeholder's refusals

Component a339747 closed the v2 behaviours the transcription named. The
facts worth keeping:

- The AddAnyPortMapping wildcard (NewExternalPort 0) was refused 402 by
  the argument parser before the facade ever saw it. The parser now
  admits the wildcard for this action only (parse_add_args_impl's
  wildcard_ext flag), and the facade reserves the lowest requested port at
  or above 1024 that no entry of the protocol claims. AddPortMapping keeps
  refusing it, as the v1 facade always has.
- The range parsers reported a start above the end as a generic 402; the
  spec's own code is 733 InconsistentParameters, and 730
  PortMappingNotFound is required when a range action finds nothing. Both
  joined the fault table. A range action that finds nothing touches no
  engine, so those two paths are wire-testable without nft.
- A lease of 0 stays the permanent mapping on the v1 face (a legacy
  control point's static mapping) and means 604800 on the v2 face
  (table 2-6). The translation sits at the dispatch arms, keyed on the
  SOAPACTION URN version, not inside add_mapping.
- The facade's lan containment check rejects a client outside the /24, so
  a wire test that wants to reach the engine past it must use
  127.0.0.1 with the loopback LAN. nft still fails in tests, so an
  accepted request answers 501, which is what an anti-stub assertion
  looks for.

## The unauthenticated listing is a plan decision, not an oversight

The device's policy (required_role in dp.rs) protects the four mapping
mutators behind an authenticated Basic session and leaves every other
WANIPConnection:2 action public. So an unauthenticated GetListOfPortMappings
is answered in full, where the spec's 2.5.21.3 recommends restricting it
to the control point's own entries and to ports at or above 1024.

This is recorded in the component transcription and in plan/0008 section
27.3c as the reading not taken, deliberately. Tightening it would change
the section 24 matrix and the boundary design, so it is a plan change to
be taken with the operator, never a quiet transcription detail.

## The OCR conversions carry expiring figure URLs, so re-host them at receipt

The GLM-OCR markdown exports reference their diagrams as signed crop URLs at
the converter's object store (`maas-watermark-prod-new.cn-wlcb.ufileos.com`,
with `Signature=` and `Expires=` in the query). The signature is time-limited;
the DeviceProtection:1 figures were lost that way and had to be re-hosted from
memory of the source.

The rule that follows: when a conversion lands, fetch every `img src` it
carries in the same session, commit the crops under the component's
`docs/<service>/images/`, and rewrite the reference to a relative path. Then
the markdown and its figures are durable together. A conversion can also
render a figure as a table instead of a crop (WANIPConnection:2's Figures 2-3
and 2-4 are exactly that), so the image count need not match the List of
Figures.

## T2 is closed: the v2 facade is mounted, and three readings of table 2-10

plan/0008 #v2-service-set is receipted done; the IGD_V2 gate is on in the
source (component 4d0160f). Three readings of the WANIPConnection:2 action
table, each correcting the one before, are worth not repeating:

- The placeholder took miniupnpd's action list (with a bogus 22nd).
- The first transcription took the spec's whole 21-action list as required
  of a device, which table 2-10's device column does not say. It splits
  them: fourteen REQUIRED, seven OPTIONAL.
- The dispatch had eleven arms, so ten actions the published SCPD
  advertised would have answered 401. An SCPD must describe what the
  device implements: the fourteen required are dispatched and the seven
  optional are neither advertised nor dispatched.

The four added required actions and their answers: SetConnectionType 731
ReadOnly (2.5.1's read-only note for an auto-configured connection),
RequestConnection success while the tuple is present and 704
ConnectionSetupFailed without it, GetNATRSIPStatus RSIP 0 / NAT 1,
ForceTermination 501.

ForceTermination's refusal is a security decision, not a gap: the facade
does not own the WAN lifetime (netifd and the ISP do) and the action is
public on the v1 face, so honouring it would give every LAN device a lever
that drops the household line for every client. The action's own error
table has no code for a device that may not, so 501 is the answer, and
that is recorded in the plan (27.3d) and the transcription.

Also landed with T2: the control point's NewPortMappingDescription is now
stored and returned rather than replaced by a device string (the label is
control-point text, so the parse drops control characters that could forge
a persisted row and the writers escape XML metacharacters), and the packet
tests now assert section 24's discovery and document rows, including the
deferred ssdp:all answer landing at the debounce deadline and an in-window
:2 flipping both answers to v2.

Still open on the v2 path, and named in the T2 receipt: SendSetupMessage
answers 600 for an unknown ProtocolType and 704 for WPS. The WPS
Registration Protocol (DP spec Appendix A) needs the Wi-Fi Alliance
specification, which is not internalized, and Appendix A requires the
exchange to run inside a certificate-authenticated TLS channel that this
plain-HTTP facade does not carry. That is a decision for the operator:
supply [WPS] and a TLS posture, or record the 704 as a device-capability
deviation.

## T3 closed: AddAnyPortMapping must not evict, and the engine now says so

plan/0008 #canonical-api is receipted (component b22a96d). The defect it
found: AddAnyPortMapping was routed through the same engine call as
AddPortMapping, so a request for a port another client held took that port
over. Section 2.5.17 says the gateway reserves any free port instead and
returns it as NewReservedPort — that reserved port is the whole reason a
control point calls the action. A client silently losing its mapping to
another client's preference is the kind of thing that never shows up in a
unit test that mocks the engine.

The engine is now reached through two entry points, which is what plan
section 17 asked for: allocate_exact (the requested port is
authoritative; a different requester takes a held port over) and
allocate_preferred (the requested port when free or the requester's own,
otherwise any free port of the protocol). preferred_port is the pure
resolution, so the contrast is asserted directly rather than through a
granted mapping; the wire and facade tests could not have caught it
because nft is absent in tests.

## The WPS limb is a decision, not an open question (call/0021)

David: "WPS spec will not be available internally." The DeviceProtection
setup ceremony's WPS limb therefore cannot be transcribed, and it is now
recorded rather than carried as a question: call/0021

  - advertise WPS, because 2.4.3.1 mandates the entry in
    SupportedProtocols and the protocol must be in the list a
    SendSetupMessage ProtocolType may name;
  - answer a WPS setup attempt with 704 Processing Error and an empty
    OutMessage, the action's own code for a failure to process InMessage;
  - reject 600, whose meaning ("the ProtocolType value is not supported by
    the Device") would contradict the list the device just published.

The two reasons are worth keeping: the message encoding lives in the Wi-Fi
Alliance WPS specification (not available, will not be internalized), and
Appendix A requires the exchange inside a certificate-authenticated TLS
channel, which this plain-HTTP facade does not carry. Reversing it needs
both: the WPS specification internalized as a component source, and a TLS
posture decision for the exchange.

Recorded at plan/0008 section 27.3e, in the component transcription
docs/upnp-dp1/TRANSCRIPTION.md, and in a fresh T2 receipt that replaces the
one which called it open.

Also repaired: plan/0008 section 12 cited call/0021 for the discovery
reversal, and no such record existed (the refs sweep called it a dead
pointer). The reversal it describes is call/0020, which supersedes the same
absolute in that section, so the pointer now names it. A register citation
written for a decision that has not been allocated yet is a trap: allocate
first, cite second.
