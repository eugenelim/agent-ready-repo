## Blockers

**1. Reference-style Markdown links bypass the new guard.** `tools/lint-guides-no-repo-only-refs.py:50`. The scanner only matches inline links. Fix: add reference-link definition target scanning and a failing test for a forbidden reference-style target.

## Concerns

**2. Spec index count drifted after adding AC11/T5.** `docs/specs/README.md:22`. Fix: update the row from 10 ACs / 4 tasks to 11 ACs / 5 tasks.

**3. Plan still names the old CI invocation spelling.** `docs/specs/governance-guides-cleanup/plan.md:108`. Fix: update the plan's CI invocation spelling from `python` to `python3`.
