# T1 EXECUTE adversarial review — round 1

**Reviewer:** adversarial-reviewer subagent
**Date:** 2026-05-26
**Scope:** T1 implementation diff (contract bump v0.6→v0.7 + lint admission of `metadata.auth` + frontmatter pre-declaration on six existing credentialed skill sources).

## Findings

**1. Subprocess test sets `PATH=/usr/bin:/bin`, which is macOS-only-coincidentally-sufficient.** `packages/agentbundle/tests/unit/test_lint_agent_artifacts_metadata_auth.py:42`. Fix: inherit parent's `PATH` so the test is portable across CI shapes (NixOS / Alpine / custom images where `git` lives outside `/usr/bin`).

**2. `credentialed: false` + `auth: <id>` combination has no test coverage.** `packages/agentbundle/tests/unit/test_lint_agent_artifacts_metadata_auth.py:122`. Fix: add a test pinning current behaviour (lint admits silently — AC26 is silent on this combination).

**3. Plan changelog ordering mixes chronological + semantic.** `docs/specs/credential-broker-contract/plan.md:422`. Fix: group all four 2026-05-26 revisions above the Initial Draft anchor; add a one-line "most-recent-first" note.

## Resolution

All three findings addressed in the same PR. Fixes:

1. `_run_lint` now uses `env={**os.environ, "LINT_ROOT": str(root)}`.
2. New test `test_credentialed_false_with_auth_declared_clean` pins the combination.
3. Plan changelog reordered with anchor note added.

Other items noted by reviewer but not actioned:
- Filename `test_contract_v07.py` is pinned by plan T1 Tests; renaming to a version-agnostic name would diverge from plan.
- `setUp` vs `setUpClass` — micro-optimisation; not a correctness concern.

## Round 2 — Clean

Round-2 adversarial review verified all three fixes; no new findings.
Verdict: **Clean — ready to commit.**
