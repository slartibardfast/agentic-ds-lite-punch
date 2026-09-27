# The TCP slot's protocol is whole; a service host is what remains

**Date:** 2026-09-27. **Task:** `plan/0012#hold-tcp-slot`. **Status:** the facade
now answers a TCP mapping properly, and one inference in the previous record is
withdrawn.

## The mapping answers

With the holder able to learn a TCP tuple, the facade's answer carries it:

```
MAP: opcode 1 code 0 (SUCCESS) lifetime 300 epoch 1307 proto 6 internal 8443 assigned 37.228.213.83:59351
MAP (renew): opcode 1 code 0 (SUCCESS) lifetime 300 epoch 1307 proto 6 internal 8443 assigned 37.228.213.83:59351
MAP lifetime 0 (delete): opcode 1 code 0 (SUCCESS) lifetime 0 epoch 1307 proto 6 internal 8443 assigned 0.0.0.0:0
```

A grant, a renewal that keeps the same tuple, and a delete, each answering
success. The answer used to be `NETWORK_FAILURE, lifetime 30`. That answer told a
client nothing about its mapping. The protocol is whole now, and the carrier's
assigned port travels with the answer.

## The withdrawn inference

The previous record left a suspicion that a freed slot leaves its `tuple-<R>` file
behind, and named it a hazard for a front that reads the file. That is withdrawn.
The file matched the live mapping exactly, `59351` in the file and `59351` in the
answer, and the publisher removes a file with its mapping in six places. Its own
comment says why: a file that outlives its mapping answers a later mapping with a
dead port. What looked like a stale file was a live file whose slot L had already
deleted.

## What remains for this task

The slot admits an external SYN from a peer the line has poked, and it reports its
tuple to the client that asked. The handshake itself needs two things this rig has
not supplied. One is a service on the client's own port, because the granted slot
delivers to the client that asked for it and this machine runs no reachable
service. The other is a return path down the DS-Lite line for that client's
replies, which the two consoles have and this host does not.

Both are properties of a deployment rather than of the daemon, which is where the
recipe takes over: the front-door deployment chooses the service host and gives it
the egress rule, or the daemon gains the rewrite that makes the rule unnecessary.