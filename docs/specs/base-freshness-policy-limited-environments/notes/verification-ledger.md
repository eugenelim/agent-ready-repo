# Verification Ledger: Base Freshness in Policy-Limited Environments

## Session Scope

This ledger records observed evidence for T1 helper behavior in the
`base-freshness` workspace on 2026-09-26. The session edited only the bundled
helper, its pytest module, and this ledger.

## Observed Evidence

| Evidence | Command or source | Observed result | Contract covered |
| --- | --- | --- | --- |
| Targeted helper suite after T1 implementation | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_check_base_freshness.py -q` | Exit 0; `27 passed in 42.25s` | Unavailable `ls-remote`, unavailable fetch, timeout skips, stale-base surface, local-state refusals, and missing-branch surface were covered by the suite. |
| Targeted helper suite after lint-only repair | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_check_base_freshness.py -q` | Exit 0; `27 passed in 67.90s` | Mechanical import and pathlib chmod repairs preserved T1 behavior. |
| Targeted helper suite after post-gates classifier repair | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_check_base_freshness.py -q` | Exit 0; `31 passed in 45.76s` | Malformed URL/protocol diagnostics remain unclassified and surface without raw stderr on both `ls-remote` and fetch paths, while DNS/auth and metadata-denied cases remain covered. |
| Existing real-Git stale-base regression | `test_behind_surfaces` within the targeted helper suite | The suite passed; the case asserts exit 1, `status == "surface"`, and a message containing `behind` and `rebase`. | A proven stale base remains blocking. |
| Policy-limited current checkout before this change | User-provided session output for `.agents/skills/work-loop/scripts/check-base-freshness.py` | Exit 1 with `{"status": "surface", "message": "ls-remote to 'origin' failed — check network/auth", "target": ""}`. | Historical context: the pre-change helper blocked when the environment prevented remote freshness verification. |

## Pending Evidence

| Evidence | Status | Owner note |
| --- | --- | --- |
| Projected helper invocation in this policy-limited checkout after regeneration | Pending | Do not claim the current checkout now returns `status: "skipped"` until the projected helper has been regenerated and the receipt has been run. The controller or user should fill this row with the exact command, exit code, and JSON. |

## Not Exercised

- Full repository gates were not run in this T1 implementer session.
- Self-host regeneration and generated projection drift checks were not run.
- The projected `.agents/` helper was not invoked after the source change.
