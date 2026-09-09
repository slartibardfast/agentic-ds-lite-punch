# Redesign the VM Ireland line for /57 delegation + DHCPv6-PD; retire router-side ds-lite

- Status: accepted
- Date: 2026-08-28

## Context and Problem Statement

Virgin Media Ireland reprovisioned the line (some days before 2026-08-28) from
the 2024 model ("the CPE routes exactly one /64 downstream" — see the
`blog.david.connol.ly` 2024-11 post) to a **/57 delegated toward the CPE**.
Symptoms of the old config colliding with the new model:

- `wan4o6` (router-side ds-lite B4 toward `aftr01.upc.ie` /
  `2001:730:2000:2::353`) stopped working: encap leaves eth1, zero replies —
  from the hub-LAN /64, from fresh IIDs, from a hand-carved /57 subnet, and
  across a CPE restart. The Hub 6 (LG-RDK, replaced the Sagemcom) runs ds-lite
  itself and the AFTR accepts only the hub's softwire.
- br-lan was squatting inside the hub's own /64 (the 2024 trick), which VM's
  upstream no longer treats as ours.

## Decision

- **`wan6`**: `reqprefix='auto'` — the Hub 6 sub-delegates a **/60** out of the
  /57 via DHCPv6-PD (observed: `…:YY70::/60`, rotates with the /57 on CPE
  restart). Keep `reqaddress='try'`, `sourcefilter='0'`.
- **`lan`**: `ip6assign='64'` — netifd assigns a /64 of the delegated /60 to
  br-lan; odhcpd advertises it. No more squatting in the hub's /64.
- **Fallback carve**: ~~`tools/99-lan-v6-carve`~~ **REMOVED 2026-08-31.**
  It carved index 1 of the /57 onto br-lan when PD was absent — but a
  non-delegated /64 is blackholed upstream (egress ok, zero replies), so the
  carve only manufactured a dead prefix for clients to SLAAC onto. The ULA
  (`fdd7:2524:58::/48`, RFC 4193) is the stable LAN-local addressing anchor,
  so the carve had no value the ULA doesn't already provide. LAN v6 *internet*
  addressing comes solely from PD (and briefly degrades if VM stops
  delegating).
- **`wan4o6`**: `disabled='1'`. Router-side ds-lite is dead under this
  provisioning (proven by probing; the hub owns the subscriber softwire).
  VM-line IPv4, when wanted, goes through the hub's own ds-lite via the
  `wan` interface (`192.168.0.x`, double-NAT, egress-only).
- **`wan`** stays as-is (the hub-LAN IPv4 data path).

Rejected alternatives: keep squatting the hub's /64 (breaks under the new
upstream filtering); hand-carve a /64 from the /57 as the primary model
(egress works but upstream returns nothing — the hub only routes prefixes it
delegated); chase a different AFTR address (DNS, VM's own DNS, and the hub's
admin page all agree on `aftr01.upc.ie` → `2001:730:2000:2::353`; the refusal
is per-subscriber B4 binding, not a stale endpoint).

## Consequences

- Verified 2026-08-28: delegation lands, br-lan gets `…:YY70::1/64`, router
  egress from the delegated prefix 3/3, VM-line v4 via hub works,
  `api.d07yx58.net` surface healthy, LAN clients/container re-SLAAC onto each
  new delegated prefix automatically.
- Prefix rotation on CPE restart renumbers the LAN (as before); PD makes this
  fully automatic now (no scripts in the normal path).
- Operational gotchas found en route: this busybox has **no `timeout` binary**
  (silently voided two tcpdump captures); ipip6 tunnel mode is `ipip6`, not
  `ip6`; pbr has `ipv6_enabled='0'` so v6 policy routing is untouched.
- If VM ever turns PD off again, LAN internet v6 drops (no carve fallback —
  removed 2026-08-31; the carved prefix was blackholed upstream anyway). ULA
  keeps LAN-local v6 alive. Treat a missing PD as a fault to raise with VM
  Ireland support, not something to paper over.
