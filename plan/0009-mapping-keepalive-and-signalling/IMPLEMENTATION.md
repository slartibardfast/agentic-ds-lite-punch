# Implementation plan: the mapping hold, its admission, and the signalling

Companion to this milestone's README. The README says what the milestone
is and how it is verified; this document says, for each task, which files
and which rules it touches, the exact commands, what a pass looks like,
and what would falsify it. Everything here was measured or read on the box
and in the crate on 2026-09-17 unless it carries an older citation.

## Facts this plan builds on

1. The AFTR's UDP idle timeout is five to ten seconds on this node, and its
   TCP one was measured at between 120 and 300 seconds. The AFTR maps per
   inner tuple (EIM), ignores the source port, forwards from any peer, and
   is written by any datagram from the tuple and read only by STUN's
   XOR-MAPPED-ADDRESS.
2. The router's own conntrack is not the aggressive party: UDP times out at
   60 s one-way and 180 s on a stream, TCP established at 7440 s, and the
   table holds 194 of 262144 entries.
3. The nft on the box is 1.1.1 and accepts this shape, validated inertly
   and removed afterwards:

```nft
table inet dslp_hold {
	ct timeout udp_long {
		protocol udp
		policy = { unreplied : 5m, replied : 5m }
	}
	ct timeout tcp_long {
		protocol tcp
		policy = { established : 2h4m }
	}
	chain preraw {
		type filter hook prerouting priority raw - 10; policy accept;
		ip saddr { 192.168.21.68, 192.168.21.138 } meta l4proto udp ct timeout set "udp_long"
		ip saddr { 192.168.21.68, 192.168.21.138 } meta l4proto tcp ct timeout set "tcp_long"
	}
}
```

   The keyword is `protocol`, not `l4proto`, which this build rejects
   outright; `ether saddr` is bridge-family and unavailable here, so the
   allowlist is by address; `unacknowledged` is rejected as a TCP state;
   and the policy applies to a flow on its next packet rather than
   retroactively.
4. The change-data-capture decision already exists in `src/cdc.rs`: an nft
   `flow_obs` dynamic-set mirror as the primary backend (a
   filter-postrouting observer at priority 110, above fw4's srcnat at 100,
   whose elements are the post-NAT tuples), `/proc/net/nf_conntrack`
   polling as the fallback, and an Aya TC hook as the performance tier,
   unwired. Netlink connection events were tried on this build and are
   silent. The contract is a live bidirectional candidate at a two-second
   cadence.
5. The vote and rotation policy already exist and are unit-tested:
   `VoteState::observe` answers Stable, Disagree or Churn, with two agreeing
   observations moving the confirmed tuple; `MappingPolicy` rotates on a
   silence threshold and on suspicion, and a lone server never
   suspect-rotates.
6. The signalling path exists and is narrow: `gena_subscribe` validates a
   LAN callback and clamps the timeout, `Sub` records the callback address,
   and `notify_one` builds a propertyset containing **only**
   `ExternalIPAddress` from its `(sid, ip, seq)` arguments. The service
   description declares `ConnectionStatus`, `ExternalIPAddress`,
   `PortMappingNumberOfEntries` and `SystemUpdateID` evented, so the
   surface is declared and unused.
7. The facade's semantics constrain what may be signalled: the reported
   external port is the requested label, so a re-key of the datapath tuple
   is not a port change; reads are contained per caller, so events must be
   contained per subscriber; and a mapping that is gone answers 714 inside
   the caller's namespace, with 730 for an empty range.
8. The external vantage for anything on the Internet side is the recorded
   host, `ubuntu@170.9.238.141`, and raw captures from the 2026-09-17
   session live at `/mnt/nvme/captures` on the router with a checksum
   manifest and a mirror on the workstation.

## The tasks

### Seed the allowlist admission {#allowlist}

1. Choose where the rules live. Two options, and the first is preferred:
   an include under `/etc/nftables.d/` that fw4 loads, so a firewall reload
   carries it; or the daemon's own table, installed at startup beside its
   slot rules, which keeps the policy in one owner but ties it to the
   daemon's lifetime.
2. Write the two policy objects and the selection rules (the shape in
   Fact 3), with the allowlist as an nft set rather than an inline list so
   adding a device is one element and not a rule rewrite.
3. Validate before applying: `nft -c -f <file>` accepts it. Then apply and
   confirm: `nft list table inet dslp_hold`.
4. Prove the behaviour, which is the part the parse does not show. Take a
   quiet UDP flow from an allowlisted device and the same from an
   unallowlisted one, both with no traffic, and watch them:
   `conntrack -L -p udp | grep <addr>` and `nft list ruleset` for the
   policy in force. Pass: the allowlisted entry survives past the
   unallowlisted one's default and reports a remaining timeout at or above
   the floor.
5. Record where the rules live and the element format in this milestone's
   `results/`, so a later session extends the list without re-deriving it.

Falsified if: an unallowlisted device's flow also gets the long timeout
(the selection is too broad); or an allowlisted flow is still reaped at
the default (the policy is not being applied where the entry is created).

### Snoop the AFTR with our own writes {#snoop}

1. Wire the capture side: the mirror backend in `cdc.rs` enumerates the
   candidate tuples and the allowlist filters them. Each candidate already
   carries the shadow-bind tuple and the br-lan origin (`host`,
   `host_port`), which is what a write needs.
2. Wire the read: a STUN Binding Request from the flow's own post-NAT
   tuple, so the answer is that tuple's XOR-MAPPED-ADDRESS. This is the
   same primitive the slot engine uses, applied per device instead of per
   slot.
3. Wire the write: a datagram from the same tuple, at the cadence the
   measurement in `#udp-threshold` settles. Until then, two seconds, which
   is what holds a slot today. The write needs the transparent-source
   primitive the crate already uses for the TCP fold, not a new socket
   per flow.
4. Report per observation: the learned tuple, the last-seen stamp, and the
   vote decision (`Stable`, `Disagree`, `Churn`). The churn path must feed
   `#signal`, so the log and the client's view cannot disagree.
5. Keep the arm off every non-allowlisted flow, and assert that in the log:
   a device not on the list produces no writes. Pass: a named device has a
   learned tuple within two cadence periods of its first flow, and no write
   appears for any other device.

Falsified if: writes appear for a device that is not on the allowlist; or a
learned tuple is reported for a flow whose owner cannot be identified
(the capture and the proc table disagreeing on identity is the known
failure mode, and `cdc.rs` already reads both for that reason).

### Signal per subscriber {#signal}

1. Extend the subscription record with the **caller's** address, captured
   at SUBSCRIBE, since containment keys on the caller and the record today
   holds only the callback. Reject nothing new; this is an added field.
2. Generalise the body builder: emit a propertyset for the declared
   evented variables that moved, with the existing eventKey and SEQ
   discipline and a zero eventKey for a subscription's initial event.
3. Compute each notification with the subscriber's view, using the same
   containment function the reads use, so `PortMappingNumberOfEntries` and
   the mapping-derived parts of the body are scoped to what that subscriber
   may see.
4. Drive it from the churn and tuple path that already feeds the log and
   the reported external address: one source, so a NOTIFY cannot contradict
   a query.
5. Bump `SystemUpdateID` on mapping add, remove and re-key, and leave the
   reported port alone on a re-key, because the reported port is the
   requested label.
6. Test with a real control point: subscribe with `upnpc`, then add,
   delete and churn a mapping, and read each NOTIFY. Pass: the variables
   that changed appear, a contained subscriber's body carries only its own
   namespace, and no event invents a port change.

Falsified if: a contained subscriber's event carries another client's
count; or a NOTIFY arrives that a following query contradicts.

### Bind PCP and NAT-PMP on their shared port {#pcp}

1. Bind `192.168.21.1:5351/udp`, LAN-only, carrying both protocols on the
   one port as the implementation notes in plan/0004 already specify, with
   the quota (16) and the result codes (0 to 8, plus
   `CANNOT_PROVIDE_EXTERNAL_PORT` as 9) as recorded there.
2. Admit requests through the same slot engine as the other three paths,
   with the same per-client key, so a mapping created here is
   indistinguishable from one created by UPnP except in the dialect.
3. Answer the assigned-port question the way this line forces: the response
   carries the label, and the learned tuple follows in an **ANNOUNCE** once
   discovery completes. A zero lifetime in an ANNOUNCE is the drop signal.
4. Refuse `PREFER_FAILURE` on the AFTR uplink, since the AFTR owns the
   external port there, and honour it where the uplink is one we own. This
   is call/0022 expressed in this protocol.
5. Honour `FILTER` as the filtering knob and gate `THIRD_PARTY` on the
   lift the containment already defines, so a control point may map for
   another host only when it is authorized to.
6. Test with a client tool: create, renew and delete a mapping, and read
   the response's lifetime and code; then read the ANNOUNCE. Pass: the
   lifetime and code match the policy, the NAT-PMP subset answers on the
   same socket, and the ANNOUNCE carries the tuple the STUN read learned.

Falsified if: the granted lifetime exceeds what the hold can maintain; or
the ANNOUNCE disagrees with a subsequent query.

### Answer the TCP question {#tcp-answer}

1. Reconcile the two numbers on the record: the AFTR reaps an idle TCP
   mapping between 120 and 300 seconds, and a client's keepalive is
   typically far slower than that.
2. Write the decision with the options costed: hold what the relay
   terminates (bounded by termination), signal the client that its session
   is at risk (cheap, needs a client that listens), or an opt-in surrogate
   on `tcpslot.rs` and `forward.rs`.
3. If the surrogate is chosen, scope it as its own milestone, because it
   terminates connections and that is a different class of change from
   every other task here.

Falsified if: the decision claims a hold the mechanism cannot deliver, for
instance promising to keep a client's own connection alive without owning
its sequence space.

### Run the acceptance under silence {#acceptance}

1. Pick a client flow on the allowlist, confirm its learned tuple, then
   silence the client (stop its traffic without killing the flow).
2. Have the external vantage send to the learned tuple at 30, 60 and 120
   seconds of silence, and record each outcome with the interval.
3. Watch the client-side signal in the same run: exactly one notification
   per change, and none for a change the client cannot see.
4. Measure the cost: packets per second spent holding the allowlist as it
   stands, at the cadence in force.
5. Record all of it in `results/`, with the capture manifest.

Falsified if: a probe lands at 30 seconds and not at 60 (the hold is not
continuous), or a signal arrives that no change justifies.

### Measure the AFTR's UDP threshold under silence {#udp-threshold}

1. Take one held flow and one unheld flow from an allowlisted device.
2. Silence the client, and probe from the vantage at 60, 120 and 300
   seconds.
3. Record the death point for each, and reconcile it with the recorded
   five to ten seconds; the earlier milestone's longer-limit campaign is
   the same experiment, so its windows (60 and 120) are reused here.
4. Set the cadence from the measured death point with margin, and record
   the margin's reason, since the cost is linear in the cadence.

Falsified if: the held flow dies inside the RFC floor anyway, which would
mean the AFTR reaps on something other than idleness and the whole hold
needs rethinking.

## Rollout and revert

Apply in the four stages the README describes, and keep the revert
commands beside each stage:

- **Ruleset revert:** delete the policy table and the rules that select it,
  which returns every flow to the default timeouts. Confirm with
  `nft list ruleset` and a fresh `conntrack -L` entry showing 60 s.
- **Daemon revert:** the previously deployed build is parked at
  `/root/ds-lite-punch.prev` by the deploy procedure, and the service
  restart is the switch.
- **Snooping revert:** the log-only stage writes nothing, so its revert is
  stopping the arm; that stage exists so the learned tuples can be read
  against the AFTR's behaviour before anything is held.

## What this plan does not do

- It does not touch the v2 authorization boundary, and the allowlist
  grants no role. No DeviceProtection action exposes it, and it cannot
  substitute for the introduction protocol call/0021 defers.
- It does not hold a flow for a device that is not on the list, and it
  does not hold a client's TCP connection without a decision saying how.
- It does not promise an assigned external port on the AFTR uplink, since
  the AFTR owns that port; the ANNOUNCE is where the learned truth goes.