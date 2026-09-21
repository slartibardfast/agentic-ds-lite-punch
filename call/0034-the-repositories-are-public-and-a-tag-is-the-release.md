# The repositories are public, and a tag is the release its artifact rides

- Status: accepted
- Scope: how these two repositories are exposed, and how a release is cut: the
  visibility, what publishing accounts for, the mechanics of a release, and the
  credential that was retired with it
- Date: 2026-09-20

## Context and Problem Statement

[call/0032](0032-the-builder-of-record-is-the-lane.md) recorded that rebuilding
from the pin is possible "for anyone with the repository and a container
runtime", and that how widely that reaches is bounded by the repository's
visibility, which it left to the operator. The operator ruled for wide reach.
Both repositories were private, and one of them, the host, carries the thought
in full: the plans, the decisions, the results and the memory.

Publishing a network project is more than a visibility flag. The docs carry
ground truth about the line. The lane that builds the artifact turned out not to
be reachable from outside at all. And a host lane cloned the component with a
long-lived token, which a public component makes unnecessary.

## Decision

- **Both repositories are public, and they publish together.** Their READMEs
  point at each other, so a public half would leave dead links on the side a
  stranger reads first.
- **The audit precedes the exposure, and it stayed clean.** `gitleaks` over both
  full histories found no leaks, and a targeted sweep behind it found no private
  keys, no WireGuard material, no tokens, no password assignment outside the
  DeviceProtection specification's own text, no PUK, no PIN and no UDN uuid.
  What publishing does expose is accounted rather than denied: the line's
  external addresses, the br-lan layout, two device MACs, the operator's name and
  address in every commit's metadata, and the DeviceProtection:1 and WIP2
  transcriptions, whose redistribution terms are a licensing question.
- **A tag is the release, and the artifact is a release asset.** `v0.1.0` sits at
  the commit the record pins. A tag-triggered job builds the musl binary inside
  the same digest-pinned image and attaches it with the line that records its
  hash. An Actions artifact is not the vehicle: measured on 2026-09-20, an
  anonymous listing answers 200 and an anonymous download answers 401, so the
  asset is what makes the bytes a stranger fetches the bytes the router runs.
- **The read token is retired.** Its only job was cloning a private component,
  and the secret is deleted rather than kept for a case that no longer exists.
- **Every lane declares what it needs.** `permissions: contents: read` on the
  lanes that only read, and write on the one job that creates a release, so a
  pull request from a fork cannot reach a credential or a release path.

## Consequences

- A stranger can clone either repository, read the record, rebuild from the pin,
  and download the deployed bytes: the asset's sha256 equals the recorded
  anchor, checked without credentials on 2026-09-20.
- The exposure is durable. What has been fetched cannot be withdrawn, and the
  audit's accounting in `MEMORY.md` is the price of the reach.
- A release now depends on the forge: it is a tag and a lane run rather than a
  local build, and the host's reproducible lane no longer needs a credential to
  materialize the component.
- The transcriptions are published under the terms of the documents they
  transcribe, which is the operator's matter and not a secret.