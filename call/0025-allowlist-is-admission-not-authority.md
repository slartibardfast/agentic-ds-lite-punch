# The admission policy: an allowlist maintains mappings, it never authorizes

- Status: accepted
- Scope: the ds-lite-punch daemon's mapping maintenance, its admission
  surfaces and the client-facing signalling (the successor to the facade
  work in plan/0007 and plan/0008)
- Date: 2026-09-17

## Context and Problem Statement

The daemon's own contract, written into the milestone that created it,
describes a lifetime shim with admission control: on the LAN side it
implements the behavioural contract the AFTR refuses to keep, and on the
WAN side it owns one property, that the mappings do not die. Two
measurements fix the size of the problem. The AFTR's UDP idle timeout is
five to ten seconds on this node, an order of magnitude under the floor
the RFCs set, and its TCP idle timeout was measured at between 120 and
300 seconds, so even a connection that is nominally established is
reaped inside a VPN's idea of a keepalive interval.

A device can be the wrong shape for that. One console here maintains its
own mapping perfectly well, running its own STUN every two seconds from
the same port it games on. Another device may not, and a device whose
keepalive is absent, sparse or disabled behind a contended peer loses a
mapping that the client never learns is gone. The response is to hold
such a device's mappings open ourselves, invisibly, and to tell the
client the truth when holding fails.

## Decision

- **The allowlist is admission for maintenance, and it carries no
  authority.** A named device's flows get the long timeouts and the
  invisible keepalive; the entry grants no role, is operator configuration
  rather than a protocol surface, and is neither readable nor writable
  over UPnP. The v2 authorization boundary of call/0024 is untouched by it.
- **The local half follows the RFC norms, declared in the ruleset.**
  Allowlisted devices' UDP flows get at least the RFC 6888 floor of 120
  seconds in both directions, and their TCP flows the RFC 5382 established
  figure that the router already carries. This is installed as `ct
  timeout` policy objects selected by source address, which is stable
  because the allowlisted devices are DHCP-pinned. The accepted shape on
  this build is recorded with the milestone: the keyword is `protocol`,
  not `l4proto`, and the TCP state set is narrower than upstream.
- **Both halves are required, and neither is sufficient.** The local
  conntrack entry is what the router's own NAT needs in order to translate
  inbound for a quiet device. It does not refresh the AFTR, whose mapping
  is refreshed only by packets on the tuple. So the allowlist is paired
  with our own writes, and the pair is the mechanism.
- **The write cadence follows the measurement, not the RFC.** The
  interval is set from the AFTR's measured idle threshold with margin,
  and the carried longer-limit campaign is what would justify anything
  longer than the two-second cadence that is known to work. A cadence
  chosen ahead of that measurement is a guess with a cost attached: at two
  seconds, one held flow spends half a packet per second, so the allowlist
  stays small or the cadence becomes adaptive.
- **One truth, projected per dialect, and scoped per subscriber.** The
  churn and tuple path is the internal truth that already feeds the log
  and the reported external address. The client-facing signals are this
  model's own: a GENA propertyset carrying the declared evented variables
  that changed, computed with the same containment view the reads use, and
  the standard faults where a query must fail. A re-key of the datapath
  tuple is **not** a client-visible port change, because the reported port
  is the requested label of call/0022, so no event invents one.
- **PCP is the fourth admission, riding the same slot table.** The
  listener, its shared port with NAT-PMP, its quota and its result codes
  are already specified in plan/0004's implementation notes; what this
  decision adds is that its ANNOUNCE is the standards-shaped home for the
  divergence notification the daemon's contract already promises. On the
  AFTR uplink the response carries the label and the learned tuple
  follows in an ANNOUNCE, because the AFTR owns the external port; that
  divergence from the specification's assigned-port semantics is recorded
  rather than hidden.
- **The TCP half cannot be injected, so it is bounded by what we
  terminate.** A router cannot write into a client's connection without
  owning its sequence space. The options are therefore to hold what the
  relay terminates, to signal the client that its session is at risk so
  it tightens its own keepalive, or to run an opt-in surrogate on the
  machinery the TCP datapath already has. The measured TCP lifetime makes
  this a real question rather than a theoretical one.
- **WPS is not substituted.** The allowlist selects devices for
  maintenance and confers no identity, so it is not a substitute for the
  introduction protocol that call/0021 defers, and it does not touch the
  DeviceProtection service. If that introduction limb is ever built, the
  identities it creates should feed the allowlist rather than sit beside
  it; deriving device authorization from the allowlist would reverse
  call/0021 by policy and needs its own decision.
- **The trust basis is stated.** Allowlisting inherits the LAN's trust
  assumption and, for a wireless device, the strength of the SSID it
  joins. A spoofed source address inherits maintenance and never
  authority, so the exposure is bounded by the cost of the keepalives and
  not by a role.

## Consequences

- A device that cannot hold its own mapping gets the RFC lifetimes it
  cannot obtain from the AFTR, and gets them without being trusted with
  anything.
- The ruleset becomes the place the policy lives, which means a router
  upgrade or a firewall reload must carry it, and the milestone's rollout
  says how.
- The daemon gains an operator-facing list whose size has a measured cost,
  so the list is a budget rather than a convenience.
- Signalling stays inside this model: a control point learns about its own
  mappings and no others, and PCP-speaking clients get the same truth in
  their own dialect.
- The two honest divergences remain on the record: the label-versus-assigned
  port answer on the AFTR uplink, and the fact that a client's own TCP
  connection can be signalled about but not held.