# The last receipt's blocker, and the two ways the doctrine offers out of it

**Date:** 2026-09-27. **What this note is for:** `plan/0012#record` is the only
unreceipted task in the repository, and its verify is
`host-lifecycle software --check .` re-running the whole gate. That gate is red on
one item, the remap phase, which is older than this milestone and belongs to
records this milestone did not author. This note lays out what the checkpoint found
and the dispositions the methodology allows, so the decision is one line rather
than a rereading.

## What the remap phase reports

Eight tell-shaped tokens, in three records. The count stood at five before this
milestone's own record arrived, and the three it added are that record's transcript
lines, each carrying `epoch`, which is the token this lane reads as a tell wherever
it appears. That resolves the line in the harvest whose flagged token puzzled L:
the word `epoch` is the tell, not the state directory named beside it.

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

Boxing a frozen record's citation is the methodology's default, so it needs nobody's
permission and L can do it. Declaring a token is the operator's, because the
vocabulary is theirs and a `DP-T` declaration needs a URL for the brief it answers
to. The two are not the same decision wearing two hats: boxing an irreducible
citation is an edit to a record, and declaring a token tells the lane that a
legitimate phrase looks like a tell.

Neither touches the milestone's status line, its record, or any task receipt. Until
the eight are disposed, `#record`'s verify re-runs the gate and finds the same red,
so the milestone's last receipt cannot be written. Nothing else in the repository is
waiting on it: a sweep of all seven milestones this turn found `#record` as the only
task without a receipt.

## How it closed

**Later the same day.** The lane's own validation answers the question this note
left open, and it forecloses the declaration for most of the five:
`validate_lexicon_entry` rejects any declared phrase that carries a position noun as
a word, which puts `section` and `epoch` beyond the lexicon's reach, and it rejects
a phrase that is itself a flag. Four of the five were therefore beyond a
declaration, and boxing is the escape the doctrine names for a frozen record
flagged by a later grammar bump.

The five, boxed where they stand:

- `call/0037`'s two lines, each showing a shape the rule forbids (the second inside
  its bullet).
- The harvest record's file list beside the fixed path.
- The harvest record's kernel version, the one the conntrack code documents.
- The brief's clause name for the role set an action requires.

A box hides its own lines and leaves the rest of the file linted, which was
measured on a scratch document: an unboxed tell beside a boxed one still reported.
With the five boxed, `host-lifecycle remap --check .` reports 0 undispositioned
tells and the gate's remap phase rechecks green.

The gate's one remaining item is the component's pin. The worktree sits at the
front-door work; the record pins the tagged previous release. That line moves with
the release, whose canonical hash comes from the recorded toolchain image, which the
lane runs and this host cannot (`call/0032`). `#record` is therefore a recorded
deferral to the release, and it draws its done when the pin names the tagged bytes.