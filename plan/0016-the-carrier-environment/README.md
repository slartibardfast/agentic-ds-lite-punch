# The carrier environment for end-to-end testing

**Status:** claimed 11 November 2026, and the active goal. The carrier research, the topology, the carrier's policy plane and the front's deployment are receipted; the b4 and the service are the frontier.

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
a generalised AFTR: the RFC 4787/5382 behavioural space as configuration
(mapping and filtering behaviours, timers, port assignment, hairpinning), with
carrier profiles as configurations and the measured Virgin Media ds-lite profile
as the default instantiation, so the daemon is exercised across carriers instead
of against one ISP's idioms. The daemon rides in its b4 namespace, so the whole
exchange (poke, admission, forward, answer, push) is exercised with the front in
the loop. Every deployment aspect is tested: the
files land where the units expect, the certificates are minted the way the line
mints them, the deployed files are checked against the record so the stale-relay
class of failure fails the harness instead of the household.

The carrier model, the profiles, and the open mapping conflict the harness's
differential run settles, are
[the research](results/RESEARCH-2026-11-11-the-aftr-in-the-record.md).

## Build sequence

### Record the carrier fidelity model {#fidelity-model}

- verify: test -f results/RESEARCH-2026-11-11-the-aftr-in-the-record.md
- inputs: plan/0016-the-carrier-environment/results/RESEARCH-2026-11-11-the-aftr-in-the-record.md

Done the day the milestone was claimed: the general model (the RFC 4787/5382
behavioural space as knobs, with the RFC 6333 extended binding table and the
transparent B4), the three carrier profiles, and the measured Virgin rows with
their sources. The record also names the open mapping conflict between the two
measurement eras.

### Stand up the topology {#topology}

- depends: #fidelity-model
- verify: python3 deploy/env/envctl.py verify

One command stands the five actors up and tears them down, and a datagram from
the internet actor reaches the carrier. The namespaces and their wiring:
`carrier` (the simulated AFTR), `front` (where
the nginx feature is deployed), `b4` (the real daemon), `service` (the target),
`internet` (the external peer). One script stands the topology up and one tears
it down; nothing leaks outside the namespaces. Without root it re-execs itself
inside a user namespace, so the whole environment runs unprivileged.

### Write the carrier's data plane and policy {#carrier-policy}

- depends: #topology
- verify: python3 deploy/env/envctl.py verify-policy

The nftables NAT44 on the carrier plus the userspace policy plane reading a
profile: the mapping and filtering behaviours, the timers with silent expiry,
the answered-poke precondition where the profile sets it, and the port
assignment. Three profiles ship: `vm-dslite` (the measured default, its open
mapping conflict named), `rfc-bcp` (the RFC best case), and `symmetric` (the
hardest).

### Deploy the front by its own pipeline {#front-deployment}

- depends: #carrier-policy
- verify: python3 deploy/env/envctl.py deploy-front
- inputs: software/ds-lite-punch/main/deploy/env/envctl.py, software/ds-lite-punch/main/deploy/front-door/install.sh, software/ds-lite-punch/main/deploy/front-door/render.sh, software/ds-lite-punch/main/deploy/front-door/mint.sh, software/ds-lite-punch/main/deploy/front-door/nginx.conf, software/ds-lite-punch/main/deploy/front-door/poke-listener.py, software/ds-lite-punch/main/deploy/front-door/front-door-nginx.service.in, software/ds-lite-punch/main/deploy/front-door/front-door-poke.service.in

One command deploys the front and probes it from outside the front
namespace. mint.sh signs the authority and both identities inside the front
namespace, and install.sh renders the configuration and the units with the
new --units-dir mode: the namespace has no init to enable them, so the
harness starts each unit's own ExecStart line. The distro nginx and its
stream module are provisioned unprivileged (apt download and dpkg-deb -x)
into the environment's cache, and the pipeline's --nginx and --module name
them. The render names the workers' account (user root), because a
namespace's setgroups denial makes the package's default account an invalid
id and nginx refuses to start over it. For proof, the protected name answers
the table over TLS with the daemon's minted identity, and a poke teaches the
relay the tuple, which the map records before nginx reloads on it and keeps
serving. Nothing is hand-placed.

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
- verify: every scenario row green across the three profiles in one command, and the suite runs in CI

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
