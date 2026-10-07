# The front's legs on the poked socket

**Status:** built and released at `v0.6.0`, 2026-10-07. Two tasks wait on the operator's word:
`#admission-rules` and `#the-first-byte`.

## What this milestone is

The front is public and serving: the protected name answers `200` from the open Internet with the
daemon's certificate and refuses the same request without it, and the control channel runs every
minute over the tunnel with the view named. Both legs carry traffic to a service behind the line and
back: a datagram from outside, and a TLS client that reaches the service's own certificate through
the pass-through name. QUIC rides UDP, so the UDP leg is the modern front door, and it owns its own
socket.

This milestone made the front's legs live on the poked socket, put the front's deployment into the
repository as artifacts, and carried the first real byte of outside traffic to a service behind the
line. [call/0049](../../call/0049-the-fronts-legs-ride-the-poked-socket.md) records the shape the
measurements settled.

## Build sequence

### Measure the admission rules {#admission-rules}

- verify: attested operator

Three measurements on the rig, each with a capture on the box, before any relay code is written:

- Does an *unanswered* poke admit the peer? Point `--poke` at a closed port on the vantage, then
  attempt an arrival from that port. A refused TCP dial and a UDP datagram nobody listens for each
  have to be shown to admit the peer, or not.
- Must the arrival's *source port* equal the poke's *destination port*? Attempt an arrival from a
  different port first, then from the matching one.
- Is the admission per address alone, with the port unconstrained?

The rule table lands in `results/`, and it decides the relay's socket policy, the TCP side's port
topology, and whether a held port serves one flow per protocol or many. Each attempt wants a rig in a
known state: one slot per protocol, its tuple read immediately before the attempt and again after it,
so a mapping that moves mid-test is visible rather than fatal. The first pass is recorded in
[the note](results/NOTE-2026-10-06-the-admission-rules-so-far.md), and it already settles one rule: a
poke answered with a refusal does not admit the peer, in either protocol, from either port.

The table is measured and recorded in [the rules](results/NOTE-2026-10-07-the-admission-rules.md):
a poke has to be answered, the admission reads the address, the spoke's protocol decides which
protocol is admitted, and a slot's arrival wants the box's own accept rule. The receipt waits on the
operator's word, because this task's verify is an attestation.

### Build the datagram leg {#the-datagram-leg}

- verify: cd software/ds-lite-punch/main && bash -n deploy/front-door/test-local.sh && python3 -m py_compile deploy/front-door/poke-listener.py

`deploy/front-door/poke-listener.py` grows into the front's relay. It owns the public UDP socket
already, so a datagram that is not the poke is relayed to the learned UDP tuple from that same
socket, which is the source port the carrier expects, and the poke still teaches it. Per-client
sockets to the slot follow the measurements; where the port has to match, the single-flow limit is
stated in the operator page rather than hidden.

The TCP leg is one relay. It serves nginx's pass-through names through a local upstream, answers the
poke's dial as the empty-SNI case, and dials the learned TCP tuple with the source policy the
measurements dictate.

`deploy/front-door/nginx.conf` simplifies: the name split stays, with the protected name reaching the
local https block and everything else reaching the relay, and the include-driven maps and the UDP leg
retire. The daemon needs no code change, since the poke's destination is configuration. The include
becomes the front's status file, and the report and the two views keep their shape.

The datagram half is built and measured, and the TCP half waits on the rule that is still open. The
socket owns the public UDP port, absorbs the pokes, and sends a client's datagram onward from itself:
proved locally with a fake slot that also plays the line, and in the lane, whose harness reports
`the front follows the poke: the datagram left for the learned tuple from the socket the poke landed
on`. nginx's UDP server and its port-keyed map are gone, and `--udp-only` leaves the port's TCP half
to nginx. One flow at a time holds the socket, which the operator page has to say out loud.

It is also measured on the rig, and it carries traffic: a datagram sent from outside reached a service
behind the line, and the service answered the message it was given. What is missing is the answer's
way home, since the service's reply leaves from its own address rather than the mapping's tuple, and
folding that reply into the slot is the daemon's next fix
([the run](results/NOTE-2026-10-06-corrected-the-datagram-leg-carries-traffic.md)). The admission is
measured with it: an absorbed poke admits the peer, and the peer's source port does not have to match
the poke's destination, so several clients can share the front while the relay's own one-socket habit
is what limits it today.

### Build the TCP leg {#the-tcp-leg}

- depends: #the-datagram-leg
- verify: cd software/ds-lite-punch/main && cargo test --release --locked

The TCP half of the front's traffic. The admission measurements unblocked it: the carrier admits a
peer by address, so a relay dialling the learned TCP tuple is not tied to the poked port, and the poke's
dial already reaches an acceptor, since an SNI-less connection is routed to the relay's place. What it
needs is a relay on the local port nginx routes those connections to, dialling the learned tuple and
splicing the two.

Built and measured, and smaller than the paragraph above expected. nginx proxies the named connection
to the carrier tuple on its own, so no relay was needed; the arrival crossed the carrier and the box
reset it, because the daemon's accept rule for the slot's port stood behind `fw4`'s zone jump, and a
rule the chain reaches after the zone jump decides nothing. The rule is placed ahead of the first
per-zone input jump now, the TCP poke names its own failures and leaves on every interval, and a
STUN-over-TCP attempt is abandoned on time. Three TLS clients brought the service's own certificate
back through the front door ([the run](results/NOTE-2026-10-06-the-tcp-leg-closes.md)).

### Put the deployment in the repository {#the-installer}

- depends: #the-datagram-leg
- verify: cd software/ds-lite-punch/main && bash -n deploy/front-door/install.sh

`deploy/front-door/` gains `install.sh`, which renders the configuration from its tokens, writes both
units and prepares the root, the templated unit files, and `mint.sh`, which mints the authority on
the line as `call/0040` requires, signs the front's leaf, and distributes the anchor and the
identity. The directory also gains an ignore entry for `__pycache__`.

The operator page is rewritten for the real shape: one public port with the poke arriving on it, the
QUIC note, the edge rules with their **source port range left empty**, and how those rules are made
to survive a reboot. The lane runs the repository's own renderer, so CI tests the shipped shape.

### Relay the service's answers {#the-relay}

- depends: #the-datagram-leg
- verify: cd software/ds-lite-punch/main && cargo test --release --locked

The reply path is the gap the run found, and [call/0048](../../call/0048-a-slot-that-pokes-a-front-answers-as-the-peer.md)
settles it: a slot that pokes a front relays symmetrically, answering its service as the peer and
carrying the service's answers out of the slot's own socket, where the mapping lives. The pin the
superseded decision asked for cannot match a service's own flow, and the transparent forward stays for
every slot without a poke, which keeps the consoles' property intact.

It is built and measured: the round trip closes, with the client's datagram reaching the service and
the service's answer returning to the client, every hop in the capture of 2026-10-06.

### Prove the first byte {#the-first-byte}

- depends: #the-relay
- verify: attested operator

The datagram half is closed: a client's datagram reached a service behind the line and the service's
answer came back to that client. What this task still asks for is the TCP client, and the TCP leg's
external handshake with it, which belongs to `#the-tcp-leg`.

The TCP client is measured with it: three TLS clients dialled the front's public port with the
pass-through name, and each brought the service's own certificate back. The receipt waits on the
operator's word, because this task's verify is an attestation.

### Release it {#the-release}

- depends: #the-first-byte
- verify: host-lifecycle software --check .

[call/0049](../../call/0049-the-fronts-legs-ride-the-poked-socket.md) records the legs-on-the-poked-socket
design and the single-flow limit the measurements impose, MEMORY takes the findings, and the release
carries the installer, the relay and the accept rule's place. It is cut at `v0.6.0`: the release verb
re-derived the canonical hash in the recorded image with the network off, the tag's lane published
those bytes, and the router runs them ([the run](results/NOTE-2026-10-07-the-release-and-both-legs.md))

## The fork the plan cannot decide alone

With one public port, UDP is clean: one socket owns it, receives the poke, and relays from it. TCP is
not, if the measurements say the arrival's source port has to match the poke's destination port. The
relay would then have to originate from the very port nginx listens on, which no socket can do. If
the rule comes back that way, the TCP leg takes a second number at the edge or waits for one. The
rule table is reported before relay code is written, so the choice rests on measurement.