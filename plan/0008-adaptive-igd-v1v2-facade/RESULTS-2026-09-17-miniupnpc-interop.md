# RESULTS-2026-09-17-miniupnpc-interop: the reference client reads the v2 listing, and what it found

Status: the probe ran and one defect it found is fixed at component
ad69a49. One divergence from the reference server is recorded and left
open.

## What ran

- The ignored probe `miniupnpc_interop` now runs. It builds the facade's
  HTTP layer on 127.0.0.1:19152 with no router, and drives it with
  miniupnpc 2.3.3 built locally at `/tmp/localupnpc` from
  `github.com/miniupnp/miniupnp` at b2b496a: `upnpc-static` for the
  client walks and `testigddescparse` for the description parser. The
  probe's doc comment now carries the fixture build commands, so the run
  is reproducible.
- The probe had been ignored since the facade review because the fixture
  was absent from the machine. Nothing about the facade blocked it.

## What the reference implementation accepted

- `testigddescparse` read both rootDesc presentations. The v1 one
  resolves `ipcondescURL`, `controlURL` and `controlURL_CIF`; the v2 one
  resolves `/igd/v2/WANIPCn.xml` on the same control URL, with
  DeviceProtection:1 and WANIPConnection:2 in place.
- `upnpc -l` accepted the device as a valid IGD on the v1 face:
  Connection Type IP_Routed, Status Connected, GetExternalIPAddress
  answered, and an empty table answered 714.
- `upnpc -L` read the v2 listing. The 3074/UDP mapping the probe seeds
  for the calling host came back parsed, with protocol, both ports, the
  internal client, the description `'interop'` and the lease.
- `upnpc -n`, which is AddAnyPortMapping on the v2 face, was refused with
  606 `Action not authorized` while the DeviceProtection store holds no
  session. The boundary holds against a real client, which the facade's
  own wire tests could not show on their own.

## The service descriptions, checked against a real parser

The four service descriptions were extracted from their constants and
parsed as XML with a conformant parser (Python's expat through
`xml.etree`): DeviceProtection, WANCommonInterfaceConfig,
WANIPConnection:2, and the WANIPConnection/WANPPPConnection description
the PPP constant aliases to. All four are well-formed. The crate carries
no XML parser, and its SCPD assertions are substring matches. This check
therefore stands at the record level. The listing fragment has its own
witness: the reference client parses it as XML in the `upnpc -L` walk
above.

The parser was controlled before its verdict was read: three deliberately
malformed documents (an unclosed element, crossed end tags, an unquoted
attribute) were each rejected, and a good one accepted.

The reference implementation's own generic validator is not usable for
this. `minixmlvalid` takes no file argument: it ignores `argc` and `argv`,
tests a fixture compiled into the binary, and reports the fixture's event
count whatever path it is given, so it accepted a malformed file and the
real descriptions alike. Its sibling `testigddescparse`, which does read a
path, is the parser used above for the two rootDesc presentations.

## The defect it found (fixed at ad69a49)

GetListOfPortMappings declares its OUT argument as `NewPortListing`,
whose type `A_ARG_TYPE_PortListing` is a string that holds an XML
fragment. The response emitted the PortMappingList as the response's own
children instead, so the fragment sat where no control point looks for it
under that name. The reference client collects the listing only from the
character data of an element named `NewPortListing`; finding no such
element and no error code, it reported `-1` and showed nothing. The
reference server (miniupnpd) wraps the same fragment in that element
inside a CDATA section, and the facade now emits that shape. The
fragment's contents were already correct: the namespaced PortMappingList
of PortMappingEntry elements of the specification's sample.

## The divergence recorded (open)

The facade answers 730 `PortMappingNotFound` when the listing range holds
nothing, and the transcription requires that answer in its
GetListOfPortMappings bullet and in its error table. The reference server
answers 200 with an empty PortMappingList instead, so the reference client
surfaces our 730 as a failed pass and prints no listing for that
protocol. A v2 client that lists both protocols therefore reads a fault
for whichever one holds nothing.

- The facade keeps the specification's answer. The transcription is this
  project's authority for WIP2, and this is not a behaviour to invent
  away on a reference implementation's say-so.
- The check owed when the PDF is at hand: whether section 2.5.21's own
  error table carries an empty-result rule at all, because the
  transcription's cites for it are 2.5.19's clause numbers, which are the
  range delete's. If 2.5.21 does not carry it, the rule belongs to
  DeletePortMappingRange alone and the listing should answer an empty
  list, which is both the reference behaviour and the friendlier client
  experience.

## Scope

The probe covers the v1 walk, the v2 listing, the v2 refusal, and the
description parser. It does not cover the authenticated v2 path, because
the reference client carries no DeviceProtection login: the probe asserts
the refusal, and the authenticated path stays covered by the facade's own
wire suite. The loopback caller is its own host, so the containment's
own-host clause is exercised and its cross-host clause is not.