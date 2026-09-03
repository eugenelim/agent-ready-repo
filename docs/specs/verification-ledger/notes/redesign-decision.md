# Redesign decision: reanchor the contract on pointer roles

## Owner authorization

The scope owner directed this amendment on 2026-09-03, in session, in these
terms: *"do the redesign based on the findings and reanchor the contract to
something that works"*, after being shown the round-5 evidence below and the
conclusion that AC3 was not tickable. This note is the stable authority and
reason reference for the `contract-amendment` engine transition.

Model judgement did not invoke this. `delivery-contract-lifecycle.md` § *Controlled
full-mode contract amendment* requires explicit scope-owner authority, and
"session end, retry cap, stasis, or model judgment never invokes this
transition".

## Why the contract is being reanchored rather than patched again

Five independent review rounds each found a real, distinct defect in
`tests/roster/test_verification_ledger_contract.py`, and each time it had
already been declared verified. Rounds 4 and 5 each also *introduced* defects
while fixing others. The full measured record is in
[`verification-ledger.md`](verification-ledger.md).

The failure is structural, not a run of bad luck. The guard asks flexible prose
to serve as both a distributed policy representation and a mechanically closed
set. Every repair therefore moved along one of two axes, and both have now
failed twice:

- **Widen a region** and one clause becomes satisfiable from another site —
  rounds 2 and 4, then V1 and V2.
- **Widen a phrase marker** and harmless prose gets rejected — round 1's
  over-broad probe, round 3, then V3.

The module already concedes the limit it cannot escape: prose cannot be proved
free of an arbitrary permission
(`tests/roster/test_verification_ledger_contract.py:39-43`).

The delivery's own spec had the right instinct — "Keep the convention as
mutability-rule owner; the template and lifecycle material point to it rather
than creating competing definitions" (`spec.md:36`). `plan.md:44` then required
six surfaces to restate the boundary "in their own operational terms", which is
what produced eight brittle regions. The amendment resolves that internal
conflict in favour of the spec's instinct.

## Two contract defects being repaired

1. **AC3's closed set is not closed.** The plan template's `## Changelog` rule,
   corrected by this delivery, is unguarded: reverting it to the `origin/main`
   wording leaves the suite at `12 passed`.

2. **AC3's final sentence is overclaimed.** "The set is closed by enumeration:
   a seventh surface stating the boundary is a defect in this criterion, not an
   omission the guard tolerates" admits no qualification, yet accepted decision
   records state the same boundary — `docs/rfc/0099-…:501`,
   `docs/adr/0099-…:52`, `docs/rfc/0096-…:365`, `docs/adr/0061-…:12`. Editing
   RFC-0099 to licence in-place edits leaves the guard green.

   The related claim that the **public how-to** also contradicts the closed set
   was **refuted**: AC3's next sentence gives the how-to its own killing
   mutation explicitly, so it is accounted for rather than omitted. The RFCs and
   ADRs receive no equivalent qualification, which is why they falsify the
   sentence and the how-to does not.

## Chosen design

**Candidate 1 — one canonical rule, site-local pointer roles.**

One authoring source defines the post-approval boundary. Every enumerated
operational site carries a locally verifiable pointer to that source or to the
ledger procedure, under a unique role identity with bounded start/end markers.
Each role is asserted separately against its own target. No concatenation by
path, no whole-file fallback, and no vocabulary-based restatement detector.
`references/state-schema.md` stays unedited and keeps its own assertion.

Pinned semantic prose falls from twelve sentences across eight files to **two
sentences in two files** — the canonical convention statement and the unchanged
state-schema mechanism sentence — plus ten structured pointer identities and one
clean sentinel token.

Each round-5 finding is closed by construction rather than patched: V1 and V2 by
per-role targets, V3 by deleting `RESTATED_RULE_MARKERS`, V5 by giving
`## Changelog` its own role, V4 by pinning the literal sentinel at its
classification site.

### What this gives up, stated plainly

Global contradiction detection, and self-contained local restatements. The
guard will no longer claim that arbitrary prose anywhere cannot contradict the
boundary. It will prove a smaller invariant precisely: one canonical
definition, a named operational pointer roster, one mechanism statement, and the
real hash behaviour. Accepted RFCs, ADRs and other decision records are
governing evidence outside the roster.

It also cannot prove a reader followed or understood a correct pointer.

### Rejected alternatives

- **A structured policy record** (TOML naming the sealed artifacts, permitted
  bookkeeping, destination and amendment route). Rejected: the engine surfaces
  that would consume it are forbidden to change, so the record would be
  descriptive rather than authoritative — a new primitive with no runtime
  enforcement, against the repository's cut-before-adding order
  (`AGENTS.md` § *Coding conventions*).
- **Keep the restatements, bound each in its own block.** Rejected: materially
  better than the current guard, but it retains the distributed-prose topology
  that produced five review rounds.

## Residual risk accepted

Pointer role markers are machinery added to human-facing shipped guidance so a
test can locate a site. That is content shaped partly for the test rather than
solely for the reader, and it is a real cost. It is accepted because the
alternative — matching prose sentences — has now failed five times, and because
a role marker carries no rule and cannot drift from one.
