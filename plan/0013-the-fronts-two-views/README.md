# The front's two views

**Status:** done, 2026-10-03; released at `v0.5.1`.

## What this milestone is

[plan/0012](../0012-the-front-door/README.md) released the front door, and deploying it on
2026-10-02 showed that a poke has two offices. The carrier admits a peer the line has
spoken to, and that office works wherever the poke leaves the line. The front's learning
needs the poke delivered, and it stopped at a host whose provider filters the port, leaving
the front with an empty table.

[call/0046](../../call/0046-the-front-learns-from-the-poke-and-from-the-push.md) settled
the answer with the cast: the front keeps both views in a fixed order, the poke's own
source authoritative for its protocol while its lease holds it, and the table the daemon's
push carries filling a protocol the poke has not reached, with every line naming the view
that supplied it.

This milestone is that decision built, its proof in the lane, and the release that carries
it.

## Build sequence

### Teach the front the two views {#two-views}

- verify: cd software/ds-lite-punch/main && cargo test --release --locked

`poke-listener.py` picks a view for each protocol: the poke's own source while its lease
holds it, and otherwise the table the daemon's push carries, which it reads rather than
discarding. The include and the answer both name the view that supplied each line, and a
protocol with neither is answered as `none none`. The daemon reads that name into its
`front-view` event. The lane's harness asserts the fallback, the poke's precedence, and the
lease that leaves a push's table in place.

It is built and measured. The lane is green at `4505377`, and on the rig the front routes
`41002 37.228.213.83:59348; # push` while the daemon logs that tuple and `tcp none` for the
protocol neither view has reached.

### Release it {#release-it}

- depends: #two-views
- verify: host-lifecycle software --check .

The daemon's reader carries the view's name now, so a release moves the pinned artifact and
the tag carries the two views together. It ran at `v0.5.1`, whose published asset hashes
`0d9e96c2de83fd39850bb04ad2364cb1b10260da5e6f1c3938e0457e2cdcf948`, the value
`.host-software` records, and the gate is green over that pin.

What the release does not carry is the poke's first view measured from outside. This
vantage's provider delivers TCP 22 alone, so that view is proved in the lane and by the
listener's own pick, and its measurement on the line waits on a host whose inbound poke
port is delivered.