# Results: the hold, its admission, and the signalling, as built

Date: 2026-09-17. Component `ds-lite-punch` at `acd1162` (the four code
tasks of this milestone, plus the tuple-file defect the on-box work found).
This record says what was built, what was verified and how, where the build
diverges from this milestone's own implementation notes, what the router
proved, and what still needs an operator.

## What was built

| Task | Where | What it does now |
|------|-------|------------------|
| `#allowlist` | `src/hold.rs`, `src/nft.rs`, `--allowlist`/`--hold` | parses the operator's list, generates the `ct timeout` policy, installs it in `table ip dslp`, and reads it back |
| `#snoop` | `src/engine.rs` | the arm acts only for named devices; without `--hold` it reports them and touches nothing; reports carry the flow's own vote decision and its last-seen stamp |
| `#signal` | `src/upnpsvc.rs` | a subscription records its caller, a NOTIFY carries exactly the variables that moved, the count is scoped by the containment the reads use, and `SystemUpdateID` moves on add and remove |
| `#pcp` | `src/pcp.rs`, `upnpsvc::pcp_serve`, `deploy/pcp-probe.py` | PCP and NAT-PMP on UDP 5351, both protocols on one socket, riding the same slot engine; `--pcp` enables it, `--pcp-peer` answers PEER |
| `#tcp-answer` | `call/0026` | the decision: a mapping the daemon terminates is held, a client's own connection is signalled and never held, the surrogate is scoped separately |

## The verification that ran

- `cargo test`: 168 passed, 0 failed, 1 ignored. The suite was 121 tests
  before this milestone. The tests were written before their
  implementations, and the ones that matter most run over real sockets:
  - `pcp::tests`: the codec field by field against the RFC's own layouts,
    with a test for every refusal the processing rules name.
  - `upnpsvc::ifindex_probe::the_shared_port_answers_announce_and_names_its_refusals`:
    a real UDP client against `pcp_serve`, covering ANNOUNCE, an unsupported
    version, the FILTER refusal, the PREFER_FAILURE refusal, the THIRD_PARTY
    refusal, an unsupported protocol, the delete form, and both NAT-PMP
    shapes on the same socket.
  - `upnpsvc::ifindex_probe::a_subscriber_is_told_about_its_own_mappings_only`:
    a real GENA subscription whose NOTIFY bodies are read, covering the
    initial event's four declared variables, a change carrying only
    `SystemUpdateID`, no delivery at all when nothing moved, and the address
    when the tuple moved.
  - `upnpsvc::ifindex_probe::a_revoked_mapping_takes_its_tuple_file_with_it`:
    the defect below, in the shape the box presented it.
  - containment and admission, in isolation, plus the CLI's failure modes.
- `cargo build --release` for `x86_64-unknown-linux-musl`: clean apart from
  two pre-existing dead-code warnings in `upnp.rs`.

## What the router proved

The build is deployed and running: `/usr/bin/ds-lite-punch` md5
`cd8e49bedb7848e8a1a2cc283905c6f5`, the previous binaries parked at
`/root/ds-lite-punch.prev` and `.prev2`, the service restarted, the external
tuple up, and the facade's state restored (the three console pins are back in
`snat_map`). Two restarts carried it, and the new startup line names the
admission in force: `{"event":"observe","cdc":"nft","max_rescues":8,"allowed":0,"hold":false}`.

`deploy/pcp-probe.py` (a stdlib PCP and NAT-PMP client, written for this
line's acceptance and shipped with the crate) was run against
`192.168.21.1:5351`. Every answer was the specification's. The block below is
the client's own output, reproduced verbatim and therefore boxed from the
naming scan: the fields it carries are protocol quantities, not references.

```host-lint:ignore
ANNOUNCE: opcode 0 code 0 (SUCCESS) lifetime 0 epoch 18
MAP proto 132: code 9 (UNSUPP_PROTOCOL)
MAP with FILTER: code 13 (EXCESSIVE_REMOTE_PEERS)
MAP with PREFER_FAILURE: code 11 (CANNOT_PROVIDE_EXTERNAL)
MAP: no answer (drop) after 4.0s
MAP (retry): code 0 (SUCCESS) lifetime 120 assigned 37.228.213.83:59221
MAP (renew): code 0 (SUCCESS) assigned 37.228.213.83:59221
MAP lifetime 0 (delete): code 0 (SUCCESS) lifetime 0
NAT-PMP op 0: SUCCESS external 37.228.213.83
NAT-PMP op 1: no answer
NAT-PMP op 9: op 137 code 5 (UNSUPP_OPCODE)
```

Read against this milestone's own rules: the assigned tuple is the one the
slot's STUN discovery actually learned rather than a guess (59221, and the
renewal reported the same one); a mapping whose discovery was still in flight
was dropped rather than answered (which is why the probe retries); and the
refusals used the RFC's codes for exactly those cases.

Two further on-box facts. The new flags are in the deployed binary's usage
and both allowlist failure modes name themselves before any work is done:

```
error: --allowlist /tmp/bad.allow: not an address: 192.168.21.1/24
error: --allowlist /tmp/absent.allow: No such file or directory (os error 2)
```

And the PCP listener is **enabled on the router** (`PCP=1` in
`/etc/ds-lite-punch.env`). The revert is that line removed and a restart.

## The defect the box found

The first probe run was answered with `37.228.213.83:59365`, a port no live
mapping held. The cause was in the datapath, not in the new code: a revoked
mapping left its per-slot tuple file behind, and the port allocator hands out
the lowest free slot, so the fresh grant landed on a port whose file still
carried a dead tuple. Three stale files were on the box from mappings revoked
hours earlier (slots 40003, 40004 and 40005). The allocator's choice makes
this likely rather than rare, and the answer is authoritative to the client:
a PCP client would publish that port to its peer and wait for packets the
AFTR no longer maps.

Fixed at `acd1162`: every revoke path now removes the file (the delete, the
pool-pressure eviction, the stray surrender, the lease GC and the grant
rollback), and the test plants a file for an entry with no lease and deletes
the mapping, which is the box's own case. The fix is proven by the same
probe: the first MAP is dropped, the retry carries the fresh tuple, and no
stale file survives the run. The three historical files were removed by hand,
and the state directory now holds only its live slots' tuples.

## The collision rules, and the port the rule steered around

A port becomes the daemon's in two ways and only one of them had a rule: an
allocation has a lease, and a punch has nothing but its packet while the AFTR
honours it anyway. `call/0027` states the rules in the form the RFC paths are
stated in, and three of them are enforced in this build:

- the allocator probes the live post-NAT set before a fresh allocation and
  skips a port a punch already holds (the table's reservation, refreshed from
  the same mirror the observation arm reads, so both mechanisms see one set of
  tuples);
- the observation arm reads the live lease table each tick, so a tuple a grant
  took after the arm started is not one it captures (the frozen start-up
  snapshot could not see that grant);
- every steering decision is logged with the ports it involved, because a
  collision resolved in silence is the one outcome the rules forbid.

The box read it back on the first fresh grant after the deploy:

```host-lint:ignore
{"event":"collision-avoided","detail":"slot 40003 steered around the live tuple(s) [40001]"}
```

Which is the rule working on exactly the case it was written for: slot 40001
was live and nobody had allocated it, so the grant took the next port instead
of sharing a tuple the AFTR keys as one mapping. Two slots the table already
held (40000 and 40002) are not in that list, because avoiding a port the
allocator holds is its ordinary business rather than a collision decision.

Two things the decision leaves to measurement, and neither is settled by
assumption: whether the local NAPT can punch a port a local socket already
holds (if it cannot, the probe is complete and the late-collision rule is
unreachable; if it can, that rule is the one that matters), and whether the
AFTR ever answers one external port to two inner tuples, which the per-slot
reads would show as a repeat and which is an uplink defect when it appears.

## Where this build diverges from the implementation notes

The notes said to verify the protocol details against the RFCs and to expect
the sketch to be wrong. It was wrong in two places, and both are decided in
the shipping code:

- **The result codes.** The notes carried "0 to 8 plus
  CANNOT_PROVIDE_EXTERNAL_PORT = 9". The RFC's own table numbers them 0..13,
  where 8 is NO_RESOURCES, 9 is UNSUPP_PROTOCOL, 10 is USER_EX_QUOTA, and the
  external-port refusal is 11. The RFC numbering ships, and the probe above
  reads back the codes a client would see.
- **An ANNOUNCE cannot carry a tuple.** The notes said the learned tuple
  "follows in an ANNOUNCE". An ANNOUNCE has no opcode-specific payload at all,
  so it carries no tuple. The MAP response carries the assigned external port
  and address, and it is where the learned truth goes. NAT-PMP's version error
  was corrected the same way: the specification's own diagram is eight octets
  with the opcode zero.

Three further choices differ from the notes' wording, each for a reason that
is recorded in the code:

- **FILTER is refused, not installed.** The notes said to honour it. This
  datapath is endpoint-independent by design, so a filter would have to be
  claimed and not enforced. The RFC provides the code for exactly this
  server, EXCESSIVE_REMOTE_PEERS, and the probe above reads it back.
- **PCP MAP admits TCP.** plan/0004 refused TCP "until the TCP idle-lifetime
  measure". That measure exists now and this milestone carries it, so the
  refusal's stated condition is satisfied and a TCP mapping rides the same
  slot engine, bounded by what call/0026 decides about holding it.
- **The policy lives in the daemon's own table.** The notes preferred an
  include under `/etc/nftables.d/` that fw4 loads. The list that drives the
  hold also drives the rules, so one owner is what keeps them from drifting;
  `table ip dslp` is already the daemon's, fw4's generator contains no
  `flush ruleset`, and the stop path's table delete reverts the policy with
  the rest of the datapath. The include form remains available if the policy
  should outlive the daemon, and it costs one UCI stanza plus a file the
  daemon would have to keep in step.
- **The list is an inline address list, not an nft set.** The whole fragment
  is regenerated from the allowlist at every start, so a set object would buy
  nothing and the generated ruleset stays readable as one piece.

One semantic is worth stating because it is a deliberate shape: an **empty
allowlist** leaves the arm the admission it was verified with (the CDC's own
predicate), and a **non-empty** one narrows it to the named devices. A
deployment that never names a device keeps yesterday's behaviour, which is
what the router is running now, and naming the first device is the act that
puts it on the list.

## What still needs an operator

The policy install is the one step this session did not take. It is the
change that puts new nftables rules on the live firewall, and it was left
alone deliberately rather than attempted around. Everything else it needs is
already deployed. Each line below is the whole command.

1. The log-only stage, which reads the named devices' live flows before
   anything is held (the two consoles are DHCP-pinned):

```
ssh root@192.168.21.1 'printf "# consoles\n192.168.21.68\n192.168.21.138\n" > /etc/ds-lite-punch.allow && sed -i "s|^# ALLOWLIST=.*|ALLOWLIST=/etc/ds-lite-punch.allow|" /etc/ds-lite-punch.env && sed -i "s|^# OBSERVATION=1|OBSERVATION=1|" /etc/ds-lite-punch.env && /etc/init.d/ds-lite-punch restart && sleep 20 && logread | grep -E "observe|hold" | tail -20'
```

2. Turn the hold on, and read the policy back. This is the step that installs
   the conntrack policy:

```
ssh root@192.168.21.1 'printf "HOLD=1\n" >> /etc/ds-lite-punch.env && /etc/init.d/ds-lite-punch restart && sleep 5 && logread | grep hold | tail -3 && nft list table ip dslp | grep -A6 "chain preraw"'
```

3. The behaviour proof, which is the part a parse does not show: hold a quiet
   flow from a named device and the same from a device that is not named, then
   compare their rows after a minute of silence. The named device's row is
   still there with a remaining timeout at or above the floor; the unnamed
   device's row is gone.

4. The acceptance under silence, with the external vantage at
   `ubuntu@170.9.238.141` probing the learned tuple at 30, 60 and 120 seconds
   of client silence, and the AFTR's own threshold measured from the death
   point of a held flow and an unheld one at 60, 120 and 300 seconds.

The revert for every stage is in this milestone's README: the table delete
returns every flow to the router's own timeouts, and the parked binaries are
the daemon's revert.

## What this leaves open

- The AFTR's true UDP threshold under silence. The two-second cadence is what
  is known to work, and the death point that would justify anything longer is
  unmeasured on this line.
- Whether any device here needs the hold at all. The one console measured so
  far maintains its own mapping, so the list may stay at its bootstrap pair.
- The assigned-port divergence for a real PCP client: the response carries the
  learned tuple, and the probe here acts on it, but a client that ignores the
  assignment and keeps its own suggestion is still unmeasured.
- The stale `upnp.tsv` row the earlier deploy window left behind, and the
  household 3074/UDP mapping that window lost. Neither is touched here.
- EIF-loss detection, which the previous milestone carried past v2.