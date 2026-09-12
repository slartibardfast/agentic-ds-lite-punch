#!/usr/bin/env python3
# connect.py — dslp-probe TCP probe to a mapped tuple (one attempt).
# Prints ok (SYN-ACK), refused (AFTR RST: mapping dead, the C8 signal), or
# timeout (no answer within 6 s). Exit 0 on ok, 1 on refused, 2 on timeout.

import socket
import sys

HOST, PORT = sys.argv[1].rsplit(":", 1)
PORT = int(PORT)


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(6)
    try:
        s.connect((HOST, PORT))
        print("ok")
        return 0
    except ConnectionRefusedError:
        print("refused")
        return 1
    except OSError:
        # Timeout or hangup: no RST, mapping not refuted.
        print("timeout")
        return 2
    finally:
        s.close()


if __name__ == "__main__":
    sys.exit(main())