# Amendment 0001 — owner authority

## Decision

The scope owner (`eugenelim`) authorized one controlled contract amendment to
`plan.md` on 2026-09-17, in session, with the single word "Amend" in reply to a
surfaced blocker and its two priced options. The owner chose the amendment over
accepting the defect as proportionate.

## What the owner was shown before deciding

Two defects in T3's `Done when`, both verified against the tree rather than
taken from the implementer's report:

1. **The clause cannot be discharged as written.** It requires that "no
   statement in the tree still asserts that `check --phase implement` guards the
   `wave-complete` transition". `docs/specs/loop-infrastructure-phase-1/plan.md`
   asserts that coupling at lines 545, 627, 653, 823, 1084 and 1356. Its spec is
   `Shipped`, its plan is `Done`, and this spec's `Constrained by` field names it
   "Shipped and frozen". The clause therefore cannot become true without editing
   a frozen artifact this spec forbids editing.
2. **Its enumeration is short.** The clause names three live surfaces; five
   assert the coupling. The two it omits are `loop-engine.py:1012`, the
   guard-table entry, and a docstring at `test_loop_engine.py:1615`. The
   guard-table entry is already covered — another clause of the same task
   requires retargeting it — so the operative omission is the test docstring,
   which nothing else in T3 reaches. Both files are already in T3's `Touches`,
   so the amendment implicates no new file.

The evidence for both is recorded in § 8.2 of
[`verification-ledger.md`](verification-ledger.md), which is this amendment's
`--reason-ref`.

## Scope of the authority

This authority covers exactly one change: narrowing T3's `Done when` coupling
clause to the live, editable surfaces and correcting its enumeration from three
to five. It does not authorize any other edit to `spec.md` or `plan.md`, does
not reopen either settled owner decision recorded in the spec (the
empty-partition verdict and the absent-container exemption), and does not widen
the accepted outcome.

T1 is complete and its section is immutable under the amendment rules. The
cohort records no completed task id — per-task completion is not implemented in
this engine phase — so this amendment carries no `--completed-evidence-ref`, and
T1's evidence is the commit that landed its ledger sections.

## Why the amendment rather than accepting the defect

A `Done when` clause is a verification obligation and contract. Leaving a
contract clause that is untrue, and knowingly discharging it against a narrower
set than it names, is the defect class ten pre-EXECUTE review rounds on this
spec were spent removing. Accepting it here would reintroduce it at the last
moment and in the contract itself.
