# Results: the field session, the hold under real play, and a state-directory incident

Date: 2026-09-18. Component at `4795061d` (the in-memory fallback and the
rename fix), deployed build still `6a62ebd3` at the time of writing. This
record is the first field run of the hold with real consoles playing: what it
said about the hold, what it said about a console's NAT type, and the
state-directory failure it exposed along with the defect that failure had
already caused once.

## The hold under real play

The arm held both consoles' own flows, not synthetic ones:

```host-lint:ignore
{"event":"rescue","detail":"claim 192.168.21.138:64300 -> 142.93.245.186:53 -> 64300 (cdc nft)"}
{"event":"observed-tuple","detail":"192.168.21.138:64300 -> 37.228.213.83:59342 (Churn((37.228.213.83, 59342)))"}
{"event":"rescue","detail":"claim 192.168.21.68:53884 -> 35.157.91.122:10025 -> 53884 (cdc nft)"}
{"event":"observed-tuple","detail":"192.168.21.68:53884 -> 37.228.213.83:59356 (Churn((37.228.213.83, 59356)))"}
```

The second is the Switch on a game flow, to a Nintendo address on port 10025,
held and reported with its learned tuple. The Switch's own NAT type was read
during the session and came back **Type A**, the same as this project measured
before any hold existed. That is the field answer to the question `call/0028`
settled in the lab: a device keeps the inbound its own flow earned, so a slot
sharing its tuple costs the device nothing, and the console's traversal is
undisturbed by our writes.

The PS3 read **Moderate**, the Type 2 this milestone's earlier acceptance
recorded, with its 3074 mapping live through a facade slot. Its entry is the
game's own name for it:

```host-lint:ignore
3074    17      40003   192.168.21.138  3074    4294967295      6084643081      DemonwarePortMapping    192.168.21.138
```

Worth noting for the household question: the slot serving that mapping has
been `40002` in one reading and `40003` in another, because a restart
re-grants the entries and the allocator picks a free port. The console's
external tuple therefore moves when the daemon restarts, and the game's peers
relearn it. That is the inner-port side of the divergence `call/0025` records,
seen in the field.

## The state-directory incident

`/tmp` reported full, and every write into the daemon's state directory failed
with ENOSPC. The cause was mine: four `tcpdump` processes of an earlier
capture attempt were still running and writing into **deleted** files, and
between them they held gigabytes of the tmpfs. Killing those four freed it, and the filesystem read
52 MB in use.

The consequence was already on the record as a mystery. `upnp.tsv` was 0 bytes
while the daemon had been running for hours, so the entry table had not been
durable since 03:16 and a restart would have restored a stale one. **The
household 3074 mapping recorded as "lost in the first deployment window" was
this defect**: the entries record was written tmpfile-then-rename with the
rename unconditional, so when the write failed the empty tmpfile was renamed
over the good table. A full state directory destroyed the record rather than
leaving it alone.

Fixed in `4795061d`, with the failures the operator would have wanted to see:

- the rename happens only on a successful write, and the test forces the
  failure with a directory where the tmpfile belongs, then asserts the good
  record is untouched;
- the learned tuples and the tables are held in memory first, so PCP answers a
  slot from the publisher's map rather than from a file, and a state directory
  that will not take a write cannot turn every MAP into a drop;
- the first failure and the first success after it are each reported once, as
  a transition, so a silent divergence between memory and disk is not the
  outcome.

The recovery is verified on the box rather than argued: after `/tmp` was freed,
a lease renewal made the daemon persist again, and both tables came back with
their real content, the PS3's 3074 row among them.

Two lessons, one of them new. The earlier ones stand: an instrument must
record a known event before its zeros mean anything. The new one is a reading
trap worth keeping: `ls -l /proc/<pid>/fd/<n>` prints the **symlink's** length
for a deleted file, not the file's size, so a scan of deleted-file holders
reported 64 bytes each while those processes held gigabytes.

## The root cause of the console's type, and the fix

The console's NAT type is decided by one tuple, the console's own
post-NAT `(address, port)`; everything else is bookkeeping. Measured on the
router during the session, that tuple was held by nothing we own:

- the facade's slot keeps a *different* inner tuple, because a slot's relay
  socket binds the slot port and its keepalive maps that port rather than the
  device's;
- the arm, the only mechanism that can hold an arbitrary device tuple,
  refused those flows twice. Its predicate required a reply, and the console's
  flows to game peers read `[UNREPLIED]`; and its budget was spent on the same
  console's one-second DNS lookups, which it then held forever because its
  liveness test read the same mirror its own writes keep populated;
- the local conntrack policy cannot compensate, because the uplink reaps at
  thirteen to twenty-one seconds, well below the router's own sixty and one
  hundred and eighty.

The other console is the control. Its game flow was answered, so the arm
claimed it and its mapping never lapsed; that console's type stayed the best
one available.

Fixed at component `0b986268` (built as `c3351220`, 189 tests): the allowlist
admits an unanswered flow (`call/0029`), liveness is the device's own packet
counters or a peer's probe and never our writes, the GC releases a device that
stops answering on the LAN, capacity is per device, and a failed write can no
longer take the daemon down by construction.

**Pending:** the field check this fix exists for, the console's type back at
Open, which needs the deploy.

## Deferred, and why

The new build is committed and pushed, and deliberately **not deployed**: the
daemon was mid-session with a console playing, and the running build persists
correctly now that the filesystem is healthy, so the restart waits for a break
in play. Nothing about the fallback is needed for a healthy state directory,
and the yield's end-to-end acceptance does not need a restart at all.