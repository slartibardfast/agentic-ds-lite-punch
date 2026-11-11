# The carrier environment for end-to-end testing

**Status:** claimed 11 November 2026. The AFTR research is recorded with its
sources, the design follows from it, and the build sequence is sketched; the
shape is in the operator's hands for approval before the first task is
receipted.

## What this milestone is

The daemon cannot prove itself without the live line, and the November line-mode
change showed what that costs: the rig's fixtures died with the box, the front's
relay ran stale against the record once already, and the UDP leg stopped closing
mid-flight with nothing able to answer "does the daemon still behave correctly?".

This milestone stands up the environment that fixes the loop for the feature the
household actually consumes: **the nginx front door**. The front is deployed into
the environment by the repository's own pipeline (install, render, mint, units),
so iterating on the split by name, the relay, the map and the deployment itself
is a harness run rather than an edit against production. The carrier around it is
simulated at the fidelity the record measured, and the daemon rides in its b4
namespace so the whole exchange — poke, admission, forward, answer, push — is
exercised with the front in the loop. Every deployment aspect is tested: the
files land where the units expect, the certificates are minted the way the line
mints them, the deployed files are checked against the record so the stale-relay
class of failure fails the harness instead of the household.

The fidelity model — every behaviour with its source, measured rows winning over
RFC floors where the real device breaks them — is
[the research](results/RESEARCH-2026-11-11-the-aftr-in-the-record.md).

## Build sequence

### Record the AFTR fidelity model {#fidelity-model}

- verify: test -f results/RESEARCH-2026-11-11-the-aftr-in-the-record.md
- inputs: results/RESEARCH-2026-11-11-the-aftr-in-the-record.md

Done the day the milestone was claimed: the architecture (the hub as the
transparent B4, the AFTR as the sole NAT44 with its IPv6-extended binding
table), the eleven-row behaviour table with a source per row, the RFC floors the
real AFTR breaks, and today's native-path incident folded in as a scenario.

### Stand up the topology {#topology}

- depends: #fidelity-model
- verify: one command stands the five actors up and tears them down, and a datagram crosses from the internet actor to the carrier

The namespaces and their wiring: `carrier` (the simulated AFTR), `front` (where
the nginx feature is deployed), `b4` (the real daemon), `service` (the target),
`internet` (the external peer). One script stands it up, one tears it down, and
nothing leaks outside them.

### Write the carrier's data plane and policy {#carrier-policy}

- depends: #topology
- verify: a poke from b4 allocates a tuple, the poked peer's arrival crosses, a stranger's is refused, and silence expires the mapping

The nftables NAT44 on the carrier plus the userspace policy plane implementing
rows 1-6 of the fidelity model: the answered-poke table, the per-destination
tuple allocation, and the short silent timer set to the measured value.

### Deploy the front by its own pipeline {#front-deployment}

- depends: #carrier-policy
- verify: install.sh, render.sh and mint.sh complete inside the front namespace, and the units come up serving on the public port

The front is deployed by the repository's deployment pipeline into the front
namespace, with the file layout and the unit equivalent the namespace supports.
Nothing is hand-placed: a deployment step that only works on production is a
defect this task exists to expose.

### Bring up the b4 and the service {#b4-and-service}

- depends: #front-deployment
- verify: the daemon holds a mapping toward the carrier, the service answers through the slot, and the daemon's push reaches the front's report

The real daemon binary in the b4 namespace with its nft datapath, pointed at the
carrier and the front, and the fake target service answering beside it.

### Check the deployment against the record {#drift-check}

- depends: #front-deployment
- verify: a seeded drift (an edited deployed file) fails the check, and a clean deployment passes it

The stale-relay class of failure as a test: every deployed front file is hashed
against the record the repository ships, and a mismatch fails the run with the
drifting file named.

### Assert the whole exchange {#the-harness}

- depends: #b4-and-service, #drift-check
- verify: every scenario row green in one command, and the suite runs in CI

One command asserting the nginx feature end to end: the pass-through name
reaches the service's own certificate, the protected name refuses without a
client certificate and serves with one, an unpublished name reaches nothing, the
datagram leg closes, the relay follows the poke, the push names its view, the
lease expires, and the stranger is refused. Iterating on the nginx feature means
editing its source, deploying into the environment, and running this command.

### Stand up the monitors {#the-monitors}

- depends: #the-harness
- verify: the external monitor and the router-side event sampler are emitted by the repository and documented

The standing correlation pair the record calls for: an external monitor over the
published path, and a router-side event sampler, so a line anomaly arrives with
its mechanism named.

## The retired shapes and why

A userspace-only carrier was the first sketch; the operator set the fidelity bar
at kernel-real, and the datagram leg's dependence on real nft keying and real
decapsulation is what a lighter fake would have hidden. Testing the front only
by its harness (the `test-local.sh` shape) is retired for the same reason: it
proves the configuration renders and answers locally, and says nothing about the
deployment that puts it on a machine.