# Comments are one line, and technical

- Status: accepted
- Scope: the source of this component: how much a comment may say, and what it
  may say it about
- Date: 2026-09-23

## Context and Problem Statement

The component's source carried 3,474 comment lines in 1,208 runs, and 753 of
those runs spanned more than one line. The longest ran to 36 lines. They held
design essays, the provenance of decisions, measurement narratives, and
citations of the pre-adoption brief's item codes and of specification clauses.

Two costs came with them. A reader looking at a function met a wall of prose
before the code, and the parts that stated a fact the code depends on sat in the
same paragraph as the parts that recorded how the fact was learned, so neither
could be found quickly. And the citations were tell-shaped: the naming audit
reported 86 findings over the component, every one a line citing a clause number
(`section 8.2`, `26.19`, `6.12`) or a brief item code (`I1`, `R5`, `B4`).

## Decision

A comment run is one line, and it states one technical fact about the code beside
it. A run of two or more comment lines is a defect, and `tools/comment-lint.py`
in the component's lane fails on one.

- A fact the code depends on is what survives: an invariant, a protocol
  requirement, a platform quirk, the meaning of a constant. A measured number
  belongs in a line when the code's behaviour turns on it, with no date and no
  story.
- Provenance, dates, measurement narratives, design rationale and citations of
  the brief's item codes do not. The brief keeps the design, `call/` keeps the
  decisions, the results files keep the measurements, and the harvest record of
  this date keeps what lived only in a comment.
- A specification is named (`RFC 6887`), and its clause numbers are not
  (`section 8.2`). A brief item code resolves to the rule it names.
- A module header and an item's doc comment are each one line. rustdoc is not an
  audience for this component, which is a binary.
- Commented-out code is deleted. The tree held none when this was decided.

## Consequences

The collapse removed about 2,950 comment lines across the component and the 86
findings with them, and the facts that had no other home went into
`plan/0004-ds-lite-punch/RESULTS-2026-09-23-comment-harvest.md` first. The
pre-collapse text of every file stays in the git history of the commit that
removed it.

The rule costs a judgement at each edit: a fact worth keeping has to be stated in
one line. That is the point of it.

Comments reach neither the binary nor the man page, so this pass moves no
artifact. The one corpus correction the harvest paid for, the two state
directories, did move the embedded help text, and that shipped as its own patch
release.