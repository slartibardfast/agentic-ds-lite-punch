# Milestone: igd facade (full UPnP/SSDP answering and honouring, TCP plus UDP)

**Status:** closed 2026-09-15. This milestone implemented plan/0004
phase E as full answering and honouring for both protocols: SSDP and
SOAP and GENA answered on br-lan, AddPortMapping granted for UDP and
TCP with real datapaths (the UDP-only constraint lifted by its own
gate), the two prerequisite measurements (the external-IP pinning
hunch; the C3 TCP idle-lifetime), and the crate migration into the
component repo. Every task is receipted done; the E6 console sign-off
completed the same day against the deployed 34d48c1 build
(results/RESULTS-2026-09-15-ps3-facade.md).

## What this milestone is

Plan/0004's phase E (IMPLEMENTATION.md, the UPnP facade entry) is
specified in detail and unbuilt. The operator's direction expands it: the
paired-TCP-Add quirk (the phase-E live decision point) resolves to a
real TCP datapath rather than the fault or the silent no-op, and the
facade answers fully for both protocols. The
relay's 2 s keepalive pinning the customer external IP is the operator's
hypothesis that the facade's GetExternalIPAddress honesty rests on, so
it is measured, not assumed.

Scope: the crate migration, the two measurements, the TCP datapath, the
facade (E1 to E8), and the closure. Out of scope: any PCP work beyond
what the facade's lease model shares (phase D stays unbuilt), any change
to the vdsl4 line, and any console-shaped code (the PS3 stays
the acceptance client, per plan/0004's constraints).

Grounding: the UDP-only constraint (plan/0004's binding-constraints
entry) names its own unlock: no TCP grants until the TCP idle-lifetime
test is measured. The crate has not landed in the component repo (call/0012 waives
reproducibility until it does); the source lives in the former
rope-agentic monorepo at tools/ds-lite-punch/. The C3 rig script
(plan/0005-test-rig/router-run-c3.py) exists unrun. Committed records
follow the standing address-redaction policy.

## Build sequence

Bands group the work: Measurements, the datapath, the facade, closure.
Every task carries verify and inputs; mechanical verifies re-run at the
gate, operator steps are attested operator.

### Migrate the crate into the component {#migrate-crate}

- verify: the worktree software/ds-lite-punch/main holds src/, deploy/
  and Cargo.toml at HEAD; cargo build --release
  --target x86_64-unknown-linux-musl succeeds; .host-software carries
  the recorded recipe and the new pin; host-lifecycle software --check
  passes; the repro waiver is retired by a decision
- inputs: the rope-agentic monorepo sources (tools/ds-lite-punch/),
  .host-software, the component README layout

Obtain the crate from the former monorepo, land it per the component
layout (src/, deploy/, Cargo.toml), record the musl toolchain and build
command in .host-software with the deps-bundle for offline
reproducibility, update the pin, retire the call/0012 waiver via a
decision, and verify the recipe end to end. This activates the
component's build lane.

### Measurements {#band-measurements}

- band

### Measure the external-IP pinning hunch {#pin-hunch}

- verify: the results record (results/<date>-pinning.md) carries the
  console-path XOR-MAPPED tuple and the keepalive-stop observations;
  the conclusion on the pinning hypothesis is stated
- inputs: the router line, the STUN echo mechanics of the A1 assertion,
  the relay tuple file

(a) Console-path XOR-MAPPED: a STUN Binding Request from the sink
container with a source port outside the fold map, routed through the
console's egress path (the from-address rule mechanism), records the
external tuple the console's class of traffic gets; the A1-observed pin
tuple is the comparison. (b) Keepalive-stop: stop the relay for windows
beyond the observed silent survival (45, 60, 90 s), observe whether the
customer session's public IP holds and which external port re-issues.
The result sizes GetExternalIPAddress honesty.

### Measure the TCP idle-lifetime (C3) {#c3-tcp}

- verify: the C3 run record with the binary-searched TCP mapping death
  point (the AFTR RST is the dead signal)
- inputs: plan/0005-test-rig/router-run-c3.py, the rig containers

Run the queued C3 measurement. This is the exact unlock the
UDP-only constraint names and sizes the TCP keepalive design.

Measured 2026-09-13 (results/RESULTS-2026-09-13-c3.md): the AFTR expires
an idle TCP mapping in (120, 300] s on this node and session (alive at
120 s, dead at 300 s, double-confirmed by the eth1 arrival capture and
the probe refused). The unlock is discharged; the datapath sizes its
re-establish-on-demand model to time, not to a UDP-style keepalive.

The C3 bring-up fixes (2026-09-13): the TCP-STUN holder server
(stun.l.google.com:3478 does not serve STUN over TCP); the holder's
egress pinned to the eth1 line with a wrong-line guard; the tuple read
from the holder stdout (the container cannot see the host runs dir);
the holder leak stopped in-container; and the alive signal scored from
the eth1 SYN arrival capture because the fw4 input chain drops forwarded
TCP NEW silently (the probe connect times out even while alive).

### The datapath {#band-datapath}

- band

### Design and implement the TCP datapath {#tcp-datapath}

- depends: #c3-tcp, #migrate-crate
- verify: a granted TCP slot forwards an external TCP connection to the
  internal client with data flowing both ways; cargo kani on the
  proxy/splice state machine; the constraint relaxation recorded
- inputs: the relay source, the C3 result

Lift the UDP-only constraint for TCP grants (recorded decision; the
constraint's own gate). Spike-verify on the line that the AFTR's
protocol dimension lets the same external port host a UDP mapping and a
TCP mapping to different inner tuples (the C3 rig's STUN-over-TCP shows
TCP mappings exist). Design: the relay terminates TCP on the pinned
external port and splices to the internal client; the idle/keepalive
model comes from C3.

### The facade {#band-facade}

- band

### Build the IGD facade per phase E {#facade}

- depends: #tcp-datapath, #pin-hunch
- verify: upnpc -l / -a / -d full verb set with captures; M-POST parity
  via curl with the MAN header; TCP and UDP Adds deliver data from an
  external vantage; GENA SUBSCRIBE and NOTIFY on churn; the unit suite
  passes (86); the facade Kani structural proofs deferred to a larger
  host (attested call/0019)
- inputs: the relay source, the phase E spec, the pinning result

E1 SSDP: join 239.255.255.250:1900 on br-lan with REUSEPORT, M-SEARCH
answers for the five v1 STs delayed randomly within MX, alive NOTIFY at
max-age/2, byebye on clean exit, stable UDN and bootid. E2 description
docs on --upnp-port (default 49152, br-lan only): IGD, WANDevice,
WANConnectionDevice, WANIPConnection:1 with the WANPPPConnection:1
alias, SCPDs cribbed from miniupnpd with attribution. E3 SOAP: POST and
M-POST/MAN (PS3-era stacks); GetExternalIPAddress returns the live STUN
tuple (never 0.0.0.0; pre-discovery returns the last known; per-slot
divergence falls back to slot-0 with the limitation documented);
AddPortMapping validates InternalClient on br-lan else InvalidArgs,
grants UDP and TCP with real datapaths, accepts and ignores RemoteHost
(EIF), treats lease 0 as max-life self-refresh, upserts on re-Add;
DeletePortMapping and GetSpecific/GetGeneric with stable enumeration
and fault codes; GetStatusInfo Connected; GetConnectionTypeInfo
IP_Routed. E4's paired-Add quirk resolves to the real TCP path. E5 GENA:
SUBSCRIBE/UNSUBSCRIBE, SID, initial NOTIFY, renewal, expiry at 2x
timeout, ExternalIPAddress events on churn, callback URLs on br-lan
only. E6 conformance and the operator PS3 test reusing the A2 chain
(Type 2 and Open must hold with the facade live): completed
2026-09-15 against the deployed 34d48c1 build
(results/RESULTS-2026-09-15-ps3-facade.md). E7 Kani: SSDP header
grammar, SOAP dispatch and fault paths, enumeration index math, SID/SEQ.
E8 hardening (size caps, LAN-only binds, no panics, capped logs) and the
documented-not-built paragraph (miniupnpd-WAN-deaf and lease file tail
escape).

### Closure {#band-closure}

- band

### Sign the milestone {#closure}

- depends: #facade
- verify: host-lifecycle tasks reports every task discharged; validate
  plan/ and call/ ok; the results records are redacted per the policy
- inputs: the milestone records, the decisions

Record the dated results (redacted), the decisions (the repro waiver
retirement, the TCP-grants relaxation), the MEMORY entries, and the
pushtail. The PS3 sign-off reuses the A2 chain with the facade live:
completed 2026-09-15 against the deployed 34d48c1 build, three-plus
games with the console's 3074/3658 grants honoured exactly as
requested and the mapping held unrotated through the session, peers
verified inbound on the packet trace
(results/RESULTS-2026-09-15-ps3-facade.md).

## Keepalive floor (design cost, measured)

The STUN keepalive that holds AFTR mappings is a bare 20-byte binding
request (stun.rs, zero attributes) plus the server's response (~55 B
nominal). At the 2 s deploy interval per slot, three armed slots carry
~8-12 MB per 24 h on the line, independent of user traffic (roughly
1 kbit/s; a rounding error against the line rate, and linearly smaller
at a longer --interval). The 2026-09-15 hold census (one day of daemon
log) showed zero tuple rotations across ~60 slot-hours while armed; the
single rotation observed corresponded to the one unarmed window (a slot
left without keepalive for about 9 minutes), which bounds the AFTR's
idle reaping on this session to under that.

## Teardown behaviour (observed: partial release on power-off)

The PS3 DOES send a DeletePortMapping at power-off: observed 2026-09-15
20:22:44, the facade honoured it and released the 3658 grant cleanly
(entry removed, slot socket released, keepalive stopped; the live
teardown path worked end to end). The cleanup is partial: the same
shutdown left the console's other grant (3074) armed, and a client
that vanishes without deleting (unplug, network loss) leaves its
grants entirely: infinite leases, no liveness detection, leases.tsv
restore. A grant is otherwise released by an explicit Delete, a
re-Add from the same client with a changed internal tuple (the replace
path), or the operator. Decision (2026-09-15): the granted lease
appears infinite (U32_MAX on the wire and in the index) while the
effective lifetime is managed underneath by the slot machinery: the
active hold (2 s keepalive, tuple watch, churn lines), the replace
path, the Delete path, the operator, and the slot-pool caps (32 slots,
16 per client). No expiry countdown churns a live tuple, and a
released mapping is not preservable on this line (re-arm gets a new
AFTR port, observed on the one unarmed slot). The appearing-infinite
value is not a permanence promise; the conservation levers remain
behind it. The IGD:2 lease guidance (max 604800 s, static via UPnP
discouraged) addresses passive mappings; this relay's active hold
supersedes it.

## Verification

- cargo build (musl) and the cargo kani suites (STUN codec, slot and
  holder invariants, SOAP dispatch, SSDP grammar, the TCP splice state
  machine).
- The rig measurements recorded (pinning, C3); external-vantage
  datapath tests for UDP and TCP Adds (vdsl4-oracle self-sourced plus
  captures; the console session as operator acceptance).
- upnpc full verb set, M-POST parity; the PS3 re-test held Type 2 and
  Open with the facade live (completed 2026-09-15,
  results/RESULTS-2026-09-15-ps3-facade.md).
- host-lifecycle tasks fully discharged; validate plan/ and validate
  call/ ok; software --check ok at the new pin.

## Results home

Records land under results/ in this room, committed with the records and
redacted per the standing policy. Raw data stays on the router.