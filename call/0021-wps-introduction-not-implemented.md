# The WPS introduction protocol is not implemented

- Status: accepted
- Scope: plan/0008 (the adaptive UPnP IGD v1/v2 compatibility facade), the
  DeviceProtection:1 setup ceremony on the ds-lite-punch facade
- Date: 2026-09-16

## Context and Problem Statement

DeviceProtection:1 mandates the WPS introduction protocol in the advertised
protocol list. Section 2.4.3.1 requires an `<Introduction><Name>WPS</Name>`
entry to "always be included" in `SupportedProtocols`, and 2.6.1.2 requires
the `ProtocolType` of `SendSetupMessage` to match one of the advertised names.
Appendix A then says what a device does with those messages: the WPS
Registration Protocol, a Diffie-Hellman exchange whose peers authenticate by
successive disclosure of knowledge of a shared secret, transported as WPS
type-length-value messages. The message M1 is retrieved by passing an empty
`InMessage`.

Two facts close that path for this device.

- **The message encoding is not available here.** Appendix A defers to the
  Wi-Fi Alliance specification for it: "The format and specific binary values
  transported in these argument is determined by the ProtocolType", with the
  Message Encoding and Data Element Definitions sections named as the
  authority. That specification is not available to this project and will not
  be internalized. An M1 or an M2D assembled without it would be invented
  bytes presented as a protocol, which is the defect this project's
  transcription discipline exists to prevent.
- **The mandatory channel does not exist.** The appendix requires the
  `SendSetupMessage` exchange to run "inside a TLS connection authenticated by
  the certificates" whose hashes are the UUID-E and UUID-R values, so the
  exchange is cryptographically bound against relay and man-in-the-middle
  attacks. This facade serves DeviceProtection over plain HTTP and treats the
  control-point address as the session key (plan/0008's security context). There is
  no certificate-authenticated transport to run it inside.

The device is also wired. It runs no WPS registrar and has no wireless
interface to enrol, no display to show a PIN, and no push button. The
appendix's own framing supports the omission being harmless here: configuring
WLAN settings "is NOT the primary purpose or intent of DeviceProtection's use
of WPS".

## Decision

Advertise WPS, as the specification mandates, and answer a WPS setup attempt
with 704 Processing Error.

- `SupportedProtocols` carries the mandated `<Introduction><Name>WPS</Name>`
  and `<Login><Name>PKCS5</Name>` entries. The list is compliant, and PKCS5,
  the login protocol, is fully implemented beside it.
- `SendSetupMessage` recognizes `ProtocolType` "WPS", because it is a name in
  the device's own advertised list, and answers 704, the code the action's
  table gives for a failure in processing `InMessage` (2.6.1.9).
  `OutMessage` stays empty: the appendix's detailed error information is
  itself carried in WPS messages, and inventing those is the same defect one
  level down.
- **600 was rejected as the answer.** Its meaning is "the `ProtocolType` value
  is not supported by the Device" (2.6.1.9), which would contradict the
  description the device just published. The device advertises the protocol
  and cannot process it, so the failure belongs in processing.
- The WPS Registration Protocol is out of scope for this work, recorded here
  rather than shipped as a scaffold that answers names.

## Consequences

- A control point that offers only WPS for introduction cannot enrol through
  DeviceProtection. It can still authenticate with PKCS5, which is what the
  ACL and role ceremony requires, so the authorization boundary stays usable.
- The 704 is a device-capability limit and reads as a permanent one, since no
  retry changes it.
- The omission is named where it is visible: plan/0008 section 27.3e and the
  component transcription `docs/upnp-dp1/TRANSCRIPTION.md` cite this decision,
  so a reader of the DP contract finds the reason at the point of the
  behaviour.
- Reversing this decision needs two things together: the Wi-Fi Alliance WPS
  specification internalized as a component source, on the pattern of
  `docs/upnp-dp1/` and `docs/upnp-wip2/`, and a certificate-authenticated
  transport for the exchange, which is a security-posture decision of its own
  rather than a detail of this one.