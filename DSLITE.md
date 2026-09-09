Let me think through this systematically. You've closed the obvious doors. Let me enumerate what remains in the full possibility space of DS-Lite, including truly fringe ideas, and evaluate each against your measured constraints.

**Your hard constraints:**
- F3896LG polices martian IPv6 sources on LAN (measured)
- No bridge mode (kills IPv4)
- No PCP, no UPnP-IGD on AFTR
- Single /128 binding, single CGNAT IPv4 identity
- OpenWrt is behind the hub, not beside it

Let me think about what DS-Lite actually exposes as attack surface:

1. **The AFTR itself** — it accepts IPv4-in-IPv6 from the bound /128. It performs NAT. It has a NAT table. It responds to the bound /128.

2. **The hub's DS-Lite client (B4)** — it encapsulates LAN-side IPv4 into IPv6 toward the AFTR. It decapsulates return traffic. It performs no NAT itself (that's the AFTR's job in pure DS-Lite). Wait — actually, does the F3896LG do NAT44 locally before DS-Lite encapsulation? In standard DS-Lite, the B4 does NOT NAT — it just tunnels. The AFTR does all NAT. But some implementations do NAT44 at the B4 as well (non-standard). If the hub does NAT44 before encapsulation, then the AFTR sees private sources and does a second NAT. If it doesn't, the AFTR sees the LAN private addresses directly.

3. **The inner IPv4 header** — the AFTR rewrites the source to the CGNAT address. But what about the *destination*? The AFTR must route inner IPv4 packets to the internet. What if we could influence the AFTR's routing of inner packets?

4. **The hub's own IPv4 stack** — the hub has a local IPv4 stack for management, TR-069, etc.

5. **Fragmentation** — IPv6 fragmentation of the encapsulated packet.

6. **The hub's firewall** — does it filter inner IPv4?

Let me think about truly fringe ideas:

**Idea 1: IPv6 Extension Header manipulation**
The AFTR validates outer IPv6 source. What if we send packets with a Routing Header (RH0 was deprecated, but RH2 exists for MIPv6) that causes the packet to appear to come from the bound /128 at the AFTR but actually originate from our OpenWrt? No — RH2 is only for Home Address destination option, and the AFTR would need to process it. Also, the hub polices at L2/L3 on the LAN, so the packet never leaves.

**Idea 2: Exploit the hub's own DS-Lite B4 as a proxy**
The hub's B4 encapsulates any IPv4 packet arriving on its LAN interfaces into the DS-Lite tunnel. If we can get the hub to encapsulate packets with specific inner IPv4 headers, we control the inner packet. The hub doesn't NAT (in pure DS-Lite), so the inner source would be whatever we send. But the AFTR will NAT the source anyway. The question is: can we control the inner *destination* and get a response back?

Wait — this is actually the key insight. In DS-Lite, the B4 (hub) is a dumb tunnel. It encapsulates ANY IPv4 packet from the LAN. The AFTR does NAT. So from OpenWrt, if we send a raw IPv4 packet with source = some private address, the hub will encapsulate it with outer src = bound /128, send to AFTR, AFTR NATs the source to CGNAT address, and forwards to the internet. Return traffic comes back to the AFTR, AFTR looks up NAT table, finds the binding (CGNAT:port → private_ip:port), decapsulates, sends back to the bound /128, hub decapsulates, delivers to LAN.

So actually... **the hub IS already proxying our IPv4 traffic through DS-Lite.** That's how DS-Lite works. The OpenWrt router behind the hub already gets IPv4 egress through the hub's B4. The problem is:
- No inbound (AFTR NAT blocks unsolicited inbound)
- Shared CGNAT identity (no unique public IPv4)
- Double NAT if OpenWrt also NATs

So the "fringe" question becomes: can we get inbound through the AFTR's NAT?

**Idea 3: NAT traversal via the AFTR**
- PCP: Not available (confirmed)
- UPnP IGD: Not available on AFTR (confirmed)
- NAT-PMP: Same as PCP essentially, not available
- STUN/TURN: Works for UDP hole-punching if the AFTR's NAT is endpoint-independent (cone NAT). If it's symmetric NAT, hole-punching fails.

This is actually worth testing! If the AFTR's NAT is endpoint-independent mapping (EIM) and endpoint-independent filtering (EIF), then UDP hole-punching works. Many CGNAT deployments use EIM/EIF for UDP to support VoIP and gaming.

**Idea 4: TCP hole-punching**
If the AFTR's NAT is EIM for TCP as well (less common but possible), TCP hole-punching is possible. This requires a rendezvous server.

**Idea 5: IPv6-based inbound to the OpenWrt directly**
Wait — the OpenWrt has its own IPv6 address (from the hub's PD or SLAAC). If the hub's IPv6 firewall allows inbound to the OpenWrt's IPv6 address, then you already have inbound IPv6. The question is whether the hub's IPv6 firewall blocks inbound.

Actually, this is probably already known. The user said "VM line = v6 inbound + egress-only v4 via the hub." So IPv6 inbound already works. The problem is specifically IPv4 inbound.

**Idea 6: Teredo / 6to4 / other transition mechanisms**
These give you IPv6 over IPv4, not IPv4 over IPv6. Wrong direction. Not useful.

**Idea 7: Use the hub's own IPv4 stack**
The hub has a management IPv4 address (the CGNAT address). Can we access services on the hub itself? The hub's web interface is on 192.168.0.1 or similar. This doesn't help with getting a public IPv4 endpoint.

**Idea 8: ICMP tricks**
Some CGNATs allow inbound ICMP echo if there's an existing outbound session. This is standard NAT behavior. Not useful for services.

**Idea 9: DNS-based inbound (e.g., DNS tunneling)**
You could run a DNS tunnel (iodine, dnscat2) through the DS-Lite path. This gives you a slow but functional inbound channel. The "inbound" is actually the DNS response to your outbound query, but with a persistent tunnel it acts like a bidirectional channel. This is a legitimate fringe option.

**Idea 10: Use a VPS as a relay**
You have VDSL4 for inbound. But if you want to use the VM line's CGNAT IPv4 for something specific, you could:
- OpenWrt initiates outbound connection to a VPS (through DS-Lite)
- VPS acts as a reverse proxy/relay
- External clients connect to VPS, VPS forwards through the persistent tunnel to OpenWrt

This is essentially a poor man's CGNAT bypass. The "inbound" is actually outbound-initiated from OpenWrt to the VPS, then the VPS relays.

**Idea 11: SCTP or other protocols**
Some CGNATs handle SCTP differently. Unlikely to help.

**Idea 12: IPv4-in-IPv6 direct to AFTR with crafted inner packets**
We can't spoof the outer /128 (measured). But what about sending IPv4-in-IPv6 to the AFTR with outer source = our own IPv6 address? The AFTR would reject it (wrong binding). Dead end.

**Idea 13: Exploit the hub's B4 to send crafted inner IPv4**
The hub encapsulates whatever IPv4 arrives on its LAN. What if we send IPv4 packets with source = 0.0.0.0 or source = the CGNAT address itself? The AFTR might handle these differently. Probably drops them, but worth testing.

**Idea 14: Fragment the outer IPv6 packet**
Send a fragmented IPv6 packet where the first fragment has the correct outer headers but the payload is crafted. The AFTR must reassemble. This is unlikely to bypass anything but is a fringe test.

**Idea 2 refined: The hub as an unwitting B4 proxy**
This is actually the most interesting fringe angle. The hub's B4 is already encapsulating our traffic. The question is whether we can influence what the AFTR does with the inner packets in a way that creates an inbound path.

If the AFTR supports **Endpoint-Independent Mapping (EIM)** for UDP:
1. OpenWrt sends UDP from port X to a rendezvous server
2. AFTR creates mapping: CGNAT:Y ↔ OpenWrt_private:X
3. Rendezvous server tells external peer "connect to CGNAT:Y"
4. External peer sends UDP to CGNAT:Y
5. AFTR looks up mapping, finds OpenWrt_private:X, encapsulates, sends to hub's /128
6. Hub decapsulates, delivers to OpenWrt

This is standard UDP hole-punching through CGNAT. The question is whether the AFTR's NAT is EIM or symmetric.

**How to test:**
```bash
# From OpenWrt, send UDP to two different servers on the same source port
# If both see the same mapped port, it's EIM
# If they see different mapped ports, it's symmetric
```

If EIM: UDP hole-punching works. You get inbound UDP.
If symmetric: No hole-punching possible.

For TCP: even with EIM mapping, TCP hole-punching requires simultaneous open, which is harder but possible with a rendezvous server.

**Idea 15: CGNAT port prediction**
If the AFTR uses sequential port allocation, you might be able to predict the next allocated port and pre-announce it to a peer. This is extremely fragile and unreliable.

**Idea 16: Abuse the hub's TR-069/CWMP session**
The hub maintains a TR-069 session with the ACS. This is an outbound HTTPS connection. Could you somehow inject data into this session? Extremely unlikely and would be detected.

**Idea 17: Multicast**
DS-Lite doesn't support multicast. Dead end.

**Idea 18: Use the hub as a SOCKS proxy**
The hub doesn't run a SOCKS proxy. Dead end.

**Idea 19: IPv6 rapid deployment (6rd)**
Wrong direction (IPv4 → IPv6, not IPv6 → IPv4). Dead end.

**Idea 20: LW4o6 (Lightweight 4over6)**
Similar to MAP-E, requires carrier provisioning. Not available. Dead end.

OK so let me organize the truly viable fringe ideas:

1. **NAT behavior characterization** (EIM/EIF testing) → determines if hole-punching is possible
2. **UDP hole-punching** (if EIM) → gives inbound UDP through CGNAT
3. **TCP hole-punching** (if EIM for TCP) → gives inbound TCP through CGNAT
4. **Persistent tunnel to VPS** → reliable inbound over the CGNAT path
5. **DNS tunneling** → slow but functional inbound
6. **Crafted inner IPv4 packets** → test AFTR behavior with unusual inner sources

Let me present these in a structured way, being honest about which are worth testing and which are long shots.

Actually, I want to reconsider one more thing. The user said "VM line = v6 inbound + egress-only v4 via the hub." This means IPv6 inbound already works to the OpenWrt. So the question is specifically: can we get IPv4 inbound through the CGNAT?

The most promising fringe ideas are:
1. NAT behavior testing (determines if hole-punching is viable)
2. Hole-punching (if NAT allows)
3. VPS relay tunnel (always works, just adds a hop)

Let me write this up properly.

Actually, I realize I should also consider:

**Idea 21: Can we get the hub to initiate a connection to our OpenWrt that we can piggyback on?**
The hub initiates TR-069 to the ACS. It also does DNS queries, NTP, etc. None of these are useful for us.

**Idea 22: Can we use the hub's DS-Lite B4 as a TCP proxy?**
If we could somehow get the hub to initiate a TCP connection through the DS-Lite tunnel to a specific destination, and then somehow redirect the response... No, this doesn't work. The hub's B4 is a dumb encapsulator.

**Idea 23: What about the AFTR's handling of ICMP?**
If we send ICMP echo request through the DS-Lite tunnel, the AFTR will NAT it and forward. The response comes back. This confirms the tunnel works but doesn't give us inbound.

**Idea 24: What about using the DS-Lite tunnel for something other than IPv4?**
The DS-Lite tunnel carries IPv4-in-IPv6 (protocol 4). The AFTR expects this. We can't send anything else through it.

OK, I think I have a comprehensive list. Let me write the response.

One more thought: **Idea 25: Can we influence the AFTR's NAT table via the hub's own traffic?**
The hub itself generates IPv4 traffic (TR-069, DNS, NTP, firmware updates). This traffic goes through the same DS-Lite tunnel and gets NATted by the AFTR. The AFTR's NAT table will have entries for the hub's own traffic. Could we somehow exploit these entries? For example, if the hub connects to a server we control, we know the CGNAT:port mapping. Could we then send traffic to that CGNAT:port from outside? Only if the AFTR's NAT filtering is endpoint-independent (EIF). If it is, then any external host can send to that CGNAT:port and it will be delivered to the hub. But we want it delivered to OpenWrt, not the hub. So this doesn't directly help unless we can somehow redirect on the hub (which we can't, it's locked down).

Wait — actually, if the AFTR's NAT is EIF, and the hub has an active connection to a server we control, we know the CGNAT:port. But the response would go to the hub's private IP, not OpenWrt's. So this is a dead end for reaching OpenWrt.

Unless... the hub does NAT44 before DS-Lite (non-standard). In that case, the hub's NAT table maps CGNAT:port → hub_private:port, and then the AFTR maps CGNAT:port → hub_private:port. This is double NAT. In this case, even if we could punch through the AFTR, we'd still need to punch through the hub's NAT. Since the hub is locked down, we can't configure port forwards. So double NAT makes hole-punching to OpenWrt impossible even with EIM/EIF on the AFTR.

But wait — in standard DS-Lite, the B4 does NOT do NAT. The B4 just encapsulates. So the AFTR sees the original private source (e.g., 192.168.0.x from OpenWrt). The AFTR's NAT table maps CGNAT:port → 192.168.0.x:port. Return traffic is decapsulated and sent to the hub, which delivers it to the correct LAN host based on the inner IPv4 destination.

If this is the case (standard DS-Lite, no NAT at B4), then hole-punching through the AFTR would deliver packets directly to OpenWrt's private IP. The hub just decapsulates and forwards based on inner destination. This would work!

But we need to verify: does the F3896LG do NAT44 before DS-Lite, or does it just encapsulate?

If it does NAT44 + DS-Lite (double NAT), then:
- AFTR NAT: CGNAT:Y → hub_lan_ip:Z (where hub_lan_ip is the hub's own LAN IP, e.g., 192.168.0.1)
- Hub NAT: hub_lan_ip:Z → openwrt_private:X
- Hole-punching through AFTR reaches the hub, but the hub's NAT doesn't know to forward to OpenWrt

If it does pure DSworks if the external peer is the same host OpenWrt contacted.
- **Address-and-port-dependent filtering (symmetric):** Only the exact external IP:port that OpenWrt sent to can send back. Hole-punching requires the external peer to be the exact host:port that OpenWrt contacted.

For UDP hole-punching with a rendezvous server:
- OpenWrt sends to rendezvous server (creates mapping)
- OpenWrt also sends to external peer's IP:port (creates a second mapping if symmetric, or reuses the same mapping if EIM)
- External peer sends back to CGNAT:port
- If EIF or address-dependent: works
- If symmetric: only works if external peer sends from the exact IP:port that OpenWrt sent to

So the key test is: **what type of NAT does the AFTR implement?**

This is testable! And it's the most promising fringe avenue.

Let me also think about one more thing:

**Idea 26: Can we use the hub's own outbound connections to create a "pinhole" that we can exploit?**
If the hub initiates a connection to a server we control (e.g., via TR-069, DNS, NTP, or firmware check), and the AFTR's NAT is EIF, then we know a CGNAT:port that maps to the hub. But the inner destination is the hub's own IP, not OpenWrt's. So we can reach the hub but not OpenWrt. Dead end for reaching OpenWrt.

Unless the hub forwards certain traffic to OpenWrt (e.g., if OpenWrt is the DMZ host). But the hub is locked down, so we can't configure DMZ. Dead end.

**Idea 27: Can we use ICMP error messages to create a mapping?**
Some NATs create mappings for ICMP error messages. For example, if OpenWrt sends a UDP packet to an external host, and the external host responds with ICMP Destination Unreachable, the NAT might create a mapping for the ICMP error. This is standard behavior but doesn't help with inbound.

OK, I think I've exhausted the fringe ideas. Let me organize the response.

The most promising fringe ideas, in order of likelihood of success:

1. **NAT behavior characterization + hole-punching** — Test if AFTR is EIM/EIF. If yes, UDP hole-punching gives inbound UDP. This is the single most promising avenue.

2. **Persistent outbound tunnel to a VPS** — Always works. OpenWrt initiates outbound TCP/UDP to a VPS through DS-Lite. VPS acts as reverse proxy. External clients connect to VPS, VPS forwards through tunnel to OpenWrt. This is reliable but adds latency and requires a VPS.

3. **DNS tunneling** — Slow but functional. Works through any NAT. Gives a bidirectional channel.

4. **Crafted inner IPv4 packets** — Test AFTR behavior with unusual inner sources (0.0.0.0, 255.255.255.255, the CGNAT address itself). Long shot but zero cost to test.

5. **IPv6 fragmentation of outer packet** — Test if AFTR handles fragmented outer IPv6 differently. Very long shot.

Let me write this up.

Actually, I want to reconsider the VPS relay idea more carefully. The user already has VDSL4 for inbound. So why would they want inbound through the VM line? Possible reasons:
- Redundancy
- Load balancing
- Specific use case that requires the VM line's IPv4 address
- The VM line has better bandwidth/latency for certain paths

If the goal is simply "get inbound IPv4 to OpenWrt," VDSL4 already solves it. The VM line's value is IPv6 inbound + egress IPv4. So the VPS relay on the VM line is only useful if there's a specific reason to need inbound on the VM line's CGNAT address.

But the user asked for "fringe ideas," so I should present all options.

Let me also think about whether there's a way to use the VM line's IPv6 for something creative:
- The OpenWrt has a public IPv6 address (from the hub's PD or SLAAC)
- IPv6 inbound already works
- Could we run a service on IPv6 and use a translation layer for IPv4 clients?
- For example: a VPS with both IPv4 and IPv6. IPv4 clients connect to VPS's IPv4. VPS forwards to OpenWrt's IPv6. This gives IPv4 clients access to OpenWrt services via the VM line's IPv6.
- This is essentially a NAT64/DNS64 setup, or just a simple proxy.
- This doesn't give OpenWrt a public IPv4, but it gives IPv4 clients access to OpenWrt services through the VM line.

This is actually a practical solution if the goal is "allow IPv4-only clients to reach OpenWrt services via the VM line."

OK, let me write the final response now. I'll organize it as a comprehensive exploration of the remaining possibility space.

Let me reconsider the structure. The user asked "is there any fringe ideas we could try?" They want me to think creatively but also honestly about what's left. I should:

1. Acknowledge what's been closed
2. Systematically explore what remains
3. Be honest about likelihood of success
4. Provide concrete test commands where possible

Let me write this up now.

I think the key insight I should lead with is: the DS-Lite B4 (hub) is a dumb tunnel. It encapsulates ANY IPv4 from the LAN. The AFTR does the NAT. So the question is really about the AFTR's NAT behavior. If we can characterize the NAT and find it's EIM/EIF, hole-punching is possible. This is the single most promising avenue.

Let me also think about whether there are any protocol-level tricks within the DS-Lite tunnel itself:

**Idea 28: Can we send IPv4 packets with destination = the CGNAT address through the tunnel?**
If OpenWrt sends an IPv4 packet with destination = CGNAT address (the address assigned by the AFTR), what happens? The hub encapsulates it, sends to AFTR. The AFTR sees inner destination = its own NAT address. It might:
- Drop it (most likely)
- Deliver it to itself (the AFTR's own stack)
- Try to NAT it (confusing)

This is a long shot but zero cost to test.

**Idea 29: Can we send IPv4 packets with source = the CGNAT address?**
If OpenWrt sends an IPv4 packet with source = CGNAT address, the hub encapsulates it. The AFTR sees inner source = CGNAT address. It might:
- Drop it (source is already the NAT'd address, confusing)
- Forward it without NAT (source is already "public")
- NAT it again (double NAT on the same address)

If the AFTR forwards it without NAT, then the response would come back to the CGNAT address, and the AFTR would need to figure out where to deliver it. This could create an interesting loop or bypass. Very speculative.

**Idea 30: Can we send IPv4 packets with source = 0.0.0.0?**
Some NATs handle 0.0.0.0 specially (e.g., for DHCP). The AFTR might drop it or handle it unexpectedly.

These are all "poke it with a stick" tests. Zero cost, low probability of success, but worth trying if you're being thorough.

OK, I think I have enough material. Let me write the response now.

Let me structure it as:

1. **The one promising avenue: NAT characterization + hole-punching**
2. **The always-works fallback: VPS relay**
3. **The creative IPv6 pivot: NAT64/proxy via IPv6**
4. **Zero-cost probes: crafted inner packets**
5. **The honest assessment**

This gives a clear hierarchy from most promising to least.

Let me write it up.

One more thought: I should also mention **CGNAT port range exhaustion as a side channel**. If we can exhaust the AFTR's port allocation for our CGNAT address, the AFTR might behave differently (e.g., allocate from a different range, or drop packets). This is not useful for inbound but could reveal information about the AFTR's implementation.

Actually, that's not really useful. Let me drop it.

Let me also think about **whether the AFTR might support PCP even though the hub doesn't expose it**. PCP is a protocol between the client and the NAT device. In DS-Lite, the PCP client would be the B4 (hub), and the PCP server would be the AFTR. If the AFTR supports PCP but the hub doesn't proxy it, we can't reach the AFTR's PCP server from behind the hub.

But wait — PCP packets are UDP to port 5351. If we send a UDP packet to port 5351 with destination = the AFTR's IPv6 address... no, that doesn't work because PCP in DS-Lite is supposed to go through the B4, which proxies it. The hub doesn't proxy PCP, so we can't reach the AFTR's PCP server.

Unless we send the PCP packet as the inner IPv4 payload of the DS-Lite tunnel. But the AFTR expects inner IPv4 to be internet-bound traffic, not PCP. The AFTR would try to NAT and forward it, not process it as PCP.

Actually, in RFC 6887 (PCP), for DS-Lite, the PCP client sends PCP requests to the B4's IPv4 address, and the B4 is supposed to proxy them to the AFTR. If the hub doesn't implement PCP proxying, we're stuck.

But what if we send a PCP request as a raw IPv4 packet with destination = some specific address that the AFTR recognizes as its PCP server? This is extremely speculative and unlikely to work.

OK, I think I've been thorough enough. Let me write the response.

Let me reconsider the structure one more time. I want to be honest and not overhype anything. The user is clearly technically sophisticated and has already closed most doors. I should:

1. Lead with the most promising idea (NAT characterization)
2. Be clear about what's testable and what's speculative
3. Provide concrete commands
4. End with an honest assessment

Here's my final structure:

**Tier 1: Testable and potentially viable**
- NAT behavior characterization (EIM/EIF/symmetric)
- UDP hole-punching (if EIM/EIF)
- TCP hole-punching (if EIM for TCP)

**Tier 2: Always works but adds infrastructure**
- VPS relay / reverse tunnel
- IPv6-to-IPv4 proxy (NAT64-style)

**Tier 3: Zero-cost probes (long shots)**
- Crafted inner IPv4 packets
- PCP directly to AFTR
- ICMP-based mapping

**Tier 4: Theoretical / likely impossible**
- IPv6 extension header tricks
- Fragmentation attacks on AFTR
- Hub TR-069 exploitation

Let me write this up now. I'll keep it concise but thorough.

Actually, I realize I should also consider: **what if the hub's DS-Lite implementation is non-standard in a way wP:port (if symmetric NAT, this creates a second mapping)
- External peer sends back

If the AFTR is EIM (endpoint-independent mapping):
- OpenWrt sends to rendezvous server → mapping CGNAT:Y ↔ 192.168.0.2:X
- OpenWrt sends to external peer → same mapping CGNAT:Y ↔ 192.168.0.2:X (same source port X, so same mapping)
- External peer sends to CGNAT:Y → AFTR finds mapping → delivers to OpenWrt ✅

If the AFTR is symmetric (endpoint-dependent mapping):
- OpenWrt sends to rendezvous server → mapping CGNAT:Y1 ↔ 192.168.0.2:X
- OpenWrt sends to external peer → mapping CGNAT:Y2 ↔ 192.168.0.2:X (different mapped port because different destination)
- External peer sends to CGNAT:Y1 → AFTR checks filtering → only allows 1.2.3.4:5000 (rendezvous server) → drops external peer's packet ❌
- External peer sends to CGNAT:Y2 → AFTR checks filtering → only allows external_peer:port → if external peer sends from the right port, it works ✅

So even with symmetric NAT, hole-punching can work if:
1. OpenWrt sends a UDP packet to the external peer's IP:port first (creates the mapping)
2. External peer sends back from the same IP:port

This is the standard UDP hole-punching technique. It works through symmetric NATs as long as both peers send to each other first.

The only case where it fails is if the AFTR uses address-and-port-dependent filtering AND the external peer can't send from the exact IP:port that OpenWrt sent to. But in practice, the external peer can always send from the same IP:port it received on.

So actually, **UDP hole-punching should work through any NAT type**, as long as:
1. Both peers know each other's mapped addresses (via rendezvous server)
2. Both peers send to each other before expecting incoming traffic
3. The NAT doesn't have a very short timeout

The main risk is that the AFTR has a very short UDP timeout (e.g., 30 seconds), which would require frequent keepalives.

For TCP hole-punching:
- Requires simultaneous open (both peers send SYN at the same time)
- Works through EIM NATs
- May not work through symmetric NATs (because the mapped port depends on the destination)
- Requires precise timing coordination via rendezvous server

So the recommendation is:
1. Test NAT type (EIM vs symmetric) using STUN or manual testing
2. If EIM: both UDP and TCP hole-punching are straightforward
3. If symmetric: UDP hole-punching still works (with the technique above), TCP hole-punching is harder but possible

This is actually quite promising! Let me write it up.

One more consideration: **does the hub's firewall block inbound IPv4 on the LAN?**
Even if the AFTR delivers the packet to the hub, the hub might have a firewall that blocks inbound IPv4 to LAN hosts. In standard DS-Lite, the B4 should deliver all decapsulated IPv4 to the LAN. But some hubs have additional firewall rules.

This is testable: if OpenWrt can receive responses to its own outbound connections (e.g., web browsing works), then the hub is delivering decapsulated IPv4 to the LAN. The question is whether it delivers unsolicited inbound (i.e., packets that don't match an existing connection from the LAN side).

If the hub has a stateful firewall that only allows established/related connections, then hole-punching won't work even if the AFTR allows it. But this is unlikely for a DS-Lite B4, because the whole point of DS-Lite is that the B4 is a dumb tunnel.

OK, I think I've been thorough enough. Let me write the response now. I'll focus on:

1. NAT characterization (the key test)
2. Hole-punching (the main opportunity)
3. VPS relay (the reliable fallback)
4. Zero-cost probes (long shots)

And I'll be honest about the likelihood of each.

Let me write it now. I'll aim for a comprehensive but focused response.

Actually, I want to reconsider one more time whether there's anything truly novel here that the user hasn't considered.

The user has:
- Measured martian filtering (spoofing impossible)
- Confirmed no MAP-E, no PCP, no UPnP
- Confirmed no bridge mode
- Confirmed single /128 binding

What they may NOT have tested:
- AFTR NAT type (EIM/EIF/symmetric)
- Whether hole-punching works through the AFTR
- Whether the hub's firewall blocks unsolicited inbound IPv4 on LAN

These are the key unknowns. Let me focus on these.

I'll also mention the VPS relay as a reliable fallback, and a few zero-cost probes.

OK, writing now.

Let me think about what tools to recommend for NAT characterization:
- `stun` client (e.g., `stunclient` from `stuntman`)
- Manual test: send UDP to two different servers on the same source port, compare mapped ports
- `natmap` or similar tools

For hole-punching:
- `pwnat` for UDP hole-punching without a rendezvous server
- Custom script with rendezvous server for TCP hole-punching
- `chisel` or `frp` for reverse tunneling (VPS relay approach)

Let me write the response now.

I think I should structure it as:

1. **The key unknown: AFTR NAT behavior** — this is the single most important thing to test
2. **If EIM/EIF: hole-punching** — concrete steps
3. **If symmetric: modified hole-punching** — still possible for UDP
4. **The reliable fallback: VPS relay** — always works
5. **Zero-cost probes** — long shots
6. **Honest assessment**

Let me write it.

I realize I've been overthinking this. Let me just write a clear, focused response.

The key insight is: **the DS-Lite B4 (hub) is a transparent tunnel. The AFTR is the only NAT. If we can characterize the AFTR's NAT behavior, we know whether hole-punching is possible.** This is the single most important test to run.

Let me write the response now.

I'll keep it focused and practical, with concrete commands and clear decision trees.

Here's my final plan:

1. **The untested variable: AFTR NAT type** — explain why this matters, how to test it
2. **Decision tree based on NAT type** — what's possible in each case
3. **Hole-punching implementation** — concrete steps for UDP and TCP
4. **VPS relay** — the reliable fallback
5. **Zero-cost probes** — crafted packets, PCP attempts
6. **Summary table**

Let me write it now. For real this time.

I need to be careful not to overstate the likelihood of success. The user is sophisticated and will see through hype. I should be honest: hole-punching through CGNAT is possible in theory, but many CGNAT deployments use symmetric NAT or have short timeouts that make it impractical. The VPS relay is the only guaranteed solution.

OK, writing now.

Let me think about the format. The user has been very structured in their responses. I should match that level of rigor. I'll use a clear structure with headers, concrete commands, and honest assessments.

Let me also think about what "fringe" means in this context. The user is asking for ideas that are outside the mainstream, that they might not have considered. So I should focus on:
- Things that are technically possible but unusual
- Things that require creative thinking
- Things that exploit specific properties of DS-Lite or CGNAT

The most "fringe" idea is probably: **using the AFTR's NAT as a rendezvous point for hole-punching.** This is not a standard use of DS-Lite, but it's technically possible if the NAT behavior allows it.

Another fringe idea: **using the hub's own outbound connections to infer the AFTR's NAT behavior.** For example, if we can observe the hub's DNS queries or NTP requests from the outside (by running a DNS/NTP server that the hub is configured to use), we can see what CGNAT:port the AFTR assigns. This tells us about the AFTR's port allocation strategy.

But wait, we can't control which DNS/NTP server the hub uses (it's locked down). So this is probably not feasi *outer* IPv6 layer (the tunnel) and the *provisioning* layer (what the carrier offers). There is one layer that hasn't been probed: **the AFTR's NAT behavior on the inner IPv4 plane.**

This is the key insight: in DS-Lite, the B4 (hub) is a transparent encapsulator. It does not NAT. The AFTR is the sole NAT device. The AFTR's NAT type determines whether hole-punching is possible.

### 1. The Critical Test: AFTR NAT Characterization

**Why it matters:**
- If the AFTR uses **Endpoint-Independent Mapping (EIM)** + **Endpoint-Independent Filtering (EIF)**: full UDP and TCP hole-punching is possible. Any external host can send to your mapped CGNAT:port.
- If the AFTR uses **EIM + Address-Dependent Filtering**: hole-punching works if the external peer is the same host you sent to.
- If the AFTR uses **Symmetric NAT** (Endpoint-Dependent Mapping): UDP hole-punching still works with the standard technique (both peers send first). TCP hole-punching is harder but possible.
- If the AFTR uses **Symmetric NAT + Address-and-Port-Dependent Filtering**: UDP hole-punching still works (both peers send to each other first). TCP hole-punching is very difficult.

**How to test:**

From OpenWrt, send UDP to two different STUN servers on the same source port:

```bash
# Install stun client
opkg install stunclient  # or use a static binary

# Test 1: Send to two different servers, same source port
stunclient stun.l.google.com --localport 5000
stunclient stun1.l.google.com --localport 5000

# If both report the same mapped port → EIM
# If they report different mapped ports → Symmetric
```

Or manually with `nc`:
```bash
# Send UDP to server A
echo -n "test" | nc -u -p 5000 1.2.3.4 5000 &
# Send UDP to server B (different IP, same source port)
echo -n "test" | nc -u -p 5000 5.6.7.8 5000 &
# Check what source port each server sees (you need a listener on both)
```

**What to look for:**
- Same mapped port for both destinations → EIM → hole-punching is easy
- Different mapped port per destination → Symmetric → hole-punching is harder but still possible for UDP

### 2. If EIM/EIF: UDP Hole-Punching

This gives you **inbound UDP** through the CGNAT.

**Architecture:**
```
External Peer → CGNAT:Y → AFTR → decapsulate → hub → OpenWrt (192.168.0.2:X)
```

**Implementation:**
1. OpenWrt sends UDP to a rendezvous server (creates NAT mapping at AFTR)
2. Rendezvous server records CGNAT:Y
3. Rendezvous server tells external peer "send to CGNAT:Y"
4. External peer sends UDP to CGNAT:Y
5. AFTR looks up mapping, decapsulates, delivers to OpenWrt

**Tools:**
- `pwnat` — UDP hole-punching without a rendezvous server (uses ICMP tricks)
- Custom rendezvous server + `socat` or `ncat`
- `chisel` over UDP (if you need TCP-like reliability)

**Limitations:**
- UDP only (unless TCP hole-punching also works)
- Requires keepalives if AFTR has short UDP timeout
- No inbound TCP unless the AFTR also supports EIM for TCP

### 3. If Symmetric: Modified UDP Hole-Punching

Even with symmetric NAT, UDP hole-punching works if both peers send to each other first:

1. OpenWrt sends UDP to external peer's IP:port (creates mapping CGNAT:Y2 ↔ peer:port)
2. External peer sends UDP to CGNAT:Y2 (AFTR allows because peer matches the mapping)
3. Bidirectional UDP established

**Requirement:** Both peers must know each other's addresses in advance (via rendezvous server or pre-arranged).

### 4. TCP Hole-Punching (Harder)

If the AFTR uses EIM for TCP:
- Simultaneous open: both peers send SYN at the same time
- Requires precise timing coordination via rendezvous server
- Tools: `punch` or custom implementation

If the AFTR uses symmetric NAT for TCP:
- Very difficult, often impractical
- The mapped port depends on the destination, so you can't predict it

### 5. The Reliable Fallback: VPS Relay

If hole-punching doesn't work (or is too fragile), the guaranteed solution is a VPS relay:

```
External Client → VPS (public IPv4) → tunnel → OpenWrt (via DS-Lite egress)
```

**Implementation:**
- OpenWrt initiates outbound TCP/UDP to VPS through DS-Lite
- VPS runs a reverse proxy (e.g., `nginx`, `caddy`, `frp`, `chisel`)
- External clients connect to VPS's public IPv4
- VPS forwards through the persistent tunnel to OpenWrt

**Tools:**
- `frp` (fast reverse proxy)
- `chisel` (TCP/UDP tunnel over HTTP)
- `bore` (simple TCP tunnel)
- `tailscale` or `zerotier` (if you want a mesh network)

**Advantages:**
- Always works regardless of NAT type
- Supports TCP and UDP
- Can expose multiple services
- Can add encryption

**Disadvantages:**
- Requires a VPS (cost)
- Adds latency (extra hop)
- All traffic transits the VPS

### 6. Zero-Cost Probes (Long Shots)

These are unlikely to work but cost nothing to test:

**a) Crafted inner IPv4 packets:**
```bash
# Send IPv4 with source = CGNAT address (might confuse AFTR)
hping3 -1 -a <CGNAT_IP> <AFTR_IP>  # Won't work directly, need to inject into DS-Lite tunnel

# Send IPv4 with source = 0.0.0.0
# Send IPv4 with destination = CGNAT address
```
These would need to be injected as raw IPv4 on the LAN, letting the hub encapsulate them. The AFTR's reaction is unpredictable.

**b) PCP directly to AFTR:**
```bash
# Try sending PCP request as inner IPv4 UDP to port 5351
# Destination: AFTR's IPv4 address (if it has one) or a well-known address
# This is extremely unlikely to work because the AFTR expects PCP via the B4 proxy
```

**c) ICMP-based mapping:**
```bash
# Some NATs create mappings for ICMP echo
# Send ICMP echo through DS-Lite, see if the response creates a usable mapping
ping -c 1 <external_ip>
# Then try to receive unsolicited ICMP from that external IP
```

### 7. Summary

| Approach | Likelihood | Effort | Result |
| :--- | :--- | :--- | :--- |
| NAT characterization | Certain (just test it) | Low | Determines all other options |
| UDP hole-punching (if EIM) | Medium-High | Medium | Inbound UDP through CGNAT |
| UDP hole-punching (if symmetric) | Medium | Medium | Inbound UDP with coordination |
| TCP hole-punching | Low-Medium | High | Inbound TCP (if EIM for TCP) |
| VPS relay | Certain | Low | Full inbound TCP+UDP |
| Crafted inner packets | Very Low | Low | Probably nothing |
| PCP to AFTR | Very Low | Low | Probably nothing |

### The Honest Assessment

The **single most valuable next step** is NAT characterization. It's a 5-minute test that determines whether hole-punching is viable. If the AFTR is EIM/EIF (which is common for CGNATs that need to support VoIP and gaming), you get inbound UDP for free.

If hole-punching fails or is too fragile, the VPS relay is the guaranteed fallback. It's not "fringe" — it's the standard solution for CGNAT bypass — but it works.

Everything else (crafted packets, PCP probes, etc.) is noise. The NAT characterization test is the only thing that could change your conclusion.

---

OK, I think this is a solid response. Let me refine it and make sure it's accurate.

One thing I want to double-check: in DS-Lite, does the B4 (hub) do NAT or not?

In standard DS-Lite (RFC 6333):
- The B4 is a dual-stack lite client. It encapsulates IPv4 packets in IPv6 and sends them to the AFTR.
- The B4 does NOT perform NAT. It is a simple encapsulator.
- The AFTR performs NAT44 on the inner IPv4 packets.

However, some implementations do NAT at the B4 as well (non-standard). This is sometimes called "NAT44 + DS-Lite" or "double NAT."

If the F3896LG does NAT44 before DS-Lite:
- OpenWrt sends IPv4 with source 192.168.0.2:X
- Hub NATs to 192.168.0.1:Z (hub's LAN IP, different port)
- Hub encapsulates in IPv6, sends to AFTR
- AFTR NATs to CGNAT:Y
- Return: AFTR → CGNAT:Y → 192.168.0.1:Z → hub NATs → 192.168elivers to OpenWrt

In this case, hole-punching through the AFTR delivers directly to OpenWrt. No additional NAT layer.

How to determine which case applies:
- If the hub does NAT44, then the AFTR sees inner source = hub's LAN IP (e.g., 192.168.0.1). The AFTR's NAT table maps CGNAT:Y → 192.168.0.1:Z.
- If the hub does NOT do NAT44, then the AFTR sees inner source = OpenWrt's IP (e.g., 192.168.0.2). The AFTR's NAT table maps CGNAT:Y → 192.168.0.2:X.

From outside, we can't tell the difference (both show CGNAT:Y). But we can infer:
- If the hub does NAT44, then the hub's web interface might show NAT sessions. But the hub is locked down.
- If the hub does NOT do NAT44, then the hub is a pure DS-Lite B4.

Actually, there's a way to test this:
- From OpenWrt, send a UDP packet to an external server with a specific source port (e.g., 12345).
- If the hub does NOT NAT: the AFTR sees inner source port 12345. The AFTR maps CGNAT:Y → 192.168.0.2:12345. The external server sees CGNAT:Y.
- If the hub DOES NAT: the hub changes the source port to something else (e.g., 54321). The AFTR sees inner source port 54321. The AFTR maps CGNAT:Y → 192.168.0.1:54321. The external server sees CGNAT:Y.

From the external server's perspective, both look the same (CGNAT:Y). But the mapped port Y might be different in each case.

Actually, we can't distinguish from outside. But we can test indirectly:
- If the hub does NAT44, then the hub's NAT has a limited port range. If we exhaust the hub's NAT ports, new connections will fail. This is a side-channel test but not very practical.

For the purpose of hole-punching, the key question is: **does the hub's NAT (if present) allow unsolicited inbound?**
- If the hub has a stateful firewall that only allows established/related connections, then even if the AFTR delivers the packet to the hub, the hub will drop it.
- If the hub's NAT is full-cone (allows any inbound to a mapped port), then hole-punching works.

In practice, most consumer routers (including ISP-provided hubs) have a stateful firewall that blocks unsolicited inbound. So even if the AFTR allows hole-punching, the hub might block it.

But wait — in DS-Lite, the hub is supposed to be a dumb tunnel. It shouldn't have a stateful firewall on the DS-Lite interface. The AFTR is the security boundary. So the hub should deliver all decapsulated IPv4 to the LAN without filtering.

This is implementation-specific. The only way to know is to test.

**How to test:**
1. From OpenWrt, send UDP to an external server (creates NAT mapping at AFTR and possibly at hub)
2. From the external server, send UDP back to the mapped CGNAT:port
3. If OpenWrt receives the response, the hub is delivering decapsulated IPv4 to the LAN

This is actually the same as testing whether the AFTR's NAT is EIF. If the response comes back, both the AFTR and the hub are allowing it.

So the NAT characterization test also implicitly tests whether the hub blocks unsolicited inbound.

OK, I think my response is solid. Let me finalize it.

Actually, I want to add one more fringe idea that I haven't considered:

**Idea 31: Can we use the hub's IPv6 prefix delegation to get a second IPv6 prefix, and then use that to reach the AFTR?**

No, this doesn't help. The AFTR validates the outer IPv6 source against the bound /128. A different prefix won't work.

**Idea 32: Can we use the hub's IPv6 address (not the bound /128) to send traffic to the AFTR?**

The hub has multiple IPv6 addresses: link-local, WAN address, PD prefix, etc. The AFTR only accepts traffic from the bound /128. Other addresses will be rejected.

**Idea 33: Can we use the hub's IPv6 address to send traffic to a different AFTR?**

If the ISP has multiple AFTRs, and one of them is less restrictive... This is extremely unlikely. The AFTR is determined by the provisioning (FQDN: aftr01.upc.ie). You can't choose a different AFTR.

But wait — what if we resolve the AFTR FQDN to a different address? The hub resolves aftr01.upc.ie to get the AFTR's IPv6 address. If we could poison the hub's DNS cache or intercept the DNS query... But the hub is locked down, and we can't modify its DNS settings.

However, if the hub uses SLAAC or DHCPv6 for DNS, and we can advertise a rogue DNS server via RA... The hub might use our rogue DNS server to resolve the AFTR FQDN. We could then return a different AFTR address (one that we control, or one that's less restrictive).

This is extremely fringe and unlikely to work, but it's worth mentioning as a theoretical possibility.

**How it would work:**
1. OpenWrt sends Router Advertisements on the , hole-punching would fail at the hub level, not the AFTR level. The AFTR would deliver the packet to the hub, but the hub would drop it.

How to test this:
- From OpenWrt, send UDP to an external server
- From the external server, send UDP back to the mapped CGNAT:port
- If OpenWrt receives the response, the hub is allowing it

But this is the same as testing whether the AFTR's NAT is EIF. If the response comes back, both the AFTR and the hub are allowing it.

So the NAT characterization test also implicitly tests the hub's behavior. Good.

OK, writing now. Final answer.

Let me also think about whether I should mention **CGNAT port range prediction** as a fringe idea. Some CGNATs allocate ports sequentially. If we can predict the next port, we can pre-announce it to a peer. But this is extremely fragile and unreliable. I'll mention it briefly.

And **port overloading**: if we open many connections from OpenWrt, we can observe the port allocation pattern. This might reveal whether the AFTR uses sequential, random, or hash-based port allocation. This is useful for port prediction but not for hole-punching.

OK, I think I have enough material. Let me write the response now. I'll keep it focused and practical.

Final structure:
1. The untested variable (AFTR NAT type)
2. How to test (concrete commands)
3. Decision tree (what's possible based on result)
4. Implementation (hole-punching or VPS relay)
5. Zero-cost probes (brief)
6. Honest assessment

Writing now.

I want to make sure I'm not repeating what the user already knows. They've already established:
- Spoofing is impossible (measured)
- MAP-E is not available
- PCP is not available
- Bridge mode is not available
- Single /128 binding

So I should focus on what's NEW: the AFTR NAT behavior and hole-punching.

Let me write the response now. I'll be concise and focused.

One more consideration: the user mentioned "the full lacuna of ds-lite." This suggests they want a comprehensive exploration of everything that could possibly work, not just the most promising idea. So I should be thorough but also honest about what's likely to work.

OK, writing now. For real. Final answer.

Let me think about the tone. The user is clearly frustrated that previous suggestions didn't work. They want something that actually works, or at least something that's worth testing. I should be direct, honest, and focused.

The tone should be: "Here's the one thing you haven't tested. Here's how to test it. Here's what to do based on the result. Here's the fallback if it doesn't work."

OK, writing now.

I think the response should be relatively concise. The user doesn't need a 2000-word essay. They need a clear, focused answer that identifies the untested variable and provides concrete next steps.

Let me aim for about 500-800 words, with concrete commands and a clear decision tree.

Writing now.

Hmm, actually I realize I should also consider one more thing: **the hub's DS-Lite implementation might do NAT44 before encapsulation.** This is non-standard but common in some ISP deployments. If the hub does NAT44, then there are TWO NATs: the hub's NAT and the AFTR's NAT. This is "double NAT" and makes hole-punching much harder.

How to detect this:
- From OpenWrt, send a UDP packet with a specific source port (e.g., 12345) to an external server
- If the hub does NOT NAT: the AFTR sees inner source port 12345
- If the hub DOES NAT: the AFTR sees a different inner source port

From outside, we can't tell the difference. But we can infer:
- If we can successfully hole-punch, the hub is not doing NAT (or is doing full-cone NAT)
- If hole-punching fails, the hub might be doing NAT with a stateful firewall

Actually, the NAT characterization test will reveal this implicitly. If hole-punching works, both the AFTR and the hub are allowing it. If it fails, we don't know which one is blocking.

To distinguish:
- If the AFTR is EIM/EIF but hole-punching fails, the hub is likely blocking
- If the AFTR is symmetric and hole-punching fails, the AFTR is likely the issue

OK, I think I've covered everything. Let me write the response now.

I'll structure it as:
1. The untested variable
2. The test
3. The decision tree
4. Implementation
5. Fallback
6. Honest assessment

Let me write it now. I'll keep it focused and practical.

OK I'm going to stop deliberating and just write the response. Here goes.

The response should focus on:
1. AFTR NAT characterization (the key untested variable)
2. Hole-punching (if NAT allows)
3. VPS relay (reliable fallback)
4. A few zero-cost probes

I'll be honest about likelihood and provapsulate | AFTR forwards without re-NATting |
| Inner dst = CGNAT addr | Send raw IPv4 with `dst = CGNAT_IP` on LAN | AFTR delivers to its own stack, reveals something |
| Inner src = 0.0.0.0 | Same technique | AFTR handles specially (DHCP-like) |
| PCP to AFTR inner | UDP port 5351 as inner IPv4 payload | AFTR processes PCP outside B4 proxy path |
| ICMP mapping | `ping` external, then have external send unsolicited ICMP back | NAT pinhole for ICMP |

Inject these as raw IPv4 on the LAN interface; the hub will encapsulate them into the DS-Lite tunnel automatically.

```bash
# Example: raw IPv4 with spoofed inner source, let hub encapsulate
hping3 -1 -a 100.64.x.x 8.8.8.8   # inner src = CGNAT addr
# Observe from outside whether anything unusual happens
```

---

### Honest Assessment

The NAT characterisation test is a five-minute measurement that could change the entire conclusion. If the AFTR is EIM/EIF — which is common on CGNATs that must support VoIP and gaming — you get inbound UDP through the VM line for free, with no infrastructure changes.

If it's symmetric or the hub blocks decapsulated inbound, hole-punching is dead and the VPS relay is the only path.

Everything else in the DS-Lite lacuna is closed. You've confirmed it empirically. This is the last untested variable.
