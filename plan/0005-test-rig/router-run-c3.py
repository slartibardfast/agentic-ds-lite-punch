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
# The holder must present through the AFTR line: the run pins the sink's
# egress to the eth1 table (rule 25002 -> table 1000, the console-path
# mechanism) so the discovered tuple is an AFTR one. A discovered tuple
# on the vdsl4 line (the sink's default route) is a wrong-line failure.
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


def stop_holder(holder):
    holder.terminate()
    # terminate() kills the lxc-attach wrapper only; the in-container
    # python survives and leaks a held AFTR TCP mapping per point.
    subprocess.run(["lxc-attach", "-n", "dslp-sink", "--", "pkill", "-f",
                    "sink-keepalive"], capture_output=True)


def point(run_dir, gap):
    holder = subprocess.Popen(
        ["lxc-attach", "-n", "dslp-sink", "--", "/usr/bin/python3",
         "/opt/dslp-test/sink-keepalive.py"],
        stdout=open(f"{run_dir}/hold.log", "w"),
        stderr=subprocess.STDOUT)
    # The holder prints the discovered tuple as its first flushed line.
    # (A cross-namespace tuple file is unavailable: the container does
    # not see the /mnt/nvme runs dir.)
    tup = None
    for _ in range(40):
        try:
            line = open(f"{run_dir}/hold.log").readline().strip()
            if line and line != "nyi":
                tup = line
                break
        except OSError:
            pass
        time.sleep(0.25)
    if not tup:
        stop_holder(holder)
        return {"gap": gap, "state": "no-tuple"}
    if tup.startswith("84.203.115.61"):
        stop_holder(holder)
        return {"gap": gap, "state": "wrong-line",
                "tuple": tup}  # holder rode the vdsl4 route, not the AFTR
    time.sleep(gap)
    # Alive signal: the AFTR forwarding the probe's SYN to the inner
    # tuple. The router's input chain (policy drop, UDP pin only) drops
    # forwarded TCP NEW silently, so the probe's own connect cannot
    # signal; the eth1 capture observes the forwarding directly, the
    # same arrival methodology as the soak campaign. tcpdump -c 1 exits
    # 0 the moment a SYN lands.
    cap = subprocess.Popen(
        ["tcpdump", "-i", "eth1", "-nn", "-c", "1", "-w", "/dev/null",
         "tcp and dst host 192.168.0.21 and tcp[tcpflags] & tcp-syn != 0"],
        stderr=subprocess.DEVNULL)
    res = lxc("dslp-probe", "probe-connect.py", [tup])
    time.sleep(1.5)
    alive = (cap.poll() == 0)
    if cap.poll() is None:
        cap.terminate()
    stop_holder(holder)
    return {"gap": gap, "tuple": tup, "alive": alive,
            "probe": res.stdout.strip(), "rc": res.returncode}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--gaps", default="15,30,60,120,300,600")
    args = ap.parse_args()
    os.makedirs(args.run_dir, exist_ok=True)
    gaps = [int(x) for x in args.gaps.split(",")]
    subprocess.run(["ip", "rule", "add", "from", "192.168.21.12",
                    "lookup", "1000", "prio", "25002"], capture_output=True)
    try:
        points = []
        for g in gaps:
            p = point(args.run_dir, g)
            points.append(p)
            with open(f"{args.run_dir}/c3.json", "w") as f:
                json.dump(points, f, indent=1)
            print(f"gap {g}: {p}", flush=True)
        print(json.dumps(points, indent=1))
    finally:
        subprocess.run(["ip", "rule", "del", "prio", "25002"],
                       capture_output=True)


if __name__ == "__main__":
    main()