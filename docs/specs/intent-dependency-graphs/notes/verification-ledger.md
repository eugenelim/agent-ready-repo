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
- Dispatch: T1 was built by the controller in-session; the owner directed on 2026-10-14 that it be recorded `human-directed`. T2 to T6 go to the `implementer` subagent.

## T2: the view payload carries dependencies

- Implemented by the `implementer` subagent. The payload gains `dependencies` after `source_links`; a `--from` export carries the linked set's records.
- Golden for the unchanged members: the pre-change navigator from `93c105475` was loaded by path from a scratch directory outside the repository and run over copies of `mixed` and `dependency`; each member's SHA-256 over canonical JSON (excluding `provenance.generated_at`) is inlined in `test_export_payload.py`.
- Gates: navigator and `close-work` suites 907 passed, 4 skipped (by design) in 26 s; `make lint-ruff lint-mypy` clean.
