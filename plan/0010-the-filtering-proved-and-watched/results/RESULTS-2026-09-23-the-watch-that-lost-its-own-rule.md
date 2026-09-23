# The watch that lost its own rule

- Date: 2026-09-23, the finding made on 2026-09-22
- Milestone: plan/0010
- Component: ds-lite-punch. The fix is tag `v0.3.4` at `13a5fc0`, artifact
  `6b2951b56894931d644883df27e22a5f2f80e33a74ac38683438eb4220730fdc`, deployed to
  the router and exercised there
- Ground truth: the `MEMORY.md` entries of these dates win where this file and a
  plan document disagree

## What happened

The watch was armed for a day on 2026-09-21, and it raised its alarm on the
22nd:

```host-lint:ignore
{"event":"carrier-silent","last_probe":1790028849,"waited":2700,"epoch":1790031549}
```

The alarm belonged to the instrument. The counter stood at `packets 10`, frozen
since 22:14:09 UTC, and nothing in the ruleset named `carrier_probe`: the counter
object and the two accept sets had survived while every rule that referenced them
had gone. The helper kept sending: its journal carries six sends after the freeze.
Probes sent by hand from a fresh source port arrived at the WAN and
translated through to the client. The carrier was forwarding.

The rules live in `inet fw4`, a table the router's firewall rebuilds. pbr
provoked rebuilds while the window ran, each logged as `Sending reload signal to
pbr due to firewall action: includes`, at 22:20:37, 22:23:37, 22:38:38, 22:41:38,
00:08:43 and 00:11:43 UTC. `ensure_carrier_probe()` ran at startup only, and
nothing re-converged it.

## The fix, and the three defects it carried

The intent was one change: the watch converges on every poll, and it says so when
a rule had to be put back. The box took three more attempts to accept it, and
each attempt found a defect in the fix itself.

**The rule was not spelled the way nft stores it.** nft lists the rule as
`counter name "carrier_probe"`, quotes included, and the install looked for the
text without them. So the install's search text missed the rule it had stored. Each poll took the
chain for one without the rule and inserted another copy: 39 copies in a few minutes,
120 in the forward chain and 114 in the input chain by the time it was measured.
Fixed in `v0.3.3`: the text is the text the listing carries, and every insert is
read back out of the chain before it is believed. Every copy after the first is
now deleted, which is what cleared the chains the storm had built.

**A no-op counted as a change.** `nft add counter` on a counter that already
exists reports success and changes nothing, and the install counted that success
as a repair. The result was a `carrier-watch-reinstalled` event every five
seconds while no rule moved. Fixed in `v0.3.4`: the counter is created only when
a read says it is absent, and only a real move is announced.

**An unreadable chain was a shrug.** `nft` segfaults intermittently on this box,
41 crashes in its uptime, in `libnftables.so.1.1.0`, and a listing that came back
empty was treated as "nothing to do". That is what hid the first two defects for
as long as it did. Fixed in `v0.3.4`: a chain that cannot be read is an error the
operator sees.

## The proof on the box

`v0.3.4` is deployed to the router, at the release's own bytes (the binary's md5
agrees with the asset), and the router runs it now.

| What was done | What the box showed |
|---|---|
| the service started | one rule in the forward chain, one in the input chain |
| `fw4 reload` | one `carrier-watch-reinstalled` within a poll, and one rule back in each chain |
| three marked datagrams from the vantage | the counter rose by exactly three, with `carrier-probe` events for the rises |

The chain held one rule, the rebuild drew one repair event, and the probes were
counted. The carrier had also moved the mapping's external port twice while this ran,
sitting at 59278 at first and at 59348 later, which is the watch's own first named cause and the reason a
helper must be re-pointed before it is believed.

## Two notes from the deploy

The counter's absolute value is not a probe count. During the diagnosis a
hand-written rule counted every TCP packet to the slot port, so the value carries
that traffic; only a rise matters, and the daemon reports the rises.

The deploy cannot replace the binary while the daemon runs: writing that file is
refused with `Text file busy`. The upgrade page now stops the service first,
which is where that instruction belongs. `/etc/ds-lite-punch.env` also had to be
edited before the restart, because the release that renamed `HOLD` to `KEEPALIVE`
reads a key the router's file did not set, and the upgrade page carries that
rename for an operator.

## What the window did prove

The stranger probe at its four windows and the alarm's own machinery stand, in
their own records. The 24-hour window carries no verdict after 22:14:09 UTC: its
counter was not counting, and one alarm within it was the instrument's.