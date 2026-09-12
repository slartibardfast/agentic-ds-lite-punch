#!/usr/bin/env python3
# run-c3.py — TCP idle-lifetime measurement (drives hold.py + connect.py).
#
# Per point: dslp-sink opens a TCP connection through the AFTR and learns
# its TCP mapping tuple via STUN-over-TCP; the mapping is then held silent.
# After the idle gap, dslp-probe connects to the mapped tuple:
#   ok        mapping alive
#   refused   AFTR RST: mapping dead (the C8 signal)
#   timeout   no answer within 6 s (recorded, not counted as dead)
#
# Gaps: [15, 30, 60, 120, 300, 600] seconds; the death point is
# binary-searched between the last ok and the first refused.
#
# Invocation: run-c3.py RUN_DIR [--gaps 15,30,60,120,300,600]

import argparse
import json
import os
import subprocess
import sys
import time


def lxc(container, script, args):
    cmd = ["lxc-attach", "-n", container, "--", "/usr/bin/python3",
           "/opt/dslp-test/" + script] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def point(run_dir, gap):
    hold_out = f"{run_dir}/hold-tuple.txt"
    if os.path.exists(hold_out):
        os.remove(hold_out)
    holder = subprocess.Popen(
        ["lxc-attach", "-n", "dslp-sink", "--", "/usr/bin/python3",
         "/opt/dslp-test/hold.py", hold_out],
        stdout=open(f"{run_dir}/hold.log", "w"))
    # Wait for the tuple discovery.
    tup = None
    for _ in range(20):
        if os.path.exists(hold_out):
            tup = open(hold_out).read().strip()
            if tup and tup != "nyi":
                break
        time.sleep(0.5)
    if not tup:
        holder.terminate()
        return {"gap": gap, "state": "no-tuple"}
    time.sleep(gap)
    res = lxc("dslp-probe", "connect.py", [tup])
    holder.terminate()
    return {"gap": gap, "tuple": tup, "result": res.stdout.strip(),
            "rc": res.returncode}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--gaps", default="15,30,60,120,300,600")
    args = ap.parse_args()
    os.makedirs(args.run_dir, exist_ok=True)
    gaps = [int(x) for x in args.gaps.split(",")]
    points = []
    for g in gaps:
        p = point(args.run_dir, g)
        points.append(p)
        with open(f"{args.run_dir}/c3.json", "w") as f:
            json.dump(points, f, indent=1)
        print(f"gap {g}: {p}", flush=True)
    print(json.dumps(points, indent=1))


if __name__ == "__main__":
    main()