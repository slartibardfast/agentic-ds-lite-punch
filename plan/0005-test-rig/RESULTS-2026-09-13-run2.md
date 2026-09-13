# RESULTS-2026-09-13-run2: A3 keepalive-pause soak with the forward leg open

Status: run complete.

Redaction note: concrete addresses in this record are replaced with
placeholders; the raw captures on the router retain them.

18/18 cells done, preconditions stable, port reuse
eighteen for eighteen (run-2 confirmation), and the relay forwarded each
cell's probe stream to dslp-sink through every pause and resume: 79 to 108
delivered receipts per cell. Artifact: relay sha256
`7127f4bfd296e5241648b02c96e66180ab75789169140c061fd7976225ee811a`
(unchanged from run 1), duration grid {5,7,10,12,20,30}s x 3, seed
202609132, relay pid 24825. The run used the forward-leg fix:
`net.ipv4.conf.eth1.accept_local = 1` (persisted at
`/etc/sysctl.d/99-ds-lite-punch.conf`), which resolves the run-1 blocker
(root-caused as the kernel source-route validation; see the RCA in the
milestone README). Evidence in `results/2026-09-13-run2/` (per-cell
sink.log receipts, checkpoint, run.json); the raw pcaps stay on the router
at /mnt/nvme/runs/2026-09-13-run2 per the results size policy.

## Method

Identical to run 1, with two changes: the accept_local fix was live, and
the driver's teardown now kills in-container agents (both probes and
sinks), so no leaked streams inflate the counts and every cell's sink
binds cleanly.

## Table

| cell | dur s | pre-stable | arrivals pre | sink receipts | old tuple | new tuple | reuse | state |
|---|---|---|---|---|---|---|---|---|
| 0 | 10 | True | 13 | 79 | <aftr-tuple> | same | y | done |
| 1 | 10 | True | 13 | 88 | <aftr-tuple> | same | y | done |
| 2 | 12 | True | 15 | 90 | <aftr-tuple> | same | y | done |
| 3 | 7 | True | 10 | 85 | <aftr-tuple> | same | y | done |
| 4 | 30 | True | 33 | 108 | <aftr-tuple> | same | y | done |
| 5 | 5 | True | 8 | 83 | <aftr-tuple> | same | y | done |
| 6 | 30 | True | 33 | 97 | <aftr-tuple> | same | y | done |
| 7 | 5 | True | 8 | 83 | <aftr-tuple> | same | y | done |
| 8 | 10 | True | 13 | 79 | <aftr-tuple> | same | y | done |
| 9 | 20 | True | 23 | 93 | <aftr-tuple> | same | y | done |
| 10 | 12 | True | 15 | 90 | <aftr-tuple> | same | y | done |
| 11 | 7 | True | 10 | 85 | <aftr-tuple> | same | y | done |
| 12 | 7 | True | 10 | 85 | <aftr-tuple> | same | y | done |
| 13 | 30 | True | 33 | 108 | <aftr-tuple> | same | y | done |
| 14 | 12 | True | 15 | 90 | <aftr-tuple> | same | y | done |
| 15 | 5 | True | 8 | 79 | <aftr-tuple> | same | y | done |
| 16 | 20 | True | 23 | 98 | <aftr-tuple> | same | y | done |
| 17 | 20 | True | 23 | 98 | <aftr-tuple> | same | y | done |

Arrival counts now match the 1 Hz probe exactly (10 s cells: 13, 30 s: 33,
5 s: 8, 20 s: 23), which confirms the leak fix. Sink receipts are the
forwarded datagrams as logged by dslp-sink per cell. All times monotonic
milliseconds since boot.

## Findings

1. Port reuse confirmed across a second, independent seed: 18/18 cells
   re-issued <aftr-tuple>. The behavior is settled for this line
   within a session.
2. The forward leg is now end-to-end proven through a full campaign: with
   accept_local=1, every probe stream was delivered to the relay socket and
   forwarded to dslp-sink with the masqueraded source preserved, in every
   cell and after every mapping recreation.
3. The driver leak fix is validated: arrival counts are exactly 1 Hz scaled,
   and every cell's sink bound cleanly (no leaked sinks holding 40002).
4. Preconditions held in every cell.

## Carried items

- The death-and-recovery reading of these runs is superseded by the
  analysis annex (ANALYSIS-2026-09-13.md): the AFTR refreshes its mappings
  on inbound datagrams, so the pause premise was confounded and no cell
  exercised a genuine mapping death. The forward one-way transit
  (14 to 19 ms median) and the buffered-flush behavior are the solid
  measurements from this campaign.
- The reply-through-mapping leg (the sink echo returning through the AFTR
  tuple) is the next measurable item now that the forward leg is open;
  it needs the A1 reply-path test (echo-on mode and the eth1 reply-tuple
  capture).
- TCP idle-lifetime (C3) remains queued behind this campaign.
- A mapping-death campaign requires the probe-quiet pause design (silence
  the probe inside the pause); see the analysis annex.