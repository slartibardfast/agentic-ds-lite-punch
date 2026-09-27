# The front's proofs are the component's lane, and a deployment's are the recipe's

- Status: accepted
- Scope: where the front door's verification lives: which clauses the component's
  lane discharges, and which wait on a deployment
- Date: 2026-09-27

## Context and Problem Statement

The front's configuration, its listener and its lease run on a machine that has
nginx, python3 and openssl. The host repository carries the plan and the receipts,
and a clone of it has none of those three, so a host-side task whose verify is a
command cannot hold for the front's proofs. The component's lane installs nginx,
runs `deploy/front-door/test-local.sh`, and does that on every push.

## Decision

- The front's proofs are discharged by the component's lane. The harness it runs on
  every push is the evidence for the split by name, for the tuple the front learns
  from the poke, and for the lease that withdraws an entry whose pokes have stopped.
- A host-side task that carries one of those proofs cites this decision. A citation
  is re-derivable by anyone with the repository, where an operator attestation is
  re-derivable by nobody.
- The TCP leg's handshake is a deployment's, and this decision records it as such.
  The arrival is measured, and the answer needs a service host whose replies take
  the line the mapping is on. The recipe carries both requirements, and the task
  that needs them records the deferral rather than passing on a claim.

## Consequences

A clone of the host can re-derive the front's proofs by running the component's
lane, and nothing in the host claims to have run nginx itself.

An unrunnable clause stays unrunnable. This decision gives the front's proofs a
citation, and it gives the deployment's clauses their owner: the operator who runs
the recipe.