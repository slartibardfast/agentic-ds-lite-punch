# A shared tuple is reachable, and the incumbent keeps it

- Status: accepted
- Scope: the ds-lite-punch daemon's collision rules, the two experiments
  call/0027 left open, and what they change about the slot's promise
- Date: 2026-09-18

## Context and Problem Statement

call/0027 states the collision rules and leaves two questions to measurement
rather than assumption: whether the local NAPT can punch a port a local
socket already holds, and whether the uplink ever answers one external port
to two inner tuples. The first is the one the rules turn on, and both were
run on the router with the instrument rule the same milestone learned the
hard way, that a capture which has not recorded a known event has not been
shown to work.

## The measurements

**The NAPT translates into a held port.** A socket held `(192.168.0.21,
52021)`, the shape a slot's shadow socket has. A second socket sent from
`(192.168.21.68, 52021)`, a source the policy sends out the VM line and
therefore one the masquerade applies to. The connection table read back:

```host-lint:ignore
src=192.168.21.68 dst=8.8.8.8 sport=52021 dport=45678 [UNREPLIED] src=8.8.8.8 dst=192.168.0.21 sport=45678 dport=52021
```

The reply tuple names `192.168.0.21`, so the flow was translated, and the
source port stayed 52021: the port already held. The selection consults
connection state and not socket bindings, and port preservation asks for the
source port first, so a device whose own outlet port falls inside the slot
range lands on a slot's tuple.

**The incumbent wins the inbound.** The arm was holding four of a console's
flows at the time (shadows bound on `65400`-`65403`, tuples `59251` and
`59220` learned). The external vantage's probes to those tuples arrived and
were translated to the console, after several minutes of the console's own
silence:

```host-lint:ignore
170.9.238.141.39897 > 192.168.0.21.65401: UDP, length 9
192.168.0.21 > 170.9.238.141: ICMP 192.168.0.21 udp port 65401 unreachable
```

The LAN-side capture names the actor on both lines: the forward went to the
device's address, and the ICMP's source there is the console itself, which
the NAT rewrote to `192.168.0.21` by the time the WAN capture saw it. The
port in that line is the quoted datagram's, since ICMP carries none, and the
quoted tuple is both how the error names its flow and what the router matched
to translate it. So the
datagram went to the device and not to the shadow socket bound on the same
port, and the port-unreachable is the console's own stack answering a flow
whose socket had closed. A listener-less port is exactly what answers that
way, and the router had no reason to answer once the datagram had been
translated to another address.

Both facts are worth separating from the third. The mapping survived five
minutes of a real device's silence and was reachable from outside for all of
it, which is the acceptance this milestone promised, measured on a console
rather than on a test client.

## Decision

- **R4 stands, and it is reachable.** call/0027 named the late-collision rule
  as the one that matters if the punch can land on a held port. It can, by the
  device's own outlet port, so the slot must yield: it re-binds, re-learns its
  tuple by its own write, and leaves the reported label alone (call/0022). The
  probe cannot prevent this direction, because the port is the device's and
  not ours to choose.
- **The precedence is the incumbent's, and that is the right direction.** A
  device's own connection keeps the inbound its flow earned. This rule is not
  a courtesy to the device; it is what keeps a session alive that was working
  before any slot existed, and it means the harm from a shared tuple falls on
  the slot, whose inbound a peer expected to reach a different client.
- **A shared tuple is detectable, and detection is what must not be skipped.**
  A shadow socket's port appearing in a connection entry whose pre-NAT origin
  is a device is the signature: the daemon owns the socket, so it can compare
  what it bound against who the connection table says owns the tuple. When
  that appears, the slot yields and the substitution is reported (R5), and the
  control point that holds that mapping hears it through the signal path.
- **The slot's outbound hold is harmless when the tuple is shared, and its
  inbound promise is not.** Both flows refresh one AFTR mapping, so the hold
  costs a packet and changes nothing; what breaks is the promise that inbound
  to that mapping reaches the slot's client, and that promise is the reason a
  slot exists.

## Consequences

- The detection rule is implementable from state the daemon already has: its
  own bound sockets against `/proc/net/nf_conntrack`'s pre-NAT origins, the
  same source the change-data-capture reads for identity.
- Until a slot yields on detection, the honest position is that a collided
  slot's mapping is reported rather than relied on, and the console run shows
  the cost of getting that wrong: a peer's packet reaches a device that never
  asked for it.
- The console measurement also closes the milestone's client-application hop,
  which the workstation run could not: the device's own answer on the wire is
  the receipt.
- The second open question from call/0027, whether the uplink ever answers one
  external port to two inner tuples, is untouched by either measurement and
  stays open on the passive evidence the per-slot reads already carry.