# The daemon over seventeen hours: flat, and no state write failed

- Date: 2026-09-19
- Milestone: plan/0009, the overnight goal's item (3)
- Component: `ds-lite-punch`, the binary running since 2026-09-18 21:57:59 on
  the test router (pid 4496). The pin has moved since, but this window attests
  the binary that was running, not the current pin.
- Ground truth: `MEMORY.md` of these dates wins where this file and a plan
  document disagree

## The window

The sampler writes one line a minute into
`/mnt/nvme/captures/overnight/soak.log`:

```
before 1789768700 rss=1136 fds=13 ct=881 holds=1     (the first sample after the restart)
after  1789830693 rss=1100 fds=15 ct=616 holds=3
```

That is 61,993 seconds, seventeen hours and thirteen minutes, 1034 samples,
against the six hours the goal asks for. The `before` line is the first sample
taken after the daemon started, so the whole window belongs to one process:
`pgrep` shows pid 4496 throughout, and the daemon's own `start` event is the
one at 21:57:59 that opened the window. The sampler itself began ten minutes
earlier, so its file's first line carries the previous process; the readings
below use the whole file and the difference over those ten minutes is smaller
than the hourly spread it shows.

## Flat, measured

RSS and open descriptors, across the window:

| series | first tenth mean | last tenth mean | min | max |
|---|---|---|---|---|
| rss (kB) | 1269.3 | 1246.1 | 956 | 1464 |
| fds | 14.8 | 15.0 | 3 | 22 |
| holds | 2.7 | 3.0 | 0 | 5 |

The hourly means, which is where a slow leak would show:

```
hour  0: rss mean    1246  fds mean  14.6
hour  1: rss mean    1300  fds mean  15.0
hour  2: rss mean    1228  fds mean  15.0
hour  3: rss mean    1278  fds mean  15.0
hour  4: rss mean    1248  fds mean  15.0
hour  5: rss mean    1330  fds mean  15.0
hour  6: rss mean    1270  fds mean  15.0
hour  7: rss mean    1287  fds mean  15.0
hour  8: rss mean    1220  fds mean  15.0
hour  9: rss mean    1241  fds mean  15.1
hour 10: rss mean    1315  fds mean  15.0
hour 11: rss mean    1313  fds mean  15.0
hour 12: rss mean    1270  fds mean  15.0
hour 13: rss mean    1337  fds mean  15.0
hour 14: rss mean    1261  fds mean  15.0
hour 15: rss mean    1284  fds mean  15.0
hour 16: rss mean    1222  fds mean  15.0
hour 17: rss mean    1279  fds mean  15.0
```

RSS moves inside a band of about a hundred kilobytes across the hourly means,
with no direction over seventeen hours, and it ends lower than it began. Descriptors sit
at fifteen, which is the daemon's sockets and the slot sockets it holds; the
extremes of three and twenty-two are the moments the table emptied and the
moments the arm held several rescued tuples, and the hourly means show they
are excursions rather than a trend. The conntrack column (not a daemon
resource) moved between 212 and 3579 entries as the household's traffic
changed, and carries no signal about the daemon.

## No state write failed

```
warns from the running daemon:  0
state-write failures in the log: none
```

The 659 `shadow keepalive ... Operation not permitted` lines in the log all
belong to earlier daemons (pids 3026, 31093 and 32114; the last of them at
21:57:53, six seconds before this window opened). None is from pid 4496, and
pid 4496 logged no warning of any kind in seventeen hours. That attribution is
itself one of this run's findings: a warning has to be credited to the process
that emitted it before it is called a defect of the running build.

The daemon was working the whole time, which is what makes the flatness
interesting:

```
rescue events:    833
churn events:      13
gc freed events:   3
collision events:  2
```

## What this window does not show

- The window contains the acceptance work of the same night: two PCP leases
  from a container, the collision that moved one of them, and the `nft`
  experiments in scratch tables. None of those restarted the daemon and none
  touched its persisted state, and the sampler's four series carry no step at
  any of them.
- It attests the running binary, not the pin. Three fixes landed after it
  started (a static port the collision rule may not move, and two passes at
  the inbound accept), and a fourth deploy would end the window rather than
  extend it.
- Two accept rules from earlier daemons disappeared from `fw4`'s input chain
  during the window and the log does not say what removed them. It is
  recorded as unexplained, and the set-based fix in the component makes the
  question moot by keeping the accept in a set whose membership the daemon
  reconciles.