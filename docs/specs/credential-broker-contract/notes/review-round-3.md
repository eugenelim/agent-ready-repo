# Round 3 adversarial review — credential-broker-contract spec + plan

**Reviewer:** adversarial-reviewer (subagent)
**Date:** 2026-05-26
**Verdict:** Not clean — 3 Blockers, 2 Concerns, 1 Nit.

## Blockers

**1. T10 contradicts AC45 — still names a conformance-suite addition.** `plan.md:277,286`. Round-2 fix B5 explicitly removed it. Fix: drop conformance-suite mention from T10 Tests + Approach.

**2. T15 enumeration omits five test files.** `plan.md:378-389`. Missing `test_keychain_macos_logic.py`, `test_credman_windows_logic.py`, `test_keychain_macos.py`, `test_credman_windows.py`, `test_example_credentialed_skill.py`. Fix: add explicit per-file dispositions for each.

**3. T14 separation-gate contradicts AC34.** `plan.md:355`. Same-PR escape parenthetical re-admits what AC34 forbids. Fix: drop "(or the same PR as...)" clause.

## Concerns

**4. T1 Tests still encode the dropped pack.schema.json work.** `plan.md:85,90`. Phantom `test_pack_schema_metadata_auth.py`. Fix: delete that test bullet; consolidate to `test_lint_agent_artifacts_metadata_auth.py`.

**5. AC34 frames three queries as "two".** `spec.md:184`. Cosmetic carry-over drift. Fix: "two" → "three".

## Nits

**6. `test_pack_schema_metadata_auth.py` filename misleads.** `plan.md:90`. Resolved with C4.
