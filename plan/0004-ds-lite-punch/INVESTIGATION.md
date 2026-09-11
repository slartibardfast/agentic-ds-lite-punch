# INVESTIGATION: the Virgin Media ds-lite possibility space

Status: superseded by measurements, 2026-08-28 to 2026-08-31; the relay that
validated the premise is plan/0004-ds-lite-punch.

This is the rewritten investigation record that was repo-root `DSLITE.md` before
the agentic-host adoption (call/0012). It preserves the explored possibility
space and the measured constraints. The question it explored: does the Virgin
Media Ireland ds-lite AFTR offer any path to inbound IPv4, and if so, how?

## Hard constraints

Measured or confirmed, in force on this line:

- The F3896LG hub polices martian IPv6 sources on the LAN. An outer or inner IPv6
  source that is not the bound /128 is dropped at L2/L3. Source spoofing of any
  kind is impossible.
- There is no bridge mode. Bridging kills IPv4 outright.
- The AFTR runs no PCP and no UPnP-IGD. There is no port-mapping protocol on the
  CGNAT.
- The subscriber softwire binds a single /128, and the CGNAT exposes a single
  IPv4 identity. There is no MAP-E or LW4o6 provisioning to fall back on.
- The OpenWrt router sits behind the hub, not beside it. The hub owns the
  softwire to the AFTR (`aftr01.upc.ie`, resolved to `2001:730:2000:2::353`).

## What was closed

Each door below was examined and closed, with the reason it is dead:

| Idea | Verdict |
|---|---|
| Spoof the outer IPv6 source | Dead. Hub polices at L2/L3 (measured). |
| IPv6 extension-header tricks (RH2 and friends) | Dead. The packet never leaves the LAN. |
| 6rd, Teredo, 6to4 | Dead. Wrong direction: they carry IPv6 over IPv4. |
| MAP-E, LW4o6 | Dead. Requires carrier provisioning that does not exist here. |
| PCP or NAT-PMP to the AFTR directly | Dead. PCP over ds-lite is proxied by the B4; the hub does not proxy. |
| Multicast over the tunnel | Dead. DS-Lite does not carry it. |
| Selecting a different AFTR | Dead. The AFTR FQDN is provisioned and the refusal is per-subscriber B4 binding, not a stale endpoint. |
| The hub's TR-069 session, its web management plane | Dead. Locked down, no usable surface. |
| 6to4-style reverse tunnels | Dead. Wrong direction. |

## The key property: the hub is a transparent encapsulator

In RFC 6333 DS-Lite, the B4 (here the hub) does not NAT. It encapsulates any
IPv4 packet arriving on its LAN interfaces into IPv6 toward the AFTR. The AFTR
is the sole NAT device. Its table maps `CGNAT:port` to the inner
`private_ip:port`, and return traffic is decapsulated and delivered to the LAN.

Two consequences follow.

1. Whatever IPv4 the router sends, the hub will carry. The question is how the
   AFTR treats the mapping, not whether the hub will forward the packet.
2. The security boundary is the AFTR. Reaching the router requires the AFTR
   NAT type to admit the mapping and the hub to forward the decapsulated
   packet. B4 implementations usually forward unfiltered; the hub's own
   behavior is implementation-specific.

## The one untested variable: AFTR NAT behavior

This was the single measurement that could change the conclusion, and it
determined every downstream option.

| AFTR NAT type | Consequence |
|---|---|
| Endpoint-independent mapping (EIM) and filtering (EIF) | Any external host can send to the mapped tuple, unsolicited. Full hole-punching. |
| EIM with address-dependent filtering | Hole-punching works when the external peer is the host the mapping was created toward. |
| Symmetric (endpoint-dependent mapping) | UDP hole-punching still works when both peers send first. TCP is very hard. |
| Symmetric with address-and-port-dependent filtering | UDP hole-punching works with both-peers-send-first. TCP is impractical. |

Characterization test, from the router: on one source port, send UDP toward two
independent servers and compare which external port each server observes. Some
CGNATs allocate ports per destination (symmetric) and some reuse the mapping
(EIM).

```bash
stunclient stun.l.google.com --localport 5000
stunclient stun.cloudflare.com --localport 5000
```

Same mapped port on both: EIM. Different mapped port per destination: symmetric.

The outcome on this line is recorded in plan/0004 and MEMORY.md: the AFTR is
EIM plus EIF for UDP, with a node-dependent idle timeout short of RFC 6888's
120 s floor, and TCP EIF is proven end-to-end. The untested variable is no
longer untested.

## The hub NAT44 question

Standard B4 implementations do not NAT. Non-standard ones (sometimes called
NAT44 plus DS-Lite, or double NAT) translate LAN sources to the hub LAN address
before encapsulation. The two cases are indistinguishable from outside, and
matter only for how far an inbound packet gets:

- If the hub does not NAT, the AFTR delivers the decapsulated packet with the
  inner destination intact, straight to the router.
- If the hub does NAT with a stateful firewall, the packet stops at the hub
  even when the AFTR allows it.

The characterization test answers both questions at once: if the return path
works end to end, both the AFTR and the hub allow it; if it fails, the
blocking device is whichever NAT is narrower. On this line the relay's live
forwarding proves the full path, hub included.

## Hole-punching

### UDP

OpenWrt sends a datagram on the forwarding socket toward a rendezvous server. The
AFTR creates the mapping `CGNAT:Y` to the inner tuple. The rendezvous server
hands `CGNAT:Y` to the external peer, which sends there. The AFTR delivers to
the inner tuple, the hub decapsulates, the router receives. Keepalives cover a
short AFTR idle timeout: any outbound UDP from the same socket refreshes the
mapping.

Tools: `pwnat` for no-rendezvous variants; `socat` or `ncat` behind a small
rendezvous script; `chisel` when the traffic needs a reliable transport.

### TCP

With EIM for TCP, simultaneous open works: both peers send SYN at the same
time, coordinated through the rendezvous server. Through symmetric NAT it is
effectively impractical. TCP was the expensive option on this line and the
relay deliberately does not do TCP (see plan/0004).

### The timeout constraint

The AFTR's UDP idle timeout was the binding risk: if it were 30 s, keepalives
would be cheap; measured here it is an order of magnitude under the RFC 6888
floor and the relay is built around that number (2 s cadence, worst-case node
5 s). The measurement and the design are in plan/0004.

## The guaranteed fallback: VPS relay

If hole-punching fails or is too fragile, the router initiates an outbound
tunnel to a VPS with a public IPv4; the VPS reverse-proxies external clients
through the tunnel. This works under any NAT type, adds a hop and a cost, and
was the risk-reduction path had the AFTR been symmetric. It is not needed on
this line.

Tools: `frp`, `chisel`, `bore`, or a mesh such as Tailscale or ZeroTier.

## Zero-cost probes

Long shots that cost nothing to test, listed for completeness:

- Crafted inner IPv4 sources (the CGNAT address itself, `0.0.0.0`) injected as
  raw packets on the LAN; the hub encapsulates them and the AFTR's reaction is
  unpredictable but probably a drop.
- PCP to the AFTR as an inner payload on UDP 5351, outside the B4 proxy path.
  Very unlikely: the AFTR expects PCP through the B4.
- ICMP echo mappings, to see whether the CGNAT opens a pinhole for ICMP.
- Port allocation observation, to detect sequential allocation. Port prediction
  is fragile and was never worth building on.

## Honest assessment

The only idea with real value was the NAT characterization: a five-minute
measurement that decided everything after it. It came back EIM plus EIF for
UDP on this AFTR, which is what the relay exploits. Everything else in the
possibility space was closed by the constraints above, and the remaining
probes are noise. The conclusion this investigation led to, and the
verification of it, are plan/0004-ds-lite-punch.