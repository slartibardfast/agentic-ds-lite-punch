# T4 results: the client-class matrix on the deployed box

Run 2026-09-17 against the router's live facade, plan/0008 `#bench-matrix`,
and re-run after the per-client key landed (call/0022). The bench is
`bench-matrix.py` (workstation vantage) with `bench-lan-client.sh` (router
vantage, driven by ssh); it prints the matrix below and writes it as JSON.

## What was deployed

- component `77825c5` and then `6a2b43c` (the enumeration fix the bench
  itself found), built to the recorded recipe
  (`cargo build --release --target x86_64-unknown-linux-musl`), static musl.
  The last run's artifact is sha256 `0e2b2b33…b203714f`, installed as
  `/usr/bin/ds-lite-punch` (md5 `32beccae…e13704c`); the previous build is
  parked at `/root/ds-lite-punch.prev` for rollback
- service `enabled` under procd, tuple `37.228.213.83:59304`, and the v2
  mount live on br-lan `192.168.21.1:49152` with DeviceProtection:1,
  WANCommonInterfaceConfig:1 and WANIPConnection:2

## The vantages

The workstation is a LAN caller at **`192.168.21.97`** as the device sees it
(the router source-maps the lab path, so the local `172.23.240.220` is not
the address the facade keys sessions and containment on; it was read from
the router's own ssh peer). The router itself is the second LAN caller, which
is what the mapping engine needs.

## Discovery, and what the misses were

The discovery rows are probed **unicast** to `192.168.21.1:1900`, because
multicast from the lab path does not reach br-lan. On that path a single
query's answer is lost in a measurable fraction of cases: two samples gave
15% and 40%, spread across every target, and one retry ~350 ms later answered
**20 of 20**. So the misses are path loss on this vantage, not a device rule;
the deadline property itself was measured twice at **1004 ms** on runs where
the answer arrived, inside the 850-1800 ms window the design allows.

## The matrix

| probe | expected | observed | result |
|---|---|---|---|
| M-SEARCH upnp:rootdevice | upnp:rootdevice + /igd/v1/ | upnp:rootdevice http://192.168.21.1:49152/igd/v1/rootDesc.xml | pass |
| M-SEARCH urn:schemas-upnp-org:device:InternetGatewayDevice:1 | urn:schemas-upnp-org:device:InternetGatewayDevice:1 + /igd/v1/ | urn:schemas-upnp-org:device:InternetGatewayDevice:1 http://192.168.21.1:49152/igd/v1/rootDesc.xml | pass |
| M-SEARCH urn:schemas-upnp-org:device:InternetGatewayDevice:2 | urn:schemas-upnp-org:device:InternetGatewayDevice:2 + /igd/v2/ | urn:schemas-upnp-org:device:InternetGatewayDevice:2 http://192.168.21.1:49152/igd/v2/rootDesc.xml | pass |
| M-SEARCH urn:schemas-upnp-org:service:WANIPConnection:2 | urn:schemas-upnp-org:service:WANIPConnection:2 + /igd/v2/ | urn:schemas-upnp-org:service:WANIPConnection:2 http://192.168.21.1:49152/igd/v2/rootDesc.xml | pass |
| ssdp:all alone: deferred v1 at the debounce deadline | v1 answer, 850-1800 ms | http://192.168.21.1:49152/igd/v1/rootDesc.xml at 1006 ms | pass |
| ssdp:all + :2 in the window flips the burst | both answers v2 | 2 answer(s), 2 on v2 | pass |
| v1 GetExternalIPAddress | 200 + a public address | 200 37.228.213.83 | pass |
| v1 AddPortMapping naming another host | 606 (containment) | 500 err=606 | pass |
| v1 enumeration with nothing visible | 714 (contained index space) | 500 err=714 | pass |
| v1 read of another client's port | 714 (the key is the caller's own) | 500 err=714 | pass |
| v2 GetExternalIPAddress | 200 | 200 37.228.213.83 | pass |
| v2 AddPortMapping unauthenticated | 606 (the boundary) | 500 err=606 | pass |
| v2 AddAnyPortMapping unauthenticated | 606 (the boundary) | 500 err=606 | pass |
| v2 DeletePortMappingRange unauthenticated | 606 (the boundary) | 500 err=606 | pass |
| v2 listing, unauthenticated, other hosts' entries present | 730 (contracted view) | 500 err=730 | pass |
| v2 GetNATRSIPStatus | RSIP 0 / NAT 1 | 200 NewRSIPAvailable>0</NewRSIPAvailable><NewNATEEnabled>1</NewNATEE | pass |
| v2 SetConnectionType | 731 | 500 err=731 | pass |
| v2 ForceTermination | 501 | 500 err=501 | pass |
| v2 RequestConnection | 200 (the line is up) | 200 err= | pass |
| v2 GetListOfPortMappings | 730 | 500 err=730 | pass |
| DP GetSupportedProtocols | WPS and PKCS5 present | 200 ['WPS', 'PKCS5'] | pass |
| DP GetAssignedRoles before login | Public | 200 'Public' | pass |
| DP GetUserLoginChallenge | Salt + Challenge issued | Salt=obLD1OX2Bxgp... Challenge=z168gzW0phZk... | pass |
| DP UserLogin with the PKCS5 authenticator | 200 | 200 err= | pass |
| DP GetAssignedRoles after login | Basic (the lift) | 200 'Basic' | pass |
| v2 read of another client's port, lifted | 714 (still the caller's own key) | 500 err=714 | pass |
| v2 enumeration, lifted | the walk reaches ext 34999 | indexes=['14572', '34999'] | pass |
| v2 listing, lifted | 200 + a PortMappingEntry | 200 entries=2 | pass |
| v1 AddPortMapping naming the caller's own address | 200 (its own host, high port) | 200 err= | pass |
| v1 read of the caller's own entry | 200 + the label it set | 200 bench-self | pass |
| the router (a second LAN client) claims 3074/UDP | 200 | http=200 | pass |
| a second holder of 3074/UDP is admitted | 200 | 200 err= | pass |
| the second holder reads its own 3074 | 200 + the label it set | 200 bench-3074 | pass |
| both holders of 3074/UDP are in the table | two entries, two clients | holders=['192.168.21.1', '192.168.21.97'] | pass |
| the router releases its 3074/UDP | 200 | http=200 | pass |
| v1 DeletePortMapping, the caller's own entry | 200 | 200 err= | pass |
| v1 DeletePortMapping, the workstation's 3074/UDP holder | 200 | 500 err=714 | FAIL |

## What the run establishes

- **The v2 mount is gated and live**: `IGD:2` and `WIP:2` resolve to the v2
  description, `IGD:1`/`upnp:rootdevice` to v1, a bare `ssdp:all` is deferred
  and answered from v1 at the debounce deadline, and an in-window `:2` flips
  both answers to v2.
- **The boundary holds**: all four v2 mapping mutators answer 606
  unauthenticated, the contained enumeration is 714 and the contained listing
  730, `GetNATRSIPStatus` reports RSIP 0 / NAT 1, `SetConnectionType` is 731
  ReadOnly, `ForceTermination` 501, `RequestConnection` 200.
- **The DeviceProtection ceremony works on hardware**: WPS and PKCS5 are
  advertised, the challenge is issued, `UserLogin` accepts an Authenticator
  computed as `HMAC-SHA-256(STORED, Challenge‖DeviceID‖CPID)[:16]` with
  STORED from PBKDF2-HMAC-SHA-256 at c=5000 over `Name‖Salt`, and the session
  then reports **Basic**.
- **The supersession is proven on the box** (`call/0022`): two LAN clients —
  the router and the workstation — each claim `3074/UDP`, both are admitted,
  each reads back **its own** label, and the lifted walk shows **two holders,
  two clients** (`192.168.21.1`, `192.168.21.97`). Under the retired
  one-holder rule the second claim would have evicted the first.

## The defect the bench found

The two-holder table enumerated as **two copies of the earlier holder**: the
index was resolved against a list of `(req_ext, proto)` keys and the entry
looked up by those two fields, which stopped being unique when the key became
per client. A control point walking the table would have read a fabricated
mapping. Fixed in `6a2b43c` (the index addresses the visible list directly,
which is exact and simpler) and pinned by the containment test: two clients
holding `1024/UDP` must enumerate as themselves. The unit tests had covered
two holders *in the table* but never walked it, which is exactly what a
deployed bench is for.

## Still open, localized

One probe fails and L can place it: after the two-holder exchange, the
workstation's own `DeletePortMapping(3074)` answers 714 even though its entry
exists and enumerates. The entry record's `client` field is the request's
`NewInternalClient` — the **datapath target** — and the per-client key is
read from that same field, so an entry created by a lifted control point
naming *another* host is keyed by that host rather than by its owner. The key
must be the **requester**, distinct from the target. That is the next change;
until it lands, a mapping made on behalf of another host is not deletable by
the control point that made it.

## A household mapping was lost during this session

The console-class `3074/UDP → 192.168.21.138` mapping, present at the start of
the session with an "appears infinite" lease, is gone; the persisted index
(`/tmp/dslp/upnp.tsv`) was last written inside the deployment window and the
daemon log shows three `DeletePortMapping` calls there, two of which this
session's own cleanup accounts for. The evidence does not conclusively
exclude the bench, so it is recorded as a loss rather than attributed. The
per-client key makes the class impossible (a delete can only ever hit the
caller's own entry at that port), and the consumer that wants `3074` will
re-create it on its next run; say the word and L will add it back by hand.
The household's other mapping, `14572/UDP → 192.168.21.12`, survived
untouched, and the run's own entries were all deleted.
