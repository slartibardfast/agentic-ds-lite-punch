# Milestone: the carrier's filtering, proved and watched

**Status:** closed 2026-09-23. The watch counts, it puts its own rules back after
a firewall rebuild, and it names the moment it did: a rebuild was followed by one
repair event within a poll and one rule in each chain, and three marked datagrams
raised the counter by three. Getting there found the instrument's own rule lost
to a firewall rebuild, then three defects in the repair. The record is
`RESULTS-2026-09-23-the-watch-that-lost-its-own-rule.md`. Record under
`results/`:
`RESULTS-2026-09-20-stranger-probe.md`,
`RESULTS-2026-09-20-alarm-proof.md`,
`RESULTS-2026-09-20-inbound-translation.md` and
`RESULTS-2026-09-20-slot-datapath-defects.md`, which writes both datapath
defects up in full. The watch is disarmed until the helper runs outside the
line, which is the operator's decision.

The line's promise is one property: a mapping the AFTR holds accepts an
unsolicited datagram from a host the mapping was never used toward. That
property is endpoint-independent filtering, and it was measured once, on
2026-08-28/29. Nothing notices if the carrier changes it, and a change is
silent: every local view still shows the mapping alive, and the first symptom
is a client that stops being reachable from outside.

## What this milestone is

The daemon holds a mapping by writing to it, and the AFTR carries the mapping
because it saw the traffic. Both of those read the map from the inside. This
milestone reads it from the outside instead: a stranger sends to the mapping,
and the router says whether the stranger's datagram arrived.

Two products follow. The first is a measurement with a name: the source tuples
that were exercised, and the delays they were exercised at. The second is a
watch, so that a change in the carrier's behaviour becomes an event with a
timestamp rather than a story a client reports days later.

The milestone does not change what the AFTR does, and it does not attempt to
force a filtering policy onto the line. It does not include the lobby case,
which needs the consoles, and it does not include the Kani re-derivation, which
needs a host with more memory. Both remain on the inherited list.

The personas it serves are the ones this host already carries: the operator,
who needs an answer rather than an assumption, and the agent, who needs a claim
verifiable from outside rather than asserted from inside.

## Build sequence

The three groups are the measurement, the watch, and the record. Every task
carries verify and inputs; the mechanical verifies re-run at the gate, and the
decision is attested.

### Confirm the vantage can speak as a stranger {#vantage}

- verify: the recorded vantage answers on its public address, and a datagram
  from it reaches a deliberately opened mapping on the router, with the arrival
  visible in the router's WAN capture for that mapping's inner tuple
- inputs: the vantage reference in MEMORY, the policy route and synthetic
  client technique the 2026-09-18 held-mapping test used, the WAN capture
  command from that run

The vantage's public address is not the AFTR's, so the vantage can be a
stranger to the mapping. Confirm that before anything rests on it, and confirm
the capture path too, because the arrival is the only evidence that counts.

### Measure the filtering with a held mapping {#eif-now}

- verify: a held mapping from a synthetic allowlisted client answers a probe
  from the vantage at 30, 60, 120 and 300 seconds of the client's own silence,
  each arrival pasted from the router's WAN capture, and the results record
  names exactly which source tuples were exercised, whether a distinct source
  port alone or a distinct source address as well
- inputs: the synthetic client, its allowlist entry, its policy route, the
  vantage's probe tool, the `flow_obs` mirror for a cross-check

This is the same shape as the silence acceptance that closed plan/0009, with
one change that is the whole point: the prober is a host the mapping has never
spoken to. Record what was measured. Name the case where the vantage can
present a distinct port but not a distinct address.

### Decide who watches, and how the daemon is told {#watch-design}

- verify: attested call/0033
- inputs: the `#eif-now` record, the daemon's observation arm (`obs.rs`,
  `cdc.rs`), the candidate shapes (a cooperating helper on the vantage, a
  daemon-side recognition of the helper's probe, the helper alone with its
  arrivals read by hand)

The daemon cannot send from a foreign address, so the watcher needs a
cooperating host outside. The decision fixes who sends, who observes, what
happens when the probe is absent, and what the helper's probe looks like on the
wire, because the daemon has to tell a cooperative probe from the traffic of a
stranger. call/0033 names the sender, the observer, the interval, the probe's
wire shape, and the two events the daemon emits.

### Recognise the cooperative probe and report its absence {#watcher}

- depends: #watch-design

- verify: the component's suite covers the recognition and the absence alarm,
  and on the box the daemon logs the arrival of a cooperative probe from a
  foreign source and logs the loss when the configured interval passes with no
  probe
- inputs: the wire shape from `#watch-design`, the component's observation arm
  and configuration surface, the forwarding path a probe's datagram takes

If the decision puts the observation somewhere other than the daemon, this task
is recorded as a skip with its citation and the watcher lives where the
decision says. What the task fixes either way is the outcome: an arrival and an
absence both become timestamped events.

### Prove the alarm without the carrier {#alarm-proof}

- depends: #watcher

- verify: with the helper silent, the daemon reports the loss within the
  configured interval, pasted from the log with timestamps, and the record
  states plainly that the alarm path was exercised while the carrier's
  behaviour was not
- inputs: the same rig, the helper held back by hand, the interval fixed by
  `#watch-design`

The carrier will not lose endpoint independence on request, so this task proves
the half that is provable: that silence produces the alarm. Say so in the
record, in those words, so a later reader cannot mistake it for a measurement
of the carrier.

### Translate an arrival to its client {#inbound-translation}

- verify: a lease's arrival reaches the LAN at the client's own port, pasted
  from a capture on br-lan, and the conntrack entry's reply tuple names that
  port; a revoke removes every translation it made, and its read-back warns
  when one survives
- inputs: the slot ports and the arm's own pin (`src/nft.rs`), the accept-set
  work of the same period, the client ports a lease names

Found by `#eif-now`: the stranger's datagrams reached the router's WAN and
never reached a client. The root cause is commit `4d31181`, which stopped
pinning the client's own tuple for a good reason (call/0014: the pin gave one
game two external tuples) and thereby removed the only thing that mapped an
arrival back to its client, because that mapping had been the pinned flow's
conntrack. The fix translates at ingress instead: a per-slot element in a set
and a map, and a prerouting rule that sends the port's arrivals to the client
that owns them. The client's egress stays its own.

### Stop the lease churn {#lease-churn}

- verify: a lease granted from a named client keeps its accept element, its
  inbound set element and its map element for the length of its lifetime, and
  no revoke names an element another lease owns; a client asking three times in
  a row leaves one live lease, and its elements survive the two surrenders
- inputs: the surrender path's bind port (`revoke_datapath`'s call sites in
  `upnpsvc.rs`), `apply_entry`'s key of `(proto, owner, int_port)`, the
  regression test `apply_entry_keyed_per_client_lets_two_holders_share_a_port`,
  the log window in `results/RESULTS-2026-09-20-slot-datapath-defects.md`

The ingress translation's own proof exposed this, and the write-up in
`results/RESULTS-2026-09-20-slot-datapath-defects.md` carries the root cause:
`apply_entry` refreshes in place on `(proto, owner, int_port)` and otherwise
lets a request surrender the same client's earlier entry at the same
`(req_ext, proto, owner)`. A request that names no port carries `req_ext`
0, which was treated as a handle like any other. Two requests that both ask for
"any port" therefore collided, so a client speaking PCP and NAT-PMP lost one
mapping per pair of requests. Fixed by refusing to supersede when `req_ext` is
0, by giving the boot restore the same datapath a fresh grant installs (the
ingress translation, and no pin), and by dropping the revoke's dead pin delete.
The record carries the failing test's own output and the three on-box
verifications.

### Count the probe where the datapath sends it {#watch-forward-path}

- verify: with the watch armed, a marked datagram from the helper raises the
  counter and the daemon logs `carrier-probe`, and the counting rule is present
  in both the input chain and the forward chain; a disarm removes both rules and
  the counter
- inputs: the counting rule's chains (`src/nft.rs`, `CARRIER_CHAINS`), the
  ingress translation of `#inbound-translation`, the arrival capture in
  `results/RESULTS-2026-09-21-the-probe-the-translation-hid.md`

Found while arming the watch on 2026-09-21: the counter stayed at zero while the
marked datagram arrived at the slot port, and the reason is this milestone's own
ingress translation. That translation sends a slot port's arrival to its client,
which makes the packet forwarded traffic, so a counting rule in the input chain
alone never sees it. The rule now goes into both paths, because which one
applies belongs to the datapath rather than to the probe, and the test that pins
it was shown failing against the input-only shape before the fix was restored.

### Record the measurement and the watch {#record}

- depends: #eif-now, #alarm-proof

- verify: the results file and the MEMORY entry exist, the design decision of
  `#watch-design` is accepted, and the reference sweep resolves every reference
  in the new records
- inputs: the arrivals, the log excerpts, the vantage and interval used

## Verification

The milestone's mechanical checks are the repository's own sweep (`validate`,
`prose`, `refs --check`, `tasks --check`, `book --check`, `software --check`) at
every gate. The two checks this work adds are the arrival capture at the
recorded delays from a foreign source, and the alarm log with its timestamps
after a deliberately silent helper. The code change rides the component's own
lane, so the artifact hash is re-derived rather than assumed, and the record is
bumped to the pin that carries the watcher.

## Rollout

The stages are observable one at a time, and the first two need no deployment.

1. **By hand.** The measurement runs as a scripted experiment, with the
   arrival read from the capture. Nothing on the router changes.
2. **On a schedule, still observed by hand.** The helper probes on its
   interval, and the arrivals are read from the mirror. This is where the
   interval's cost is measured, in packets per hour.
3. **The daemon's half.** The recognition and the alarm deploy from a lane run,
   with the artifact hash re-derived and checked against the record, and the
   previous build parked as the deploy procedure already does.
4. **The alarm's voice.** Whether a loss reaches a person, and how, is a
   question this milestone deliberately leaves open; the log line ships when
   the daemon's half lands, and nothing louder does.

The revert path is the parked build plus stopping the helper, and both are
independent of the router's ruleset.

## Open questions

- Whether the carrier's filtering survives a new session, a line re-provision
  and an AFTR restart, which a longer campaign would measure.
- What detection delay is worth what probe cost, since the interval sets both.
- Whether the daemon should answer the probe, so the helper can confirm the
  round trip from its own side without reading the router.
- Whether any external host may serve as the helper, or only the recorded
  vantage.
- Whether a loss should also raise the LAN-side signal the hold already uses,
  which needs a decision the hold's own record does not yet cover.

## Results home

Records land under `results/` in this room. The arrival captures and the alarm
log excerpts are pasted into them, and the raw captures stay on the router
under the path the earlier runs established, with a checksum manifest and a
mirrored copy on the workstation.