# A2 acceptance reframe: fold-attributed PSN Type 2 is impossible by construction; the verdict takes organic Type 2 plus the A1 fold proof

- Status: accepted
- Scope: console acceptance (A2)
- Date: 2026-09-13

## Context and Problem Statement

The plan/0006 A2 gate as drafted demanded "NAT Type 2 AND console
egress SNAT'd to the pin", i.e. a fold-attributed PSN type reading. The
capture of the console's own internet test shows PSN's NAT servers on
UDP 3478/3479 echoing datagrams the console sent from its ephemeral
source ports. A single-target relay bound at the pin cannot demux those
inbound echoes: the AFTR rewrites every inbound datagram's destination
to the pin port, and the relay has one forward target. A fold-attributed
PSN Type 2 reading is therefore impossible by construction, whatever the
relay does.

The achievable evidence base is strong on its own terms: the organic
PSN NAT Type 2 reading (capture-attributed), the in-game Modern Warfare
2 NAT indicator Open across full multiplayer sessions, no IGD answering
SSDP anywhere in the path, and the pin's folding mechanism proven end to
end by the A1 assertion (a client's flows folded through the pin, an
external STUN response transited the same mapping, and the relay
forwarded it with the demux classification correct).

## Decision

A2 acceptance is reframed to what the architecture can actually prove:

- (a) organic PSN NAT Type 2, capture-attributed, from the console's
  internet test (PSN's NAT servers on UDP 3478/3479 echoing the
  console's datagrams);
- (b) the fold proof of A1: a LAN client's outbound flows fold through
  the pin and an external-originated datagram transits the same mapping
  back to the client through the relay;
- (c) tuple stability under churn: identical external-tuple re-issue
  across the kills of the soak campaigns and session-stable operation
  through the PSN and multiplayer sessions.

The relay-attributed PSN type reading is formally out of scope: the
probe's ephemeral console-side ports cannot ride the single-target pin,
so no configuration of the relay can produce it. The fold's correctness
is attested by (b) instead of by a PSN reading. The retarget of the
deployed relay to the console is therefore skipped under this decision.

## Consequences

- Positive: A2 signs on achievable, capture-attributed evidence; the
  console acceptance for the relay is honest about the product's actual
  contribution (a stable published tuple and the fold, plus endurance),
  not a NAT-type transformation of PSN's own probe.
- Negative: a reviewer must accept the reframe: where the draft said
  "PSN Type 2 on the pin", the accepted wording is "organic Type 2 plus
  a fold-attributed echo plus tuple stability". The console's story on
  this line is "works alongside the relay", not "enabled by it".
- The phase-E decision is separated into its own record (call/0015);
  the organic Type 2 with no IGD is the direct evidence for it.