# Milestone: test rig (ds-lite-punch acceptance harness)

**Status:** draft for operator review. The rig and the campaign tooling live
in this room (`config/`, `router/`, `probe/`, `sink/`); nothing is applied to
the router until the review checklist below is signed. The rig closes the A1,
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

`router/run-soak.py` drives, on the router: a 10 min baseline, a
10 min control, then the pause grid `[5, 7, 10, 12, 20, 30]` seconds, three
repetitions each, in seeded-random order, with 60 s settle between cells.
Each cell kills the mapping with `kill -STOP`, observes its death from the
probe's series on eth1, resumes with `-CONT`, and times detection,
republish, and recovery, with a 60 s resurrection watch on the old tuple to
count port reuse. `router/run-c3.py` measures the TCP idle-lifetime:
the sink holds a TCP mapping discovered by STUN-over-TCP, and the probe
connects at gaps 15 to 600 s, binary-searching the death point (the AFTR
RST is the dead signal). The full data dictionary is in the scripts'
invocation headers.

## Review checklist (operator sign-off)

1. br-lan assignments 192.168.21.11 and .12 are free at apply time.
2. Nothing contends for the fwmark nibble 0x10000/0xff0000 for the probe's
   traffic.
3. The masquerade scope (only the probe's UDP out pppoe-vdsl4) is the
   agreed vdsl4 blast radius.
4. The relay retarget window: one mapping reset at retarget, one at revert,
   plus one per campaign cell; the target is the router sink only.
5. /mnt/nvme has about 109 G free; each rootfs is about 1 G; raw runs go
   under /mnt/nvme/runs/.
6. hwaddrs 10:66:6a:00:00:11 and .12 are unique on br-lan.
7. All runtime scripts are idempotent; the rules and the retarget carry
   explicit revert instructions.

## Execution order

1. Create the containers with lxc-create (the archlinux download template).
2. Configure static IPs and hostnames inside the containers; copy the tools
   into the rootfs at /opt/dslp-test/.
3. Apply router/nft-bringup.sh; verify the probe egress reveals the
   public source 84.203.115.61 (STUN from dslp-probe).
4. Retarget the relay with router/relay-retarget.sh to-sink.
5. Run the campaign; pull the raw data; analyze; commit the dated results
   record and a MEMORY.md entry.

## Results home

Raw captures stay local under `results/` (gitignored). The derived
record commits as a dated annex in this room, the way plan/0004 embeds its
measured records.