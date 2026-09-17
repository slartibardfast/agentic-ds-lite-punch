# The requested external port is a per-client label

- Status: accepted
- Scope: the UPnP IGD facade, the mapping namespace on both faces (plan/0007
  phase E successor; plan/0008's canonical mapping API)
- Date: 2026-09-17

## Context and Problem Statement

`call/0018` fixed the requested external port as the mapping's key, on the
assumption the specification makes everywhere: that the device owns the
external port it hands out. On this line it owns it on neither uplink.

- With an AFTR (the ds-lite uplink) the CGNAT dictates the external tuple, and
  the relay's slot mechanism is the datapath, so the requested port is never
  bound at all.
- On an IPv4 uplink we control, `ds-lite-punch` itself owns the external port,
  and there the requested port *can* be honoured.

So the one-holder rule has no physical basis here: with the AFTR the port is a
label and nothing collides when two clients hold it. Worse, the rule as
implemented was not even the specification's: a second claimant **evicted** the
first, so a working client's mapping was torn down silently, which is neither
the specification's 718 ConflictInMappingEntry nor a duplicate.

The case that matters is the console pair: two consoles on the LAN both ask
for `3074/UDP`, the port their software names. Under one holder, the second
breaks the first.

## Decision

The requested external port is a **per-client label**. The key is
`(client, external port, protocol)`, and several clients may hold the same
requested port. This supersedes IGDv1's one-holder behaviour for the ds-lite
world, and the same key serves an IPv4 uplink we control.

- A write replaces only the caller's own entry at that port: a re-Add of the
  same internal tuple rides the port, and a re-Add with a different internal
  tuple replaces the caller's own mapping there. Another client's entry at the
  same port is never touched, and never becomes a stray to tear down.
- Each holder gets its own slot and therefore its own real tuple: the AFTR's on
  the ds-lite uplink, or our own allocation where we own the port. On an uplink
  we own, the first holder of a requested port may be given that port itself,
  and a later claimant is served by the any-port path (2.5.17's
  `NewReservedPort`), which is the mechanism the specification provides for a
  taken port.
- `GetSpecificPortMappingEntry` and `DeletePortMapping` resolve to the caller's
  own entry at that port, or 714. Their keys carry no client, so with
  duplicates some resolution rule is needed; "mine" is the rule, because the
  port is the caller's own handle. A contained caller therefore no longer
  answers 606 for another client's port: that port is simply not in its
  namespace. A lifted caller's view of other clients' mappings is the
  enumeration and the listing, and its bulk path is `DeletePortMappingRange`
  with `NewManage` (2.5.19), which is the specification's own mechanism for
  deleting on behalf of other clients.
- The reported `NewExternalPort` stays the requested label where the datapath's
  real port is ephemeral (the AFTR's, which moved across today's restarts), and
  the requested port is honoured and reported where we own the port.

## Consequences

- **Positive:** two consoles may both hold `3074` with working datapaths; the
  eviction defect disappears rather than needing 718, because a write can only
  ever replace the caller's own entry; one key serves both uplinks and both
  faces, which is what superseding IGDv1 behaviour here means; and
  delete/enumerate stay symmetric with add from each client's own point of
  view.
- **Negative:** a control point cannot learn by port alone that another client
  holds the same requested port. On an uplink where we own the port, two
  holders of one requested port have two different real ports, so the label is
  not what the world dials there either.
- **Boundary:** if a mode is ever added that binds the requested port on an
  uplink we control, the uniqueness rule returns for that uplink alone, because
  one real port can forward to one internal tuple. The per-client key keeps
  each client's handle intact meanwhile.
- This supersedes the *first* clause of
  [call/0018](0018-igd-facade-honours-requests-as-reported.md), the keying. Its
  other two clauses, the pre-discovery external address and the GENA expiry,
  stand unchanged.