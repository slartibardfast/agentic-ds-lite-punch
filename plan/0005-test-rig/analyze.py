#!/usr/bin/env python3
# analyze.py — host-side parse of one run directory into the results record.
# Reads checkpoint.json (soak) or c3.json (TCP), snapshot.tsv, sink.log,
# probe*.log; emits <run>/results.md (markdown) with the per-cell table and
# summary stats, plus <run>/metrics.json for further use.

import json
import os
import subprocess
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


def pcap_arrivals(pcap, btime):
    # Mapping-liveness markers: the eth1 capture's arrivals of the probe
    # flow (src 84.203.115.61 to dst 192.168.0.21:40000). Death = last
    # arrival before the pause; recovery = first arrival after republish.
    # Convert capture (wall) time to the driver's monotonic clock via btime.
    if not os.path.exists(pcap):
        return []
    try:
        out = subprocess.run(
            ["tcpdump", "-r", pcap, "-nn", "-tt",
             "src host 84.203.115.61 and dst port 40000"],
            capture_output=True, text=True, timeout=60).stdout
    except OSError:
        return []
    base = int(btime) * 1000
    hits = []
    for ln in out.splitlines():
        parts = ln.split()
        if not parts:
            continue
        try:
            wall = float(parts[0])
        except ValueError:
            continue
        hits.append(int(wall * 1000) - base)
    return hits


def cells_table(run_dir, checkpoint):
    rows = []
    btime = "0"
    try:
        run = json.load(open(os.path.join(run_dir, "run.json")))
        btime = run.get("btime", "0")
    except OSError:
        pass
    for c in checkpoint.get("cells", []):
        arr = pcap_arrivals(f"{run_dir}/cell-{c.get('cell', 0):02d}/eth1.pcap",
                            btime)
        t0 = c.get("t0") or 0
        t_resume = c.get("t_resume") or 0
        t_repub = c.get("t_repub") or 0
        before = [a for a in arr if a <= t_resume]
        after_pub = [a for a in arr if a > t_repub]
        rows.append({
            "cell": c.get("cell"),
            "duration_s": c.get("duration_s"),
            "arrivals_pre": len(before),
            "t_last_arrival": before[-1] if before else "",
            "t_first_after_repub": after_pub[0] if after_pub else "",
            "pre_stable": c.get("pre_stable"),
            "tuple_old": c.get("tuple_old"),
            "tuple_new": c.get("tuple_new"),
            "port_reuse": "y" if c.get("tuple_new") == c.get("tuple_old") else "-",
            "state": c.get("state"),
        })
    return rows


def main():
    run_dir = sys.argv[1]
    ck = json.load(open(os.path.join(run_dir, "checkpoint.json")))
    rows = cells_table(run_dir, ck)
    reuse = sum(1 for r in rows if r["port_reuse"] == "y")
    out = [
        "# Soak results: " + run_dir,
        "",
        "| cell | dur s | pre | arrivals | last pre | first post-repub | old tuple | new tuple | reuse | state |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append("| {cell} | {duration_s} | {pre_stable} | {arrivals_pre} | "
                   "{t_last_arrival} | {t_first_after_repub} | {tuple_old} | "
                   "{tuple_new} | {port_reuse} | {state} |".format(**r))
    out.append("")
    out.append(f"Port reuse in {reuse} of {len(rows)} cells. All times are "
               "monotonic milliseconds since boot (eth1 arrival markers).")
    with open(os.path.join(run_dir, "results.md"), "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()