# Spec: Guide metadata completion

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** docs/product/briefs/tech-site-completion.md
- **Discovery:** none
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

Readers can identify the purpose and ownership of every published guide before
opening it because each content page has reviewed title, summary, pack, and kind
metadata. Structural indexes stay explicitly outside the content contract, and
the emitted sites expose the reviewed metadata. Catalogue-format source moves
to its correct shared-reference owner while an explicit slug preserves its
existing public route; every other public route remains unchanged.

## Boundaries

### Always do

- Author every summary as editorial content that describes the guide's user
  outcome; do not derive it mechanically from the first paragraph.
- Keep metadata titles coherent with the existing H1 unless the separately
  approved title-clarity spec changes that title.
- Encode the five approved non-content exceptions explicitly and silently.
- Apply the 125 exact affected-page rows in
  [`metadata-decisions.md`](metadata-decisions.md) and preserve their six
  approved review batches.
- Move catalogue-format source to shared reference ownership while preserving
  `/docs/guides/_reference/catalogue-format/`.
- Correct the approved false opening in pack-journey authoring in the same
  content batch.

### Ask first

- Exempt any Markdown file beyond the approved five-file set.
- Change a guide title, route, alias, sidebar order, or content body beyond the
  exact catalogue move, compatibility slug, four title-spec changes, and
  pack-journey opening approved by this spec.
- Change the meaning or allowed values of the published guide schema.

### Never do

- Generate summaries, pack ownership, or guide kind from filenames or folders
  and treat that output as reviewed content.
- Move user-facing guides into the maintainer-only `docs/guides/` tree.
- Add a dependency or weaken the validator to suppress incomplete metadata.

## Testing Strategy

- Metadata completeness, schema validity, and the exact exception set use TDD
  in the existing guide validator tests.
- Generated metadata and route preservation use goal-based full-site build and
  rendered-output checks.
- Summary usefulness and title coherence use recorded editorial review because
  those are judgment-led content outcomes.

## Acceptance Criteria

- [ ] The incomplete-metadata backfill is exactly the 125 affected public pages
  in `metadata-decisions.md`; each receives its exact schema-valid `summary`,
  `pack`, and `kind`, while `title` is exact from that ledger except for the
  four replacements owned by `guide-title-clarity`.
- [ ] The only files exempt from public-guide metadata are
  `guides/AGENTS.md`, `guides/_shared/tutorials/README.md`,
  `guides/_shared/how-to/README.md`,
  `guides/_shared/reference/README.md`, and
  `guides/_shared/explanation/README.md`.
- [ ] The validator encodes those five paths as intentional non-content files
  and emits neither errors nor warnings for them.
- [ ] `tools/validate_guides.py` finishes with zero errors and zero warnings for
  the complete published-guide tree.
- [ ] Each metadata title matches its guide H1, except where the independently
  approved `guide-title-clarity` spec supplies the replacement title.
- [ ] Each summary is human-reviewed, outcome-led, specific to its guide, and
  does not merely repeat the title or opening sentence.
- [ ] Each `pack` value identifies the owning pack or approved shared ownership,
  and each `kind` matches the guide's Diátaxis location.
- [ ] `guides/_reference/catalogue-format.md` moves to
  `guides/_shared/reference/catalogue-format.md` with `_shared` ownership and
  `reference` kind, while an explicit slug preserves
  `/docs/guides/_reference/catalogue-format/`; the old structural group is
  removed only if navigation and route checks prove it empty and safe.
- [ ] The opening of
  `guides/_shared/how-to/pack-journey-authoring.md` is the approved public-guide
  wording in `metadata-decisions.md` and no longer claims the page is an
  internal `docs/guides/` maintainer guide.
- [ ] Existing optional `slug`, `order`, and `aliases` values remain unchanged
  unless a source is already invalid under `contracts/guide.schema.json`.
- [ ] The built marketing and documentation sites enumerate all 125 affected
  pages and expose each reviewed title and summary wherever their current
  page-list, search, or description contracts consume guide metadata.
- [ ] Complete public-guide coverage—including pages that already had valid
  metadata before this backfill—proves every pre-change route, alias, and
  navigation destination still resolves, and the combined rendered-link
  checker reports no broken page or fragment.

## Assumptions

- Technical: the current validator reports 130 warnings, comprising 125
  affected publishable guide files without complete metadata plus the five
  approved non-content files (source: repository validation on 2026-08-17).
- Technical: `contracts/guide.schema.json` and `tools/validate_guides.py` are
  the living metadata contract and validator (source: repository inspection on
  2026-08-17).
- Product: exactly five files are structural or non-content exceptions and all
  other published-guide Markdown receives metadata (source: user confirmation
  2026-08-17).
- Product: summaries and metadata classification remain human-reviewed rather
  than generated; the exact accepted values live in
  `metadata-decisions.md` (source: user approval 2026-08-17).
- Product: catalogue-format is public shared reference content and its source
  ownership moves while its existing route stays fixed (source: user approval
  2026-08-17).
- Process: all other public routes and navigation contracts remain fixed
  (source: `docs/product/briefs/tech-site-completion.md`).
