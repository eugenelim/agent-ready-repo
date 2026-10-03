# Verification ledger: visual-handoff-golden-path

Execution observations recorded after the plan baseline was pinned on
2026-10-03. The approved spec and plan are unchanged.

## Observations

- **T1 — fixture layout files are gitignored.** The repository ignores every
  `agentbundle-layout.toml` (`.gitignore`), so the five fixture layout files
  were absent from the first commit and the roster test would have failed in CI.
  Repaired by one negation line, `!tests/roster/fixtures/**/agentbundle-layout.toml`,
  following the existing `!packs/**/evals/files/agentbundle-layout.toml`
  precedent. `.gitignore` is outside every task's `Touches`; the change is
  required for the test to run from a clean checkout and alters nothing else.
  Verified by running the module from a fresh clone of the branch.
- **T1–T5 — implemented by the controller.** The owner directed controller
  implementation on 2026-10-03; each task's dispatch receipt records
  `human-directed`.
- **T4 — carrier floor.** Re-measured after every delivery file existed: 16
  non-Markdown carriers (13 before, plus the new roster module and its two
  run-record fixtures).
- **Manual verification — eval entry point.** On 2026-10-03 the in-harness
  entry point prepared a workspace for each golden case:
  `agentbundle pack evals run --pack frontend-engineering --mode in-harness --check behavior --prepare-workspace frontend-engineering/<case>`
  for `visual-golden-path-confirmed-values`,
  `visual-golden-path-unconfirmed-target` and
  `visual-golden-path-refusal-preserved`. Each exited 0 with an empty
  workspace, as a case declaring no `files` should. No model run was performed
  and no case was graded: a graded run needs an agent to execute the skill and
  attest the assertions, which this session did not do. Workspace preparation
  is not a graded result.
- **Post-gates review round 1.** Eight sustained findings repaired: each
  AC-0016 negative now breaks exactly one rule; the AC-0013 check reads the
  markup's declarations and role-bound properties too; the missing-`[design]`
  named skip and the slug length bound are parsed from the installed skill;
  AC-0007's test proves the refusal fixture resolves under a conforming slug;
  the fixture taxonomies carry a Proving set; the `unresolved-domain` taxonomy
  no longer claims an incumbent; the golden cases also exclude the upper-case
  fallback placeholder.
