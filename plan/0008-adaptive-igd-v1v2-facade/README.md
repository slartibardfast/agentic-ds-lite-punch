# Milestone: adaptive UPnP IGD v1/v2 compatibility facade

- Status: specified 2026-09-16; not yet started.
- Scope: the ds-lite-punch UPnP facade (plan/0007 phase E successor);
  builds on the deployed 34d48c1-era facade and the lease policy.
- This document is the milestone specification. The build-sequence
  tasks are derived at kickoff; the behaviour spec (allium lane) lives
  with the component code when implementation begins.

This document specifies an implementation architecture for a new IPv4
UPnP Internet Gateway Device (IGD) server whose principal requirement
is simultaneous interoperability with:

* legacy IGD:1 control points, including observed Xbox One behavior;
* modern IGD:2 control points;
* clients that perform discovery using `ssdp:all`;
* clients that explicitly search for `InternetGatewayDevice:2`;
* clients that probe both IGD:2 and IGD:1.

The design deliberately separates the **canonical NAT/mapping implementation** from the **UPnP discovery and description facade**.

The central conclusion is:

> **Do not use cross-request debounce to decide whether `ssdp:all` is "really" a v2 client. Treat `ssdp:all` as the legacy/v1 facade, and treat an explicit IGD:2 search as positive evidence for the v2 facade. Use the UPnP `MX` timing allowance only for ordinary response jitter/coalescing, not as a version-negotiation protocol.**

This produces deterministic behavior without relying upon client identity, HTTP source-IP heuristics, or a mutable `rootDesc.xml`.

---

# 1. Terminology

The following identifiers are abbreviated:

```text
IGD1 =
  urn:schemas-upnp-org:device:InternetGatewayDevice:1

IGD2 =
  urn:schemas-upnp-org:device:InternetGatewayDevice:2

WIP1 =
  urn:schemas-upnp-org:service:WANIPConnection:1

WIP2 =
  urn:schemas-upnp-org:service:WANIPConnection:2
```

The relevant IPv4 port-mapping operations are:

```text
WIP1#AddPortMapping

WIP2#AddPortMapping
WIP2#AddAnyPortMapping
```

`AddAnyPortMapping` is a v2 service operation; it is not an SSDP search target.

---

# 2. Normative background

## 2.1 `ssdp:all` is part of UDA 1.0

UPnP Device Architecture 1.0 defines `ssdp:all` as an M-SEARCH target meaning search for all devices and services. It is therefore not a v2 feature.

A response to `ssdp:all` may consist of multiple discovery responses covering the root device, embedded devices and distinct service types. UDA 1.0 describes the response count as `3 + 2d + k` for a root device with `d` embedded devices and `k` distinct service types.

Consequently:

```text
ssdp:all
```

must never be interpreted as:

```text
IGD:1
```

by the protocol itself.

This specification nevertheless deliberately assigns the server's **IPv4 compatibility facade** for `ssdp:all` to its v1 presentation. That is an interoperability policy, not a claim that `ssdp:all` is intrinsically version 1.

---

## 2.2 Explicit version searches

UDA requires a versioned device/service search to receive a response whose `ST` contains the same version that was searched for.

UDA 1.1 and UDA 2.0 explicitly require a device supporting version 2 to respond to both version-2 and version-1 searches, with the response retaining the version specified in the request.

Thus:

```text
M-SEARCH ST: IGD1
        ↓
response ST: IGD1

M-SEARCH ST: IGD2
        ↓
response ST: IGD2
```

A server MUST NOT answer an `IGD2` search with:

```text
ST: IGD1
```

and MUST NOT answer an `IGD1` search with:

```text
ST: IGD2
```

because the search response's `ST` is required to match the searched version.

---

## 2.3 A v2 device advertises its highest supported version

UDA 1.1/2.0 also specifies that devices advertise the **highest supported version** of each supported device/service type; they do not advertise multiple versions merely because the implementation remains backward compatible. A control point supporting v1 is expected to be able to interact with the advertised v2 type using the functionality defined by v1.

This is important because a strictly standards-conformant IGD2 advertisement set is not supposed to look like:

```text
IGD:1
IGD:2
WANDevice:1
WANDevice:2
...
```

as a conventional unsolicited advertisement set.

IGD2 is the advertised version; v1 interoperability is provided through versioned search compatibility.

---

# 3. M-SEARCH timing

## 3.1 Response delay

For multicast M-SEARCH, UDA specifies a randomized response delay in the interval:

```text
0 <= delay <= MX
```

where `MX` comes from the request.

A device may assume an MX value smaller than the value supplied by the control point, and an MX greater than 120 seconds is constrained by the architecture. The control point is expected to wait at least MX for responses. UDA 2.0 additionally states explicitly that a responder is permitted to transmit exactly at MX.

Therefore an implementation MAY deliberately defer its response to any individual M-SEARCH, provided the response is sent no later than the selected MX deadline.

---

## 3.2 The timing allowance is not a negotiation mechanism

Nothing in UDA defines:

```text
M-SEARCH :all
    ↓ wait
M-SEARCH :2
    ↓
therefore reinterpret the original :all
```

as a version-negotiation mechanism.

Nor does UDA give the responder permission to withhold a response to one search while waiting indefinitely to discover what other searches the control point might issue.

The architecture explicitly permits independent M-SEARCH transactions, and a control point may send them repeatedly because UDP discovery is lossy. UDA 2.0 specifically notes that control points should retransmit M-SEARCH and that the effective search period can exceed MX.

Therefore:

> **A server MUST NOT make the semantic result of an already received M-SEARCH dependent on a future M-SEARCH that has not yet arrived.**

This eliminates the proposed cross-target debounce as a requirements mechanism.

---

# 4. Empirical legacy-client facts: Xbox One

There is direct packet/log evidence for Xbox One using IGD:1 discovery.

A MiniUPnP capture records:

```text
SSDP M-SEARCH
ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1
```

followed by:

```text
GET /rootDesc.xml
GET /L3F.xml
GET /WANCfg.xml
GET /WANIPCn.xml
```

and subsequently:

```text
WANIPConnection:1#GetConnectionTypeInfo
WANIPConnection:1#GetNATRSIPStatus
WANIPConnection:1#AddPortMapping
```

The same test series showed the Xbox succeeding with the IGD1 presentation while failing when MiniUPnP was built in IGD2 mode; in the latter case the Xbox fetched `DP.xml` and subscribed to DeviceProtection before abandoning the sequence.

A separate MiniUPnP trace shows repeated Xbox One searches for:

```text
ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1
```

with the corresponding IGD1 SSDP response and `LOCATION: .../rootDesc.xml`.

The trace therefore establishes:

```text
Xbox One observed discovery:
    IGD:1

Xbox One observed SOAP protocol:
    WANIPConnection:1

Xbox One observed port-mapping operation:
    AddPortMapping
```

There is **no evidence in these captures of an Xbox One `M-SEARCH` for IGD:2**.

The evidence does **not** establish that Xbox One is intrinsically or universally IGD1-only. Later testing found combinations in which Xbox One obtained Open NAT with IGD2 as well. The defensible statement is therefore:

> **Xbox One is a demonstrably sensitive IGD1 control point whose interoperability can differ materially depending upon the IGD2 description presented by the gateway.**

That is stronger and more accurate than classifying Xbox as permanently v1-only.

---

# 5. The IGD2 description is materially different

IGD2 is not merely the IGD1 XML with `:1` strings replaced by `:2`.

The IGD2 device template defines a different device hierarchy and newer services. The standardized IGD2 set includes:

```text
InternetGatewayDevice:2
WANDevice:2
WANConnectionDevice:2
WANIPConnection:2
```

and may include DeviceProtection:1 and the IPv6 firewall-control service.

The IGD2 specification explicitly states that an IGD2 implementation contains the newest version of each applicable service and that earlier service versions are not used where a newer version exists.

The Xbox trace is therefore especially informative:

```text
IGD1 description
    ↓
Layer3Forwarding
WANCommonInterfaceConfig
WANIPConnection:1
    ↓
AddPortMapping
```

versus:

```text
IGD2 description
    ↓
Layer3Forwarding
DeviceProtection
    ↓
Xbox requests DP.xml
    ↓
failure
```

The MiniUPnP maintainer himself explicitly identified DeviceProtection as a possible source of the Xbox interoperability problem.

This is why **root-description compatibility is a real interoperability surface** rather than something that can safely be delegated to UDA's abstract backward-compatibility statement.

---

# 6. Existing implementation precedent

MiniUPnPd added:

```text
force_igd_desc_v1
```

specifically to force its IGD2-capable implementation to present the root description as IGD1.

Its configuration documents the option explicitly:

```text
# If compiled with IGD_V2 defined, force reporting IGDv1 in rootDesc
#force_igd_desc_v1=no
```

and its changelog records the addition as:

> "option force_igd_desc_v1 to force devices and services versions to 1 in IGD v2 mode"

in February 2018.

MiniUPnP therefore provides direct precedent for treating:

```text
implementation capability
        ≠
description presented to legacy control points
```

as an explicit compatibility concern.

This is evidence of deployed engineering practice, not merely theoretical design.

---

# 7. Modern v2-capable clients

The opposite side is also concrete.

Syncthing's IPv4 discovery code searches:

```text
IGD:2
IGD:1
```

in that order. Its IPv6 discovery deliberately searches IGD2 only because IPv6 UPnP is standardized only for IGD2 and combining IGD1 with it would lead to duplicates.

Tailscale's UPnP implementation uses `AddAnyPortMapping` when a `WANIPConnection:2` client is available and falls back to `AddPortMapping` otherwise.

Tailscale also explicitly prefers an IGD2 response when it receives multiple responses pointing to the same location:

> if it receives responses for both `InternetGatewayDevice:1` and `InternetGatewayDevice:2`, it keeps the IGD2 response.

This confirms that real modern clients perform active version probing and can distinguish an IGD2-capable gateway from an IGD1-only gateway.

---

# 8. Required facade model

The server SHALL implement one canonical internal mapping engine:

```text
                    +--------------------------+
                    |   canonical IPv4 NAT     |
                    |   mapping/lease engine   |
                    +------------+-------------+
                                 |
                 +---------------+---------------+
                 |                               |
          IGD1 compatibility facade       IGD2 modern facade
```

The facade is protocol presentation only.

The mapping database MUST NOT have independent "v1 mappings" and "v2 mappings". Both APIs MUST resolve to the same mapping objects and the same NAT/firewall state.

---

# 9. Discovery classification

For the purpose of this compatibility profile, classification is intentionally trivial.

## 9.1 Explicit IGD2 search

If a control point sends:

```text
M-SEARCH
ST: urn:schemas-upnp-org:device:InternetGatewayDevice:2
```

the server SHALL:

1. recognize the control point as v2-capable;
2. respond with:

```text
ST: urn:schemas-upnp-org:device:InternetGatewayDevice:2
```

3. provide a LOCATION that resolves to the IGD2 description;
4. make `WANIPConnection:2` discoverable in that description.

This is the positive v2 capability signal.

---

## 9.2 Explicit IGD1 search

If the control point sends:

```text
M-SEARCH
ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1
```

the server SHALL respond with:

```text
ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1
```

For the **compatibility facade**, the LOCATION SHOULD point to the IGD1-compatible root description.

This is the path that protects Xbox-class clients.

---

## 9.3 `ssdp:all`

A device does not advertise additional lower versions of a type; UDA describes `ssdp:all` as discovering the device's advertised capabilities. Therefore a gateway which supports IGD2 and advertises IGD2, but makes every `ssdp:all` response look exclusively IGD1, cannot claim that its discovery facade is a literal, complete implementation of the UDA advertisement model.

The correct engineering characterization is:

> **The universal facade is a compatibility mode that deliberately constrains the advertised/discoverable surface presented to generic legacy discovery.**

That is materially different from claiming formal UPnP certification for every aspect of the facade.

This is exactly why the implementation should make the policy explicit rather than hiding it inside the device-description generator.

---

# 10. The v1 advertisement surface

A device does not advertise additional lower versions. It also describes `ssdp:all` as discovering the device's advertised capabilities.

Therefore a gateway which:

```text
supports IGD2
advertises IGD2
but deliberately makes every ssdp:all response look exclusively IGD1
```

cannot simultaneously claim that its discovery facade is a literal, complete implementation of the UDA advertisement model.

The correct engineering characterization is:

> **The universal facade is a compatibility mode that deliberately constrains the advertised/discoverable surface presented to generic legacy discovery.**

That is materially different from claiming formal UPnP certification for every aspect of the facade.

This is exactly why the implementation should make the policy explicit rather than hiding it inside the device-description generator.

---

# 11. Recommended URL structure

Do **not** make one URL such as:

```text
/rootDesc.xml
```

return different XML depending on which client IP happens to request it.

That creates unnecessary statefulness and potential cache ambiguity.

Instead expose separate deterministic URLs:

```text
/igd/v1/rootDesc.xml
/igd/v2/rootDesc.xml
```

and corresponding service descriptions:

```text
/igd/v1/L3F.xml
/igd/v1/WANCfg.xml
/igd/v1/WANIPCn.xml

/igd/v2/L3F.xml
/igd/v2/DP.xml
/igd/v2/WANCommonIFC.xml
/igd/v2/WANIPCn.xml
...
```

The SSDP response selects the appropriate LOCATION:

```text
ST: IGD1
LOCATION: http://gateway/.../igd/v1/rootDesc.xml

ST: IGD2
LOCATION: http://gateway/.../igd/v2/rootDesc.xml
```

This removes any requirement to infer the presentation from a later HTTP request.

UPnP explicitly defines LOCATION as the URL for the root-device description, and requires it to be reachable by the control point receiving the response.

---

# 12. Do not use future-packet debounce to decide `:all`

The tempting implementation is:

```text
t0: receive :all
       |
       | wait for possible :2
       |
t1: receive :2
       |
       +--> turn original :all into v2
```

This SHOULD NOT be implemented.

The reasons are:

1. The `:all` transaction already has an MX response deadline.
2. UDA does not define cross-search correlation as negotiation.
3. A control point can send searches independently or repeatedly.
4. A later `:2` may arrive after the server has legitimately answered `:all`.
5. A server cannot know whether a later `:2` will ever arrive.

The permitted randomized delay is useful only within the response window of the individual request.

Therefore:

> **Classification MUST be based on the ST of the individual search, not on a future-search debounce heuristic.**

---

# 13. Optional response coalescing

An implementation MAY coalesce duplicate or near-duplicate searches from the same control point, but this is an optimization, not protocol negotiation.

For example:

```text
t=0.000 :all
t=0.002 :all
t=0.008 :all
```

may be collapsed into a single response schedule, provided all required responses are ultimately emitted according to the `ssdp:all` response rules.

The server MAY select:

```text
response_delay = random(0, MX)
```

or any deterministic delay no greater than the applicable MX that satisfies the specification.

It MUST NOT wait for a hypothetical future `:2` beyond the response window of the current M-SEARCH.

---

# 14. `:all` + `:2` from the same client

This is the most important practical case.

A modern client such as Syncthing may actively probe:

```text
:2
:1
```

and other real clients may also issue generic searches.

The server SHOULD treat each search as an independent request:

```text
M-SEARCH :all
    → v1 facade

M-SEARCH :2
    → v2 facade

M-SEARCH :1
    → v1 facade
```

A control point that knows v2 exists will discover the v2 location from the response to the explicit `:2` search.

This is vastly preferable to trying to retroactively rewrite the `:all` response.

---

# 15. Why returning v1 for `:all` is useful

Consider an Xbox-class client:

```text
M-SEARCH :all
M-SEARCH IGD:1
```

The server gives it the v1 presentation:

```text
IGD:1
Layer3Forwarding:1
WANCommonInterfaceConfig:1
WANIPConnection:1
```

The client therefore sees the exact protocol surface it has historically been observed to consume:

```text
GetConnectionTypeInfo
GetNATRSIPStatus
AddPortMapping
```

The Xbox trace is direct evidence that this path exists in the field.

No inference about Microsoft's internal implementation is required.

---

# 16. Why v2 clients still work

A modern client explicitly searching:

```text
IGD:2
```

receives:

```text
IGD:2
WANDevice:2
WANConnectionDevice:2
WANIPConnection:2
```

and can therefore use:

```text
AddAnyPortMapping
```

when desired.

Tailscale provides a concrete example of a modern implementation using `AddAnyPortMapping` when the v2 service exists and falling back to `AddPortMapping` otherwise.

Syncthing provides a concrete example of a modern IPv4 client probing IGD2 and then IGD1.

---

# 17. Version-specific SOAP semantics

The internal mapping API SHOULD be approximately:

```text
allocate_exact(
    protocol,
    external_port,
    internal_client,
    internal_port,
    remote_host,
    lease_duration,
    description
)

allocate_preferred(
    protocol,
    preferred_external_port,
    internal_client,
    internal_port,
    remote_host,
    lease_duration,
    description
)
```

Then:

```text
WIP1#AddPortMapping
WIP2#AddPortMapping
    → allocate_exact()

WIP2#AddAnyPortMapping
    → allocate_preferred()
```

This maintains one mapping table while preserving the semantic difference between exact-port and allocate-any semantics.

---

# 18. Architecture: one canonical engine, two presentation facades

```text
                    +--------------------------+
                    |   canonical IPv4 NAT     |
                    |   mapping/lease engine   |
                    +------------+-------------+
                                 |
                 +---------------+---------------+
                 |                               |
           IGD1 presentation            IGD2 presentation
                 |                               |
              /igd/v1/...                  /igd/v2/...
                 |                               |
            IGD1 facade                    IGD2 facade
                 |                               |
         WIP1 / exact                   WIP2 / exact
                                          WIP2 / any
```

Discovery policy:

```text
ST=ssdp:all
    => IGD1 LOCATION

ST=IGD1
    => IGD1 LOCATION
    => ST=IGD1

ST=IGD2
    => IGD2 LOCATION
    => ST=IGD2

ST=WIP1
    => WIP1 discovery response

ST=WIP2
    => WIP2 discovery response
```

The v1 and v2 descriptions MUST have distinct service URLs.

The canonical NAT state MUST be shared.

---

# 19. State machine

The actual discovery dispatcher can be this simple:

```text
receive M-SEARCH

validate:
    MAN == "ssdp:discover"
    MX present
    valid ST

switch ST:

    ssdp:all:
        schedule v1-compatible discovery response(s)

    IGD:1:
        schedule v1 response
        ST := IGD:1

    IGD:2:
        schedule v2 response
        ST := IGD:2

    WIP:1:
        schedule v1 service response
        ST := WIP:1

    WIP:2:
        schedule v2 service response
        ST := WIP:2

    otherwise:
        no response unless supported
```

No client database is required.

No source-IP inference is required.

No user-agent detection is required.

No future-search prediction is required.

No `rootDesc.xml` mutation is required.

---

# 20. Timing algorithm

For every M-SEARCH:

```text
deadline = receive_time + MX
delay = implementation_selected_random_delay
response_time = receive_time + delay
```

with:

```text
0 <= delay <= MX
```

The server MAY use a smaller effective maximum than the client supplied, as permitted by the architecture.

For a burst of duplicate requests, the server may coalesce internal work, but every required response must remain attributable to the corresponding search.

The server MUST NOT do:

```text
await :2
```

before deciding how to answer an already pending:

```text
:all
```

This would turn an optional timing heuristic into a non-standard version-negotiation protocol.

---

# 21. `LOCATION` design

Use deterministic version-specific URLs:

```text
http://192.0.2.1:49152/igd/v1/rootDesc.xml
http://192.0.2.1:49152/igd/v2/rootDesc.xml
```

The actual address is, of course, the gateway's LAN address.

Do not use:

```text
/rootDesc.xml
```

for both facades while varying the HTTP response based on source IP.

A static version-specific URL makes packet capture, caching, debugging, regression testing and client behavior substantially easier to reason about.

It also means the following trace is self-explanatory:

```text
M-SEARCH ST=:1
  LOCATION=/igd/v1/rootDesc.xml

M-SEARCH ST=:2
  LOCATION=/igd/v2/rootDesc.xml
```

---

# 22. Interaction with `ssdp:all`

The one deliberate policy exception is:

```text
ssdp:all → v1 facade
```

This should be treated as a **compatibility profile**, not as an assertion that the gateway does not support v2.

The reason for accepting that trade is empirical:

* Xbox One has been observed searching for IGD1 and then operating against WIP1.
* IGD2 descriptions introduce materially different services such as DeviceProtection.
* the same Xbox has exhibited failures when exposed to such an IGD2 description.
* MiniUPnP added an explicit forced-v1-description compatibility switch for IGD2 mode.

Thus generic discovery is intentionally conservative.

---

# 23. The unresolved standards boundary is now explicit

There is no unresolved timing question that needs to be solved experimentally.

The correct interpretation is:

```text
MX is a response-jitter budget.
It is NOT a cross-request version-negotiation budget.
```

The remaining standards compromise is instead architectural:

```text
strict UDA IGD2 advertisement model
        versus
legacy-client compatibility facade
```

That compromise should be represented as an explicit server mode.

It should not be hidden inside arbitrary response timing.

---

# 24. Test matrix

The implementation agent MUST construct at least these packet-level regression tests:

| Search     | Expected LOCATION      | Expected ST                             | Expected description |
| ---------- | ---------------------- | --------------------------------------- | -------------------- |
| `ssdp:all` | `/igd/v1/rootDesc.xml` | `ssdp:all`/appropriate response targets | IGD1 facade          |
| `IGD:1`    | `/igd/v1/rootDesc.xml` | `IGD:1`                                 | IGD1                 |
| `IGD:2`    | `/igd/v2/rootDesc.xml` | `IGD:2`                                 | IGD2                 |
| `WIP:1`    | v1 description         | `WIP:1`                                 | WIP1                 |
| `WIP:2`    | v2 description         | `WIP:2`                                 | WIP2                 |

Then:

### Xbox-class test

```text
M-SEARCH IGD1
GET v1 rootDesc
GET v1 service descriptions
SOAP WIP1
AddPortMapping
```

must succeed.

### Syncthing-class test

```text
M-SEARCH IGD2
M-SEARCH IGD1
GET v2 rootDesc
discover WIP2
```

must succeed.

### Tailscale-class test

```text
discover WIP2
AddAnyPortMapping
```

must succeed.

### Legacy-only test

```text
M-SEARCH ssdp:all
```

must receive only the compatibility presentation defined for the mode.

---

# 25. Final implementation rule set

The implementation agent should treat the following as normative requirements for this project:

```text
R1  One canonical IPv4 mapping engine.

R2  Separate v1 and v2 UPnP presentation layers.

R3  Explicit IGD:2 search is positive v2 evidence.

R4  Explicit IGD:1 search receives IGD:1 response.

R5  Implement the v2 features correctly and completely; no carve-outs.
    The v2 facade is not a stub: every exposed v2 service is a real,
    enforced implementation (see DeviceProtection below).
```

---

# 26. IGD:2 DeviceProtection Implementation Logic

Normative intent, stated once at the top: implement the v2 features
correctly and completely. No carve-outs. DeviceProtection in
particular is implemented as a genuine authorization subsystem, not as
an advertised endpoint over an always-authorized service.

## 26.1 Requirement

An IGD:2 presentation SHALL expose a fully functional:

```text
urn:schemas-upnp-org:service:DeviceProtection:1
```

service attached to the `InternetGatewayDevice:2` root device.

The v1 compatibility facade MUST NOT expose DeviceProtection.

This implements the IGD:2 security model rather than merely placing the service in `rootDesc.xml`. The IGD:2 device specification identifies DeviceProtection as a recommended component of the IGD:2 hierarchy, while IGD-specific security requirements remain mandatory.

## 26.2 Purpose

DeviceProtection is an authorization layer for UPnP services.

It is not merely authentication of the SOAP connection. It establishes identities/roles and determines whether a control point is authorized to invoke protected actions.

The underlying model is:

```text
Control Point
     |
     | UPnP SOAP request
     v
DeviceProtection authorization context
     |
     +---- authenticated / authorized
     |          |
     |          v
     |      target service action
     |
     +---- unauthenticated / unauthorized
                |
                v
             reject
```

DeviceProtection is explicitly intended to provide secure communication and access control to UPnP services.

## 26.3 Security model

Implement DeviceProtection as a genuine authorization subsystem:

```text
identity
   ↓
authentication/session
   ↓
role membership
   ↓
ACL/policy evaluation
   ↓
SOAP action authorization
```

Do NOT implement:

```text
DeviceProtection endpoint
       +
always-authorized WANIPConnection
```

as that would provide the appearance of IGD:2 security while leaving the protected service unrestricted.

RFC 6970's IGD/PCP interoperability guidance reinforces this interpretation: when IGD:2 is used, IGD:2 access-control requirements and authorization levels SHOULD be applied by default, and operations on behalf of another device should require authentication and authorization.

## 26.4 Root-device placement

The IGD:2 device description SHALL place:

```text
DeviceProtection:1
```

directly under:

```text
InternetGatewayDevice:2
```

unless the implementation is following another hierarchy explicitly permitted by the DeviceProtection specification.

The IGD:2 device specification specifically recommends connecting DeviceProtection to the InternetGatewayDevice in the device/service hierarchy.

## 26.5 Service implementation

Implement the complete standardized DeviceProtection:1 SCPD and its complete action/event surface.

Do not implement a reduced compatibility subset.

The implementation agent SHALL obtain the normative DeviceProtection:1 service specification and implement every required:

```text
action
argument
state variable
data type
event
SOAP error
authorization rule
```

defined there.

The service specification is the authoritative source for the exact action names, arguments, XML namespaces, data types and error codes. DeviceProtection:1 is the standardized UPnP Forum service dated February 24, 2011.

## 26.6 Public versus protected operations

The implementation SHALL distinguish:

```text
Public operations
    ↓
available without an authenticated security context

Protected operations
    ↓
require authentication + authorization
```

The service's own security policy MUST determine which operations are public.

The implementation MUST NOT make all operations public merely to maximize compatibility.

For an IGD server, operations that alter security-sensitive gateway state, particularly port mappings, firewall state, or security configuration, must flow through the authorization layer.

## 26.7 WANIPConnection integration

The authorization check occurs before the canonical mapping engine:

```text
SOAP WANIPConnection action
           |
           v
DeviceProtection authorization
           |
      authorized?
       /       \
     no         yes
     |           |
 SOAP error      v
             canonical
             NAT engine
```

This applies to both:

```text
WANIPConnection:2#AddPortMapping
WANIPConnection:2#AddAnyPortMapping
```

and to all other security-sensitive WANIPConnection operations.

The v1 facade remains a legacy unauthenticated compatibility surface and is therefore kept separate from this IGD:2 authorization path.

## 26.8 Security context

The implementation SHALL maintain an authenticated security context associated with the control point's DeviceProtection session.

That context SHALL identify at minimum:

```text
principal / user
authenticated state
roles
session validity / expiry
```

The authorization decision for a subsequent protected SOAP invocation MUST be derived from that context rather than from:

```text
source IP address
MAC address
SSDP search target
User-Agent
```

alone.

Those may be useful for diagnostics but MUST NOT constitute authentication.

## 26.9 ACL model

Implement the DeviceProtection ACL model as specified by the DeviceProtection service.

Conceptually:

```text
ACL:
    principal/role
        |
        +---- service/device scope
        |
        +---- permitted action set
```

The authorization engine should therefore support:

```text
principal
role
resource/service
action
allow/deny
```

as first-class objects.

Do not hard-code:

```text
LAN client == administrator
```

because that bypasses the security model.

## 26.10 Default security posture

Default installation SHALL use the restrictive interpretation of the IGD:2 security model:

```text
unknown control point
    → unauthenticated
    → only explicitly Public operations

authenticated principal
    → assigned role
    → ACL evaluation

no matching authorization
    → deny
```

This is consistent with the IGD2 security direction and with RFC 6970's recommendation that IGD:2 authorization controls be applied by default.

## 26.11 DeviceProtection absence is not an acceptable IGD:2 shortcut

Do not implement:

```text
IGD2 root description
    +
WIP2
    -
DeviceProtection
```

and call that a fully featured IGD:2 implementation.

The OCF IGD v2 definition explicitly identifies DeviceProtection as a security enhancement of IGD2, and the normative IGD2 device document includes DeviceProtection in the required hierarchy model.

For this project the implementation target is deliberately stronger:

> If the server exposes the IGD:2 facade, it also exposes and actually enforces DeviceProtection:1.

## 26.12 v1 facade isolation

The v1 description SHALL contain none of:

```text
DeviceProtection:1
```

or its control/event URLs.

Thus:

```text
v1 facade:
    Layer3Forwarding
    WANCommonInterfaceConfig
    WANIPConnection:1
    ...

v2 facade:
    Layer3Forwarding
    DeviceProtection:1
    WANIPConnection:2
    ...
```

This keeps Xbox/legacy clients from encountering the IGD:2 security-control surface that has been implicated in real Xbox interoperability failures. The Xbox/MiniUPnP capture specifically showed the legacy client fetching `DP.xml` when exposed to the IGD2 description.

## 26.13 Error handling

Authorization failure MUST be a proper UPnP SOAP fault using the DeviceProtection-defined mechanism where one exists.

Do not return:

```text
HTTP 404
HTTP 401
HTTP 403
```

as a substitute for the standardized UPnP application-level error unless the DeviceProtection specification explicitly calls for that behavior.

Likewise, do not convert authorization failures into generic WANIPConnection errors.

## 26.14 Eventing

Implement DeviceProtection eventing exactly as required by its service specification.

The implementation MUST maintain event subscriptions independently of ordinary SSDP discovery state.

An authorization change that affects evented security state SHALL generate the corresponding standardized event notification.

## 26.15 Persistence

Persistent security configuration SHOULD survive ordinary service restart/reboot according to the DeviceProtection specification and the gateway's security model.

Transient authentication/session state SHOULD NOT be persisted unless explicitly required by the specification.

At minimum distinguish:

```text
persistent:
    users / credentials
    role assignments
    ACL/policy configuration

transient:
    authenticated sessions
    challenge state
    nonces / tokens
```

## 26.16 Credentials

Credentials SHALL never appear in:

```text
SSDP
rootDesc.xml
SCPD XML
event notifications
ordinary diagnostic logs
```

Passwords or equivalent authenticators MUST be stored using the secure representation required by the DeviceProtection specification.

Do not invent a weaker password scheme for implementation convenience.

## 26.17 Cryptographic ceremonies

Where DeviceProtection specifies a cryptographic exchange, challenge, certificate, or security-token ceremony, implement the complete ceremony.

Do not replace it with:

```text
Basic Auth
Bearer token
shared static secret
source-IP whitelist
```

unless the DeviceProtection specification explicitly permits that mechanism as the corresponding standardized procedure.

The DeviceProtection specification exists specifically to provide secure communication and access control for UPnP services.

## 26.18 Authorization boundary for the canonical mapping engine

The canonical mapping engine MUST have no direct UPnP-facing bypass.

Every v2 SOAP entry point SHALL pass:

```text
SOAP request
    ↓
parse / validate
    ↓
resolve security principal
    ↓
authorize action
    ↓
mapping engine
```

Never:

```text
SOAP request
    ↓
mapping engine
```

for v2 services.

This ensures that a later addition of another control path cannot accidentally bypass DeviceProtection.

## 26.19 Testing

The implementation agent SHALL construct conformance tests for at least:

```text
unauthenticated public action
unauthenticated protected action
authenticated authorized action
authenticated unauthorized action
expired session
invalid credentials
invalid authorization context
ACL change
role change
service restart
device reboot
multiple simultaneous control points
```

and verify that the security result is independent of source IP.

Additionally test:

```text
v1 facade:
    no DeviceProtection exposure
    legacy AddPortMapping remains functional

v2 facade:
    DeviceProtection is discoverable
    authentication works
    authorization affects WIP2 operations
```

## 26.20 Interoperability policy

DeviceProtection is part of the **v2 facade only**.

The server therefore has:

```text
legacy discovery
    → v1 facade
    → no DeviceProtection

explicit v2 discovery
    → v2 facade
    → full DeviceProtection
    → authorized WIP2
```

This preserves the empirically demonstrated Xbox compatibility path while allowing modern v2 control points to receive a genuinely security-aware IGD2 device.

## 26.21 Implementation target

The implementation agent should interpret this document as:

> **Implement the complete DeviceProtection:1 standardized service and integrate it as the authorization boundary for the complete IGD:2 service set. Do not implement DeviceProtection as a stub, advertisement-only service, or optional compatibility feature.**

The fact that the base IGD2 document phrases DeviceProtection as **SHOULD** is therefore intentional at the specification level; this project chooses the stronger implementation target so that "IGD2" means a genuinely security-complete implementation rather than merely the `WANIPConnection:2` API surface.

---

# 27. Research annex: DeviceProtection:1 in the field (2026-09-16)

Research findings from primary and secondary sources on what "a real
DeviceProtection:1 implementation" means in deployed practice. The
conclusion up front:

> **The only widely-deployed open implementation is miniupnpd, and it
> implements a three-action subset of the specification. "Complete" per
> this milestone is therefore a deliberate superset of the reference,
> not a parity target. Every action the specification defines is
> implemented and enforced; nothing is scaffolded by name only.**

## 27.1 The reference implementation: miniupnpd

Miniupnpd (the OpenWrt/pfSense/DD-WRT default IGD) is the sole
widespread open implementation. Its own description generator
(`miniupnpd/upnpdescgen.c`) ships a DeviceProtection:1 SCPD whose
action surface is exactly:

```text
SendSetupMessage
GetSupportedProtocols
GetAssignedRoles
```

with state variables:

```text
SetupReady            (boolean, evented; the generated value is always 1)
SupportedProtocols    (string)
A_ARG_TYPE_ACL        (string)
A_ARG_TYPE_IdentityList
A_ARG_TYPE_Identity
A_ARG_TYPE_Base64     (bin.base64)
A_ARG_TYPE_String
```

The service is gated by the compile flag `ENABLE_DP_SERVICE`, and in
`IGD_V2` builds the `force_igd1` path (the `force_igd_desc_v1` option
from section 6) strips DeviceProtection and WANIPv6FirewallControl
from the emitted root description. The version-specific URLs from
section 21 map onto its `DP_PATH` / `DP_CONTROLURL` / `DP_EVENTURL`
macros.

Miniupnpd's own project notes state that IGD v2 support was added in
2011 and that IGD2 is still not enabled by default because of
interoperability issues.

Consequences for this milestone:

1. A comparator that "matches miniupnpd" would deliver only
   `SendSetupMessage` + `GetSupportedProtocols` + `GetAssignedRoles`
   and could still claim DeviceProtection presence. That is exactly
   the stub-class anti-pattern this milestone rejects.
2. The specification's full surface is the completion target, not the
   reference implementation's subset.
3. The reference's own gating and force-igd1 behaviour corroborate the
   facade thesis: the description presented to legacy discovery is an
   explicit, toggleable policy, separate from implementation
   capability.

## 27.2 The specification's full surface

The DeviceProtection:1 service specification (UPnP Forum, February
2011) defines the actions this milestone implements in full:

```text
GetSupportedProtocols
GetAssignedRoles
RequestUserLogin
ValidateIdentity
SendSetupMessage
GetACLData
AddACLEntry
RemoveACLEntry
GetListOfRoles
RevokeRole
GetRolesForAction
GetUserLoginChallenge
LoginWithPIN
LoginWithThirdParty
```

The authentication-protocol model carries at least the protocol
families X.509, RSA, Kerberos, username/password, and third-party
identity; `GetSupportedProtocols` reports the implemented set, and the
login flow comprises a challenge (`GetUserLoginChallenge`), a PIN
login (`LoginWithPIN`, administrator PUK versus user PIN), and a
certificate login (`LoginWithThirdParty` + `ValidateIdentity`), with
the setup ceremony running through `SendSetupMessage`. The ACL and
role surface (`GetACLData`, `AddACLEntry`, `RemoveACLEntry`,
`GetListOfRoles`, `RevokeRole`, `GetRolesForAction`) is persisted and
enforced, not reported.

At kickoff the normative PDF
(`UPnP-gw-DeviceProtection-v1-Service.pdf`) is obtained and the exact
argument tables, protocol strings, state-variable semantics and event
definitions are transcribed into the behaviour spec that lives with
the component. This annex records the shape; the PDF is the
authority.

## 27.3 What "complete and enforced" means here

```text
complete:
    14 actions implemented
    7 state variables declared as specified
    SetupReady event semantics as specified
    ACL and role state persisted per section 26.15
    the setup and login ceremonies implemented, not simulated

enforced:
    every protected WIP2 action passes the authorization boundary
    (section 26.7) with a real, session-derived principal
    an unauthenticated or unauthorized invocation receives the
    DeviceProtection-defined SOAP fault, not a stub approval
    the v1 facade exposes none of it (section 26.12)
```

The test obligations of section 26.19 (unauthorized action, expired
session, invalid credentials, ACL change, role change, restart,
reboot, multiple control points, source-IP independence) are the
verification that the implementation is not a scaffold. A stub that
answers names but never enforces fails every one of them by
construction; the conformance suite is the anti-stub gate.

## 27.4 The second reference: Orange igd2-for-linux

Orange-OpenSource's `igd2-for-linux` (imported from the retired
gitorious of the same name) is the Linux UPnP IGD updated to the
InternetGatewayDevice:2 specifications, with an OpenWrt custom feed
under `openwrt/`. Its source tree is a second primary reference for
this milestone, and it makes two points directly.

### 27.4.1 The dual-presentation switch exists in production

The tree ships TWO root device descriptions:

```text
gatedesc.xml     InternetGatewayDevice:2, WANDevice:2,
                 WANConnectionDevice:2, WANIPConnection:2,
                 WANIPv6FirewallControl:1, ... (no Layer3Forwarding,
                 no DeviceProtection)

gatedesc1.xml    InternetGatewayDevice:1, WANDevice:1,
                 WANConnectionDevice:1, WANIPConnection:1, ...
```

This is section 11's model operating as a shipped configuration:
the capability is v2, and the presentation to a given control point is
a policy choice between two deterministic descriptions. It corroborates
the facade thesis from a production codebase, not just from the
miniupnpd changelog.

One divergence from this milestone's requirement: both root descs
point at the SAME service SCPD URLs (`/gateconnSCPD.xml` et al.).
Section 21's "the v1 and v2 descriptions MUST have distinct service
URLs" is therefore deliberately stricter than the Orange precedent;
the strictness exists for determinism and cache clarity and is
retained.

### 27.4.2 The shared connection SCPD is a vendor-extended superset

The one shared `gateconnSCPD.xml` contains WIP1 actions (including
`GetNATRSIPStatus`, which is a WIP1-only action) together with the
v2-era extensions `AddAnyPortMapping`, `DeletePortMappingRange` and
`GetListOfPortMappings`. The SCPD itself does not declare a
serviceType; version attribution lives in the root description that
references it. The single-superset-SCPD pattern is a real-world third
shape beside miniupnpd's strict versioning and this milestone's
distinct-service-URLs model.

### 27.4.3 DeviceProtection is absent there too

No file in the tree carries DeviceProtection; neither root description
exposes the service. A major carrier's production IGD2 therefore ships
without any DeviceProtection surface (and without Layer3Forwarding),
confirming how little of the IGD2 hierarchy the deployed ecosystem
actually implements.

### 27.4.4 The field picture, updated

```text
miniupnpd   IGD2 optional, off by default; DP = 3 actions
            (SendSetupMessage, GetSupportedProtocols,
            GetAssignedRoles), no working login/ACL ceremonies

Orange igd2 IGD2 with WIP2 + WANIPv6FirewallControl; dual root descs;
            shared superset SCPD; DP absent entirely

this milestone
            complete DP:1 (14 actions, enforced), dual facades with
            distinct per-version service URLs
```

No deployed open implementation provides even a working subset of the
DP login, setup and ACL ceremonies. "Complete" per this milestone is
therefore a superset of every reference found; there is no reference
that can be matched while remaining non-stub, which is precisely the
reason the specification text, not any implementation, is the
completion authority.