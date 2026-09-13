#!/usr/bin/env python3
# probe-tuple.py — a STUN Binding Request from a caller-supplied source
# port; prints the XOR-MAPPED external tuple. Used by the pinning
# measurement: bind a port OUTSIDE the relay's fold map so the flow
# egresses non-folded, the console's class of traffic. Arg: bind port.
import socket
import struct
import sys

COOKIE = 0x2112A442


def main():
    port = int(sys.argv[1])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    sock.settimeout(8)
    sock.sendto(struct.pack(">HHI", 0x0001, 0, COOKIE) + b"\x05" * 12,
                ("46.225.95.169", 3478))
    try:
        data, _ = sock.recvfrom(2048)
    except socket.timeout:
        print("timeout")
        return 2
    off = 20
    while off + 4 <= len(data):
        t, ln = struct.unpack(">HH", data[off:off + 4])
        a = data[off + 4:off + 4 + ln]
        if t == 0x0020 and ln >= 8 and a[1] == 1:
            p = ((a[2] ^ 0x21) << 8) | (a[3] ^ 0x12)
            ip = ".".join(str(b ^ c) for b, c in zip(a[4:8], b"\x21\x12\xa4\x42"))
            print(f"{ip}:{p}")
            return 0
        off += 4 + ln
    print("no-mapped")
    return 1


if __name__ == "__main__":
    sys.exit(main())