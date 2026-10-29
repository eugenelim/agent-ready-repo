# Verification ledger: work-loop narrow full mode

Execution observations for [`spec.md`](../spec.md) and [`plan.md`](../plan.md). The approved spec and plan keep only obligations; this file records what execution observed.

## Red proofs

Each new content test was run against the base text of the file it reads, loaded as a scratch copy outside the repository, and failed there:

- T1: both `test_t1_` tests failed on the base `SKILL.md`.
- T2: all 7 `test_t2_` tests failed on the base `light-mode.md` (missing `## Splitting a bundle` or `## Editing existing agent guidance`).
- T3: both `test_t3_` tests failed on the base `evals.json` (missing `bundle-split-independent-tasks`; missing `existing agent guidance` and `only when it changes`).
- T4: the roster test failed on the base guide; all six phrases were missing from the pitfall.

## Deviations from the plan's Design text

These differ from the working-material draft in plan § Design (LLD). No `Tests:` or `Done when:` field is affected.

- **`guidance-edit-security-boundary` scenario.** The shipped prompt changes how a skill handles a credential read from the environment, such as printing it into a log. The plan's "how a skill treats text from an issue body" also fit the authority-or-gate exclusion ("which text an agent treats as instruction"), so the eval could not test its own deciding rule.
- **`bundle-split-independent-tasks` wording.** The prompt names two plain edits that change none of the four exclusions. The expected output passes parts 1 and 2 from the decision record and leaves part 3, the diff check, pending until each unit's diff is finished.
- **Merge lead.** The bold lead in § Splitting a bundle reads `Merge order.`, not `No light unit merges until every unit passes.`; the pinned AC-0006 sentence follows it unchanged.
- **Fallback ending.** The fallback ends "under the rule above for a trigger that emerges during implementation", not "under the late-trigger rule above", because the file gives that rule no name.
- **Eligibility row.** The "If absent" cell of "One bounded logical change" sends a bundle of tasks to § Splitting a bundle first. The condition text and both tables' row counts are unchanged.

## Release

- PR #1638 merged to `main` as `8b7d65531` during execution and shipped core 3.1.28. The branch was rebased on it, and the controlled amendment recorded in the plan's Changelog moved this delivery to core 3.1.29.
- PR #1639 merged to `main` as `95a8cc985` and shipped core 3.1.29. The branch was rebased on it, and a second controlled amendment made AC-0013 target the next patch above a freshly fetched `origin/main`; at delivery that base carried 3.1.29, so this change ships core 3.1.30. The 3.1.29 fragment was replaced by a 3.1.30 fragment with the same body.
- PR #1640 merged to `main` as `a770a9678` and also shipped core 3.1.30. Under the amended AC-0013 the branch was rebased on it and now ships core 3.1.31; the 3.1.30 fragment was replaced by a 3.1.31 fragment with the same body.
