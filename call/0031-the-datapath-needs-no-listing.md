# The datapath never needs a listing, and an intermittent nft crash is tolerated

- Status: accepted
- Scope: the ds-lite-punch daemon's use of the nft CLI, how a slot's inbound
  accept is installed and removed, and what a failed nft call may do
- Date: 2026-09-19

## Context and Problem Statement

The daemon drives nftables through the `nft` command, and every per-slot
inbound accept used to be an `fw4` input *rule*. That rule was deleted by a
handle read out of `nft -a list chain inet fw4 input`, and two things went
wrong with it, both measured on the test router on 2026-09-18:

- `delete rule` by expression is refused by this build. The attempt
  `nft delete rule inet fw4 input iifname "eth1" udp dport 49001 accept
  comment "dslitepunch-49001"` answers `syntax error, unexpected iifname,
  expecting handle`, so a handle is the only way and a listing is the only
  source of one.
- A delete that could not read the listing left its rule installed. Two accept
  rules from earlier daemons were still in the chain, `dslitepunch-40002-tcp`
  for a protocol the running daemon does not enable and a legacy
  `dslitepunch` with no port in its comment. An inbound accept that outlives
  its slot is a port opened for nobody.

Separately, the kernel log carries intermittent crashes of the `nft` command
inside libnftables (`segfault at 20040 ... error 4 in libnftables.so.1.1.0`,
the same code bytes every time), 24 of them over one session, and they
coincide with daemon activity: installs of the hold policy, the facade's
grants and revokes, the observation arm's pins. They are not reproducible from
a shell: 60 hand-run cycles of the daemon's two hold batches, 3000 listings,
and 1200 concurrent and mixed read and write invocations produced none, with
no failed call among them.

## Decision

- **A slot's inbound accept is an element of a set the daemon names**, one set
  per protocol (`dslp_ports_udp` and `dslp_ports_tcp`), with the two rules
  that accept those sets installed once. Element operations are addressed by
  key, so no per-slot operation needs a handle and none needs a listing.
- **The sets are emptied when the daemon installs them.** The boot path then
  adds an element for every slot restored from the persisted table, after the
  ruleset is installed, so a restart keeps exactly the ports its table holds
  and the sets never carry a port the table does not.
- **One listing is read at startup**, for the two questions it can answer
  cheaply: whether the accept rules are already installed, and whether an
  older daemon left per-port litter behind. Litter is removed by handle from
  that same listing, once. A listing that fails leaves the rules alone rather
  than adding a second copy of them.
- **An intermittent crash of the `nft` command is not chased.** It belongs to
  libnftables, it is not reproducible by shape, volume or concurrency, and
  every call site already treats a failed call as a failed call: the hold
  policy is reported as absent, a grant is refused, a revoke is retried by the
  per-operation path. Nothing assumes an `nft` call succeeded.

## Consequences

- The datapath cannot leak an accept. An element goes away by key, and a
  restart reconciles the sets to the table rather than inheriting the last
  run's ports.
- A UDP slot no longer opens a TCP accept for its port, which a single set for
  both protocols would have done.
- fw4's table now carries two sets and two rules the daemon owns. An
  `fw4 reload` wipes them, exactly as it wiped the per-port rules before, and
  the daemon does not notice either way. That is unchanged by this decision
  and is not addressed here.
- If the `nft` command does crash, what the daemon loses is one call, which is
  logged; it does not lose the correctness of the datapath, because the
  datapath is not derived from a listing.