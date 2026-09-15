# MEMORY: working memory (append-only)

Ground truth, measurements, and session state that a fresh session needs. Newest
entry on top. Append, never rewrite; an entry that is wrong is superseded by a
newer one, not edited.

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
  Recorded follow-up: clamp granted leases to a device policy max so
  the GC reclaims vanished clients; the console pattern survives a
  bounded lease because the games re-Add on boot.

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