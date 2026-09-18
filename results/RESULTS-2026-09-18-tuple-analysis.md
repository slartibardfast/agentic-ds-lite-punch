# The uplink's tuple behaviour, read from the daemon's own log

- Date: 2026-09-18
- Question: call/0027's second, still-open one — does the AFTR ever answer one
  external port to two inner tuples? — and its mirror, one inner tuple holding
  two external ports at once
- Milestone: plan/0009, the overnight goal's item (4)
- Tool: `deploy/tuple-analysis.py` (reads the daemon's log on stdin)
- Data: the daemon's own tuple events, which are the only local record of what
  the uplink allocated, since each mapping's external tuple is learned from the
  outside by the observation arm and the facade's slot churn

## The command

```
ssh root@192.168.21.1 'logread | grep -E "\"event\":\"(tuple|observed-tuple|churn|rescue|collision)"' \
  > /tmp/tuples.log
deploy/tuple-analysis.py < /tmp/tuples.log
```

## The window and the sample

```
window: Fri Sep 18 14:53:44 .. Fri Sep 18 22:02:35  (353 events)

=== the sample ===
  distinct inner tuples:    35
  distinct external tuples: 35
  pairs (inner -> external): 83
```

Seven hours and nine minutes, 35 distinct inner tuples, 35 distinct external
tuples, 83 learned pairs. The log's ring buffer reaches back to 03:20; the
first tuple event in it is 14:53.

## One external tuple under more than one inner tuple: not concurrent, twice

Two external tuples were learned by two different inner tuples. Both are
sequential reuse, hours apart:

```
=== one external tuple under more than one inner tuple ===
  37.228.213.83:59205: 2 inner tuples
      Fri Sep 18 18:37:16  192.168.21.138:63465
      ...
      Fri Sep 18 18:42:26  192.168.21.138:63465
      Fri Sep 18 21:39:16  192.168.21.97:50129
      Fri Sep 18 21:44:18  192.168.21.97:50129
      verdict: sequential
  37.228.213.83:59230: 2 inner tuples
      Fri Sep 18 18:52:06  192.168.21.138:63456
      Fri Sep 18 21:39:18  192.168.21.97:53418
      Fri Sep 18 21:44:48  192.168.21.97:53418
      verdict: sequential
```

No external tuple was in two inner tuples' hands at the same time. The
reuses are three hours apart, which is an allocator recycling a port whose
first mapping is long gone.

## The mirror case: one inner tuple under two externals at once — this is real

```
=== one inner tuple under more than one external tuple ===
  192.168.21.138:3074: 3 externals
      Fri Sep 18 18:43:28  37.228.213.83:59220
      Fri Sep 18 18:53:18  37.228.213.83:59343
      Fri Sep 18 18:53:20  37.228.213.83:59220
      Fri Sep 18 18:53:24  37.228.213.83:59211
      verdict: CONCURRENT
```

The console's own port held two external tuples inside a six-second span at
18:53. That is the client-visible split, and it is the case a console scores
as Strict or Moderate. Its cause was identified and fixed the same evening:
three mechanisms pinned the *device's* key, so one game egressed on two
external tuples at once, and call/0014 removed the last of them
(`nft::grant_datapath` installs only the accept rule now). The 59343 entry
shows the second half of the same defect: that external tuple was slot
40001's, confirmed between 18:36 and 18:45, and the device's flow appeared on
it eight minutes later.

## The slot view

Each slot learned the external tuples it held, and every one of them is the
slot's own mapping rather than a device's under it:

```
  slot 40000: 28 events, learned ['37.228.213.83:59278']
  slot 40001: 22 events, learned ['…:59201', '…:59209', '…:59343', '…:59265', '…:59281']
  slot 40002: 14 events, learned ['…:59266', '…:59206', '…:59284']
  slot 40003: 6 events, learned ['…:59211']
  slot 40004: 12 events, learned ['…:59384', '…:59234']
```

Three external tuples appear under both a slot and an inner tuple. All three
are sequential, and the two that involve a console (`.138:3074` on 59211 and
on 59343) are the defect above: the slot had moved on before the device's
flow appeared on its tuple.

## What this settles, and what it does not

- The uplink did not answer one external port to two inner tuples in this
  window. The console's NAT-type failures are therefore not explained by the
  downstream allocating one external port twice; they are explained by the
  local device-key pinning that call/0014 removed. That closes the shape of
  call/0027's second question for the observed hours, and leaves it open as a
  standing property to watch.
- It is an observation over 83 pairs in one 7.2-hour window, not a proof. The
  sample is dominated by two browsers' churn (one inner, one external, twice a
  minute), which is the population that would *show* a concurrent reuse if the
  uplink produced one.
- The soak window widens this in the morning: the same command over the
  overnight log re-runs the analysis with more pairs and no new code.

## The defect this analysis does not fix

Reading the same log for the mirror case shows one inner tuple appearing under
two externals concurrently. That defect's code fix is in (call/0014, the
device-key pin); this file is the evidence that the *analysis* can see it, and
the shape a future regression would take.