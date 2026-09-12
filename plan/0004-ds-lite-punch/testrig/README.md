# Test rig: bring-up and measurement campaign (review package)

Status: draft for operator review. Apply nothing to the router until the
review checklist at the bottom is signed. This tooling migrates into the
ds-lite-punch component repo at crate migration (call/0012); until then it
lives here, versioned with the plan.

## What this stands up

Two experiment-only Arch LXCs on the router, mirroring the established
pattern (`/mnt/nvme/lxc`, `dir:` rootfs, `lxc-download` Arch template, veth
on br-lan, IP configured inside the container):

| Name | br-lan IPv4 | Role |
|---|---|---|
| dslp-probe | 192.168.21.11 | external vantage: its UDP is fwmark-routed to the vdsl4 table and masqueraded to 84.203.115.61, so the AFTR sees a genuine off-subscriber source |
| dslp-sink | 192.168.21.12 | relay forward target at UDP 40002; the A1 reply-path SNAT pin makes its replies egress as (192.168.0.21, 40000), the relay tuple |

The production container api.d07yx58.net is untouched.

## Why the probe egresses vdsl4 via fwmark

The router's policy routing selects by fwmark, not source address:
`ip rule 30000: from all fwmark 0x10000/0xff0000 lookup pbr_vdsl4`, and
84.203.115.61 is a /32 PPPoE, so the probe cannot hold the public address
directly. One mangle rule marks UDP from 192.168.21.11 into the vdsl4
nibble; one postrouting rule masquerades that source to 84.203.115.61. The
probe's sockets live in the container netns, so the relay's `IP_TRANSPARENT`
forward bind of the peer source no longer collides (the G8.4 EADDRINUSE
artifact is gone): the forward leg and the reply path both complete.

## The relay retarget

During the campaign `--target` points at 192.168.21.12:40002 (env edit +
procd reload). The retarget restarts the relay, which is itself one more
port-reuse observation (the AFTR re-issuing 59230, documented twice). The
revert restores `--target 192.168.21.1:40001` and drops the added rules.

## Measurement campaign

Driver `run-soak.py` (on the router): baseline 10 min, control 10 min, then
the soak matrix pause grid `[5, 7, 10, 12, 20, 30]` seconds x 3, randomized,
each with a 60 s settle. `kill -STOP`/`-CONT` on the relay pid; eth1
tcpdump and a 1 Hz tuple/process snapshot are the router timebase; the probe
runs a 1 Hz series against the old tuple through the pause (death marker),
then the new tuple after republish (recovery), with a 60 s resurrection
watch on the old port (port-reuse frequency). Full data dictionary per run
in `run-soak.py`. Phase C3 (TCP idle lifetime) is a separate driver:
dslp-sink discovers its TCP mapping via STUN-over-TCP and the probe
connects at idle gaps 15/30/60/120/300/600 s, binary-searching the death
point (AFTR RST is the dead signal).

## Review checklist (operator sign-off)

1. br-lan assignment: 192.168.21.11 / .12 confirmed free at apply time.
2. fwmark nibble 0x10000/0xff0000 is the vdsl4 selector and nothing else
   contends for it (mwan3-style marks absent for the probe's traffic).
3. The masquerade scope (only 192.168.21.11 UDP out pppoe-vdsl4) is the
   agreed blast radius for the vdsl4 line.
4. Retarget window: the relay's mapping resets once at retarget and once at
   revert; the run itself kills and recreates the mapping per cell.
5. /mnt/nvme has ~109 G free; each Arch rootfs is about 1 G; runs dir
   /mnt/nvme/runs/2026-09-12 holds raw captures.
6. hwaddrs: probe 10:66:6a:00:00:11, sink 10:66:6a:00:00:12, unique on br-lan.
7. All scripts are idempotent where applied at runtime; the rules and the
   retarget carry explicit revert instructions.