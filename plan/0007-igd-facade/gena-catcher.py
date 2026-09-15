#!/usr/bin/env python3
# gena-catcher.py — a GENA callback endpoint for the facade verification.
# Listens on 0.0.0.0:<port>; every request is logged with its full header
# block and body so the initial NOTIFY (SEQ 0, ExternalIPAddress) and any
# churn events are visible in the log.
import sys, socket, threading

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 18080

def handle(conn, addr):
    data = b""
    conn.settimeout(2)
    try:
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if len(data) > 16384:
                break
        head, _, body = data.partition(b"\r\n\r\n")
        lines = head.decode("latin-1").split("\r\n")
        seq = next((l.split(":", 1)[1].strip() for l in lines if l.lower().startswith("seq:")), "?")
        sid = next((l.split(":", 1)[1].strip() for l in lines if l.lower().startswith("sid:")), "?")
        ext = next((l.split(">", 1)[1].split("<", 1)[0] for l in body.split(b"\n") if b"ExternalIPAddress" in l), "?")
        print(f"NOTIFY from {addr[0]}:{addr[1]} SEQ={seq} SID={sid} ExternalIPAddress={ext}", flush=True)
        sys.stdout.flush()
    except Exception as e:
        print(f"catcher error: {e}", flush=True)
    finally:
        conn.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", PORT))
s.listen(8)
print(f"gena-catcher listening on {PORT}", flush=True)
while True:
    conn, addr = s.accept()
    threading.Thread(target=handle, args=(conn, addr), daemon=True).start()