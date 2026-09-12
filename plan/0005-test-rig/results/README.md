# results

Raw captures, logs, and the derived record for each campaign run live here,
committed with the results record (decision: raw travels with the record).
Runs land via `../collect.sh`; the derived `results.md` and the dated results
record are produced by `../analyze.py`.

Size policy: raw material commits while a run stays under about 8 MB. A run
that exceeds that keeps its raw data on the router at `/mnt/nvme/runs/` and
commits only the derived tables and the dated record.