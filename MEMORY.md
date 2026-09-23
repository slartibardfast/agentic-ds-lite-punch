# MEMORY: working memory (append-only)

Ground truth, measurements, and session state that a fresh session needs. Newest
entry on top. Append, never rewrite; an entry that is wrong is superseded by a
newer one, not edited.

## 2026-09-17 — state hand-off: where the work stands and what is on the box

Written for a session with no memory of this conversation. Everything below
is committed and pushed unless it says otherwise.

- **The programme.** `call/0025` is the policy spine (the allowlist as
  admission for maintenance, the RFC-norm timeouts in the ruleset, the
  cadence from the measured threshold, one truth projected per dialect,
  PCP as the fourth admission, the TCP bound, the WPS boundary).
  `plan/0009-mapping-hold-and-signalling/` is the build: its README carries
  the milestone, the seven anchored tasks, the four-stage rollout and the
  acceptance, and its `IMPLEMENTATION.md` carries the line-by-line detail
  with the validated ruleset, the exact commands and what falsifies each
  task. `plan/PLAN.md` carries the index row. The newest component pin is
  `ad69a49`.
- **On the router, deployed and persistent:** the daemon at `ad69a49`
  (md5 `1518f455…`, pid 32329 at hand-off) installed as
  `/usr/bin/ds-lite-punch` with the outgoing build parked at
  `/root/ds-lite-punch.prev`; the deploy assets installed from the pin; the
  DHCP static host `switch` = `80:d2:e5:6d:d1:00` = 192.168.21.68
  committed through uci; the relay tuple around `37.228.213.83:59304`.
- **On the router, runtime only and lost on reboot or a netifd reload:**
  the two source rules that put the consoles on the Virgin Media line,
  `from 192.168.21.68 lookup 1000 priority 25000` and
  `from 192.168.21.138 lookup 1000 priority 25001`, with table 1000
  holding `192.168.0.0/24 dev eth1` and `default via 192.168.0.1 dev eth1`.
  Without them the consoles fall back to the main default, which is the
  Digiweb pppoe line. Revert with `ip rule del from <addr> lookup 1000`
  and `ip route flush table 1000`. Making them persistent is an open
  operator question, as is installing the timeout policy.
- **Not installed:** the conntrack timeout policy itself. Rollout stage 2
  of plan/0009 is where it lands, and it awaits the operator's word. The
  validation on 2026-09-17 applied nothing: the objects were created
  inertly and the table deleted.
- **The capture taps are stopped** and their output is at
  `/mnt/nvme/captures` on the router (27 files plus `MD5SUMS`), mirrored on
  the workstation at `~/captures-2026-09-17-final`, with an earlier
  snapshot under `~/captures-switch-2026-09-17/`. Nothing further is being
  recorded on the wire.
- **The next step.** plan/0009's first task: seed the allowlist admission
  for the two pinned consoles, with the policy objects and the selection
  rules in the shape `IMPLEMENTATION.md` records, then prove that a quiet
  allowlisted flow outlives an unallowlisted one.
- **Two defects and one deferral still open**, none of them touched since
  they were found: the rig's stale `upnp.tsv` row (`14572` claiming the
  console's slot `40002`, which a delete would revoke through
  `delete_by_bind_port`); the household `3074/UDP` mapping that went
  missing inside the first deployment window of the 2026-09-17 session and
  was never restored; and the WPS introduction limb (call/0021), which
  needs the Wi-Fi Alliance specification plus a certificate-authenticated
  transport, or an explicit acceptance of the operator bootstrap
  (call/0023) as the administration path.
- **Carried work with a home:** the AFTR's UDP threshold under silence
  (plan/0009 `#udp-threshold`, with the shorter windows the earlier
  milestone already named), the Kani re-derivation (the remediation branch
  and the state record on this host), and EIF-loss detection.

## 2026-09-17 — the admission policy and its milestone written, and what PCP already had

- **call/0025** fixes the allowlist as *admission for maintenance* with no
  authority attached, alongside the RFC-norm timeouts declared in the
  ruleset, the pairing of the local conntrack half with our own writes to
  the AFTR, the cadence set from the measured threshold, one truth
  projected per dialect with per-subscriber scoping, PCP as the fourth
  admission, the TCP bound, and the WPS boundary.
- **plan/0009** is the build: seven tasks with anchors, verify and inputs,
  a four-stage rollout, and a silence acceptance with an outside witness.
  The index row is in `plan/PLAN.md`.
- **PCP was already the design.** `plan/0004/IMPLEMENTATION.md`'s mental
  model reads "Admission: config | PCP | UPnP | observation", and the same
  document specifies the listener (192.168.21.1:5351/udp, LAN-only, PCP and
  NAT-PMP sharing the port, quota 16, result codes 0 to 8 plus 9). It is
  unbuilt, and nothing on the LAN speaks it today.
- **Conntrack-as-CDC was already decided too.** `cdc.rs` carries the three
  backends with the nft `flow_obs` mirror primary (post-routing observer
  whose elements are the post-NAT tuples), `/proc` as fallback and an
  unwired Aya TC tier; netlink CT events are silent on this build. So
  Track 1 is an extension of the existing path, not a new reader.
- **The AFTR's TCP idle lifetime is measured**: between 120 and 300
  seconds, so a VPN connection with sparse keepalives really does lose its
  mapping — the TCP question is real, and the answer is bounded by what
  the relay terminates because a router cannot write into a client's
  sequence space.
- **The ruleset shape this build accepts** (validated inertly, then
  removed): `ct timeout <name> { protocol udp; policy = { unreplied : 5m,
  replied : 5m } }` with `protocol`, **not** `l4proto`, and the TCP state
  set narrower than upstream (`unacknowledged` is rejected). Selection is
  by source address, which is stable because the allowlisted devices are
  DHCP-pinned; `ether saddr` is not available in the inet family.
- **The WPS boundary, recorded**: the allowlist confers no identity, so it
  does not substitute for the introduction protocol call/0021 defers; if
  that limb is ever built its identities should feed the list, and
  deriving device authorization from the list would reverse call/0021 by
  policy and needs its own decision.

## 2026-09-17 — the pin is deployed and verified on the box, and a tag-name trap

- The pin (ad69a49) is **live on the router**: built to the recorded recipe,
  installed as `/usr/bin/ds-lite-punch` (md5 `1518f455…`), outgoing build
  parked at `/root/ds-lite-punch.prev`, service restarted onto it (pid
  32329) with the new init script; the seed stayed inert for want of
  `/etc/ds-lite-punch.acl`. The tuple re-established at
  `37.228.213.83:59304`.
- **The listing fix is verified on the deployed box**, not only in the tree:
  a v1 `AddPortMapping` for the caller's own host answers 200, and the v2
  `GetListOfPortMappings` response carries `<NewPortListing><![CDATA[` with
  the entry inside; the v1 delete answers 200 and it leaves the table. The
  contained caller saw its own entry and no other.
- **Trap worth remembering:** the AddPortMapping *argument* is
  `NewPortMappingDescription`, while the *listing entry element* is
  `NewDescription`. A request that names the listing's element stores an
  empty description and the listing reports one, which reads like a defect
  until the tag is checked. `parse_desc` reads the argument name.
- The stale-slot inconsistency survives the restart: `upnp.tsv` still holds
  the rig's row `14572 … bind_port 40002` alongside the PS3's `3074 … 40002`
  while `leases.tsv` grants 40002 to the console alone. A delete of the rig's
  entry would revoke the console's slot through `delete_by_bind_port`. Not
  touched; it needs its own investigation and fix.
- The peer-inbound picture is a one-evening census: every game peer was
  contacted by the console first, so no peer sent first in the window. Both
  records carry that limitation; longer runs are needed to widen it.

## 2026-09-17 — the Switch measures NAT type A on the VM line, and how the captures were misread

- **The "big if" is answered.** A Nintendo Switch (`80:d2:e5:6d:d1:00`,
  192.168.21.68, a USB Ethernet adapter) routed onto the Virgin Media
  ds-lite path (`vm4` = dhcp on eth1 → hub → AFTR) reports **NAT type A**.
  The evidence and the one caveat are in
  plan/0004-ds-lite-punch/RESULTS-2026-09-17-switch-nat-type.md.
- The console's own NAT check is on tape: it asked 3.74.50.213 on ports
  33334 and 10025 for its mapping, and 40 ms later **port 50920 of the same
  host**, a port it had never written to, sent five 16-byte packets to its
  mapped port 57216 and they arrived. That is the filtering test passing
  through the AFTR, on the VM line (the Digiweb capture holds none of it).
- Mapping: one local port (57216) served eight peers with inbound within a
  few percent of outbound on each (16,501/16,554, 13,517/13,081,
  10,245/9,931). Source-port preservation is not needed by this class.
- **The PS3's P2P rode the facade, not its own NAT.** `nft`'s `dslp snat_map`
  folds `192.168.21.138:3074 ↔ 192.168.0.21:40002`, and on the VM side
  peers' packets arrive at the slot (4,852 from `87.59.252.198:3074` alone),
  with the same 4,852 delivered to the console on br-lan. A real console's
  game traffic carried end to end through the AFTR by the facade.
- **Two of my own readings were wrong and the cause is now known.** `cat
  file1 file2 | tcpdump -r -` does **not** merge captures: tcpdump reads the
  first file and stops (control: 53,451 packets reported against 148,324
  with `mergecap`). Every `cat | tcpdump` aggregate I reported was
  first-file-only, which is exactly why the Switch's game UDP "did not
  emerge" and why the Digiweb and PS3 inbound reads came back empty. Merge
  with `mergecap` (installed on this host alongside tcpdump and tshark) and
  analyse the merged capture.
- Also corrected: my flag that the missing per-slot accept rules (none for
  40000 or 40002, only 40001) might block inbound. Inbound arrived and was
  delivered because the flow-matched conntrack accepts it; the caution is
  retired.
- **The router's clock was corrected backwards by about 38 minutes** during
  the session, so pcap timestamps written before the correction read ahead
  of the wall clock after it. Ordering and intervals inside a capture are
  unaffected; quote intervals rather than absolute times when correlating.
- The captures live at `/mnt/nvme/captures` on the router (27 files plus a
  `MD5SUMS` manifest), mirrored on the workstation at
  `~/captures-2026-09-17-final`. Four taps were used: br-lan, eth1 (VM
  side), `pppoe-vdsl4` (Digiweb side) and the raw eth2 device. The Digiweb
  IP side is `pppoe-vdsl4`; capturing the raw `eth2` shows only PPPoE
  frames, which is why filters aimed at `84.203.115.61` on `eth2` matched
  nothing.

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


## 2026-09-17 (late): plan/0009's four code tasks are built, deployed and proved on the router

The hold, its admission, the signalling and the shared port are implemented,
and the milestone's results record is
`plan/0009-mapping-hold-and-signalling/results/RESULTS-2026-09-17-implementation.md`.
The component is at `acd1162` and the deployed binary is that build (md5
`cd8e49be`); the previous ones are parked at `/root/ds-lite-punch.prev` and
`.prev2`. The suite went from 121 tests to 168, written before their
implementations.

What the router proved, since a claim is not evidence:

- the PCP and NAT-PMP surface, read back with `deploy/pcp-probe.py` (shipped
  with the crate): ANNOUNCE, MAP, renewal and delete, the four refusals
  (UNSUPP_PROTOCOL, EXCESSIVE_REMOTE_PEERS for a filter this datapath will not
  install, CANNOT_PROVIDE_EXTERNAL for PREFER_FAILURE, ADDRESS_MISMATCH for a
  client field the source does not match), the NAT-PMP public address, map and
  delete, the unsupported opcode, and the drop-then-retry rule for a mapping
  whose discovery is in flight;
- the assigned tuple is the one the slot's STUN discovery learned, not a
  suggestion echoed back;
- both allowlist failure modes name themselves before any work is done;
- `PCP=1` is now in `/etc/ds-lite-punch.env` on the router, so the shared port
  is live. Its revert is that line removed and a restart.

A defect the box found, and its fix: a revoked mapping left its per-slot
tuple file behind, and because the allocator hands out the lowest free slot, a
fresh grant on that port was answered with the dead mapping's external port
(three such files were on the box, from mappings revoked hours earlier). Fixed
at `acd1162`: every revoke path removes the file, and the same probe then
showed the drop followed by the fresh tuple. The triangulation is worth
keeping: the client's port could not have been invented by the new code,
because the new code reads that file, and the file was on the box.

Deliberately not done, and waiting on the operator: installing the conntrack
policy. It is the one change that puts new nftables rules on the live firewall,
so it was left alone rather than attempted around; the results record carries
the exact command. The acceptance under silence and the AFTR's own threshold
need the same session.

Two traps this session hit, both worth the ink. A pin is a value, not a
recollection: a hand-typed SHA suffix was wrong at the first attempt, and only
the tool's own echo of `rev-parse` caught it. And a verbatim client transcript
in an authored doc trips the naming lane on its protocol quantities (`epoch
18`), which is the case the sanctioned boxed block exists for: the block stays
verbatim, the rest of the file stays linted.


## 2026-09-18: the collision rules for punched ports, and what the box proved

A port becomes this daemon's in two ways: an allocation (a lease, a row, a
bind port) and a punch (a datagram the AFTR maps because it saw one). Only the
first had a rule, so `call/0027` states both in the RFC idiom the PCP and
NAT-PMP work was held to: the incumbent keeps the tuple, an allocation probes
before it claims, a late collision moves the allocation and never the punch,
the requested port is a label rather than a reservation, and no collision is
resolved in silence.

Three of the rules are enforced at `a9e5bd19` (deployed, md5 `a9e5bd199b75`):
the allocator's probe over the live post-NAT set, the observation arm reading
the live lease table each tick instead of the snapshot it started with, and a
log line for every steering decision. The box read the rule back on the first
fresh grant:

    {"event":"collision-avoided","detail":"slot 40003 steered around the live tuple(s) [40001]"}

Slot 40001 was live and unallocated, which is exactly the case the rules were
written for; the two slots the table held are absent from the list because
avoiding those is the allocator's ordinary business.

Two questions are named as experiments rather than answered: whether the local
NAPT can punch a port a local socket already holds (the trigger for the
late-collision rule), and whether the AFTR ever answers one external port to
two inner tuples. The second is observable passively in the per-slot reads.


## 2026-09-18: the acceptance run, and the two defects it found

plan/0009 is done and its records are
`results/RESULTS-2026-09-18-acceptance.md` (the box work) beside the earlier
`RESULTS-2026-09-17-implementation.md`. The component is at `5bcc9d6a` and the
deployed binary is `9049ba42`.

The measurements, in the order they falsified something:

- **`ct timeout set` needs a post-conntrack hook on this build.** The policy
  installed cleanly and did nothing: an allowlisted flow read 57 s, the
  router's default. One hook later (mangle priority, where the conntrack hook
  has already created the entry) the same statement read 297. The chain moved
  to mangle and was renamed `hold`, because `preraw` described a hook that
  does not work. The plan predicted this class of failure in its own
  falsifier, and the falsifier is what fired.
- **The proof, same device, one list edit apart**: named read 296 s and was
  alive at t+65 s; unnamed read 55 s and was gone by then.
- **The held mapping was reachable from outside** at t0+31.4, 61.4, 121.4 and
  301.4 s of client silence, and the router forwarded each to the client's
  address with the sender preserved. The client application did not receive
  them, and the reason is the test client's own second NAT (WSL): a packet
  from a peer its flow never spoke to has no mapping there. The router's hops
  are the ones the daemon owns.
- **The AFTR reaps an idle UDP mapping between thirteen and twenty-one
  seconds**, not the five to ten the milestone was written against: an unheld
  flow was still reachable at t0+13.4 s and gone by t0+21.3 s. The two-second
  cadence sits comfortably inside that.
- **The event surface, driven by a real control point**: an initial event with
  all four declared variables and a count of zero while the table held the
  consoles' mappings, then add and delete each carrying only the two variables
  that moved, the contained subscriber seeing its own namespace alone.
- **An arm defect, found by asking where a re-key would show**: the arm
  reported only the first tuple, so a mapping the AFTR moved under a held flow
  would have been invisible. It now reports per observation.

Two lessons worth more than the numbers. An instrument has not been shown to
work until it has recorded a known event: a capture whose filter busybox
refused never started, and its zeros read as "no arrival" until a control
showed the difference. And a policy can be installed, readable in the table,
and inert: only a reading of the flow's own state says whether it is doing
anything.

Still open: whether any device here needs the hold in the field, and the last
hop to a client behind a second NAT.


## 2026-09-18 (later): the collision is reachable, the incumbent keeps the tuple, and a console closed the client hop

Three measurements from the same session, all on the router with captures
that had recorded a known event first (the earlier run's zeros were an
instrument that never started):

- **The NAPT translates into a held port.** A socket holding `(192.168.0.21,
  52021)` did not stop a console-sourced flow from being masqueraded with
  `sport=52021`: port preservation asks for the source port first and the
  selection consults connection state, not socket bindings. So a device whose
  own outlet port falls inside the slot range lands on a slot's tuple, and
  `call/0027`'s late-collision rule is reachable rather than hypothetical.
- **The incumbent wins the inbound.** On a shared tuple the AFTR-forwarded
  datagram went to the *device* (`src=192.168.21.138` in the reply tuple), not
  to the shadow socket bound on the same port, and the device's own stack
  answered ICMP port-unreachable because its socket had closed. The harm of a
  collision therefore falls on the slot, whose peer expected to reach a
  different client, and the device's working session is untouched, which is
  the right direction.
- **A console closed the acceptance's client hop.** The arm held four console
  flows; probes to their learned tuples arrived after several minutes of the
  console's silence and were delivered to the device with the sender
  preserved. The workstation run could not show this because its own second
  NAT drops a packet from a peer its flow never spoke to.

The precedence is a feature for the device and a defect for the slot, so the
slot must yield on detection and the substitution must be reported. The
detection signature is the daemon's own bound socket appearing in a
connection entry whose pre-NAT origin is a device, which is state the daemon
already reads for identity.

`call/0028` records all of it; the experiment ships as
`deploy/collision-probe.py` so the next run is one command.


## 2026-09-18 (later still): the late-collision rule is implemented, and the router narrowed it

`call/0027`'s R4 now lives in the daemon: the table detects the signature
`call/0028` named (a connection entry whose NAT side is one of our bind tuples
while its origin is a br-lan host), the facade moves the lease to a port the
probe leaves free and reports the substitution, the arm reports a tuple it
refuses instead of capturing, and a move that cannot complete leaves the slot
working where it was. 182 tests, seven of them new.

The router then narrowed the rule instead of widening it, and the readings are
worth keeping:

- a bare socket holding `(192.168.0.21, 52021)` did not stop a console-sourced
  flow being translated with `sport=52021` (call/0028);
- a live slot did stop it: with the daemon's shadow on `40001`, the same flow
  came back at `1024`, because the slot's own keepalive holds the tuple in the
  connection table and the port selection reads that table. So the reachable
  window is a held port with no live entry: granted-but-not-punching, a relay
  gone quiet, or a configured port whose holder is idle.

The deployment gave the detection a real negative control: the live table held
an entry whose NAT side was the lease's port (the slot's own 68-packet punch)
and the detection did not fire, because its origin was the NAT address rather
than a device.

Deferred, not attested: the yield's end-to-end acceptance. A forwarded flow
must take a leased port for that, which needs its inlet port known and pinned,
and the workstation sits behind a second NAT that rewrites it. A console on
the LAN can be the client, and the run is recorded as owed.


## 2026-09-18 (field session): two consoles, the hold under real play, and a state-directory incident

The arm held both consoles' *own* flows for the first time (the Switch on a
game flow to port 10025, the PS3 on its own), and the Switch still negotiated
**NAT Type A** — the field confirmation of `call/0028`'s precedence: a device
keeps the inbound its flow earned, so our hold costs it nothing. The PS3 read
Moderate (Type 2) with its 3074 mapping live through a facade slot; that slot
has been 40002 in one reading and 40003 in another, because a restart
re-grants the entries and the allocator picks a free port, so the console's
external tuple moves when the daemon restarts and the game relearns it.

Then an incident worth the ink. `/tmp` filled and every write into the state
directory failed. The cause was mine: four stale `tcpdump` processes were still
writing into *deleted* files and held gigabytes of the tmpfs. Killing them
returned 52 MB of 7.7 G in use. But the consequence was already on the record
as a mystery: `upnp.tsv` was 0 bytes, so the entry table had not been durable
since 03:16, and **the household 3074 mapping "lost in the first deployment
window" was this defect** — the entries record was renamed into place
unconditionally, so a failed write published an empty tmpfile over the good
table. Fixed at `4795061d`: rename only on success (with a test that forces the
failure), and the tuples and tables now live in memory first, with the first
failure and first success each reported once. The recovery is verified on the
box: after the filesystem was freed, a lease renewal made both tables come back
with their real content, the PS3's 3074 row included.

A new reading trap: `ls -l /proc/<pid>/fd/<n>` prints the **symlink's** length
for a deleted file, not the file's size, so a deleted-file scan reported 64
bytes each while those processes held gigabytes.

The new build is committed and pushed and deliberately not deployed: the daemon
was mid-session, and the running build persists correctly now.


A prose-lane pattern worth keeping, from five rewrites in one session of
authored records: "from X to Y" reads as a false range, a dotted numeral
("7.7", "2.67") reads as a section reference, and a "no X: ... and it is
also" construction reads as negative parallelism. None of the three is
visible to me while writing; all three are cheap to reword once flagged.


## 2026-09-18 (root cause): the tuple a console's type rides was held by nobody

The PS3 read Strict while the Switch read Type A, and the difference was one
predicate. A console's NAT type is decided by its *own* post-NAT tuple; the
facade's slot keeps a different inner tuple (its relay port, not the device's),
and the arm — the only mechanism that can hold an arbitrary tuple — refused the
console's flows because they were `[UNREPLIED]`, while its budget went on the
same console's one-second DNS lookups, which it held forever because the exit
rule read the mirror its own writes keep populated.

`call/0029` states the rule: the allowlist admits an unanswered flow, liveness
is the device's packet counters or a peer's probe and never ours, device
presence is a LAN ICMP probe for the GC, capacity is per device, and a failed
write is never fatal (with `panic = "abort"` set, a poisoned lock or a broken
stdout pipe would otherwise abort the daemon: every lock now recovers, every
emitted line drops its error). Component `0b986268`, 189 tests, built as
`c3351220`.

Pending: the deploy and the field check it exists for, the console's type back
at Open.


## 2026-09-18 (deploy): the fix is on the router, and the presence probe had to change

Deployed `171af463` (component `1b98cc71`). The hold's admission fix went on
first, and then the GC's instrument was measured before a run could rely on
it: **both consoles drop ICMP** — `ping` to the Switch and the PS3 answered
"does NOT answer" while the Switch was demonstrably present — so an
echo-based presence probe would have read a live console as gone and released
every hold for it about twenty seconds after claiming it. The neighbour table
is the instrument: a console that drops ICMP still answers ARP, `STALE` or
`REACHABLE` with a MAC means present, `FAILED` or `INCOMPLETE` means a probe
went unanswered, an echo is only a trigger when there is no entry to read, and
an instrument that cannot run answers present. Lucky timing: the boxes were
idle, so the arm had claimed nothing and the bad probe never fired.

Worth separating from the instrument: the PS3 was genuinely absent at that
moment (`FAILED`, no ARP), which is why the arm was holding nothing at all.


## 2026-09-18 (in game): the two-tuple fault, found live

The console's type was Strict because **its game flows egressed on two
different external tuples at once**: some on its own preserved 3074 and some
on a slot's port. The connection table made it plain — one flow with 14,740
packets on the slot's port beside siblings keeping 3074 — and two external
tuples for one game is what a console scores Strict or Moderate. `call/0014`
had already settled the principle: the console's story is organic, "works
alongside, not enabled by" the relay.

Three mechanisms pinned the *device's* key, and each had to be found against
the map rather than reasoned about, because I attributed it to the facade
first, then the statics, and only the third reading showed the arm doing it
too:

- the arm pinned `(client, port) -> our port` when what its shadow needs is
  its own egress pinned;
- the facade's grant pinned the client's own key (removed: the relay's inbound
  needs the accept rule and its own socket, never the client's egress);
- the operator's static relay keeps its own target pin, which is the legacy
  design for the rig and is left alone.

Also fixed on the way, all found live: a claim now waits for the device to
stop refreshing a flow (the DNS churn had filled the device's capacity, so its
game tuple could not be held); a hold is no longer released for going quiet,
because quiet is what a hold is for; a pin that meets a stale element replaces
it rather than refusing, since a stale value mis-translates a device's traffic
while nothing looks wrong; and device presence for the GC comes from the
neighbour table, because both consoles drop ICMP.

Deployed `03a36a67` (component `13a67143`). Measured after: one claim in
thirty seconds instead of twenty-three DNS claims, no releases on quiet, the
map holding only the operator's static pin, and the console's live flows back
on 3074.


## 2026-09-18 (consoles off): what the daemon does with nobody home, and one asymmetry

With both consoles off, the daemon is idle and clean: no claims, no releases,
no holds for the absent devices, no fatal or state-write failures, and the
policy still in force. The arm holds nothing because the flows ended and the
capture reports none, and the budget is untouched for the next session. The
presence reads were the PS3 at FAILED (no ARP) and the Switch at STALE with
its MAC, which is last-known rather than live: the daemon only probes devices
it holds, and it holds none.

The asymmetry worth naming: the **facade's** slots are not covered by this
GC. The console's 3074 mapping was requested with no expiry, so its slot
(socket 40004) persists and its keepalive spends about half a packet per
second holding an AFTR mapping for a device that is not on the LAN. The same
device-presence rule answers it: a mapping whose client has gone should be
released, and the client re-requests it when it returns. Until then the cost
is one slot and one mapping per absent client.


## 2026-09-18 (from scratch): the presence rule, and a mapping that ends with its device

`call/0030` states it: a client-requested mapping ends when its client leaves
the LAN and never when it is quiet. Quiet is a lobby, a paused game and a
sleeping screen, which is exactly what a mapping must survive; a device that
is gone has nothing to be promised, and it asks again when it returns. One
rule (`src/presence.rs`) now decides presence for both mechanisms that hold
something for a device, the arm's holds and the facade's leases.

Measured live with both consoles off: the arm's release rule and the facade's
hand disagreed before, and the console's mapping sat there with its keepalive
running for a device that was not on the LAN. After the deploy, the presence
pass released it on its second tick:

    {"event":"mapping-released","detail":"192.168.21.138:3074 asked for 3074 and is no longer on the LAN; its mapping goes"}

the entries file emptied, the only socket left was the operator's static, and
the rig (present, STALE with its MAC) was untouched. Component `68c2e2d5`,
deployed `ce6cc566`, 192 tests.

Two mistakes of mine that the live test caught and the code now records: the
GC runs as one pass per tick, so a miss counter local to the pass resets
before it reaches any threshold (it belongs on the facade), and a guard must
not be held across the release await (decide under the lock, work after).


## 2026-09-18 (hand-off before compact): the state, and what the overnight run is for

**Deployed:** component `68c2e2d5`, binary `ce6cc566` (pid 16100), host `44481a9`,
pin in step, 192 tests. Policy in force for both consoles; PCP live; the
observation arm up with `allowed: 2`.

**Where the overall goal stands.** The daemon's purpose is met and verified:
the PS3 reads Open and the Switch Type A, with the mechanism understood and
fixed — three mechanisms were pinning the *device's* key so one game egressed
on two external tuples at once (measured: one flow with 14,740 packets on a
slot's port beside siblings on its own), the arm refused the console's own
unanswered flows and spent its budget on DNS churn it held forever, holds were
released for going quiet, and a mapping outlived its device. All four are
fixed, with a shared presence rule (`call/0030`), and the consoles' state is
the acceptance.

**Open, in the order I would take them:**
1. The *lobby* case with a real console — the one unexercised case, and it
   needs the operator (three minutes when either console sits in a lobby).
2. The yield acceptance (`call/0027`'s late-collision rule) — runnable alone
   by driving a device flow onto a leased port with the IP_TRANSPARENT trick
   in `deploy/collision-probe.py`.
3. A soak: the new GC logic has never run for hours, and the daemon's memory,
   fds, state writes and presence transitions under load are unmeasured.
4. The objective outside-probe of a held tuple across a silence window (the
   synthetic client makes this possible without a console).
5. `call/0027`'s second question: whether the uplink ever answers one external
   port to two inner tuples (passive; the per-slot reads would show it).
6. Hygiene: the artifact hash on the canonical build host; the Kani
   re-derivation on the larger host; EIF-loss detection, carried past v2.

**Session captures are still running** on the NVMe (`session-2026-09-18/`,
3.8 GB and growing at about a megabyte a second): stop or rotate them before
an overnight run, and use *simple* tcpdump filters that busybox accepts, each
validated by a known event.

**The held mapping answers across its client's silence: item (4) of that list
is measured and passes, and four defects fell out of it** (2026-09-18, pin
68c2e2d). Two leases were asked for over PCP from inside the router's
`dslp-probe` container (192.168.21.11). A container's flow is *forwarded*, so
the observation arm's mirror sees it, and its admission budget is its own,
which is what the workstation's spent browser flows kept refusing. Each client
then went fully silent, and the external vantage probed the learned external
tuple at 30, 60, 120 and 300 seconds of that silence, with the schedule armed
from the silence's own epoch so each probe landed at its window rather than
past it. All eight arrivals are pasted in
`results/RESULTS-2026-09-18-held-mapping-silence.md` (29.96, 59.97, 119.97 and
299.97 s; 29.35, 59.34, 119.34 and 299.34 s), each also forwarded to the
client. What it settles: the AFTR's 13 to 21 s idle reaping does not claim a
mapping the daemon holds, because the slot's own punch is more frequent than
the reaper. The lease was asked for with a 600 s lifetime, because the granted
lifetime is the ceiling the windows must fit in.

**Read the WAN capture by the router's own slot port, not by the CGNAT tuple.**
On eth1 the AFTR has already translated the destination back, so the arrival
that the vantage sent to `37.228.213.83:59281` appears as
`> 192.168.0.21.40001`. A filter by the CGNAT port finds nothing and reads as
a lost packet.

**Four defects the run exposed** (evidence in that results file):
1. `obs.rs`'s `should_rescue` ends with `reply_dst != ctx.vm_nat`, which
   requires the flow to have *seen a reply*: a named device's unreplied flow
   is therefore refused, against call/0029 and the function's own comment.
   Measured: an allowlisted client's flow to a black-hole peer was never
   claimed across 60 s with a fresh daemon and an empty budget.
2. The `nft` CLI segfaults inside libnftables at daemon start (`apply_hold`'s
   batch is the suspect; the same commands run by hand all succeed). The
   policy is in force after every start, so nothing broke tonight.
3. The shadow keepalive fails `EPERM`, so the *arm*'s hold rests on the
   device's own traffic while the *facade*'s rests on its own punch. That is
   why this acceptance had to use a lease.
4. `collided()` includes `Lease::Static`, so a device flow landing on a
   static's port would make the late-collision yield move a port the operator
   configured, against call/0030.

**Harness footguns, rediscovered or new:** the router's shell has no `timeout`
and no `pkill` (it is `ash`); the router's ssh *hangs* on an unknown host key,
so drive the vantage from the workstation; `pgrep -f` self-matches the ssh
wrapper, so use the bracket trick; a container's `/tmp` is a separate mount,
so stage files under `/root` in the rootfs (`/mnt/nvme/lxc/<ct>/rootfs/`); and
a UDP socket that has been `connect`ed delivers only from its peer, so a held
client must dissolve the association before probes from the vantage can reach
it. `pcp-probe.py` gained `--lifetime` and `--hold` for this run.

**The collision rule moved the operator's static; found by the acceptance and
fixed test-first** (2026-09-18). `LeaseTable::collided()` matched *any* slot's
bind port, `Lease::Static` among them, so a device's flow landing on a
static's port was reported as a collision for the yield to move: the running
state would have diverged from the config that produced it, against
call/0030. The test that failed first is
`a_static_is_the_operators_and_is_never_the_slot_that_moves` (red with
"a static's port is the operator's, not a lease the yield may move"), and the
rule now reads the way call/0030 states it: a static is reported and left, a
granted lease is yielded. The deployed binary is deliberately *not* rebuilt:
the six-hour soak runs on the binary under test, and a redeploy mid-soak would
end the run. The fix ships with the next deploy.

**Item (4): the per-slot learned tuples analysed, and call/0027's second
question answered for the observed window** (2026-09-18). `deploy/tuple-analysis.py`
reads the daemon's own tuple events and prints three views: one inner under
several externals (the client-visible split), one external under several
inners (the uplink's own collision), and externals shared between a slot and
an inner. Liveness is decided from event times, so sequential reuse hours
apart is reported apart from a genuine concurrency. Over 14:53:44 to 22:02:35
(353 events, 35 inner tuples, 35 external tuples, 83 pairs) **no external
tuple was in two inner tuples' hands at once**: the two shared externals
(`59205`, `59230`) were recycled three hours later. What the same log does
show, concurrently, is the mirror case: `192.168.21.138:3074` learned 59343,
59220 and 59211 inside a six-second span at 18:53, which is the console split
call/0014 fixed. So the console's Strict/Moderate was never the uplink
allocating one external port twice — it was the local device-key pinning —
and the downstream question stays open only as a standing property to watch.
The sample is dominated by two browsers' churn, and the soak window widens it
in the morning with no new code. Results:
`results/RESULTS-2026-09-18-tuple-analysis.md`.

**Items (1) and (2) are both driven and passing, and two of the four defects I
recorded earlier are retracted** (2026-09-18, pin 0f150da). Item (1) again,
through the *hold* proper rather than a lease: a silent container client
(`192.168.21.11:47077`), one datagram, then the vantage's probes at 30, 60,
120 and 300 s each arrived at the WAN and were delivered to the client's own
socket (`RX 1..4` at 1789770277.492, …307.480, …367.497, …547.482). Item (2),
driven live: a device's TCP flow from `.11:40001` (the leased port) made the
daemon move the lease — `collision-yield slot 40001 yielded to a device's flow
and moved to 40003 (label 0 kept)` — and the slot confirmed a fresh external
tuple `59241` in the same second, with its state file, its accept rule and the
client's lease all following. Evidence:
`results/RESULTS-2026-09-18-collision-yield.md`.

**The two retractions matter more than the two confirmations.**
(1) "a named device's unreplied flow is refused" was **wrong**: the synthetic
client had no policy route, so its packets left by `pppoe-vdsl4`
(84.203.115.61) instead of `eth1`, and the observation arm only sees
`oifname eth1`. With `ip rule add from 192.168.21.11 lookup 1000` the same
unreplied flow was claimed at once — eth1's fullcone masquerade sets the NAT
source to 192.168.0.21 even with no reply, so `reply_dst == vm_nat` holds.
(2) "the shadow keepalive cannot write (EPERM)" was **stale**: every such
warning belongs to pids 3026/31093/32114, the last at 21:57:53, and the
daemon started at 21:57:59 has logged none. A socket bound to
`(192.168.0.21, port)` sends to the STUN servers fine, with and without a
`snat_map` pin of that tuple to itself. Lesson: attribute a warning to the
process that emitted it before calling it a defect of the current build.

**The hold is the daemon's own writes, measured.** With the client silent
since 22:24:07, its conntrack entry ran 252 → 256 packets in 8 s in both
directions (`src=192.168.0.21 sport=47077 → 74.125.250.129:19302 [ASSURED]`):
one small STUN exchange every two seconds, all of it the shadow keepalive.
That is why a mapping survives silence, and why the earlier "13–21 s idle
reaping" and tonight's 300 s both stand: without writes the mapping dies in
seconds, with them it lives.

**A synthetic client must be policy-routed like the consoles.** `.68`, `.138`
and `.97` have `ip rule → table 1000` (default via 192.168.0.1 dev eth1); a
container or any new address otherwise takes the main table's lowest-metric
default out `pppoe-vdsl4`, which is invisible to the mirror and to
`collided()`. Add the rule (I added 25003 for `.11`) and remember it in the
cleanup list.

**Two doors onto a leased port, and only one is open.** A device's *UDP* flow
cannot take a leased port while the slot's relay socket holds it — the kernel
NAT'd it to 1024, reproduced twice — and the allocator steers new slots around
live mirrored tuples (`collision-avoided`). A device's *TCP* flow can, because
conntrack keeps the port space per protocol; the rule is protocol-blind and
fired. Worth a decision: scope R4 to the entry's protocol, or state that a
cross-protocol port conflict is in scope. Also: two stale inbound accept rules
(`dslitepunch-40002-tcp`, the legacy `dslitepunch`) survive from earlier
daemons, because the accept rule is deleted by *handle* parsed from
`nft -a list` — the same path the libnftables segfaults come from.

**Item (5), second fix: the accept rule was deleted by a handle, so it could
outlive its slot** (2026-09-18). `nft::del_input_accept` ran
`nft -a list chain inet fw4 input`, parsed `# handle N` out of the listing and
deleted by handle. Two consequences, both measured on the test router: the
delete depended on a listing at all (and that listing is the one the
libnftables segfaults come from), and when it failed the rule stayed — two
accept rules from earlier daemons are still installed, `dslitepunch-40002-tcp`
for a protocol this build does not enable and a legacy `dslitepunch` with no
port in its comment. Now `accept_match()` is the single definition of the
rule's match: `accept_rule` builds the insert from it, `del_input_accept`
deletes by it (bounded loop, so a duplicate from an older daemon goes too) and
`revoke_datapath`'s batch uses it, so insert and delete cannot drift. Tests
first: `a_slots_accept_rule_is_matched_by_expression_never_by_handle` and
`the_insert_and_the_delete_share_one_match`; suite 195 passed. Committed and
the pin bumped, but **not deployed** — the six-hour soak runs on the running
binary and a redeploy would end the run.

**Item (5), correction and third fix: the accept rule cannot be deleted by
expression, so it is a set element now** (2026-09-18). My previous entry said
the delete was fixed by using the rule's match expression. That was wrong, and
the router said so: `nft delete rule inet fw4 input iifname "eth1" udp dport
49001 accept comment "dslitepunch-49001"` is refused with "syntax error,
unexpected iifname, expecting handle" on this build (libnftables 1.1.0). The
committed version would therefore have failed every delete and let accept
rules *accumulate*. The real fix is structural: a slot's inbound accept is now
an **element** of one of two daemon-named sets inside fw4
(`dslp_ports_udp`, `dslp_ports_tcp`), with the two accept rules installed once
by `ensure_accept_sets`, which also empties both sets and sweeps any per-port
rule an older daemon left (by handle, from the one listing it already reads).
Every per-slot operation is by key, so no handle is needed in the datapath at
all, and the boot path re-adds an element per restored slot after
`ensure_ruleset`, so a restart keeps exactly the ports its table holds.
Verified on the box in a scratch table: set create, rule add (rendering exactly
the text the code builds), element add/list/delete, delete-of-non-member
refused, flush, table delete. The live fw4 chain now holds only
`dslitepunch-47077` and `dslitepunch-1024`, the arm's two rescues; the two
stale rules and my own leaked `dslitepunch-49001` are gone, and how they went
is not attributable from the log — recorded as unexplained rather than
claimed. Tests first: `a_slots_accept_is_a_set_element_never_a_rule_handle`,
`the_two_protocols_use_two_sets`, `the_legacy_sweep_takes_only_the_daemons_per_port_rules`;
suite 196 passed. Committed, pin bumped, **not deployed** (the soak runs on the
running binary).

**Item (3) done: seventeen hours of soak, flat, with no failed state write**
(2026-09-18 21:57:59 to 2026-09-19 15:11:33). One process (pid 4496) for the
whole window, 1034 one-minute samples: before `1789768700 rss=1136 fds=13
ct=881 holds=1`, after `1789830693 rss=1100 fds=15 ct=616 holds=3`. The
hourly RSS means move inside 1220 to 1337 kB with no direction over seventeen
hours and end lower than they began; descriptors sit at 15.0 with excursions
to 3 and 22 when the slot table emptied and when the arm held several rescued
tuples. The daemon was busy throughout: 833 rescues, 13 churn events, 3 GC
frees, 2 collision events. Zero warnings from the running daemon and no state
write failed; the 659 `EPERM` lines belong to earlier pids, the last of them
six seconds before this window opened. Readings in
`results/RESULTS-2026-09-19-soak.md`.

**The overnight goal's five items are done, the fixes are committed, and the
router is as it was found** (2026-09-19). Items: (1) a synthetic client's held
mapping answered the external vantage at 30, 60, 120 and 300 seconds of its
own silence, twice, once through a facade lease and once through the arm's own
hold, each arrival pasted from the router's WAN capture and each delivered to
the client's socket; (2) a device's TCP flow onto a leased port made the
daemon move the lease, `slot 40001 yielded to a device's flow and moved to
40003`, with the slot confirming a fresh external tuple in the same second;
(3) seventeen hours of soak, one process, RSS flat across the hourly means
(1220 to 1337 kB), descriptors at 15.0, zero warnings from the running daemon
and no failed state write; (4) the tuple analysis, which found no external
tuple in two inner tuples' hands at once and did find the concurrent split
call/0014 fixed; (5) three defects fixed with a failing test first (a static
port the collision rule may not move; the inbound accept deleted by a handle,
twice: the second, set-based fix replaced the first, which relied on a
`delete rule` by expression that this nft refuses), and one defect dispositioned
rather than fixed because it is an upstream libnftables crash that 4,260
hand-run invocations of the daemon's own shapes could not reproduce
(call/0031). Two defects I had recorded are retracted with evidence: the
`reply_dst` gate was never reached (the client had no policy route) and the
`EPERM` shadow warnings belong to earlier pids.

**What the operator still holds**: the lobby case with a real console; the
artifact hash on the canonical build host; the Kani re-derivation on the larger
host; and the next deploy, which carries the three fixes and the set-based
accept. Also open by decision: whether R4 should be scoped to the entry's
protocol (recorded in `results/RESULTS-2026-09-18-collision-yield.md`).

**Cleaned up on the test router**: the sampler and the two overnight captures
stopped, the capture files removed (their evidence is in the results files),
the PCP clients and listeners killed, the harness files removed from `/tmp`
and from the container's root, the temporary ip rules 25002 and 25003 removed,
`/etc/ds-lite-punch.allow` restored to the operator's three, and the daemon
restarted (pid 27551) so those apply. `soak.log` is kept on the NVMe as the
series the soak reading cites. The other observer's capture (pid 14409) was
never touched.

**The overnight goal is closed: its work is done and committed, and the Goal
mechanism stopped on its own bookkeeping limit** (2026-09-19). All five checks
are met with committed evidence: the held mapping's four windows, the driven
collision-yield, the seventeen-hour soak, the tuple analysis, and three
defects fixed behind failing tests with the pin bumped. The runtime reports
the Goal `usage_limited` after three consecutive evidence-checkpoint overflows
(the catalog could not fit the claim list inside its bound), not because any
check failed, and it asks for a narrower objective if the Goal is to be
resumed. Nothing is left running: the repo is clean and pushed at 6efba91, the
component at 41f63ae, and the router is as it was found. Open for the
operator, unchanged from the hand-off: the lobby case with a real console, the
artifact hash on the canonical build host, the Kani re-derivation, the next
deploy (which carries the three fixes and the set-based accept), and the
question of whether R4 should be scoped to the entry's protocol.

**CI fixed on both repositories: the reproducible lane never ran, and the
component had no lane at all** (2026-09-19). The host's Reproducible build job
had failed on every push since it was written, and the reason was one field:
`host-lifecycle software --verify-build` runs the *recorded `build`* inside the
*recorded `toolchain`*, and `.host-software` held `toolchain =
x86_64-unknown-linux-musl`, a Rust target triple. Docker read that as an image
name and the lane died with `pull access denied for x86_64-unknown-linux-musl:
repository does not exist` before it built anything.

**A `toolchain` in `.host-software` is a container image, and it should be a
digest.** It is now
`ghcr.io/rust-cross/rust-musl-cross@sha256:ce75e9174325d4fbb3de85c309e2d7ca29f7500169bc4b5d2c611ff7e86d549a`,
which carries the musl cross toolchain and the target already, and the digest
is the same on Docker Hub and ghcr. Two things had to be checked from the
registry rather than assumed, because this development host has no docker and
no podman: the image has **no ENTRYPOINT** (the tool appends `sh -c`, so an
entrypoint would swallow it), and it exposes `CARGO_BUILD_TARGET` and the musl
toolchain. Both were read from the registry API with a token from
`ghcr.io/token`; the recipe is in this session.

**The artifact hash can only be re-derived where the toolchain can run.** With
no container runtime here, the component's own CI is the re-deriver: its new
lane builds in that image and prints `artifact = <path> <hash>` in the form the
record uses. Two consecutive runs produced the identical
`ab0f9bd517ef075885fd5b6e6a91b9fcc7e64ad9805e7d6450f2bd3eefd11a45`, and the
host's lane then reproduced it from the pin on a GitHub runner, in the same
image, at the same `/src` mount. That is the first time the chain
CI-build → recorded anchor → independent rebuild has actually closed here.

**The component's lane runs its tests inside the pinned toolchain, and that is
not stylistic.** The crate's `.cargo/config.toml` sets
`[build] target = x86_64-unknown-linux-musl` for every cargo command, so a bare
`cargo test` on an ubuntu runner fails with `can't find crate for core` before
it reaches a test. Both jobs therefore `docker run -v "$PWD":/src -w /src
"$TOOLCHAIN" sh -c '… --locked'`, which also removes the second compiler: the
release profile carries `lto`, `codegen-units = 1` and `strip`, so a test built
by a different rustc would be a different program from the one that ships. The
suite is 196 passed, 1 ignored, in CI as on the dev host.

**Housekeeping the same run exposed**: the naming lane had flagged 23 tokens in
the two results files, which are pasted packet timestamps and the sampler's
hourly means. Fenced blocks are still scanned; a fence tagged
```` ```host-lint:ignore ```` is not, which is the disposition the methodology
gives an irreducible literal citation, so those two blocks are boxed and the
surrounding prose stays linted. `software --check` reports 0 undispositioned
tells, prose and reconcile are clean, and the refs sweep resolves every
reference in 62 documents.

**CI failure drift filed as a methodology bug: connollydavid/host#21**
(2026-09-19). The finding is not that a lane was red, it is that the rules
cannot see a lane's outcome. Measured in this host repository over the whole
life of its workflows: the Reproducible build lane ran 67 times and failed 64
of them, the Prose lane failed 24, and only Site ever passed (66 of 66). The
component repository had no `.github/workflows/` at all for the same period and
nothing in the spine owed it one, because the mandatory-lane rules are
conditional on a spec of a kind existing (`.allium`, `.tla`, a declared rung)
and this component carries none. Every local gate stayed green throughout:
`validate`, `software --check`, `obligations`, `book --check`, prose, refs,
reconcile, and each phase receipt.

**The consequence is three hashes for one component, and only two agree.** The
recorded anchor, built in the pinned image, is `ab0f9bd517ef…`; the binary the
test router runs is `8e21070e3a42c5240aed01900af3c451095bff263a28d36438e4aae403a814be`;
and a build of the same pin on this development host is that same
`8e21070e…`. The deployed artifact and the local build agree because the
deployment was made from here, and the record anchors another toolchain's
output, so a release input existed that no receipt could vouch for.

**The ask in the report is that addressing CI failures become a function of the
rules, per turn**: a per-turn duty in the operating manual (read the default
branch's recent conclusions, fix or receipt them), a mechanical CI clause in
the verify phase's recheck that HAZARDs on any non-green conclusion and on a
declared lane with **no runs at all** (absence must fail, not pass vacuously),
and forge-anchored re-derivation so a receipt names the run that discharged the
claim rather than only a digest. Filed at
https://github.com/connollydavid/host/issues/21 with the two documentation gaps
the work exposed: the `[software]` `toolchain` key never says *container image*
(which is how a Rust target triple got recorded there), and the conditional
lane rule does not name its residue, a component whose tests never ran anywhere
except a laptop.

**Open decision from the same session**: aligning this host with CI byte for
byte. The choices are to upload the component's release artifact from its lane
and deploy from the run (one builder, nothing to install here), to bring the
pinned image to this host so local builds match CI, or both. The image has no
ENTRYPOINT and this host has no docker or podman, which was verified from the
registry rather than assumed.

**CI and this host are aligned onto GitHub's bytes, and the router runs them**
(2026-09-19). The operator ruled the direction: GitHub is the builder and the
host matches it, because reproducibility has to hold widely rather than on one
machine's ambient compiler. Recorded as call/0032. The component's lane now
publishes the artifact it builds together with the `artifact = path hash` line
the record uses, and fails the job if the upload produces nothing.

**Verified end to end**: the artifact downloaded from run 35459015279 hashes to
`ab0f9bd517ef…`, which is the recorded anchor; the test router's
`/usr/bin/ds-lite-punch` was replaced with exactly those bytes and checked
against the record before the daemon was started; it came up (`start`, `hold`
with the ruleset in force, `observe` with the three allowlisted devices, `pcp`)
and confirmed a slot tuple in the swap second (`slot 40000 confirmed
37.228.213.83:59278` at 17:47:25), so its datapath worked. The replaced binary
is parked at `/root/ds-lite-punch.prev14` for rollback. The record, the lane's
output and the running daemon are now one hash.

**Local ambient builds still differ** (`8e21070e…`) because this host has no
container runtime, and they are now explicitly a development aid rather than a
deployment source: the `.host-software` note says so, and a deployment checks
the downloaded artifact against the record first.

**One observation worth keeping, and it sharpens the filed report**: the local
gate caught a *pin* drift within a minute of it happening (`DRIFT
software/ds-lite-punch/main at 1b758047 but pinned to 9a4f1c0e` after the
component's upload commit), because the pin is a recorded fact the gate can
read. It stayed green for two and a half days while the *lane* failed 64 times,
because a lane's outcome is a forge fact no local gate reads. Both are drift;
only one is visible from here.

**CI thread closed; the forge, the record and the router are one artifact**
(2026-09-19). End state: the host's three lanes and the component's lane are
green, `software --check` reports every component at its pinned SHA with no
worktree-symlink hazards, and the recorded `toolchain` is the digest-pinned
image, the recorded `artifact` is `ab0f9bd517ef…`, and the daemon on the test
router is those same bytes (pid 12490). The pin is the component's upload
commit `1b758047…`, which the reproducible lane rebuilt and reproduced. The
filed report of the drift that hid all this is connollydavid/host#21.

**What the next session inherits**: the lobby case with a real console, the
Kani re-derivation on a larger host (call/0019), and the open question from
the collision work, whether R4 should be scoped to the entry's protocol.
Two `software --check` notes stay by design: this host's `target/` is an
ambient build that differs from the anchor (it is not a deployment source,
call/0032), and the `.host` stamp has no `baseline` yet, which
`host-lifecycle upgrade` migrates when the next upgrade lands.

**A habit worth keeping from today**: the prose audit went red twice on my own
new decision record, and both times the shape was a negation or a contrast the
detector reads as a trope ("has no X, so Y"; "the record anchors A while the
host hashes B"). Stating it positively cleared it. The auditor is the oracle:
reword, re-run, repeat, and do it in the same turn as the push rather than
letting a lane carry the failure.

## 2026-09-19 — the name is derived, and both READMEs state it

**`punch` = Proxy UPnP NAT/CGNAT Holder.** The operator supplied the derivation
in session; before today no file in either repository carried it. A search for
"Proxy UPnP", "NAT/CGNAT" and "Holder" found only the imported sense of
"holder" (the STUN and mapping holder in code), and the field was empty in the
host's tracked docs, in `call/` and here. One search lesson: `software/` is
gitignored, so workspace-wide greps skip the component worktree entirely (an
earlier pass therefore reported "no component README" when one exists); search
the component by explicit path.

**Both READMEs carry the derivation in one identical sentence** (the operator
chose to state it in full rather than point): `**ds-lite-punch = DS-Lite Proxy
UPnP NAT/CGNAT Holder.**` Two copies of one sentence is the recorded cost of
that choice, and a diff of the two files shows any drift in one line.

**The rewrite is ASD-STE100 Simplified Technical English**, ultra-terse, for a
general reader: one fact per sentence, active voice, vertical lists, no
addresses, and a `Terms` list at the end. Both files gained a dated state line
and a future-work section holding the inherited open list (the lobby case with
a real console; the Kani re-derivation on a larger host; the R4 protocol
question; EIF-loss detection).

**The component README's evidence table points at the record for the pin, and
that is deliberate**: a file cannot name the commit that carries it, because
writing the SHA into the file changes the commit. The artifact hash, the
toolchain digest and the test count are stated exactly; the pin is a link to
`.host-software`, which is the authority.

**Re-verified rather than copied**: the lane run at `c8b067d` (35463976941)
reported `196 passed; 0 failed; 1 ignored` and printed the artifact line with
`ab0f9bd517ef…`, identical to the record, so a README-only change did not move
the artifact. The pin is bumped to `c8b067d`; `software --check` reports every
component at its pinned SHA, with no worktree-symlink hazards.

**Two stale claims in `AGENTS.md` project specifics were corrected**, because
the new README would have contradicted them: the crate "is being migrated" and
the component "carries a `repro-waiver`" (the migration landed 2026-09-13, and
call/0016 retired the waiver), and "(multi-instance and the UPnP control plane
are open)" (multi-instance is built; plan/0007 and plan/0008 deliver the
control plane).

**Lane state at the push**: prose clean, every reference resolved across 63
documents, and the naming lane's advisories unchanged apart from one new note
on the host README (four of its seven paragraphs are single-sentence) — the
terse register produces that note, the prose lane does not flag it, and the
note advises rather than gates.

**One stray untracked tree was left alone**:
`software/ds-lite-punch/main/.qwen/tmp/` holds two `qwen-review-*.json` files
from 2026-09-15. Nothing is committed, the tree is not mine, and a careless
`git add -A` in that worktree would sweep it in; the operator may delete it or
keep it on purpose.

## 2026-09-19 — the derivation reads as the full name, with the short name beside it

**The operator reordered the derivation sentence.** Both READMEs now read
`**DS-Lite Proxy UPnP NAT/CGNAT Holder (ds-lite-punch).**`, the full name first
and the short name in the parentheses. The entry above quotes the earlier form
(`ds-lite-punch = DS-Lite Proxy UPnP NAT/CGNAT Holder`); this entry corrects
that quote and points back to it, and the two READMEs carry the live text.
Both copies remain one identical sentence, so a diff still shows any drift in a
single line.

**The change is `9b860c6` in the component and `54226ff` in the host README**,
and the pin moves with the component commit. Nothing touched the code, and the
artifact hash is unmoved: the component lane at `9b860c6` (35465214784) is
green, reporting `196 passed; 0 failed; 1 ignored` and printing the artifact
line with `ab0f9bd517ef…`, identical to the record. Prose is clean, every
reference resolves across 63 documents, and `software --check` puts every
component at its pinned SHA.

## 2026-09-20 — the filtering, read from outside, and one client asking twice

**The line forwards a stranger's datagram to a held mapping.** plan/0010's
`#vantage` and `#eif-now` are done and receipted. A client in the `dslp-probe`
container asked for a PCP mapping (external `37.228.213.83:59292`, internal
3075, 600 s), went silent, and the vantage `170.9.238.141` sent unsolicited
datagrams from `170.9.238.141:54372`, a source the mapping had never used. All
four arrived at the router's WAN at 30, 60, 120 and 300 seconds of the
client's silence, each within 74 ms of its send. Record:
`plan/0010-the-filtering-proved-and-watched/results/RESULTS-2026-09-20-stranger-probe.md`.

**The mis-grep happened again.** On eth1 the arrival's destination is the
router's own slot port (`40002`); searching the capture for the CGNAT tuple
(`59292`) finds nothing, and the 2026-09-18 record already warned about this.
Read the capture by the slot port.

**A new defect, recorded and not fixed: one client asking twice leaves the
datapath uninstalled.** With two leases live from the same client (internal
3074 then 3075), the second grant revokes the first, the revoke logs
`Error: Could not process rule: No such file or directory` for
`delete element ip dslp snat_map { 192.168.21.11 . 3074 }`, and `snat_map` ends
empty while the accept set holds the slot ports. The arrivals reached the
router and were not delivered to the client (no RX in the client's log, nothing
on the LAN capture), where the 2026-09-18 run — which asked for its two
mappings one at a time — delivered every one. A fix owes a failing test first,
in the shape call/0022 set for the port label.

**Method lessons, each of which cost a round.** An `ip rule add` for the
synthetic client needs an explicit priority above `25000`, because the default
lands behind the firewall's mark rule at `30000` and the flow leaves by the
wrong WAN. `pkill -f <script>.py` kills the shell that carries the script path
in its own command line, twice today, and the bracket form is the fix. `ash`
has no brace expansion, so a staged-file removal written with braces removes
nothing. The vantage needs root for a capture (`sudo -n` works), and its own
OpenVPN server's traffic crosses `enp0s6`, so a filter on the destination host
alone fills with that flow and misses the probe.

**The box is as it was.** The ip rule, the allowlist entry, the client, the
sink listener and the captures are gone. The two captures are archived at
`/mnt/nvme/captures/eif-2026-09-20/` with `sha256sums.txt`. One capture on the
router is not mine and was left: pids `14409` and `24104`, a wrapper loop
capturing `192.168.21.138` traffic, which predates today and wants the
operator's decision. The daemon still runs `ab0f9bd5`, so the README rounds
moved no bytes.

## 2026-09-20 — the watch, built, deployed, proven, and disarmed

**The milestone's watcher exists and its alarm was proven on the box.** Pin
`0c7085ab`, artifact `33091964`, 205 tests. plan/0010 is done: `#vantage`,
`#eif-now`, `#watch-design`, `#watcher`, `#alarm-proof` and `#record` all carry
receipts. Record: `plan/0010-.../results/RESULTS-2026-09-20-alarm-proof.md`.

**The proof, in the daemon's own words.** One marked datagram from the vantage
to the slot tuple produced `{"event":"carrier-probe","count":1,"epoch":1789907858}`
and `packets 1 bytes 44` in the counter; withholding the helper produced
`{"event":"carrier-silent","last_probe":1789907858,"waited":60,"epoch":1789907918}`
at exactly three intervals after the probe. The carrier's behaviour was not
exercised; the record says so.

**A defect found by deploying, and fixed test-first.** The counting rule was
appended to fw4's input chain, after fw4's own accept rules for the same ports,
so an accepted packet never reached it: the marked datagram arrived
(`170.9.238.141.41000 > 192.168.0.21.40000`, 16 bytes) while the counter stayed
at zero. The fix installs with `insert`. The test was shown failing against the
pre-fix shape (`left: "add" right: "insert"`) before the fix was restored.

**A fragility that needed a hand.** The install is idempotent by rule *text*,
so a box already carrying the misplaced rule keeps it and the daemon adds
nothing. This router needed `nft delete rule inet fw4 input handle 15514`
before the restart; a fresh box gets the placement right on first install.

**The watch is disarmed, deliberately.** `CARRIER_PROBE=0` in the router's env
with the arming line beside it, and the counter and rule removed. Arming it
obliges the helper to run outside the line, and a helper that stops and a
carrier that stops look the same to a counter: the operator decides whether the
vantage runs `deploy/carrier-probe.py` as a service.

**Two smaller lessons.** A task's `verify: attested <call/NNNN>` must be the
whole value: prose after the citation is read as part of the reference and
fails to resolve, which `software --check` HAZARDs. And a documented script
must be executable in git: the lane's setup check HAZARDs `./script.py` at mode
`100644`, and `git update-index --chmod=+x` is the fix.

**The router runs the watcher build with the watch off**, parked rollbacks
beside it (`prev-ab0f9bd5`, `prev-86ee70fe`), and the record's pin and artifact
hash are `0c7085ab` and `33091964`.

## 2026-09-20 — the ingress translation, and the churn behind it

**A lease's arrival now reaches its client, and the root cause was a commit
from the collision work.** `4d31181` stopped pinning the client's own tuple,
which was right for the reason call/0014 records (the pin gave one game two
external tuples), and that pin's conntrack entry had also been the only thing
that mapped an arrival at the slot port back to the client. With it gone, an
arrival reached the port and stopped. Fixed at pins `56faf04` and `5214039b`
(artifact `0abae591`, 210 tests): a per-slot element in `dslp_in_udp` /
`dslp_in_tcp` and `dslp_dnat_udp` / `dslp_dnat_tcp`, a prerouting chain at
priority `-150`, and a rule per protocol that dnat's the port's arrivals to the
client that owns them. Egress untouched. Record:
`plan/0010-.../results/RESULTS-2026-09-20-inbound-translation.md`.

**Proven at the datapath, not yet into a socket.** A stranger's datagram to a
lease's external tuple appeared on br-lan at the client's own port
(`13:06:36.907238 IP 170.9.238.141.41112 > 192.168.21.11.41020: UDP, length 12`)
and the conntrack reply tuple names that port. The socket half failed for a
tool reason: `pcp-probe.py` requests an internal port with `--int-port` while
its socket binds an ephemeral one, so nothing waits on the port the lease
names. A delivery-to-socket claim needs a listener bound to the requested port.

**A second defect, recorded and pending: lease churn.** Leases granted at
13:09:09 had their elements deleted at 13:09:11, each delete naming an element
that was never there, one of them an internal port no lease in that session
used (`192.168.21.11 . 3074`). The inbound set and map end empty while the
leases live in the table. It is `plan/0010#lease-churn`, pending, and no
delivery measurement can rest on a lease that lives seconds.

**Two deployment lessons.** A design that adds a rule to a chain must install
the chain: the first inbound build left it out, the rule had nowhere to live,
and the daemon refused to start rather than run blind — the parked build was
restored within a minute while procd was respawn-looping it. And the revoke now
runs each element delete as its own statement with a read-back, because the
all-or-nothing batch let an absent element cancel the rest.

**The stale captures are gone**, as the operator asked: pids `14409` and
`24104` (the wrapper loop for `192.168.21.138`) and my own leftover `13248`.

**Both datapath defects are written up, with a root cause named for each:**
`plan/0010-.../results/RESULTS-2026-09-20-slot-datapath-defects.md`. The second
one's cause, now settled from the code and the log: an entry is keyed by its
internal tuple (`apply_entry`, `(proto, owner, int_port)`), so a client's
second request surrenders the first, and the surrender hands `revoke_datapath`
a bind port that the pool has since reallocated. The revoke then removes a
*live* lease's acceptance and its translation. The "No such file" deletes that
accompany it are the ordinary case: the retired entry never had elements under
the keys its revoke names. The tree's existing regression test
(`apply_entry_keyed_per_client_lets_two_holders_share_a_port`) guards the
*refresh* path; this arrives through the *surrender* path. What made it visible
was the probe's own shape: `deploy/pcp-probe.py` sends NAT-PMP legs whose
internal port defaults to `3074`, so a run on `--int-port 41040` also asks for
`3074` and surrenders it on the next run.

## 2026-09-20 — both defects fixed, and the first write-up corrected

**The mapping-coexistence defect is fixed and verified.** The cause, settled at
the code and by a failing test: `apply_entry` refreshes on
`(proto, owner, int_port)` and otherwise lets a request surrender the same
client's earlier entry at the same `(req_ext, proto, owner)`, and a request
naming no port carries `req_ext` 0, which was treated as a handle. Two
"any port" requests therefore collided, so a client speaking PCP and NAT-PMP
lost one mapping per pair. The failing test returned the first lease's slot
(`Some((40002, 192.168.21.11, 41010))`) before the guard. Pins `8f179c7` and
`0b72060b`, artifact `f4499c2c`, 211 tests.

**Two more defects were found and fixed with it.** The boot restore pinned every
restored slot while a fresh grant installs an ingress translation and no pin,
so a restored lease carried the egress consequence call/0014 settled against
and had no translation of its own; the restore now installs the grant datapath.
And the revoke deleted a `snat_map` element the grant never creates, which put
an error line in the log on every revoke (54 in one session); that statement is
gone.

**My first write-up was wrong in its harm claim, and the record now says so.**
The log window it rested on was produced largely by my own instrument:
`pcp-probe.py` ends every run by deleting its own mapping, so a run looks like
a lease that lived two seconds, and its legs all name the same suggested port.
The defect is real but narrower than "a revoke tears down another client's live
lease", and
`plan/0010-.../results/RESULTS-2026-09-20-slot-datapath-defects.md` is corrected
in place: symptom, root cause, mechanism, blast radius and disposition all
rewritten around the failing test rather than the log reading.

**Verified on the box, three ways.** Three holding clients leave three leases
with three slots and three translations; a stranger's datagram to a lease's
external tuple reaches a listener bound to the port the lease names
(`RX 19 bytes from 170.9.238.141:41122 at 1789941059.865`, 72 ms after the
send), which closes the delivery defect's socket half; and after a restart the
restored slots keep their accept and translation elements, carry no pin, and
still deliver (`RX 22 bytes … at 1789941118.179`) with no error line following
the restart.

**Instrument and hygiene lessons.** `pkill -f` and pattern-based kill loops
self-match: for the third time today a `case` pattern in my own command line
matched my shell and killed it before the file removals ran, so a kill loop now
goes in a command of its own. The box is clear: staged files removed, the three
leases left to expire on their own, one `/tmp/ds-lite-punch.staged` from an
earlier session deliberately left, and the router runs `f4499c2c` with
`prev-0abae591`, `prev-d5d19d07`, `prev-86ee70fe` and `prev-ab0f9bd5` parked
beside it.

## 2026-09-20 — the revoke stops printing errors, and the log goes quiet

**The last of the revoke's error lines is gone.** After the churn fix, three
lines remained at 21:58, one per lease that expired at that minute, and they
came from the tolerant `del_pin` call inside `revoke_datapath`: the facade
installs no pin, so it could only fail and print nft's own stderr into the log.
The statement version had already gone in the churn fix; this removed the call
beside it, and the same removal in the grant-failure rollback. The paths that do
pin, the arm's self-pin and the TCP holder, clean their own.

**Measured, not assumed.** A lease was created and deleted through the probe
(`internal 41090`, external `37.228.213.83:59245`): the error count is 57
before and 57 after, and the last error line is still the old 21:58 one. Pin
`709e7668`, artifact `ddfe3903`, 211 tests, deployed and recorded; the router
runs it with `prev-f4499c2c` parked beside the earlier ones, and no capture of
mine remains.

## 2026-09-20 — both repositories are public, after a clean audit

**The audit found no secrets.** `gitleaks` 8.29.0 over the *full histories*: the
host's 425 commits (385 MB scanned) and the component's 83 commits, both "no
leaks found". A targeted sweep behind it found no private keys
(`BEGIN … PRIVATE KEY`), no WireGuard material (`PrivateKey =`, the PSK), no
tokens (`ghp_`, `github_pat_`, `sk-`), no PUK, no PIN, no password assignment
outside the DeviceProtection spec's own PBKDF2 language, and no UDN uuid. The
`sk-` hits were the word `task-receipts`; the `password` hits were
`password = Password, salt = Name || Salt` from the specification.

**The flip, and its verification.** Both repos are now `visibility=public`: the
unauthenticated API and web URLs answer 200, an anonymous `git ls-remote`
returns HEAD (host `4181cb3`, component `709e7668`, the deployed pin), the
component README renders its derivation line to a stranger, and all five
submodules were already public, so a recursive clone resolves.

**What publishing exposes, now live** (the operator chose wide reach, and this
is the accounting): the line's external address `37.228.213.83` (97 mentions in
the host docs), the VM line's `84.203.115.61` (1635), the vantage
`170.9.238.141` (55), br-lan addresses (164), two device MACs, the operator's
name and address in every commit's metadata plus one MEMORY mention, and the
DeviceProtection:1 and WIP2 spec transcriptions (2.4 MB and 1.9 MB in the
component) whose redistribution terms are a licensing question rather than a
secret.

**A gap the flip exposed: the artifact is not anonymously retrievable.** The
actions artifacts API lists 12 artifacts anonymously (200) and *downloads* them
with 401, because Actions artifacts always need a token. Neither repo carries a
tag or a release, so the component's `version = "0.1.0"` is exactly what the
spine calls an unreleased version, and the tag-triggered job that builds the
artifacts from a tag does not exist. A stranger can clone and rebuild (the
pinned toolchain image is public), and cannot fetch the bytes the router runs.
The fix is a `v0.1.0` tag and a tag-triggered release attaching the musl
binary, which satisfies the spine's tag rule and makes the bytes anonymous.

**Two follow-ups owed.** `DSLITE_READ_TOKEN` on the host repo is now redundant:
the lane used it to clone the private component, and a public clone needs no
token, so it should be deleted and the lane simplified. And `prose.yml` and the
component's `ci.yml` carry no `permissions:` block, so a stranger's pull
request runs them with the repository default; `contents: read` is the
hardening.

## 2026-09-20 — the release is cut, and its receipt waits for a container

**Four things landed with the flip.** `call/0034` records the visibility ruling,
the audit and the release duty. The read token is gone: the secret is deleted,
the host's reproducible lane materializes the component with the runner's own
token, and the lane passes that way (checked after the change). Every lane
declares `permissions:`, read-only except the release job that creates a
release. And the token never entered a commit: the history holds its *name* in
one workflow commit and *zero* token-shaped values.

**The release exists and is verifiable by a stranger.** Annotated tag `v0.1.0`
at `b15c165b`, the commit the record pins. The component's new Release lane
built the musl binary in the same digest-pinned image and attached
`ds-lite-punch` and `artifact-record.txt` to the release. Fetched with no
credentials:

```
GET https://github.com/slartibardfast/ds-lite-punch/releases/download/v0.1.0/ds-lite-punch
-> 200, 1045168 bytes, sha256 ddfe3903…  (the record's anchor, byte for byte)
```

That closes what the flip exposed: Actions artifacts answer 401 anonymously,
while a release asset answers 200 with the recorded bytes.

**The release phase receipt is owed to a host with a container runtime.**
`host-lifecycle release ds-lite-punch --change-class neither --authorized
call/0034` ran the verify gate green (`prose: clean`, `reconcile: clean`, 69
documents resolved), computed the version `0.1.0 -> 0.1.1`, and then blocked:
"no container runtime (docker/podman) — release BLOCKS; the canonical hash must
come from the recorded toolchain, never an ambient build (R5/R6)". It left the
tree untouched, which is the fail-safe behaving. So `.host-lifecycle-receipts`
still carries the adoption-era `[receipt "release" "ds-lite-punch"] skip, reason
= call/0012` while a release has since been cut; the `done` is owed on a host or
a lane that has Docker, and a release-phase workflow is the natural place for
it.

## 2026-09-21 — 0.1.1 earned by the phase, and releases go immutable

**The release phase earned the release.** Dispatched with the change class
`neither` and authorized by `call/0034`, the lane ran the phase green on a
runner: `verify: green`, version `0.1.0 -> 0.1.1`, and then it *printed the
outward steps it authorizes* rather than performing them. That is the tool's
design, and the lane cannot perform them either: the tag belongs to the
component, whose repository the host's token cannot write, and the token that
could was retired when the component went public. The lane now stops at that
door on purpose and says so, instead of failing on a missing git identity as its
first version did.

**A defect the lane's own flag found.** My version bump left `Cargo.lock` at
`0.1.0`, so the first `v0.1.1` tag pointed at a commit whose `--locked` build
fails. The fix is `a2eddcd`, and with the operator's explicit approval —
the policy refuses a tag rewrite on a repository that already carries a release,
and it was right to — `v0.1.1` was re-pointed at it. A young tag, no release
attached, no consumer.

**The bytes agree across two machines.** The phase's digest and the Release
lane's artifact line are both `4a6bf405838b9d55a1764b9aeed77087fb783d9505c82ac9214ba46152332c71`,
and an anonymous fetch of
`releases/download/v0.1.1/ds-lite-punch` returns 200 with those bytes. The lock
fix did not move the binary, which is what one wants from a lock whose only
change is the crate's own version string.

**The receipt is earned, not asserted.** `[receipt "release" "ds-lite-punch"]
disposition = done`, evidence `v0.1.1@4a6bf405…`, authorization `call/0034`,
replaces the adoption-era skip that reasoned `call/0012`. The record is re-pinned
to `a2eddcd` with that artifact, and `software --check` reports every component
at its pinned SHA.

**Immutable releases are enabled** on the component, by its own endpoint:
`PUT /repos/{owner}/{repo}/immutable-releases`, with `GET` returning
`{enabled, enforced_by_owner}`. The repository-update endpoint carries no such
parameter. Existing releases stay mutable, so both read `immutable: false` and
the setting holds from the next release onward; from then a tag whose release is
immutable can no longer be moved, which is precisely the guard the policy
enforced by hand today. The host's was enabled at the operator's word for
symmetry and reads `enabled: true`; it is inert there, since the host cuts no
releases.

**The lane is proven, and it performs nothing.** Re-dispatched after its fix
(run 35633025190), every step succeeded: `verify: green`, `version: 0.1.1 ->
0.1.2 (the tool computed this from the change class)`, and then the tool's own
line, "release ds-lite-punch v0.1.2 — verified build reproduces. Outward steps,
authorized by call/0034". That authorization is a *log line*: the remote still
carries exactly two tags (`v0.1.0` at `b15c165b`, `v0.1.1` at `a2eddcd6`), no
`v0.1.2` exists, and both repositories' remotes equal their local heads. A
dispatch therefore verifies and says what a release would be, and it cannot
release anything by itself — which is the shape that leaves the outward steps
with a credential that reaches both repositories.

**The five CI failures of the day, all closed.** The host's three release-phase
runs: the recursive-submodule checkout that wedged (cancelled), the missing
`host-template` ("the adopted template has none"), and the push step that failed
on the component worktree's missing git identity — each fixed, and the last two
proven by the clean re-dispatch. The component's two runs on `6b9dee4`: `CI` and
`Release` both failed on the lock, and both are green at `a2eddcd`. And the
2026-09-19 `CI` failure on `04a6666` is the one whose repair produced the pinned
toolchain lane in the first place. Immutable releases are on for the host too.

## 2026-09-21 — the watch counts, after four defects, and its window closes itself

**The carrier watch is armed and counting.** `CARRIER_PROBE=1`, interval 900 s,
the router on the released `a452cf38…`, the helper under systemd on the vantage,
and both disarms scheduled for the same moment: the vantage's timer at
`2026-09-22 19:44 UTC` and a dated cron entry on this workstation for the router
half, which removes its own line. Record:
`plan/0010-.../results/RESULTS-2026-09-21-the-probe-the-translation-hid.md`.

**Four defects sat between the watch and its first counted probe**, each found by
measuring rather than reading:

1. the counting rule lived in the input chain only, and the milestone's own
   ingress translation turns a slot port's arrival into forwarded traffic;
2. the forward rule asked for the slot's port, which the translation has already
   rewritten to the client's before that hook;
3. that rule was a **syntax error** (`syntax error, unexpected @, expecting
   length or checksum or sport or dport`) because a bare `udp` before a payload
   expression makes nft expect a UDP header field — the fix spells it
   `meta l4proto udp`, and the daemon's own `warn: carrier watch install failed`
   line carried the refusal the whole time;
4. an install that only adds leaves an older build's rule, and a rule that is
   merely different counts nothing, so the install now replaces stale variants.

Final reading, with nothing installed by hand: the daemon's own two rules, the
counter at `packets 3 bytes 132`, and `{"event":"carrier-probe","count":3}`.

**Three release lessons, one of them expensive.** The phase verifies the
*pinned* source, so the pin must name the fix before the phase runs: dispatched
earlier, it authorised a digest for a different source than the tag's build. An
immutable release is frozen at creation, so the asset must ride the creation —
the lane is draft-then-publish now. And repairing that first attempt **burned the
tag**: `v0.1.2`'s release was deleted and can never be re-created
(`tag_name was used by an immutable release`), so the fix shipped as `v0.1.3`,
`v0.1.4` and `v0.1.5`, each earned by the phase, attached by the lane, and
downloaded anonymously to check the hash against the authorised digest.

**A stale tuple is read after the restart, never before.** Arming the router
restarts the daemon, so the helper's tuple comes from
`/run/ds-lite-punch/tuple-40000` *after* that restart. The first attempt read it
first; the tuple happened to be re-learned identically, so the mistake cost
nothing, and the ordering is the lesson.

## 2026-09-21 — the template upgrade, by the process, and four entries it cannot record

**The template moved by the ledger, never by a diff.** `host-template` fetched to
`b917d4d` (main HEAD), its grafted shallow clone unshallowed so the tool could
derive a baseline, and `upgrade` migrated the legacy `revision` stamp to
`baseline = e4ed590` by itself. The stamp has never been hand-edited. The pending
span was **12 entries**, not the three the plan assumed, because the derived
baseline sits earlier than the ledger tail the project's copy carried.

**Applied: 8 of 12.** RETIRE-hermetic-exempt, RENAME-repro-waiver,
LEXICON-declaration-is-a-report, PIN-two-surfaces-two-claims,
ACTIVE-corpus-and-agents-manual, LEM-address-direction, LEM-exemplar-section,
LEM-lane-and-mcp. Three of them failed at first only because the tool calls
itself by name and was not on PATH; with `PATH` set they recorded. `--advance`
compacted the contiguous run into `baseline = RENAME-repro-waiver` and the
out-of-order ones stay in the append-only applied set.

**Pending: 4, of which three are one defect's cascade.** `REFS-a-number-resolves`
verifies `grep -rqs "A number that names something resolves to it"
host-template/CLAUDE.md`, and `LEM-pronoun-system` verifies `grep -irqs "pronoun
system" CLAUDE.md`. The template's own `CLAUDE.md` says "The operating manual is
AGENTS.md. This file is a pointer", so the phrases live in AGENTS.md and in no
CLAUDE.md at all: neither verify can pass for a compliant adopter. The ledger's
own rule 2 warns against exactly this shape, and `GATE-refs-in-verify` and
`REFS-a-foreign-citation-names-its-repository` are blocked behind them. A report
to the template is offered rather than filed unasked.

**Tool pins followed the template's own tip**, not only the ledger's floor:
host-lint v0.19.0 to v0.22.0, host-lifecycle v0.53.0 to v0.54.2, both rebuilt and
the skills re-linked (24, up from 19).

**The lem contract flags nothing here.** A full `--all` run under host-lint
v0.22.0 reports 70 advisories and none of them lem, pronoun or first-person, so
the cleanup the operator authorised turned out to be a no-op. Stated limit: a
probe file carrying a bare first-person token was not flagged either, so the
lane's reach over new surfaces is unproven here while its reading of this corpus
is clean.

**The spine re-applied**: AGENTS.md is the new manual (1058 lines) with this
project's specifics appended (30), exactly one heading, a pre-upgrade copy kept in
`/tmp/AGENTS.md.pre-upgrade`; UPGRADING.md copied at the target (58 stanzas);
STRUCTURE.md, CLAUDE.md, LICENSE and lifecycle.manifest were already identical,
and .gitignore already carried the spine's three generated-artifact rules. The
gate is green under the new tools, prose is clean and every reference resolves in
71 documents.

**MCP registered**: `host-lint mcp` as a stdio server in `.qwen/settings.json`,
which `.qwen/` being gitignored keeps machine-local. It is effective at the next
session rather than this one.

**A Site publish race, found by the upgrade's three pushes.** Landing the spine,
the pins and the memory as three commits in a row started three Site runs at
once; the loser's push to `gh-pages` was rejected with
`! [rejected] gh-pages -> gh-pages (fetch first)`. It was self-inflicted and
harmless, and it is now impossible: `site.yml` carries `concurrency: {group:
site-gh-pages, cancel-in-progress: false}`, so a second publish serialises behind
the first. All three lanes are green on the newest commit. The book itself is
published to `gh-pages` and GitHub Pages is not yet enabled for the repository,
so the site URL answers 404 until that setting is turned on.

**Upgrade claims re-verify raw, and two of them call the tool by name.** After the
upgrade, `software --check` raised two HAZARDs — `4a98d92` and
`LEXICON-declaration-is-a-report` "claimed applied but its verify no longer holds"
— and the cause is an asymmetry in the tool: manifest conditions are rewritten by
`self_invoking()` so a bare `host-lifecycle` token becomes the absolute path of
the running binary, while the upgrade-claim recheck runs the entry's verify
through `sh -c` with the inherited PATH, untouched. Both verifies therefore hold
only when a `host-lifecycle` happens to be on PATH. `4a98d92` also pipes, which
the ledger's own rule 3 warns does not survive a non-POSIX shell. Disposed locally
by linking the built tool at `~/.local/bin/host-lifecycle`, which a shell here
resolves, and the gate is green again; upstream is owed the report that the two
recheck paths should agree. The component's own pins and the two defects are
untouched by this: `software --check` reports every component at its pinned SHA.

**The carrier watch stopped counting, and its alarm belonged to the instrument.**
Reading the armed window on 2026-09-22 found the counter frozen at
`packets 10 bytes 440` since 22:14:09 UTC and `{"event":"carrier-silent",
"last_probe":1790028849,"waited":2700,"epoch":1790031549}` at 22:59:09 UTC. The
helper kept sending every 900 s (its journal carries six sends after the freeze),
and probes from a fresh source port sent by hand arrived and translated through:

```host-lint:ignore
170.9.238.141.41060 > 192.168.0.21.40000: UDP, length 16     # eth1, the WAN
170.9.238.141.41070 > 192.168.21.12.40002: UDP, length 16    # br-lan, the client
```

So the carrier still forwards a stranger's traffic and the ingress translation
still delivers. Nothing in the ruleset names `carrier_probe` or `@dslp_ports_udp`
any more; only the counter object and the two sets survive, holding their old
values. The cause is the rule's home: the counting rules are inserted into `inet
fw4`, which fw4 rebuilds, and pbr provoked reloads (`Sending reload signal to pbr
due to firewall action: includes`) at 22:20:37, 22:23:37, 22:38:38, 22:41:38,
00:08:43 and 00:11:43 UTC. `ensure_carrier_probe()` runs once, at startup
(`src/main.rs:975`), and the poll loop only reads the counter, so a wipe leaves a
plausible reading and no way for the watch to tell that its own rule left. The
milestone's central function survives this — the lease path delivered throughout —
but every hour of the window after 22:14 UTC is void, and while armed the watch can
raise only false alarms. Not fixed here: the fix needs the rule to live somewhere
fw4 does not rebuild (the daemon's own `table ip dslp`, the principle the init
script already states for the conntrack policy) or a re-converge on the poll, and
then a fresh window.

**The book is live, and the two upgrade reports are filed.** GitHub Pages is now
enabled on this repository, serving the `gh-pages` branch:
`https://slartibardfast.github.io/agentic-ds-lite-punch/` answers HTTP 200 with
24 KB, first build `built` at `9968f50`. The two upstream reports went to
`connollydavid/host`, because `connollydavid/host-template` has its issues
disabled. `connollydavid/host#22`: two ledger verifies read `CLAUDE.md`
(`UPGRADING.md:359` and `:387`) for text the `ACTIVE-corpus-and-agents-manual`
entry moved into `AGENTS.md`, so `REFS-a-number-resolves` and `LEM-pronoun-system`
can never be recorded and the two entries that depend on them are blocked with
them; the four re-list on every `upgrade .`. `connollydavid/host#23`: the claim
recheck runs an entry's verify raw. That corrects the earlier note here — it is
four claims, not two, that HAZARD with the tool absent from PATH (`4a98d92`,
`LEXICON-declaration-is-a-report`, `PIN-two-surfaces-two-claims`,
`ACTIVE-corpus-and-agents-manual`), `software --check` exits 1, and the manifest's
own `recheck` clause, calling the tool by the same bare name, stays green in that
run.

**The operator's surfaces shipped, and v0.2.0 carries them.** plan/0011 is done,
all nine tasks receipted, and the record is
`plan/0011-operator-surfaces/results/RESULTS-2026-09-22-operator-surfaces.md`.
What landed: a sectioned `--help` with `--version` and an exit-status section; a
manual page in section 8 with ENVIRONMENT, FILES, LOG EVENTS, LIMITS and SEE
ALSO sections the generator appends; five operator pages under `docs/operators/`;
a site at `https://slartibardfast.github.io/ds-lite-punch/` serving `docs/` with
all five pages answering 200; the Unlicense; eight repository topics; and a
release whose three assets are the binary, the manual page and the recorded hash
line. The help text and the manual page come from one clap definition in
`tools/argdoc`, a crate with its own empty `[workspace]` table so the shipping
crate's `Cargo.toml` and `Cargo.lock` never moved and the daemon links none of
it; it prints the text through `include_str!`. The flag-coverage test reads the
parser's own match arms out of the source above the test module, which is what
catches a flag added to the parser without the help.

**Three findings that change how the next release runs.** (1) The router carries
no `man`, no `mandoc`, no `nroff` and no `/usr/share/man` at all, so the
installed page is for a reader who pulls it off the box or takes it from the
release, and the on-box reader is `--help`, which prints the same generated text.
(2) A version bump now moves the artifact bytes, because `--version` compiles the
crate version in. The release order that follows is: apply the bump, tag that
commit, and pin the tagged commit with the hash its build produced. Pinning a
commit and bumping after it leaves the record describing a different source, which
is what the host's reproducible lane said once, in its own words:
`DRIFT     ds-lite-punch rebuild is 0bdb6b926485 but recorded a452cf38c9c7 — NOT
reproducible`. The next commit set the pin and the hash together and the lane
reproduced `924281b2` from the pin. (3) The release phase is one dispatch per
release: it computes the version from the manifest plus the change class and
prints the outward steps, so a dispatch after a completed release proposes the
next version and derives the digest of a bump that exists only in that run. The
dispatch made after 0.2.0 shipped reported `0.2.0 -> 0.3.0` with a digest for a
`0.3.0` source; that proposal was not applied, and the receipt was recorded by
hand from the release's own evidence.

**The release's hash was built three times and the three agree.** The component's
own lane printed `924281b2f6b544d6da6b17dddd312978560cdb467df58a96f15e9016bbe72db9`
for the tagged commit, the Release lane attached the same value in
`artifact-record.txt`, and an anonymous fetch of the asset hashed to the same
value. The release is immutable, and the phase's receipt records
`v0.2.0@924281b2…` authorized by plan/0011.

**The component's lane gained a docs job, and each check was broken first.** The
generated artifacts are regenerated on the runner with the host target named
against the crate tree's musl pin and then compared with `git diff --exit-code`
(a drifted help text was staged to prove it bites); groff writes to stderr and
still exits zero, so the render gate is a non-empty stderr file (an undefined
macro proved it); `tools/link-check.sh` walks the authored docs and a renamed
target proved it; and the prose audit runs the host's own `host-lint`, pinned by
a clone and build of `v0.22.0` (which resolves to `0eeabc20`, the commit this
host's submodule pins) from `/tmp`, because cargo reads its config from the
working directory and the component's `.cargo/config.toml` would aim that build
at musl. `.host-lintignore` names the two archived specification transcriptions.
The naming half is deliberately not wired: it reports 86 findings over the
component, every one a source comment holding an RFC section reference, a
numbered UPnP clause, or a pre-adoption plan label.

**The operator rejected the vocabulary, three times, and the words are now the
RFC's.** First `--max-rescues` (a plural that hid what the number counts), then
"hold" ("we ain't Lassy"), then "rides"/"lands" and the rest of the business
jargon. `call/0035` records the mapping, and each sense took the word the
behaviour comes from: the feature that keeps a named device's mapping alive is
`--keepalive`/`KEEPALIVE`/the `keepalive` event/`src/keepalive.rs` (RFC 8085's
word); attempts to put a vanished mapping back are `--max-refresh-attempts`
(RFC 4787's verb); a tuple a slot owns is `owned`/`is_owned`, which the code's
own comment already said; the TCP connection that maintains a mapping is
`ConnectionState`/`run_connection`/`connection` with `Live` and `Dead`; and a
client's record in the facade is an `entry`, with the spec-derived rule renamed
from "one-holder" to "one-mapping". The component commit is `e8c47d8` (23 files,
217 tests green), the surfaces regenerated, and `plan/0009` and `call/0026` were
renamed to keepalive through `git mv` with every live reference moved with them
(`4cf3d3b`).

Three things deliberately did not move. The software's name keeps "Holder",
because that is the derived name of `punch` the operator set. Ordinary English
stays: a lock is held, a directory holds files, a client holds a mapping, a rule
holds. And the records keep their words: `MEMORY.md`, the closed milestone
bodies and the results files quote what was true and what was said at the time,
so the old flag name survives there and in `plan/0009`'s own body.

Two traps from this sweep are worth keeping. A phrase-level rule is sharper than
a word-level one, and it still bites: `("the hold", "the keepalive")` matched
inside "the holder" seven times in `tcpslot.rs` and coined "the keepaliveer",
and `("is the caller's", "is left to the caller's")` overreached into a sentence
about a 600 response. Both were caught by reading the diff and the compiler, not
by the grep. And the naming audit reads "RFC 8085 section 3.5" as a positional
tell, so the decision cites the RFC by its subject instead.

**The release that carries the new flag is owed and not cut.** The published
`v0.2.0` documents `--hold` and `--max-rescues` in its help text and manual page,
so the words a stranger reads from the release are the rejected ones until a new
tag ships. The rename is a flag removal and an addition, which the tool maps to a
minor bump, and the phase reads the manifest version, so it would compute
`0.2.0 -> 0.3.0`.

**"This has been a productive session" — the operator's words, and the record of
what it produced.** The sentiment lives here rather than in `call/`, because that
room holds decisions about the software and a feeling is not one of them; the
session's decision is `call/0036`, on the release order the embedded version
forced. What the session produced, in the order it happened: plan/0011 opened and
closed with nine receipted tasks, from a generated `--help` and a manual page to
five operator pages and a live site; `v0.2.0` cut, published and immutable,
carrying the binary, the page and the recorded hash; `v0.2.0`'s own defect found
and fixed, which was the operator rejecting `--max-rescues`, then "hold", then
"rides" and "lands"; `call/0035` recording the words; the milestone and decision
slugs renamed onto them; and `call/0036` recording what the release taught.

**The audit at the end of the session, and its one open item.** `validate`,
`prose`, `reconcile`, `book --check`, `manifest --check`, `software
--verify-setup` and `dream` all report clean, and the reference sweep resolves
all 74 documents. `software --check` reports one item:
`DRIFT software/ds-lite-punch/main at 425642dc4084 but pinned to f0c65e3938ac`.
That is the release thread stated as a fact: the component moved past the tagged
0.2.0 when the vocabulary landed, and the pin follows the next release. The other
open threads, unchanged by this session: the four upgrade ledger entries blocked
upstream (`connollydavid/host#22`), the component's naming lane with its 86
source-comment findings, the carrier watch whose counter is dead and whose window
is void (so plan/0010 wants its closure and its results file), and the router
still running 0.1.5, where the deploy is the operator's step.
