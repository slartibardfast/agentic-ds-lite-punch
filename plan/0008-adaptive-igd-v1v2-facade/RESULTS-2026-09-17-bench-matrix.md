# T4 results: the client-class matrix on the deployed box

Run 2026-09-17 against the router's live facade, plan/0008 `#bench-matrix`.
The bench is `bench-matrix.py` (workstation vantage) with
`bench-lan-client.sh` (router vantage, driven by ssh); it prints the table
below and writes it as JSON.

## What was deployed

- component pin `2158485`, host pin `ae3c306`-era; artifact built to the
  recorded recipe (`cargo build --release --target x86_64-unknown-linux-musl`),
  sha256 `c9b246c5…3181db41`, 987872 bytes, static musl
- installed as `/usr/bin/ds-lite-punch` (md5 `396a22c3…feca8718`), service
  `enabled`, procd; the previous binary is kept at `/root/ds-lite-punch.prev`
  (md5 `c1d27aad…75e78bd8`)
- the facade answers on br-lan (`192.168.21.1:49152`, UDP 1900); the v2 mount
  is live: `/igd/v2/rootDesc.xml` serves IGD:2 with DeviceProtection:1,
  WANCommonInterfaceConfig:1 and WANIPConnection:2, and the WIP2 SCPD carries
  the fourteen required actions

## The two vantages, and why

The workstation reaches the device through the lab path, and the router
source-maps it: the address on this side (`172.23.240.220`) is not the one
the facade keys sessions and containment on. The device sees
**`192.168.21.97`**, read from the router's own ssh peer for the same host:

```
ssh root@192.168.21.1 'ss -tn state established "( sport = :22 )"'
```

So the workstation is a LAN caller, and the mapping engine is reachable from
both vantages. Two caveats recorded rather than papered over:

- **SSDP was probed unicast** to `192.168.21.1:1900`. Multicast from the lab
  path does not reach br-lan, so the discovery rows exercise the responder and
  the burst state machine, not multicast delivery to a LAN client. Delivery to
  real LAN clients is the deployed behaviour the household mappings below
  already evidence.
- **One probe failed once and did not reproduce.** In the first full run the
  `WANIPConnection:2` M-SEARCH drew no answer while the three others answered;
  four isolated rounds of `IGD:2` immediately followed by `WIP:2` answered
  both every time (40-990 ms), and the two later full runs passed the row.
  Recorded as a single unreproduced miss on a UDP unicast path, not as a
  device property.

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

| v1 read of the LAN client's entry | 606 (containment) | 500 err=606 | pass |

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

| DP GetUserLoginChallenge | Salt + Challenge issued | Salt=obLD1OX2Bxgp... Challenge=toUjhjHEHpJs... | pass |

| DP UserLogin with the PKCS5 authenticator | 200 | 200 err= | pass |

| DP GetAssignedRoles after login | Basic (the lift) | 200 'Basic' | pass |

| v2 read of the LAN client's entry, lifted | 200 + the entry | 200 192.168.21.1 bench-lan | pass |

| v2 enumeration, lifted | the walk reaches ext 34999 | indexes=['3074', '14572', '34999'] | pass |

| v2 listing, lifted | 200 + a PortMappingEntry | 200 entries=3 | pass |

| v1 AddPortMapping naming the caller's own address | 200 (its own host, high port) | 200 err= | pass |

| v1 read of the caller's own entry | 200 + the label it set | 200 bench-self | pass |

| v1 DeletePortMapping of the caller's own entry | 200 | 200 err= | pass |

## What the run establishes

- **The v2 mount is real and gated.** `IGD:2` and `WIP:2` resolve to the v2
  description, `IGD:1`/`upnp:rootdevice` to v1, a bare `ssdp:all` is deferred
  and answered from v1 at the debounce deadline (measured 1004 ms, inside the
  850-1800 ms window the design allows), and an explicit `:2` inside that
  window flips both answers to v2.
- **The boundary holds against a caller that has authenticated for
  nothing.** All four mapping mutators answer 606 unauthenticated, and the
  reads are contracted: another client's entry is 606 rather than 714, the
  enumeration's index space is empty for that caller, and the listing is 730.
- **The required non-mapping actions answer as transcribed**: 731 ReadOnly
  for the auto-configured connection type, 501 for ForceTermination (the
  refusal that keeps a public action from handing every LAN device a lever on
  the household line), 200 for RequestConnection while the tuple is held, and
  RSIP 0 / NAT 1.
- **The DeviceProtection ceremony works on hardware, end to end**:
  SupportedProtocols carries WPS and PKCS5, GetAssignedRoles reports Public,
  the PKCS5 challenge is issued, `UserLogin` accepts an Authenticator computed
  as `HMAC-SHA-256(STORED, Challenge‖DeviceID‖CPID)[:16]` with STORED from
  PBKDF2-HMAC-SHA-256 at c=5000 over `Name‖Salt`, and the session then reports
  **Basic**.
- **The lift is real, and it rides the principal**: the same reads that were
  606/730 unauthenticated answer 200 when that session holds Basic, on either
  face. The containment is not a wall, which is what makes it a policy.
- **The containment bounds the caller's own mapping without touching anyone
  else's**: the workstation created a mapping for itself on a high port (200),
  read back the label it set, and deleted it (200).

## The box is in production use, and the run left it as it found it

The lifted enumeration shows the pre-existing household mappings untouched by
the bench:

| external | internal client | description | lease |
|---|---|---|---|
| 3074/UDP | 192.168.21.138 | (none) | 4294967295 |
| 14572/UDP | 192.168.21.12 | (none) | 4294967295 |

Both leases read `4294967295`, which is the v1 "appears infinite" policy on a
live box, and the 3074 mapping is the console-class port, so the deployed
facade is serving real clients as well as the bench. Every mapping the bench
created (the wildcard's `1024`, the LAN client's `34999`, the workstation's
`34998`) was deleted, and the final enumeration holds exactly the two rows
above.

## The bootstrap gap this exposed

To drive the authenticated sequences the DeviceProtection store had to be
seeded out of band: a `U` row for a user and an `A` row for a control-point
identity in `/run/ds-lite-punch/dp.tsv`, then a restart so `dp_load` reads it.
Without that, the deployed surface is **fail-closed**: no identity exists, so
no control point can hold a role, and the containment can never be lifted.

That is correct behaviour and an unusable product at once, and it is the
shadow of `call/0021`: the WPS introduction protocol, which the specification
makes the device's in-band way to introduce a control point and assign it a
role, is not implemented, and no operator bootstrap is documented in its
place. The bench's seed was removed after the run and the service restarted,
so the device is back to fail-closed (`GetAssignedRoles` Public,
`GetUserLoginChallenge` 600 for an absent name, `AddAnyPortMapping` 606).
Closing the gap is a decision for the operator: seed the store out of band as
a documented procedure, or implement the introduction limb.
