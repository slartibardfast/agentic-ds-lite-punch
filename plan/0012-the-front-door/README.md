# Milestone: the front door

**Status:** in progress, opened 2026-09-26. The architecture is settled in
[call/0038](../call/0038-the-front-door-is-a-held-port.md), what the control
channel costs the binary in
[call/0039](../call/0039-the-control-channel-carries-a-tls-client.md), how a
client becomes an identity in
[call/0040](../call/0040-admission-is-a-certificate-minted-on-the-line.md), and
where the front's proofs live in
[call/0041](../call/0041-the-fronts-proofs-are-the-components-lane.md). Six tasks
carry a done receipt and one is a recorded deferral, which the tasks below name,
and the frontier is the daemon's own identity.

## What this milestone is

A service on this line is reached today by something that terminates a connection
outside the line and re-originates it inside: an HTTP or database proxy on a
public host, or a tunnel that carries every port. The port this daemon already
holds changes the question. A carrier mapping is a real external address and port
while it lives, the daemon keeps it alive and republishes it when the carrier
moves it, and a granted TCP slot already accepts an outside arrival and splices
it onto the br-lan target. What was missing was everything outside the line: a
public endpoint, a route that turns a name into the held port, and a decision
about who may use it.

This milestone builds that outside end. One front serves the ports held here and
the daemon tells it where they are, which leaves an address that can move and a
name that routes, with no tunnel in the data path.

The measurement comes first on purpose. A front door is worth nothing if the
carrier refuses a stranger's arrival at the mapping, and that property is
currently implied rather than measured.

The reader is a person who runs a small service behind a carrier NAT and wants a
name on it rather than a proxy in front of it. Whether that reader is a new
persona or the operator this host already carries is settled before the recipe is
written, because the recipe page is written for that person.

What this milestone does not do, and the recipe repeats: it does not make the
carrier's port stable or reservable, and it does not give the LAN service the
client's own address on the TCP path.

## What the measurements changed

Four results moved this milestone's shape, and each one is recorded in the
results directory beside this file.

- A held port admits the peers the line has spoken to. A front reaches one only
  after the line speaks first, and the daemon pokes for that reason, with the front
  taking the poke's own source as the tuple.
- A TCP slot learns its tuple only from a server that answers STUN over TCP. The
  default list now carries one, which is the piece it lacked, and a granted TCP
  mapping answers with its tuple where it used to answer NETWORK_FAILURE.
- The UDP forward keeps the peer's own address and port, and the TCP splice
  presents the router's. A front door over QUIC therefore behaves differently from
  one over TLS, and the recipe says so.
- A service host's replies need the line the mapping is on. That path takes a rule
  of its own today, or the daemon-side rewrite when it lands.

The front's own halves are built and proven in the component's lane: the split by
name, the listener that learns the tuple, and the lease that withdraws an entry
whose pokes have stopped. The tasks below that carry them stay attestations,
because a clone of the host runs no nginx.

## Build sequence

Twelve tasks. The first gives the line a peer to speak to, the second measures what
the carrier then admits, the next two put a port and a route in place, and the rest
build the front's half, the authority that admits a client, the control channel
with the bundle it obliges, and the recipe that ends it. Every task carries a
verify, and the mechanical ones re-run at the gate.

### Send from the slot, so a peer is admitted {#poke-the-front}

- verify: cargo test --release --locked
- inputs: the send in `src/main.rs`, the state field in `src/mapping.rs`, the flag's definition in `tools/argdoc/src/main.rs`, `deploy/ds-lite-punch.init`

The slot's own socket sends one datagram per interval to a nominated address.
Only that socket holds the carrier's mapping state, so only it can create the
state that admits a reply from the far end. The measurement above proved the
carrier refuses a source the line has not spoken to; this task makes the front a
source it has. The interval rides the existing keepalive loop, well inside the
mapping's life. Tests assert that the datagram leaves from the slot's socket, on
the interval, and that a slot with no nominated address sends nothing.

### Measure a stranger's arrival {#stranger-arrival}

- depends: #poke-the-front
- verify: attested operator

From the vantage, send a datagram and a connection attempt to a held tuple from a
source that is not the keepalive peer: an address the STUN servers do not use,
and no prior outbound traffic from the line toward it. Read the box while it
happens, with the daemon's counter and log, and record what arrived, what the
forwarded packet looked like at eth1, and whether the carrier's filtering
distinguishes the source. The console acceptance in
[plan/0006](../0006-ps3-requirements/README.md) already implies this property; the
task measures it deliberately and characterises the filtering, because a front
door rests on the answer.

The first run is recorded in
[the results](results/RESULTS-2026-09-26-stranger-arrival.md), and its answer
narrows the premise: a held port admits the peers the line talks to and refuses a
stranger, which is what the console's own NAT Type 2 verdict means. The second
half of this task is therefore the pinhole test: the slot's own socket sends a
datagram toward the front's address, and the front then reaches the held port.
Only that socket can create the carrier's state, because the mapping belongs to
the inner tuple. The same run settles the shape of the restriction: whether the
carrier remembers an address alone or an address and a port. That answer decides
which source port the front may reach from, and it is load-bearing now, because
the poke's destination port is the thing the carrier will remember.

### Learn the line's tuple at the front {#front-learns-the-tuple}

- depends: #poke-the-front
- verify: attested call/0041

The front completes the exchange the poke opens.
`deploy/front-door/poke-listener.py` listens on the port the daemon pokes and
writes the table the front routes to, one line for each protocol. The line's tuple
for a protocol is the source of the poke the front receives, and the front is the
only party that sees it: the carrier admits a peer the line has spoken to. The
component's harness proves the behaviour beside the split, where a poke-shaped
datagram and a poke-shaped connection each leave that protocol's tuple in the
table. This task stays an attestation for the reason the front's configuration
does, since a clone of the host carries no nginx.

### Hold a TCP slot for the front {#hold-tcp-slot}

- depends: #stranger-arrival
- verify: attested call/0041

The keepalive arm already holds a UDP port. The front needs a TCP slot, and the
first external handshake through it recorded. Two routes, and this task's record
names the one taken: request the slot once from a LAN client over the existing
PCP or UPnP facade, which persists it in `leases.tsv` and restores it at start,
or let `--static-map` carry a protocol, which is a parser change with a test
first and a regenerated help text and manual page.

### Route two classes of name at the front {#front-config}

- verify: attested call/0041

The front's configuration, with both classes in one file, is written and proven:
`deploy/front-door/nginx.conf` carries the split, and
`deploy/front-door/test-local.sh` renders it, mints a throwaway authority, and
asserts that a pass-through name reaches the service's own certificate, that a
protected name is refused without a client certificate, and that the same name is
served with one. The script runs in the component's own lane, where nginx can be
installed. This task's verify stays an attestation because a clone of the host
carries no nginx, and a mechanical clause an environment cannot meet is not
evidence.

### Put an authority on the line {#the-ca-on-the-line}

- depends: #front-config
- verify: attested call/0041

The operator's half of
[call/0040](../call/0040-admission-is-a-certificate-minted-on-the-line.md): a tool
under `deploy/front-door/` holds the authority and mints a client certificate for
an identity whose password the DeviceProtection store accepts. The certificate
carries what that identity may reach. The component's lane runs its test beside the
harness, where a wrong password is refused, an identity without the required role
is refused, and a minted certificate carries the identity and the permission.

### Give the daemon its own identity {#the-daemons-identity}

- depends: #the-ca-on-the-line
- verify: cargo test --release --locked
- inputs: the certificate module under `src/`, `Cargo.toml`, `Cargo.lock`

The daemon's half, settled by
[call/0039](../call/0039-the-control-channel-carries-a-tls-client.md): it loads a
client certificate and its key from files the environment names, and it trusts the
front's certificate through an anchor the operator places, with the public roots as
the fallback. This is the crate's first dependency beyond `tokio` and `libc`, and
it is what `#deps-bundle` pins.

The flags and the loading have landed. `--client-identity cert.pem:key.pem` and
`--front-anchor ca.pem` are read at startup, a file that cannot be read stops the
daemon and the refusal names the flag, and four tests cover the loader with two
more covering those refusals. The identity reaches the wire with the control
channel, which is where a TLS stack and the public roots arrive, so this task stays
open until that lands rather than claiming a trust it does not yet perform.

### Carry the routing table to the front {#control-channel}

- depends: #hold-tcp-slot, #the-daemons-identity
- verify: cargo test --release --locked
- inputs: the control channel module under `src/`, `Cargo.toml`, `Cargo.lock`

The daemon opens HTTPS to the front's endpoint and pushes the table whole: each
held slot, its carrier tuple, the name the front routes, and whether the class is
pass-through or terminated. It authenticates with its own client certificate. A
failed push is followed by the whole table again rather than a delta, so a
reconnect repairs whatever was missed. Unit tests cover the request body and the
retry.

### Renew the lease and let it expire {#lease}

- depends: #control-channel
- verify: cargo test --release --locked

Each entry the daemon pushes carries a duration it refreshes, so a line that
stops renewing stops being routed. The front enforces the withdrawal on its own
today, while the control channel is unbuilt: the listener drops an entry whose
pokes have stopped, reloads, and the harness proves the entry leaves with the
pokes that kept it. Tests cover the renewal, the expiry, and the drop of a stale
entry.

### Pin the dependency bundle {#deps-bundle}

- depends: #control-channel
- verify: host-lifecycle software --verify-build .
- inputs: `.host-software`, `Cargo.lock`

The TLS client is the first dependency this crate has taken beyond `tokio` and
`libc`, and [call/0039](../call/0039-the-control-channel-carries-a-tls-client.md)
settles what that owes: a hash-pinned bundle recorded in `.host-software`, so the
artifact is reproduced from pinned inputs with the network off. The crate pins the
musl target in `.cargo/config.toml`, so the dependency builds for musl wherever the
suite runs. This machine carries `x86_64-linux-musl-gcc`, which a TLS crate with a C
core needs, and the machine that cuts the release carries the pinned image; both are
worth naming in the release record, since the recorded hash comes from the pinned
image and not from whichever compiler is nearest.

### Write the front-door recipe {#recipe}

- depends: #stranger-arrival, #front-config
- verify: attested call/0041

An operator page for the person this milestone serves: the front's configuration
in full, the tuple the daemon publishes and how the front learns it, the two
classes of name, the counterpart on the UDP path for QUIC, and the two
asymmetries, where QUIC keeps the client's own address and HTTPS does not. David
Álvarez Rosa's "Self-Hosting Behind CGNAT" is cited as the inspiration for the
front-door use case.

### Record the milestone {#record}

- depends: #recipe, #deps-bundle, #lease
- verify: host-lifecycle software --check .

The results document: the measurement's transcript and what the carrier's
filtering turned out to be, the handshake through the held port, the front's
configuration as it ran, and the size the binary grew to.