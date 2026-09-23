# The watch that lost its own rule

- Date: 2026-09-23
- Milestone: plan/0010, found while reading the armed window a day earlier
- Component: ds-lite-punch, tag `v0.3.2` at `ac66c716`, artifact
  `ac2693ef59ae4b81102abbdbb23c69b49ba67ca4d2bc901f9170a9520021d009`
- Ground truth: the `MEMORY.md` entries of these dates win where this file and a
  plan document disagree

## What happened

The watch was armed for a day on 2026-09-21. Its counter froze at 22:14:09 UTC
on the 22nd, and at 22:59:09 UTC it raised its alarm:

```host-lint:ignore
{"event":"carrier-silent","last_probe":1790028849,"waited":2700,"epoch":1790031549}
```

The helper had not stopped. Its journal carried six sends after the freeze, one
every 900 seconds, and the tuple it named was the one the carrier held.

## The alarm belonged to the instrument

The counter stood still:

```host-lint:ignore
counter carrier_probe {
        packets 10 bytes 440
}
```

Nothing in the ruleset named the counter, and the two accept sets that sat beside
it in the firewall's tables were absent as well. The counter object and the sets
themselves had survived, which is what made the reading look unchanged.

The carrier was still forwarding. Probes sent by hand from a fresh source port
arrived at the WAN and translated through to the client, which is the whole path
the watch exists to measure:

```host-lint:ignore
170.9.238.141.41060 > 192.168.0.21.40000: UDP, length 16     # eth1, the WAN
170.9.238.141.41070 > 192.168.21.12.40002: UDP, length 16    # br-lan, the client
```

## The cause

The counting rules are inserted into `inet fw4`, a table the router's firewall
rebuilds. pbr provoked rebuilds while the window ran, each one logged as
`Sending reload signal to pbr due to firewall action: includes`, at 22:20:37,
22:23:37, 22:38:38, 22:41:38, 00:08:43 and 00:11:43 UTC. A rebuild takes the
rules the daemon inserted and leaves the counter object in place.

`ensure_carrier_probe()` ran at startup only, and nothing re-converged it. The watch read a plausible number for two and a half hours and then reported
a silence that was its own.

## The fix, in v0.3.2

The watch converges on every poll. It installs its rules when a chain does not
carry them, and replaces any older variant that names the counter, so a rule lost
to a rebuild is back before the next interval closes. The reading the convergence
acts on is pure and tested, `carrier_probe_chain_state`, with the wipe as the
case where the chain carries the object and no rule names it.

A repair is reported, because the counter cannot show it:

```host-lint:ignore
{"event":"carrier-watch-reinstalled","counter":"carrier_probe","epoch":...}
```

That event is in the manual page's LOG EVENTS and in the operator pages, so an
alarm raised before a repair can be read as the instrument's rather than the
carrier's.

## The proof that is owed

The on-box reproduction: reload the router's firewall, watch the daemon put its
rules back within one poll, then send a marked probe from the vantage and watch
the counter rise. It is owed because the deploy writes the router's own
configuration, which this session's policy holds for the operator's approval. The
router still runs 0.1.5 with the rules missing, which is exactly the state the
fix addresses, so the reproduction is one deploy away, and this record is the
undertaking rather than a claim that it ran.

## What the window did prove

The stranger probe at its four windows and the alarm's own machinery stand, in
their own records. The 24-hour window carries no verdict after 22:14:09 UTC: its
counter was not counting, and one alarm within it was the instrument's.