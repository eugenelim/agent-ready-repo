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

## T4 — the differential can fail, both ways (2026-09-13)

`python3 -m pytest tools/test_merge_driver_behaviour.py -k record_index`:

| Mutation | Result |
| --- | --- |
| fixture calls `_configure` (driver registered before the halting run) | 2 errors — the fixture's unset guard fires: `assert 0 != 0 ... stdout='true\n'` |
| both `.gitattributes` lines deleted | 2 failed — the merge no longer halts, and no row is discarded |
| none | 2 passed |

The first mutation is the inherited-config case: a `--global merge.regen.driver`
would otherwise let the halting half pass without proving anything. The second is
the case four earlier formulations of this criterion could not detect.

## T4 — `AGENTS.local.md` budget and command runnability (2026-09-13)

58 lines before, 59 after, against `MAX_ROOT_LOCAL_LINES = 60`;
`python3 tools/lint-agents-md.py` exits 0. Both commands extracted from the file
and executed from the repository root return exit 0 and leave
`docs/{adr,rfc}/README.md` unmodified — the generators are idempotent.

One correction worth recording: the first runnability check reported both
commands as failing. The commands were fine; the harness was not. zsh does not
word-split an unquoted `$c`, so the loop ran the whole string as one command
name and got exit 127. Re-run with `eval "$c"`, both return 0. A verification
harness can produce a false negative as easily as a false positive.
