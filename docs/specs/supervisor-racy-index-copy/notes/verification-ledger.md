# Verification ledger — supervisor-racy-index-copy

The approved `spec.md` and `plan.md` hold the obligations; this file records the runs that met them.

## Criteria

| Criterion | Test | Run | Result |
| --- | --- | --- | --- |
| AC-0001 | `packs/core/tests/skills/work-loop/test_supervisor_git.py::test_a_same_size_rewrite_in_the_index_second_is_seen_by_the_seeded_scan` | Supervisor run `run-1db42959521d6730`, 2026-11-07, under `WORK_SUPERVISOR_INTEGRATION=1` | Pass: git suite 57 passed, commit suite 21 passed. Without the fix the test fails 3 of 3 runs, and with the `os.utime` call disabled it fails 5 of 5. |

## Closeout

- Core is 4.0.24, one patch above freshly fetched `origin/main` (4.0.23); `tools/check-core-release.py --base origin/main` reports the release consistent.
- `agentbundle catalogue self-host --root . --check` is clean after the supervisor's `regenerate` step.
- Reviews: security-reviewer clean; adversarial-reviewer closed an unclosed plan comment and a docstring residual-risk gap in T2, leaving one nit that the closeout merge with `origin/main` settles.
