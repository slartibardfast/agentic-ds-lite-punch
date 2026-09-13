# RESULTS-2026-09-13-pinning: the 2 s keepalive and the external IP

Status: measured. The hypothesis that the relay's 2 s keepalive "pins
the external IP" is resolved with evidence: the public IP is pinned by
the customer session, not by the relay's keepalive. The keepalive pins
(by survival or identical re-issue) the relay's own external port.

Redaction note: the public IP is a placeholder (<aftr-ip>); the external
ports are retained as relative data because the pinning and reuse claims
require them. The raw captures stay on the router.

## Method

- Console-path probe: `probe-tuple.py` sends a STUN Binding Request from
  a caller-supplied source port OUTSIDE the relay's fold map, routed
  through the console's egress path (the from-address rule to table
  1000), and prints the XOR-MAPPED external tuple. The result is the
  external tuple the console's class of non-folded traffic gets.
- Keepalive-stop gradient: the relay is SIGSTOPped for 45, 60 and 90 s
  windows (State=T verified in the first window; a keepalive-quiet
  capture over 9 s showed one in-flight packet then silence), with
  console-path probes taken near the end of each stop and after each
  resume. The relay's published tuple is read from its tuple file.

## Data

All external tuples share <aftr-ip>; the ports are the AFTR's session
allocations.

| sample | context | external port |
|---|---|---|
| step-a control | single probe, no stop | 59343 |
| pre | before the first stop | 59229 |
| during-45 s | relay State=T | 59201 |
| post-45 s | relay resumed | 59391 |
| during-60 s | relay State=T | 59234 |
| post-60 s | relay resumed | 59242 |
| during-90 s | relay State=T | 59353 |
| post-90 s | relay resumed | 59299 |

Relay pin through the whole sequence: 59230 (tuple file unchanged; its
mtime is held from 12:58, so no reported churn across the entire
session, including every resume).

## Conclusion

1. The external IP is customer-session-pinned: identical <aftr-ip> for
   all 8 console-class probes and the relay's pin, including probes
   taken during 90 s of relay silence with the relay demonstrably
   stopped.
2. The 2 s keepalive pins the relay's own external port: 59230 held
   through every 45 to 90 s stop (survival or identical re-issue, the
   same reuse rule the soak campaigns measured at 18 of 18, now
   extended to these windows).
3. The console's flows allocate sibling ports in the session's port
   space (the observed cluster 59201 to 59391), independent of the
   relay's keepalives: they live and die on their own traffic.
4. The keepalive's product value is port determinism for the relay's
   own mapping, not IP stability for the line.

## Scoping (operator caveat)

One AFTR node, one session, one load. The earlier documented 5 to 10 s
node-dependent TTL versus today's >30 s silent survival already shows
the AFTR's state is node and load dependent. These conclusions are
samples; the facade's GetExternalIPAddress honesty model assumes a
session-pinned IP, which is measured here and must be re-checked if node
churn is suspected.

## Enabler

GetExternalIPAddress can report the live STUN tuple honestly: the
relay's tuple and the console-class tuples share the session IP, and
the tuple re-issues identically under churn.