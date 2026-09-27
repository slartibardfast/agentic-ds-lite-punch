# The last receipt's blocker, and the two ways the doctrine offers out of it

**Date:** 2026-09-27. **What this note is for:** `plan/0012#record` is the only
unreceipted task in the repository, and its verify is
`host-lifecycle software --check .` re-running the whole gate. That gate is red on
one item, the remap phase, which is older than this milestone and belongs to
records this milestone did not author. This note lays out what the checkpoint found
and the dispositions the methodology allows, so the decision is one line rather
than a rereading.

## What the remap phase reports

Five tell-shaped tokens, in two records:

```host-lint:ignore
call/0037-comments-are-one-line-and-technical.md:20: warning: (`section 8.2`, `26.19`, `6.12`) or a brief item code (`I1`, `R5`, `B4`). (section)
call/0037-comments-are-one-line-and-technical.md:37: warning: (`section 8.2`). A brief item code resolves to the rule it names. (section)
plan/0004-ds-lite-punch/RESULTS-2026-09-23-comment-harvest.md:33: warning: Confirmed on the router on 2026-09-23: `/tmp/dslp/` held `epoch` (11 bytes, (epoch)
plan/0004-ds-lite-punch/RESULTS-2026-09-23-comment-harvest.md:186: warning: - The conntrack line layout is documented in the code for the 6.12 kernel, token (6.12)
plan/0004-ds-lite-punch/RESULTS-2026-09-23-comment-harvest.md:624: warning: - The role set an action requires with the section 3.1 name (dp.rs:187), DP-T:141. (section)
```

The first two are `call/0037` quoting, on purpose, the shapes its rule catches.
The last three are the harvest record: a kernel version, a section reference, and a
line whose flagged token is `epoch`. The `epoch` one is the odd one out: the lane
flags the token in a line about the state directory, and why it reads as a tell is
not something L worked out. That one wants the lane's own explanation before any
disposition, because a declaration made blind is a guess.

## Disposition A: declare the tokens

The methodology's escape for legitimate domain vocabulary is a declaration:
`.host-remap` for a sanctioned token or phrase, or host-lint's `LEXICON` for a
provenance-checked one. Two rules bite here.

The entry must be the full contextual phrase, never the bare token: the tool
refuses a master key, and refuses a phrase that is itself a tell. So the kernel
version is declared as a phrase naming it as a kernel version, and the item code as
a phrase naming the rule it stands for.

A tracker reference needs its backing URL. `DP-T:141` is an item code from the
DeviceProtection:1 brief, so its declaration needs the URL of the record it
answers to, and L has no URL for that brief in the repository to quote.

This disposition leaves both records unrewritten, which is why it is the natural
one for a dated results record.

## Disposition B: box the citations

The other escape is for a document that must reproduce a tell verbatim: wrap it in
a fenced block tagged `host-lint:ignore`, which the scan skips while the rest of
the file stays linted. It applies to the two `call/0037` lines, both of which quote
the shapes as the subject of the rule and read badly when reworded, since a rule
about shapes that cannot show one is a rule about nothing.

Boxing an inline citation inside a sentence means restructuring the sentence into a
block, so it edits a record rather than declaring a token. For a document that
quotes shapes as its subject, that is the honest form.

## What each choice costs, and what waits

Both leave the milestone's status line, its record, and every task receipt as they
stand. Neither is L's to make: the methodology puts the vocabulary with the
operator, and the same holds for the URL that a `DP-T` declaration needs.

Until one is chosen, `#record`'s verify re-runs the gate and finds the same red, so
the milestone's last receipt cannot be written. Nothing else in the repository is
waiting on it: a sweep of all seven milestones this turn found `#record` as the only
task without a receipt.