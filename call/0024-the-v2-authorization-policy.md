# The v2 authorization policy: mutators gated, reads public, the caller contained

- Status: accepted
- Scope: the UPnP IGD facade's authorization boundary on both faces
  (plan/0008's v2 path)
- Date: 2026-09-17

## Context and Problem Statement

Version 2 introduces access control and leaves the policy to the device:
the specification recommends a policy instead of mandating one, as the
transcription's access-control note records. The boundary is implemented
and tested at the wire, and the milestone's annex asks for the policy to be
settled as a decision rather than left standing in the transcription,
because three of its choices belong to this project and each carries a
consequence a reader will later ask about:

1. Which actions require a session at all.
2. Which role the mapping mutators require.
3. What a control point that never authenticates may see and do.

## Decision

- The boundary rides the v2 face only. Four actions on that face are gated
  in front of the canonical mapping engine: AddPortMapping,
  AddAnyPortMapping, DeletePortMapping and DeletePortMappingRange. Each
  one requires a live session whose roles include Basic, which Admin also
  satisfies. The v1 face stays the unauthenticated legacy compatibility
  surface of the specification's isolation rule, and its AddPortMapping
  keeps working: DeviceProtection is advertised on the v2 presentation
  alone, so a v1 control point can hold no session, and gating the v1 face
  would break the console-era path this milestone exists to serve while
  protecting nothing the v1 description offers.
- Every other action is public on both faces. That includes the mapping
  reads (GetExternalIPAddress, GetGenericPortMappingEntry,
  GetSpecificPortMappingEntry and GetListOfPortMappings) and the
  DeviceProtection reads that are not administrative.
- The administrative DeviceProtection actions require Admin: GetACLData,
  AddIdentityList, RemoveIdentity, SetUserLoginPassword,
  AddRolesForIdentity and RemoveRolesForIdentity.
- A control point without the lift is contained. The lift is a live
  session whose roles include Basic, decided by the same policy function
  the boundary itself calls, so the containment cannot drift from the
  gate. A contained caller acts on its own host alone: it may add,
  enumerate, read and delete mappings whose internal client is itself, and
  on the v2 face only at ports at or above 1024. That is section 2.5.21.3's
  recommendation taken as policy. The lift belongs to the principal's
  roles, so a control point that authenticates reaches the whole table
  from either face.
- The refusals are codes a control point can act on. A gated mutator
  without a session answers 606 Action not authorized, and so does a
  contained caller that names another host or a port below the floor. A
  contained caller's specific read or delete resolves inside its own
  namespace, so a port it does not own answers 714 NoSuchEntry, which is
  the terminator its enumeration loop already handles; its own entry below
  the floor answers 606.

## Consequences

- The v2 face is genuinely security-complete. A control point cannot open
  a door for another host, and cannot open one at all without a session.
- The legacy path survives for the stacks that never heard of
  DeviceProtection, which is the compatibility this milestone exists for.
- The listing stays public, so an unauthenticated caller can enumerate
  what it is allowed to see. This decision does not narrow the
  transcription's boundary any further than the containment, and a later
  narrowing returns as a new decision rather than as a drift in behaviour.
- The port floor binds the v2 face. On the v1 face the containment is by
  host alone, since a v1 caller cannot lift it and its purpose is the
  legacy mapping surface.
- Verified at the wire: the boundary and containment suites in the
  component, and the reference client refused with 606 in
  [RESULTS-2026-09-17-miniupnpc-interop.md](https://github.com/slartibardfast/agentic-ds-lite-punch/blob/main/plan/0008-adaptive-igd-v1v2-facade/RESULTS-2026-09-17-miniupnpc-interop.md).