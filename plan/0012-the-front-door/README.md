# Milestone: the front door

**Status:** done, 2026-09-27; released 2026-09-28 at `v0.4.1`. Every task in the build
sequence carries a receipt, and two of them are recorded
deferrals;
[the milestone's record](results/RESULTS-2026-09-27-the-front-door.md) gathers what
the measurements found and where each proof lives. The architecture is settled in
[call/0038](../call/0038-the-front-door-is-a-held-port.md), what the control
channel costs the binary in
[call/0039](../call/0039-the-control-channel-carries-a-tls-client.md), how a
client becomes an identity in
[call/0040](../call/0040-admission-is-a-certificate-minted-on-the-line.md), where
the front's proofs live in
[call/0041](../call/0041-the-fronts-proofs-are-the-components-lane.md), and what
the poke delivers in
[call/0042](../call/0042-the-poke-delivers-the-tuple.md). The remap debt the last
receipt waited on is disposed: two records' citation lines, each in a
`host-lint:ignore` box, which is where a frozen record's citation goes once the lane
refuses to declare it (a declared phrase carrying `section` or `epoch` as a position
noun is refused outright). What the gate still reports is the pin that the release
moves, and the release runs where the recorded toolchain is available
(`call/0032`): the bundle's own release is published, the release ran on 2026-09-28 and
ended at `0.4.1`, and the section below carries what it turned up and how that closed.

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

The keepalive arm holds a UDP port, and the front needs a TCP slot with the first
external handshake through it recorded. The slot is held and its tuple is known: a
LAN client asked the facade for a TCP mapping, which `leases.tsv` persists and a
restart restores, and a STUN server that answers over TCP supplied the tuple
([the slot](results/RESULTS-2026-09-27-the-tcp-slot.md)). The poke admits the peer:
the vantage sent a SYN that arrived at the inner tuple from the exact port the line
had poked ([the SYN](results/RESULTS-2026-09-27-the-tcp-syn.md)).

What stopped the handshake was the reply's line. A forwarded arrival is answered by
the client, whose traffic carries no rule for the mapping's line, so the peer
discarded a reset from another address
([the return path](results/RESULTS-2026-09-27-the-return-path.md)). [call/0044](../call/0044-a-granted-tcp-slot-is-served-by-the-daemons-own-connection.md)
settles it: a granted TCP slot installs no translation, and the daemon's own
listener serves it from its bind address, which the line already routes.

The handshake through that path was attempted on 2026-10-02. The half inside the box is
measured: the granted slot installs no translation, and a connection to its port is
spliced to the client by the daemon's own listener. The half outside stops at the
vantage, whose provider forwards one TCP port and rewrites its outbound source ports, so
the peer cannot present the tuple the carrier admits
([the run](results/NOTE-2026-10-02-the-granted-tcp-slot-at-the-lan.md)).

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
- verify: attested call/0041
- inputs: the certificate module under `src/`, `Cargo.toml`, `Cargo.lock`

The daemon's half, settled by
[call/0039](../call/0039-the-control-channel-carries-a-tls-client.md): it loads a
client certificate and its key from files the environment names, and it trusts the
front's certificate through an anchor the operator places, with the public roots as
the fallback. This is the crate's first dependency beyond `tokio` and `libc`, and
it is what `#deps-bundle` pins.

The flags, the loading and the trust have landed. `--client-identity cert.pem:key.pem`
and `--front-anchor ca.pem` are read at startup, a file that cannot be read stops
the daemon and the refusal names the flag. The client names its TLS provider
explicitly, carries the pair, and accepts the anchor: a handshake against a server
the anchor signed completes, and a server another authority signed is refused. A
test over a key that belongs to no certificate proves rustls checks the pairing, so
a wrong identity stops at the configuration rather than at the first push. The
control channel is what puts the configuration to work.

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

The transport is built and its wiring waits for a payload. `src/front.rs` renders
the table, opens the TLS connection with the daemon's identity and the operator's
anchor, and sends the whole table again when a push fails. Four tests cover the
rendering, the endpoint, a push that reaches a server the anchor signed, and a
retry whose second attempt carries the identical table. What has no caller is the
push itself, because
[call/0042](../call/0042-the-poke-delivers-the-tuple.md) found that the front
already learns the tuple from the poke, keeps its names in the operator's
configuration, and expires its own lease.

### Renew the lease and let it expire {#lease}

- depends: #control-channel
- verify: attested call/0041

Each entry the daemon pushes carries a duration it refreshes, so a line that
stops renewing stops being routed. The front holds that property on its own
today: the listener drops an entry whose pokes have stopped, reloads, and the
harness proves the entry leaves with the pokes that kept it. The duration the
daemon would push rides the control channel when that channel has a reader, which
[call/0042](../call/0042-the-poke-delivers-the-tuple.md) records.

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

The dependency has arrived and both builds carry it. This machine builds the musl
target in 1m38s with `x86_64-linux-musl-gcc` present, and the component's lane
built it in the pinned image on the commit that added it. The artifact measured
1,065,696 bytes against 1,061,600 before, because the linker leaves a crate out
until something calls it, so the size the release record carries is the one the
client produces rather than the one the manifest declares.

The bundle itself is the release phase's to produce. The recorded toolchain image
builds the artifact, and the same run vendors the dependency layer, records its
digest in `.host-software`, and re-derives the artifact hash with the network off.
The host's reproducible lane already performs the re-derivation half on every push,
and [call/0039](../call/0039-the-control-channel-carries-a-tls-client.md) settled
that obligation.

The tool exists and the claim behind it is measured. `tools/bundle-deps.sh` vendors
the dependencies into a tarball of 16 MB and prints its digest, this run's being
`dc033b6310f523c90253e62eae2fee72cfaebf108308964ab21a686592d8f72b`. Extracting that
tarball into the crate root, appending the config it carries, and building with a
fresh cargo home and `--offline` produced the artifact in 4m17s with exit 0, so the
crate is reproduced from pinned inputs with no network. The release still owes the
publish, the `.host-software` line, and the artifact re-derivation in the recorded
image.

That digest is superseded, and that tarball is not the one to publish. The run named
its config snippet `config.toml`, and the host's release stages a bundle by reading
`vendor-config.toml`, so the tarball of that run could not have been staged at all.
The producer carries the name the host reads now, the component's lane asserts it
and rebuilds with the network off, and this milestone's release section carries the
current digest. The 16 MB, the offline build and the path rewrite measured above all
stand.

The path in that config is the part worth knowing. `cargo vendor` prints an
absolute directory, which is where the generator's own scratch lived and which the
generator then removes, so the first tarball carried a path into a deleted
directory and could be used nowhere. The tool rewrites it to a relative `vendor`,
and the bundle extracts into the crate root. The first offline attempt failed for
the other half of the same mistake, an extraction outside the crate root, and the
second, with the bundle in place, exited 0.

Two comparisons settle what the bundle does to the artifact. The registry build at
the crate's own path and at the staged path produced the same hash, `015cbbe3…`, so
the registry build is independent of the directory it runs in. The vendored build
at that staged path produced `e88a8040…`, a different hash at the same size of
1,069,792 bytes, so the dependency source is what moves the bytes and the bundle is
not byte-neutral. The release that adopts it re-pins, and that movement is
attributable to the bundle rather than to any change in the crate.

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

## What the release still needs

The milestone's substance is closed and committed. The one item the host gate
reports is the component's pin, and the release is what moves it. What is done, and
what the run still waits on, are both checkable here.

The bundle is published, and its download is verified. It took a release of its own,
because this repository's releases are immutable once published and the release job
attaches the binary, the manual page and the artifact line rather than a bundle
(`.github/workflows/release.yml`). The commands that gave it one, run in the
component worktree, were:

```sh
sha256sum target/deps-vendor.tar.gz
gh release create deps-vendor-v1 --draft --title "ds-lite-punch dependency bundle" --notes "The vendored dependency layer the release build stages: the pinned image builds with the network off against these sources." --repo slartibardfast/ds-lite-punch
gh release upload deps-vendor-v1 target/deps-vendor.tar.gz --repo slartibardfast/ds-lite-punch
gh release edit deps-vendor-v1 --draft=false --repo slartibardfast/ds-lite-punch
```

The tag does not begin with `v`, so the `v*` release job does not fire on it. The
asset sits at
`https://github.com/slartibardfast/ds-lite-punch/releases/download/deps-vendor-v1/deps-vendor.tar.gz`,
and fetching that URL with `curl -fsSL` returns 16,319,220 bytes hashing to
`7341bc06d101ebea32736db1d2d333af3d3b051a44590a521294b985b5e29730`, byte-identical
to the tarball the producer left in the worktree. `.host-software` records it as the
`deps-bundle` line, at that URL with that digest, so the contract the release stages
is the published asset and its digest is what anchors the download.

The account above expected the lock to ship as its own fix-only release. That release
happens only when the verb has to write the lock file:
`host-lifecycle software --lock ds-lite-punch --authorized plan/0012 .` stages
`deps-bundle.lock` and bumps the version. The earlier run left that file in the
worktree, so the verb reports the lock as already there. The lock therefore rides the
release commit, and the milestone's release is a single run.

`podman` was installed on this host on 2026-09-28, and the run followed:

```sh
host-lifecycle release ds-lite-punch --change-class adds-flag --authorized plan/0012 .
```

It ran the verify sweep, bumped `0.3.5` to `0.4.0`, staged the published bundle, built
in the recorded image with the network off, and printed
`59552c68ac29e8c5ff184358d5e215ccdc30bf2f8b4954353d48470cdf1d2fd5`. The commit and the
tag `v0.4.0` are pushed, `.host-software` names that commit as the pin and that hash as
the artifact, and the phase carries its receipt.

The bundle's bytes are not reproducible, which decided what got published. Two runs of
the producer on this machine, one after the other, produced different digests, so the
tarball whose digest is recorded here is the one published, and a rebuild will not
match it. The digest anchors the download; the crate sources that download unpacks are
what the offline build reproduces from.

## What the release turned up

The tag's own lane failed on this release, and the asset it published is not the binary
the record anchors. [The note](results/NOTE-2026-09-28-the-canonical-build-and-the-lanes.md)
carries the measurement: three builds of one commit, the two causes, and the fix now in
the component's three artifact lanes. The published manual page is stale as well, for the
same release's reason.

The replacement release ran the same day at `0.4.1`, from the corrected lanes, with the
generated page regenerated inside its release commit. Its published asset hashes
`609a12f296d604a3772e2643c21c41e39c530b7207691d5c084ecd0d267e710e`, which is the value
`.host-software` records, and `artifact-record.txt` in the release carries that line. The
pin names the tagged commit, the gate is green, and `#record` is done. The two defects are
filed upstream as [host-lifecycle#30](https://github.com/connollydavid/host-lifecycle/issues/30)
and [#31](https://github.com/connollydavid/host-lifecycle/issues/31). The v0.4.0 release
keeps its published bytes, because this repository's releases are immutable, and the
section above states what they are.