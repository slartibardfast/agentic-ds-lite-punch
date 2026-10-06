# The front's legs on the poked socket

**Status:** in progress, 2026-10-06.

## What this milestone is

The front is public and serving: the protected name answers `200` from the open Internet with the
daemon's certificate and refuses the same request without it, and the control channel runs every
minute over the tunnel with the view named. No byte of outside traffic has yet reached a service
behind the line, and the wiring cannot carry one: the carrier admits a peer by the exact tuple the
mapping spoke to, and nginx opens an ephemeral source port for every upstream. QUIC rides UDP, so
the UDP leg is the modern front door, and it has to own its socket rather than borrow nginx's.

This milestone makes the front's legs live on the poked socket, puts the front's deployment into the
repository as artifacts, and proves one real byte from outside to a service behind the line.

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
topology, and whether a held port serves one flow per protocol or many.

### Build the legs {#the-legs}

- depends: #admission-rules
- verify: cd software/ds-lite-punch/main && bash -n deploy/front-door/test-local.sh && python3 -m py_compile deploy/front-door/poke-listener.py

`deploy/front-door/poke-listener.py` grows into the front's relay. It owns the public UDP socket
already, so a datagram that is not the poke is relayed to the learned UDP tuple from that same
socket, which is the source port the carrier expects, and the poke still teaches it. Per-client
sockets to the slot follow the measurements; where the port has to match, the single-flow limit is
stated in the operator page rather than hidden.

The TCP leg is one relay serving nginx's pass-through names through a local upstream, answering the
poke's dial as the empty-SNI case and dialing the learned TCP tuple with the source policy the
measurements dictate.

`deploy/front-door/nginx.conf` simplifies: the name split stays, with the protected name reaching the
local https block and everything else reaching the relay, and the include-driven maps and the UDP leg
retire. The daemon needs no code change, since the poke's destination is configuration. The include
becomes the front's status file, and the report and the two views keep their shape.

### Put the deployment in the repository {#the-installer}

- depends: #the-legs
- verify: cd software/ds-lite-punch/main && bash -n deploy/front-door/install.sh

`deploy/front-door/` gains `install.sh`, which renders the configuration from its tokens, writes both
units and prepares the root, the templated unit files, and `mint.sh`, which mints the authority on
the line as `call/0040` requires, signs the front's leaf, and distributes the anchor and the
identity. The directory also gains an ignore entry for `__pycache__`.

The operator page is rewritten for the real shape: one public port with the poke arriving on it, the
QUIC note, the edge rules with their **source port range left empty**, and how those rules are made
to survive a reboot. The lane runs the repository's own renderer, so CI tests the shipped shape.

### Prove the first byte {#the-first-byte}

- depends: #the-installer
- verify: attested operator

Deploy with the installer, point `--poke` at the front's public port, reopen the edge rules for it,
and capture on both ends while an outside client reaches a service behind the line through the front,
once with a UDP probe and once with a TCP client. This closes three owed things at once: the front
door's data path, the TCP leg's external handshake, and the poke's authority at the front.

### Release it {#the-release}

- depends: #the-first-byte
- verify: host-lifecycle software --check .

A decision records the legs-on-the-poked-socket design and any single-flow limit the measurements
impose, MEMORY takes the findings, and a release carries the installer and the relay.

## The fork the plan cannot decide alone

With one public port, UDP is clean: one socket owns it, receives the poke, and relays from it. TCP is
not, if the measurements say the arrival's source port has to match the poke's destination port. The
relay would then have to originate from the very port nginx listens on, which no socket can do. If
the rule comes back that way, the TCP leg takes a second number at the edge or waits for one. The
rule table is reported before relay code is written, so the choice rests on measurement.