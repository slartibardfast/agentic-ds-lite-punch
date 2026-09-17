# The operator bootstraps DeviceProtection out of band

- Status: accepted
- Scope: the ds-lite-punch facade's DeviceProtection store and its procd
  service (plan/0008's v2 surface)
- Date: 2026-09-17

## Context and Problem Statement

The v2 surface carries an enforced authorization boundary: the mapping
mutators require an authenticated session holding at least `Basic`
(plan/0008's boundary, `call/0018`, `call/0022`), and their refusal is 606.
The specification's in-band way to create the first identity is the WPS
introduction protocol, which `call/0021` defers: its message encoding is not
available to this project and the exchange requires a certificate-
authenticated transport this facade does not carry.

So a fresh device cannot be administered at all. The store is empty, no
identity exists, no control point can hold a role, and the containment can
never be lifted. T4's bench had to write `dp.tsv` by hand and restart the
service to exercise the authenticated half of the matrix, which is a bench
trick rather than an operator procedure. And the state directory the store
lives in is tmpfs, so even that would not survive a reboot.

## Decision

The operator bootstraps the store out of band, from a root-owned file in
`/etc`, because that is the only path that exists before an identity does.

- The file (default `/etc/ds-lite-punch.acl`, moved or disabled by
  `DEVICE_PROTECTION_ACL`) holds the store in the daemon's own tab-separated
  form: `U` rows for PKCS5 users (`name`, hex salt, hex STORED, roles) and `A`
  rows for ACL identities (`name`, alias, hex identity, roles).
- The init script copies it into the state directory **at start, and only
  when no store exists yet**. A seed that fired on every start would revert
  whatever a control point had since changed over the wire; seeding once
  creates the first identity and leaves the store the device's own thereafter.
- Absent, or set to `none`, the seed does nothing and the empty-store refusal
  stands: no identity, every role-gated action 606, the fail-closed default.
- The file is `root`-owned and mode-restricted like the rest of `/etc`. Its
  contents are a credential, so it is not committed to any repository, and the
  component ships the procedure and not an example secret.

## Consequences

- **The deployed surface becomes administerable.** The operator creates one
  `Admin` identity (and a PKCS5 user for the ceremony), puts it in the file,
  restarts, and can then authenticate over the wire and lift the containment.
  Nothing else in the v2 surface needs to change for that to work.
- **The bootstrap is a documented procedure rather than a bench secret.** The
  file's format, the PBKDF2 derivation of `stored`, and the roles are written
  in the component's deploy notes beside the service, so the device can be
  re-administered after a factory reset without the agent that built it.
- **Revocation is file surgery plus a restart**, and it is stated plainly:
  remove or edit the file and delete `/run/ds-lite-punch/dp.tsv`, then restart.
  A store the device already holds is never silently overwritten.
- **This is a bootstrap, not the introduction protocol.** It does not give a
  control point a way to introduce *itself*; that remains `call/0021`'s
  deferral, and a reversal there would make this decision unnecessary rather
  than wrong.
- The bench's own seed is never left in place: verification ends with the file
  and the store removed, so the device returns to fail-closed, which is the
  state the T4 record documents.