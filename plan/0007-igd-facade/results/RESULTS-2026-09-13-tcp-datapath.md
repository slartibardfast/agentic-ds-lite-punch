# RESULTS-2026-09-13-tcp-datapath: staged line verification

Status: layered. The TCP datapath core is implemented and verified at
the code level (54 unit tests, 32 of 32 Kani harnesses). The staged
line deployment proved the mapping maintenance, the SYN forwarding, and
the accept-splice-target path as separable layers, with one frontier
left: the acceptance of AFTR-forwarded SYNs past the netfilter input
path. The deployed relay was restored to its recorded artifact after the
test (sha 7127f4bf, the soak-campaign build); the container test
instruments were removed.

Redaction note: addresses are placeholders; the raw data stays on the
router.

## What was proven

1. Mapping maintenance (the holder): a TCP slot's external tuple is
   created and held by a STUN-over-TCP holder that originates from an
   ephemeral local port folded to the slot tuple by the relay's own nft
   snat_map. The tuple published correctly on the line (external ports
   in the session's port space, distinct from the UDP pin's, per the
   protocol-dimension spike).
2. SYN forwarding: the AFTR forwarded probe SYNs (from the rig's own
   vdsl4 vantage and from a genuinely external source through the us
   wireguard) to the slot's inner tuple, captured on eth1 with dst the
   slot port.
3. The datapath code: the wildcard listener accepts, the splice dials
   the target, and the reply returns through the splice. Proven by the
   local loopback round-trip: a local connection to the slot's listener
   produced the target's echo end to end.
4. A socket-binding lesson with a durable fix: a listener and an
   outbound connector cannot share one tuple on this kernel under any
   plain-socket SO_REUSE combination (reuseaddr plus reuseaddr refused;
   reuseport plus reuseport misroutes inbound SYNs into the holder;
   reuseport listener with a reuseaddr holder refuses the holder's
   bind). The holder therefore never binds the slot tuple: the fold
   does its source work.

## The remaining frontier

The AFTR-forwarded SYN (arriving on eth1, dst the slot tuple) is not
answered even though the accept rule sits first in the input chain and
the wildcard listener is bound. A local SYN to the same listener is
answered. The split points at the netfilter input path for eth1-
originated translated SYNs (the candidate is the eth1 rp_filter or the
route for the translated source), the same class as the C3 finding that
the input chain drops forwarded TCP NEW. This is a follow-up
experiment, not a datapath defect: the code path is proven by the local
loop.

## Vantage artifacts recorded

- The rig's own egress sources are the router's own addresses: a probe
  through vdsl4 masquerades to the router's own PPPoE IP, so the
  listener's reply is routed locally and never egresses the AFTR. The
  dead-mapping RST readings in C3 worked because that RST came from the
  AFTR, not the router.
- The us wireguard as an external vantage: the SYN arrived from the us
  endpoint's public address (the AFTR accepts any source, EIM), but the
  VPN's own return path did not carry the reply in this test.
- Globalping: the current API schema accepts only ping, traceroute,
  dns, mtr and http types; options are rejected wholesale, the http
  probe targets port 80 only, and this line never receives an
  AFTR-chosen external port 80 (no source-port preservation), so the
  API cannot address the mapping.

## Follow-ups

- The eth1 forwarded-SYN acceptance: test the rp_filter hypothesis
  (net.ipv4.conf.eth1.rp_filter=0) or an equivalent netfilter change,
  then re-run the external connect (the us-vpn or a real off-box peer).
- The #tcp-datapath receipt stays pending until the eth1 acceptance is
  closed; the code-level verification (tests and Kani) stands as
  recorded.
- The socket-binding matrix and the fold-holder resolution are recorded
  in the tcpslot source comments for the next engineer.