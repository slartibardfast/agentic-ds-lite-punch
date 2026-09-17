# Milestone: adaptive UPnP IGD v1/v2 compatibility facade

- Status: specified 2026-09-16; every build-sequence task receipted. T1
  (#disc-presentation), T2 (#v2-service-set) and T3 (#canonical-api)
  landed in the component, and T4 (#bench-matrix) ran on the deployed box
  2026-09-17 with all 31 probes passing (RESULTS-2026-09-17-bench-matrix.md).
  The IGD_V2 gate is on and the device presents the v1 and the v2 facade
  together; the mapping engine is reached through allocate_exact and
  allocate_preferred; and the running artifact is the one built from
  component 2158485, which the router now carries.
- Scope: the ds-lite-punch UPnP facade (plan/0007 phase E successor);
  builds on the deployed 34d48c1-era facade and the lease policy.
- This document is the milestone specification. The build-sequence
  tasks are defined below; the behaviour spec (allium lane) lives with
  the component code as implementation lands.

## Build sequence

### Define the discovery and presentation layer {#disc-presentation}

- verify: cargo test (the test matrix, burst rows included);
  cargo clippy clean of new warnings
- inputs: mdbook plan text, the deployed facade code
- delivers the per-control-point burst state machine
  (DISCOVERY_DEBOUNCE = 1 s), the :1/:2/:all classification, the
  /igd/v1 and /igd/v2 URL structure, and the IGD_V2 gate that mounts
  the v2 surface only when its complete service set is real.

### Mount the v2 service set (WIP2 + DeviceProtection:1) {#v2-service-set}

- verify: the test matrix's v2 rows; the conformance suite;
  the DP SCPD transcribed from the normative PDF (the authority) and
  every one of its 13 actions enforced; the WIP2 SCPD transcribed from
  the WANIPConnection:2 PDF and every one of its fourteen REQUIRED
  actions dispatched (table 2-10's device column; the seven OPTIONAL
  ones are neither advertised nor dispatched)
- inputs: the DeviceProtection:1 service specification PDF, internalized
  at component docs/upnp-dp1/ (commit c5609cd: the full OCR
  transcription with the seven List-of-Figures diagrams and the ACL
  schema fragment re-hosted locally, the signed figure URLs expired and
  gone; the source PDF is committed alongside as the authoritative
  rendering), the WANIPConnection:2 service specification, internalized
  at component docs/upnp-wip2/ (the source PDF, the conversion with its
  five figure crops re-hosted under docs/upnp-wip2/images/ before their
  signed URLs expired, and the contract transcribed in TRANSCRIPTION.md),
  the canonical mapping engine
- delivers WIP2 (AddAnyPortMapping, the superset SCPD set) behind the
  DeviceProtection authorization boundary,
  the complete DP:1 service, ACL and role persistence, the login and
  setup ceremonies, and the event surface. The IGD_V2 gate flips on
  here and stays on.

### Canonicalize the mapping API {#canonical-api}

- verify: unit tests for allocate_exact versus allocate_preferred
  semantics over the one engine
- inputs: the current upsert/add_mapping paths
- delivers the allocate_exact / allocate_preferred split (the version-specific SOAP semantics)
  so WIP1 and WIP2 resolve to the same mapping objects unchanged.

### Bench the client matrix {#bench-matrix}

- verify: the Xbox-class, Syncthing-class, Tailscale-class and
  legacy-only sequences of the test matrix and the discovery deadline
  assertions, against the deployed box
- inputs: the deployed facade, the console chain, a v2-capable client
- delivers the empirical record of the burst policy and of the
  actual IGD2-mode failure driver (the DeviceProtection-causation re-read).

This document specifies an implementation architecture for a new IPv4
UPnP Internet Gateway Device (IGD) server whose principal requirement
is simultaneous interoperability with:

* legacy IGD:1 control points, among them observed Xbox One behavior;
* modern IGD:2 control points;
* clients that perform discovery using `ssdp:all`;
* clients that explicitly search for `InternetGatewayDevice:2`;
* clients that probe both IGD:2 and IGD:1.

The design deliberately separates the **canonical NAT/mapping implementation** from the **UPnP discovery and description facade**.

The central conclusion is:

> **`ssdp:all` response selection is deferred for a bounded, per-control-point discovery-coalescing window (no longer than the `:all` request's MX). If an explicit IGD:2 search from the same control point is observed inside the window, the pending `ssdp:all` search and the `IGD:2` search are both answered from the IGD:2 facade. Otherwise the pending `ssdp:all` search is answered from the IGD:1 compatibility facade. An `IGD:1` search never affects the classification and is answered from the v1 facade independently. This is a deliberate, bounded deviation from a strict no-cross-request-negotiation reading of UDA; it is deterministic over a window, not a heuristic over long-lived state.**

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

## `ssdp:all` is part of UDA 1.0

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

## Explicit version searches

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

## A v2 device advertises its highest supported version

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

## Response delay

For multicast M-SEARCH, UDA specifies a randomized response delay in the interval:

```text
0 <= delay <= MX
```

where `MX` comes from the request.

A device may assume an MX value smaller than the value supplied by the control point, and an MX greater than 120 seconds is constrained by the architecture. The control point is expected to wait at least MX for responses. UDA 2.0 additionally states explicitly that a responder is permitted to transmit exactly at MX.

Therefore an implementation MAY deliberately defer its response to any individual M-SEARCH, provided the response is sent no later than the selected MX deadline.

---

## The timing allowance is not a negotiation mechanism

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

## Explicit IGD2 search

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

## Explicit IGD1 search

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

## The `ssdp:all` rule

A device does not advertise additional lower versions of a type; UDA describes `ssdp:all` as discovering the device's advertised capabilities.

The v1/v2 decision for a pending `ssdp:all` search is:

```text
:all received
    -> open a burst window (deadline = receive + MX(:all))
    -> defer the response, do not answer yet

:2 from the same control point inside the window
    -> classify the pending :all as v2
    -> answer the pending :all from the v2 facade (still before its MX)
    -> answer the :2 from the v2 facade

window expires with no :2
    -> answer the pending :all from the v1 compatibility facade

:1 from the same control point
    -> independent request: answered from the v1 facade immediately;
       never influences the :all classification
```

The window bound is the implementation parameter
`DISCOVERY_DEBOUNCE = 1 s`: the server's assumed-MX floor (per UDA the
server may assume a smaller MX, and a well-formed request carries at
least the default of 1 s), so the window never exceeds any valid MX of
the pending `:all`. Per-control-point burst state is short-lived: it
exists only while at least one `:all` response is deferred, and
expires with it. There is no long-lived client database, no source-IP
learning beyond identifying the control point for the window's
duration, and no state is kept once the window closes.

This replaces the earlier fixed rule "ssdp:all is always answered from
the v1 facade": the bounded burst debounce gives the reversal rationale,
and the Livebox finding records the production behaviour that
superseded it.

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

# 12. Bounded burst debounce: the deliberate exception

This section supersedes an earlier absolute in this document, which
required classification to rest on the ST of the individual search and
forbade any dependence on a search still to come. The superseded text, kept
verbatim because it is the thing being departed from:

```host-lint:ignore
a server MUST NOT make the semantic result of an already received M-SEARCH
dependent on a future M-SEARCH that has not yet arrived. Classification
MUST be based on the ST of the individual search, not on a future-search
debounce heuristic.
``` The
reversal is recorded in [call/0020](https://github.com/slartibardfast/agentic-ds-lite-punch/blob/main/call/0020-deferred-ssdpall-classification.md).
The rejection that stands is of
UNBOUNDED debounce; the mechanism adopted is a BOUNDED, deterministic
one.

The adopted state machine is per discovery burst, per control point:

```text
BURST {
    start = receive(:all)
    deadline = start + MX(:all)
    seen_v2 = false
}
```

At `:all`: create the burst and defer the response. At `:2` from the
same control point inside the window: set `seen_v2 = true` and
schedule the `:all` and `:2` responses together, both still before
their respective MX deadlines. At window expiry: answer the pending
`:all` from `seen_v2 ? v2 : v1`. An `:1` search is never consulted:
it is an independent request answered from the v1 facade immediately.

The constraints that keep this bounded and deterministic:

1. The window is the implementation parameter `DISCOVERY_DEBOUNCE
   = 1 s` (the ssdp:all rule). One second is the UDA default for a missing
   MX, so the server may assume it as the MX floor, and the window
   never exceeds any valid MX of the pending `:all`.
2. The window state is per control point, keyed only for the window's
   lifetime; it expires with the deferred response. No long-lived
   client database is created.
3. A delayed `:all` response is always sent before its own MX (the
   debounce expires at 1 s, which is at most that MX), so no search is
   starved while another is awaited beyond the allowed response
   window.
4. Duplicate `:all` retransmissions inside the window coalesce onto
   the single pending response schedule (the burst-window coalescing).
5. `:1` never triggers or suppresses the v2 classification.

The implementation holds the `:all` response for up to
`DISCOVERY_DEBOUNCE = 1 s`. It releases early only when an observed
`:2` permits an earlier v2 answer. The `:2` response itself obeys its
own MX deadline independently. This is deliberate product behavior,
not an accidental compatibility heuristic (call/0020 records the
decision).

Why this is adopted despite being a deviation: it makes `ssdp:all` a
capability-probing request with the explicit `:2` search as the
disambiguator, which solves the practical Xbox-versus-modern split without
permanently fixing generic discovery to v1. The Livebox
reverse-engineering (the research annex) showed production serves `ssdp:all`
from v2; the burst rule decides *when* v2 is safe to present, with the
v1 compatibility presentation as the drop-dead default.

---

# 13. Burst-window coalescing

Duplicate or near-duplicate searches from the same control point are
collapsed onto the burst's single response schedule:

```text
t=0.000 :all
t=0.002 :all
t=0.008 :all
```

All three retransmissions are answered by the burst's one response
(deferred per the bounded burst debounce, then resolved from `seen_v2 ? v2 : v1`),
provided every required response is emitted before its own MX. The
coalescing window IS the capability window: it exists only while a
response is deferred and doubles as the span in which an `:2` flips
the classification.

The server MAY select:

```text
response_delay = random(0, MX)
```

or any deterministic delay no greater than the applicable MX that
satisfies the specification. The response to a search is never delayed
beyond that search's own window, and no search is held open waiting
for a hypothetical future `:2` past the deadline of the bounded burst debounce's
burst window.

---

# 14. `:all` + `:2` from the same client

This is the most important practical case.

A modern client such as Syncthing may actively probe:

```text
:2
:1
```

and other real clients may also issue generic searches.

Under the burst rule the behavior is:

```text
M-SEARCH :all
    -> burst window opens; response deferred (the bounded burst debounce)

M-SEARCH :2   (same control point, inside the window)
    -> pending :all resolves to v2
    -> both :all and :2 answered from the v2 facade

M-SEARCH :1
    -> independent; answered from the v1 facade immediately
```

A burst that contains an explicit `:2` therefore yields the v2
presentation for BOTH the generic and the versioned search of the same
control point, without permanently attaching v1 to generic discovery.
A control point that never issues `:2` receives the v1 compatibility
presentation for its `:all` once the window expires.

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
        open a burst window and defer (see the ssdp:all rule)
        resolve at the window deadline from seen_v2 ? v2 : v1

    IGD:1:
        schedule v1 response
        ST := IGD:1

    IGD:2:
        mark the burst seen_v2 (if any), schedule v2 response
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

The server MAY use a smaller effective maximum than the client
supplied, as permitted by the architecture. For a pending `ssdp:all`
search the effective deadline is `receive_time + DISCOVERY_DEBOUNCE`
(1 s), the assumed-MX floor that also bounds the burst window
(the ssdp:all rule and the bounded burst debounce); the deferred response is released at or before
that deadline, early if a `:2` flips the classification.

For a burst of duplicate requests, the server may coalesce internal
work, but every required response must remain attributable to the
corresponding search.

The only permitted cross-search dependency is the recorded, bounded
one: a pending `:all` may await a `:2` from the same control point,
but never past `DISCOVERY_DEBOUNCE`, and never involving `:1`
(sections 12 and 14). Any unbounded form of "await `:2` before
deciding `:all`" remains prohibited.

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

The policy exception is now conditional via the burst rule (sections
the ssdp:all rule and the bounded burst debounce):

```text
ssdp:all (no :2 in the window) -> v1 compatibility facade
ssdp:all (with :2 in the window) -> v2 facade
```

The v1 answer remains the drop-dead default for generic discovery,
treated as a **compatibility profile**, not as an assertion that the
gateway does not support v2. The reasons for the conservative default
are empirical:

* Xbox One has been observed searching for IGD1 and then operating against WIP1.
* IGD2 descriptions introduce materially different services such as DeviceProtection.
* the same Xbox has exhibited failures when exposed to such an IGD2 description.
* MiniUPnP added an explicit forced-v1-description compatibility switch for IGD2 mode.

The burst rule adds the flip side: a control point that demonstrably
searches for IGD2 inside the window gets the v2 presentation for its
generic discovery too, which matches the Livebox production behavior of
serving v2 to generic discovery for capable clients.

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
| `ssdp:all` alone (no `:2` in window) | `/igd/v1/rootDesc.xml` | `ssdp:all`/appropriate response targets | IGD1 facade, released at `receive + DISCOVERY_DEBOUNCE` |
| `ssdp:all` then `IGD:2` within `DISCOVERY_DEBOUNCE` | `/igd/v2/rootDesc.xml` | `ssdp:all`/appropriate targets | IGD2 facade, released early |
| `ssdp:all` then `IGD:1` within the window | `/igd/v1/rootDesc.xml` | `ssdp:all`/appropriate targets | IGD1 facade; the `:1` does not upgrade |
| `IGD:1`    | `/igd/v1/rootDesc.xml` | `IGD:1`                                 | IGD1                 |
| `IGD:2`    | `/igd/v2/rootDesc.xml` | `IGD:2`                                 | IGD2                 |
| `WIP:1`    | v1 description         | `WIP:1`                                 | WIP1                 |
| `WIP:2`    | v2 description         | `WIP:2`                                 | WIP2                 |

Every burst case MUST also assert the deadline property: the `:all`
response arrives within `receive + DISCOVERY_DEBOUNCE`, and a `:2`
response within its own MX.

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

R6  Deferred `ssdp:all` classification with
    `DISCOVERY_DEBOUNCE = 1 s`: a pending `:all` is held up to one
    second (the assumed-MX floor) and answered from the v2 facade only
    if an `IGD:2` search from the same control point is observed in
    the window; otherwise from the v1 facade. An `IGD:1` search never
    influences the classification (the ssdp:all rule, the bounded burst debounce, the same-client rule, call/0020).
```

---

# 26. IGD:2 DeviceProtection Implementation Logic

Normative intent, stated once at the top: implement the v2 features
correctly and completely. No carve-outs. DeviceProtection in
particular is implemented as a genuine authorization subsystem, not as
an advertised endpoint over an always-authorized service.

## Requirement

An IGD:2 presentation SHALL expose a fully functional:

```text
urn:schemas-upnp-org:service:DeviceProtection:1
```

service attached to the `InternetGatewayDevice:2` root device.

The v1 compatibility facade MUST NOT expose DeviceProtection.

This implements the IGD:2 security model rather than merely placing the service in `rootDesc.xml`. The IGD:2 device specification identifies DeviceProtection as a recommended component of the IGD:2 hierarchy, while IGD-specific security requirements remain mandatory.

## Purpose

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

## Security model

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

## Root-device placement

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

## Service implementation

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

## Public versus protected operations

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

## WANIPConnection integration

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

## Security context

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

## ACL model

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

## Default security posture

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

## DeviceProtection absence is not an acceptable IGD:2 shortcut

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

## v1 facade isolation

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

This keeps Xbox/legacy clients from encountering the IGD:2
security-control surface. The association is correlational, not
causal: the Xbox/MiniUPnP capture showed the legacy client fetching
`DP.xml` in IGD2 mode before abandoning the sequence, but no evidence
shows the DP service itself caused the abandonment (see 27.5). The v1
facade policy rests on the direct trace evidence that Xbox consumes
IGD1 + WIP1 successfully, not on the DeviceProtection hypothesis.

## Error handling

Authorization failure MUST be a proper UPnP SOAP fault using the DeviceProtection-defined mechanism where one exists.

Do not return:

```text
HTTP 404
HTTP 401
HTTP 403
```

as a substitute for the standardized UPnP application-level error unless the DeviceProtection specification explicitly calls for that behavior.

Likewise, do not convert authorization failures into generic WANIPConnection errors.

## Eventing

Implement DeviceProtection eventing exactly as required by its service specification.

The implementation MUST maintain event subscriptions independently of ordinary SSDP discovery state.

An authorization change that affects evented security state SHALL generate the corresponding standardized event notification.

## Persistence rules

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

## Credentials

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

## Cryptographic ceremonies

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

## Authorization boundary for the canonical mapping engine

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

## The conformance suite

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

## Interoperability policy

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

## Implementation target

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

## The containment for callers without the lift

The authorization boundary sits in front of the mapping
engine, and the v1 facade isolation keeps the v1 face unauthenticated for the console-class
control points that cannot speak DeviceProtection. Between them sat a gap
that the specification closes for us: 2.5.16.2, 2.5.18.2, 2.5.14.2 and
2.5.21.3 RECOMMEND a policy for unauthenticated and unauthorized control
points, and the engine enforced none of it. It checked only that the named
`InternalClient` lay somewhere in the LAN /24. Any device on the LAN could
therefore open a door for another host, on any port, and the router itself
was within its reach.

That is not bookkeeping on this box. A mapping is an ingress path punched
through CGNAT that terminates on a host the caller names, and the mapping
table is therefore the set of doors into the LAN. The recommended policy is
the ceremony-free half of protecting it, and it is now enforced.

### The clauses and where each binds

- **The caller's own host.** A request that names another host is 606, and
  an entry that is not the caller's own is not listed, not enumerable and
  not deletable. This clause needs no remedy, so it binds **both faces**,
  and it is the one that matters on the v1 face, where no authentication
  exists.
- **The port floor.** Internal and external ports at or above 1024, with
  the wildcard external port admitted because it resolves above the floor
  by construction. This clause binds **the v2 face**, where a control point
  can lift it by authenticating; low-port self-mapping is common enough
  that a remedy-free refusal on the legacy face would be a compatibility
  break rather than a policy.
- **The reads.** A contained caller's Listing and enumeration hold only its
  own entries at or above the floor, and a specific read of another
  client's entry is 606 rather than "not found". This binds **both faces**
  as well, and for the same reason the address clause does: a read confers
  no capability, but the table is the ingress map (which internal host is
  reachable from outside, on which port, over which protocol, with how much
  lease left), and on this box that map is the artefact the punch work
  creates. One view therefore serves reads and writes on either face.

### The lift, and what it does not cost the operator

A live DeviceProtection session whose roles satisfy Basic lifts every
clause; Admin satisfies Basic, so it lifts them too. The lift is decided by
the same policy function the boundary gate uses (`dp::authorize` against
`DpAuthz::Roles(["Basic"])`), so the two cannot drift apart. On the v2 face
an unauthenticated mutator is refused by the gate before the containment is
consulted, and the containment is the reason a *public* v2 read is still
confined.

A lift belongs to the principal rather than to a face, so a control point
that authenticates over DeviceProtection reaches the whole table on either
face: the v1 read containment has a remedy, and it is the remedy the v2
face provides. Nothing privileged depends on the anonymous read in the
meantime, because the daemon already writes the whole index to its state
file (`/tmp/dslp/upnp.tsv` while it runs), which is a local read rather than
a network one. An earlier draft of this section kept the v1 reads whole to
preserve anonymous diagnostics; that was overstated, since the local index
already serves them.

### Mechanics

A `Contain { caller, high_port }` value is computed once in the dispatcher
and passed into the engine as a view, so the containment sits under the
boundary gate rather than beside it. The two allocation entry points take a
`MappingReq`, which is also what makes the exact and preferred pair differ
in port resolution alone. A range delete skips what the caller may not
touch and continues, which is the rule 2.5.19.2 gives, with an empty
selection still 730.

### Evidence

- `containment_predicates` pins both clauses, the wildcard, and the "the
  floor never licenses another host" case.
- `containment_view_over_the_table` drives a contained caller over seeded
  entries: the listing, the specific read (606 for another client's entry),
  the enumeration (the index space is what the caller may see, so a walk
  past the end still terminates on 714), the single delete, and the range
  delete with the skip rule.
- The `dp_boundary_wire` wire test asserts, against a seeded table holding
  another host's entry: the v1 face refuses a request naming another host
  with 606 while admitting the caller's own request past the containment to
  the engine; a read of the other host's entry is 606 on either face and
  the contained enumeration ends at index 0 with 714; and, once a
  DeviceProtection session is established, the same read answers on either
  face, which is the lift riding the principal rather than the face.

Component 58fed63, host pin recorded with it.

## The requested port is a per-client label

The mapping table is keyed `(client, external port, protocol)`. Several
control points may hold the same requested port, each with its own slot and
its own real external tuple, which is what lets two consoles both ask for
`3074/UDP`. The reasoning, and the two uplinks it covers, are in
[call/0022](https://github.com/slartibardfast/agentic-ds-lite-punch/blob/main/call/0022-requested-port-is-a-per-client-label.md);
this section records what the facade does with it.

- A write replaces only the caller's own entry at that port. Another
  requester's entry at the same port is never touched, and is never a stray
  to tear down, which retires the earlier behaviour where a second claimant
  evicted the first and silently broke its mapping.
- `GetSpecificPortMappingEntry` and `DeletePortMapping` resolve to the
  caller's own entry at that port, or 714, because their keys carry no client
  and the port is the caller's handle. The containment therefore no longer
  answers 606 for another client's port: that port is not in the caller's
  namespace at all, and the lift is observable through the enumeration and
  the listing, with the range delete as the bulk path.
- The any-port path (`allocate_preferred`) still matters where the device owns
  the port: the first holder of a requested port may be given that port
  itself, and a later claimant gets a different one and is told so through
  `NewReservedPort`.

## The operator bootstraps the store

The boundary above needs an identity to have any effect, and the
specification's in-band way to create the first one is the introduction
protocol this milestone defers. A fresh device therefore refuses every
role-gated action and nothing can lift the containment. The bootstrap is the
operator's: a root-owned `/etc/ds-lite-punch.acl` in the store's own
tab-separated form, which the procd script copies into the state directory at
start and only when no store exists, so it creates the first identity without
reverting a store the device already holds. Absent it the fail-closed refusal
stands. The reasoning and the exact consequences are in
[call/0023](https://github.com/slartibardfast/agentic-ds-lite-punch/blob/main/call/0023-the-operator-bootstraps-deviceprotection.md);
the file's format and the PBKDF2 derivation are in the component's
`deploy/ds-lite-punch.env` beside the service, and the mechanism was verified
on the deployed box (seed fires, the credential reaches Basic over the wire, a
store already present is not clobbered).

## The miniupnpd reference

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
from the precedent implementation) strips DeviceProtection and WANIPv6FirewallControl
from the emitted root description. The version-specific URLs from
the LOCATION design map onto its `DP_PATH` / `DP_CONTROLURL` / `DP_EVENTURL`
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

## The specification's full surface

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

## What "complete and enforced" means here

```text
complete:
    13 actions implemented (the authoritative surface; an earlier
        miniupnpd-derived count of 14 carried wrong names:
        RequestUserLogin, ValidateIdentity, AddACLEntry, LoginWithPIN
        and friends are not actions of this service; superseded)
    7 state variables declared as specified
    SetupReady event semantics as specified
    ACL and role state persisted per the persistence rules (dp.tsv)
    the setup and login ceremonies implemented, not simulated
    the fourteen REQUIRED WIP2 actions (table 2-10's device column)
        carrying their own argument tables in the published SCPD, and
        the seven OPTIONAL ones neither advertised nor dispatched (the
        placeholder named the v2 actions without describing them and
        declared a bogus 22nd; the second transcription took all
        twenty-one as required)
    23 WIP2 state variables with the specified eventing (five evented:
        PossibleConnectionTypes, ConnectionStatus, ExternalIPAddress,
        PortMappingNumberOfEntries, SystemUpdateID)

enforced:
    every protected WIP2 action passes the authorization boundary
    (the WANIPConnection integration) with a real, session-derived principal
    an unauthenticated or unauthorized invocation receives the
    DeviceProtection-defined SOAP fault, not a stub approval
    the v1 facade exposes none of it (the v1 facade isolation)
```

The test obligations of the conformance suite (unauthorized action, expired
session, invalid credentials, ACL change, role change, restart,
reboot, multiple control points, source-IP independence) are the
verification that the implementation is not a scaffold. A stub that
answers names but never enforces fails every one of them by
construction; the conformance suite is the anti-stub gate.

## Implementation record (the #v2-service-set dispatch)

The normative contract is transcribed (component docs/upnp-dp1/
TRANSCRIPTION.md) and the surface is wired: the thirteen actions behind
`/ctl/DP`, the PKCS5 ceremony with the spec's exact parameters (STORED =
PBKDF2-HMAC-SHA-256, salt = Name || Salt, c = 5000; authenticator =
first 128 bits of HMAC-SHA-256(STORED, Challenge || DeviceID ||
ControlPointID)), the identity-must-be-in-ACL login rule (2.6.6.5),
the five-failure backstop (2.6.6.8), live ACL/role evaluation so grants
and revocations take effect on existing sessions, and the DeviceProtection
-defined faults (600/606/701/704). Sessions are keyed by the control
point's address, the plain-HTTP analogue of the spec's authenticated TLS
session (the security context: the address keys the store; the decision is a pure
function of the principal's roles). The role vocabulary is the spec's own
Public/Basic/Admin (the DeviceProtection role definitions) with the recommended Admin-over-Basic
hierarchy (2.6.3.2, 2.6.4.5). The v2 WIP2 mapping mutators pass the
boundary (the WANIPConnection integration); the :1 face stays legacy-unauthenticated.

Deferrals at the time of the dispatch, all closed but one: the argument
tables transcription, the AddAnyPortMapping wildcard request, the range
refusals and the version 2 lease reading landed at components aaca491
and a339747 (sections 27.3b and 27.3c); the WPS registrar transport is
still absent (SendSetupMessage answers 600/704, and this wired IGD runs
no WPS registrar). Body of the conformances: dp.rs
the conformance suite + a wire-level suite driving the HTTP/SOAP path through
login to the opened boundary and the logout re-close.

### The WIP2 transcription (component aaca491)

The WANIPConnection:2 service is now transcribed from its own normative
document (component docs/upnp-wip2/TRANSCRIPTION.md), the source PDF and
its conversion committed beside it as docs/upnp-wip2/, with the five
figure crops re-hosted locally (component 93138a2: the conversion carried
its diagrams as signed object-store URLs, and the signatures expire, so a
clone made later would have had a document whose figures resolve to
nothing). The published
`SCPD_WIP2` is that document projected onto what a device must provide:
the fourteen REQUIRED actions of the spec's table 2-10, each with the
argument table of its own section; the 23 state variables
of table 2-2 plus the two argument types, with the allowed values and
ranges of tables 2-3 to 2-8; and the five evented variables of table 2-9,
the mapping pair evented together per 2.4.4 and 2.4.5. The
`v2_builders_carry_the_surface` test asserts the surface action by
action, so a description that names an action without describing it
fails, and it rejects the placeholder's bogus action and invented
argument types by name.

`GetListOfPortMappings` now answers with the PortMappingList fragment of
section 2.3.25 (a PortMappingList of PortMappingEntry elements in the
`urn:schemas-upnp-org:gw:WANIPConnection` namespace, NewLeaseTime as the
remaining lease per 2.4.6) rather than an invented element tree. The
schema URL the spec names no longer serves the schema, so the sample
document of 2.3.25.2 is the shape authority. `NewDescription` is reported
empty because the device does not persist the control point's
description string; storing it is a recorded fidelity gap, not a claim
that the control point sent nothing.

### The v2 readings the transcription required (component a339747)

The behaviours 27.3b named as still open are implemented, each with the
section that requires it and a test that a name-only implementation
fails:

- `DeletePortMappingRange` and `GetListOfPortMappings` answer 730
  PortMappingNotFound on an empty range (2.5.19.2, 2.5.21.3) and 733
  InconsistentParameters when the start port is above the end (2.5.19.6,
  2.5.21.7). Both codes joined the fault table as 730 and 733.
- `AddAnyPortMapping` with `NewExternalPort` 0 reserves the lowest
  requested port at or above 1024 that no entry of the protocol claims
  and returns it as `NewReservedPort` (2.5.17). The spec's other reading
  of 2.5.17.3, a wildcard mapping answered as 0, is not installable here:
  the AFTR is the mapper and it maps one tuple at a time.
- A lease of 0 on the v2 face is read as 604800 (table 2-6), while the v1
  face keeps 0 as the permanent mapping a legacy control point means by
  it.

The wire suite drives all four through HTTP/SOAP under an open session;
two unit tests pin the port choice, the lease reading, the Listing
fragment's shape and its remaining-lease value.

### The required surface, and the four actions it was missing

A third reading of table 2-10, this time of its device column: the service
defines twenty-one actions, fourteen REQUIRED of a device and seven
OPTIONAL. The transcription had taken all twenty-one as required, and the
facade then dispatched eleven of them, so the published SCPD promised ten
actions the dispatcher would answer with 401 (component 4d0160f).

Now: the four required actions that had no arm are implemented with the
section that decides each (SetConnectionType 731 ReadOnly per 2.5.1's
read-only note; RequestConnection success with a tuple and 704
ConnectionSetupFailed without it, per 2.5.3.4 through 2.5.3.6;
GetNATRSIPStatus per 2.3.11 and 2.3.12; ForceTermination refused, below),
and the seven OPTIONAL actions are neither advertised nor dispatched, so
the SCPD describes exactly what the device implements. New faults 731
ReadOnly and 704 ConnectionSetupFailed join the table.

ForceTermination is the one deliberate refusal in the required set, and
the reason is a security one: the facade does not own the WAN lifetime
(netifd and the ISP do), and the action is public on the v1 face, so
honouring it would give every device on the LAN a lever that drops the
household line for every client. Its own error table (2.5.5.6) has no code
for a device that may not terminate, so the answer is the UDA generic 501.

### The WPS introduction protocol is not implemented

DeviceProtection's setup ceremony has one limb that cannot be built from
what this project can transcribe. Section 2.4.3.1 mandates the WPS entry in
the advertised protocol list, and Appendix A defines the message exchange
behind it by deferring to the Wi-Fi Alliance WPS specification, which is not
available here and will not be internalized, while also requiring the
exchange to run inside a certificate-authenticated TLS channel this
plain-HTTP facade does not carry.

The behaviour is decided rather than left open: WPS is advertised as
mandated, and `SendSetupMessage` with `ProtocolType` WPS answers 704
Processing Error with an empty `OutMessage`, which is the action's own code
for a failure to process `InMessage` (2.6.1.9). The full reasoning, the
rejected alternative (600, which would contradict the published list), and
the two things a reversal needs are recorded in
[call/0021](https://github.com/slartibardfast/agentic-ds-lite-punch/blob/main/call/0021-wps-introduction-not-implemented.md).

One item remains open on the v2 path: the access control policy the device
applies is stated in the transcription rather than inferred, with the
mapping mutators requiring an authenticated `Basic` session while the reads,
an unauthenticated `GetListOfPortMappings` among them, are public. Section
2.5.21.3 recommends restricting that listing to the control point's own
entries and to ports at or above 1024, so this is a deliberate policy choice
with a named consequence, to be settled here rather than in the
transcription.

## The second reference: Orange igd2-for-linux

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
the LOCATION design's "the v1 and v2 descriptions MUST have distinct service
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
without any DeviceProtection surface (and without Layer3Forwarding). That
confirms how little of the IGD2 hierarchy the deployed ecosystem
actually implements.

### 27.4.4 The field picture, updated

```text
miniupnpd   IGD2 optional, off by default; DP = 3 actions
            (SendSetupMessage, GetSupportedProtocols,
            GetAssignedRoles), no working login/ACL ceremonies

Orange igd2 IGD2 with WIP2 + WANIPv6FirewallControl; dual root descs;
            shared superset SCPD; DP absent entirely

this milestone
            complete DP:1 (13 actions, enforced), dual facades with
            distinct per-version service URLs
```

No deployed open implementation provides even a working subset of the
DP login, setup and ACL ceremonies. "Complete" per this milestone is
therefore a superset of every reference found; there is no reference
that can be matched while remaining non-stub, which is precisely the
reason the specification text, not any implementation, is the
completion authority.

## The DeviceProtection-causation re-read (2026-09-16)

The milestone's earlier framing carried an implied causal claim: that
exposing DeviceProtection to legacy clients was a driver of the
observed Xbox One IGD2-mode failure. That claim is weakened by the
field research and is no longer load-bearing:

1. Orange ships a production IGD2 presentation with no DeviceProtection
   surface at all (27.4.3), so DP cannot be a universal IGD2 interop
   breaker.
2. miniupnpd's own DeviceProtection is a three-action scaffold
   (the miniupnpd reference); the IGD2 presentation the Xbox actually encountered was not
   a rich, functional security surface.
3. The Xbox trace establishes correlation only: in IGD2 mode the
   client fetched `DP.xml` and then abandoned. The IGD2-versus-IGD1
   delta is a bundle of differences (device hierarchy, WIP2 SCPD
   action set, additional services, missing services such as
   Layer3Forwarding and WANIPv6FirewallControl differences, UDA
   version). Capture order establishes no causation: the step recorded
   last before a failure may be a bystander.

The defensible causal statement is therefore the one in the Xbox One
legacy-client facts: Xbox is a demonstrably sensitive IGD1 control point
whose interoperability differs materially with the IGD2 description
presented. The driver of the IGD2-mode failure is unproven.

Plan consequences:

- DeviceProtection remains in the v2 facade because R5 requires a
  complete IGD2, not because it protects the Xbox path.
- The v1-for-ssdp:all policy rests on the direct trace evidence
  (Xbox consumes IGD1 + WIP1 successfully), not on the DP hypothesis.
- The test phase gains an empirical obligation: bench legacy clients
  (the Xbox chain) against the v2 facade and capture where the
  sequence abandons, to isolate the actual IGD2-mode failure driver
  instead of assuming it.

---

# 28. Research annex: the Livebox Play IGD reverse-engineered (2026-09-16)

Reverse-engineering of the UPnP/IGD implementation in the Livebox Play
Sagemcom firmware source archive
(`lb_play_sagemcom-sg30_sip-fr-5.7.16-all-packages.tar.bz2`,
61,016 files, all under `opensrc/sah/`). The durable full report is
kept outside the repo; this annex records the plan-relevant facts.

## Provenance, from source

The IGD daemon is
`opensrc/sah/services/linux-igd/REL/2014-06-19_V3.9.1/linuxigd2` and
its own headers carry:

```c
/* This file is part of Nokia InternetGatewayDevice v2 reference
   implementation */
```

That is the lineage both narratives trace to: the Nokia/linux-igd v2
code that Orange's `igd2-for-linux` also derived from, packaged here
by SoftAtHome as service `linux-igd V3.9.1` inside their SOP
component framework with SoftAtHome glue (`fw_wrapper.c`,
`nemo_wrapper.c`, `ipc_wrapper.c`, `pcb_eventloop.c`). The
SSDP/HTTP/SOAP engine is libupnp 1.6.18, visibly forked: a six-argument
`UpnpRegisterRootDevice4(..., LowerDescUrl)` (`upnp.h:1353`,
`upnpapi.c:1139`), version-aware M-SEARCH routing in `ssdp_server.c`,
and `#define X_USER_AGENT "redsonic"` (`ssdplib.h:93`, "needed for
the DSM-320"). Miniupnpd appears only as the test client
(`test/miniupnpc-1.5.20110618/`), never as the IGD.

## The two-description mechanism

`gatedesc.xml` / `gatedesc1.xml` are build-time-processed templates
(`m4 -D__PRESENTATION_URL__`, `sed __ICON_LIST__`; Makefile) named by
the config pair `description_document_name` / `lower_description_document`
(`upnpd.conf`, default defines in `globals.h`). The daemon registers
one root device with both URLs (`main.c:92-113` wrapper,
`UpnpRegisterRootDevice4(desc, ..., LowerDescUrl)`), and the forked
libupnp selects at M-SEARCH time:

```text
requested < registered   -> ST=requested(lower) + LOCATION=LowerDescURL
                           (gatedesc1.xml, the v1 presentation)
requested == registered  -> ST=:2 + LOCATION=DescURL (gatedesc.xml)
```

The product's own config states the intent: the lower document
"advertise[s] an UPnP IGD v1 device embedding all the UPnP IGD v2
functions for legacy Control Points which are not able to interact
with UPnP IGD v2 device (those legacy CPs are not compliant with the
UDA)". The two descriptions differ in device versions only
(InternetGatewayDevice/WANDevice/WANConnectionDevice :1 vs :2); the
connection service is a single shared superset SCPD
(`GetNATRSIPStatus` plus `AddAnyPortMapping`), with an IP/PPP build
split (`__SERVICE_TYPE__` substitution).

## The Livebox finding: production serves ssdp:all from the v2 description

In the forked libupnp the ssdp:all branch replies with the PRIMARY
(DescURL) description (`ssdp_server.c`, SSDP_ALL case); the lower
document is served only on explicit lower-version STs. The Livebox
therefore resolves generic discovery to the v2 facade, not the v1
compatibility facade.

Decision recorded for this milestone, since superseded by 9.3/12
(call/0020): the original position kept ssdp:all permanently at v1 and
deferred the comparison to bench time. The burst rule replaces it: the
Livebox's production behavior of serving v2 to generic discovery is
now the expected outcome for any control point that demonstrates an
IGD:2 search inside the window, and v1 remains the drop-dead default
otherwise. The bench phase records how Xbox-family and modern clients
behave against the concrete DISCOVERY_DEBOUNCE = 1 s policy.

## The production-absence finding: no DeviceProtection in the carrier image

The Livebox config set carries no DeviceProtection SCPD, and the
daemon's authorization is an internal access-level ACL
(`accessLevelXml`, `ACL_XML /etc/upnpd_ACL.xml`) with the literal
source comment `//TODO: must be replaced by DeviceProtection`
(`globals.h:113`). A second production IGD2 implementation therefore
ships without DP and with its own placeholder for it, reinforcing
section 27's field picture and the completion bar: no deployed
reference implements the full DP surface, and this milestone remains a
superset of every one.