# A client's admission is a certificate the line minted

- Status: accepted
- Scope: how a client of a front-door name becomes an identity: where the authority
  lives, what a certificate carries, how long it lasts, and how an identity stops
  being authorised
- Date: 2026-09-27

## Context and Problem Statement

`call/0038` puts admission at the front, and a client certificate is the one thing
the front can check there. The carrier's mapping belongs to the line, and the
front is the only party that sees the client, so the check has to happen where the
client arrives.

DeviceProtection:1 already supplies identities, PBKDF2 passwords and roles
(`src/dp.rs`), behind a facade that refuses callers outside the LAN
(`src/upnpsvc.rs:952`). It has no X.509 notion at all: `SendSetupMessage` answers
704 because this device runs no registrar, so a certificate programme runs beside
DP rather than inside it.

## Decision

- The authority lives on the line. A certificate is minted after a login that the
  DP store authenticates, so possession of a certificate records that login.
- The certificate carries the identity and what that identity may reach. The front
  checks a chain and reads a permission from it, and never asks the line about a
  connection.
- A certificate is short-lived and renewed. Exclusion is then a decision not to
  renew, and no revocation list has to be published anywhere.
- The daemon is a client of the same programme. It holds an identity for its own
  control channel, and the front verifies it there.
- The front keeps the public half of the authority, and nothing else about the
  identity store.

## Consequences

One authority, one enforcement point. The front holds no copy of the roles, so a
role change takes effect at the next renewal rather than immediately, and a
revocation has no path to travel.

A renewal gap is an outage for that client, and the lifetime is the knob that
trades that against the cost of exclusion. Short lifetimes suit a small number of
identities, which is the case this front door serves.

The means of minting belongs to the milestone: which tool holds the authority, and
how a login gates a mint. This record settles the properties, and the properties
are what the front depends on.

## What this does not claim

A certificate is only as good as the ceremony behind it. A login that anyone on
the LAN can complete mints a certificate for anyone on the LAN, so the DP roles
are the real gate and the certificate is how that gate's decision travels out to
the front.