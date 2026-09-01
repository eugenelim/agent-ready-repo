# Spec: guide-callout-inventory

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none
- **Shape:** data

Mode: light (no risk trigger fires — the change removes a coupling and moves
assertions between files; it adds no module boundary, dependency, stored
state, or security surface)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Nothing compares the 2026 blockquote conversion ledger against the guides
tree, so editing a guide cannot redden a record of history. Every check that
asks "does this guide render the callouts its source declares?" derives the
expectation from the source file at test time, in both Python and TypeScript,
so there is no intermediate artifact to keep in step. The ledger remains as
what it is — a frozen record, asserted only against itself — and the register
entry that tracked the coupling is gone, because the coupling is gone.

## Boundaries

### Always do

- Derive an expectation about a guide from that guide's own bytes at test
  time.
- Mirror the shape of `sourceAsideCount` in `web/src/test/rendered-output.test.ts`
  when deriving the blockquote expectation; it is the pattern already proven
  in that file.
- Delete a check rather than re-point it when the property it asserts is
  already covered by a source-derived check.

### Ask first

- Retaining any comparison between ledger rows and the guides tree.
- Removing, renumbering, or rewording any ledger row.
- Gating any assertion whose drift has no mechanical repair.

### Never do

- Introduce a generated artifact, a regenerator, a new dependency, a new
  top-level file or directory, or a new module boundary.
- Edit any guide's prose, or either frozen spec's body, to make a check pass.
- Reintroduce a value derived by parsing a frozen spec's prose.

## Testing Strategy

- **Source-derived rendering checks — TDD.** AC2 and AC3 are behaviour over
  file bytes; the blockquote counter is written test-first and proven by a
  mutation that makes the rendering check red.
- **Decoupling — goal-based check.** AC1 is structural and exhaustive by
  construction: no tracked source in any language reads a ledger path and a
  `guides/` path in the same assertion. A repository-wide search over every
  consumer verifies it, not a sample.
- **Ledger integrity — TDD.** AC4's rules are asserted against a `tmp_path`
  copy of the two JSONL files, each rule killed by mutating that copy, with a
  positive control on the unmutated copy.
- **Gating and register — goal-based check.**

## Acceptance Criteria

- [ ] **AC1 — No assertion reads the ledger against the guides tree, in any
      language.** No tracked source file opens
      `notes/blockquote-classification.jsonl` or
      `notes/blockquote-baseline-identities.jsonl` and a path under `guides/`
      in the same assertion. `web/src/test/rendered-output.test.ts` references
      neither file.
- [ ] **AC2 — A guide's built blockquotes are checked against its own source.**
      For every `guides/**/*.md`, the rendered-output suite compares the count
      of built `<blockquote>` elements outside any `aside.starlight-aside`
      against the count of blockquote runs in that file's source, where a run
      is a contiguous block of lines beginning `>` at column 0 outside a fenced
      code block, fences being matched by the same expressions
      `sourceAsideCount` already uses.
- [ ] **AC3 — A guide's built asides are checked against its own source, per
      type.** For every `guides/**/*.md`, the rendered-output suite compares the
      count of built `aside.starlight-aside--<type>` elements against the count
      of `:::<type>` blocks in that file's source, for each of `note`, `tip`,
      `caution`, `danger`.
- [ ] **AC4 — The ledger's integrity is asserted against itself.**
      `tools/test_guide_ledger_integrity.py` checks: `item` values exactly
      `1..N` in order; every row carrying exactly the fields `item`, `path`,
      `line`, `content_sha256`, `anchor`, `classification`, `status`,
      `reason`; `status` in `{done, superseded}`; `classification` in
      `{quotation, note, tip, caution, danger}`; non-empty `reason` and
      `anchor`; `content_sha256` matching `[0-9a-f]{64}`; unique
      `(path, line, content_sha256)` triples; unique `(path, anchor)` pairs;
      and identity equality with the baseline file. No assertion derives an
      expected value by parsing prose in
      `docs/specs/guide-typed-asides-conversion/spec.md`.
- [ ] **AC5 — The ledger-integrity module is a required check.**
      `tools/test_guide_ledger_integrity.py` appears in the Makefile `test`
      group, in the `build-check.yml` step carrying the parallel pytest list,
      and in `FINAL_TOOL_BATCH` in
      `tools/test_local_ci_shared_test_deduplication.py`.
- [ ] **AC6 — The tripwires stay out of the gate.** The release-notes and
      release-handoff assertions, whose drift has no mechanical repair, remain
      in `tools/test_guide_typed_asides.py`, which appears in none of the three
      lists AC5 names; its module docstring says so, says how to run it, and
      states no count of guide files or ledger rows that a routine guide edit
      can falsify.
- [ ] **AC7 — The register no longer carries the entry.** The slug
      `guide-blockquote-ledger-has-no-regenerator` appears nowhere in
      `workspace.toml` — neither in `[backlog].open` nor in `[backlog].closed`
      — and no comment line in that file refers to it.
- [ ] **AC8 — Every added and relocated assertion is falsifiable.** Each
      assertion added or moved by this change has a recorded mutation that
      makes it fail, with a positive control on the unmutated fixture,
      recorded in [`notes/falsifiability.md`](notes/falsifiability.md).
- [ ] **AC9 — `make ci` and the `web/` vitest suite both pass.**

## Assumptions

- Technical: `web/src/test/rendered-output.test.ts` already derives its aside
  expectation from source at test time (`sourceAsideCount`, `:231-249`) while
  deriving its blockquote expectation from ledger rows (`:1004-1019`), so the
  correct pattern is present in the same file and this change makes the two
  halves symmetric (source: that file).
- Technical: the ledger's consumers in `web/` are one loader and two tests
  (`ASIDE_LEDGER` `:33`, `AsideLedgerRow` `:187`, `asideLedger()` `:198`, and
  their uses at `:960` and `:994-1019`), so removing the dependency is bounded
  (source: `grep` over that file).
- Technical: `.github/workflows/pages.yml:192` runs `npm test --prefix web` on
  every PR touching `guides/**` (`:30-35`), and `make test` does not run that
  suite, so the `web/` half must be verified with `npm ci` plus vitest
  explicitly (source: that workflow; `Makefile`).
- Technical: the ledger holds 175 rows (169 `done`, 6 `superseded`), while
  `guides/**` holds 194 callouts across 79 of 203 files; 27 live callouts have
  no ledger row and 2 `done` rows no longer resolve. The ledger has therefore
  not described the tree for some time, which is why no check should compare
  them (source: read-only inventory probe, 2026-08-31).
- Technical: `EXPECTED_ROOT_TOOL_PATHS` folds in `FINAL_TOOL_BATCH` and is
  asserted against the real Makefile by
  `test_real_make_root_tool_groups_match_the_approved_profiles`, so a Makefile
  test-list addition must also join that tuple (source:
  `tools/test_local_ci_shared_test_deduplication.py:175-182,1240`).
- Process: `tools/test_guide_typed_asides.py` stays unwired, so
  `docs/specs/guide-typed-asides-test-gate/spec.md` AC4 and AC5 both remain
  true, and `tools/test_guide_ledger_integrity.py` is a new file that frozen
  spec makes no claim about. Its **AC6** is a different matter: it requires
  every gate-excluded assertion to resolve to a `[backlog].open` slug, and the
  deleted slug was that resolution for the two surviving tripwires. Nothing is
  superseded — every decision in that spec stands — so the licensed
  non-supersession `Status`-line pointer of `docs/CONVENTIONS.md` § *Superseding
  a frozen document* records the closure instead, on both that spec and the plan
  that names the anchor (source: that spec's AC4–AC6, its
  `plan.md:94-96`, and `docs/CONVENTIONS.md:186-203`).
- Process: no spec carries a deferral marker naming this slug, so deleting the
  register entry cannot break `lint-spec-status.py` invariant (iv). Stated
  without spelling the marker on purpose: `_DEFERRED_RE` in that linter matches
  the literal `(deferred: <slug>)` form anywhere in a spec, including inside
  prose describing it, so an earlier wording of this very line created the
  dangling anchor it denied (source: repository-wide search for that marker,
  and `lint-spec-status.py:103`).
- Product: the register entry is deleted rather than moved to
  `[backlog].closed`, because the coupling it tracked ceases to exist and a
  closed record would describe a condition no longer in the repository
  (source: user direction 2026-08-31).
- Product: the deliverable is the removal of the coupling and the closure of
  the register entry, not a regenerated artifact. A registry derived from
  `guides/**` and compared only against `guides/**` was cut at the necessity
  rung: its diff is redundant with the guide diff that produced it (source:
  user direction 2026-08-31).
- Product: per-type counting is accepted as weaker than the deleted
  ledger-to-HTML test in one respect: that test resolved each classified row to
  emitted HTML by anchor text, so an aside whose rendered body is replaced
  wholesale, or two same-type asides that swap position, now pass. Accepted
  rather than replaced with a source-derived body check, which would add scope
  the contract does not require (source: user direction 2026-09-01).
- Product: enforcing the reviewed judgement that a specific block stays a
  quotation is deliberately given up. That judgement is frozen history, two
  of its rows are already stale from legitimate rewording, and enforcing it
  forever is the coupling this change removes (source: user direction
  2026-08-31).
