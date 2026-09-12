#!/usr/bin/env python3
# probe.py — dslp-probe UDP series against target tuples.
# Modes:
#   series TARGET [RATE]     1 Hz (default) probes to TARGET, payload
#                            {mode,run,seq,ts,echo} ; echoed back by the sink.
#   echo-on TARGET            same as series, requests the sink to echo.
# Logs one JSON line per send to stdout (epoch ms + payload).
# The router marks this traffic into the vdsl4 table; the public source is
# 84.203.115.61 after the line masquerade.

import json
import socket
import sys
import time


def now_ms():
    return int(time.time() * 1000)


def main():
    mode = sys.argv[1]
    target = sys.argv[2]  # host:port of the tuple to probe
    rate = float(sys.argv[3]) if len(sys.argv) > 3 else 1
    host, port = target.rsplit(":", 1)
    port = int(port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    run = sys.argv[4] if len(sys.argv) > 4 else "adhoc"
    seq = 0
    while True:
        body = json.dumps(
            {"mode": mode, "run": run, "seq": seq, "ts": now_ms()},
            separators=(",", ":"),
        ).encode()
        sock.sendto(body, (host, port))
        print(json.dumps({"sent": now_ms(), "seq": seq, "to": target}))
        sys.stdout.flush()
        seq += 1
        time.sleep(1.0 / rate)


if __name__ == "__main__":
    main()