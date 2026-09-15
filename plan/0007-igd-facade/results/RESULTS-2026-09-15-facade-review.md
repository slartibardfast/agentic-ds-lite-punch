# RESULTS-2026-09-15-facade-review: the E1-E8 facade review and its fixes

Status: staged for closure. The 17-agent review of the facade increment
found five criticals; all five and the approved suggestions are fixed in
component 34d48c1 (the review commit 24f4e4d plus the kani scoping
commit) and tested at 86 runnable tests, all green.

Live-rig verification carried over from the bringup (build 92ac62cc):
the full upnpc -l walk with the CIF service, Add/Delete datapath grants
and revokes, 8x GENA SUBSCRIBE with flat RSS on the urandom-fix build,
and the OOM RCA recorded 2026-09-14. The walk is re-runnable via
plan/0007-igd-facade/facade-verify.sh.

## The five criticals (fixed)

1. Respawn-restored grants: main's slot loop skips granted leases in
   facade mode; `UpnpFacade::start` re-spawns them and registers the
   JoinHandles (`spawn_restored_grants`) so `delete_mapping` and
   `gc_loop` abort them. The 2026-09-14 socket-leak class was reachable
   through the documented respawn path. Regression:
   `restored_grant_revoke_frees_socket`.
2. The control-plane entry index: one entry per internal
   (proto, client, int_port) tuple via the pure `apply_entry` decision;
   a re-Add that moves a mapping to a new slot tears down the old
   occupant (replace semantics) instead of leaving a stale bind_port.
   Regression:
   `apply_entry_rides_internal_identity_and_replaces_occupant`.
3. SIGTERM: the byebye sleep and `exit(0)` sit inside the signal
   registration guard, so a registration failure no longer
   self-terminates the daemon 150 ms after boot.
4. SSDP bind: `UpnpFacade::start` returns a Result; a bind failure on
   UDP 1900 (or an unowned lan-ip) degrades the facade instead of
   panicking the daemon; the deploy env gained UPNP=0.
5. M-POST parity: `classify` runs the GENA markers on both transports,
   so a quoted action value that fabricates header lines dispatches
   identically on POST and M-POST. The Kani counterexample is closed;
   the proof itself is deferred (call/0019) and the corner is
   unit-pinned by `mpost_post_parity_multiline_corners`.

## Approved suggestions fixed

- GENA initial NOTIFY advances the subscription eventKey, so the first
  change event is 1, never a repeat of 0. Regression:
  `gena_initial_notify_advances_seq`.
- bind_ssdp checks both setsockopt results and fails closed on a failed
  group join.
- parse_callback rejects a residual bracket (the multi-URL CALLBACK
  form) rather than mangling the path.
- xml_tag and find_close skip comment and CDATA spans; a CDATA wrapper
  unwraps only when it is the whole value, never a partial accept.
  Regression: `xml_tag_skips_comments_and_cdata`.
- http_serve continues on accept errors instead of killing the control
  plane.
- persist::snapshot is the single projection (main's inline copy
  deleted) with the respawn-restore contract pinned, and
  seed_external_ip has a fixture test.

## Kani state (deferred, call/0019)

The pre-facade 32 of 32 record stands. On this tree the facade
structural harnesses do not converge under CBMC 0.67.0: three timed-out
runs, 17 min, 10 min, 5 min. `mpost_post_parity` now proofs clean action
text; the multi-line corners are unit-pinned. A full-suite re-derivation
runs on a larger host before any deploy that relies on the Kani receipt.

## Deferred by operator decision (2026-09-15), E6 now superseded

- The E6 PS3 sign-off with the facade live was completed the same day
  against the deployed 34d48c1 build: three games played perfectly, the
  3074/3658 mappings held unrotated through the session, three external
  peers reached the console inbound through the mapping (see
  RESULTS-2026-09-15-ps3-facade.md). This deferred note is superseded.

## Verification

- cargo test: 86 passed, 0 failed, 1 ignored (`miniupnpc_interop`, an
  off-router probe).
- cargo clippy: no warnings added by the review fixes (36 pre-existing).
- The nft datapaths were exercised by the live rig walk (build
  92ac62cc, Add/Delete grants and revokes) and by the unprivileged
  rollback path in the test harness.

Redaction note: rig addresses appear only as the placeholders used in
the recorded results; raw data stays on the router.