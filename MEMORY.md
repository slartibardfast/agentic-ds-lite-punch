# MEMORY: working memory (append-only)

Ground truth, measurements, and session state that a fresh session needs. Newest
entry on top. Append, never rewrite; an entry that is wrong is superseded by a
newer one, not edited.

## 2026-09-11 — agentic-host adoption (host-template 41ba4e1)

- The repo-root investigation `DSLITE.md` moved to
  `plan/0004-ds-lite-punch/INVESTIGATION.md` and rewritten to zero prose tropes.
  It is the possibility-space record that fed call/0011 and plan/0004
  (decision call/0012).
- The ds-lite-punch software is embedded at `software/ds-lite-punch` (bare
  store + main worktree, pin f7e11e934e99; recipe in `.host-software`). The
  crate has not yet been migrated into that component repo from the former
  rope-agentic monorepo (`tools/ds-lite-punch/`); reproducibility is waived by
  call/0012 until it lands.
- Register continuation: next plan number 0005, next call number 0012.
- Network ground truth for the VM line (AFTR address, no PCP/UPnP, LAN
  addressing model) lives in call/0011 and the milestone docs; policy routing
  and IP assignments are unchanged by this adoption.

## "CGNAT UDP timeout measured"

- AFTR UDP idle timeout: (5,10) s, node-dependent. The RFC 6888 floor is
  120 s; Virgin will not change it. This is the number the relay is built
  around (2 s STUN keepalive cadence, worst-case node about 5 s).
- TCP mapping idle lifetime remains unmeasured (the TCP idle-lifetime test,
  deferred, gates TCP grants only).

## "UDP hole punching works"

- The AFTR is endpoint-independent mapping and filtering (EIM+EIF) for UDP:
  consistent mapping under rotating STUN, and unsolicited inbound to the
  mapped tuple is delivered.
- External ports are always AFTR-chosen random-high, never the inner source
  port (no source-port preservation).
- The v1 core's live tuple 37.228.213.52:24258 held stable under 2 s
  keepalive; external UDP probes from four or more countries forwarded with
  peer source preserved.

## "TCP EIF" (full method)

- Proven 2026-08-31. Setup: the client held a TCP mapping open, inner
  (192.168.0.21, 32014), external 37.228.213.83:59390, discovered via STUN.
  Our vdsl4 line acted as the dual-homed source-port oracle (third party).
- Probes: 5/5 globalping HTTP probes (DE/BR/JP/US/AU) returned HTTP 200 from
  the router-side twin listener. Each response body echoed the exact post-AFTR
  source IP the AFTR forwarded, matching the twin's accept log 1:1.
- Control: probes to an unmapped port in the same batch returned 5/5
  `ECONNREFUSED` (AFTR RST, unchanged behavior).
- Consequence: endpoint-independent filtering holds for TCP as well as UDP; a
  TCP mapping is reachable by any external address. The relay stays UDP-only
  by product decision, not CGNAT limitation.