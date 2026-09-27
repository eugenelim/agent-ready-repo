# Verification Ledger: Base Freshness in Policy-Limited Environments

## Session Scope

This ledger records observed evidence for the helper and its delivery gates in
the `base-freshness` workspace on 2026-09-26.

## Observed Evidence

| Evidence | Command or source | Observed result | Contract covered |
| --- | --- | --- | --- |
| Targeted helper suite after T1 implementation | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_check_base_freshness.py -q` | Exit 0; `27 passed in 42.25s` | Unavailable `ls-remote`, unavailable fetch, timeout skips, stale-base surface, local-state refusals, and missing-branch surface were covered by the suite. |
| Targeted helper suite after lint-only repair | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_check_base_freshness.py -q` | Exit 0; `27 passed in 67.90s` | Mechanical import and pathlib chmod repairs preserved T1 behavior. |
| Targeted helper suite after post-gates classifier repair | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_check_base_freshness.py -q` | Exit 0; `31 passed in 45.76s` | Malformed URL/protocol diagnostics remain unclassified and surface without raw stderr on both `ls-remote` and fetch paths, while DNS/auth and metadata-denied cases remain covered. |
| Targeted helper suite after missing-branch classifier repair | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_check_base_freshness.py -q` | Exit 0; `32 passed in 40.01s` | Only the exact C-locale missing-ref diagnostic for the case-sensitive requested branch takes the missing-branch path; echoed remote paths fall through safely. |
| Targeted helper suite after structured-cause classifier repair | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_check_base_freshness.py -q` | Exit 0; `41 passed in 44.91s` | Closed unavailable and metadata-denial categories are derived from structured diagnostic causes, while category phrases embedded in echoed URLs, paths, or refs remain blocking and redacted. |
| Targeted helper suite after SSH causal-line completion | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_check_base_freshness.py -q` | Exit 0; `46 passed in 52.95s` | Trailer-only failures remain blocking, genuine SSH `Operation timed out` skips through its causal line, and a closed cause followed by the generic trailer still skips. |
| Targeted helper suite after closing quality repair | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_check_base_freshness.py -q` | Exit 0; `46 passed in 52.25s` | Skipped paths now assert empty stderr and bounded messages, and the metadata-denied fetch path uses deterministic injection instead of filesystem permission semantics. |
| Final local lint and type gate | `env PYTHONDONTWRITEBYTECODE=1 make lint-ruff lint-mypy` | Exit 0; Ruff passed and mypy found no issues in 149 source files. | Changed Python and test code satisfy the repository's required local gate. |
| Final caller-contract regressions | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/pack/test_work_intake_surface.py packs/core/tests/skills/work-loop/test_step0_eval_contract.py -q` | Exit 0; `11 passed in 0.68s`. | Pack boundary metadata and executable skipped-status eval assertions remain aligned. |
| Final contract alignment | `env PYTHONDONTWRITEBYTECODE=1 python3 .agents/skills/new-spec/scripts/lint-contract-item-alignment.py --root . docs/specs/base-freshness-policy-limited-environments` | Exit 0; 0 findings across the feature spec. | Acceptance criteria, plan tasks, and verification groups remain aligned. |
| Final lifecycle consistency | `env PYTHONDONTWRITEBYTECODE=1 python3 .agents/skills/work-loop/scripts/lint-spec-status.py --root . --all` | Exit 0; all 485 specs were metadata-clean, with 227 warn-only findings hidden. | Shipped spec status, done plan status, checked acceptance criteria, and repository-wide references are valid. |
| Final review round | Persisted round-7 adversarial, quality, and security reports under the ignored `.context/reviews/39ba280f-c34a-45b2-a5ba-59e6ec5cd52f/` session path | Adversarial and quality reviews returned the exact clean sentinel; security returned clean with its bounded `Not checked` footer, which independent adjudication classified clean. | No unresolved Blocker, Concern, Nit, or indeterminate security item remains. |
| Existing real-Git stale-base regression | `test_behind_surfaces` within the targeted helper suite | The suite passed; the case asserts exit 1, `status == "surface"`, and a message containing `behind` and `rebase`. | A proven stale base remains blocking. |
| Policy-limited current checkout before this change | User-provided session output for `.agents/skills/work-loop/scripts/check-base-freshness.py` | Exit 1 with `{"status": "surface", "message": "ls-remote to 'origin' failed — check network/auth", "target": ""}`. | Historical context: the pre-change helper blocked when the environment prevented remote freshness verification. |
| Projected helper invocation after regeneration | `env PYTHONDONTWRITEBYTECODE=1 python3 .agents/skills/work-loop/scripts/check-base-freshness.py` | Exit 1 with `status: "surface"`, `target: "origin/main"`, and a bounded message that the dirty branch was 2 commits behind. Stderr was empty. | The remote query and fetch succeeded, so the helper correctly preserved the proven-stale blocking path instead of using `skipped`. |
| Local comparison after the owner updated the branch | `git rev-list --count HEAD..refs/remotes/origin/main` | Exit 0 with count `0`; `git status --short` was empty. | The confirmed-stale stop was resolved before work resumed. |

## Evidence Limits

- The post-change live invocation did not exercise `status: "skipped"` because
  remote discovery and fetch succeeded; timeout, transport/authentication, and
  metadata-denial skip paths are covered by the targeted suite.
- SAST, SCA, secret, and CVE scanners were not run; those are scanner-owned
  gates, and this change adds no dependency or external artifact.
- Git diagnostics were not exhaustively sampled across every Git version and
  transport. The closed structured forms implemented here are covered directly.

## Completion Evidence

- **Accepted outcome:** environmental remote-query or Git-metadata capability
  failures can return a bounded `skipped` result, while stale, unsafe, missing,
  malformed, and unclassified states remain blocking.
- **Implemented scope:** helper classification, work-loop caller guidance and
  evals, pack metadata/projections, regression tests, release version, and
  changelog.
- **Durable outputs:** the shipped spec, done plan, source skill/helper, tests,
  generated projections, and changelog are present in the repository.
- **Verification:** the final targeted suites, lint/type gate, contract lint,
  projection comparisons, catalogue verification, self-host build, and three
  warranted closing reviewers passed. Stable command-level evidence is in the
  table above and the earlier user-run gate records under `.context/`.
- **Deferrals and dependencies:** none. The result relies only on existing Git
  and Python behavior and introduces no new dependency or migration.
- **Tail triage:** the canonical behavior and test change is below the 2,000-line
  review-shape threshold; generated adapter copies were compared byte-for-byte
  with the canonical helper.
