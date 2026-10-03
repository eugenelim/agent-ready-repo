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
