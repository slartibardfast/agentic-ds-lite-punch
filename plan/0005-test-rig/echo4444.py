#!/usr/bin/env python3
# echo4444.py — TCP responder on port 4444 for the tcp-datapath line
# test. Answers an HTTP GET with a minimal 200 (so the Globalping http
# probe through the relay's TCP slot sees a valid HTTP status), and an
# echo otherwise (the local probe's data round-trip).
import socket

S = b"HTTP/1.0 200 OK\r\nContent-Length: 8\r\n\r\ndslp-ok\n"

srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("0.0.0.0", 4444))
srv.listen(8)
while True:
    c, _ = srv.accept()
    try:
        d = c.recv(256)
        if d.startswith(b"GET") or d.startswith(b"HEAD"):
            c.sendall(S)
        else:
            c.sendall(b"echo:" + d)
    except OSError:
        pass
    finally:
        c.close()