# The hold's admission is the named device, its liveness is the device and its peers, and a failed write is never fatal

- Status: accepted
- Scope: the ds-lite-punch daemon's mapping hold, its admission and its
  liveness signals, and the failure behaviour of everything it writes
- Date: 2026-09-18

## Context and Problem Statement

A console's NAT type is decided by one tuple: the console's own post-NAT
`(address, port)`, the one its own packets create and the one a game's peers
are told. Measured on the router during a session, that tuple was held by
nothing we own. The facade's slot keeps a *different* inner tuple, because a
slot's relay socket binds the slot port and its keepalive maps that port. The
observation arm is the only mechanism that can hold an arbitrary device tuple,
and it refused these flows twice over: its predicate required a reply, and a
console's flows to game peers are frequently unanswered; and its budget was
spent on the same console's one-second DNS lookups, which the arm then held
indefinitely because its liveness test read the same mirror its own writes
keep populated.

The contrast in the field was the proof. The other console's game flow was
answered, so the arm claimed it, its mapping never lapsed, and that console's
type stayed the best one available. Same code, same line, two outcomes.

## Decision

- **The allowlist admits an unanswered flow.** For a flow whose pre-NAT origin
  is a named device, the reply requirement is dropped: the device's own
  outbound tuple is exactly the one a quiet device will lose, so an
  unanswered flow is the case that needs us, not the case to skip. An
  unnamed flow keeps the reply requirement, where the heuristic is all there
  is to go on. This is `call/0025`'s rule applied to the predicate.
- **Liveness is the device's and its peers', and never ours.** A held flow
  stays alive when the device's own packet counters advance, read as a delta
  over the connection table (our writes carry the NAT address as their
  origin, so they cannot be mistaken for the device's), or when a peer's
  datagram arrives at the held tuple. Our own keepalives are excluded from
  the liveness test, because a signal our writes can satisfy proves nothing
  and made every claim permanent.
- **Device presence is a LAN probe.** A device that is off or asleep releases
  its holds, since nothing it owns can be waiting for a mapping. The probe is
  the router's own `ping`, one per tick in a round robin so a tick never
  blocks on more than one, and a probe that cannot run at all answers "up": a
  broken probe must never release a live hold.
- **Capacity is per device.** One device's churn cannot spend another's, and
  a flow both sides have left silent for a minute is released, so the hold's
  budget is a working set rather than a queue.
- **A failed write is never fatal, by construction.** The release profile
  sets `panic = "abort"`, so any panic takes the whole daemon down. Two paths
  could panic on a failed write: a poisoned mutex, and a write to a broken
  stdout pipe, which is what a daemon's log stream is. Every shared lock now
  takes a poison-tolerant accessor, and every emitted line goes through a
  writer that drops the error.
- **State lives in memory, and the disk is its record.** The learned tuples
  and both tables are served from memory; a state directory that will not
  take a write is reported once and recovers once, and it can no longer
  destroy the record it failed to replace.

## Consequences

- A console that goes quiet in a lobby keeps the mapping its type depends on,
  which is the daemon's whole purpose on this line.
- The hold now runs at the granularity that matters (a named device's mapping)
  rather than at the granularity a heuristic could see, and it stops paying
  for flows the device is refreshing itself.
- The arm's log carries the transitions, the claim and the release with its
  reason, so the field can be read without a capture.
- The remaining exposure is honest and named: a device that is awake but whose
  application has stopped leaving a mapping open looks exactly like a device
  waiting for a peer, and only the peer side distinguishes them. That is why
  the peer's probe counts as liveness.