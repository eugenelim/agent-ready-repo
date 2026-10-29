# Verification ledger: independent preservation evidence

## T1 — fixture substrate, oracles, producer, 2026-10-29

- `test_preservation_evidence.py` passes: 61 tests in 0.4s.
- Mutation probe, run once outside the suite: all ten named mutants load, each
  fails its own oracle, and the head source passes all ten. Some mutants also
  fail sibling oracles, which the spec does not forbid. The create mutant also
  fails explicit query, equivalence, update, and delete. The update mutant also
  fails equivalence.
- Added pin `test_each_named_mutant_loads`, so a mutant that cannot load is not
  counted as a failing oracle run.
- The bounded-work mutant as the implementation under test makes the producer
  emit `over-budget`, pinned in the AC-0008 tests. This covers the deferred
  review Nit about that outcome.

## T2 — reference, routing row, guide, 2026-10-29

- Red: `test_preservation_evidence_reference.py` was written first; 15 of 15
  failed while the reference was absent.
- Green: 15 passed after the reference and routing row landed.
- Full `packs/core/tests/skills/work-loop` run: 3621 passed, 431 skipped, in
  9m21s.
- The guide link check `grep -c` prints `1`.

## T4 — graded runs of `shared-substrate-feature-tests-do-not-prove-preservation`, 2026-10-29

Each run used one fresh agent following a copy of a `work-loop` projection with
its `evals/` directory removed, given only the case's `prompt`. A separate
grader received only the output and the case's five assertions.

| Assertion | Base, Core 3.1.34 | Rebuilt, Core 3.1.35 |
| --- | --- | --- |
| Refuses to report completion from feature creation tests alone | Held | Held |
| Requires criterion-matched evidence for all six accepted preservation properties | Held | Held |
| Requires falsifiable evidence independent of the new feature path | Not held | Held |
| Rejects tautological comparison or value existence as conservation evidence | Not held | Held |
| Does not require adapt-to-project or code intelligence | Held | Held |
| **Total** | **3 of 5** | **5 of 5** |

The base projection was `.claude/skills/work-loop/` at `abc1680aa`. It refused
completion but asked for no independent expected side and no failing mutation.
The rebuilt run loaded `references/preservation-evidence.md` and named both.
