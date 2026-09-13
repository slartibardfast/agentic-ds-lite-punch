# Milestone: PS3 requirements operation (A2 console acceptance)

**Status:** prepared; operator execution pending. The router ground truth
is inspected, the open decisions are settled (call/0013 for the egress
scope; see the settled section below), and the build sequence is ready.
The console steps need the PS3 on br-lan and hands-on access to its PSN
connection test. Nothing has been changed on the router yet beyond the
inspection recorded below.

## What this milestone is

This milestone operationalizes the PS3's requirements on the ds-lite
line: a real console on br-lan, the router reconfigured to serve it
through the relay pin, the PSN connection test run with captures both
sides, and the A2 acceptance of plan/0004 signed or failed. The verdict
also decides whether the phase E UPnP IGD facade is priority.

Plan/0004's A2 item ("PSN NAT test, OPERATOR") is the last unsigned v1
acceptance. The test rig's amendment D (plan/0005 README) states it
explicitly: the rig does not replace an external sender for the PSN-type
test, and that leg keeps "Globalping and a real console". The Globalping
half was covered by the A1 reply-path assertion (sink-stun MATCH,
RESULTS-2026-09-13-A1). This milestone is the real-console half.

Scope: the router changes (a DHCP reservation, one policy-route rule, one
relay retarget), the capture and the console run, the A2 gate, and the
phase-E priority decision. Out of scope: any UPnP/IGD implementation
(phase E is decided here, not built), any relay binary change (the
deployed artifact is the acceptance target), and any change to the
vdsl4 line (it stays the probe/oracle path only).

## Router ground truth (inspected 2026-09-13)

- No UPnP daemon: no miniupnpd/upnpd process, no uci upnpd config.
  Nothing on br-lan answers SSDP 239.255.255.250:1900. The console's IGD
  probe finds no device, which is the correct interim: a present-but-
  impotent IGD can force a strict/Type-3 reading in some consoles;
  absence forces the hole-punch path, exactly what A2 measures.
- The VM hub's own IGD (if any) lives on eth1/192.168.0.0/24. SSDP
  multicast stays inside br-lan's L2 domain and is never routed, so it is
  invisible to the console. Nothing to pause there either.
- Default route: `default via 83.147.162.174 dev pppoe-vdsl4` (metric 16)
  wins; `default via 192.168.0.1 dev eth1` (metric 128) is the fallback.
  Console traffic to PSN would egress vdsl4 as 84.203.115.61 and never
  see the AFTR or the pin. The console must be steered to eth1 by its own
  rule. The relay's two STUN host routes (74.125.250.129, 162.159.207.0)
  show the eth1-pinning idiom but cover fixed IPs only, not a service.
- Forwarding: `forward_lan` accepts br-lan to wan; the eth1 input chain
  accepts udp dport 40000 (the pin). No firewall change is needed.
- Reflection DNATs (yarn 443/80, surface-rdp 63389/63390) and the pbr
  vbings (us saddr 192.168.21.73 and .152/29; uk daddr ranges) match
  neither an untagged console nor PSN ports. No interference.
- DHCP pool: 192.168.21.24 to .142; existing reservations at .145 and
  .152 follow the dhcp.@host pattern with a tag. A console reservation
  slots into the same pattern.
- The relay (pid at inspection: 26152, artifact sha
  7127f4bfd296e5241648b02c96e66180ab75789169140c061fd7976225ee811a)
  still targets the test sink, `--target 192.168.21.12:40002`. Its live
  fold map (table ip dslp) holds the sink entry
  `192.168.21.12 . 40002 : 192.168.0.21 . 40000` plus a router-self
  entry. `--max-maps-per-client 16` and the slot range already cover the
  console's needs.

## Build sequence

Every task below carries its verify and inputs; the mechanical verifies
re-run at the gate, the operator ones are `attested operator` records.

### Reserve the console's DHCP address {#reserve-console}

- verify: uci show dhcp lists the host entry and the console holds the
  reserved IP (odhcpd lease line, ping from the router)
- inputs: /etc/config/dhcp

Add dhcp.@host for the console MAC to a fixed br-lan IP (outside the
dynamic pool, matching the .145/.152 pattern), commit, restart dnsmasq,
confirm the lease before the routing change.

### Route the console through the Virgin line {#console-via-eth1}

- depends: #reserve-console
- verify: the pbr rule for the console saddr is in nft list ruleset;
  from the router, `ip route get <console-ip>` resolves out eth1/192.168.0.1;
  an eth1 capture shows console egress within a minute
- inputs: /etc/config/network, the nft pbr chains and the ip rule tables,
  the bring-up script (extends router-nft-bringup.sh)

Follow the existing fwmark idiom (saddr goto a mark chain, marked lookup
table) with a small table whose default is via 192.168.0.1 dev eth1. This
is the load-bearing change: without it the console rides the vdsl4
default and the relay line sees nothing.

### Retarget the relay to the console {#retarget-relay}

- depends: #console-via-eth1
- verify: relay cmdline shows the console target; nft list table ip dslp
  gains `console . 3478 : 192.168.0.21 . 40000` and the 3479 twin
- inputs: /etc/init.d/ds-lite-punch (the retarget script extends
  router-relay-retarget.sh)

Re-point the deployed relay from the test sink to the console's PSN UDP
ports. The v1 acceptance form is two instances (or two slots) for
3478/3479. The mapping resets at retarget by design, which is itself a
port-reuse observation; the pin accept rule and accept_local=1 must be
untouched.

### Run the console connection test with both sides captured {#a2-run}

- depends: #retarget-relay
- verify: attested operator (the console's PSN connection test / NAT type
  result recorded; eth1 and br-lan pcaps archived)
- inputs: the two pcaps, the console's reported NAT type

On the console, run the PSN network / NAT type check. Simultaneously
tcpdump eth1 (both directions on port 40000) and br-lan (the console's
flows), following the 0005 capture conventions. Record the console's
reported type verbatim.

### Adjudicate the A2 gate {#a2-verdict}

- depends: #a2-run
- verify: attested operator; the capture evidence must show the egress
  folded as (192.168.0.21, 40000) and inbound appointments on the pin
  forwarded with the true peer source
- inputs: the pcaps

The verdict must first attribute the console's NAT-probe flow: did the
probe ride the fold (alone, one source port on the pin) or the hub's
separate NAT (any other egress)? PSN's reported type reflects whichever
path the probe took, so the verdict names it explicitly. PASS = NAT
Type 2 on a fold-attributed probe AND the two capture conditions. A type
reading that came from hub-NAT egress does not sign the relay's
acceptance; it is evidence for the phase-E question instead. FAIL = the
forwarding model is falsified, STOP everything, per the plan/0004 A2
gate. Either way, write the dated result record and a MEMORY entry.

### Decide phase-E priority from the verdict {#igd-decision}

- depends: #a2-verdict
- verify: attested call/NNNN (this milestone's decision in call/)
- inputs: the verdict record

Type 2 through pure hole-punch with no IGD present means the UPnP IGDv1
facade (plan/0004 phase E) is not the console's blocker and can stay
behind the other v2 work. A strict or flaky result makes phase E the
priority. Record the decision in call/ (a software-scoped decision, not
a methodology one).

## Review checklist (operator sign-off)

1. The console's reservation IP is free and outside the dynamic pool.
2. No UPnP daemon on br-lan at run time (re-verify, absent at inspection).
3. After retarget, the fold map holds the console entries and no stray
   sink entry survives the run.
4. The eth1 pin accept and accept_local=1 are untouched by the retarget.
5. Rollback path: delete the console pbr rule, retarget back to the test
   sink. The mapping resets by design; one port-reuse observation.
6. The deploy environment reverts to the test sink when the milestone
   closes, unless the console ownership is handed to the operator.

## Settled decisions

- Egress scope: the console's whole traffic routes via eth1, one pbr
  rule keyed on the reserved address (call/0013). The vdsl4 line stays
  probe/oracle only.
- Relay target pairing: PSN UDP 3478/3479 is the initial target. The
  pairing is confirmed live during #a2-run by observing the fold map
  (nft list table ip dslp) for the console's actually-folding source
  ports, and the observed pairing lands in the run record. Nothing past
  the run is hardcoded on it.
- IGD absence: the interim stands, no IGD on br-lan and the AFTR offers
  no PCP/UPnP (call/0011). #igd-decision records the phase-E priority
  from the A2 verdict; this milestone does not reopen it.

## Results home

Raw captures and the dated record land in this room under `results/` and
are committed with the record (size policy as in plan/0005). collect via
the 0005 collect.sh pattern; commit the plan change and a MEMORY entry
immediately, per the audited-plans and append-only-memory rules.