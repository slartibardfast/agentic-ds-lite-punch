# Milestone: test rig (ds-lite-punch acceptance harness)

**Status:** draft for operator review. The rig and the campaign tooling live
flat in this room (lxc-*.conf, router-*.sh, router-run-*.py, probe-*.py,
sink-*.py, analyze.py, collect.sh); the review checklist below gates every
router-side change. Nothing has touched the router yet.
The rig closes the A1,
A3, C6, and G8 acceptance paths of plan/0004 that need a second host, and
hosts the TCP idle-lifetime measurement. Tooling migrates into the
ds-lite-punch component at crate migration (call/0012).

## What this milestone is

Two experiment-only Arch LXCs on the router, mirroring the established
container pattern (`/mnt/nvme/lxc`, `dir:` rootfs, `lxc-download` template,
veth on br-lan, IP set inside the container):

| Name | br-lan IPv4 | Role |
|---|---|---|
| dslp-probe | 192.168.21.11 | the external vantage: its UDP is fwmark-routed into the vdsl4 table and masqueraded to 84.203.115.61, so the AFTR sees a genuine off-subscriber source |
| dslp-sink | 192.168.21.12 | the relay forward target at UDP 40002; the A1 reply-path pin makes replies egress as the relay tuple (192.168.0.21, 40000) |

The production container api.d07yx58.net is untouched.

## Why the probe egresses vdsl4 by fwmark

The router selects egress by fwmark, not source address
(`ip rule 30000: from all fwmark 0x10000/0xff0000 lookup pbr_vdsl4`), and
84.203.115.61 is a /32 PPPoE address, so the probe cannot hold the public
address directly. One mangle rule marks UDP from the probe into the vdsl4
nibble; one postrouting rule masquerades that source on the vdsl4 uplink.
The probe's sockets live in its own netns, so the relay's `IP_TRANSPARENT`
forward bind of the peer source no longer collides: the G8.4 EADDRINUSE
artifact is gone, and the forward and reply legs both complete.

## The campaign

`router-run-soak.py` drives, on the router: a 10 min baseline, a
10 min control, then the pause grid `[5, 7, 10, 12, 20, 30]` seconds, three
repetitions each, in seeded-random order, with 60 s settle between cells.
Each cell kills the mapping with `kill -STOP`, observes its death from the
probe's series on eth1, resumes with `-CONT`, and times detection,
republish, and recovery, with a 60 s resurrection watch on the old tuple to
count port reuse. `router-run-c3.py` measures the TCP idle-lifetime:
the sink holds a TCP mapping discovered by STUN-over-TCP, and the probe
connects at gaps 15 to 600 s, binary-searching the death point (the AFTR
RST is the dead signal). The full data dictionary is in the scripts'
invocation headers.

## Review checklist (operator sign-off)

1. br-lan assignments 192.168.21.11 and .12: VERIFIED free, and both sit
   outside the DHCP pool (the range starts at .24), so no later lease
   conflict can claim them.
2. The probe's vdsl4 egress: NO MARK RULE NEEDED. The fw4 pbr_output chain
   matches specific sources and destinations; the probe matches nothing and
   already falls through to the main-table default via pppoe-vdsl4 (metric
   16). The bring-up adds no mark; it adds only the masquerade.
3. The masquerade: VERIFIED REQUIRED. The router has zero masquerade rules
   and br-lan v4 has no egress today (`ip route get` from a br-lan source
   is Network unreachable). The scoped rule (only the probe's UDP out
   pppoe-vdsl4) is load-bearing, not belt-and-braces; the bring-up verifies
   the probe's first probe on pppoe-vdsl4 with source 84.203.115.61.
4. The relay retarget: `service ... reload` is a procd restart (no reload
   service is defined); the mapping resets at retarget and revert by design
   and is itself a port-reuse observation. The deployed build carries a live
   observation engine (the ip dslp snat_map holds active pins at all times);
   the rig's test-table NAT must be verified on-wire against fw4's fixed
   eth1 snat and the live map, not assumed. The per-cell window is one
   mapping kill per cell; the target is the router sink only.
5. /mnt/nvme: VERIFIED, 109.1 G free; the production rootfs measures under
   2 G, two more are trivial. Raw runs go under /mnt/nvme/runs/.
6. hwaddrs 10:66:6a:00:00:11 and .12: VERIFIED unique on br-lan (no
   neighbor, no lease).
7. Idempotency and rollback: the scripts are add-or-ignore, and the revert
   is table-scoped; accepted.

Open amendments (new, from the 2026-09-12 review):

A. Reply leg, honest scope. The probe's public source is the router's own
   84.203.115.61, so a reply addressed to it terminates at the router: the
   echo as drafted turns around through the vdsl4 masquerade conntrack and
   never loops through the AFTR mapping. The rig proves the arrival and
   forward legs and the local echo RTT; the reply-through-mapping leg is
   cross-checked with an internet-side sender (Globalping), per plan/0004.
B. Input accept for the relay port. No `dport 40000` rule matched in the
   current ruleset text; inbound demonstrably works, so the accept exists in
   some form or under zone policy. Preflight confirms the relay port stays
   reachable before any cell runs.
C. Artifact binding. run.json records sha256 of /usr/bin/ds-lite-punch
   (currently 7127f4bf...), the init script, and the procd state, so results
   bind to the exact deployed build, whose behaviors (slot range, observer)
   supersede the v1-core milestone text.
D. Foreign-network reserve. The rig does not replace an external sender for
   the PSN-type test; that leg keeps Globalping and a real console.

## Wiring findings and RCA (2026-09-12/13)

Bring-up verified; the forward leg is blocked by a pre-socket kernel-path
consumption of NEW inbound UDP, reproduced with two relay builds. Evidence:

- Probe egress: masqueraded source 84.203.115.61 observed on pppoe-vdsl4
  toward the mapping; no fwmark rule needed (pbr_output matches nothing for
  the probe).
- AFTR arrival: probe datagrams delivered to the router, captured on eth1
  (src 84.203.115.61 to 192.168.0.21:40000) and counted at prerouting
  (38 hits in 8 s of 1 Hz probing, dbg-observed 34 in the prior run).
- Input stage: of those arrivals, only the established-return traffic
  (STUN responses) reaches the input chain and the relay socket (relay
  recv-log confirms 6 STUN receives, zero probe receives in the instrumented
  run); the bulk of NEW inbound datagrams are consumed between prerouting
  (priority -299) and the filter input chain.
- Counter stages, production active: prerouting dport 40000 = 38, input
  dport 40000 = 4, forward dport 40000 = 0. With the fresh binary the input
  count was 0. Both the deployed binary and a fresh musl build of the
  current source reproduce the black hole, and the source is exonerated:
  forward.rs is a plain transparent bind + sendto (replicated successfully
  by hand, including on the live NAT'd port), the recv loop has no guard,
  and the binary logs every forward failure (none logged).
- Exonerated mechanisms: reverse-path filtering (off); flow offload (not
  configured); shadow-socket theft (one holder on the tuple);
  dslitepunch-40000 accept placement (first rule of the input chain);
  dstnat rewrites (none for 40000); raw prerouting (empty);
  SO_REUSEADDR (irrelevant).

Conclusion: the relay is not the cause. NEW inbound UDP to the mapping is
consumed in the router's prerouting stage before the socket, so no forward
can occur regardless of binary or target. The soak therefore reads mapping
liveness from the eth1 capture (arrivals of the .61 to 40000 flow), which
is robust and measures the AFTR-side truth directly. The forward and reply
legs remain external-sender functions (the standards idiom: first-party
cannot be third-party), and the router's inbound-NEW path is recorded as an
independent open item (kernel/firewall stage accounting) for the crate
migration. Analysis markers derive from the per-cell eth1 pcap, not from
sink arrivals.

## Execution order

1. Create the containers with lxc-create (the archlinux download template).
2. Configure static IPs and hostnames inside the containers; copy the tools
   into the rootfs at /opt/dslp-test/.
3. Apply router-nft-bringup.sh; verify the probe egress reveals the
   public source 84.203.115.61 (STUN from dslp-probe).
4. Retarget the relay with router-relay-retarget.sh to-sink.
5. Run the campaign; pull the raw data; analyze; commit the dated results
   record and a MEMORY.md entry.

## Results home

Raw captures, logs, and the derived record land in `results/` and are
committed with the record (size policy in `results/README.md`). `collect.sh`
pulls a run from the router; `analyze.py` renders the per-cell table.