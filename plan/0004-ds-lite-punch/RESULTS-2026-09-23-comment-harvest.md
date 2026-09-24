# The comment harvest

- Date: 2026-09-23
- Component: ds-lite-punch at `13a5fc06` (the `v0.3.4` tag), whose source
  comments are being collapsed to one line each
- Why: a comment run of more than one line dilutes the code, so the rule from
  this date is one line, technical only. This record takes what the long
  comments stated and nothing else does, so the collapse loses no fact.

## What this record is, and what it is not

It is the residue: the facts that lived only in a source comment. It is not a
copy of the design, and not a copy of the measurements. The comparison
documents were `plan/0004-ds-lite-punch/IMPLEMENTATION.md` (the design brief),
`MEMORY.md`, and the results files of plan/0007, plan/0008, plan/0009 and
plan/0010. Facts those documents already carry are named below as carried, and
not restated.

The full pre-collapse text of every comment stays in the git history of the
commit that removed it, one commit per file.

## Persistence, and the two state directories

`persist.rs` and `publish.rs` write the daemon's state into **two** directories,
and nothing else in the project says so. This is the finding the harvest paid
for, because the manual page and the operator pages stated one directory.

| Directory | Files | Written by |
|---|---|---|
| `/tmp/dslp`, a fixed path (`persist::DEFAULT_DIR`) | `epoch`, `leases.tsv`, `upnp.tsv` | `persist.rs`, on every change, atomically |
| the state directory, `--state-dir`, default `/run/ds-lite-punch` | `tuple`, `tuple-<R>`, `upnp-ident`, and `dp.tsv` | `publish.rs`, `upnpsvc.rs` |

Confirmed on the router on 2026-09-23: `/tmp/dslp/` held `epoch` (11 bytes,
written 2026-09-14), `leases.tsv` (38 bytes) and an empty `upnp.tsv`, while
`/run/ds-lite-punch/` held `tuple`, `tuple-40000` and `upnp-ident`. The init
script seeds the DeviceProtection store at `$STATE/dp.tsv`, where `STATE` is
`/run/ds-lite-punch`.

Both directories are on temporary filesystems, so every file survives a restart
of the daemon and none of them survives a reboot.

**Carried elsewhere:** that a lease record and a mapping share a lifetime
(MEMORY, the lease-churn work), and the tuple file's role in answering a client
(call/0022, the man page's FILES section).

## The tuple file's lifetime, and the write that publishes

From `publish.rs`, two facts worth keeping as one line each in the code:

- A tuple file goes when its mapping goes. The file holds the **learned** tuple,
  so one that outlives its mapping is a lie a client can act on: a later mapping
  that takes the same bind port would be answered with the dead port. The box
  found this on 2026-09-17 with three revoked slots still carrying their old
  tuples.
- Renaming a temporary file over the good one is what publishes a record, so the
  rename must happen only when the write did. Renaming unconditionally published
  an empty file over a good table when the state directory was full, which is
  what a zero-byte `upnp.tsv` and a long-running daemon were on the router on
  2026-09-18.

**Carried elsewhere:** the emit helpers exist because `panic = "abort"` makes a
panicking `println!` fatal and a poisoned mutex abort the next request
(call/0029). The memory-first tuple read is documented in the manual page's
FILES section.

## The netlink conntrack delete, abandoned

`ct.rs` is a documented dead end, and the reason is a kernel-build quirk:

- Deleting a conntrack entry by netlink returns `EINVAL` on this 6.12.35
  ImmortalWrt build for **every** encoding tried (family 0 and 2, with and
  without `NLA_F_NESTED`, original and reply direction, with and without a
  zone), while a canonical libmnl-shaped message fails the same way. No
  conntrack tool is installable from the router's package set.
- The encodings were bisected with a `--ct-probe` flag that creates its own
  conntrack entry from a fresh local socket, tries each variant against it, and
  prints each acknowledgement code. That flag stays in the binary for
  re-bisecting.
- The mechanism that replaced it is the self-pin: an explicit
  `(NAT, R_nat) → (NAT, R_nat)` map element makes the shadow's keepalives egress
  under the observed tuple with no deletion at all, by the same explicit-tuple
  source translation the slot pins use.
- Why the deletion was wanted: the kernel source-translates the shadow's
  keepalives to a fresh ephemeral port (measured on this box 2026-09-02,
  41077 to 1024), so the refresh lands on a mapping of its own while the
  observed one dies at the AFTR's timeout.
- The wire shape is recorded here because the code is dead: the tuple bytes
  appear big-endian in the payload, and nested attributes need
  `NLA_F_NESTED` or strict nfnetlink validation rejects them with `EINVAL`.

**Carried elsewhere:** the self-pin is item G3(c) of the brief's observation
engine and appears in the engine's own comments and in MEMORY; the ephemeral
port measurement is in MEMORY.