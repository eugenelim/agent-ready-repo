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

## Design first chosen, then cut the same day

**Superseded — read this before the rest of the section.** The design below was
chosen, then cut before approval on owner instruction to apply the razor to the
whole contract. It is kept because the decision trail matters, not because it
describes what ships. What ships is in *What was actually chosen* below.

**Candidate 1 — one canonical rule, site-local pointer roles.**

One authoring source defines the post-approval boundary. Every enumerated
operational site carries a locally verifiable pointer to that source or to the
ledger procedure. No vocabulary-based restatement detector, and no assertion
that one site can satisfy from another site's text.

Pinned semantic prose falls from twelve sentences across eight files to **four
sentences in four files**: the canonical convention statement, and the three
statements that are already correct and stay — the public how-to's immutability
sentence, `pre-execute-review.md`'s permitted-edit-set rule, and
`state-schema.md`'s mechanism description. Everything else becomes a pointer
assertion or a destination-absence assertion, plus one clean sentinel token.

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

### Two corrections to the design as first proposed

The adviser's proposal was adopted with two changes, both made before the
contract was amended.

**It would have dropped two killing mutations.** It listed the public how-to
and `references/pre-execute-review.md` as pointer sites. Round 2 established
that `pre-execute-review.md:205-215` carries no cross-reference and
independently states the permitted post-approval edit set, so it is
rule-bearing; the how-to likewise retains its own immutability sentence.
Treating either as a pure pointer would delete correct guidance and lose the
mutation that catches its reversion. Both keep a guarded statement *and* a
pointer.

**It called for synthetic role markers everywhere; measurement says they are
mostly unnecessary.** Six guarded sites are unique real Markdown headings and
the template's `Done when:` instruction occurs exactly once, so seven of eleven
need no marker at all. For the remainder the fix is assertion shape, not marked
prose: region extraction only ever existed to stop one site satisfying
another's claim, and asserting that **no non-canonical destination appears
anywhere in the roster** achieves that with no anchor, immune to re-wrapping,
because a link target is not prose. Measured on entry: `notes/*.md` across the
eight roster files resolves to exactly one value, `notes/verification-ledger.md`.

No markers are therefore added to shipped human-facing guidance.

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

## What was actually chosen

Measurement against the merge-base `1134701ba` refused the restructuring. Across
both vocabularies of the false premise, only three surfaces ever carried it — the
convention seed (3 literal licence hits plus 16 "change as you learn"/Living),
the plan template (1), and the public explanation (1). The lifecycle reference,
`pre-execute-review.md`, `state-schema.md`, the public how-to and
`work-loop/SKILL.md` carried it in **neither**. All three corrections shipped in
T1-T2, and no surface carries it today.

The three open defects are therefore all guard-side, and all three are repairable
inside `tests/roster/test_verification_ledger_contract.py` with no prose,
projection or release change: V1's by-path region concatenation, V2's whole-file
fallback for the template, and V5's unguarded template `## Changelog`. V3's
over-broad `RESTATED_RULE_MARKERS` is removed in the same pass.

So the amendment reduces to **one guard-repair task**. Restructuring seven shipped
files to make the test easier to write was content shaped for the test rather than
the reader, which is the cost the corrections section below had already flagged
and which measurement then showed was not buying anything.

Dropping `RESTATED_RULE_MARKERS` also drops the guard's claim that
`work-loop/SKILL.md` is free of an independent rule. AC2 now claims only a
resolvable pointer there, because that is what stays mechanically checkable.

Round 4 sustained a Blocker against the first attempt at this cut: it changed AC2
alone and left the pointer mandate standing in ten other clauses plus a
`Depends on:` edge to a deleted task, which would have left AC3 undischargeable —
the same failure that authorised the redesign. The reconciled version is
`894c94206`.

## Residual risk accepted

Two risks remain, and neither is the marker cost, which the corrections above
removed.

**One prose sentence per governed clause is still matched as prose**, and the
guard is still a prose-matching test — the reduction removed the restructuring,
not that property.

**A lapsed risk, kept for the record.** It cannot notice a site that drops its
pointer while a sibling pointer survives in the same file. That risk lapsed
with the cut: no task creates a pointer role, so nothing depends on
absence-scanning.

**Four prose sentences are still matched as prose.** The owner statement and
the three retained statements are pinned by content, so re-wording any of them
still requires editing the guard. That is the irreducible core: something must
pin the sentence that carries the rule. The reduction from twelve to four is
the gain, not the elimination of the class.
