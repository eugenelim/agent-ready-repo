# Verification ledger: record-index merge driver

Execution observations. The spec and plan state what must hold; this records
what was observed when it was checked.

## T1 — the rail derivation can fail (2026-09-13)

`_record_index_paths` replaced by one returning the literal pair
`{docs/adr/README.md, docs/rfc/README.md}` regardless of input:

```
FAILED tools/test_gitattributes_merge_driver.py::test_record_index_rail_is_empty_without_a_gate_step
1 failed, 2 passed
```

The empty case is what a literal fallback defeats, and it reds. Restored: 3 passed.

## T2 — the date control can fail (2026-09-13)

The synthetic record's `- **Date:** 2026-01-01` line removed, which is the exact
degradation that makes a generate-then-check pass while proving nothing:

```
FAILED tools/test_gitattributes_merge_driver.py::test_index_table_carries_the_records_own_date
1 failed, 2 passed
```

Restored: 3 passed. Two earlier formulations of this control had no failing
state; this one does.

## T3 — scope mutations, both directions (2026-09-13)

`python3 -m pytest tools/test_gitattributes_merge_driver.py -k equals_gate_covered`
against three mutations of `.gitattributes`:

| Mutation | over-scope | under-scope |
| --- | --- | --- |
| `docs/adr/README.md` line removed | 0 | 1 — `docs/adr/README.md` |
| `docs/rfc/README.md` line removed | 0 | 1 — `docs/rfc/README.md` |
| `docs/specs/README.md` added | 1 — `docs/specs/README.md` | 0 |

The third is the destructive direction: `docs/specs/README.md` has no generator
at all, because ADR-0112 retired its index table, so declaring the driver on it
would discard a real edit. Restored: 1 passed.

## T3 — pattern anchoring (2026-09-13)

`git check-attr merge` over every tracked `*/adr/README.md` and `*/rfc/README.md`:

```
docs/adr/README.md                               -> regen
docs/rfc/README.md                               -> regen
packs/governance-extras/seeds/docs/adr/README.md -> unspecified
packs/governance-extras/seeds/docs/rfc/README.md -> unspecified
```

The seed copies are untouched. Both patterns carry a directory separator, so
they anchor at the repository root rather than matching at every depth.
