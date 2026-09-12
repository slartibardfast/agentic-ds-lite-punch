#!/usr/bin/env python3
# hold.py — dslp-sink TCP mapping holder for the C3 run.
# Opens one TCP connection to a public STUN server, learns the AFTR TCP
# mapping via STUN Binding over the same socket, prints the tuple, then
# holds the connection silent until the driver kills it. No keepalives:
# the mapping idle timer is left to the AFTR.

import socket
import struct
import sys
import time

STUN_SERVER = ("stun.l.google.com", 3478)
COOKIE = 0x2112A442


def stun_request():
    tid = b"\x00" * 12
    msg = struct.pack(">HHI", 0x0001, 0, COOKIE) + tid
    return msg


def stun_tuple(sock):
    sock.sendall(stun_request())
    time.sleep(0.5)
    data = sock.recv(2048)
    # Walk attributes for XOR-MAPPED-ADDRESS (0x0020), IPv4.
    off = 20
    while off + 4 <= len(data):
        atype, alen = struct.unpack(">HH", data[off:off + 4])
        a = data[off + 4:off + 4 + alen]
        if atype == 0x0020 and alen >= 8 and a[1] == 0x01:
            port = ((a[2] ^ 0x21) << 8) | (a[3] ^ 0x12)
            ip = ".".join(str(b ^ c) for b, c in
                          zip(a[4:8], b"\x21\x12\xa4\x42"))
            return f"{ip}:{port}"
        off += 4 + alen
    return "nyi"


def main():
    sock = socket.create_connection(STUN_SERVER, timeout=5)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 0)
    tup = stun_tuple(sock)
    print(tup, flush=True)
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w") as f:
            f.write(tup + "\n")
    # Silent hold: accept in-bound demonstrations via a listen backlog is
    # not needed; the probe's SYN lands on this socket and stays unanswered
    # at the app layer, which the driver treats as "mapping alive".
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()