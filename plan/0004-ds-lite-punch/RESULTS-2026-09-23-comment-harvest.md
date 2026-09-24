# The comment harvest

- Date: 2026-09-23
- Component: ds-lite-punch at `13a5fc06` (the `v0.3.4` tag), whose source
  comments are being collapsed to one line each
- Why: a comment run of more than one line dilutes the code, so the rule from
  this date is one line, technical only. This record takes what the long
  comments stated and nothing else does, so the collapse loses no fact.

## What this record is, and what it is not

It is the residue: the facts that lived only in a source comment. It is not a
copy of the design, and not a copy of the measurements. The comparison
documents were `plan/0004-ds-lite-punch/IMPLEMENTATION.md` (the design brief),
`MEMORY.md`, and the results files of plan/0007, plan/0008, plan/0009 and
plan/0010. Facts those documents already carry are named below as carried, and
not restated.

The full pre-collapse text of every comment stays in the git history of the
commit that removed it, one commit per file.

## Persistence, and the two state directories

`persist.rs` and `publish.rs` write the daemon's state into **two** directories,
and nothing else in the project says so. This is the finding the harvest paid
for, because the manual page and the operator pages stated one directory.

| Directory | Files | Written by |
|---|---|---|
| `/tmp/dslp`, a fixed path (`persist::DEFAULT_DIR`) | `epoch`, `leases.tsv`, `upnp.tsv` | `persist.rs`, on every change, atomically |
| the state directory, `--state-dir`, default `/run/ds-lite-punch` | `tuple`, `tuple-<R>`, `upnp-ident`, and `dp.tsv` | `publish.rs`, `upnpsvc.rs` |

Confirmed on the router on 2026-09-23: `/tmp/dslp/` held `epoch` (11 bytes,
written 2026-09-14), `leases.tsv` (38 bytes) and an empty `upnp.tsv`, while
`/run/ds-lite-punch/` held `tuple`, `tuple-40000` and `upnp-ident`. The init
script seeds the DeviceProtection store at `$STATE/dp.tsv`, where `STATE` is
`/run/ds-lite-punch`.

Both directories are on temporary filesystems, so every file survives a restart
of the daemon and none of them survives a reboot.

**Carried elsewhere:** that a lease record and a mapping share a lifetime
(MEMORY, the lease-churn work), and the tuple file's role in answering a client
(call/0022, the man page's FILES section).

## The tuple file's lifetime, and the write that publishes

From `publish.rs`, two facts worth keeping as one line each in the code:

- A tuple file goes when its mapping goes. The file holds the **learned** tuple,
  so one that outlives its mapping is a lie a client can act on: a later mapping
  that takes the same bind port would be answered with the dead port. The box
  found this on 2026-09-17 with three revoked slots still carrying their old
  tuples.
- Renaming a temporary file over the good one is what publishes a record, so the
  rename must happen only when the write did. Renaming unconditionally published
  an empty file over a good table when the state directory was full, which is
  what a zero-byte `upnp.tsv` and a long-running daemon were on the router on
  2026-09-18.

**Carried elsewhere:** the emit helpers exist because `panic = "abort"` makes a
panicking `println!` fatal and a poisoned mutex abort the next request
(call/0029). The memory-first tuple read is documented in the manual page's
FILES section.

## The netlink conntrack delete, abandoned

`ct.rs` is a documented dead end, and the reason is a kernel-build quirk:

- Deleting a conntrack entry by netlink returns `EINVAL` on this 6.12.35
  ImmortalWrt build for **every** encoding tried (family 0 and 2, with and
  without `NLA_F_NESTED`, original and reply direction, with and without a
  zone), while a canonical libmnl-shaped message fails the same way. No
  conntrack tool is installable from the router's package set.
- The encodings were bisected with a `--ct-probe` flag that creates its own
  conntrack entry from a fresh local socket, tries each variant against it, and
  prints each acknowledgement code. That flag stays in the binary for
  re-bisecting.
- The mechanism that replaced it is the self-pin: an explicit
  `(NAT, R_nat) → (NAT, R_nat)` map element makes the shadow's keepalives egress
  under the observed tuple with no deletion at all, by the same explicit-tuple
  source translation the slot pins use.
- Why the deletion was wanted: the kernel source-translates the shadow's
  keepalives to a fresh ephemeral port (measured on this box 2026-09-02,
  41077 to 1024), so the refresh lands on a mapping of its own while the
  observed one dies at the AFTR's timeout.
- The wire shape is recorded here because the code is dead: the tuple bytes
  appear big-endian in the payload, and nested attributes need
  `NLA_F_NESTED` or strict nfnetlink validation rejects them with `EINVAL`.

**Carried elsewhere:** the self-pin is item G3(c) of the brief's observation
engine and appears in the engine's own comments and in MEMORY; the ephemeral
port measurement is in MEMORY.

## The slot engine's gates and budgets

None of these constants appears anywhere outside the component.

| What it governs | Value | Where |
|---|---|---|
| the engine's tick | 2 s, chosen under the AFTR's 5 to 10 s idle timeout | engine.rs:52 |
| the grace before a candidate is claimed | 3 ticks, about 6 s, counted from the entry's death, which itself lags the device's silence | engine.rs:54 |
| the silence that makes a candidate | 3 ticks (`KEEPALIVE_AFTER_TICKS`), so a flow the device still refreshes is never claimed | engine.rs:564 |
| the silence that releases a hold | 150 ticks (`LONG_QUIET_TICKS`), the backstop behind the presence probe | engine.rs:570 |
| failed LAN probes that release a hold | 3 (`DEV_MISSES_TO_RELEASE`) | engine.rs:575 |
| the device probe cadence | one probe every 3 ticks, round robin, so a tick never waits on two | engine.rs:577 |
| holds per device | 4 | engine.rs:239 |
| the lease stamp rate | one last-seen write per slot per 15 s (`LEASE_STAMP_MIN_S`), ample for a 24 hour grace | main.rs:441 |
| the GC loop | every 60 s, and the facade's own GC takes over when the facade is on | main.rs:694 |
| the TCP keepalive interval | 60 s (`TCP_KEEPALIVE_SECS`), strictly under the 120 s silent-death bound | tcpslot.rs:26 |
| the vote's servers | `MAX_VOTE_SERVERS = 4`, and two are needed for a vote | vote.rs:30 |

Behaviour the constants serve, one line each:

- `ExitReason::DeviceGone` is the third exit: a keepalive for a device that is
  off or asleep releases nothing anyone uses (engine.rs:61).
- `release_reason` is the one place a keepalive's end is decided, and it is pure
  so the policy is testable without a clock; `long_quiet` arrives as a
  parameter (engine.rs:581).
- The young-candidate map keys on the bind tuple and holds the device's packet
  count and its quiet ticks; a candidate leaves it when it leaves the live set
  (engine.rs:205).
- A candidate takes its packet baseline from its own host port until the table carries a count (engine.rs:333).
- The report set keeps only tuples that are still live, in both modes, so a
  tuple that is gone cannot keep a place in it (engine.rs:281).
- The per-flow tuple report fires on the first look and on every change, so a
  re-key appears beside its decision (engine.rs:544).
- `PinOps::del` removes a self-pin only, guarded by the NAT address: a device-key
  element is not ours to take away with the tuple (engine.rs:123).
- `NftPins::add` ignores its host arguments and always installs the self-pin;
  the device pin is a separate call (engine.rs:113).
- `device_packets` sums the entries whose NAT side is the tuple and whose origin
  is the device, because a game talking to several peers is several entries on
  one tuple; the daemon's own writes carry the NAT address as origin and count
  out (engine.rs:607).
- A slot's own keepalive egresses with the NAT address as origin, so it can never
  be read as the device's liveness (engine.rs:437).
- The used set is a sorted `Vec` and uses `swap_remove`, because a tail `memmove`
  stalls the Kani solver and slot order carries no meaning (slot.rs:124).
- The `avoid` reservation is sorted, unique, filtered to the allocator's range,
  and replaced on every refresh instead of accumulated, so a tuple that goes
  quiet stops reserving its port (slot.rs:176).
- `find_free_bind_port` scans the live slots directly, so Kani sees iteration
  over arrays and no intermediate collection (slot.rs:210).
- A lease keeps wall-clock integers instead of `Instant` so its arithmetic is
  provable; `expires_at_unix == 0` means none, for a static (slot.rs:52).
- `StaticMapErr` stays `Copy` and heap-free because the proofs walk its error
  paths; the human-readable text is built at the `main.rs` boundary (slot.rs:420).
- `insert_static` is UDP by definition, the classic relay datapath; a TCP pin
  arrives only through the grant path (slot.rs:414).
- Restore sets `expires_at_unix = now + remaining.clamp(1, lifetime)` and seeds
  `last_activity_unix = now`, so a grant that survived a restart is never reaped
  at once; the last-seen clock is not persisted (slot.rs:588).
- `gc` requires an expired lease, past the grace and unbusy, and never touches a
  static (slot.rs:476).
- TCP grants sit outside the idle policy: a live splice can be control-silent,
  and the AFTR reaps an idle TCP mapping at its own bound (slot.rs:511).
- `evict_idle_client` takes the longest-idle UDP grant of another client; the
  requester's own grants are never candidates (slot.rs:527).
- `by_upnp_key` treats the bookkeeping external port as the bind port, because
  the AFTR's real port is learned by STUN and reported separately, so delete and
  enumerate stay unique on the control point's requested port (slot.rs:337).
- `avoid_steering` reports only the live tuples below the chosen port that no
  slot holds, which is the set the rule decided; empty means the choice was free
  (slot.rs:311).
- `move_bind_port` pushes the old port into `avoid` before probing, because that
  tuple is a device's now (slot.rs:283).
- The `Cdc` trait is `Send + Sync` because the backends live behind an `Arc` in a
  spawned task and the engine reads the lease table across an await while holding
  the lock (cdc.rs:41).
- `NftCdc` resolves a tuple's identity once from a `/proc` scan and caches it
  until the mirror evicts the tuple, so steady state reads no proc files
  (cdc.rs:103).
- The mirror carries the bind tuples only, and identity is absent from it, which
  is why the code reads both sources (cdc.rs:106).
- `reconcile`'s budget caps how many fresh tuples resolve per tick (cdc.rs:284).
- The vote's pending observations are slotted per server and use a sentinel for a
  server that has not weighed in, so no collision bookkeeping is needed
  (vote.rs:47).
- Re-seeing the confirmed value clears every pending suspicion, because the
  disagreement was transient (vote.rs:77).
- The vote's proofs are named for the five properties they carry (vote.rs:130).

## The observation arm

- The conntrack line layout is documented in the code for the 6.12 kernel, token
  by token, including the optional flags and the trailing mark, zone and use
  fields (obs.rs:36).
- The parse assumes the protocol in the fourth token and rejects a line with
  fewer than 16 tokens, so a kernel layout change yields no candidates and no
  error (obs.rs:229).
- The reply half is found at the position of the second `src=` token, which is
  where the original window ends (obs.rs:244).
- `orig_dport` is never parsed and is always zero, because nothing consumes it;
  the symbolic proof entry pins both ports to zero so the tree stays small
  (obs.rs:266).
- The predicate requires the reply destination to be the VM address, since only
  flows that egress that line have a mapping to refresh (obs.rs:154).
- `scan` returns candidates in stable line order and caps a scan at the refresh
  budget (obs.rs:189).
- The parser's fixtures are real conntrack lines captured on the router on
  2026-08-31, and `cdc.rs` reuses them (obs.rs:294).
- The proc backend takes a test path, and a missing proc file yields an empty
  tick instead of a panic (cdc.rs:65).
- The backends are named `proc` and `nft`, and the chosen name is what the
  startup observe event reports (cdc.rs:100).

## The nft datapath, and the spellings that fail in silence

This is the most valuable residue of the harvest, because each entry is a
spelling or a shape that was measured failing with nothing to show for it.

| Spelling or shape | What a different spelling does | Where |
|---|---|---|
| `priority -150` for the translation chains | the nat hook floor is -200 and nft rejects that value itself, validated on the box; the priority must also stay below the firewall's source translation at -100, or the map is handed the post-translation tuple | nft.rs:17 |
| `meta l4proto udp` | a bare `udp` before a payload expression is a hard syntax error, and before the map statement it parses ambiguously; the payload case shipped broken through two releases | nft.rs:22 |
| `counter name "carrier_probe"`, quoted | the install compares its text with the chain listing, and the listing quotes the name; unquoted, the install reads its own rule as absent and adds a copy per poll, 39 of them in minutes | nft.rs:589 |
| the install reads the chain back | the listing is the only oracle for whether a rule landed, and a repair reported without one announced a change every five seconds | nft.rs:762 |
| `insert` for the counting rule | the firewall's own accepts sit earlier in the same chain, so the rule is inserted ahead of them to count at all | nft.rs:672 |
| `update` for the mirror element | the element's 15 s timeout goes unrefreshed, so it expires under a 2 s keepalive and the engine reads the flow as gone | nft.rs:498 |
| the inbound rule is a translation, and the grant and revoke work on the translation alone | a reintroduced pin creates the two-tuple fault call/0014 settled against; the grant installs no pin, so a pin delete could only fail, 54 error lines in one session on 2026-09-20 | nft.rs:192 |
| the translation chain is installed before its rule | without the chain the install errors, and the daemon refuses to start, which is the only safe direction | nft.rs:213 |
| each revoke statement runs on its own | a batch is all-or-nothing, so one absent element cancels the rest and leaves a port accepted with nothing translating it | nft.rs:330 |
| the revoke is read back | a translation left behind can deliver another client's traffic to a port that was reallocated | nft.rs:349 |
| the pin install replaces a stale element | a stale value mis-translates the device's traffic to a port the device has left, and the fault shows up nowhere | nft.rs:838 |
| the accept sets are flushed at install, and the two accept rules stay | flushing keeps a port's life to the life of the process that wanted it, and leaving the two rules avoids churn on every restart | nft.rs:229 |
| a set reference is table-scoped | the input counting rule reaches the accept set because both live in the firewall's table; moving either breaks the match silently | nft.rs:571 |

Further one-liners. The legacy sweep takes only the lines whose comment names the
daemon, so the sets' own rules stay outside its reach (nft.rs:166). The inbound set,
the inbound map and the accept sets are all created with room for 65535 entries
(nft.rs:253). `ensure_inbound` tolerates an existing chain, set or map, checks
for the rule's exact text before adding it, and flushes both sets (nft.rs:229).
`hold_in_force` parses the table after the apply instead of trusting the batch's
exit status, because the parse is the evidence (nft.rs:107). An unreadable
firewall listing reads as "the accept is there", since a duplicate accept changes
nothing about which packets pass (nft.rs:434). The source translation rules are
recognised by two exact needles (nft.rs:463). The observer's rule set is
installed from its own function so the production ruleset stays byte-identical to
the one already deployed, and its set is an address and service pair with a 15 s
timeout (nft.rs:475). The mark is the eight bytes at the start of the transport
payload, at bit 64 of the transport header (nft.rs:598). The counter's name is
defined once, so the rule and the counter read cannot drift (nft.rs:564).
`parse_carrier_probe` reads the first packet-count token and reports zero when the
listing has none (nft.rs:802). Two accept sets exist, one per protocol, because
one set for both would accept TCP on a UDP slot's port (nft.rs:866).

## The STUN reading

- Message and attribute codes: binding request `0x0001`, success response
  `0x0101`, mapped address `0x0001`, xor-mapped address `0x0020`, IPv4 family
  `0x01` (stun.rs:5).
- `parse_mapped` refuses a message type other than the success response and a
  cookie other than the magic value, and returns nothing for a buffer under 20
  bytes (stun.rs:40).
- Attribute values pad to four bytes, and the walk advances by the padded length
  (stun.rs:78). The message length is clamped to the buffer (stun.rs:52).
- The transaction id comes from a small linear congruential generator seeded from
  the clock, and uniqueness is all it needs, because STUN is unauthenticated
  (stun.rs:20).
- The xor unmask is the port against the cookie's high half and the address one
  byte at a time (stun.rs:69).
- `build_mapped_response` is shared by the unit tests and the proofs, so both
  exercise one wire format (stun.rs:83).
- The proof set is: the parser never panics, the xor is an exact inverse, the
  request always has the RFC 5389 layout, a `Some` result implies a genuine
  success response, and a truncated response yields nothing or the same tuple
  (stun.rs:139). The unwinding bounds are 13 for the parser loop and 6 for the
  two shorter loops (stun.rs:152).
- The default server list is `stun.l.google.com:19302` and
  `stun.cloudflare.com:3478` (main.rs:357), and resolution takes the first IPv4
  address per host, with a warning when a host does not resolve (main.rs:470).

## The TCP connection

- The state machine has two states, live and dead; an error from live changes it
  and an error from dead does not, and re-establishment restores it
  (tcpslot.rs:44).
- The connection is re-established on the next interval and rotates the server
  (tcpslot.rs:186).
- The ephemeral fold element from the previous round is deleted before the next,
  so a fold does not leak across re-establishes (tcpslot.rs:186).
- The listener binds the wildcard address with a backlog of 128, and the WAN-side
  scoping of inbound is the firewall's accept, and not the bind (tcpslot.rs:62).
- The specific-tuple bind beside the wildcard listener is the classic reuse
  exception: no reuseport group exists, so an inbound connection reaches the
  listener's queue, measured on this kernel (tcpslot.rs:69).
- `splice` is deliberately minimal: one dial per accept, a dial failure closes
  the peer, and the copy dominates the work (tcpslot.rs:95).
- A proof asserts the interval sits under the 120 s bound at compile time, so the
  margin is machine-checked (tcpslot.rs:232), and another asserts the state
  machine alternates with no third state (tcpslot.rs:243).

## Four comments that disagreed with the code

The harvest's other finding. Each is fixed rather than collapsed as written.

1. **`main.rs:736` claimed a pin the code does not install.** It said the boot
   path installs a pin and an accept per slot, with the pin key
   `(target ip, target port) → (NAT_ADDR, R)`. The code installs the ingress
   translation and the accept with no pin, and the comment thirteen lines below
   says so. Collapsing the first one as written would have re-enshrined the
   regress call/0014 settled against.
2. **`obs.rs:175` described a deletion that no longer happens.** It called the
   candidate's peer "the other half of the conntrack orig tuple the claim
   deletes". The engine self-pins, and `ct.rs` is recorded as an abandoned dead
   end. The measurement it carried, 41077 to 1024, is in this record.
3. **`obs.rs:125` listed a mask the code does not have.** It named five
   destinations as private or local; the code masks four, which are 10/8,
   172.16/12, 192.168/16 and 127/8. The fifth, 0/8, was never implemented. It is
   also unreachable, because the predicate requires the reply destination to be
   the VM address, so the comment drops it and the code stands.
4. **The two nftables version numbers are both right.** `nft.rs` says the on-box
   validation was on nftables 1.1.1, and MEMORY records libnftables 1.1.0. The
   router's own `nft --version` reports 1.1.1, and the library named in the
   segfault messages is `libnftables.so.1.1.0`. One is the tool and the other is
   the library.

## Startup and wiring

One-liners that live only in `main.rs`. The keepalive is a sibling task whose
handle the caller owns, because its own reference would keep the slot socket
bound after the receive loop is aborted, which is the leak of 2026-09-14
(main.rs:525). The slot table is built entirely through restore, so a static is
inserted once, and a collision or an out-of-range static is fatal at startup
because it is a configuration error (main.rs:628). A persisted grant whose port
collides with a configured static is dropped as stale, with the configuration
winning (main.rs:647). One projection of the slot table exists, in the persist
module, and the boot path must not carry a second copy that can drift from it
(main.rs:686). TCP slots spawn their own path with a fresh vote state and no UDP
keepalive (main.rs:786). In facade mode the facade rebuilds the restored leases
and is the one owner that can tear them down, so a second spawn here would
double-bind the socket (main.rs:780). The termination handler is registered only
when the signal registration succeeds, because a failed registration must leave
the default action in place, and on a signal the facade sends its goodbye
notifications, waits 150 ms and exits zero (main.rs:1088). The external address
is seeded from the per-slot tuple file first and the aggregate second, trimming
before splitting, and an unreadable file yields the unspecified address
(main.rs:1110). The help-coverage test reads the parser's own arms out of the
source instead of trusting the help text (main.rs:1160); a double-dash token
counts as a flag only when the rest is lowercase or a hyphen, and a single-dash
token only when one letter follows (main.rs:1146). The allowlist is read and
validated while parsing, so a typo fails the start and every bad line is named
(main.rs:214). The manual-page test asserts that the appended sections survive,
that the dropped extra block has not returned, and that the neutral name sits in
the fifth header field (main.rs:1220). An unwired backend and a PCP listener
without a facade exit two, and a command line with no mappings exits two after
printing the help to standard error, so a service log keeps the text (main.rs:288).
The argument parser is a separate function so the repeatable form is testable
without running the binary (main.rs:114). The engine is handed the live lease
table, so a tuple a grant has taken since startup is never captured (main.rs:950).
A facade that fails to start is not fatal: the daemon logs it and runs on
(main.rs:876).

## Carried elsewhere, and not restated here

The brief, MEMORY and the results files already hold: the self-pin and its
measurement; the 2 s cadence against the AFTR's timeout; the shadow's server
rotation; the accept at claim time; the allowlist as admission; liveness as the
device's counters; the presence probe and the device-gone exit; the engine
reading the live table; the collision report; the log-only stage; the absent
netlink events; the mirror rule and its priority; the counting rule's placement;
the inbound translation defects; the grant and revoke shapes; the punch-collision
rules; the epoch semantics; the allocator's determinism; the Kani invariants; the
vote policy; the STUN cookie and its fallback; the TCP fold and its three-way
reuse bisect; the firewall's TCP accept; the C3 window; the egress policy and the
STUN host routes; the stagger; the restored-slot datapath; the socket-leak class;
the facade's GC ownership; the version line and the coverage tests; the facade's
scope and its goodbye; and the PCP admission. Each appears in
`IMPLEMENTATION.md`, in MEMORY, or in a results file of plan/0007, plan/0009 or
plan/0010, and the harvest leaves them there.