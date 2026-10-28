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
