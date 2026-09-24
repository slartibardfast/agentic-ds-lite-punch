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

## The UPnP facade, DeviceProtection and the PCP codec

The line numbers are from the component worktree at `65acff8`, later than the
`13a5fc06` this record names, because the collapse landed `persist.rs` and
`publish.rs` first. The comparison set is the one this record declares, extended
by `plan/0011` and by the component's own shipped pages (`docs/operators/`,
`deploy/ds-lite-punch.env`, `deploy/man/ds-lite-punch.8`), which stay and carry
the store format and the shared port.

### The SOAP and GENA layers

| What it governs | Value | Where |
|---|---|---|
| the SSDP advertisement age | 1800 s (`SSDP_MAX_AGE`) | upnp.rs:31 |
| the alive NOTIFY interval | 900 s, half the advertisement age | upnp.rs:31 |
| the SOAP envelope namespace an M-POST MAN header must name | `http://schemas.xmlsoap.org/soap/envelope/` | upnp.rs:34 |
| the request head and body cap | 8192 bytes (`HTTP_CAP`) | upnp.rs:37 |
| live GENA subscriptions | 8 (`MAX_GENA_SUBS`) | upnp.rs:40 |
| a callback URL length | 256 bytes (`GENA_CB_MAX`) | upnp.rs:41 |
| a subscription's requested timeout | capped at 1800 s (`GENA_TIMEOUT_CAP`) | upnp.rs:42 |
| the SERVER product line | `ImmortalWrt/1.0 UPnP/1.0 ds-lite-punch/0.1` | upnp.rs:45 |
| the M-SEARCH MX ceiling | 5 s, the SSDP recommended maximum response delay | upnp.rs:194 |
| the SSDP and USN UDN suffix | 41 bytes, `uuid:` plus 36 | upnp.rs:245 |
| concurrent HTTP connections | 16 (`HTTP_CONN_CAP`) | upnpsvc.rs:38 |
| one connection's lifetime | 30 s, which bounds a stalled handler | upnpsvc.rs:1991 |
| the GENA prune pass | 60 s (`GENA_PRUNE_S`) | upnpsvc.rs:74 |
| the local lease GC pass | 60 s (`GC_TICK_S`) | upnpsvc.rs:76 |
| one NOTIFY delivery | 2 s (`NOTIFY_TIMEOUT`) | upnpsvc.rs:78 |
| the per-control-point burst window | 1000 ms (`DISCOVERY_DEBOUNCE_MS`) | upnpsvc.rs:48 |

- An M-SEARCH carries MAN with `ssdp:discover`, and a missing MX parses as zero (upnp.rs:161).
- ST matching strips one pair of surrounding double quotes and compares case-insensitively, and an unrecognised target answers as `Ignore` (upnp.rs:151).
- Header lookup is case-insensitive on the key, skips the request line, ends a line at a bare `\n`, strips a trailing `\r`, and splits at the first `:` (upnp.rs:84).
- `trim` removes ASCII space, tab, CR and LF only (upnp.rs:73).
- Only the text after the last `#` in a SOAPACTION value is the action name, and action names are case-sensitive (upnp.rs:631).
- A SOAPACTION value with no `#` yields no action (upnp.rs:635).
- An M-POST MAN value is `"<envelope-ns>";ns=NN`, only the URL is quoted, so a leading quote is dropped before the prefix match (upnp.rs:471).
- The M-POST action header is spelled `<ns>-SOAPACTION` (upnp.rs:506), and the `ns` token is 1 to 4 bytes (upnp.rs:473).
- The four control URLs are `/ctl/IPConn`, `/ctl/PPPConn`, `/ctl/CmnIfCfg` and `/ctl/DP`, matched case-insensitively (upnp.rs:353).
- The GET paths served are `/`, `/rootDesc.xml`, `/WANIPC.xml`, `/WANPPP.xml`, `/WANCfg.xml`, and any path beginning `/igd/v1/` or `/igd/v2/` (upnp.rs:715).
- The legacy description paths stay served beside the versioned prefixes (upnpsvc.rs:2041).
- A request that is not a GET, SUBSCRIBE, UNSUBSCRIBE, POST or M-POST answers 404, and a SOAP-shaped request whose action or MAN does not resolve answers 401 (upnp.rs:672).
- The GENA markers run on POST and M-POST alike: `NT` with `upnp:event` beside `CALLBACK` marks a subscribe, and `SID` marks a renewal (upnp.rs:690).
- The SOAP fault envelope is fixed: `s:Client`, the fault string `UPnPError`, and `detail/UPnPError` in namespace `urn:schemas-upnp-org:control-1-0` (upnp.rs:1258).
- The SOAP success envelope declares `s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"` (upnp.rs:1197).
- The response envelope's namespace comes from the SOAPACTION's own URN, so a `:2` invocation is answered in the `:2` namespace (upnp.rs:335).
- A SID is accepted as `uuid:` plus 36 dashed hex characters, or as 32 raw hex characters (upnp.rs:266).
- `Sid::v4` sets the version nibble to 4 and the variant bits to `0b10` (upnp.rs:377).
- The eventKey starts at 0 with the initial NOTIFY and wraps at 2^32 (upnp.rs:399).
- The initial event carries every declared variable whether or not it moved (upnpsvc.rs:1624).
- A NOTIFY is delivered when something moved for that subscriber, and a subscription stores the view it was last told so each event carries the delta (upnpsvc.rs:134, 1641).
- The three evented variables the daemon reports are the external address, the connection status, and the subscriber's own mapping count (upnpsvc.rs:1573).
- The subscriber's own count is computed with the containment its reads apply, and the port floor binds the v2 face only (upnpsvc.rs:131, 1573).
- A datapath re-key leaves SystemUpdateID alone, because the reported port is the client's label and an event would invent a port change; the address is reported through ExternalIPAddress (upnpsvc.rs:1593).
- A mapping's appearance or removal is signalled before the entry index is persisted (upnpsvc.rs:740).
- The GENA TIMEOUT parser accepts `Second-N` and the literal `infinite` (upnpsvc.rs:2810).
- A SUBSCRIBE is refused with 501 Action Failed when the subscription table is full (upnpsvc.rs:1516).
- A subscription records its caller at SUBSCRIBE, and the callback address is not the caller (upnpsvc.rs:128).
- Any SOAP action from a client IP refreshes that client's grants' last-seen, whatever the action's own outcome (upnpsvc.rs:1909).
- The LAN-presence miss counter lives on the facade, because the GC runs one pass per tick and a pass-local counter would reset before its threshold (upnpsvc.rs:216).
- The request body may already sit in the same read as the head, so it is split out before the rest is read (upnpsvc.rs:2013).
- A deferred `ssdp:all` answer goes out at the window deadline with no added jitter, and the deadline is at most the assumed 1 s MX floor (upnpsvc.rs:521).
- The deferred `ssdp:all` answer echoes `upnp:rootdevice` as its ST (upnpsvc.rs:6050).
- Pending bursts are keyed by control point, the source address and port (upnpsvc.rs:204).
- A `watch::changed()` error means the sender dropped, and the last value still decides (upnpsvc.rs:184).
- `GetCommonLinkProperties` reports Up whenever the tuple watch holds a value, and reports 0 for both Layer-1 bit rates because the symmetric ds-lite line offers no measurable rate: the value is absent, not a measured zero (upnpsvc.rs:561).
- The connection status has two honest states on this line, the external tuple is known or it is not, because nothing dials the connection (upnpsvc.rs:2967).
- `GetNATRSIPStatus` answers NAT 1 and RSIP 0 (upnpsvc.rs:2246).
- The LAN interface is selected by index and never by address: the LAN IP can be bound to more than one interface, and `join_multicast_v4(addr)` resolves from the local table and picked a point-to-point tunnel, so `ip_mreqn` with an explicit ifindex and `imr_address = 0` is the form that hears br-lan multicast (upnpsvc.rs:3412).
- `lan_ifindex` prefers a broadcast-scope interface over a point-to-point one, and falls back to any owner when a tunnel alone carries the address (upnpsvc.rs:3457).
- The SSDP fd is created `O_NONBLOCK|O_CLOEXEC`, because tokio's `from_std` only debug-asserts nonblocking and a release build strips the assert (upnpsvc.rs:3366).
- The interface name is zero-padded, so only the used portion may be handed to `CString` (upnpsvc.rs:3496).

**Carried elsewhere:** the SSDP group and port, the search targets, the MX jitter, the alive NOTIFY with its byebye, the stable UDN and the bootid, the description chain with the WANPPPConnection:1 alias, the miniupnpd-derived SCPDs, the versioned URLs, the POST and M-POST parity with its multi-line corner, the E7 Kani scope, the burst window with its `seen_v2` rule, and the SSDP bind degrading the facade are in `IMPLEMENTATION.md`, MEMORY and the results files of plan/0007 and plan/0008. The SID OOM root cause is in MEMORY.

### The DeviceProtection store, identity and roles

| What it governs | Value | Where |
|---|---|---|
| a session's idle ceiling | 1800 s (`DP_SESSION_TTL_SECS`) | dp.rs:341 |
| failed logins before the challenge is freed | 5 (`DP_LOGIN_FAILURE_LIMIT`) | dp.rs:345 |
| PBKDF2 iterations for STORED | 5000 (`DP_PBKDF2_ITERATIONS`) | dp.rs:260 |
| the device identity and the CP identity | 16 octets each | dp.rs:160, 173 |
| the mapping description's stored length | 64 bytes (`DESC_MAX`) | upnpsvc.rs:61 |
| the automatic external-port floor | 1024 (`ANY_PORT_BASE`) | upnpsvc.rs:58 |

- The DP core is io-free and unit-tested, and the ceremony's invariants are the standard vector pins for SHA-256, HMAC and PBKDF2, which is this module's Kani non-goal (dp.rs:18).
- SHA-256, HMAC and PBKDF2 are written out in pure Rust because the crate carries no dependencies (dp.rs:15).
- `pbkdf2_hmac_sha256`, `DP_PBKDF2_ITERATIONS` and `stored_for` are the control-point side of the ceremony and are dead on the device, kept for the vector tests (dp.rs:113).
- An identity's `name` is case-sensitive and is the control point's certificate CN, and its `alias` is a display label with no certificate impact (dp.rs:155).
- One user record carries Salt and STORED plus the roles associated with the Name (dp.rs:171).
- The role hierarchy is two levels, Basic at 0 and Admin at 1, and an unknown role satisfies nothing (dp.rs:174).
- The authorization decision is a pure function of the principal's roles and the action's requirement, and it never consults the transport address (dp.rs:200).
- A session is keyed by the control point's IPv4 address, the plain-HTTP analogue of the spec's TLS session, and that address keys the store without being an authorization input (dp.rs:312).
- SetupReady is reported as permanently 1 with no transitions, because the device runs no setup-protocol registrar and no setup operation is pending; the pressure a setup-capable control point can meet is the SendSetupMessage fault path (dp.rs:401).
- A user identity carries an all-zero 16-octet ID and is skipped when the login searches the ACL for a ControlPointID (dp.rs:483).
- GetUserLoginChallenge returns the user's Salt and a fresh Challenge and replaces the session's previous challenge (dp.rs:407).
- A failed login leaves an existing session's roles intact (dp.rs:1247).
- `add_identities` keys a User identity by name and a CP identity by its 16-octet ID, and re-adds nothing already present (dp.rs:633).
- `remove_identity` removes by Name case-sensitively, treats an absent identity as a no-op success, and leaves the 600 for an invalid Identity to the caller (dp.rs:641).
- `set_user_password` creates a user record when the Name already names an ACL identity or at least one CP identity exists, and returns false otherwise (dp.rs:650).
- `add_roles` and `remove_roles` resolve the identity against the user records first and the ACL identities second (dp.rs:680).
- The DP action policy hardens six actions to Admin: `GetACLData`, `AddIdentityList`, `RemoveIdentity`, `SetUserLoginPassword`, `AddRolesForIdentity`, `RemoveRolesForIdentity` (dp.rs:734).
- `valid_role` admits `Admin` and `Basic`, `Public` is not an assignable role, and an unknown role answers 600 (dp.rs:753).
- The store's rows are `U<TAB>name<TAB>salt-hex32<TAB>stored-hex32<TAB>roles` and `A<TAB>name<TAB>alias-or-dash<TAB>id-hex32<TAB>roles`, with `-` for an absent alias and unknown roles dropped on load (dp.rs:760).
- `config_from_tsv` skips a malformed line, and a partial parse is the caller's decision (dp.rs:783).
- The base64 decoder tolerates ASCII whitespace anywhere and admits `=` only in the final group's last two slots (dp.rs:864).
- The device ID derives from the root UDN: the dashed-hex UUID's bytes when the UDN is dashed hex, and a stable FNV projection otherwise, so device and control point derive one value from one UDN (upnpsvc.rs:3521).
- An absent or unreadable `dp.tsv` yields an empty ACL, so every protected action answers 606 until the operator provisions the store (upnpsvc.rs:3546).
- `dp_save` writes the store through a temporary file and a rename (upnpsvc.rs:3559).
- A DP nonce is exactly 16 bytes read from `/dev/urandom`, and the earlier unbounded read is the recorded OOM root cause (upnpsvc.rs:3571).
- `GetRolesForAction` answers RoleList with the unconditional roles and an empty RestrictedRoleList, because no role is conditional in this policy (upnpsvc.rs:2471).
- The RoleList argument is space-separated, and each role must be one the device understands (upnpsvc.rs:2645).
- The identity-name reader takes every `<Name>` inside each `<Identity>` element with a minimal scanner (upnpsvc.rs:2656).
- The DP error set mapped to SOAP faults is 600, 606, 701 and 704, and 704 is shared with the WANIPConnection fault `ConnectionSetupFailed` (upnpsvc.rs:3584).

**Carried elsewhere:** the PKCS5 parameters with the union-of-roles login, the identity-must-be-in-ACL rule, the live ACL evaluation, the persistence split with sessions transient, the operator bootstrap through `/etc/ds-lite-punch.acl`, the boundary in front of the engine, the lift as the principal's roles, the containment clauses with the 1024 floor on the v2 face, and the five unauthenticated refusals are in MEMORY, call/0021, call/0023, call/0024 and the results files of plan/0008. The store's row format is also on the component's own pages (`docs/operators/install.md:149`, `deploy/ds-lite-punch.env:23`).

### The service descriptions and the transcribed tables

- The mapping description's stored length is bounded at 64 bytes, because the format is application-defined with no spec bound and this keeps the persisted index line bounded (upnpsvc.rs:61).
- The automatic external-port choice starts at 1024, and its scan terminates because the lease table caps at a few hundred slots while the port space holds 64512 ports (upnpsvc.rs:58, 2863).
- `parse_desc` drops control characters, because the persisted index holds one tab-separated line per entry and a newline in the label would forge a second row, and it bounds the length (upnpsvc.rs:2952).
- `xml_escape` escapes the five XML metacharacters, and the comment says the mapping description is the one field that needs it because the other emitted fields are numbers or a parsed address (upnpsvc.rs:3114).
- The listing fragment is carried in a CDATA section inside `<NewPortListing>`, because the reference client collects the listing from that element's character data alone (upnpsvc.rs:3878).
- A description cannot break the CDATA section, because `xml_escape` renders `>` as `&gt;`, so the sequence `]]>` cannot occur inside a fragment (upnpsvc.rs:3885).
- The PortListing root names `xmlns:xsi` and an `xsi:schemaLocation` at `http://www.upnp.org/schemas/gw/WANIPConnection-v2.xsd`, a URL that no longer answers, so the spec's own sample is the shape authority (upnpsvc.rs:3871).
- The WANIPConnection:1 and WANCommonInterfaceConfig:1 SCPDs are cribbed from miniupnpd (`netfilter/upnp_desc.c`, BSD) with attribution (upnpsvc.rs:3890, 3971).
- The PPP alias serves the identical SCPD constant, because the WANPPPConnection:1 action set matches for the actions honoured (upnpsvc.rs:3967).
- The WANCommonInterfaceConfig:1 service must appear in the root description, because miniupnpc's `GetValidIGD` marks a device an IGD only when its rootDesc carries it, and one action is answered (upnpsvc.rs:486, 4320).
- The embedded devices get their own derived UDNs from the root UDN (upnpsvc.rs:4326).
- `<URLBase>` is emitted as `http://<lan-ip>:<port>/` (upnpsvc.rs:3759, 3815).
- A Kani gate checks that the published DP SCPD carries the authoritative action names, so the superseded miniupnpd-derived names cannot return (upnpsvc.rs:4125).
- The seven OPTIONAL actions of table 2-10 are absent from the published v2 SCPD, because publishing them would promise a disconnect the ISP-managed line cannot make, and an invocation of one answers 401 (upnpsvc.rs:5748).

**Carried elsewhere:** the 21 actions and 23 state variables of WANIPConnection:2 with five evented, the fourteen REQUIRED actions with their argument tables, the 13 DeviceProtection actions, the superseded placeholder names with its invented argument types, the lease of 0 reading as 604800 on v2, and the lease-remaining rule for a listing query are in the two transcriptions, in MEMORY and in plan/0008.

### Argument parsing and faults

- `xml_tag` returns the text of the first element named exactly `tag`, tolerates whitespace and comments or CDATA around the value, and fails closed at the caller's parse when a comment or CDATA sits inside the value or when same-name elements nest; a real parser is the escalation (upnp.rs:857).
- A CDATA wrapper is unwrapped when it is the whole value, and a span with text outside it is returned whole so the caller's parse rejects it (upnp.rs:941).
- The closer search skips comment spans and CDATA spans, whose contents are not element text (upnp.rs:888).
- `xml_tag` returns nothing when the opening `<` has no `>` (upnp.rs:874).
- A missing `NewLeaseDuration` parses as the maximum, `NewRemoteHost` is accepted and ignored, and `NewEnabled` and the description are descriptive (upnpsvc.rs:2778).
- The wildcard `NewExternalPort` of 0 is admitted for `AddAnyPortMapping` and refused by `AddPortMapping`'s parser, and that flag is the only difference between the two callers (upnpsvc.rs:2749, 2758).
- The range parsers treat the endpoints as an entry filter, so no scan runs over the port span, and a start above the end answers 733 `InconsistentParameters` (upnpsvc.rs:2694).
- `GetListOfPortMappings` accepts `NewProtocol` of `TCP`, `UDP` or `ALL`, and accepts and ignores `NewManage`, because managed entries are not a concept this facade exposes (upnpsvc.rs:2712).
- The range delete collects its target list before it removes anything, and its cost is bounded by the entries table and never by the port span (upnpsvc.rs:1390).
- A contained caller's request is judged before the port is resolved, so a preference below the floor is a request the caller may not make (upnpsvc.rs:1362).
- The containment carries its port floor as a field, because the floor binds the v2 face where a control point can authenticate to lift it, while the caller's-own-address clause binds both faces (upnpsvc.rs:2891).
- The containment covers reads and writes alike, and a lift belongs to the principal, so an authenticated control point reaches the whole table on either face (upnpsvc.rs:2178).
- An entry a contained caller may not see answers 606, and an empty selection answers 730 (upnpsvc.rs:1278, 1403).
- The fault table carries two faults on code 704, WANIPConnection's `ConnectionSetupFailed` and DeviceProtection's `Processing Error` (upnp.rs:565).
- 730 `PortMappingNotFound` and 733 `InconsistentParameters` are WANIPConnection:2's own codes for the range actions, and 731 `ReadOnly` answers a `SetConnectionType` on an auto-configured line (upnp.rs:575).
- Every parse is fallible and no parse panics (upnpsvc.rs:2743).
- The wildcard external port resolves above the floor, which is why `AddAnyPortMapping` admits it (upnpsvc.rs:2904).
- `preferred_port` honours the requested port while another client holds it, and the wildcard is the one request that states no preference (upnpsvc.rs:2922).
- The version 2 lease reading is applied at the dispatch arm, keyed on the SOAPACTION URN's version (upnpsvc.rs:2260).

**Carried elsewhere:** the range refusals 730 and 733, the wildcard's refusal before the facade saw it, the containment's clauses, the `NewManage` semantics, the versioned lease reading, and the DP fault set are in MEMORY and plan/0008.

### The PCP and NAT-PMP codec

| What it governs | Value | Where |
|---|---|---|
| the shared port | 5351 (`PORT`) | pcp.rs:37 |
| the PCP version answered | 2 (`VERSION`) | pcp.rs:40 |
| the longest PCP message | 1100 octets (`MAX_MSG`) | pcp.rs:48 |
| the PCP common header | 24 octets (`HEADER`) | pcp.rs:50 |
| MAP and PEER request data | 36 octets (`OPCODE_DATA`) | pcp.rs:52 |
| the longest PCP mapping lifetime | 600 s (`MAX_LIFETIME`) | pcp.rs:41 |
| NAT-PMP's lifetime | 7200 s (`NPMP_LIFETIME`) | pcp.rs:44 |
| the THIRD_PARTY option length | 16 octets (`OPT_THIRD_PARTY_LEN`) | pcp.rs:114 |
| the FILTER option length | 20 octets (`OPT_FILTER_LEN`) | pcp.rs:115 |
| an error response's lifetime | 30 s for the three short-lifetime codes and 1800 s for the rest | pcp.rs:419 |
| the discovery grace before NETWORK_FAILURE | 10 s (`DISCOVERY_GRACE_S`) | upnpsvc.rs:3099 |

- The PCP result codes the codec names are `UNSUPP_VERSION` 1, `NOT_AUTHORIZED` 2, `MALFORMED_REQUEST` 3, `UNSUPP_OPCODE` 4, `UNSUPP_OPTION` 5, `MALFORMED_OPTION` 6, `NETWORK_FAILURE` 7, `NO_RESOURCES` 8, `UNSUPP_PROTOCOL` 9, `USER_EX_QUOTA` 10, `CANNOT_PROVIDE_EXTERNAL` 11, `ADDRESS_MISMATCH` 12 and `EXCESSIVE_REMOTE_PEERS` 13 (pcp.rs:60).
- The NAT-PMP result codes are `SUCCESS` 0, `UNSUPP_VERSION` 1, `NOT_AUTHORIZED` 2, `NETWORK_FAILURE` 3, `NO_RESOURCES` 4 and `UNSUPP_OPCODE` 5 (pcp.rs:75).
- The PCP opcodes are ANNOUNCE 0, MAP 1 and PEER 2 (pcp.rs:55).
- The PCP option codes read are THIRD_PARTY 1, PREFER_FAILURE 2 and FILTER 3 (pcp.rs:109).
- NAT-PMP's opcodes are the public-address request 0, map UDP 1 and map TCP 2, and a response sets bit 0x80 (pcp.rs:85).
- An IPv4 field must be in the IPv4-mapped IPv6 form with bytes 10 and 11 at 0xff, and a field outside that form reads as the unspecified address, which the caller's comparison refuses (pcp.rs:117).
- The response header is 24 octets: the version, the opcode with bit 0x80, a zero reserved byte, the result code, lifetime, epoch and 12 zero octets (pcp.rs:136).
- A MAP or PEER response body is the request's 12-octet nonce, the protocol byte, three zero octets, the internal port, the assigned external port and the 16-octet mapped address (pcp.rs:146).
- Options are walked with 4-octet padding, a remainder that does not consume the buffer answers `MALFORMED_REQUEST`, and an option whose declared length overruns the buffer answers `MALFORMED_OPTION` (pcp.rs:158).
- An option code with the top bit set is optional and an unknown one is ignored, and an unknown option with the top bit clear is refused with `UNSUPP_OPTION` (pcp.rs:176).
- A THIRD_PARTY or FILTER option with the wrong length answers `MALFORMED_OPTION` (pcp.rs:163).
- A FILTER with prefix length 0 clears the filters already requested and means no filter (pcp.rs:182).
- A response arriving at the server is dropped in silence, which stops a reply loop (pcp.rs:281).
- A datagram under 2 octets is dropped in silence, and a version 2 datagram under 24 octets is dropped in silence (pcp.rs:275, 288).
- The client address is compared against header bytes 8 to 24 (pcp.rs:296).
- A request whose length is not a multiple of 4 octets answers `MALFORMED_REQUEST` (pcp.rs:291).
- An unknown opcode answers `UNSUPP_OPCODE` with the request's opcode echoed (pcp.rs:346).
- A MAP with internal port 0 is the delete form and carries lifetime 0, and internal port 0 with a non-zero lifetime answers `MALFORMED_REQUEST` (pcp.rs:341).
- MAP request offsets are nonce 24 to 36, protocol 36, internal port 40 to 42, suggested external port 42 to 44 and suggested external address 44 to 60, and PEER adds peer port 60 to 62 with peer address 64 to 80 (pcp.rs:321).
- A PEER request needs 24 plus 36 plus 20 octets (pcp.rs:310).
- An ANNOUNCE request's lifetime is ignored on reception (pcp.rs:1000).
- An ANNOUNCE response is the 24-octet header alone with lifetime 0 (pcp.rs:389).
- A PEER response uses the MAP body layout (pcp.rs:375).
- An error response returns the request's own payload cut at 1100 octets and padded to four, and copies the client field into the reserved field so a client can match an answer to a request that did not parse (pcp.rs:395).
- `CANNOT_PROVIDE_EXTERNAL` takes the long error lifetime because the AFTR owns the external port, so a retry answers the same (pcp.rs:425).
- A lifetime request of 0 is the delete form and answers 0, and any other request is capped at the dialect's ceiling (pcp.rs:435).
- The admission outcome maps Granted and Refreshed to `SUCCESS`, UserQuotaExceeded to `USER_EX_QUOTA` and TableFull to `NO_RESOURCES` (pcp.rs:443).
- The shared-port discriminator is the first octet, with 0 for NAT-PMP and 2 for PCP, and any other value is resolved by length: at least 24 octets reads as a PCP version to refuse with `UNSUPP_VERSION`, and under 24 reads as NAT-PMP (pcp.rs:453).
- A NAT-PMP request under 2 octets is dropped in silence, a response-bit opcode is dropped in silence, and a non-zero version answers `UNSUPP_VERSION` (pcp.rs:495).
- A NAT-PMP map request needs 12 octets, with the internal port at 4 to 6, the suggested external port at 6 to 8 and the lifetime at 8 to 12 (pcp.rs:506).
- A NAT-PMP map response is 16 octets: zero, the opcode with the response bit, the result code, epoch, internal port, external port and lifetime (pcp.rs:536).
- A NAT-PMP public-address response is 12 octets: zero, the opcode with the response bit, the result code, epoch and address (pcp.rs:553).
- A NAT-PMP version error is 8 octets with the opcode zeroed, and the result code marks it as an error (pcp.rs:562).
- A NAT-PMP unsupported-opcode response echoes the request with the response bit and code 5, and a request under 12 octets carries the code in the short public-address form (pcp.rs:570).
- An unknown NAT-PMP opcode is refused while a response is dropped in silence (pcp.rs:497).
- The PCP epoch is seconds since the facade's state was created, and a reboot resets it near zero, which tells a PCP client its mappings are gone (upnpsvc.rs:749).
- Discovery in flight means the datagram is dropped, and past the 10 s grace the answer is `NETWORK_FAILURE`, because a client's retransmission is the protocol's recovery (upnpsvc.rs:3097).
- The wait is recorded per bind port, with the second the wait began (upnpsvc.rs:212).
- The per-slot tuple lookup reads memory before the file, which keeps a PCP MAP answerable while the state directory is unwritable (upnpsvc.rs:760).
- Only UDP and TCP are mappings this datapath can hold, and the protocol field is read as sent so admission decides (upnpsvc.rs:3061).
- The listener is one socket on the LAN address, and the caller owns the bind so the service can be exercised off the production port (upnpsvc.rs:1089).
- A request from outside the LAN is refused by an explicit check beside the bind (upnpsvc.rs:1105).
- A PEER is answered with the mapping's own tuple when the operator enabled the opcode, and the filtering is endpoint-independent so nothing is installed (upnpsvc.rs:892, 909).
- THIRD_PARTY is gated on the containment lift, so a caller authenticated over DeviceProtection may map for another host (upnpsvc.rs:934).
- A delete with nothing to delete answers `SUCCESS` with lifetime 0 (upnpsvc.rs:7448).
- NAT-PMP's result codes are translated from the shared admission outcomes, so a NAT-PMP client reads its own numbering (upnpsvc.rs:3084).
- An error answer carries the request's suggested external port and address back (upnpsvc.rs:3072).

**Carried elsewhere:** the result-code divergence with the RFC numbering, the correction that ANNOUNCE carries no tuple, the NAT-PMP version error's shape, FILTER refused with `EXCESSIVE_REMOTE_PEERS`, PREFER_FAILURE's 11, the shared port and the LAN-only bind, the drop-then-retry rule, the fixed 7200 lifetime, the opcode numbering with the response bit, and the epoch value are in the results file of plan/0009 and in MEMORY.

### The collision and supersession rules

- The allocator's probe runs before a fresh allocation and steers around every live tuple the change-data-capture shows, a renewal allocates nothing so it reads nothing, and an unavailable mirror is reported (upnpsvc.rs:619).
- At most one pool-pressure eviction is permitted per Add (upnpsvc.rs:1122).
- A request that names no port has no handle to act on, so another mapping stays untouched (upnpsvc.rs:3214).
- A preferred port is honoured while another client holds it, and the wildcard is the one request that states no preference (upnpsvc.rs:2930).
- A device's flow onto a leased port wins: the probe runs first, the slot moves to a port nothing live holds, the substitution is reported, and the reported port stays the client's label so no event is invented; a PCP client learns the new assigned tuple on its next renewal (upnpsvc.rs:1695, 1768).
- The client-presence reap leaves a static alone, because a client's request is a promise to a device and a device that is gone has nothing to be promised (upnpsvc.rs:1703).
- The lease-policy backstop covers the pool-state case, with 24 h of client silence making a UDP grant reapeable and a 7-day sweep catching ghosts (upnpsvc.rs:65, 1870).
- An entry whose bind port is already the new slot is a stale index row to refresh in place (upnpsvc.rs:3202).
- A delete or a specific read resolves the caller's own mapping at that port or answers 714, and the range delete with `NewManage` is the bulk path to another client's entry (upnpsvc.rs:1218).
- The enumeration index addresses the visible list directly, because indexing a list of `(req_ext, proto)` keys and then looking up by those fields renders the earlier entry twice once the key is per client (upnpsvc.rs:1298).
- The cross-protocol supersession measured on 2026-09-20: a PCP lease was torn down two seconds after it was granted because the same client's NAT-PMP leg asked for the same no-preference key of 0, and the loser was the client's own mapping, so a library that sends both protocols loses one mapping per request (upnpsvc.rs:3198).

**Carried elsewhere:** call/0022's per-client port label, call/0027's collision rules with the probe and the steering log line, call/0028's late-collision yield, the client-presence reap that superseded the silence backstop, and the measured two-second loss are in MEMORY, plan/0009 and plan/0010.

### Specification restatements that can go

Each line below restates a transcription that stays available under `docs/upnp-dp1` or `docs/upnp-wip2`, so the collapse can drop it and the reader keeps the source.

- The ceremony parameters and the authenticator MAC input (dp.rs:1), contract at DP-T:120-130.
- The identity field meanings with the 16-octet binary identity and its certificate mapping (dp.rs:150), DP-T:104 and DP-T:111.
- The user record of Salt and STORED with the roles of the Name (dp.rs:165), DP-T:120.
- The pending challenge (dp.rs:183), DP-T:125.
- The role set an action requires with the section 3.1 name (dp.rs:187), DP-T:141.
- SupportedProtocols with the mandated WPS introduction and PKCS5 login (dp.rs:246), DP-T:72.
- The ACL document shape (dp.rs:258), DP-T:99.
- The IdentityList document shape (dp.rs:278), DP-T:99.
- A fresh login challenge from a device-random nonce (dp.rs:290), DP-T:125.
- The PBKDF2 iteration count of 5000 (dp.rs:294), DP-T:121.
- STORED as the first 128 bits of T1 over the password and Name concatenated with Salt (dp.rs:298), DP-T:120.
- The authenticator comparison over STORED and the three bound identifiers (dp.rs:307), DP-T:127.
- The four fault codes with their per-action citations (dp.rs:336), DP-T:134.
- SetupReady and its completion rule (dp.rs:401), DP-T:34.
- GetUserLoginChallenge's known-Name rule with the challenge replacement (dp.rs:407), DP-T:125.
- UserLogin's verification against the challenge's user with the ACL identity rule and the role union (dp.rs:415), DP-T:131.
- UserLogout as a no-op when nothing is logged in (dp.rs:447), DP-T:59.
- AddIdentityList as a union add with the added set returned (dp.rs:633), DP-T:61.
- SetUserLoginPassword setting Stored and Salt (dp.rs:651), DP-T:63.
- AddRolesForIdentity and RemoveRolesForIdentity (dp.rs:680, 698), DP-T:64 and DP-T:65.
- SHA-256 padding, HMAC's 64-byte block, and PBKDF2 with HMAC-SHA-256 (dp.rs:44, 99, 112), textbook algorithm text in FIPS 180-4 and RFC 2104.
- GetUserLoginChallenge's PKCS5-only protocol and its Salt and Challenge outputs (upnpsvc.rs:2412), DP-T:57.
- UserLogin's argument list with no outputs (upnpsvc.rs:2433), DP-T:58.
- UserLogout's empty argument list (upnpsvc.rs:2452), DP-T:59.
- GetAssignedRoles as a space-separated list with Public for an unauthenticated session (upnpsvc.rs:2459), DP-T:55.
- GetACLData's embedded document output (upnpsvc.rs:2514), DP-T:60.
- AddIdentityList's result document (upnpsvc.rs:2524), DP-T:61.
- RemoveIdentity by Name with the 600 for an invalid identity (upnpsvc.rs:2548), DP-T:62.
- SetUserLoginPassword's admin rule with the logged-in user exception (upnpsvc.rs:2566), DP-T:63.
- AddRolesForIdentity and RemoveRolesForIdentity with the unknown-role refusal (upnpsvc.rs:2590), DP-T:64 and DP-T:65.
- The DP SCPD's thirteen actions and their argument tables (upnpsvc.rs:4120), DP-T:43 and the reassembled `<scpd>`.
- The DP state table with SetupReady the one evented variable and `A_ARG_TYPE_Base64` as `bin.base64` (upnpsvc.rs:5804), DP-T:21.
- The 21 v2 actions with 23 state variables and five evented (upnpsvc.rs:3996), W2-T:70 and W2-T:133.
- The fourteen REQUIRED actions of table 2-10 with their argument tables (upnpsvc.rs:5566), W2-T:133.
- Table 2-9's five evented variables with the mapping pair evented together (upnpsvc.rs:5717), W2-T:122.
- The response shapes for the connection control actions (upnpsvc.rs:2220, 2246), the spec's own action sections.
- The range actions' semantics with 730 and 733 (upnpsvc.rs:1390, 2694), the spec's own action sections.
- The PortListing fragment with the remaining lease of a query (upnpsvc.rs:1422), W2-T:375.
- The v2 lease reading of 0 as 604800 (upnpsvc.rs:2944), W2-T:59.
- The action wire names and the fault code and description pairs (upnp.rs:604, 1109), the spec's own tables.

### Load-bearing for correctness

| The shape | What a different shape breaks | Where |
|---|---|---|
| the PCP response header of 24 octets | a client reads the lifetime or the epoch from another field | pcp.rs:136 |
| the MAP and PEER body order of nonce, protocol, reserved, internal port, assigned external port, mapped address | every client's parse of an answer shifts by one field | pcp.rs:146 |
| the request offsets, nonce 24 to 36, protocol 36, internal port 40 to 42, suggested port 42 to 44, suggested address 44 to 60, peer port 60 to 62, peer address 64 to 80 | the datapath maps a flow the client never named | pcp.rs:321 |
| the NAT-PMP map response of 16 octets | a client reads the lifetime from the wrong bytes and refreshes at the wrong time | pcp.rs:536 |
| the NAT-PMP version error of 8 octets with the opcode zeroed | a legacy client reads the result code from the wrong position and retries indefinitely | pcp.rs:562 |
| the shared-port discriminator by first octet and length | a future PCP version is answered as a NAT-PMP version error, or a NAT-PMP request is parsed as PCP | pcp.rs:453 |
| the error lifetime of 30 s and 1800 s | a client retries at the wrong cadence against a structural refusal | pcp.rs:419 |
| the client field copied into the error response's reserved bytes | a client cannot match an answer to its own request | pcp.rs:410 |
| the IPv4-mapped IPv6 form with bytes 10 and 11 at 0xff | the client check reads an address that never matches the source, so every request answers `ADDRESS_MISMATCH` | pcp.rs:117 |
| the PCP version of 2 with the multiple-of-four length rule | a valid request is refused, or a malformed one is parsed | pcp.rs:40, 291 |
| the delete form of internal port 0 with lifetime 0 | a delete carrying a non-zero lifetime removes a mapping the client meant to create | pcp.rs:341 |
| the authenticator MAC input order of Challenge, DeviceID and ControlPointID | every login fails, and a reordered binding is weaker than the spec's | dp.rs:307 |
| the PBKDF2 salt of Name concatenated with Salt at 5000 iterations | a stored password that no control point can reproduce | dp.rs:298 |
| the device ID derivation from the root UDN | device and control point derive different identifiers and the ceremony never binds | upnpsvc.rs:3521 |
| the all-zero ID marking a user identity | the login tries the all-zero identifier as a ControlPointID | dp.rs:483 |
| the two-level role map with an unknown role satisfying nothing | a widened match grants access on a role the device does not know | dp.rs:174 |
| the session idle ceiling of 1800 s with the five-failure limit | an expired session keeps its roles, or the failure backstop never fires | dp.rs:341, 345 |
| the base64 padding rule | a malformed Stored, Salt, Challenge or Authenticator is accepted | dp.rs:864 |
| `xml_escape`'s five metacharacters | a description injects markup into the SOAP response, and the CDATA section closes early | upnpsvc.rs:3114, 3885 |
| `parse_desc`'s control-character strip with the 64-byte bound | a label forges a second line in the persisted index | upnpsvc.rs:2952 |
| `xml_tag`'s fail-closed corners with the whole-value CDATA rule | a partial value is accepted where the parse should refuse it | upnp.rs:857, 941 |
| the case-sensitive action names with the last-`#` rule | dispatch answers a different action | upnp.rs:631 |
| the `ns` token's 1 to 4 byte bound with the `<ns>-SOAPACTION` spelling | an M-POST action goes unresolved and the request answers 401 | upnp.rs:471, 506 |
| the eventKey start of 0, its advance on delivery alone, and its 32-bit wrap | a subscriber enforcing monotonicity drops the first change event | upnpsvc.rs:1531, 1641 |
| the rule that a re-key leaves SystemUpdateID alone | an event invents a port change the client cannot see | upnpsvc.rs:1593 |
| the order that signals a mapping change before persisting the index | a subscriber reads the index and the event disagrees | upnpsvc.rs:740 |
| the SSDP fd flags with the by-index interface join | a blocking fd wedges the io driver, and an address-based join hears no br-lan multicast | upnpsvc.rs:3366, 3412 |
| the containment check before port resolution | a substitution silently widens a contained caller's request | upnpsvc.rs:1362 |
| the wildcard admitted for `AddAnyPortMapping` and refused for `AddPortMapping` | a legacy client sends a request the v1 action never accepted | upnpsvc.rs:2749 |
| the range actions' 730 on empty and 733 on crossed | a control point's enumeration loop never terminates, or a malformed range is accepted | upnpsvc.rs:2694, 1403 |
| the lease reading of 0 as 604800 on v2 and as permanent on v1 | a v2 client gets a static mapping where the spec reads the maximum | upnpsvc.rs:2944, 2260 |
| the one-eviction-per-Add limit with the probe before allocation | a retry loop evicts a working mapping, or a live punch is shared | upnpsvc.rs:1122, 619 |

### Two findings, and they are defects

**The DeviceProtection XML builders interpolate control-point text with no escaping.**
`xml_escape` has two call sites, `upnpsvc.rs:1476` and `upnpsvc.rs:3148`, and
both pass `e.desc`, the mapping description. `dp::acl_xml` at `dp.rs:259` and
`dp::identity_list_xml` at `dp.rs:282` interpolate the identity name, the alias
and each role. The name arrives from the wire: `dp_identity_names` at
`upnpsvc.rs:2659` reads the `<Name>` text of each `<Identity>`,
`dp_add_identities` at `upnpsvc.rs:2543` stores it, and `dp_get_acl` at
`upnpsvc.rs:2521` returns `dp::acl_xml` inside the SOAP body, with GetACLData
behind the Admin gate. The role path is safe, because `valid_role` at `dp.rs:753`
admits `Admin` and `Basic` alone. Verified: the two call sites, the two
interpolation sites and the wire reader were read in the source at `65acff8`,
so the line at `upnpsvc.rs:3114` that says the description is the one field
needing escape is inaccurate for the DeviceProtection documents. Not verified:
no request was driven against a live facade, the alias arrives from the
operator's `dp.tsv`, and the effect of a malformed document on a control point
was not measured.

**The dispatch-completeness proof claims totality and the harness checks seven actions.**
`upnp.rs:1719` says "every action's wire name parses back to the same action (the
dispatch table is total over the enum)", and the loop at `upnp.rs:1720` lists
seven variants: `GetExternalIpAddress`, `GetStatusInfo`,
`GetConnectionTypeInfo`, `AddPortMapping`, `DeletePortMapping`,
`GetSpecificPortMappingEntry` and `GetGenericPortMappingEntry`. The enum at
`upnp.rs:563` carries 28 variants. The neighbouring `soap_classify_never_panics`
proof is stronger in shape, because its round-trip assertion sits inside the
`Soap` arm over any 64-byte head. Verified: the comment text, the loop's seven
entries and the variant count were read at `65acff8`. Not verified: `cargo kani`
was not run, so this is a reading of the harness source, and the round-trip for
the twenty-one unchecked names was not established. The correction belongs to
the line's claim, either by widening the list or by narrowing the sentence.

**Disposition, 2026-09-23.** The operator took both in this pass, so neither
waits on a follow-up, and the collapse carried neither.

The sanitising was fixed test-first, and both tests failed on the defect before
the fix landed. One pins that a name carrying a tab and a newline cannot forge a
row in the store the daemon writes and reloads; the other pins that a name
holding markup is escaped in the ACL document and the identity list. The fix
adds `dp::clean_name`, which drops control characters, and calls it where the
name is read off the wire and at the store's two creation points, so a name keys
the same identity on every call. It also shares `xml_escape` with the
DeviceProtection module and applies it to the name and the alias, and corrects
that function's own comment, which named the mapping description as the only
field needing it. 220 tests pass, in `850eda1`.

The proof's claim was corrected to its coverage, and the harness was left as it is:
its comment now says the round trip holds for the seven actions it names and that
the table holds 28, which was counted rather than assumed. Widening the loop to
the whole table stays open as a follow-up, because it is a proof change and this
pass is the comment collapse. The correction is in `ea90ab5`.

## The five modules the first pass missed

Five modules kept comment runs the first pass did not reach: `keepalive.rs`,
`mapping.rs`, `presence.rs`, `carrier.rs` and `forward.rs`. The facts those runs
stated with no other home are here. The line numbers are from the component
worktree at `56294a5`, the tree the collapse read.

### keepalive.rs, the allowlist's policy and its chain

- The two policy objects carry the project prefix because nft object names are
  global to the table, and `ip dslp` is shared with the rest of the datapath
  (keepalive.rs:38).
- The selection chain hooks at prerouting priority -150, the mangle hook after
  conntrack, and that hook is what attaches the policy at all: the same
  statement at a pre-conntrack priority left the entry at the default 60 s on
  this build (keepalive.rs:42, 108).
- The install is guarded by a read of the table listing, because re-adding an
  existing `ct timeout` object is an error under `nft -f` and the whole batch
  would then apply nothing (keepalive.rs:121, 135).
- Teardown deletes the chain first and the two policy objects after it
  (keepalive.rs:123).
- The install re-enters the table block that the named map and the CDC mirror
  already occupy, and it never flushes or deletes, so the rest of the datapath
  stays (keepalive.rs:239).

**Carried elsewhere:** the 5m and 2h4m policy bodies with the RFC 4787 floor and
the RFC 5382 established figure, the `protocol` keyword an object takes against
the selection's `meta l4proto`, the inline address list, the empty allowlist
leaving every flow at the router's own timeouts, and the address as the key with
`ether saddr` unavailable are in MEMORY, call/0025, call/0026 and the results
files of plan/0009.

### mapping.rs, the tuple health machine

- The rotation proofs take a symbolic threshold of 1 through 8, and the unwind
  bounds are 10, 20 and 6 (mapping.rs:144, 165, 183).
- `mark_suspect` moves at most one step, stays in range and resets the silence
  count, and a single server makes it a no-op (mapping.rs:70).

**Carried elsewhere:** the three states with their meanings, the 3-cycle
threshold of about 6 s, the majority vote marking a server suspect, and the
`Instant` that keeps `note_response` out of the proofs are in plan/0004's README
and IMPLEMENTATION.md.

### presence.rs, the presence rule

The rule this module implements is stated in call/0030 in full: the neighbour
table as the instrument, the ICMP echo as a trigger alone, `FAILED` and
`INCOMPLETE` as absence, a probe that cannot run answering present, the
two-miss threshold, and a static mapping that presence never releases. No fact
in these comments is recorded here.

### carrier.rs, the watch over the counter

- The first poll adopts the counter's reading as the baseline, so a counter left
  by an earlier run is not reported as an arrival (carrier.rs:42, 97).

**Carried elsewhere:** the mark's eight bytes with its `@th,64,64` match, the
three-interval window, the alarm firing once with a probe clearing it, and the
from-start form are in call/0033, in the helper the component ships under
`deploy/`, and in the results files of plan/0010.

### forward.rs, the source-preserving forward

- `IP_TRANSPARENT` is 19, the Linux value for the option that lets the bind take
  a foreign source address (forward.rs:11).
- `to_sockaddr_in` writes the port and the address in network byte order, which
  is the order the kernel reads a `sockaddr_in` in (forward.rs:63, 65).

**Carried elsewhere:** the per-datagram `IP_TRANSPARENT` forward with the peer's
source address preserved is in plan/0004's IMPLEMENTATION.md and README.