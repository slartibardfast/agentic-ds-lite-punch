# MEMORY: working memory (append-only)

Ground truth, measurements, and session state that a fresh session needs. Newest
entry on top. Append, never rewrite; an entry that is wrong is superseded by a
newer one, not edited.

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