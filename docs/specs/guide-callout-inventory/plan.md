# Plan: guide-callout-inventory

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `web/src/test/rendered-output.test.ts:231-249`
  (`sourceAsideCount` — the source-derived pattern this change mirrors) and
  `:994-1019` (the ledger-derived half it replaces);
  [`tools/AGENTS.md`](../../../tools/AGENTS.md) (pure-stdlib rule);
  `tools/test_local_ci_shared_test_deduplication.py:175-182` (the tuple a
  Makefile test-list addition must join).

## Approach

Delete a coupling rather than manage it. The ledger stops being compared to
the guides tree in both languages; each rendering check derives its
expectation from the guide's own source at test time, which the `web/` suite
already does for asides. What remains of the ledger is asserted against
itself, and the assertions with a mechanical repair move to their own gated
module while the tripwires stay unwired.

Net effect is a smaller repository: one new small module holding relocated
assertions, one new ~15-line counter, and the removal of two tests, one
loader, one interface and one constant.

## Constraints

- `tools/` additions are pure-stdlib.
- The Makefile `test` group, `build-check.yml`'s parallel pytest list, and
  `FINAL_TOOL_BATCH` are asserted against each other; a partial edit reddens a
  different suite than the one being changed.
- The two JSONL files are frozen: row text is not edited, renumbered, or
  removed. Mutation proofs use `tmp_path` copies.
- `make test` does not run the `web/` vitest suite; that half needs
  `npm ci --prefix web` (or `make bootstrap-sites`) and an explicit vitest run.

## Construction tests

`tools/test_guide_ledger_integrity.py` is new and holds the relocated ledger
assertions, driven against `tmp_path` copies so each rule can be killed.
`tools/test_guide_typed_asides.py` keeps only the two release tripwires.
The `web/` change is verified by its own suite plus a mutation.

## Tasks

### T1: The rendered-output suite derives blockquote expectations from source

**Depends on:** none

**Touches:** web/src/test/rendered-output.test.ts

**Tests:**
- The suite passes against the built tree with no ledger read (AC1, AC2).
- Mutation: add a blockquote to one guide source without touching anything
  else; the suite goes red naming that file. Restore and confirm green (AC2,
  AC8).
- Mutation: the existing aside comparison still fails when a source aside is
  removed, proving AC3 lost no coverage.

**Approach:**
- Add `sourceBlockquoteCount(sourcePath)` mirroring `sourceAsideCount`: same
  fence tracking, counting contiguous runs of lines matching `/^>/` outside a
  fence, a run ending at the first non-`>` line.
- Replace the `quotationRows` comparison with it, and drop the per-blockquote
  `anchor` substring match — the source count is the expectation now.
- Delete `ASIDE_LEDGER`, `AsideLedgerRow`, `asideLedger()`, and the
  ledger-row-to-HTML test at `:960`; its property (each classified row renders
  as its type) is covered by the source-derived aside comparison.

**Done when:** `npx vitest run --root web src/test/rendered-output.test.ts`
passes, `grep -c 'blockquote-classification' web/src/test/rendered-output.test.ts`
is 0, and both mutations are recorded.

### T2: Ledger integrity is asserted against itself in its own gated module

**Depends on:** none

**Touches:** tools/test_guide_ledger_integrity.py,
tools/test_guide_typed_asides.py

**Tests:**
- Each AC4 rule killed by mutating a `tmp_path` copy of the two JSONL files,
  with a positive control on the unmutated copy (AC4, AC8).
- No assertion in either module parses the conversion spec's prose for a
  count (AC4).

**Approach:**
- Create `tools/test_guide_ledger_integrity.py` carrying the relocated
  assertions, with the ledger paths parameterised so a copy can be
  substituted.
- From `tools/test_guide_typed_asides.py` delete
  `test_ledger_has_complete_terminal_classifications`,
  `test_ledger_matches_converted_asides_and_unchanged_quotations`,
  `_expected_baseline_count`, `_load_ledger`, `_load_baseline`,
  `_blockquote_blocks`, `_blockquote_body`, `_aside_blocks`, `GUIDES_ROOT`,
  and the now-unused constants. **Keep `SPEC_PATH`** — the retained handoff
  test reads it.
- Rewrite that module's docstring: two release tripwires, why they are not
  gated, how to run them, and no falsifiable counts.

**Done when:** `python3 -m pytest tools/test_guide_ledger_integrity.py
tools/test_guide_typed_asides.py -q` is green, both files pass `make
lint-ruff`, and every relocated rule has a recorded kill.

### T3: The integrity module is gated and the register entry is wiped

**Depends on:** T1, T2

**Touches:** Makefile, .github/workflows/build-check.yml,
tools/test_local_ci_shared_test_deduplication.py, workspace.toml,
docs/specs/README.md, docs/specs/guide-callout-inventory/notes/falsifiability.md

**Tests:**
- `tools/test_local_ci_shared_test_deduplication.py` passes, which is what
  asserts Makefile membership against `FINAL_TOOL_BATCH` (AC5).
- `tools/test_guide_authoring_standard.py` passes unchanged — its
  unwired assertion still names only `tools/test_guide_typed_asides.py`, which
  stays out of all three lists (AC6).
- Goal-based: a `tomllib` read plus a plain-text search confirm the slug is
  absent from `workspace.toml` entirely, comments included (AC7).

**Approach:**
- Add `tools/test_guide_ledger_integrity.py` to the three lists in one commit.
- Delete the backlog entry outright rather than closing it; the coupling it
  tracked no longer exists, so there is nothing for a closed record to
  describe.
- Add the `docs/specs/README.md` active-list row.
- Record `notes/falsifiability.md`.

**Done when:** `make ci` passes, the `web/` vitest suite passes, and a
deliberate removal from any one of the three lists reddens a suite (AC9).

## Rollout

One PR, reversible by revert. No flag, no runtime surface, no infrastructure.

## Risks

- **Losing the quotation-vs-aside judgement.** Source-derived counting cannot
  tell that a block *should* have stayed a quotation. Accepted by the owner:
  that judgement is frozen history, two of its rows are already stale, and
  enforcing it forever is the coupling being removed.
- **`make test` does not cover the `web/` half.** A green `make ci` alone does
  not prove T1. The vitest run is a separate, named gate in T3's Done-when.
- **A blockquote run's definition could drift from remark's.** Both counters
  use column-0 markers; an indented `>` would be counted by remark and not by
  either counter. Measured: zero such cases in `guides/**` today, and the
  asymmetry already exists for asides, so this change neither adds nor removes
  it.

## Changelog

- 2026-08-31 — Drafted as a regenerator plus a generated registry, then cut to
  a deletion at the necessity rung. The registry would have been derived from
  `guides/**` and compared only against `guides/**`, so its diff was redundant
  with the guide diff that produced it; the regenerator, TOML emitter,
  check/write CLI, root-file placement, `EXCLUDED_PATTERNS` registration, ADR
  and frozen-spec supersession all existed only to keep that artifact honest
  and were removed with it. Two review rounds against the larger design
  produced the fact that made the cut obvious: `web/src/test/rendered-output.test.ts`
  already derives its aside expectation from source and only its blockquote
  expectation from the ledger.
