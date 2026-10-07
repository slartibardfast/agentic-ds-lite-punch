# The release carries both legs, and the front's relay was the stale half

Date: 2026-10-07. Task: `plan/0014#the-release`.

## The release

`v0.6.0` is cut at `5bbd9cb`, the commit carrying the version bump, the regenerated help text and
manual page, and the operator page's correction. The release verb built it in the recorded image with
the staged dependency bundle and the network off, and printed:

```
canonical hash: ccfee85724eaa9d3ee08de276c40d3c0725ae1fb056d5f49331edf5971f2b93d
```

The tag's lane published `ds-lite-punch`, and its sha256 is that value, so the released bytes are the
anchor the pin names. `.host-software` carries the pin and the hash, and the release receipt carries
the authorization, `plan/0014#the-release`.

## Both legs on the released bytes

The router runs the release: `--version` reads `ds-lite-punch 0.6.0`, its sha256 is the anchor, and the
slot's accept rule sits ahead of the family's per-zone input jump. The front's routing table carries a
line for each protocol:

```
8443 37.228.213.83:59348; # poke
passthru.rig 37.228.213.83:59315; # push
```

The vantage sent a datagram to the front's public port, it reached the service behind the line, and
the service's answer came back to that client:

```
ANSWER b'the service answered: the release leg, both ways' from ('170.9.238.141', 8443)
```

Three TLS clients dialled the same port with the pass-through name, and each brought the service's own
certificate back:

```
subject=CN = the-service-behind-the-line
```

## The stale half on the front

The first probe's answer arrived as a runaway: forty-five copies of the service's prefix, with the
poke's own marker at the tail. The front ran the relay from before `fcd62d4`, which answered each poke with the
marker it carried, and the daemon forwards every arrival at a relaying slot to its service, so the sink
collected each echoed marker and answered with the whole buffer.

The relay is installed from the repository now, its sha256 matches the file the record carries, and the
marker answer is gone. The record held the fix for a day, and the front ran the older file throughout.
The probe's dirty answer is what showed it, which is the argument for reading the deployed artifact
against the record before trusting a proof taken through it.

## The fixture's file is gone

The service behind the line runs as `/tmp/echo3.py`, and that file no longer exists on the box: the
process holds a deleted file, so the rig's fixtures did not survive the box's restart. A rig rebuilt
from scratch wants its fixture scripts re-created, and the shape of an answer is the first thing to
read when one looks wrong.