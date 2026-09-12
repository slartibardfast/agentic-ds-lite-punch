#!/usr/bin/env python3
# run-soak.py — the A3 soak campaign driver (runs on the router).
#
# Baseline 10 min, control 10 min, then the matrix of pause durations
# [5,7,10,12,20,30] seconds x 3 in a seeded random order. Each cell:
#
#   t0        pause starts (kill -STOP)
#   t_death   last sink arrival from the old tuple (mapping death, ~1s)
#   t_resume  kill -CONT at t0 + duration
#   t_resp    first STUN response on eth1 after resume (capture)
#   t_repub   tuple file change (snapshot)
#   t_recov   first sink arrival through the NEW tuple
#   reuse     old external tuple re-issued by the AFTR? (resurrection watch)
#
# Old-tuple probes continue through the pause and for 60 s after republish
# (ports the AFTR may resurrect). The payload sequence numbers correlate
# probe, capture, and sink logs. Every line timestamp is monotonic ms from
# /proc/uptime on the router.
#
# Invocation: run-soak.py RUN_DIR [--cells 5,7,10,12,20,30 --reps 3 --seed N]
# State: RUN_DIR/run.json, checkpoint.json (abort-safe resume).

import argparse
import json
import os
import random
import signal
import subprocess
import sys
import time

RELAY_CMD = "/usr/bin/ds-lite-punch"
PROBE = "dslp-probe"
SINK = "dslp-sink"
SINK_TARGET = "192.168.21.12:40002"
TUPLE_FILE = "/run/ds-lite-punch/tuple"


def monoms():
    with open("/proc/uptime") as f:
        return int(float(f.read().split()[0]) * 1000)


def relay_pid():
    out = subprocess.run(
        ["pgrep", "-f", RELAY_CMD], capture_output=True, text=True
    ).stdout.split()
    return int(out[0]) if out else None


def read_tuple():
    try:
        with open(TUPLE_FILE) as f:
            return f.read().strip()
    except OSError:
        return "absent"


def lxc(container, script, args, logpath):
    cmd = ["lxc-attach", "-n", container, "--", "/usr/bin/python3",
           "/opt/dslp-test/" + script] + args
    with open(logpath, "wb") as f:
        return subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)


def stable_tuple(checkpoints=5, window=5):
    seen = []
    for _ in range(checkpoints):
        seen.append(read_tuple())
        time.sleep(window / checkpoints)
    return len(set(seen)) == 1, seen[-1]


def run_baseline(run_dir, minutes=10, echo=True):
    os.makedirs(run_dir, exist_ok=True)
    tup = read_tuple()
    probe = lxc(PROBE, "probe.py",
                ["echo-on", SINK_TARGET if echo else tup, "1", "baseline"],
                f"{run_dir}/probe.log")
    snap = subprocess.Popen(["./snapshot.sh", run_dir],
                            stdout=subprocess.DEVNULL)
    cap = subprocess.Popen(["tcpdump", "-i", "eth1", "-nn", "-U", "-w",
                            f"{run_dir}/baseline.pcap"], stderr=subprocess.DEVNULL)
    time.sleep(minutes * 60)
    probe.terminate()
    snap.terminate()
    cap.terminate()
    return {"state": "done", "minutes": minutes, "tuple": tup}


def cell(run_dir, i, duration, seed):
    cdir = f"{run_dir}/cell-{i:02d}"
    os.makedirs(cdir, exist_ok=True)
    meta = {"cell": i, "duration_s": duration, "seed": seed}
    ok, tup = stable_tuple()
    meta["pre_stable"] = ok
    meta["tuple_old"] = tup
    pid0 = relay_pid()
    meta["pid0"] = pid0
    if not ok or pid0 is None:
        meta["state"] = "aborted-pre"
        return meta

    probe = lxc(PROBE, "probe-client.py", ["echo-on", tup, "1", f"cell-{i}"],
                f"{cdir}/probe.log")
    sink = lxc(SINK, "sink-server.py", [], f"{cdir}/sink.log")
    snap = subprocess.Popen(["./router-snapshot.sh", cdir],
                            stdout=subprocess.DEVNULL)
    cap = subprocess.Popen(["tcpdump", "-i", "eth1", "-nn", "-U", "-w",
                            f"{cdir}/eth1.pcap"], stderr=subprocess.DEVNULL)
    time.sleep(3)  # instruments are live

    t0 = monoms()
    os.kill(pid0, signal.SIGSTOP)
    meta["t0"] = t0
    time.sleep(duration)
    t_resume = monoms()
    os.kill(pid0, signal.SIGCONT)
    meta["t_resume"] = t_resume

    # Watch for republish (tuple change) up to 12 s, then keep probing the
    # OLD tuple for the resurrection watch, then switch to the new tuple.
    new_tup = tup
    deadline = monoms() + 15000
    while monoms() < deadline:
        cur = read_tuple()
        if cur != tup:
            new_tup = cur
            meta["t_repub"] = monoms()
            meta["tuple_new"] = cur
            break
        time.sleep(0.2)
    if "t_repub" not in meta:
        meta["tuple_new"] = new_tup
    time.sleep(60)  # resurrection watch on the old tuple
    probe.terminate()
    if new_tup != tup:
        probe = lxc(PROBE, "probe-client.py", ["echo-on", new_tup, "1", f"cell-{i}-new"],
                    f"{cdir}/probe-new.log")
        time.sleep(15)
        probe.terminate()
    snap.terminate()
    cap.terminate()
    sink.terminate()
    meta["state"] = "done"
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--durations", default="5,7,10,12,20,30")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--seed", type=int, default=20260912)
    args = ap.parse_args()

    pids = sorted(relay_pid() for _ in range(2))
    if len(set(pids)) != 1:
        sys.exit("relay pid unstable, abort")
    if read_tuple() == "absent":
        sys.exit("no tuple, abort")

    os.makedirs(args.run_dir, exist_ok=True)
    plan = {
        "target": "the deployed relay at " + read_tuple(),
        "durations": [int(x) for x in args.durations.split(",")],
        "reps": args.reps,
        "seed": args.seed,
        "pid": pids[0],
    }
    with open(f"{args.run_dir}/run.json", "w") as f:
        json.dump(plan, f, indent=1)

    results = {"baseline": run_baseline(f"{args.run_dir}/baseline", 10),
               "control": run_baseline(f"{args.run_dir}/control", 10),
               "cells": []}
    order = []
    for d in plan["durations"]:
        order.extend([d] * args.reps)
    random.Random(args.seed).shuffle(order)
    for i, d in enumerate(order):
        results["cells"].append(cell(args.run_dir, i, d, args.seed))
        with open(f"{args.run_dir}/checkpoint.json", "w") as f:
            json.dump(results, f, indent=1)
        print(f"cell {i} duration {d} state {results['cells'][-1]['state']}")
        sys.stdout.flush()
        time.sleep(60)  # settle before the next cell

    print("campaign complete: " + args.run_dir)


if __name__ == "__main__":
    main()