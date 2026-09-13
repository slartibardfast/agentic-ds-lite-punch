#!/usr/bin/env python3
# analyze_latency.py — per-cell timing analysis from the raw pcaps and
# sink receipts. Router-side (needs tcpdump). For each cell:
#   death_delay   last delivered arrival after the pause start, minus t0
#                 (the AFTR's effective UDP idle timeout, bounded by the
#                 probe cadence)
#   first_after   first arrival after resume (recovery, boundary t_resume)
#   gap           first_after minus last delivered arrival (delivery gap)
#   survived      arrival stream never stopped (pause shorter than death)
#   oneway        sink receipt recv minus the probe's payload ts (median,
#                 from the cell sink.log forward receipts)
# Usage: analyze_latency.py RUN_DIR

import json
import os
import subprocess
import sys


def median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def mono(wall_ms, btime_ms):
    return wall_ms - btime_ms


def arrivals(pcap, btime_ms):
    if not os.path.exists(pcap):
        return []
    out = subprocess.run(
        ["tcpdump", "-r", pcap, "-nn", "-tt",
         "src host 84.203.115.61 and dst port 40000"],
        capture_output=True, text=True, timeout=120).stdout
    hits = []
    for ln in out.splitlines():
        parts = ln.split()
        if not parts:
            continue
        try:
            wall = float(parts[0])
        except ValueError:
            continue
        hits.append(mono(int(wall * 1000), btime_ms))
    hits.sort()
    return hits


def oneway(cell_sink_log):
    if not os.path.exists(cell_sink_log):
        return []
    deltas = []
    with open(cell_sink_log) as f:
        for ln in f:
            try:
                j = json.loads(ln)
            except ValueError:
                continue
            recv = j.get("recv")
            ts = j.get("payload", {}).get("ts")
            if recv and ts:
                deltas.append(recv - ts)
    return deltas


def main():
    run_dir = sys.argv[1]
    ck = json.load(open(os.path.join(run_dir, "checkpoint.json")))
    run = json.load(open(os.path.join(run_dir, "run.json")))
    btime_ms = int(run.get("btime", "0")) * 1000
    print("# latency analysis: " + run_dir)
    print("| cell | dur | last-pre | first-after | gap ms | death+ | survived | fwd oneway med/max ms |")
    print("|---|---|---|---|---|---|---|---|")
    gaps = []
    deaths = []
    for c in ck.get("cells", []):
        ci = c.get("cell", 0)
        t0 = c.get("t0") or 0
        tres = c.get("t_resume") or 0
        arr = arrivals(f"{run_dir}/cell-{ci:02d}/eth1.pcap", btime_ms)
        pre = [a for a in arr if a <= tres]
        post = [a for a in arr if a > tres]
        last_pre = pre[-1] if pre else ""
        first_after = post[0] if post else ""
        gap = first_after - last_pre if (post and pre) else ""
        death = last_pre - t0 if pre else ""
        survived = "y" if (pre and pre[-1] > tres - 1500) else "n"
        if gap != "":
            gaps.append(gap)
        if death != "":
            deaths.append(death)
        ow = oneway(f"{run_dir}/cell-{ci:02d}/sink.log")
        ow_s = f"{median(ow):.0f}/{max(ow):.0f}" if ow else "-"
        print(f"| {ci} | {c.get('duration_s')} | {last_pre} | {first_after} "
              f"| {gap} | {death} | {survived} | {ow_s} |")
    if gaps:
        print(f"gaps: n={len(gaps)} min={min(gaps)} med={median(gaps):.0f} "
              f"max={max(gaps)}")
    if deaths:
        print(f"death-delay: n={len(deaths)} min={min(deaths)} "
              f"med={median(deaths):.0f} max={max(deaths)}")


if __name__ == "__main__":
    main()