#!/usr/bin/env python3
# sink-stun.py — A1 reply-path probe: a br-lan host (the sink, standing in
# for the console) sends a STUN Binding Request from the pin's source port
# and reports the XOR-MAPPED-ADDRESS it observes. Arg: STUN server host:port
# (must be OUTSIDE the relay's rotation, else the relay consumes the
# response as its own). With the pin live, the request egresses eth1 as
# (192.168.0.21, 40000), the AFTR maps it, and the response loops back
# through the mapping to the sink. The observed tuple should equal the
# relay's published tuple.

import socket
import struct
import sys

COOKIE = 0x2112A442


def stun_request(txn):
    return struct.pack(">HHI", 0x0001, 0, COOKIE) + txn


def main():
    host, port = sys.argv[1].rsplit(":", 1)
    port = int(port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 40002))
    txn = b"\x01" * 12
    sock.sendto(stun_request(txn), (host, port))
    sock.settimeout(8)
    try:
        data, src = sock.recvfrom(2048)
    except socket.timeout:
        print("timeout: no response to the A1 STUN")
        return 2
    # Walk attributes for XOR-MAPPED-ADDRESS (0x0020), IPv4.
    off = 20
    mapped = None
    while off + 4 <= len(data):
        atype, alen = struct.unpack(">HH", data[off:off + 4])
        a = data[off + 4:off + 4 + alen]
        if atype == 0x0020 and alen >= 8 and a[1] == 0x01:
            port = ((a[2] ^ 0x21) << 8) | (a[3] ^ 0x12)
            ip = ".".join(str(b ^ c) for b, c in zip(a[4:8], b"\x21\x12\xa4\x42"))
            mapped = f"{ip}:{port}"
            break
        off += 4 + alen
    print(f"local bind: 192.168.21.12:40002  server: {host}:{port}")
    print(f"observed XOR-MAPPED-ADDRESS: {mapped}")
    print(f"published relay tuple: 37.228.213.83:59230")
    if mapped:
        ok = mapped.split(":")[0] == "37.228.213.83" and mapped.split(":")[1] == "59230"
        print("MATCH" if ok else "MISMATCH")
        return 0 if ok else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())