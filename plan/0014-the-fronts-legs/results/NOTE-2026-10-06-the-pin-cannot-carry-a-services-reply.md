# The pin cannot carry a service's reply, and what a front-door slot needs instead

Date: 2026-10-06. Task: `plan/0014#the-fold`, and it changes what that task should build.

## The lead that closed

`flow_obs` exists and reads from a shell; the daemon's own read fails only because its command names
the set without its table, and the observation engine falls back to `/proc` with one warning. That is
a cosmetic daemon bug to fix, and it has nothing to do with the fold.

## What the probes left standing

The pin is installed (`192.168.21.12 . 40003 : 192.168.0.21 . 40000`), the rule is in the chain at
mangle priority and was also tried in a chain at the standard srcnat priority. The chain is reached: a
catch-all counter stands at 302 packets. The counter that matches the service's own key stands at
**zero**, and the reply leaves as the service's own address on a fresh flow by the right interface.

So the lookup never matches, and the pin cannot fold a service's forwarded flow.

## Why, and what a front-door slot needs instead

A carrier mapping's inner tuple belongs to one socket: the daemon's, on a front door's slot, or a
console's own port on a console's mapping. The daemon relays an arrival and preserves the peer's
address, which is the property the consoles depend on, so the service answers the peer directly. That
answer is a flow of its own, and no translation of it can make it the mapping's, because the mapping
belongs to a socket the service is not.

A front door's slot therefore needs a symmetric relay: the daemon answers the service as the peer and
carries the service's datagrams back out of the slot's own socket. That reverses, for that slot, the
property `call/0047` asserted, which is why it wants its own decision rather than a patch to the pin.

## The rig

The probe chain and its counters are off the box. The daemon keeps the fold it installs, which is
inert until a slot is served by the relay this note describes.