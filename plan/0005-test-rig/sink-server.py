#!/usr/bin/env python3
# sink.py — dslp-sink UDP recorder on :40002.
# Logs every datagram {recv_ts, src, payload} to stdout and echoes it back
# when the payload carries mode=echo-on (exercising the reply path through
# the A1 pin). The relay forwards inbound probes here with their public
# source preserved; the pin is what makes the echo egress as the relay tuple.

import json
import socket
import sys
import time

BIND = ("0.0.0.0", 40002)


def now_ms():
    return int(time.time() * 1000)


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(BIND)
    while True:
        data, src = sock.recvfrom(2048)
        try:
            body = json.loads(data)
        except ValueError:
            body = {"raw": data.decode(errors="replace")}
        line = {"recv": now_ms(), "src": f"{src[0]}:{src[1]}", "payload": body}
        print(json.dumps(line, separators=(",", ":")))
        sys.stdout.flush()
        if body.get("mode") == "echo-on":
            sock.sendto(data, src)


if __name__ == "__main__":
    main()