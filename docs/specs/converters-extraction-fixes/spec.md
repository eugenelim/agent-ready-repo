# Spec: converters-extraction-fixes

- **Status:** Shipped
- **Owner:** eugenelim
- **Contract:** none — this spec fixes bugs in the existing `converters` pack
  (`file-to-markdown` skill) without changing any documented I/O contract or
  output schema.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (work-loop). No risk trigger fired: familiar territory,
single-person, independent fixes, NO new dependency, and no public-interface /
schema change (the reconciler's JSON + frontmatter schema is unchanged; only its
behavior becomes more faithful). Scope is the non-RFC subset of the
doc-extraction pressure-test (.context/doc-extraction-pressure-test.md): the
silent-data-loss bugs, one doc↔code drift, and one honesty warning. The
architectural work (capability tiering, unified output contract, general-image
mode, chunking, enrichment, timeouts) is deliberately deferred to a forthcoming
RFC and is NOT in this PR. -->

## Objective

Fix correctness and honesty defects in `file-to-markdown` that cause **silent
data loss** and **doc↔code drift**, without adding dependencies or changing the
output schema. After this PR the image reconciler preserves every distinct
element the agent reports, the document branch fails with actionable guidance,
and the image branch is honest about multi-frame inputs.

## Acceptance Criteria

- [x] **AC1 — Distinct same-label nodes are preserved.** In `reconcile.py`, two
  elements of the same `(type, name)` whose global bounding boxes are spatially
  disjoint (IoU below the merge threshold) are kept as **separate** canonical
  elements, not collapsed into one. Elements seen across overlapping tiles (IoU
  ≥ threshold, or missing bbox) still merge to one with combined `tile_sources`
  (no regression of the core dedup).

- [x] **AC2 — Unnamed elements are no longer silently dropped.** An element with
  an empty/absent `name` is retained (spatially deduped like any other) and
  rendered with a visible `(unlabeled)` label in the Markdown table; it is
  counted in `ELEMENTS`. The stored JSON `name` stays faithful (empty string).

- [x] **AC3 — Actionable failure on the document branch.** When Docling raises
  during conversion (`convert.py`), the script exits non-zero with a message
  that names the likely causes (password-protected/encrypted, or corrupt file)
  and the remedy — making the SKILL.md "fails fast; tell the user to remove the
  password" claim true. No password *detector* is added (no new dependency).

- [x] **AC4 — Multi-frame images are surfaced.** When the image branch opens a
  multi-frame image (animated GIF, multi-page TIFF), `split_image.py` emits a
  `WARNING:` to **stderr** stating only the first frame is processed. The
  `recommend` JSON on stdout is unaffected (warning goes to stderr).

- [x] **AC5 — Tests + release hygiene.** A `test_reconcile.py` locks AC1 + AC2
  (unit + one real `python scripts/reconcile.py` subprocess invocation) and
  passes. The `converters` pack patch version is bumped (`pack.toml`,
  `plugin.json`, `marketplace.json` consistent — verified drift-clean via
  build-self). A `docs/product/changelog.md` `[Unreleased]` entry records the
  user-visible fixes.

## Boundaries

- **Always do:** keep the change to `packs/converters/.apm/skills/file-to-markdown/`
  (source, not projections) + changelog + version files; preserve the existing
  output schema and stdout markers.
- **Never do:** add a runtime dependency; introduce a timeout/page-limit policy;
  add enrichment, chunking, a general-image OCR mode, or a unified output
  contract (all RFC-deferred); edit projected `.claude/` paths by hand.

## Testing Strategy

- **AC1, AC2 — TDD:** unit tests on `reconcile.py`'s pure functions (red first),
  plus one end-to-end subprocess run of the documented `python scripts/reconcile.py`
  invocation asserting `ELEMENTS` count and `(unlabeled)` in the Markdown.
- **AC3 — goal-based/manual:** run `convert.py` against a deliberately corrupt
  file; observe actionable stderr + exit 1.
- **AC4 — goal-based/manual:** run `split_image.py` against a multi-frame GIF;
  observe the stderr warning and clean stdout.
- **AC5 — goal-based:** `pytest` green; `make build-self` leaves the tree
  drift-clean; changelog grep.

## Assumptions

- The agent almost always supplies `bbox_in_tile` per the strategy references, so
  bbox-less elements are an edge case; bbox-less same-`(type,name)` elements
  collapse to one cluster (can't be spatially distinguished) — acceptable and
  strictly better than the current drop. *Verified against the strategy
  reference files, which all instruct emitting `bbox_in_tile`.*
- A single node bisected at a tile edge (each tile reporting a partial
  `bbox_in_tile`) can yield two global bboxes with IoU below the merge
  threshold and therefore split into two elements — the inverse of the
  over-merge bug this PR fixes. This is the accepted tradeoff: a visible
  duplicate the user can reconcile beats silent loss of a distinct node. It is
  mitigated by the pipeline's 33% default tile overlap and the strategy
  guidance to emit whole-element bounding boxes.

### Declined patterns

- Tempted to add a `repeated_label` ambiguity record so repeated/split labels
  surface for review; declining — it flips `requires-review` on every diagram
  with a legitimately repeated label (noise), and review-surfacing belongs to
  the RFC's output-contract work. The faithful fix (show both) is enough here.
- Tempted to add a real PDF-encryption detector; declining — it needs a parser
  dependency and this PR is explicitly no-new-deps. An actionable error message
  satisfies the SKILL.md claim.
- Tempted to also fix `convert.py`'s image path for multi-frame; declining —
  that path feeds the Docling/ML tier the RFC will rework; the image branch
  (`split_image.py`) is the canonical one and gets the fix.
