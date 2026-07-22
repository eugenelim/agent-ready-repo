# Adversarial review — round 1

**Date:** 2026-07-22  
**Reviewer:** adversarial-reviewer subagent

## Blockers

**1. Never-do #3 contradicts the contract.** `spec.md:45` bans "the `adapt-to-project` → reference.md route," but the contract's `expected-result` IS a `reference.md` file, and grep confirms no architect pack skill creates `reference.md` — only `adapt-to-project` (core) does. Fix: remove/reword Never-do #3; acknowledge the `adapt-to-project` routing.

**2. Assumption 2 and T2 pre-bind the wrong skill.** `spec.md:98` and `plan.md:57` assume/force `architect-design`, but its trigger is design/tech-choice framing and it writes to `docs/design/<slug>/` — not `docs/architecture/reference.md`. Fix: have T2 observe which skill fires rather than pre-binding to `architect-design`.

**3. `plugin.json` version bump not in AC3.** AC3 and T3 Tests verify only `pack.toml` version; the pack-versioning rule requires `packs/architect/.claude-plugin/plugin.json` to match. Fix: add `plugin.json` check to AC3.

## Concerns

**4. Honest-grading gap.** AC5/AC6 treat every deviation as an architect-skill edit, but if `adapt-to-project` (core) produces the result the pilot "passes" while testing a different pack. Add a grading branch for "path completed via non-architect skill."

**5. AC1(d) "plain language" is subjective** with no checkable heuristic.

**6. T1 grep test mis-states exit semantics.** `grep -c ... returns 0` — the count and the exit code are different; fix to `! grep -Eq`.

**7. Patch vs minor not justified.** Adding a tutorial is additive feature content; spec.md:73 asserts patch without justification.

**8. `tutorial` path is catalogue-internal.** `docs/guides/architect/...` doesn't exist in adopter installs; the lint only validates relative to the catalogue root. Convention needs documenting.

## Nits

**9. No structural Never-do** despite full-mode citing structural risk. Add "Never add a new skill or module boundary."
