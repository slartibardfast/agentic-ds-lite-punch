# ds-lite-punch implementation brief v2: facades + observation rescue over one slot engine

**Audience:** implementation agent. **Repo:** `ds-lite-punch`, Rust, musl-static,
single process, one poll loop, procd-managed on ImmortalWrt (br-lan
192.168.0.0/24, daemon at 192.168.0.21, IPv4 egress = DS-Lite tunnel to AFTR).
**[OPERATOR]** = needs human/hardware; agent prepares scripts and analyzes
output. This brief supersedes v1; changes are the observation engine (Phase G),
expanded measurements (Phase C), invariant enforcement, and the quirk ledger
(§11). Busybox router: no `nohup`/`pkill`/`timeout`; use `&`, `pgrep`+`kill`,
`tcpdump -c`. `/tmp` is tmpfs: self-restoring `trap`s in every script, router
state clean after every run.

> **Reconciliation deltas (agent, 2026-08-31), read before implementing.**
> Verified against the deployed source and the live router. Where the brief
> conflicts with deployed reality, the delta wins and this section is
> authoritative. Carried forward from v1, re-checked against v2:
>
> 1. **No local `dsltun` interface.** Router-side ds-lite (wan4o6) is disabled;
>    the hub owns the softwire and the tunnel terminates there. The router's
>    VM line is plain `eth1` (192.168.0.21/24, gateway 192.168.0.1). Capture on
>    **`eth1`** everywhere the brief says "on the tunnel" (A0.2, A2, G8).
>    The softwire to the AFTR exists; it just is not a local interface.
> 2. **The v1 core's inbound forward is userspace `IP_TRANSPARENT`
>    per-datagram** (`forward.rs`), not TPROXY. No TPROXY rule set exists or
>    is planned. The brief's "implement TPROXY as the fix if reply-path
>    validation failed" maps to: debug the SNAT pin (rule order, `ip rule`
>    priority, conntrack). There is no TPROXY variant to build.
> 3. **Tokio stays (DECIDED 2026-08-31, David): hand-rolled epoll rejected.**
>    The v1 core ships tokio (single process, musl-static, about 640 KB). The
>    brief constraint "no async runtime" (§2) reads as "no second process, no
>    new heavy framework"; the runtime's single IO loop satisfies "one poll
>    loop". Phase B must NOT rewrite the v1 IO path.
> 4. **`--gateway` + STUN host routes are load-bearing** (`ip route replace
>    <stun-ip> via 192.168.0.1`): without them the default route sends STUN
>    down vdsl4 and maps the wrong NAT. Reproduce per slot's rotation; absent
>    from the brief's config list, present in the v1 core's deployed CLI.
> 5. **State paths.** Published tuple stays at `/run/ds-lite-punch/tuple`
>    (existing consumers); epoch + leases under `/tmp/dslp/` per B9/B10.
>    Keep both, do not merge.
> 6. **The v1 endpoint is the router itself** (192.168.21.1:40001 sink).
>    A2/G8 need a real second br-lan host (Arch LXC 192.168.21.10 or a
>    laptop).
> 7. **PCP + NAT-PMP share UDP 5351** (RFC 6887 §6). Bind
>    `192.168.21.1:5351/udp`, LAN-only, both protocols on it (D1/D5).
> 8. Result codes: 0 to 8 per §A.3 as listed; `CANNOT_PROVIDE_EXTERNAL_PORT` =
>    9; verify all nine numerics against the RFC during D3. Quota default 16
>    (headroom under Juniper's 32/client max).
> 9. Existing Kani: 8 harnesses / 192 checks / 0 failures; "8 existing + per
>    phase new" at every gate. Allocator proof note: `BTreeSet` used-sets
>    stalled the solver; the used set is a sorted `Vec` (at most 32 slots),
>    which keeps the proof surface array-based (see `slot.rs`).
> 10. **Phase G is in scope and assigned.** The observation rescue engine
>    (G1-G10) rides on the slot engine. CDC per G1 DECIDED (2026-09-01): one
>    `Cdc` trait, three backends: nft `flow_obs` set mirror (primary), Aya TC
>    hook (first-class performance tier, not an escalation), `/proc` polling
>    (fallback). The conntrack-CDC evidence (netlink CT events silent on this
>    build) is recorded; the Aya gate in the old §13 STOP list is removed.

## §0 Mental model (guides all design decisions)

The AFTR mapping table is authoritative and unreadable. Its key is the inner
tuple (EIM); its TTL is 5 to 10 s. Write to it: any datagram from the inner
tuple. Read it: STUN XOR-MAPPED-ADDRESS.

The B4 NAPT (nft + conntrack): RFC 6333 assigns the router this role; it is
fully ours. Pin / shadow-bind / DNAT = translation agreement. conntrack =
change-data-capture.

The slot table is a shadow replica of AFTR state plus leases. Admission:
config | PCP | UPnP | observation.

The daemon is a **lifetime shim with admission control**. On the LAN side it
implements the behavioral contract the AFTR refuses to keep (RFC 6888
lifetimes, reportable tuples, divergence notification). On the WAN side it
changes nothing and owns exactly one property: the mappings do not die. Five
verbs only: TTL-write (keepalive), read (STUN), translation-agreement (nft),
CDC (conntrack), admission/eventing (facades + epoch).

## §1 Facts you may rely on (measured or spec; do not re-derive)

1. AFTR UDP idle timeout 5 to 10 s, node-dependent (RFC 6888 floor violated).
   No inbound IPv4 except via live mappings.
2. UDP EIM+EIF proven. TCP EIF proven 2026-08-31 (5/5 probes vs 5/5
   ECONNREFUSED control). External ports always AFTR-chosen random-high,
   never equal to inner (RFC 6888 honors randomization; permanent and
   upstream). TCP external port space separate. TCP idle lifetime unmeasured.
3. **EIM means any destination refreshes the same mapping** (proven by the
   v1 core's rotating STUN). Corollary: STUN keepalive and tuple discovery
   are one packet; and all servers must return the same XOR-MAPPED-ADDRESS,
   because disagreement means churn or a lying server.
4. TCP unmapped: AFTR RSTs (the dead-mapping signal exists for TCP only).
   UDP unmapped: assumed silent drop; ICMP behavior unknown (unmapped-ICMP
   probe).
5. DS-Lite per RFC 6333: the B4 (router) performs NAPT. Our SNAT/shadow-bind
   work is the spec's role, not a hack.
6. Linux: installing an nft rule does **not** re-translate existing conntrack
   entries. Conntrack entry death stops DNAT of inbound packets.
7. The v1 core is deployed and clean; Kani 8 harnesses / 192 checks / 0
   failures. Its source-preserving inbound-forward mechanism is proven;
   reuse it verbatim wherever forwarding is needed.

## §2 Binding constraints and invariants

**Constraints (violation = stop):** UDP only; no TCP grants until the TCP
idle-lifetime test is measured.
No console-shaped code (no MACs, no vendor ports, no client detection; PSN
and Switch are acceptance workloads/observations only). Everything behind the
router on br-lan. uk/us hosts never relay/backup paths. eBPF only as
Rust/Aya, only after userspace paths are exhausted. UPnP IGDv1 only (PS3
cannot discover v2-only gateways). Single process, one poll loop, no async
runtime, no new heavy deps, parsers hand-rolled and tiny. No TLS.

**Invariants (enforce in code + Kani):**

- **One holder per inner tuple.** Precedence: static > lease (PCP/UPnP
  share one table row) > observation. The allocator refuses a second holder;
  observation never captures a tuple a lease/static holds. Split-brain equals
  tuple churn mid-session equals STOP condition.
- **Keepalives originate from the tuple as seen past the B4 NAPT.**
  Config/lease slots: daemon socket at R. Observed flows: shadow socket at
  the conntrack-resolved post-NAT port. The SNAT pin is this invariant as a
  rule.
- **Clocks nest.** 2 s keepalive sits below the 5 to 10 s AFTR TTL,
  which sits below the rescue window, which sits below the conntrack timeout,
  which sits below lease lifetimes. Record actual sysctls (conntrack-CDC
  test); document the table; every layer's recovery assumes the layer below
  does not die first. AFTR-before-conntrack death is what makes G's
  promotion structural, not contingent.
- **Honesty gradient per channel.** PCP reports the true tuple (in-spec).
  UPnP reports requested-port plus true-IP (request-channel lie, never
  load-bearing because the SNAT pin makes the client's observed tuple equal
  the held tuple). Observation is silent (no client to inform). Never
  synthesize port preservation anywhere.
- **Restoration cheaper than construction.** Respawn = rebind + one STUN
  cycle; reboot = epoch reset + tmpfs wipe, aligned exactly with AFTR state
  death.

## §3 Phase map

| Phase | Content |
|---|---|
| A | v1 acceptance [OPERATOR-gated], blocks D/E sign-off, runs against the deployed v1 core |
| B | Slot engine refactor, starts immediately, foundation for D/E/G |
| C | Measurements: divergence, TPROXY, and idle-lifetime tests feed D/E; CDC, shadow-bind, rescue-timing, and signal checks gate G; unmapped-ICMP probe optional |
| D | PCP facade, after B (+ A sign-off) |
| E | UPnP IGDv1 facade, after D |
| F | Switch observation [OPERATOR], anytime hardware available, zero product work |
| G | Observation rescue engine, after B and the Phase C gate measurements; independent of D/E order |

## §4 Phase A: v1 acceptance (restated from v1)

1. **A0 preflight.** Daemon alive under procd; STUN cadence about 2 s
   confirmed via `tcpdump -c 20` on eth1; nft ruleset present; `/tmp` clean.
   All green, or restore known-clean first.
2. **A1 reply-path validation.** A br-lan endpoint PC sends STUN from the v1
   endpoint tuple; assert its XOR-MAPPED-ADDRESS equals the daemon's
   discovered tuple (SNAT pin working). If a peer-scoped rule blocks this,
   use paired echo: external prober sends to the tuple, PC echoes, prober
   confirms. **STOP** if replies egress with a fresh port: debug rule order
   and `ip rule` priority before any facade work. The reply-path outcome
   also resolves the TPROXY question (TPROXY needed only if this validation
   failed).
3. **A2 PSN NAT test [OPERATOR].** DHCP-reserve console at the endpoint;
   capture br-lan + eth1 both sides during the console's connection test.
   **Pass = NAT Type 2 AND** pcaps show console egress SNAT'd to R and
   inbound probes forwarded with true peer source. **Fail = forwarding model
   falsified, STOP everything.**
4. **A3 keepalive-pause soak.** `kill -STOP; sleep 12; kill -CONT`; expect
   churn, then detect, then republish; old tuple dead, new tuple
   inbound-reachable within a single keepalive interval. 3× at 12 s, 3× at
   20 s. This mechanism underwrites every lease and every GENA event (E4).

## §5 Phase B: slot engine (v1 items + synthesis additions)

1. Branch `p2-slot-engine`. With one static map configured, packet behavior
   byte-identical to the v1 core (pcap diff = bisection baseline).
2. Core: `Slot { bind_port R, target, external: Option<(IpAddr,u16)>,
   stun_cursor, phase_ms, lease }`; `Lease = Static | Granted{client,
   int_port, proto, lifetime, expires_at}`. One table, keyed on inner tuple,
   with PCP index (proto, int_port, client) and UPnP bookkeeping external-port
   index.
3. Config: repeatable `--static-map R=ip:port`; `--slot-port-range
   30000-39999`; `--max-slots 32`; `--max-maps-per-client 16`.
4. **Holder registry (one holder per inner tuple).** Every allocation passes
   a single `holder_of(inner_tuple)` check; a duplicate is refused and
   logged. Kani property: no state reachable with two holders.
5. nft dynamic state as **named-map elements only** (fixed rule set installed
   once): (src ip, src port) to R for the pin; inbound per the v1 core's
   proven mechanism unchanged. Slot create/delete = element add/delete,
   atomic.
6. **STUN majority vote (new).** The shared STUN client compares each
   XOR-MAPPED-ADDRESS against the cached tuple. At least 2 servers agree on a
   new value: churn and republish. Single-server disagreement marks the
   server suspect, rotates on, and does not republish. Log both paths. Kani:
   the vote logic.
7. Stagger STUN: slot i at `(i × 2000/N) ms` offset. Per-slot independent
   server rotation.
8. Persistence in `/tmp/dslp/`: `epoch` (creation ts, written on first
   start), `leases.tsv` (rewritten on change). Respawn rebinds the same Rs,
   re-STUNs all slots (startup burst allowed), re-adds elements: one-cycle
   restore. Test with `kill -9`.
9. Epoch semantics: `epoch = now − creation_ts`; tmpfs survives respawn
   (continuous) but not reboot (reset), correct cache-invalidation alignment
   (the restoration-first rule). Feeds D5.
10. GC: lease expired ×3 grace with no refresh and no observed traffic frees
    the slot. Unleased-undiscovered slots die at 60 s.
11. **Record conntrack facts (feeds the conntrack-CDC test and the
    clocks-nest rule).** Read
    `net.netfilter.nf_conntrack_udp_timeout` and `_stream` from sysctls; write
    them into the README clock-nesting table. Do not assume defaults.
12. Acceptance: 3-slot 30-min soak (feeds the per-slot divergence test);
    kill-9 respawn restore; a pcap identical to the v1 core's; Kani (lease
    state machine, epoch monotonicity,
    allocator, holder uniqueness, majority vote).

## §6 Phase C: measurements

> **RESULTS RECORDED 2026-08-31** (full method + evidence in project memory
> `vm-aftr-dslite.md`; probe tool `tools/conntrack-probe`):
>
> - **No per-slot IP divergence.** 3-slot 30-min soak held
>   `37.228.213.83` on all slots (59230/59346/59274), 0 churn post-confirm,
>   0 disagreements. E3 returns the live value, no slot-0 caveat. Stagger
>   verified on-wire (+0/+668/+1335 ms per 2 s cycle).
> - **Netlink conntrack event multicast does NOT reach userspace** on
>   this 6.12.35 ImmortalWrt build (config=y, module loaded, CT_GET dump
>   round-trips cleanly, groups 1-32 joined, `nf_conntrack_events` 0/1/2 all
>   silent). Consequence: netlink CT events are not the CDC; see G1 for the
>   layered design it drove. Conntrack clocks: 60/180/30 s (clocks-nest
>   rule: the AFTR dies before conntrack, so promotion is structural).
> - **G1 CDC DECIDED (2026-09-01, layered, not a fallback ladder):**
>   1. **Primary: nft dynamic-set mirror** `flow_obs` (`type ipv4_addr .
>      inet_service`, `flags timeout`, about 15 s) in `table ip dslp`,
>      populated by a filter-hook postrouting rule on `oifname eth1` UDP at
>      priority 110. **Gating test PASSED (2026-09-02, on-box):** the
>      observer sees the post-NAT source; elements are the shadow-bind tuples
>      `(192.168.0.21, R_nat)` directly; no conntrack read for R_nat (tier 3,
>      CT_GET assist, is dead). Two measured corrections to the brief: fw4's
>      `srcnat` chain sits at the default `priority srcnat` = 100 (**not
>      -100**), so the observer must be above 100 (110 used); and fw4's eth1
>      NAT is a fixed `snat ip to 192.168.0.21` (port-preserving), so R_nat =
>      the flow's original source port. Kernel keeps membership + expiry; the
>      15 s element timeout IS the silence detector; userspace reads only
>      live candidates each tick.
>   2. **Performance: Aya TC hook on br-lan** (about 50 LOC or less: parse
>      eth/IP/UDP, key (saddr, sport), store ktime) into a BPF map, userspace
>      drains: same candidate semantics with no nft read churn. **A
>      performance win when BTF is available, NOT a stretch goal** (David,
>      2026-09-01). Confirmed available here: `/sys/kernel/btf/vmlinux`
>      present, `DEBUG_INFO_BTF=y`, and qosify already runs tc-hook + BPF
>      maps in production on this router.
>   3. **Assist: ctnetlink targeted CT_GET** per candidate, only if the
>      primary set lands on pre-NAT tuples (recovers R_nat). Dead if the
>      post-NAT variant holds.
>   4. **Fallback: `/proc/net/nf_conntrack` polling** (existence +
>      [UNREPLIED]/[ASSURED]), kept, last resort, `--cdc proc` (David: "I
>      don't like 1, keep it as a fallback").
>   Implemented as one `Cdc` trait with three backends (`nft` / `aya` /
>   `proc`), same contract: live bidirectional UDP candidates with
>   shadow-bind tuples at cadence at most 2 s. **Aya is no longer listed in
>   §13 as an escalation requiring justification; it is a first-class tier.**
> - **Shadow-bind feasibility: PASS.** The relay's own keepalive socket IS a
>   bound NAPT-translated tuple (soaked stable 30 min); the rescue-timing rig
>   verified WAN-to-relay-socket delivery through the pin. (Its self-probe
>   EADDRINUSE = a local-source artifact: the probe from the router's own IP
>   collides with the relay's IP_TRANSPARENT bind; external sources cannot
>   collide.)
> - **Rescue timing.** The mapping survives host silence at least 45 s
>   (relay keepalive owns lifetime; probes arrived at relay socket at
>   T+0/15/45). External echo
>   round-trip half: globalping UDP traceroute does NOT honor fixed ports
>   (probes 33434+n; identical on mapped/unmapped), so **[OPERATOR] phone
>   hotspot per G8.4**. Do not fake it.
> - **Keepalive: the liveness signal.** (30-min stability; no additional
>   probe needed).
> - **Unmapped UDP on the pool: silent drop.** No ICMP; contrast TCP,
>   which RSTs. Dead-mapping detection: TCP has RST; UDP relies on
>   shadow-STUN (G3e) + slot GC.
> - Bonus: the AFTR re-issued the SAME external port to the same inner tuple
>   after relay restart (twice). Recent-mapping reuse observed, noted.
> - Deploy gotcha: manual (non-procd) instances LEAK nft pins + accepts on
>   kill; production restore = single pin + one accept (verify with
>   `nft list map ip dslp snat_map` after any manual instance).

1. **Per-slot public IP divergence.** Log per-slot XOR IP for 10 min, 3
   slots. Identical: GetExternalIPAddress returns the live value.
   Divergent: PCP stays per-slot-honest; UPnP uses slot-0 + documented
   limitation. Record the fact either way. **[DONE: no divergence.]**
2. **TPROXY decision.** Resolved from the reply-path validation: a pass
   means "no fallback needed" recorded;
   fail means debug the SNAT pin (rule order / `ip rule` priority /
   conntrack) and re-run A1/A2. Never build both paths speculatively.
   **[Resolved from A1/B10: SNAT pin works, no TPROXY path; see B10 pcap
   diff.]**
3. **TCP idle lifetime (deferred, non-blocking).** Hold UDP mirror;
   establish TCP mapping; probe mapped tuple at 15/30/60/120/300/600 s idle
   gaps; binary-search the death point. Gates TCP grants only.
4. **Conntrack CDC read.** Measure before building G: sysctl values (see
   B11) AND whether `netlink` conntrack events fire on activity from a br-lan
   host (use the rescue-timing rig); `/proc/net/nf_conntrack`
   existence/[UNREPLIED]/[ASSURED] polling as cross-check; also confirm
   on-activity state-change notifications reach userspace. Record the
   mechanism choice for G1. Do not assume netlink events fire on default
   kernels: the router's kernel is a custom ImmortalWrt build. **[DONE:
   events do not deliver; G1 = /proc polling.]**
5. **Shadow-bind feasibility** (gate for the shadow-socket rescue step).
   From the router, `bind` a NAPT-translated (NAT addr, R_nat) tuple: the
   192.168.0.21:40000 v1-core socket is the existence proof; the
   rescue-timing rig re-proves it with a NAT'd port and a
   *second* flow, and checks the response path to a shadow socket.
   PASS/FAIL recorded. **FAIL means the raw-injection rescue path is the
   route.** **[DONE: PASS, shadow-socket path.]**
6. **Rescue-timing rig.** A br-lan host sends UDP toward an external echo
   (e.g. `socat`/python on the vdsl4 line, or a public STUN server), then
   goes silent; measure at 0/2/5/10/15/60 s: (i) is the tunnel still mapping
   (external STUN from the same tuple sees the mapping), the rescue window
   edge; (ii) does an external prober reach the host through the existing pin
   (the lease slot's tuple), with pin-liveness tested separately from mapping
   liveness; (iii) the timing of both. Budget the rescue thresholds from this.
   PASS/FAIL for live-pin injection. **[DONE: mapping survives 45 s of
   silence; echo half [OPERATOR].]**
7. **Signal-of-life check.** The managed daemon's STUN keepalive from the
   pinned tuple is itself evidence the mapping lives; any external delivery
   to the pinned tuple is the strongest. Record, don't chase. **[DONE:
   keepalive is the signal.]**
8. **ICMP-on-unmapped probe [optional].** From the router send unmapped-tuple
   UDP and note ICMP behavior on both lines. Answer: silent drop or ICMP
   unreachable? Informs "dead mapping" detection for TCP and defers UDP
   detection (falls to G/slot GC). Record finding or defer. **[DONE: silent
   drop.]**

## §7 Phase D: PCP server

1. Socket: `192.168.21.1:5351/udp` (br-lan; never 0.0.0.0). NAT-PMP behind
   `--natpmp` (default on), same port.
2. Parser: hand-rolled; every length is checked against the remaining buffer
   *before* use; options skipped by length; no unguarded indexing. Kani owns
   the parser. **The wire format sketch above is memory, not authority:
   verify every field, opcode, option type, and result code against RFC 6887
   §§6-9 and the A.3 table during implementation.**
3. Dispatch. **ANNOUNCE**: epoch only. **MAP UDP**: existing key = refresh
   (extend, respond with *current* live tuple; this is how churn heals
   client-side); new = quota check (USER_EXQUOTED / NO_RESOURCES), then
   allocate R, add pin element, begin discovery. **MAP TCP**:
   UNSUPP_PROTOCOL (until the TCP idle-lifetime measure). **PREFER_FAILURE**: always
   CANNOT_PROVIDE_EXTERNAL_PORT, never substitute. **Discovery in flight**:
   silently drop the request (client retry is spec-expected;
   drop-not-queue). **Discovery failed**: NETWORK_FAILURE next request.
   **PEER**: SUCCESS no-op behind `--pcp-peer` (EIF = no per-peer gate; log
   first N). **THIRD_PARTY**: NOT_AUTHORIZED. Unknown/malformed:
   MALFORMED_REQUEST; parser never panics.
4. SUCCESS MAP carries the **real** STUN tuple as assigned external (clients
   MUST accept assigned ≠ suggested; PCP is fully honest). Echo nonce.
   Granted lifetime = min(requested, `--pcp-max-lifetime` 600); document:
   bounds post-churn staleness (refresh reports the then-current tuple).
   Lifetime 0 = delete now.
5. Epoch from B9 in every response. NAT-PMP behind `--natpmp` (default on):
   opcodes 0/1/2, response opcode req+128, fixed 7200, no epoch.
6. **Before implementing lease reconciliation with E, read RFC 6886
   (IGD↔PCP interworking).** Where IGD lease semantics and PCP lifetimes
   collide, follow 6886's mapping table rather than inventing. Verify section
   numbers during implementation.
7. Kani: parser vectors (all truncation offsets, bad version, option length
   edges, 0/1-byte), dispatch, quota arithmetic, epoch continuity across a
   simulated respawn.
8. Acceptance (in-repo test client): **flagship: MAP's returned tuple equals
   what a STUN Binding sent by the client from (client_ip, int_port) itself
   observes** (the pin makes the PCP answer and client self-observation
   identical). Plus: refresh extends; lifetime-0 frees (element gone);
   PREFER_FAILURE fails; THIRD_PARTY refused; NAT-PMP public-address matches.
9. Non-goals: DHCP option 157, TCP success path, relay.

## §8 Phase E: UPnP IGDv1 facade (v1 items + additions)

1. SSDP: join 239.255.255.250:1900 on br-lan, REUSEPORT; M-SEARCH for the
   five v1 STs; responses delayed randomly within MX; alive NOTIFY at
   max-age/2; byebye on clean exit; stable persisted UDN; bootid.
2. Description docs on `--upnp-port` (default 49152), br-lan only:
   the chain IGD, WANDevice, WANConnectionDevice, then WANIPConnection:1 (+
   WANPPPConnection:1 alias, default on). SCPDs cribbed from miniupnpd (BSD;
   attribution comment).
3. SOAP: accept **both POST and M-POST/MAN** (PS3-era stacks). Actions:
   GetExternalIPAddress (**live STUN value, never 0.0.0.0**; pre-discovery =
   last known; on per-slot divergence: slot-0 + documented limitation);
   AddPortMapping (InternalClient in br-lan else InvalidArgs; **UDP only**;
   RemoteHost accepted + ignored (EIF); **NewLeaseDuration=0 accepted as
   infinite**, modeled as a max-life lease the engine self-refreshes; re-Add
   same key = upsert, never duplicate; external port grant is
   report-requested, documented); DeletePortMapping (absent faults; verify
   codes); GetSpecific/GetGenericPortMappingEntry (stable enumeration; past
   end faults; verify codes); GetStatusInfo (Connected);
   GetConnectionTypeInfo (IP_Routed).
4. **Paired TCP+UDP Add quirk (live decision point).** Consoles commonly Add
   both protocols. Default = honest TCP fault per scope. At E5, observe the
   real console: if it aborts its whole setup on the fault, switch to the
   documented fallback (silent no-op success for TCP Adds,
   "report-granted, no datapath", consistent with leases-advisory). Record
   the decision in the boundary file.
5. GENA minimal: SUBSCRIBE/UNSUBSCRIBE, SID, initial NOTIFY, renewal, expiry
   at 2× timeout. **Event ExternalIPAddress on every churn/republish** (A3 is
   the proof this fires). Callback URLs http + br-lan only, validated.
6. Conformance: `upnpc -l / -a / -d` full verb set (capture both sides);
   M-POST parity via curl with MAN header, assert identical dispatch. Then
   **[OPERATOR]** PS3/4/5 test (reuses the A2 chain; PS3 is the v1 acceptance
   client).
7. Kani: SSDP header grammar, SOAP dispatch + fault paths, enumeration index
   math, SID/SEQ state machine.
8. Documented-not-built: miniupnpd-WAN-deaf + lease_file tail escape
   hatch: one README paragraph. Hardening: size caps, LAN-only binds, no
   panics, capped logs.

## §9 Phase F: Switch observation [OPERATOR], zero product work

1. Record predictions *before* testing: VM line: NAT Type **D** (grader
   checks source-port preservation; AFTR randomizes; structurally unfixable
   at any layer we own). vdsl4 control: **B**. Test: Settings, Internet,
   Test Connection, each line.
2. Lobby join on the VM line via stranger matchmaking (Pia/NEX title).
   Interpretation: D-to-B peer join works = boundary settled (grade measures
   preservation; gameplay runs on EIM+EIF observed-tuple exchange). D-to-D
   failure is ambiguous: both sides' NAT affects the outcome; do not
   conclude from it.
3. Write the conclusion + residual uncertainties (does the grading probe
   share a socket with game traffic; hairpin unmeasured, needs a second VM
   vantage, mark untestable-now) into the boundary file.
4. **Enforced non-actions:** no Switch detection, no Switch-specific rules,
   no preservation emulation. Review rejects any. If the operator points a
   static map at the Switch's address, that is a README usage example of
   generic functionality, not code.

## §10 Phase G: observation rescue engine (new)

Rides on B (holder registry, STUN module, pin-element machinery). Gate: the
conntrack-CDC record, shadow-bind PASS (else raw injection), and the
rescue-timing margin measured. A-phase sign-off does **not**
block G.

1. **G1 CDC (DECIDED 2026-09-01, layered, not a fallback ladder).** Netlink
   CT events are not used (measured silent; the conntrack-CDC record). One
   `Cdc` trait, three
   backends, same contract (live bidirectional UDP candidates +
   shadow-bind tuples at cadence at most 2 s): **(a) nft `flow_obs`
   dynamic-set mirror** (primary: kernel-managed membership + 15 s expiry,
   post-NAT tuples, gating test PASSED 2026-09-02, priority 110 above fw4
   srcnat 100; CT_GET assist dead); **(b) Aya TC hook on br-lan**
   (performance tier: BTF confirmed, qosify tc+BPF-map precedent live; *a
   performance win when available, not a stretch goal*); **(c)
   `/proc/net/nf_conntrack` polling** (fallback, `--cdc proc`). Full
   rationale in the Phase C results block. G2 uses no `silence budget`
   condition: the CDC's kernel-side timeout is the silence detector.
2. **G2 policy predicate (console-agnostic, Kani truth table).** proto UDP ∧
   src in br-lan ∧ dst off-LAN ∧ entry has seen reply (bidirectional;
   a mapping matters to a peer) ∧ inner tuple not held by static/lease (the
   one-holder rule) ∧ rescues below `--max-rescues` (8). No other condition. No
   hostname/MAC/port allowlists; review rejects any. (The `silence budget`
   clause is gone: the CDC's kernel-side set timeout is the silence
   detector; a silent flow evicts itself from the mirror; the predicate only
   sees live candidates.)
3. **G3 rescue sequence (exact order).** (a) Read the entry's translation:
   NAPT source address + R_nat from conntrack, never assumed. (b) Bind
   shadow socket (NAT addr, R_nat), gated on the shadow-bind test. (c)
   Install pin element
   (src_ip, src_port) targeted at R_nat, any-dst UDP: safe to install
   immediately; the no-retranslate quirk means the existing entry is
   untouched, and the pin targets the *same* R_nat, so present and future
   flows agree; any-dst scope makes all console traffic from that port share
   one AFTR inner tuple (full EIM, consistent with the v1 core). (d) Send
   STUN from the shadow socket: EIM means it refreshes the flow's mapping,
   the peer receives nothing. (e) Record XOR-MAPPED-ADDRESS = the flow's
   actual external tuple (free per-flow observability; a large slice of the
   deferred EIF-loss item). (f) 2 s cadence while active, staggered with
   slots.
4. **G3b raw-injection fallback (only if shadow-bind failed).** Craft a
   br-lan packet
   matching the entry's original direction (src = host:port, dst = entry's
   original peer), emit raw; the conntrack match applies the stored SNAT.
   Document the cost: the original peer sees a 0-byte UDP datagram. Prefer
   G3 whenever possible.
5. **G4 promotion (structural, per the clocks-nest rule).** Trigger =
   datagram receive on the shadow socket. Forward
   in the v1 style to the observed host:port (inbound works
   again; the peer sees the flow as alive). conntrack is never touched;
   forward is socket-level. Keepalive continues while active; mapping
   liveness = shadow STUN. This is the property: AFTR dies before local
   state does.
6. **G5 exit.** Budget exhausted (`--max-rescues` reached) | datagram
   received (promotion) | tuple claimed by static/lease | entry destroyed
   and no inbound for a grace period. On exit: close shadow socket, delete
   pin element, drop record. (Pin deletion can change the console's external
   tuple; acceptable only at budget-exit, flow presumed dead.)
7. **G6 caps/logging.** Max rescues; log the first 20 events fully, counters
   after.
8. **G8 acceptance (scripted rig built on the rescue-timing setup).**
   (1) Control: flow silent, no
   injection, tuple X dead by T+10. (2) Rescue: injection at measured
   threshold, X identical at T+10/T+60/T+300 (within budget) via shadow
   STUN. (3) Mid-rescue pin: a LAN host sends a *new* datagram from (host, P)
   toward a different destination; tunnel capture shows inner source port
   R_nat. (4) Promotion: delete the conntrack entry (`conntrack -D` if
   present, else netlink, else wait for natural timeout) mid-rescue, then an
   external UDP sender (globalping UDP traceroute to the live tuple if it
   accepts target ports; otherwise mark [OPERATOR] with any external UDP
   source, a phone hotspot works, and **do not fake it**): assert receipt on
   the shadow socket + forward to the LAN host in the daemon log.

> **G8 on-box record (2026-09-02, production daemon + `--observation`, rig =
> STUN from 192.168.21.1:41077 through the VM line).** The no-claims
> assertion passed (no claims without rig traffic; the relay's own tuple is
> filtered out by the one-holder rule). The identical-tuple assertion passed
> on all five runs: the observed flow's external tuple
> `37.228.213.83:59213` was read identically from the shadow's XOR-MAPPED
> and from host re-STUNs at T+2.5 min of host silence (it would die at the
> 5 to 10 s AFTR TTL without rescue); the claim held past the mirror's 15 s
> expiry with zero Stale exits once the fixes below were in. The pin-held
> assertion passed: the host-pin + self-pin elements
> live in `snat_map` for the claim's duration; the host's re-STUN rode the
> pin through the same inner tuple (proven by the identical mapping). The
> arrival leg passed end-to-end: a vdsl4-sourced probe to
> `37.228.213.83:59213` was delivered by the AFTR to the observed tuple on
> eth1 (`… .43999 > 192.168.0.21.41077`, captured). The FORWARD leg cannot be
> completed from the router's own address: the forward's IP_TRANSPARENT bind
> of the probe's source collides with the probe's own socket, the plan's
> "self-probe EADDRINUSE" artifact (rescue timing); uk/us are not vantages
> (standing rule).
> **[OPERATOR] per the plan: any genuinely external UDP sender (phone
> hotspot) to the live tuple completes the receipt-on-shadow +
> forward-to-host assertion.**
>
> **Measured integration fixes (all box-verified).**
> (a) fw4 srcnat is `priority srcnat` = 100, **not -100**, so the mirror
> observer needs priority above 100 (110 used; gating test PASSED, elements
> are post-NAT `(192.168.0.21, orig_sport)`: fw4's eth1 NAT is a fixed
> *port-preserving* snat, so R_nat = the flow's original source port).
> (b) **Self-pin.** While the observed conntrack entry lives, the kernel
> NAPTs the shadow's keepalives to an ephemeral port (measured 41077 to
> 1024), refreshing the WRONG mapping. An explicit (NAT, R_nat) to (NAT,
> R_nat) map element (the "self-pin") makes the keepalives egress under the
> observed tuple. The CT_DELETE alternative was bisected (`--ct-probe`, all
> family/nested/dir/zone encodings): EINVAL on this 6.12.35 build; no
> conntrack tool installable (no such apk package); recorded in `ct.rs`.
> (c) The mirror rule must use nft **`update`**, not `add`: `add` on an
> existing element does NOT refresh its timeout (element died every 15 s
> despite 2 s keepalive traffic, causing spurious Stale exits); `update` =
> insert-or-refresh (element pinned about 14 s forever).
> (d) The shadow sticks to one STUN server (rotate on failure only, relay
> pattern); concurrent flows from one source port get remapped too.
> (e) Input accepts at claim (B4-parallel): `ct state established` does not
> cover the promotion datagram (a genuinely NEW inbound flow), which fw4's
> input_wan would otherwise reject; the daemon installs `dslitepunch-<R>` per
> claim and removes it at exit.

9. **G9 Kani.** Predicate truth table, budget arithmetic, precedence (never
   captures a held tuple), exit state machine.
10. **G10 README.** What observation does (mapping never dies during
    lobby/loading silences; promotion keeps inbound alive) and does not
    (grade unaffected, D stays D; peer-side NAT expiry is not ours; hairpin
    out of scope). Switch benefit is a zero-config consequence of a generic
    policy; stated, never special-cased.

## §11 Quirk ledger (quirk, rule, where it lands)

| Quirk | Rule | Line |
|---|---|---|
| AFTR TTL 5 to 10 s, node-varying | 2 s staggered cadence; rescue threshold from the rescue-timing rig | B7/B6, G3 |
| EIM any-dst refresh | STUN rotation legal; majority vote on disagreement | B6, G3e |
| Random-high external ports, always | PREFER_FAILURE always fails; UPnP reports requested port; never emulate parity | D3, E3, §2 |
| XOR-MAPPED-ADDRESS is the only read | keepalive = discovery, one packet | §0, B |
| TCP unmapped: RST; UDP unmapped: silent (ICMP unknown) | dead-signal asymmetry documented; the unmapped-ICMP probe informs v2 | the ICMP probe |
| Rule install does not re-translate existing entries | pin at rescue-start to the entry's own R_nat; mechanism-B (capture-to-slot) deferred for this reason | G3c |
| Conntrack death stops DNAT | promotion = shadow socket receives, forwards in the v1 style | G4 |
| Lease-0 = infinite; lease-0 clients never refresh | self-refreshing max-life lease; respawn transparency load-bearing | E3, B8 |
| M-POST/MAN; paired TCP+UDP Adds | M-POST parity mandatory; TCP-fault vs no-op decided at E5, recorded | E3/E5 |
| NAT-PMP: no epoch field, +128, fixed 7200 | as specified | D5 |
| PCP retry-expected | drop-not-queue during in-flight discovery | D3 |
| IGD↔PCP lease collision | follow RFC 6886, don't invent | D6 |
| Hairpin unmeasured | boundary file, untestable-now | F3 |

## §12 Merge gates

| Phase | Criterion |
|---|---|
| all | Kani 0 failures (8 existing + per-phase new); router clean (pgrep/nft//tmp); tagged commit |
| A | A2 Type 2 + pcap evidence; A3 3× churn-republish-recover |
| B | B12 incl. a pcap identical to the v1 core's, kill-9 restore, holder-uniqueness proof |
| C | divergence fact recorded; TPROXY decision recorded; CDC, shadow-bind, and rescue-timing records (gate G) |
| D | D8 flagship: PCP answer matches the client's own STUN observation |
| E | upnpc verb set + M-POST parity + [OPERATOR] PS3 Type 2 |
| F | predictions + lobby result in boundary file |
| G | the four rig assertions (promotion may be [OPERATOR]-deferred if no external UDP sender) + G9 |

## §13 Global STOP conditions

A2 failure (forwarding model falsified; nothing proceeds until root-caused and
A1/A2 re-pass). Any Kani failure. Any console-shaped code. Any TCP grant path.
Any UPnP v2 construct. Any process split or async runtime. **Any state with
two holders on one inner tuple.** Any port-preservation emulation. Any
relay/backup path via uk/us hosts. (Removed: "Aya adopted without the
conntrack-CDC evidence of insufficiency": Aya is a first-class performance
tier per the G1 decision, not an escalation requiring justification.)

## §14 Open items carried forward (do not silently close)

TCP idle lifetime (the deferred test, gates TCP grants only). EIF-loss
detection v2 (informed by the unmapped-ICMP probe and the rescue sequence's
free per-flow tuples). Hairpin behavior (second VM vantage
required). ICMP-on-unmapped conclusion (the probe). Console behavior on
paired-Add TCP fault (E5 decision record). Per-slot IP divergence policy if
the divergence test says divergent. Whether the Switch's grading probe shares a socket with game
traffic (F residual).