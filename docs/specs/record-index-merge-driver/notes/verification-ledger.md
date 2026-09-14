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

## Sync with origin/main — a premise changed underneath the spec (2026-09-13)

Merging `origin/main` (4 commits) re-added
`web/src/lib/now-highlights.generated.json`, which commit `da10ba428` had
untracked and which the spec recorded as untracked and gitignored. Commit
`081c26209` (PR #1292) tracks it again, so that Assumption was false by the
time this branch synced. The ignore entry itself is still at `.gitignore:146`,
inside the rationale block at `:131-145`; it is inert rather than removed,
because git ignores nothing it already tracks.

It stays out of the driver, for a different reason than before. The original
reason was that an untracked file cannot conflict; the reason now is the rule
itself. `tools/build-site.py` writes it, has no `--check` mode, appears in no
`build-check` chain step, and runs only in `pages.yml` and `docs.yml` — neither
a required PR check. Nothing reds if a merge leaves it stale, so declaring the
driver would discard a real edit with nothing to notice.

AC1 is unaffected: the file is tracked but belongs to neither side of the
equality, and `test_merge_regen_set_equals_gate_covered_set` passed after the
merge. The `.gitattributes` header now names it among the eligible-looking
ineligible paths, because tracked-and-generated is exactly what makes a path
look eligible.

## T4 — wall-clock delta on the behaviour suite (2026-09-13)

Required by the plan's Constraints and T4's Done-when. The two new cases add
**~10.2s of attributed time**, measured with `pytest --durations=0`:

| Case | setup | call |
| --- | ---: | ---: |
| `test_record_index_merge_is_driver_resolved_not_textual` | 1.20s | 5.53s |
| `test_record_index_regeneration_recovers_the_discarded_row` | 1.25s | 2.20s |

Against a suite total of 55.18s, in which the pre-existing
`test_build_self_converges_after_an_auto_resolved_merge` alone costs 28.27s
(8.96s setup + 19.31s call). So the addition is roughly a quarter of the
suite's attributed time and about a third of what one existing case already
costs. `.github/workflows/build-check.yml:75-79` records both merge-driver
steps at 22s and 33s on one 2026 macOS dev machine; this grows the second.

**Method note, because the obvious method failed here.** A whole-suite
before/after wall clock was attempted first and is not reportable: three arm
pairs gave deltas of +37.3s, +0.2s and +53.0s on a machine whose load average
was 36 during measurement. One of those runs would have supported "the two
cases nearly double the suite" and another "they cost nothing"; neither is a
measurement. Per-test attribution is reported instead because pytest charges
time to the case that spent it, which survives the contention that destroys a
whole-run comparison. The figures above are still an upper bound on a loaded
machine, not a clean-room number.

## Citation drift after the sync, and why the plan keeps its approved bytes (2026-09-13)

Merging `origin/main` inserted `release-jsonl-otlp-exporter.yml` into
`tools/lint-ci-parity.py`, and this change's own comment rewrap moved two
workflow steps. Five citations in the contract drifted. Recomputed against the
post-merge tree:

| Cited as | Actually at |
| --- | --- |
| `build-check.yml:287` (AC1 step) | `:288-289` |
| `build-check.yml:294-295` (behaviour step) | `:298-299` |
| `lint-ci-parity.py:377` (AC1 disposition) | `:378-379` |
| `lint-ci-parity.py:379` (behaviour disposition) | `:380-381` |
| `lint-ci-parity.py:377-380` (both pinned keys) | `:378-381` |

The three in `spec.md` were corrected in place. The two in `plan.md` were not,
and the plan carries its approved bytes: `loop-cohort schedule` pins `plan.md`
at `approve-plan`, and editing it — even for two line numbers — breaks that
baseline. The documented recovery re-pins whatever is on disk, which the tool
itself describes as "a re-approval in substance", and a re-approval is the
human's to give, not something to take for a citation fix. Restoring the
approved bytes returned `schedule check-current` to OK.

The property those two citations stand for is unaffected and is what the
closeout actually tests: both step-name strings are unchanged, so
`lint-ci-parity.py`'s pinned dict keys still resolve. Only the line numbers in
the plan's prose are stale, and this table is where a reader finds the current
ones.

## The /now/ projection, answered against the post-merge tree (2026-09-13)

The second sync pulled in changes to `tools/build-site.py` and 118 lines of
`tools/test_build_site_routing.py`, which is the suite the original request
asked about. Re-checked, because the earlier answer rested on the file being
untracked and that premise had already failed once.

- The suite **is** in a required check: `build-check.yml:339` runs it in
  `gate-main`.
- It does **not** assert the committed file is current. Every `now_highlights`
  case calls `build_site.project_now_highlights(text)` against inline fixtures;
  `grep -rn "now-highlights.generated" tools/` returns exactly one hit, the
  write path in `build-site.py`.
- The only other readers are `web/src/pages/now/index.astro`, which consumes the
  file at build time, and `web/src/test/rendered-output.test.ts`, a web vitest
  suite `build-check.yml` does not run.

So the path fails the rule for the reason the rule exists: exercising a
generator is not gating its output. A required check that tests the projection
function would stay green while the committed blob rotted, and the driver would
discard a real edit with nothing to notice. It stays out, and the
`.gitattributes` header names it among the eligible-looking ineligible paths.
