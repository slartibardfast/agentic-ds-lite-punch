# T4 results: the client-class matrix on the deployed box

Run 2026-09-17 against the router's live facade, plan/0008 `#bench-matrix`,
re-run after the per-client key landed (`call/0022`) and after the two
defects that key exposed were fixed. The bench is `bench-matrix.py`
(workstation vantage) with `bench-lan-client.sh` (router vantage, driven over
ssh); it prints the matrix below and writes it as JSON.

**37 of 37 probes pass.**

## What was deployed

- component `887be84`, built to the recorded recipe
  (`cargo build --release --target x86_64-unknown-linux-musl`), static musl,
  installed as `/usr/bin/ds-lite-punch` (md5 `bb13c65c…cf2fd2075`); the
  previous build is parked at `/root/ds-lite-punch.prev` for rollback
- service `enabled` under procd; the v2 mount live on br-lan
  `192.168.21.1:49152` carrying DeviceProtection:1,
  WANCommonInterfaceConfig:1 and WANIPConnection:2

## The vantages

The workstation is a LAN caller at **`192.168.21.97`** as the device sees it
(the router source-maps the lab path, so the local `172.23.240.220` is not
the address the facade keys sessions and containment on). A six-round
add/read/delete cycle from this vantage is clean, so its source address is
stable across calls. The router itself is the second LAN caller, which is
what the mapping engine needs for the two-holder case.

## Discovery

The discovery rows are probed **unicast** to `192.168.21.1:1900`, since
multicast from the lab path does not reach br-lan. On that path a single
query's answer is lost in a measurable fraction of cases: two samples gave
15% and 40%, spread across every target, and one retry ~350 ms later answered
**20 of 20**. This run lost none of the five. The misses are path loss on
this vantage, not a device rule; the deadline property itself measured
**1004 ms** on the runs where the answer arrived, inside the 850-1800 ms
window the design allows.

## The matrix

| probe | expected | observed | result |
|---|---|---|---|
| M-SEARCH upnp:rootdevice | upnp:rootdevice + /igd/v1/ | upnp:rootdevice http://192.168.21.1:49152/igd/v1/rootDesc.xml | pass |
| M-SEARCH urn:schemas-upnp-org:device:InternetGatewayDevice:1 | urn:schemas-upnp-org:device:InternetGatewayDevice:1 + /igd/v1/ | urn:schemas-upnp-org:device:InternetGatewayDevice:1 http://192.168.21.1:49152/igd/v1/rootDesc.xml | pass |
| M-SEARCH urn:schemas-upnp-org:device:InternetGatewayDevice:2 | urn:schemas-upnp-org:device:InternetGatewayDevice:2 + /igd/v2/ | urn:schemas-upnp-org:device:InternetGatewayDevice:2 http://192.168.21.1:49152/igd/v2/rootDesc.xml | pass |
| M-SEARCH urn:schemas-upnp-org:service:WANIPConnection:2 | urn:schemas-upnp-org:service:WANIPConnection:2 + /igd/v2/ | urn:schemas-upnp-org:service:WANIPConnection:2 http://192.168.21.1:49152/igd/v2/rootDesc.xml | pass |
| ssdp:all alone: deferred v1 at the debounce deadline | v1 answer, 850-1800 ms | http://192.168.21.1:49152/igd/v1/rootDesc.xml at 1004 ms | pass |
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
| DP GetUserLoginChallenge | Salt + Challenge issued | Salt=obLD1OX2Bxgp... Challenge=hkvFjMosMA/G... | pass |
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
| v1 DeletePortMapping, the workstation's 3074/UDP holder | 200 | 200 err= | pass |

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
- **The supersession is proven on the box** (`call/0022`): two LAN clients,
  the router and the workstation, each claim `3074/UDP`; both are admitted;
  each reads back **its own** label; the lifted walk shows **two holders, two
  clients**; and each one's delete removes **only its own** mapping, the
  other still standing afterwards. Under the retired one-holder rule the
  second claim would have evicted the first, and under the owner-blind
  teardown the first claimant's delete would have taken the second's mapping
  with it.

## The defects this bench found, both fixed

Both were real, both were reachable only by walking a deployed table, and the
unit tests covered neither: the tests had two holders *in* the table but never
enumerated or deleted through it.

1. **The enumeration fabricated a holder** (`6a2b43c`). The index was resolved
   against a list of `(req_ext, proto)` keys and the entry then looked up by
   those two fields, which stopped being unique the moment the key became per
   client, so a two-holder table enumerated as two copies of the earlier
   holder. The index now addresses the visible list directly.
2. **The key read the target, not the requester** (`64d4b20`), and **the
   delete teardown drained by port alone** (`887be84`). A lifted control point
   mapping on another host's behalf was keyed by the host it named, and the
   teardown's retain was still the one-holder rule, so one client's delete
   took every holder's entry at that port. The record now carries `owner` (the
   requester, and what the per-client key and the containment read) alongside
   `client` (the datapath target that `NewInternalClient` names), the row
   grows a field with older rows reading the target as the requester, and the
   teardown retains on the owner.

## The state the run left behind

The DeviceProtection store was seeded out of band for the authenticated rows
(a `U` row and an `A` row in `/run/ds-lite-punch/dp.tsv`) and removed after
the run, so the deployed default is fail-closed: no identity exists, so no
control point can hold a role. Every mapping the bench created was deleted,
and the table holds only the household's `14572/UDP → 192.168.21.12`.

## A household mapping was lost earlier in the session

The console-class `3074/UDP → 192.168.21.138` mapping, present at the start of
the session with an "appears infinite" lease, disappeared inside the first
deployment window. The evidence does not conclusively exclude that bench, and
this run's own two-holder probes use `3074` deliberately, so the loss is
recorded rather than attributed. The consumer that wants it will re-create it
on its next run; L can also add it back by hand on request.
