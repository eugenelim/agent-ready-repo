# Verification ledger: grounding-preservation-contract-proof

## 2026-10-28 — T1 at base `42d02f315f22c4f25653644212c7615ada79f1d7`

- `packs/core/tests/skills/work-loop/test_preservation_contract_proof.py`: 55 passed, 0.4 s.
- Suite can fail. Each change below was made to a scratch copy of
  `_acceptance.py`, and the shipped file was not changed:

  | Sabotage | Failed | Passed |
  | --- | ---: | ---: |
  | Freshness ignores the acceptance fingerprint | 13 | 42 |
  | Contradiction never fires | 7 | 48 |
  | Outcome not checked against the term's `outcomes` | 9 | 46 |
  | Reserved `supported-review-failure` term always added | 2 | 53 |

- `make lint-ruff lint-mypy`: pass.

## 2026-10-28 — T2

- AC-0010: the `Contract-fit result` section states "Existing contract
  sufficient" and `42d02f315f22c4f25653644212c7615ada79f1d7`.
- AC-0011: `git diff --name-only "$(git merge-base origin/main HEAD)" HEAD` on
  the committed branch lists six paths, all allowed: the brief,
  `workspace.toml`, the test module, and this spec's `spec.md`, `plan.md`, and
  `notes/verification-ledger.md`. No path is under `packs/*/.apm/` or
  `packs/*/seeds/`.

## 2026-10-28 — CI repair, PR #1640

- `lint-pack-test-boundary` refused the suite's read of `contracts/delivery/`.
  The suite now relies on the shipped validators; the roster parity suites own
  their agreement with the schema files.
- The roster version-bump test requires a Core patch bump for any change under
  `packs/core/`. Core moves to `3.1.30`, the next free patch after `3.1.29` on
  main, with a changelog fragment.
- The workspace-retirement inventory requires a row for every spec file that
  names the registry; this spec directory gets a `historical` row.
