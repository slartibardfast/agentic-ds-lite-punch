# Milestone: the mapping hold, its admission, and the signalling to clients

**Status:** open, started 2026-09-17. This milestone keeps a named
device's mappings alive for the lifetimes the RFCs promise and the AFTR
refuses, and gives the daemon a voice so a client learns the truth about
its own mapping. The policy spine is call/0025; the measurements that
size the work are the AFTR's UDP idle timeout (five to ten seconds on this
node) and its TCP one (between 120 and 300 seconds), both already on the
record.

## What this milestone is

A device behind this line can be the wrong shape for it. One console on
this LAN maintains its own UDP mapping perfectly well, running its own
STUN every two seconds from the same port it games on, and needs nothing
from us. Another device may keep no mapping at all, or keep one on a
cadence the AFTR ignores, and when its mapping dies the client is never
told. The daemon's stated contract is to be the lifetime shim the AFTR
will not be: on the LAN side it implements the behaviour the AFTR refuses
(RFC 6888 lifetimes, reportable tuples, divergence notification), while
on the WAN side it changes nothing and owns one property, that the
mappings do not die.

This milestone is the admission that names which devices get that
treatment, the arm that performs it, and the signalling that tells a
client when its mapping changed or died. It is scoped to the daemon and
its operator configuration. It does not revisit the facade's authorization
boundary (call/0024), it does not implement the introduction protocol
call/0021 defers, and it does not change what the AFTR does.

The personas it serves are the ones this host already carries: the
operator, who needs the list to be a budget rather than a convenience,
and the agent, who needs the mechanism to be verifiable from the outside
rather than asserted from inside.

## Build sequence

Bands group the work: the admission, the arm that acts on it, the voice it
gives the daemon, the fourth admission surface, the TCP question, and the
acceptance that closes it. Every task carries verify and inputs;
mechanical verifies re-run at the gate.

### Seed the allowlist admission {#allowlist}

- verify: `nft -c` accepts the ruleset; a named device's quiet UDP flow
  still has a conntrack entry after 60 s of silence with a remaining
  timeout at or above the floor, while an unnamed device's entry is gone;
  the rules are carried by a file the boot reads
- inputs: the accepted ruleset shape (the `ct timeout` objects with
  `protocol udp` and the states this build accepts, and the per-device
  rules that select them), the DHCP-pinned addresses, the watching
  commands (`conntrack -L`, `nft list ruleset`)

Install the policy objects and the rules that select them for a first
allowlist, which starts with the two consoles because their addresses are
already pinned, and prove the behaviour rather than the parse: a quiet
allowlisted flow outlives the default single-direction timeout while an
unallowlisted one does not. Record where the rules live so a firewall
reload or a carrier upgrade carries them.

### Snoop the AFTR with our own writes {#snoop}

- verify: the observation log carries a learned external tuple for a named
  device within two cadence periods of its first flow, with the
  last-seen stamp and the vote decision for each observation; no write
  occurs for a flow whose device is not on the allowlist
- inputs: the change-data-capture backends in `cdc.rs` (the nft
  `flow_obs` mirror is primary and records post-NAT tuples), `vote.rs` and
  `mapping.rs` with their existing tests, the accept syntax from
  `#allowlist`

The arm reads the AFTR the way the design already says to read it, with a
STUN Binding Request from the flow's own post-NAT tuple, and writes it
the way the design already says to write it, with a datagram from that
same tuple. The capture backend already exists and its contract is a live
bidirectional candidate at a two-second cadence, so this task is the
per-device wiring and its reporting, not a new reader. Netlink connection
events were tried on this build and are silent, which is why the nft
mirror leads.

### Signal per subscriber {#signal}

- verify: a real control point subscribes, then a mapping is added, deleted
  and churned, and each NOTIFY carries the declared evented variables that
  changed; a contained subscriber's event carries counts for its own
  namespace alone
- inputs: `#snoop` for the change events, the subscription and notify path
  in `upnpsvc.rs`, the containment view the reads already build, the
  evented set the service description declares

The daemon already knows when a mapping appears, changes and dies, and it
already says so in its own log. This task gives that truth a second
voice: a propertyset carrying `ExternalIPAddress`, `ConnectionStatus`,
`PortMappingNumberOfEntries` and `SystemUpdateID` as they change, computed
with the same containment view the reads use so an event cannot leak
another client's namespace, and scoped to the subscription that asked. A
re-key of the datapath tuple raises no port change, because the reported
port is the requested label call/0022 fixed.

### Bind PCP and NAT-PMP on their shared port {#pcp}

- verify: a PCP client creates, renews and deletes a mapping against the
  bound port, the response carries the granted lifetime and the result
  code the policy implies, a NAT-PMP request answers on the same socket,
  and an ANNOUNCE carries the learned tuple once discovery completes
- inputs: the listener, quota and result-code notes in plan/0004's
  implementation document, the slot engine, the specification's message
  shapes

The fourth admission path, already named in the design's own mental model,
becomes real here: a LAN-only listener carrying both protocols on the one
port, the quota and the result codes as specified, and the one divergence
this line forces stated in the answer itself. On the AFTR uplink the
external port belongs to the AFTR, so the response carries the label and
the learned tuple follows in an ANNOUNCE, which is the mechanism the
protocol provides for exactly this.

### Answer the TCP question {#tcp-answer}

- verify: a decision record states the choice, its cost and its
  preconditions; if a surrogate is chosen, that work is scoped into its own
  milestone rather than left implied
- inputs: the measured AFTR TCP lifetime (between 120 and 300 seconds, on
  the C3 record), the TCP machinery the relay already owns
  (`tcpslot.rs`, `forward.rs`), the signalling path from `#signal`

A connection that is nominally established is reaped inside a VPN's idea
of a keepalive, so this is a real question and not a hypothetical one. A
router cannot write into a client's connection without owning its
sequence space, so the honest options are to hold what the relay
terminates, to let the client know its session is at risk, or to run an
opt-in surrogate on the machinery the datapath already has. The decision
record names which, and what it costs.

### Reconcile the punch and the allocation {#collisions}

- depends: #allowlist, #pcp

- verify: a fresh grant on a port a live tuple holds takes another port and
  logs the one it steered around; a renewal keeps the port it has; the arm
  refuses a tuple an allocation holds; the rules are stated as requirements
  in call/0027 and each one names its experiment
- inputs: the change-data-capture mirror the arm already reads, the lease
  table, call/0027's rules, the live-tuple set on the box

A port becomes the daemon's in two ways, and only one of them was specified.
An allocation has a lease and a row; a punch has nothing but its packet, and
the AFTR honours it anyway. The rules that keep the two apart are call/0027's,
and they are written as requirements because that is what they are: the
incumbent keeps the tuple, an allocation probes before it claims, a late
collision moves the allocation and never the punch, and every collision is
reported rather than resolved in silence. Two things the decision leaves open
are experiments rather than opinions, and both are named there with the
measurement that would settle them.

### Run the acceptance under silence {#acceptance}

- verify: the external vantage reaches a held mapping at 30, 60 and 120
  seconds of client silence, with the intervals printed; the client-side
  signal arrives exactly once per change; the keepalive cost is measured
  in packets per second for the allowlist as it stands
- inputs: the rig and the external vantage the datapath work already uses,
  the captures on the router's storage, `#udp-threshold`'s death point,
  `#signal` and `#pcp`

The acceptance is a silence test with an outside witness, because inside
the box every layer can look healthy while the mapping is gone. It also
records the cost, since the allowlist's size is a budget and this is where
the budget is measured.

### Measure the AFTR's UDP threshold under silence {#udp-threshold}

- depends: #allowlist, #snoop

- verify: a results record states the death point for a held flow and for
  an unheld one across silent windows of 60, 120 and 300 seconds, with the
  vantage's probe outcomes
- inputs: the external vantage, the rig, the observation log from `#snoop`

The recorded figure of five to ten seconds was measured before the hold
existed, and the longer-limit campaign the previous milestone carried is
the same experiment as this one. Running it here settles the interval the
arm should use and settles whether the RFC floor can be honoured on this
line at all.

## Verification

The milestone's mechanical checks are the repository's own sweep
(`validate`, `prose`, `refs --check`, `tasks --check`, `book --check`,
`software --check`) at every gate, plus the two checks this work adds: an
allowlisted flow outliving an unallowlisted one under silence, and a
subscriber's event carrying its own namespace alone. The on-box changes
are the ruleset policy and the deployed daemon, so the rollout says how
each is carried and how each is reverted.

## Rollout

The policy lands in stages, and each stage is observable before the next.

1. **Log only.** The snooping arm runs with no writes, so the learned
   tuples and the vote decisions can be read against the AFTR's real
   behaviour before anything is held on a device's behalf.
2. **The policy objects and two devices.** The ruleset carries the timeout
   policy for the consoles that are already pinned, and the holds are
   turned on for them alone. The load is measured here, since two flows at
   the working cadence are cheap and the number is what sizes any further
   device.
3. **A device that needs it.** The first genuinely broken device is
   admitted only after the silence test shows it cannot hold its own
   mapping, which the snooping arm is how we learn.
4. **The pcp listener last.** It answers on a port nothing on the LAN uses
   today, so it carries no risk to what works, and it lands after the
   signalling is proven so its ANNOUNCE is not the first thing testing the
   truth path.

The revert path for the ruleset is deleting the policy table and the rules
that select it, which returns every flow to the default timeouts; the
daemon's revert is the previously deployed build, parked beside the
binary as the deploy procedure already does.

## Open questions

- The AFTR's true UDP threshold, which the silence test measures; until it
  is known, the two-second cadence is what works rather than what is
  required.
- Whether any device on this LAN actually needs the hold. The one console
  measured so far does not, so the allowlist may stay at the
  bootstrap pair for a long time.
- Whether the assigned-port divergence matters to a real PCP client, or
  whether the ANNOUNCE is enough in practice.
- Whether the WPS introduction limb is ever built, since the identities it
  would create should then feed the allowlist rather than sit beside it.
- The LAN's trust basis for an allowlist, which is the same assumption the
  DHCP pins already rest on.

## Results home

Records land under `results/` in this room. Raw captures from the
acceptance stay on the router under the captures path the earlier runs
established, with a checksum manifest alongside and a mirrored copy on the
workstation, as the switch NAT-type record documents.