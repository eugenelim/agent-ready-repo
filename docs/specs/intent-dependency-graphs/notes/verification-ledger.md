# Verification ledger: intent dependency graphs

Execution observations for [`spec.md`](../spec.md) and [`plan.md`](../plan.md). Each entry names the commit it ran against.

## T1: dependency query and text

### Real-input corpus (VI-1003)

Characterized before the refusal fixtures were finalized, at base commit `93c1054755fa`.

| Intent file | SHA-256 | `Depends on:` value | Form | Result |
| --- | --- | --- | --- | --- |
| `docs/product/intents/FEAT-0007-work-item-promotion-routing.md` | `1f5bd12821fb…` | `docs/product/intents/FEAT-0006-work-item-capture-contract.md` | `path` | edge |
| `docs/product/intents/FEAT-0008-governance-item-record-routing.md` | `87f4795f5ea9…` | `docs/product/intents/FEAT-0007-work-item-promotion-routing.md` | `path` | edge |
| `docs/product/intents/FEAT-0009-duplicate-coverage-check.md` | `5c84b4e5dc41…` | `docs/product/intents/FEAT-0007-work-item-promotion-routing.md` | `path` | edge |

Three headers, all legacy paths with a trailing preamble comment: 3 accepted, 0 refused. No typed value is in use yet, so the path rule is what makes today's dependencies visible.

### Red and green

- Red: with `dependencies` removed from the operation set, `test_dependencies.py` gave 31 failed, 9 passed (the 9 are the refusal and compatibility cases that hold either way).
- Seeded defects, each reverted: dropping the self-loop rule failed 1 test; dropping the empty/`.`/`..` segment check failed 1 test.
- Green: `test_dependencies.py` 40 passed in 4.2 s. The navigator and `close-work` suites: 899 passed, 4 skipped (by-design whole-operation-failure corpora) in 26 s. `make lint-ruff lint-mypy` clean.
