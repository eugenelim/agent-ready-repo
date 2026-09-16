# Verification ledger — design-output-addressing

## Reviewer gate, 2026-09-16

`reviewers-clean` was fired on the owner's explicit instruction, **not** on a
clean sentinel. No adversarial round returned one. Recording the basis so a
later reader does not mistake the transition for sentinel-backed evidence.

**What the gate rests on.** Eight adversarial rounds, finding counts
21 → 15 → 14 → 8 → 2 → 4 → 3 → 1. Every round's findings were applied. The final
round returned one concern, no blockers, and verified the three substantive
repairs before it: T1's clause enumeration maps one-to-one onto the spec's eight
`The shared containment module states` criteria with no clause asserted that no
criterion carries; T9's three construction tests are differential; and T2's
account of both `type:` literals is true of the tree. That concern is patched,
and a companion sweep over every fact the last three commits changed found one
further instance the round had not reached, also patched.

**What it does not rest on.** No reviewer has seen the two commits that close
round eight. The structural properties were confirmed at round four and
re-confirmed since — every open criterion has an implementing task, and every
`Done when` is reachable from its declared dependency closure — but that
confirmation predates those commits.

**Known residual risk.** The recurring defect through rounds four to eight was a
companion statement left behind by an edit to the thing it described: a count, a
completion condition, or a restatement of a proof standard. It recurred five
times, including inside the fix intended to retire it. Both traversal
instruments were run before this gate; the class is diagnosed, not proven
absent. A reader finding another instance should treat it as expected residue of
that class rather than as a new defect class.

**Owner decision.** The owner approved the spec and plan and instructed
implementation to begin, having been shown the trend, the absent sentinel, and
the option to run a ninth round.

## Execution observation — T6, 2026-09-16

`guides/experience-design/how-to/design-each-screen.md:374` carries the rung
`authored; information-architecture SKILL.md declares the record but not its
path`. T2 gives that skill a declared path, at which point the rung's second
clause is false. No task owns rewriting it: T7's rung work is scoped to
`establish-design-intent.md`, and the guide-agreement test asserts that an
`artifact_location` resolves to a declared path, not that its rung is accurate.

This is the companion-staleness class that produced the majority of findings in
review rounds four through eight, now appearing in implementation: an edit to a
thing leaves a statement about that thing behind.

**Disposition.** Carried into T7 as a bundled fix under the carve-out's Tier 3 —
same area (a guide rung), same concern (a guide claim matching its skill),
visibly smaller than the task, and mechanical. It is not a design call. T7
depends on T2, so the declaration exists by then. Recorded here rather than
amending the approved plan for a one-line correction, and listed under
`Bundled fixes:` when T7 is committed.
