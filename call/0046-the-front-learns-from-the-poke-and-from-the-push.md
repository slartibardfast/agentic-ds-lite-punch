# The front learns from the poke first, and the push names itself when it fills in

- Status: accepted
- Scope: which view teaches the front the line's tuple, what each view's authority is, and
  what a front says when it has neither
- Date: 2026-10-03

## Context and Problem Statement

[call/0042](0042-the-poke-delivers-the-tuple.md) settled that the front learns the tuple
from the source of the poke it receives, and
[call/0045](0045-the-control-channel-carries-the-tuple-the-front-sees.md) gave the channel
a payload, so the front answers the daemon with what it sees. The deployment of
2026-10-02
([the run](../plan/0012-the-front-door/results/NOTE-2026-10-02-the-front-deployed-on-the-rig.md))
showed that a poke has two offices and separated them. The carrier admits a peer the line
has spoken to, and that office needs the poke to leave the line, which it does. The
front's learning needs the poke delivered, and a host whose provider filters the poke
port leaves the front with an empty table.

That deployment was weighed with the cast on 2026-10-03. The operator, who is this
front's primary persona, wants a service reached from outside the line with no tunnel,
verifies cheaply, and counts a confident wrong assumption among their named frustrations.
A fallback that teaches the front a tuple the daemon believes is right is that
assumption, so it has to name itself and never win quietly. The same deployment produced
a second demand, since the operator found the empty table by capture rather than by
reading it: a front that routes nothing has to say so. The agent works in a bounded
window and needs the rule deterministic enough for a lane to check and written where the
next session reads it, because a rule that lives only in the code reads as an accident to
whoever resumes.

## Decision

Both views are kept, in a fixed order. The poke's source is authoritative for its
protocol while it is fresh. The push's table fills a protocol that has no fresh poked
tuple, and every entry it fills is named as the push's, in the include the front routes
with and in the report the daemon reads. A push entry never replaces a fresh poked one,
and two views that disagree are a line of their own rather than a quiet change.

A protocol with no fresh view at all is reported once, so a front that routes nothing
says so and says why.

## Consequences

The front routes on a host whose poke port is filtered, and that filtering becomes a
named fallback instead of silence. The report doubles as a cross-check: the daemon learns
what the front observes for a tuple the daemon named.

The include carries a marker for each entry's source and the report carries the same, so
the renderer of the include and the parser of the report both move, and the lane's
harness grows an assertion for each view.

The posture of call/0042 stands. The poke teaches the front, and this decides what
happens when the poke cannot reach it.

## What this does not claim

It does not move the carrier's office. A peer is admitted when the line has spoken to it,
and a front that routes a tuple the carrier will not admit reaches nothing, whichever
view taught it the number. The poke still has to leave the line.