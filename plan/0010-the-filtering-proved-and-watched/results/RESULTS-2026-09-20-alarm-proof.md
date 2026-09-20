# The watch counts the helper's probe, and silence raises the alarm

- Date: 2026-09-20
- Milestone: plan/0010 (the carrier's filtering, proved and watched), the tasks
  `#watcher` and `#alarm-proof`
- Component: `ds-lite-punch`, pin `0c7085ab`, binary on the router `33091964`
- Ground truth: `MEMORY.md` entries of this date win where this file and a plan
  document disagree

## What was built, and what the lane said

The decision is call/0033. The daemon gained a named `nft` counter
(`carrier_probe`), a non-terminating rule that counts the helper's mark at the
start of the transport payload, a poll that turns the counter's readings into
two events, four configuration flags, and the init-script surface that carries
them. The helper ships as `deploy/carrier-probe.py`, and it binds a fixed
source port.

The component's suite is now 205 tests, one ignored, and the lane's run on the
pin that deployed is green with the same count:

```host-lint:ignore
test result: ok. 205 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out; finished in 10.49s
artifact = target/x86_64-unknown-linux-musl/release/ds-lite-punch 33091964d00f442b911e208f1eeba84bb1c9a288acd61b982df85772d26743a8
```

The downloaded artifact hashed to that same value, the router was installed
from those bytes after the check, and the previous build is parked as
`/root/ds-lite-punch.prev-86ee70fe` beside the one before it.

## The defect the proof found

The first deployment counted nothing. The marked datagram arrived at the slot
port and the counter stayed at zero:

```host-lint:ignore
12:30:43.415611 IP 170.9.238.141.41000 > 192.168.0.21.40000: UDP, length 16
packets 0 bytes 0
```

The rule had been appended to fw4's input chain, and fw4's own accept rules for
the same ports sit earlier in it, so a packet they accept never reaches a later
rule. The reading is exact: `nft -a list chain inet fw4 input` put the accepts
at handles 15511 and 15512 and the counting rule at 15514.

The fix installs the rule with `insert` instead of `add`, so the count happens
ahead of every decision while the rule still terminates nothing. The test that
pins it was shown failing against the pre-fix shape before the fix was
restored:

```host-lint:ignore
assertion `left == right` failed: an appended rule is never evaluated past an accept: ["add", "rule", "inet", "fw4", "input", "iifname \"eth1\" udp dport @dslp_ports_udp @th,64,64 0x64736c702d707262 counter name carrier_probe"]
  left: "add"
 right: "insert"
```

**A fragility worth knowing.** The install is idempotent by the rule's text, so
a box that already carries the misplaced rule keeps it: the check finds the
text and adds nothing. This router needed one hand delete
(`nft delete rule inet fw4 input handle 15514`) before the restart, after which
the daemon inserted its own at the head. A fresh box gets the placement right
on the first install.

## The proof

The watch was armed at a twenty second interval with three misses, so the alarm
window is sixty seconds instead of the production forty-five minutes.

The helper sent one marked datagram to the daemon's own slot tuple, at the
address and port the log names. The daemon recorded the arrival:

```host-lint:ignore
SENT source-port 41000 -> 37.228.213.83:59278 at 1789907856
{"event":"carrier-probe","count":1,"epoch":1789907858}
packets 1 bytes 44
```

Then nothing was sent, and the alarm came when the arithmetic says it should,
with the last probe's epoch in it:

```host-lint:ignore
{"event":"carrier-silent","last_probe":1789907858,"waited":60,"epoch":1789907918}
```

The window arithmetic is the whole point of the reading: the probe's epoch plus
three intervals of twenty seconds is `1789907918`, and the event carries
exactly that epoch. Nothing else in the daemon could have produced it.

The alarm also has a from-start form, exercised by the first, pre-fix
deployment, where no probe had ever been seen:

```host-lint:ignore
{"event":"carrier-silent","last_probe":null,"waited":60,"epoch":1789907423}
```

## What this proves, and what it does not

Proven: a marked datagram from a foreign address is counted by the datapath, the
daemon names it, and a silence of three intervals raises one dated event that
clears when a probe returns. Every step of the alarm path ran on the box.

Not proven, and not provisional: the carrier's filtering was not exercised.
The probe arrived, and the alarm was raised by withholding it. That is the
shape call/0033 and this milestone's `#alarm-proof` task ask for, and the
record says so rather than implying a carrier measurement.

## State after the proof

The watch is off (`CARRIER_PROBE=0` in the router's env file, with the arming
line documented beside it), the counter and the rule are removed, and the
binary stays the watcher build, because that build is what the record pins.
Arming the watch obliges the helper to run on a host outside the line, and a
helper that stops and a carrier that stops look the same to a counter: the
operator's decision is whether the vantage runs the helper as a service.