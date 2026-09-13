# RESULTS-2026-09-13-tcp-datapath: staged line verification

Status: closed 2026-09-13. The RCA identified the return-path defect:
accepted TCP connections' replies followed the kernel's output lookup
(the vdsl4 default) instead of the eth1 line the AFTR mapping lives on,
so the AFTR could never translate them. The fix (the tuple-egress policy
rule, component 6c3d15a) is proven end to end: a genuinely external peer
through the us wireguard completed a mapped TCP session with data
flowing both ways. 54 unit tests pass; the Kani suite (32 of 32) was
verified on the datapath before the egress change, which is
syscall-only and outside the proven surface.

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
   local loopback round-trip and by the external end-to-end session.
4. A socket-binding lesson with a durable fix: a listener and an
   outbound connector cannot share one tuple on this kernel under any
   plain-socket SO_REUSE combination (reuseaddr plus reuseaddr refused;
   reuseport plus reuseport misroutes inbound SYNs into the holder;
   reuseport listener with a reuseaddr holder refuses the holder's
   bind). The holder therefore never binds the slot tuple: the fold
   does its source work.
5. The external end-to-end proof: a peer behind the us wireguard
   (`170.9.238.141`, a genuinely external source) completed the full
   circuit: SYN to the published tuple, the AFTR forwarding to the
   listener, the splice to the target, the echo reply returning through
   the splice, the AFTR translating the return, and the peer receiving
   the data. The capture shows the clean three-way handshake, the data
   both ways, and the FIN/ACK close.

## The RCA (rp_filter to root cause)

- rp_filter: off (eth1 and all = 0) — refuted as the cause.
- Source validation: open (accept_local = 1) — not the cause.
- The listener and the accept rule: healthy (a local SYN completes; the
  lo capture shows the SYN-ACK generated).
- Root cause: the accepted connection's reply routes per the kernel's
  output lookup. For a self-sourced peer (the probe masqueraded to the
  router's own vdsl4 address), the reply's destination is local and the
  local table (priority 0) loops it internally, so a self-sourced
  handshake is impossible by construction. For a remote peer, the reply
  followed the main-table default (vdsl4), never the eth1 line the
  mapping lives on, so the AFTR could not translate the return path.
- Fix: add_egress_rule installs a policy rule from the bind address
  into a dedicated table whose default is the hub (prio 25100, table
  1001), forcing every tuple-sourced flow (replies, keepalives, the
  holder) out eth1; the init script removes the rule and flushes the
  table on stop. The rule does not rescue local-destination replies
  (the local table outranks it), which is why the self-sourced probe
  can never complete and the external peer is the verification gate.

## Vantage artifacts recorded

- The rig's own egress sources are the router's own addresses: a probe
  through vdsl4 masquerades to the router's own PPPoE IP, so the
  listener's reply is routed locally and never egresses the AFTR. The
  dead-mapping RST readings in C3 worked because that RST came from the
  AFTR, not the router.
- The us wireguard as the external vantage completed the proof: the
  peer's SYN arrived from the us endpoint's public address (the AFTR
  accepts any source, EIM), and the egress rule carried the reply back
  through the mapping.
- Globalping: the current API schema accepts only ping, traceroute,
  dns, mtr and http types; options are rejected wholesale, the http
  probe targets port 80 only, and this line never receives an
  AFTR-chosen external port 80 (no source-port preservation), so the
  API cannot address the mapping.

## Follow-ups

- The datapath receipt is recorded: the verify items are met (a granted
  TCP slot forwards an external TCP connection to the internal client
  with data flowing both ways; the splice state machine Kani-proven;
  the constraint relaxation recorded in call/0017).
- The facade (#facade) can now proceed behind the datapath receipt; the
  deployed relay is restored to the recorded artifact (7127f4bf) and
  the staging instruments were removed after the test.