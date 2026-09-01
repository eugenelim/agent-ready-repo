# Spec: guide typed asides test gate

- **Status:** Shipped (AC6's register anchor `guide-blockquote-ledger-has-no-regenerator` was closed by [`guide-callout-inventory`](../guide-callout-inventory/spec.md); not a supersession — every decision here stands) <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Depends on:** `spec/marketplace-generator-single-source` — its gate asserts that the
  Makefile `test` group and the `build-check.yml` step name the same files, which is
  what verifies AC5 here. That spec lands first; this one is stacked on it.
- **Contract:** none

Mode: light (no risk trigger fired)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The live invariants of the packaged guide authoring standard are enforced by a gate,
so a maintainer who lets the shipped copy drift from the repository's finds out from
CI rather than from an adopter. The assertions that are *not* live invariants — the
archival record of a one-time blockquote conversion — stay out of the gate on purpose,
recorded as a decision rather than left as an accident. And
`tools/test_guide_typed_asides.py` tells the truth about the repository: it was red on
`main`, asserting that the current package version equalled `0.37.1`.

## Boundaries

### Always do

- Gate an assertion only if a routine, unrelated change cannot redden it. Where that
  is not true, say so and register why.
- Keep the Makefile `test` target and `build-check.yml`'s parallel pytest list
  identical.

### Ask first

- Wiring the blockquote-ledger assertions into any gate.
- Adding a release obligation (such as requiring `README-pypi.md` to name the current
  version) that no existing checklist documents.

### Never do

- Change an assertion to match a value that drifts again next release.
- Delete an assertion because it is failing; only remove one that encodes no
  invariant, and say why.
- Edit `docs/specs/guide-typed-asides-conversion/notes/*.jsonl`, or another spec's
  gate wiring, in this change.

## Testing Strategy

- **AC1–AC4 — TDD.** The files are their own tests, and every assertion **in the gated
  file** is confirmed falsifiable against a fixture: a mutation of the thing it guards
  must make it fail, with a positive control. An assertion that has never been seen red
  is not a control. The archival file's ledger assertions are *not* probed — they are the
  frozen record of a completed conversion, they are not gated, and probing them would
  mean regenerating the ledger this spec explicitly does not touch.
- **AC5 — TDD.** Both halves are asserted, not grepped: the gated file's presence in
  each list by `spec/marketplace-generator-single-source`'s parity gate, and the archival
  file's *absence* by `test_the_archival_conversion_record_stays_unwired` in the gated
  file itself — otherwise nothing detects it being wired back in.
- **AC6, AC7 — goal-based check.**

## Acceptance Criteria

- [x] **AC1.** `tools/test_guide_authoring_standard.py` and
      `tools/test_guide_typed_asides.py` both pass, and neither contains an assertion
      comparing the *current* `pyproject.toml` version to a literal — so both survive a
      version bump untouched.
- [x] **AC2.** The gated file asserts only invariants that hold at every release: the
      authoring standard's fixed aside contract, the packaged scaffold copy's
      byte-equality with the repository's, its manifest digest, and `CLI_VERSION` ↔
      `pyproject.toml`.
- [x] **AC3.** Every assertion in the gated file is demonstrably falsifiable: mutating
      what it guards makes it fail, with a positive control on the unmutated fixture.
      Recorded in [`notes/falsifiability.md`](notes/falsifiability.md) together with the
      harness that produced it, so the record is reproducible rather than asserted.
- [x] **AC4.** The archival file states in its module docstring that it is deliberately
      unwired, why, and how to run it; its historical release assertion is anchored to
      exactly one `## [<release>]` heading and is whitespace-normalised, so neither a
      `###` subheading nor a reflow satisfies or breaks it.
- [x] **AC5.** `tools/test_guide_authoring_standard.py` appears in the Makefile `test`
      target and in the `build-check.yml` step carrying the parallel pytest list;
      `tools/test_guide_typed_asides.py` appears in neither.
- [x] **AC6.** Each assertion excluded from the gate resolves to a
      `workspace.toml [backlog].open` slug recording the defect, the fix, why it was
      excluded rather than gated, and an `Unblocks when:` line.
- [x] **AC7.** `make ci` passes.
