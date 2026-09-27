# The front door: what the line, the front and a deployment each hold

**Date:** 2026-09-27. **Milestone:** `plan/0012-the-front-door`. **Status:** every
task carries a receipt, three of them recorded deferrals. The host gate stands red
on one pre-existing item, the remap debt in `call/0037` and the harvest record,
which is the operator's vocabulary to dispose of and no part of this milestone.

## What the milestone set out to do

A name over TLS, served from a port the carrier holds, with no tunnel anywhere in
the data path. The port existed before this milestone: a slot's mapping, kept alive
by the daemon's own keepalive. What was missing was everything outside the line.

## What the measurements found

- The carrier admits the peers the line has spoken to, and refuses a stranger.
  Three datagrams the external vantage sent to the published tuple produced
  nothing, while the same capture window showed the mapping's own STUN reply
  arriving at the inner tuple. The poke is the answer: a slot's socket speaks
  first, and the front takes the poke's own source as the line's tuple. The
  harness proves the UDP forward reaching the tuple it learned.
- A TCP slot learns its tuple only from a server that answers STUN over TCP, and
  the default list carried none, so a granted TCP mapping answered
  `NETWORK_FAILURE` for a mapping that existed. `stun.nextcloud.com:443` answers,
  the default carries it now, and a TCP slot published its tuple with a bound
  listener and a fold pin.
- A service host's replies need the line the mapping is on. Reverse-path filtering
  is off on every interface and the slot address's route is correct, so the fault
  behind an early failure was the client's own reply path taking the other WAN.
- The UDP forward keeps the peer's own address and port, and the TCP splice
  presents the router's. A front door over QUIC therefore behaves differently from
  one over TLS.
- Each slot has an external port of its own: slot 40000 held `59348` and slot
  40003 held `59355`.

## What the front holds

`deploy/front-door/nginx.conf` routes by name on both legs, keyed on the name for
TCP and on the listening port for UDP, reading an include the listener writes.
`poke-listener.py` listens on the port the daemon pokes, takes the poke's source as
the line's tuple, writes the include, reloads, and withdraws an entry once its
pokes stop. `mint-client.py` holds the authority, checks a password against the
DeviceProtection store by the derivation the spec states, requires the identity to
hold a role, and signs a certificate whose subject carries the identity and what
it may reach. The front needs the authority's public half and nothing else.

## What the daemon holds

The poke, for UDP and for TCP, from each slot's own socket. The identity: two PEM
files and an anchor, read at startup, with a refusal that names the flag when a
file cannot be read. The TLS client that carries that identity and verifies the
anchor, and the push with its whole-table retry, which waits for a reader.

## Where each proof lives

The component's lane runs the front's proofs on every push, which is what
`call/0041` records: the split by name, the learned tuple, the lease's withdrawal,
the mint's three refusals, the identity's four loader tests and two refusals, the
handshake against a server the anchor signed, the handshake refusing another, and
the push and its retry. Locally the same proofs run as `cargo test --release
--locked`, now 237 tests, and as `deploy/front-door/test-local.sh`, whose fixtures
are a throwaway authority minted in the run.

## What waits

- The TCP leg's handshake belongs to a deployment: the arrival is measured, and
  the answer needs a service host whose replies take the DS-Lite line
  (`call/0041`).
- The control channel's wiring waits for a payload, since the poke already
  delivers the tuple, the operator owns the names, and the front's timer keeps the
  lease (`call/0042`).
- The dependency bundle is the release phase's to produce, in the recorded
  toolchain image, and the host's reproducible lane already re-derives the
  artifact hash on every push (`call/0039`).

## The sizes

The binary measured 1,061,600 bytes before the TLS dependency and 1,065,696 after
it, a difference of four kilobytes, because the linker leaves a crate out until
something calls it. The size the release record will carry is the one the client
produces when it is wired, and the manifest's declaration is not that number.

## The decisions this milestone rests on

`call/0038` for the shape, the two classes of name and the lease; `call/0039` for
the client the binary carries; `call/0040` for how a client becomes an identity;
`call/0041` for where the front's proofs live; `call/0042` for what the poke
delivers and what the push therefore waits for.