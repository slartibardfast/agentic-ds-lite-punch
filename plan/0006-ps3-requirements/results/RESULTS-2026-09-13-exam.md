# RESULTS-2026-09-13: PSN examination (organic failure, OS update, NAT Type 2)

Status: findings recorded. The PS3's organic PSN failure is diagnosed as
console-side firmware staleness, resolved by the console OS update. The
network and this milestone's routing were exonerated. NAT Type 2 was
measured organically and is capture-attributed. The relay-attributed A2
run remains pending.

Redaction note: concrete addresses (console, relay, peers, the AFTR
tuple) are replaced with placeholders; the raw captures that retain them
stay on the router under /mnt/nvme/runs/2026-09-13-ps3-exam per the
results size policy.

## The organic failure

The console could not reach PSN before the update. The evidence ruling
out the network:

- The legacy console-facing zone is gone from the public DNS: no A and no
  AAAA records for api.playstation.net, us.playstation.net,
  epps.dl.playstation.net, or nss.cr.us.playstation.net, queried
  directly against a public resolver (8.8.8.8). www.playstation.com and
  the update zone survive; a control lookup (xboxlive.com) resolved.
- Both lines are healthy: the vdsl4 path returned HTTP 403 from
  auth.api.sonyentertainmentnetwork.com (TLS and TCP fine), and a br-lan
  source routed through the console's exact egress (policy rule 25000,
  table 1000) established a TCP connection to the same host on 443.

Conclusion: the stale firmware's stack depended on the decommissioned
legacy names (and their certificate era). A network-side fix does not
exist for that state; the console-side update does.

## The resolution

The console OS update downloaded over HTTP/80 from Akamai (the update
zone resolves: ps3.update.playstation.net via a192.h.akamai.net). After
the update, PSN works and the console's DNS namespace is current:
nsx.np.dl.playstation.net, video.dl.playstation.net,
*.np.community.playstation.net, auth.np.ac.playstation.net,
*.sonyentertainmentnetwork.com. None of the dead legacy names appear in
the console's queries.

## The NAT Type 2 result and its attribution

Captured during the operator's internet test (dual capture, br-lan and
eth1, ~240 s window then continued):

- NAT probe: PSN servers <psn-nat-a> and <psn-nat-b> on UDP 3478/3479
  echoed the console's datagrams from ephemeral source ports 53004 and
  53010. The console reported NAT Type 2.
- SSDP: the console M-SEARCHed 239.255.255.250:1900 and no IGD answered
  (consistent with the no-UPnP ground truth recorded at inspection).
  Type 2 therefore came from hole punching alone, with no IGD present.
- The relay was NOT in this path. It remained targeted at the test sink
  (<sink-endpoint>), and the fold map holds no <console-ip> entries.
  The probe's console-side ports are ephemeral, so even a retargeted
  single-target relay at 3478 could not have carried the probe's inbound
  echoes (the pin cannot demux arbitrary console ports).

Attribution verdict per #a2-verdict: this Type 2 is organic, not
relay-fold-attributed. It validates that the line alone composes to
Type 2 without IGD (phase-E relevance: IGD absence did not block a
Type 2 reading), but it does not sign the relay's acceptance.

## MW2 multiplayer session (2026-09-13)

The operator ran a Modern Warfare 2 session while the capture continued.
The in-game NAT indicator reported Open. The capture shows the organic
path carrying actual gameplay: UDP game data on 3074 both directions with
the CoD server ranges (<cod-backend>:3074, <cod-peer-a>:3074,
<cod-peer-b>:3074), the console's own game socket bound on 3074, inbound
datagrams from a remote reaching the console's 3074 (<game-host> to
<console-ip>:3074), TCP 3074 to a CoD backend, and service traffic
(<psn-service>:5223). Combined with the PSN Type 2, this is a second,
gameplay-level NAT classification (Open) on the organic path, with no
relay and no IGD in the path.

## Carried items

- The relay-attributed A2 run: retarget the relay to the console and
  re-run the connection test under capture, then check whether the
  relay's dynamic fold absorbs the console's probe ports (egress as
  <pin-endpoint>) and adjudicate the gate on that evidence.
- The routing idiom swap: replace the direct policy rule 25000 with a
  pbr-package policy in the box's PBR config after the acceptance run.
- The capture ran continuously through the update and remains live while
  the console is active.