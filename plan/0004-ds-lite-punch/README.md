# Milestone: ds-lite-punch, a CGNAT-aware UDP relay for the Virgin Media line

**Status:** The v1 core is built, deployed, and formally verified
(2026-08-29); multi-instance is built and its CLI contract is tested; the UPnP
control plane this milestone named is delivered and exceeded by plan/0007 and
plan/0008. Crate in the ds-lite-punch component (software/ds-lite-punch);
musl-static binary under procd on the router that holds a live CGNAT mapping
and forwards inbound UDP to a br-lan target with source preserved.
The two v1 acceptance items are reconciled rather than outstanding (one closed
by reframing, one run with a named remainder), see *Where we stand*. Ground truth from the 2026-08-28/29 experiments:
see `MEMORY.md` "UDP hole punching works" and "CGNAT UDP timeout measured".

## What this is

A single-binary Rust daemon on the router that makes UDP services behind br-lan
reachable from the internet through the VM Ireland ds-lite CGNAT, with zero ISP
cooperation. It exists because the AFTR's UDP idle timeout is (5,10) s,
node-dependent, an order of magnitude under RFC 6888's 120 s floor, and Virgin
will not change it. The relay is built around that number, not in spite of it.

```
internet peer       (AFTR CGNAT, EIM+EIF, measured)
  UDP toward PUB_IP:EXT_PORT
softwire via Hub 6 (B4)
router eth1         ds-lite-punch socket S on 192.168.0.21:R
  console/service   192.168.21.x:C (nft SNAT sends its replies back out via
  the (192.168.0.21:R) tuple)
```

Two jobs, one process. Job one: keep the mapping alive and observe it, the
STUN loop. Job two: move datagrams with endpoint consistency.

## Port detection in practice (the core question)

The relay learns its external port the same way every cycle: STUN
self-discovery on the forwarding socket itself; it asks the CGNAT and
believes the answer.

1. **One socket, one mapping.** S is bound to (192.168.0.21, R). Keepalives
   and forwarded traffic all egress S, so there is exactly one CGNAT mapping
   that matters, and STUN observes exactly that mapping.
2. **Keepalive equals discovery.** Every 2 s S sends a STUN Binding Request
   (RFC 5389) to a server from a rotation list (`stun.l.google.com:19302`,
   `stun.cloudflare.com:3478`, plus fallbacks). The request refreshes the
   mapping; the response reports it. One packet, both jobs.
3. **Parse.** Magic cookie `0x2112A442`, attribute `0x0020`
   XOR-MAPPED-ADDRESS (fallback `0x0001`), unmask port with `0x2112`, address
   with the cookie. About 80 lines, no crate.
4. **Compare, three states.**
   - Same tuple: healthy, no action.
   - Different tuple: churn event. The mapping died and was re-created, or the
     pool/port-block rotated. Update state, re-publish, log. Churn during
     steady 2 s keepalives should be near zero; if it is not, raise the cadence
     or suspect packet loss.
   - N consecutive STUN timeouts: blind. Rotate to the next STUN server.
     Refresh still works while blind, any outbound UDP refreshes the mapping;
     STUN is only needed for observation. Keep sending.
5. **Demux on receive.** A datagram from a known STUN-server IP that parses as
   a STUN response goes to the observation path. Everything else goes to the
   forwarding path. Anti-spoof is pragmatic: accept STUN only from IPs we
   actually sent requests to in the last few seconds (STUN itself is
   unauthenticated).
6. **Startup.** Bind S, first STUN round, first tuple, publish, then open
   forwarding. No forwarding before the first tuple exists.

Cadence math: worst-case node timeout about 5 s, so a 2 s keepalive; STUN RTT
expected under 300 ms; a STUN server is declared dead after 3 silent cycles
(about 6 s) and rotated. Mapping declared healthy if a response arrived within
the last 3 cycles.

The 2 s cadence is a deliberate divergence from RFC 6263's 15 s keepalive
envelope, and the Request message type is deliberate too: the RFC's guidance
assumes a minute-scale NAT binding lifetime, while the AFTR measures 5 to 10 s,
so 15 s would lose the mapping outright; and the exchange must be a Binding
Request rather than an Indication because tuple observation is a co-equal job.
Both whys, and the full standards sweep, are asserted in the implementation
brief §15.

## Forwarding model (endpoint consistency without TPROXY)

The CGNAT mapping is keyed to (192.168.0.21, R). Peers must see that tuple in
both directions.

- **Inbound.** A datagram on S from peer P is delivered at (console, C) with
  source address untouched. The console must see real peer addresses; its own
  NAT-traversal logic depends on it.
- **Outbound.** An nft rule does the consistency work, no userspace involved.

  ```
  nft add rule ... postrouting oifname eth1 udp saddr <console> sport C \
      snat to 192.168.0.21:R
  ```

  Console egress leaves as (192.168.0.21, R), the same CGNAT mapping (EIM).
  conntrack then carries established flows kernel-side in both directions;
  userspace S only handles first-contact inbound per peer. TPROXY is the
  fallback if the SNAT-to-a-bound-port trick misbehaves; it should not, NATted
  egress never touches S's socket.
- **Firewall.** Input accept for `udp dport R` on eth1 (learned the hard way:
  wan-input drops UDP to the router itself).

## Shape of the Rust binary

- The ds-lite-punch crate, single `main.rs` (400 to 600 lines). Edition 2021,
  tokio (rt/net/time/macros), **no TLS, no openssl**. musl-static
  x86_64-unknown-linux-musl, `opt-level="z"` plus `lto` (pal-run convention).
- Config via CLI flags/env: `--bind 192.168.0.21:R --target 192.168.21.x:C
  --stun a:1,b:2 --interval 2`. No config file parsing, keep it lean.
- Tasks: keepalive loop (timer + server rotation + tuple state) and recv loop
  (classify + forward); both loops share `Arc<UdpSocket>`; STUN responses
  cross via mpsc.
- Publication on tuple change: write `/run/ds-lite-punch/tuple`, emit a JSON
  line to stdout (journald), optional exec hook (DDNS update later).
- Logs state transitions only (churn, blind/recovered, tuple change), never
  per-keepalive, or the journal drowns.
- systemd unit, `Restart=always`. Router reboots recreate mappings; the daemon
  re-discovers and re-publishes within one cycle.

## Scope per phase: generic relay, PSN as the test app

ds-lite-punch is a workload-agnostic UDP exposure primitive: one instance
equals one CGNAT mapping equals one (local port, internal endpoint) pair. It
knows nothing about what it carries. PSN is the first acceptance workload, not
the product; the design must not grow PSN-shaped branches.

- **v1:** static configuration. Acceptance: two instances for PSN's UDP
  3478/3479 (console on br-lan), verified by external probes and a live PSN
  NAT-type test. The same config serves any UDP service.
- **v2:** dynamic mappings. A UPnP-IGD control plane that spawns/retires
  instances on `AddPortMapping` (consoles speak UPnP, not PCP; any UPnP
  client benefits equally). Advertises **IGDv1 / `WANIPConnection:1`**, see
  the control-plane section below; v2-only breaks old clients (PS3).
- **Explicitly out:** inbound TCP. The relay is UDP-only by decision, and the
  CGNAT-side justification for that changed on 2026-08-31: TCP EIF through
  the AFTR is now proven (see *Where we stand*), so "unreachable" is no longer
  why TCP is out. It is a product-scope choice, and a TCP variant would be
  net-new work that the CGNAT does not block. Hub-LAN placement NAK'd;
  everything stays behind our router.

## UPnP control plane (v2 phase)

The research below is what the facade was built from: the IGDv1-versus-v2
advertisement decision and the console-compatibility facts it rests on. It
landed as [plan/0007](../0007-igd-facade/README.md)'s facade and then as
[plan/0008](../0008-adaptive-igd-v1v2-facade/README.md)'s dual presentation
with the DeviceProtection boundary, so this section is the design record it
came from rather than work still to do.

**Version: advertise IGDv1 (`WANIPConnection:1`), deliberately.** Researched
2026-08-29; this is the decision behind "PS3 doesn't work with UPnP v2":

- The UPnP IGD **v2** spec REQUIRES an `InternetGatewayDevice:2` to advertise
  only `WANIPConnection:2`: "earlier versions must not be used if newer
  version exists." A `WANIPConnection:1` control point therefore cannot
  discover a v2-only gateway.
- The **PS3 (2006, UPnP 1.0 era) is a `WANIPConnection:1` client.** Against a
  v2-only IGD it finds no service it can use, no mappings, and UPnP "doesn't
  work." That is the failure David recalled.
- v2 also changes semantics v1 clients do not handle: lease-duration `0`
  becomes capped at 604800 s (no infinite UPnP mappings), access control
  restricts unauthenticated control points to their own IP plus ports at or
  above 1024, and several v1 error codes are deprecated.
- Corroboration: miniupnpd defaults to IGDv1; IGDv2 support exists but is not
  enabled by default because of interoperability issues. Wikipedia likewise
  notes v1 clients (Windows-XP-era, Xbox) break against v2-only gateways.

Decision: ds-lite-punch advertises `WANIPConnection:1` (IGDv1). It may add `:2`
alongside later, but `:1` must be present; v1-only is the safe default.

**Policy: always permit, report granted, let STUN reconcile.**
`AddPortMapping` is a void action, and the external port is unchoosable on
this CGNAT (AFTR assigns a random high port). The control plane accepts every
request, spawns the instance, and reports success. The client learns its real
external tuple via STUN discovery, which is what PSN actually uses for
connectivity (STUN/ICE candidates, not the UPnP-reported port). Residual risk
is narrow: a game doing naive fixed-port P2P ("connect to me at X") without a
STUN exchange, and that breaks whether we report truth or lie, because the
real port differs either way.

**Lease durations are advisory.** v1 clients often request lease `0` (static);
there are no static mappings on this CGNAT, they die in 5 to 10 s without
keepalive. ds-lite-punch accepts any lease value and keeps the instance alive
with its own 2 to 3 s keepalives regardless. Mapping lifetime is decoupled
from the requested lease.

**Multi-console.** One instance per (console, port); consoles are
distinguished by UPnP `InternalClient` source IP. Instances are independent
(distinct bind ports, distinct CGNAT tuples), sharing only the AFTR subscriber
port block (thousands of ports; `session-limit-per-prefix` configurable to
16384), fine for a handful of consoles. Keepalive load stays trivial, one
small STUN per instance per 2 to 3 s.

## Console traversal behavior (researched 2026-08-29)

ds-lite-punch is workload-agnostic, but the acceptance workloads have different
traversal models, and they set expectations for what the relay can and cannot
achieve on this CGNAT. Two measured CGNAT facts shape everything:

- **EIM + EIF for UDP** (full-cone-ish): consistent mapping, and unsolicited
  inbound to the mapped tuple is delivered.
- **No source-port preservation:** an internal source port P appears
  externally as a random high port (AFTR-chosen, from the port block).

**PlayStation 3 / 4 / 5: UPnP + STUN, not source-port-sensitive.**

- Ports: UDP 3478/3479 (core PSN); TCP 80/443/3478-3480 sign-in. Connectivity
  runs on STUN/ICE-discovered candidates, not fixed external ports.
- Model: console requests mappings via UPnP (IGD), then discovers its real
  external tuple via STUN and uses that, so the external port differing from
  the source port is fine.
- Result on our CGNAT: **NAT Type 2 is achievable.** EIF delivers inbound,
  STUN gives the console the correct tuple. This is the acceptance workload
  and it is expected to work.
- PS3 caveat: must advertise IGDv1 (previous section); the PS3 is a
  `WANIPConnection:1` client and cannot use a v2-only gateway.

**Nintendo Switch / Switch 2: wide UDP range, possibly source-port-sensitive.**

- Ports: effectively UDP 1-65535 plus TCP 6667/12400/28910/29900/29901. Too
  broad to forward statically; the console relies on UPnP/DMZ and is a
  UPnP/NAT-PMP client requesting wide high-port ranges.
- The open question (the "big if"): whether the Switch requires external-port
  equal to source-port, or whether it is satisfied by EIM/EIF plus STUN
  discovery like the PS5. The source-port-preservation claim traces to a
  single pfSense forum thread, whose "Static Port" fix may actually have been
  achieving endpoint independence (EIM) rather than literal port preservation,
  and our CGNAT already provides EIM+EIF.
- So the Switch's real NAT type on our CGNAT is unknown; measure on the
  hardware. Best case B (full-cone is the most permissive class); worst
  case D. A hardware test, not a design blocker, and not something the relay
  can change either way.
- Switch 2: same as Switch on IPv4 (per the same sources); may also use IPv6,
  which bypasses the v4 CGNAT entirely on our line (native IPv6).

**Design stance.** The relay provides EIM+EIF reachability plus keepalive and
knows nothing about the workload. STUN/UPnP-discovery consoles (PS3/4/5)
benefit fully. Any console that truly requires source-port preservation is
bounded by the AFTR (which we do not control), recorded as a known boundary
to resolve on hardware, not in the relay.

## Build plan

Target runs on the ImmortalWrt router itself; it must bind 192.168.0.21 (the
hub-LAN address) and is where the nft rules live. The Arch LXC container is on
br-lan, so it cannot host the relay. Deliverable is a musl-static Rust binary
cross-compiled (`x86_64-unknown-linux-musl`, `opt-level="z"`, `lto`), scp'd to
the router; no Rust toolchain needed on-box.

- **Toolchain smoke test.** Cross-compile a hello-world, run it on the
  router. Confirms musl-static runs on ImmortalWrt before writing real code.
- **v1 core, one static mapping.** STUN codec; keepalive/discovery loop
  (interval timer + server rotation + tuple state machine); recv/forward loop
  on the same socket (classify STUN-response vs data, forward data with source
  untouched); nft SNAT + input-accept; publish tuple file + JSON line.
  *Acceptance:* Globalping UDP to the published tuple from at least 4
  countries; pause keepalive about 10 s, expect churn detected + re-publish on
  resume.
- **Multi-instance.** Config-driven list of (bind-port, target); spawn
  the v1 core per instance; shared STUN-server rotation. *Acceptance:* two
  concurrent instances (PSN 3478/3479) probed independently.
- **UPnP-IGDv1 control plane.** SSDP responder +
  `WANIPConnection:1` SOAP (`AddPortMapping` / `DeletePortMapping` /
  `GetExternalIPAddress` / `GetSpecificPortMappingEntry`); always-permit;
  spawn/retire instances on demand; leases advisory. *Acceptance:* PS4/PS5
  UPnP request creates a live mapping; PS3 discovers the IGDv1 service.

Module sketch (single crate, edition 2021, tokio rt/net/time/macros, no TLS):

| Module | Responsibility | Approx lines |
|---|---|---|
| `stun.rs` | codec, magic cookie, XOR-MAPPED/MAPPED unmask, txn-id bookkeeping | 120 |
| `mapping.rs` | per-instance state machine (tuple, healthy/churn/blind), owns socket | 150 |
| `forward.rs` | recv classify (STUN vs data) + forward with source untouched | 80 |
| `publish.rs` | `/run/ds-lite-punch/tuple` + JSON log lines + optional exec hook | 40 |
| `upnp.rs` | SSDP + IGDv1 SOAP | 200 |
| `main.rs` | config, task wiring, supervision | 120 |

Config is CLI/env only (no file): `--bind 192.168.0.21:R --target
192.168.21.x:C --stun stun.l.google.com:19302,stun.cloudflare.com:3478
--interval 2`; multi-instance adds repeatable `--map R=C`; the UPnP control
plane adds `--upnp`.

Deployment: the router host is ImmortalWrt, so **procd, not systemd**. Ship a
`/etc/init.d/ds-lite-punch` procd script (`USE_PROCD=1`, `respawn`) plus
`/etc/ds-lite-punch.env` config; the script also idempotently inserts the
wan-zone input-accept rule for the bind port. nft SNAT for the console reply
path is console-specific config, added per target (the v1 core uses a sink
target; a real console adds the SNAT + `ip rule` for its egress).

## Where we stand

Ledger of what is actually built and signed off, against the build plan above.
Update it whenever a phase or an acceptance item moves.

| Phase | State | Evidence |
|---|---|---|
| Toolchain smoke test | **done** | musl-static x86_64 cross-compile runs on ImmortalWrt |
| v1 core, one static mapping | **built + deployed; acceptance reconciled below** | live tuple held stable under a 2 s keepalive (the line's tuple moves as the AFTR re-grants it: `37.228.213.83:59304` on 2026-09-17); external UDP probes from 4+ countries forwarded with peer source preserved |
| v1 formal verification | **done** | `cargo kani` 8 harnesses / 192 checks / 0 failures (about 21 s, Kani 0.67.0); 5 unit tests |
| Multi-instance | **built; contract tested** | the CLI carries a repeatable `--static-map R=ip:port` beside the legacy single-map pair, and the two are mutually exclusive by design; the test `static_map_parse_is_repeatable_and_exclusive` pins both forms and every malformed shape, at component `0cc2b04` where the suite stands at 120 tests. The deployed env file still uses the legacy pair, so N=1 in production |
| UPnP control plane | **delivered, and exceeded** | the IGDv1 facade landed in [plan/0007](../0007-igd-facade/README.md) and the v1/v2 facade with an enforced DeviceProtection surface in [plan/0008](../0008-adaptive-igd-v1v2-facade/README.md); the deployed artifact serves both faces on br-lan and its client matrix is receipted |
| TCP EIF characterization | **done (2026-08-31)** | TCP EIF through the AFTR is proven: 5/5 globalping HTTP-200 probes (DE/BR/JP/US/AU) forwarded to the mapped inner tuple via a dual-homed source-port oracle (our vdsl4 line as third party); 1:1 accept-log/IP cross-match; unmapped port RSTs on control. Full method in `MEMORY.md` (TCP EIF) |

Shipped with the v1 core: `stun.rs`, `mapping.rs`, `forward.rs`, `publish.rs`,
`main.rs` (about 640 KB stripped, tokio + libc, no TLS), plus
`deploy/ds-lite-punch.init` (procd, `respawn`), `deploy/ds-lite-punch.env`,
and `deploy/install.sh`.

> **2026-08-31: scope-relevant measurement (TCP EIF).** The one genuinely
> untested DS-Lite capability, whether the AFTR's endpoint-independent
> filtering also applies to TCP, was tested and **confirmed working**:
> with the client holding a mapping open (inner (192.168.0.21, 32014),
> external 37.228.213.83:59390), 5/5 globalping HTTP probes from five
> continents returned **HTTP 200** from the router-side twin listener, each
> response body echoing the exact post-AFTR source IP the AFTR forwarded,
> matching the twin's accept log 1:1. Control to an unmapped port in the
> same batch: 5/5 `ECONNREFUSED` (AFTR RST, unchanged behavior). So:
> **endpoint-independent filtering holds for TCP as well as UDP; a TCP
> mapping is reachable by any external address.** Consequence for scope: the
> relay stays UDP-only by decision, not by CGNAT limitation (see "Explicitly
> out"); a future TCP variant is unblocked at the AFTR level. Not re-measured:
> TCP mapping idle lifetime (UDP is 5 to 10 s, node-dependent; TCP untested).

### v1 acceptance, reconciled

Neither item is unsigned in the sense this section first meant, and both are
recorded here as they actually resolved.

- **The console PSN NAT-type test.** It is closed by reframing rather than by
  the test: the console's NAT probe uses ephemeral source ports a single-target
  pin cannot demux, so a fold-attributed PSN NAT type is impossible by
  construction (call/0014), and the console was then measured reaching PSN NAT
  Type 2 and MW2 NAT Open along the organic path, with the IGD facade
  deprioritised (plan/0006, call/0015). The forwarding model was not
  invalidated; the console story is "works alongside the relay" rather than
  "enabled by" it.
- **The keepalive-pause soak, discharged including the correction.** It ran on
  2026-09-13: first with the probes in flight (the pause grid `[5, 7, 10, 12,
  20, 30]` seconds, three repetitions per cell, relay stopped with `kill
  -STOP` and resumed with `-CONT`, detection, re-publish and recovery timed,
  a resurrection watch on the old tuple), which the relay survived in every
  cell; the analysis `ANALYSIS-2026-09-13.md` then showed that run was
  confounded, because the probes kept sending through the pause, and named the
  probe-quiet variant. **That variant then ran** as
  `RESULTS-2026-09-13-run3.md`: 18 of 18 cells with `pause-arr 0` (zero
  packets in any pause window, from any source), and the AFTR mapping
  **survived 30 seconds of total silence** with an unchanged tuple and a flat
  816 to 826 ms recovery.
  Two things follow. The survival is survival and not death plus re-issue, by
  the recovery-spread signature. And the run found the premise under question:
  the AFTR's UDP idle timeout on today's node **exceeds 30 seconds**, where the
  figure the relay was built around is 5 to 10 seconds, node-dependent. The
  carried item is therefore not an acceptance gap but a **longer-limit
  campaign** (60 s and 120 s silent windows, the probe-quiet design unchanged,
  RFC 6888's 120 s floor as the outer bound), the natural run 4, which is what
  would locate today's true timeout and reconcile it with the recorded one. The
  relay's own contract is unaffected either way: its 2 s cadence sits inside
  the floor whichever figure is right.

### What is deliberately not covered

- `forward.rs` is `libc` FFI (`IP_TRANSPARENT` bind + `sendto`) and is not
  Kani-modelable; `Instant`/`SystemTime` keep `note_response` out of the proofs
  too. Both stay covered by the on-box PoC and end-to-end probes.
- EIF loss remains invisible in v1 (external prober deferred to v2).
- The TPROXY-fallback question for the SNAT-to-bound-port trick is still open,
  see *Open questions*.

### Next step

Multi-instance itself is built (the repeatable `--static-map`), so the step
this section first named is done, and the pause acceptance is discharged
including its probe-quiet correction. What is left is one rig run rather than
a code change: the **longer-limit campaign** above, 60 s and 120 s silent
windows, which locates the AFTR's true idle timeout on today's node and
reconciles it with the 5 to 10 second figure this milestone was built around.
The operator's config may stay on the legacy single-map pair until a second
mapping is wanted, at which point the env file moves to `--static-map` lines
and nothing else changes.

## Failure modes

| Mode | Detection | Response |
|---|---|---|
| Tuple expiry (idle gap) | churn on next STUN response | auto re-publish; cadence already at most half the worst-case timeout |
| Pool IP / port-block rotation (CPE restart) | churn | same path; tuple publication tracks IP and port |
| STUN fleet outage | blind state | keepalives continue (any outbound UDP refreshes the tuple); observation degrades, tuple stays live |
| EIF switched off upstream | STUN stays healthy (responses are solicited) but unsolicited inbound stops | v1: invisible (noted); v2: external prober |
| Router reboot | procd `respawn` | a fresh tuple + re-publish in one cycle |

## Test rig

The acceptance paths that need a second host (A1 reply-path validation, the
A3 soak, the C6 echo half, the G8 forward leg) run from the experiment-only
LXCs defined and measured in [plan/0005](../0005-test-rig/README.md):
`dslp-probe` on the vdsl4 line, `dslp-sink` on the VM side. The self-probe
artifact is gone because the probe's sockets live in their own netns. The
soak runs end to end via that rig; no phone hotspot is needed.

## Testing

- Unit (example-based): STUN parser vectors; tuple-compare/churn state machine.
- **Formal (Kani, `cargo kani`):** bit-precise proofs over ALL inputs for the
  parser and the pure state machines. Parse never panics on any byte stream;
  (XOR-)MAPPED-ADDRESS decode is an exact inverse of encode; the Binding
  Request always has the RFC 5389 layout; a `Some` implies a genuine Binding
  Success Response; STUN-server rotation fires exactly at its threshold.
  `forward.rs` is `libc` FFI (not Kani-modelable) and stays covered by the
  on-box PoC + end-to-end probes. Unwind bounds must cover the 4-iteration XOR
  loop as well as the attribute loop; `#[kani::unwind]` is per-harness, not
  per-loop.
  The suite has grown well past the eight harnesses this section first
  recorded: it now stands at **40 harnesses across eight modules** (stun 6,
  slot 9, upnp 8, obs 5, vote 5, mapping 3, engine 2, tcpslot 2), and several
  of the later ones were restructured for tractability (the E7 parity proof,
  the TCP datapath's proofs). The full-suite re-derivation call/0019 asked for
  ran on the andromeda workstation at 34d48c1: 37 of 40 verdicts, 35
  successful, two failures classified as a CBMC artifact and an unwind bound
  rather than code defects, and three harnesses unresolved. This development
  host cannot run it (3843 MiB and four cores, operator-confirmed
  2026-09-17), and the proofs have since drifted from the tree: `src/slot.rs`
  gained three unproven lease-policy methods, and `src/upnp.rs` changed the
  code under proof for the WANIPConnection:2 surface.
  [plan/0007's Kani state record](../0007-igd-facade/results/RESULTS-2026-09-17-kani-state.md)
  holds the state and the steps that close it.
- On-router soak: **run**, not owed. The pause grid ran through
  [plan/0005](../0005-test-rig/README.md)'s rig, including the probe-quiet
  variant, and the mapping survived every silent window up to 30 seconds; the
  section on acceptance above states what it left.
- End-to-end: Globalping UDP to the published tuple from at least 4 countries
  **done**; the PSN NAT test on the console is closed by reframing, see above.

## Open questions

- EIF-loss detection (needs an external prober). The v2 facade landed without
  it, so the deferral this bullet first recorded did not discharge: the
  external prober is **carried past v2**, not delivered by it.
- Whether the SNAT-to-bound-port trick needs the TPROXY fallback on this
  kernel. **Answered:** the TCP datapath needed no TPROXY. A listener and an
  outbound mapping-holder cannot share one tuple under any plain-socket reuse
  combination, so the holder originates from an ephemeral local port that the
  relay's own `snat_map` folds to the slot's tuple (plan/0007's tcp-datapath
  task, `src/tcpslot.rs`); there is no TPROXY in the tree.
- PS3-specific acceptance: **closed.** The console reached PSN NAT Type 2 and
  MW2 NAT Open along the organic path, with the IGD facade deprioritised
  (plan/0006, call/0015).
- **Switch / Switch 2 NAT type on this CGNAT** (the "big if"): is it satisfied
  by EIM+EIF (NAT B) or does it truly need source-port preservation (NAT D)?
  Cannot be settled from sources; measure on the hardware via
  Settings, Internet, Test Connection, VM line vs vdsl4 as control. Does not
  block the build; it bounds expectations for one workload class.