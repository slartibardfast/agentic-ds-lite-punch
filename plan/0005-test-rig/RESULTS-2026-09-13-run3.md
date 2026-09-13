# RESULTS-2026-09-13-run3: the probe-quiet pause (mapping survival under silence)

Status: run complete.

Redaction note: concrete addresses in this record are replaced with
placeholders; the raw captures on the router retain them.

18/18 cells done, preconditions stable, and the
probe-quiet pause is validated at the packet level: zero packets touched
the relay port in any pause window, from any source, in any direction.
The AFTR mapping survived every silent window including 30 seconds with
no tuple change and a flat recovery. Artifact: relay sha256
`7127f4bfd296e5241648b02c96e66180ab75789169140c061fd7976225ee811a`
(unchanged from runs 1 and 2), duration grid {5,7,10,12,20,30}s x 3,
seed 202609133, relay pid 26152. Evidence in
`results/2026-09-13-run3/` (per-cell sink.log receipts, checkpoint,
run.json, per-cell eth1 pcaps); the raw data stays on the router at
/mnt/nvme/runs/2026-09-13-run3 per the results size policy.

## Method

Run 3 applies the methodology correction from ANALYSIS-2026-09-13: a
probe-quiet pause. At t0 the driver stops the relay (SIGSTOP) and also
kills the in-container probe, so nothing inbound sustains the AFTR
mapping through the window. At t_resume it resumes the relay and
relaunches the probe on the old tuple. With both silent, the mapping can
only survive on the AFTR's own idle timeout: any arrival after resume is
either a continuation of a mapping that never died (survival) or the
re-creation of one that did (death plus re-issue). The distinguishing
observables are the packet silence itself, the tuple, and the recovery
time (first arrival after t_resume), where a death would add the relay's
post-resume keepalive wait on top of the probe cadence.

## Quiet verification

For every cell the eth1 pcap was scanned for ANY packet matching port
40000 whose timestamp falls inside (t0, t_resume]. Result: 0 packets in
all 18 windows. This is stronger than the arrival filter used for the
timing columns (which counts only the vdsl4-masqueraded probe flow): it
also excludes ambient inbound from third parties and outbound traffic
from the stopped relay. The pauses were genuinely silent at the AFTR, so
the inbound-refresh confound of runs 1 and 2 is closed.

## Table

| cell | dur s | pause-arr | pre-tail ms | recov ms | fwd oneway med/max ms | tuple | state |
|---|---|---|---|---|---|---|---|
| 0 | 10 | 0 | 179 | 817 | 17/21 | <aftr-tuple> | done |
| 1 | 12 | 0 | 170 | 822 | 16/21 | <aftr-tuple> | done |
| 2 | 10 | 0 | 175 | 822 | 14/20 | <aftr-tuple> | done |
| 3 | 20 | 0 | 179 | 822 | 17/21 | <aftr-tuple> | done |
| 4 | 12 | 0 | 180 | 817 | 17/20 | <aftr-tuple> | done |
| 5 | 30 | 0 | 179 | 825 | 17/21 | <aftr-tuple> | done |
| 6 | 5 | 0 | 180 | 826 | 16/21 | <aftr-tuple> | done |
| 7 | 30 | 0 | 176 | 816 | 14/19 | <aftr-tuple> | done |
| 8 | 12 | 0 | 179 | 816 | 14/20 | <aftr-tuple> | done |
| 9 | 7 | 0 | 180 | 819 | 17/20 | <aftr-tuple> | done |
| 10 | 20 | 0 | 165 | 820 | 14/19 | <aftr-tuple> | done |
| 11 | 30 | 0 | 173 | 826 | 16/21 | <aftr-tuple> | done |
| 12 | 7 | 0 | 182 | 817 | 14/19 | <aftr-tuple> | done |
| 13 | 5 | 0 | 181 | 821 | 14/23 | <aftr-tuple> | done |
| 14 | 5 | 0 | 175 | 820 | 17/21 | <aftr-tuple> | done |
| 15 | 10 | 0 | 177 | 823 | 14/19 | <aftr-tuple> | done |
| 16 | 7 | 0 | 182 | 820 | 14/18 | <aftr-tuple> | done |
| 17 | 20 | 0 | 177 | 823 | 14/19 | <aftr-tuple> | done |

Recovery summary: n=18, min 816 ms, median 820 ms, max 826 ms. Forward
one-way transit: 14 to 17 ms median, 18 to 23 ms max in every cell (the
buffered-flush echoes of runs 1 and 2, which were the pause-window
datagrams queued at the stopped relay's socket, are absent here by
construction: nothing arrived during the pause to buffer).

## Findings

1. A fully silent mapping survives 30 seconds on this node and session.
   All 18 cells are survival, not death plus re-issue: the tuple is
   unchanged everywhere, and the recovery is a flat 816 to 826 ms, the
   probe-cadence realignment of a stream that was never interrupted at
   the mapping layer. Had any pause exceeded the AFTR's idle timeout, the
   post-resume keepalive would have needed to re-create the mapping
   before the probe's datagrams could transit, which would show as a
   longer and more variable recovery. The observed spread (10 ms across
   18 cells) is the signature of survival.
2. The AFTR's UDP idle timeout on today's node exceeds 30 seconds,
   bounded below but not above by this campaign (the grid tops out at
   30 s). This sits at odds with the recorded figure of 5 to 10 seconds,
   node-dependent, which the relay's 2 s keepalive cadence was built
   around. The difference is either node dependence across the AFTR farm
   or a methodology difference in the original measurement; the record
   now carries both, and the reconciliation is a longer-limit campaign
   (60 s and 120 s silent windows would locate today's true timeout, with
   RFC 6888's 120 s floor as the outer bound worth testing).
3. The probe-quiet design works as intended and is cheap to audit:
   pause-arr 0 in all 18 cells, no instrumentation faults, per-cell
   captures self-contained.
4. The product's safety margin is not harmed by this finding. The relay
   sends keepalives every 2 s, which is correct regardless of whether the
   true timeout is 5 s on some nodes or over 30 s on today's: the cadence
   sits inside the floor. Nothing about the relay's contract changes. The
   one scenario this relaxes is the unmanaged one: a mapping left
   unkeptalived by a crashed relay may outlive a 30 s window on a lenient
   node, which is exactly the case the startup path covers by re-STUNning
   and taking the mapping over.

## Reconciliation with runs 1 and 2

Runs 1 and 2 measured that inbound datagrams refresh the mapping
(RFC 7857 S7 violation; see ANALYSIS-2026-09-13). Run 3 measures that
even with zero traffic the mapping is not idle-expiring within 30 s on
today's node. Together: the mapping is held by outbound keepalives, is
refreshed by any inbound, and does not die quickly under silence. The
death-within-pause reading that originally motivated the A3 matrix is not
reached at these durations; the relay restart events remain the genuine
mapping death plus immediate re-issue evidence on this line.

## Carried items

- Locate the true idle timeout with a longer-limit run (60 s, 120 s
  silent windows), the natural run 4, gated by the same probe-quiet
  design.
- TCP idle-lifetime (C3) remains queued behind the UDP campaign.