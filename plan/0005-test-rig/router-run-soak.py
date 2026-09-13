#!/usr/bin/env python3
# run-soak.py — the A3 soak campaign driver (runs on the router).
#
# Baseline 10 min, control 10 min, then the matrix of pause durations
# [5,7,10,12,20,30] seconds x 3 in a seeded random order. Each cell:
#
#   t0        pause starts (kill -STOP; probe is silenced too)
#   t_resume  kill -CONT at t0 + duration; probe relaunched on the old tuple
#   t_repub   tuple file change (snapshot)
#   t_recov   first sink arrival after t_resume (recovery, analysis annex)
#   reuse     old external tuple re-issued by the AFTR? (resurrection watch)
#
# Run 3 uses a probe-quiet pause: at t0 the driver kills the in-container
# probe as well as stopping the relay, so nothing inbound sustains the
# AFTR mapping through the window (the AFTR refreshes mappings on inbound
# datagrams, RFC 7857 S7 violation; see ANALYSIS-2026-09-13). With both
# silent, the mapping expires at the AFTR's true idle timeout, and the
# arrival stream resumes only after the relay's first post-resume keepalive
# re-creates it. The payload sequence numbers correlate probe, capture,
# and sink logs. Every line timestamp is monotonic ms from /proc/uptime.
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


def kill_container_agents():
    # terminate() kills the lxc-attach wrapper only; the in-container
    # python survives and leaks. Kill both agent kinds inside their
    # containers where pkill exists: leaked probes flood the arrival
    # stream, a leaked sink holds 40002 and EADDRINUSE-blocks the next
    # cell's receiver.
    subprocess.run(["lxc-attach", "-n", PROBE, "--", "pkill", "-f",
                    "probe-client"], capture_output=True)
    subprocess.run(["lxc-attach", "-n", SINK, "--", "pkill", "-f",
                    "sink-server"], capture_output=True)


def run_baseline(run_dir, minutes=10):
    os.makedirs(run_dir, exist_ok=True)
    tup = read_tuple()
    probe = lxc(PROBE, "probe-client.py",
                ["series", tup, "1", "baseline"],
                f"{run_dir}/probe.log")
    snap = subprocess.Popen(["./router-snapshot.sh", run_dir],
                            stdout=subprocess.DEVNULL)
    cap = subprocess.Popen(["tcpdump", "-i", "eth1", "-nn", "-U", "-w",
                            f"{run_dir}/baseline.pcap"], stderr=subprocess.DEVNULL)
    time.sleep(minutes * 60)
    probe.terminate()
    kill_container_agents()
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

    probe = lxc(PROBE, "probe-client.py", ["series", tup, "1", f"cell-{i}"],
                f"{cdir}/probe.log")
    sink = lxc(SINK, "sink-server.py", [], f"{cdir}/sink.log")
    snap = subprocess.Popen(["./router-snapshot.sh", cdir],
                            stdout=subprocess.DEVNULL)
    cap = subprocess.Popen(["tcpdump", "-i", "eth1", "-nn", "-U", "-w",
                            f"{cdir}/eth1.pcap"], stderr=subprocess.DEVNULL)
    time.sleep(3)  # instruments are live

    t0 = monoms()
    os.kill(pid0, signal.SIGSTOP)
    # Probe-quiet pause: silence the probe inside its container too, so no
    # inbound datagram sustains the AFTR mapping while the relay is stopped.
    subprocess.run(["lxc-attach", "-n", PROBE, "--", "pkill", "-f",
                    "probe-client"], capture_output=True)
    meta["t0"] = t0
    meta["quiet"] = True
    time.sleep(duration)
    t_resume = monoms()
    os.kill(pid0, signal.SIGCONT)
    meta["t_resume"] = t_resume
    # Relaunch the probe on the old tuple: if the mapping died in the pause,
    # datagrams vanish until the relay's post-resume keepalive re-creates
    # it; the arrival resume is the true recovery mark.
    probe = lxc(PROBE, "probe-client.py", ["series", tup, "1",
                f"cell-{i}-res"], f"{cdir}/probe-res.log")
    time.sleep(2)

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
    kill_container_agents()
    if new_tup != tup:
        probe = lxc(PROBE, "probe-client.py", ["series", new_tup, "1", f"cell-{i}-new"],
                    f"{cdir}/probe-new.log")
        time.sleep(15)
        probe.terminate()
        kill_container_agents()
    snap.terminate()
    cap.terminate()
    sink.terminate()
    kill_container_agents()
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
    sha = subprocess.run(["sha256sum", "/usr/bin/ds-lite-punch"],
                         capture_output=True, text=True).stdout.split()[0]
    init_sha = subprocess.run(["sha256sum", "/etc/init.d/ds-lite-punch"],
                              capture_output=True, text=True).stdout.split()[0]
    btime = "0"
    try:
        for ln in open("/proc/stat"):
            if ln.startswith("btime"):
                btime = ln.split()[1]
                break
    except OSError:
        pass
    plan = {
        "target": "the deployed relay at " + read_tuple(),
        "relay_sha256": sha,
        "init_sha256": init_sha,
        "btime": btime,
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