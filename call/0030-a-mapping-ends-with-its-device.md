# A mapping asked for by a device ends when that device leaves, and never when it is quiet

- Status: accepted
- Scope: the ds-lite-punch daemon's mapping lifetimes for client-requested
  mappings, the presence rule the hold and the facade share, and the
  distinction between a client's request and the operator's configuration
- Date: 2026-09-18

## Context and Problem Statement

Two mechanisms hold a tuple for a device, and until now they disagreed about
when to let go. The observation arm released a hold because the flow had gone
quiet, which is the one state a hold exists to survive: a console in a lobby,
a paused game and a sleeping screen all present as quiet, and the mapping is
what must outlast them. The facade released a lease on silence as well, and
its slots sat outside any presence rule at all, so a console's requested
mapping outlived the console itself: a relay socket and an AFTR mapping kept
alive for a device that was not on the LAN, at about half a packet per second
each, and a slot of the pool spent on nobody.

The question a lifetime has to answer is therefore not what the traffic looks
like. It is whether the device that asked for the mapping is still there.

## Decision

- **Presence is the lifetime, and it is measured once.** One rule decides
  whether a device is on the LAN, stated in `presence.rs` and used by both
  mechanisms that hold something for a device. The neighbour table is the
  instrument: a listing with a link-layer address means present, `FAILED` or
  `INCOMPLETE` means a probe went unanswered, an echo is only a trigger when
  there is no entry to read, and an instrument that cannot run answers
  present. A broken probe never releases a live mapping.
- **A client-requested mapping ends when its client is gone.** The request was
  a promise to a device; a device that is gone has nothing to be promised, and
  the client asks again when it returns. Two consecutive misses are the
  threshold, because one miss is a Wi-Fi blip and two in a row is a device
  that is not answering.
- **Quiet is never a reason.** No lifetime in this daemon is shortened because
  the traffic stopped. A lobby, a paused game, a sleeping screen and a device
  whose keepalive is sparse all look like silence, and each of them is the
  case the mapping exists for.
- **A static mapping is the operator's configuration.** It is not a client's
  request, so presence does not release it, and the same rule that releases a
  console's mapping leaves the configured relay alone.
- **State that outlives a pass belongs to the object that lives as long.** The
  presence miss count is held by the facade rather than by the pass that
  computes it, because the GC runs as one pass per tick and a counter local to
  the pass resets before it reaches any threshold. The same rule applies to
  the release itself: the decision is taken under the lock and the work
  happens after it is dropped.

## Consequences

- A console that is switched off loses its mapping within about two GC ticks,
  and its slot returns to the pool; the same console asks again at its next
  game start.
- The daemon no longer spends a relay socket, an AFTR mapping and half a
  packet per second on a device that is not there, and the pool cannot be
  consumed by an absent client.
- The two mechanisms now agree on lifetimes, which matters because they hold
  the same kind of thing for the same devices: the arm holds a device's own
  tuple, and the facade holds a mapping the device requested.
- The remaining asymmetry is deliberate and named: the facade keeps a mapping
  for a *present* but idle client, because the client may use it the moment it
  wakes, and nothing about silence tells us otherwise.