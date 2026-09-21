# The probe the translation hid

- Date: 2026-09-21
- Milestone: plan/0010, the task `#watch-forward-path`, found while arming the
  watch for its authorized day
- Component: `ds-lite-punch`, pin `6a786ad2` carries the fix; the released
  build on the router is still `ddfe3903`
- Ground truth: `MEMORY.md` entries of this date win where this file and a plan
  document disagree

## What happened

Arming the watch exposed a defect in the watch itself. The helper sent its
marked datagram, the datagram arrived at the router's WAN, and the daemon's
counter stayed at zero: no `carrier-probe` event, and a counter reading of
`packets 0 bytes 0`.

## The evidence

The arrival is on eth1, and the counter did not move:

```host-lint:ignore
19:06:01.870591 IP 170.9.238.141.41001 > 192.168.0.21.40000: UDP, length 16
packets 0 bytes 0
```

The rule was present, first in the chain, inserted ahead of the accepts, with
the mark and the counter, and the port was in the set:

```host-lint:ignore
3:              type filter hook input priority filter; policy drop;
4:              iifname "eth1" udp dport @dslp_ports_udp @th,64,64 0x64736c702d707262 counter name "carrier_probe" # handle 17660
5:              iifname "eth1" udp dport 40000 accept comment "dslitepunch" # handle 17656
elements = { 40000 }
```

## The cause

This milestone's own ingress translation. `#inbound-translation` made an
arrival at a slot port translate to its client, which turns the packet into
forwarded traffic: it traverses the forward hook and never reaches the input
chain where the counting rule lived. The rule and the translation were each
correct on their own, and the second one moved the packet out from under the
first.

## The fix

`src/nft.rs` installs the counting rule in both paths
(`CARRIER_CHAINS = ["input", "forward"]`), each with `insert` and each
non-terminating, because which path applies belongs to the datapath and not to
the probe. Pin `6a786ad2`, 212 tests. The test was shown failing against the
input-only shape before the fix was restored:
`assertion failed: CARRIER_CHAINS.contains(&"forward")`.

## What the arming proved, and what it did not

Proven on the router: `{"event":"carrier-watch","counter":"carrier_probe",
"interval":900,"misses":3,"poll":5}` after the restart, with the counter and the
rule installed and the env change backed up at
`/etc/ds-lite-punch.env.pre-watch`. Proven on the vantage: the helper runs under
systemd and sends on its interval,
`SENT source-port 41000 -> 37.228.213.83:59278 at 1790017476`.

Not proven, and that is the defect above: a counted probe. The watch was
disarmed so it could not raise a `carrier-silent` about the carrier while its
own observation point was broken.

## Two smaller defects on the way

- The disarm unit failed to load. `date -u +%FT%TZ` inside its `ExecStart` is
  read by systemd as unit specifiers, and the whole unit was refused with
  "Invalid slot". The line formats no date now, and the journal timestamps it.
- The tuple in the helper's `ExecStart` must be read *after* the daemon
  restarts, not before. The first attempt armed the router, restarted the
  daemon, and pointed the helper at a tuple read before that restart. The tuple
  was re-learned identically (`59278`), so the mistake cost nothing, and the
  ordering is the lesson.

## The window's state

Armed and counting, on both boxes. The router runs the released build
`a452cf38…`, `CARRIER_PROBE=1` with a 900 s interval, and `{"event":"carrier-watch"}`
logged at 20:40:54. The vantage runs the helper under systemd, and its disarm
timer is active with `NEXT Tue 2026-09-22 19:44:05 UTC`; the router half's disarm
is a dated cron entry at the same moment, so the window closes on both sides. The
tuple the helper names is the one the daemon reported after the restart that
installed this build.

The final reading, with nothing installed by hand: the counter at
`packets 3 bytes 132` and the daemon's own log line
`{"event":"carrier-probe","count":3,"epoch":1790023284}`.

## The release that carries the fix, and three lessons

**The phase must run against the pin.** Dispatched for the version after the
fix, the phase verified the build of the *pinned* source, and at that moment the
pin named the commit before the fix. Its digest (`a92fcf2f…`) therefore
describes a different source than the tag's own build (`777d5189…`), and the two
numbers mean different things. The ordering that makes them agree: push the fix,
pin it, then dispatch the phase, then apply exactly the bump it authorized. The
component's CI lane confirmed `777d5189…` for that commit independently, which
is how the tag's build was checked without the release lane's help.

**Immutable releases freeze at creation, so assets must ride the creation.** The
Release lane created the release and then uploaded, and GitHub answered

```host-lint:ignore
HTTP 422: Cannot upload assets to an immutable release
```

The lane is a draft-then-publish now (`gh release create --draft`, upload,
`gh release edit --draft=false`), which is what the setting requires.

**The repair of that first attempt burned the tag.** Deleting the asset-less
release succeeded; re-creating it was refused:

```host-lint:ignore
HTTP 422: Validation Failed … tag_name was used by an immutable release
```

So `v0.1.2` carries the correct source and can never carry a release. That is
the setting behaving as designed: a released tag name is spent. The fix ships as
the next version instead, whose lane is the corrected draft-then-publish shape,
and the burned tag is recorded rather than hidden.

## What a working watch needed, in the end

Four defects sat between the watch and its first counted probe, and each one
came out of a measurement rather than a reading.

1. **The rule lived in the input chain only.** The ingress translation sends a
   slot port's arrival to its client, which makes it forwarded traffic, so the
   input hook never sees it. The rule goes into both paths.
2. **The forward rule asked for the slot's port.** The translation rewrites the
   destination to the client's port before that hook, so the port match could
   never hold. The forward rule asks for the mark alone:
   `iifname "eth1" meta l4proto udp @th,64,64 0x64736c702d707262 counter name "carrier_probe"`.
3. **That rule was a syntax error, so it was never installed.** A bare `udp`
   before a payload expression makes nft expect a UDP header field:
   `syntax error, unexpected @, expecting length or checksum or sport or dport`.
   The protocol is named `meta l4proto udp`, and the daemon's stderr carried the
   refusal in a `warn: carrier watch install failed` line that was there to be
   read.
4. **An install that only adds leaves an older build's rule.** Two stale input
   variants and a stale forward rule survived two releases, and a rule that is
   merely different counts nothing. The install now replaces the rules that name
   the counter and are not the one it means.

The end state, read from the box with nothing installed by hand: the input rule
`iifname "eth1" udp dport @dslp_ports_udp @th,64,64 …` and the forward rule
above, both the daemon's own, and a probe that raised the counter to
`packets 3 bytes 132`.