# Plain language for the program: keepalive, owned, entry

- Status: accepted
- Scope: the words the software uses for its own parts, and for its flags, log
  events and pages
- Date: 2026-09-22

## Context and Problem Statement

The operator rejected three words in what shipped, one after another:
`--max-rescues`, whose plural hid what the number counts; `hold`, a coinage this
project invented for a mapping it keeps alive; and the comment vocabulary
`rides` and `lands`, which is business jargon. The standard they set is simple
language from the RFCs, the words a network engineer already reads.

Naming is identity here, so those words had reached further than the help text:
a flag, an environment key, a log event, a module, a milestone folder, a
decision slug, and the comments of every source file.

## Decision

Each sense of the old word takes the word that says what it is, anchored in the
source of the behaviour.

| Sense | Was | Is | Anchor |
|---|---|---|---|
| keeping a named device's mapping alive | `--hold`, `HOLD`, the `hold` event, `hold.rs` | `--keepalive`, `KEEPALIVE`, the `keepalive` event, `keepalive.rs` | RFC 8085, on keepalives: the packets that keep a binding open |
| attempts to put a vanished mapping back | `--max-rescues` | `--max-refresh-attempts` | RFC 4787, on mapping refresh: a timer is refreshed by traffic |
| a tuple a slot owns | `held`, `is_held` | `owned`, `is_owned` | the code already said "own", and the I1 gate is `claim_allowed` |
| the TCP connection that maintains a mapping | `HolderState`, `run_holder`, `holder` | `ConnectionState`, `run_connection`, `connection`, with `Live` and `Dead` | a STUN-over-TCP connection's liveness |
| a client's record in the facade | `holder`, the one-holder rule | `entry`, the one-mapping rule | the facade's own table of entries |

The flag rename is a removal and an addition, so the release that carries it is
a minor bump. From 0.2.0 on, a version bump also moves the artifact's bytes,
because `--version` compiles the version in.

## Consequences

The help text, the manual page and the operator pages speak one
language, and the source comments speak it too. The path renames reach
`plan/0009-mapping-keepalive-and-signalling` and
`call/0026-tcp-keepalive-is-signalled-not-injected`.

Three things deliberately did not change.

The name of the software. *DS-Lite Proxy UPnP NAT/CGNAT Holder* is the derived
name of `punch`, and the operator set it.

Ordinary English. A lock is held, a directory holds files, a client holds a
mapping, and a rule holds. Those read as what they are.

The records. `MEMORY.md`, the closed milestone bodies and the results files keep
the words they were written with, because a record quotes what was true and what
was said at the time. The earlier attempts are visible in that layer: the flag
was first renamed to `--max-rescue`, which the operator rejected for the same
reason as `--max-rescues`, and the sweep that followed this decision carries the
final words.