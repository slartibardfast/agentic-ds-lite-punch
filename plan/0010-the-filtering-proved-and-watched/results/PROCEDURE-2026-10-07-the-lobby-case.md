# Procedure: the lobby case on a real console

Date: 2026-10-07. For `plan/0010`'s future work, and the one case its own run leaves out.
[call/0030](../../call/0030-a-mapping-ends-with-its-device.md) is the claim this measures: a
client-requested mapping ends when its client leaves the LAN, and never because it went quiet.

Operator: about three minutes of a console sitting in a lobby, plus a minute for the second half. The
daemon does the rest, and the log carries the evidence.

## What has to be true first

- The console is on the LAN and is named in the allowlist file `ALLOWLIST` points at.
- `KEEPALIVE=1` and `UPNP=1` are set, so the arm holds and the facade grants.
- The console holds a mapping it asked for, which its own game start produces.

## The quiet half

1. Read the console's mapping and the tuple, and keep both:

   ```sh
   nft list table ip dslp
   cat /run/ds-lite-punch/tuple
   ```

2. Note the log's position: `logread | grep ds-lite-punch | tail -5`.
3. Leave the console in a lobby or a paused game for at least three minutes. A lobby, a paused game
   and a sleeping screen each present as silence, which is the state the mapping exists to survive.
4. Read the log again across the window:

   ```sh
   logread | grep ds-lite-punch | grep -E "hold|observe|tuple|gc|release"
   ```

   The `hold` event names the devices and confirms the ruleset is in force. The mapping's element
   stays in the table, and the tuple does not move.

## The present half, which is the other side of the claim

5. Take the console off the LAN, by its own standby or by disconnecting it, and wait about two GC
   ticks.
6. Read the log again. The mapping ends and its slot returns to the pool, because the device that
   asked is gone. A configured static mapping stays, since the operator's configuration is not a
   client's request.

## What falsifies the claim

A release during the quiet window falsifies the first half: the log then carries the release while the
console sat in the lobby. A mapping that outlives the console's departure falsifies the second.

## Where the evidence goes

Paste the log excerpts across both windows, the ruleset's element before and after, and the tuple
value, into a `RESULTS-<date>-the-lobby-case.md` in this room. The receipts of `plan/0010` then carry
the case it left open.