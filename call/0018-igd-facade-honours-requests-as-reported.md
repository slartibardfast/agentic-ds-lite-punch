# The IGD facade honours requests as reported, not as NATs do

- Status: accepted
- Scope: the UPnP IGD facade (plan/0007 phase E)
- Date: 2026-09-13

## Context and Problem Statement

The facade (E3 AddPortMapping/GetExternalIPAddress and E5 GENA) runs
against an AFTR-operated CGNAT that dictates the external tuple: the
relay's measured ground truth (EIM+EIF, no source-port preservation,
per-protocol mapping keys) means a conventional IGD's contract —
"the requested external port is the one the world dials" — cannot be
honoured. The control point's `NewExternalPort` is a request, not a
grant. Three divergences follow and must be decided once, not invented
per request:

1. AddPortMapping keying: the requested external port cannot equal the
   mapping's external port. The request is still the control-point's
   handle (delete/enumerate must be symmetric with add), so it is the
   mapping's key.
2. GetExternalIPAddress pre-discovery: before the first STUN round the
   external IP is genuinely unknown. Returning the unspecified address
   is forbidden by the milestone spec ("never 0.0.0.0").
3. GENA expiry semantics: the UPnP GENA spec leaves subscription
   reaping at the publisher's discretion; the milestone says "expiry at
   2x timeout".

## Decision

- The requested external port is the *report-requested* key: the grant
  is keyed by the request and reported back; the slot's actual inner R
  (and the AFTR-chosen external tuple, discovered via STUN) is the
  datapath reality. A divergent `NewExternalPort` is a re-Add (same
  internal key refreshes the mapping), never a duplicate; enumeration
  reports the request alongside the grant's real properties.
- GetExternalIPAddress answers the *last published* external IP
  (persisted across respawns via the tuple files; live per
  publication). Only a reboot-fresh box with no tuple yet answers
  ActionFailed (501): an honest "no mapping exists yet", never a
  fabricated or unspecified address.
- GENA subscriptions are reaped at 2x the negotiated timeout, without
  a final NOTIFY (the control point's own renewal obligations are
  unchanged); the initial NOTIFY carries eventKey 0, and every
  ExternalIPAddress change event increments it per subscription.

## Consequences

- Positive: delete/enumerate are symmetric with add for every client;
  the PS3-era stacks (POST and M-POST) and modern ones (upnpc) get a
  consistent, honest surface; no address is ever fabricated.
- Negative: a client that insists its requested external port be
  reachable on the public side will not find it there — that is the
  CGNAT's nature, documented in the E8 paragraph of the component
  README, and the reason the facade reports tuples rather than
  promising ports.
- The chosen external-port key divergence is confined to the facade
  layer: the slot engine and its persisted record are unchanged.
- Scope: this decision governs the facade only; the PS3 acceptance run
  (the operator tail) is the conformance gate that decides whether any
  further tolerance is needed.