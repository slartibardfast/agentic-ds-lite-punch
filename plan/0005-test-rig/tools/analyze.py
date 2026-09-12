#!/usr/bin/env python3
# analyze.py — host-side parse of one run directory into the results record.
# Reads checkpoint.json (soak) or c3.json (TCP), snapshot.tsv, sink.log,
# probe*.log; emits <run>/results.md (markdown) with the per-cell table and
# summary stats, plus <run>/metrics.json for further use.

import json
import os
import sys


def monotonic_ts_lines(path):
    lines = []
    if not os.path.exists(path):
        return lines
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if not ln or "\t" not in ln:
                continue
            parts = ln.split("\t")
            if len(parts) >= 2:
                lines.append((int(parts[0]), parts[1]))
    return lines


def arrivals(path):
    ev = []
    if not os.path.exists(path):
        return ev
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                j = json.loads(ln)
            except ValueError:
                continue
            ev.append(j)
    return ev


def cells_table(checkpoint):
    rows = []
    for c in checkpoint.get("cells", []):
        dt = c.get("t_resume", 0) - c.get("t0", 0)
        rows.append({
            "cell": c.get("cell"),
            "duration": c.get("duration_s"),
            "pre_stable": c.get("pre_stable"),
            "tuple_old": c.get("tuple_old"),
            "tuple_new": c.get("tuple_new"),
            "reuse": c.get("tuple_new") == c.get("tuple_old"),
            "t_repub": c.get("t_repub"),
            "state": c.get("state"),
        })
    return rows


def main():
    run_dir = sys.argv[1]
    ck = json.load(open(os.path.join(run_dir, "checkpoint.json")))
    rows = cells_table(ck)
    reuse = sum(1 for r in rows if r["reuse"])
    out = [
        "# Soak results: " + run_dir,
        "",
        "| cell | dur s | pre-stable | old tuple | new tuple | reuse | t_repub | state |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append("| {cell} | {duration} | {pre_stable} | {tuple_old} | "
                   "{tuple_new} | {reuse} | {t_repub} | {state} |".format(**r))
    out.append("")
    out.append(f"Port-reuse observed in {reuse} of {len(rows)} cells.")
    with open(os.path.join(run_dir, "results.md"), "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()