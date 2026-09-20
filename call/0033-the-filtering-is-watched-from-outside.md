# The filtering is watched by a stranger's probe, and the daemon is told

- Status: accepted
- Scope: how a change in the AFTR's filtering becomes an event. Who sends the
  probe, who observes it, the interval it runs at, the shape it has on the
  wire, and what the daemon says when it stops
- Date: 2026-09-20

## Context and Problem Statement

The design rests on one property of the line: a mapping the AFTR holds accepts
an unsolicited datagram from a host the mapping was never used toward. That
property was measured on 2026-08-28/29, and measured again on 2026-09-20 from
the outside, at thirty, sixty, one hundred and twenty and three hundred
seconds of a client's silence
([the record](../plan/0010-the-filtering-proved-and-watched/results/RESULTS-2026-09-20-stranger-probe.md)).

Nothing watches it. A change at the carrier would be silent in every local
view: the daemon's writes keep the mapping alive, the facade keeps reporting
the tuple, and the first symptom is a client that stops being reachable from
outside. The failure would then be dated to when somebody noticed.

The daemon cannot see this property by looking inward, because what proves it
is a datagram from a foreign address arriving at the mapping. The daemon cannot
send from a foreign address. Something outside has to send, and the daemon is
the only place where the arrival is visible.

## Decision

- **A cooperating helper on the external vantage sends the probe.** It binds a
  fixed source port, sends one datagram to the mapping's learned external tuple
  on an interval, and logs each send with its epoch. It ships as a script in
  the component's `deploy/` directory, so a later reader can run the same
  mechanism the daemon expects.
- **The daemon recognises the probe and records its arrival.** The probe
  carries a fixed mark in its first bytes. The daemon emits a `carrier-probe`
  event naming the source tuple and the epoch, and a marked datagram is
  forwarded like any other, so recognising it grants no authority and changes
  no datapath.
- **Absence raises an event, and the event means what it says.** Three
  consecutive intervals with no probe seen produces a `carrier-silent` event,
  logged with the last probe's epoch. That event covers two causes, the
  carrier's filtering and the helper's own failure, and its text names both.
  The helper's own log separates them, and the operator's first check is the
  helper.
- **One interval, fifteen minutes.** The interval sets both the cost and the
  delay: fifteen minutes of traffic, forty-five minutes before the alarm. The
  probe is small beside the hold's own writes, and forty-five minutes is the
  price of not calling a carrier change on one lost datagram.
- **The alarm's voice is the log line.** A LAN-side signal is left open, since
  it raises questions of who is listening that this decision does not answer.

## Consequences

- A carrier change becomes a dated event. The last probe's epoch says when a
  stranger was last seen to get through it.
- The mechanism adds a dependency outside the router. The helper has to run and
  the vantage has to stay reachable, and their absence raises the same event as
  the carrier's change. That ambiguity is real, which is why the event names
  both causes and why the helper keeps its own log.
- The probe's shape is a contract between two hosts the operator owns, and it
  lives in the script the daemon ships beside its code, so a change to the
  shape is a change to both.
- The alarm path is provable without the carrier. Withholding the helper for
  three intervals exercises every step of it, and the alarm task in
  [plan/0010](../plan/0010-the-filtering-proved-and-watched/README.md) records
  exactly that while it claims nothing about the carrier.
- A period of no internet connectivity raises the event too, because the
  helper's datagram will not arrive. The event is a prompt to look, which is
  the right shape for a signal that can be wrong in both directions.
- The probe tells the carrier nothing new. It is one small datagram to an
  existing mapping, sent by the operator's own host to the operator's own
  tuple.