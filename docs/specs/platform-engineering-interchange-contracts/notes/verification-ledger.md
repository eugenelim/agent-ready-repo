# Verification ledger

Execution observations for `platform-engineering-interchange-contracts`. All dates are 2026-11-12. The supervised run `run-821fbe5494340f5b` reached `terminal`, and `work-supervisor.py status --check` exited 0 with every criterion `supported`.

## Caller journeys (AC-0032, AC-0033)

Neither pack is self-hosted in this repository, so `make build-self` projects no copy of these skills. The shipped pack-source entry points are the built artifacts an installer copies. Both runs were made from the repository root at the final head, with `--now 2026-01-01T12:30:00Z`.

| Command | Exit | Result |
| --- | --- | --- |
| `python3 packs/iac-terraform/.apm/skills/generate-iac/scripts/plan_bundle.py validate iac-plan-bundle.v1.json --root packs/iac-terraform/.apm/skills/generate-iac/assets/native-adr-caller --policy trusted-policy.json --now …` | 0 | `status: "valid"`, no issues, 8 evidence records `verified` |
| `python3 packs/release-engineering/.apm/skills/release-loop/scripts/release_handoff.py validate release-handoff.yaml --root packs/release-engineering/.apm/skills/release-loop/assets/image-only-ci-caller --policy trusted-policy.json --now …` | 0 | `status: "valid"`, no issues, 5 evidence records `verified` |
| `release_handoff.py import-v1 image.yaml --output out.yaml …` on a temporary copy of the synthetic v1 image fixture with no supplement | 1 | `status: "incomplete"`, field-addressed `missing-field` and `missing-evidence` gaps; a new `out.yaml` was written; the input's SHA-256 was the same before and after |

No Terraform binary, network fetch, deployment or cloud account was used. The synthetic plan bytes prove validator behaviour, not Terraform executability.

## Synthetic v1 corpus

No recorded corpus of real v1 handoffs exists. The importer suite freezes 8 synthetic fixtures under `packs/release-engineering/tests/skills/release-loop/fixtures/v1/`: 3 convert and 5 are refused (unknown version, anchor, flow collection, duplicate key, unsafe name).

## Suites and gates (final head)

| Check | Result |
| --- | --- |
| `pytest packs/iac-terraform/tests/skills/generate-iac/` | 491 passed |
| `pytest packs/release-engineering/tests/skills/release-loop/` | 384 passed |
| `make lint-ruff lint-mypy` | pass |
| `make build-self` then `make precheck` (AC-0040) | both exit 0; bandit run separately on both scripts, no findings |
| `tools/lint-pack-test-boundary.py`, `tools/lint-ci-parity.py` | pass |
| `pytest tools/test_local_ci_shared_test_deduplication.py` | 51 passed |
| `tools/changelog.py validate` | pass |
| `tools/validate_guides.py`, `check-guide-index.py`, `lint-guides-no-repo-only-refs.py` | pass |
| 1 MiB adversarial decimal YAML scalar | parsed in 0.068 s (AC-0050 bound 2 s) |

## Acceptance verification

An independent verifier checked every criterion against the committed artifacts twice. The first pass found AC-0041 failing: a missing component identity cascaded into `subject-mismatch`. Repair task T7 fixed it with table-wide deletion tests, and the second pass showed it passing. Both passes flagged AC-0031 because no executable legacy reader exists. The approved plan names the oracle: a content pin of the unchanged v1 tolerant-reader passage plus parsing of the synthetic fixtures, and that pin passes.

## Code review

Reviewers were `adversarial-reviewer`, `security-reviewer` and `quality-engineer`, each over the whole change every round, with each finding adjudicated before repair.

| Round | Sustained findings | Repair task |
| --- | --- | --- |
| 1 | 5 (YAML decimal parsing super-linear, reported by two roles; JSON integer cap; U+2028 line splitting; masked confinement test); 1 refuted | T8 |
| 2 | 3 (unresolved plan binding dropped from imported candidate; quotes inside plain scalars; masked inspection-binding test) | T9 |
| 3 | 1 (no independent negative test for check-evidence coverage) | T10 |
| 4 | 1 (additional correctly bound plan checks rejected) | T11 |
| 5 | 0 — all three roles clean | — |

An integer literal longer than 4,300 digits is kept as exact decimal text. It is accepted only as inert `extensions` metadata and is `malformed-type` in a normative integer field. The two guide reference pages state this rule.

## Run environment incidents

- Another process on this machine rewrote the shared `.git/packed-refs` and deleted loose refs four times during the run. Each time the controller restored this branch, and when missing the supervisor product ref and `origin/main`, to their last recorded values. No commit was lost.
- The shared `.git/info/refs` changed under open attempts at least nine times. Under the owner's standing authorization, the controller re-baselined only that manifest entry each time.
