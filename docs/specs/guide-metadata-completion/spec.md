# Spec: Guide metadata completion

- **Status:** Shipped
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

- [x] The incomplete-metadata backfill is exactly the 125 affected public pages
  in `metadata-decisions.md`; each receives its exact schema-valid `summary`,
  `pack`, and `kind`, while `title` is exact from that ledger except for the
  four replacements owned by `guide-title-clarity`.
- [x] The five exempt files remain mirrored and published — e.g.
  `/docs/guides/AGENTS/` and `/docs/guides/_shared/how-to/` are reachable — so five
  emitted pages carry no `summary` while the other 188 do. Recorded so the
  exemption's blast radius is on the record rather than implied by "structural
  indexes stay outside the content contract".
- [x] The only files exempt from public-guide metadata are
  `guides/AGENTS.md`, `guides/_shared/tutorials/README.md`,
  `guides/_shared/how-to/README.md`,
  `guides/_shared/reference/README.md`, and
  `guides/_shared/explanation/README.md`.
- [x] The validator encodes those five paths as intentional non-content files
  and emits neither errors nor warnings for them.
- [x] `tools/validate_guides.py` finishes with zero errors and zero warnings for
  the complete published-guide tree.
- [x] Each metadata title matches its guide H1, except where the independently
  approved `guide-title-clarity` spec supplies the replacement title.

  "Matches" is `tools/lint-guide-titles.py`'s definition — NFKC, backticks and
  asterisks stripped, whitespace collapsed, casefolded, trailing punctuation
  removed — and that gate is green. Its printed count is the **walk size** (193 both
  before and after), which is invariant to whether any comparison ran, so it is not
  evidence of coverage; the number that moved is the count of files actually
  compared, which `check_file` skips for any file without a frontmatter `title`:
  **54 before, 179 after**. All 125 ledger titles are byte-identical to their H1s.
  Recorded because a stricter byte-equality reading finds five mismatches
  (`guides/release-engineering/README.md`,
  `guides/frontend-engineering/reference/performance-targets.md`,
  `guides/_shared/how-to/install-agentbundle-from-clone.md`,
  `guides/_shared/how-to/preview-install-or-upgrade.md`,
  `guides/core/how-to/adapt-to-project.md`) that differ only by case, inline-code
  markers or a hyphen. All five predate this spec, none is a ledger row, and the
  gate accepts them; they are named here so a later reader does not rediscover
  them as this change's doing.
- [x] Each summary is human-reviewed, outcome-led, specific to its guide, and
  does not merely repeat the title or opening sentence.
- [x] Each `pack` value identifies the owning pack or approved shared ownership,
  and each `kind` matches the guide's Diátaxis location.
- [x] `guides/_reference/catalogue-format.md` moves to
  `guides/_shared/reference/catalogue-format.md` with `_shared` ownership and
  `reference` kind, while an explicit slug preserves
  `/docs/guides/_reference/catalogue-format/`; the old structural group is
  removed only if navigation and route checks prove it empty and safe.
- [x] The opening of
  `guides/_shared/how-to/pack-journey-authoring.md` is the approved public-guide
  wording in `metadata-decisions.md` and no longer claims the page is an
  internal `docs/guides/` maintainer guide.
- [x] Existing optional `slug`, `order`, and `aliases` values remain unchanged
  unless a source is already invalid under `contracts/guide.schema.json`.
- [x] Applying the reviewed titles changes **125 sidebar labels**, reorders items in
  **9 kind buckets**, and moves one page between groups. Measured with the SHIPPING
  label chain, against `origin/main`'s tree and baseline.

  This required removing **84 entries from `guide-nav-baseline.toml`** (101 → 17).
  That registry has highest precedence in `_guide_label`, so without the removal the
  curated titles reached the page but not navigation — 84 of the 125 kept their
  pre-change sidebar label, leaving the criterion below unmet for two thirds of the
  set. `guide-nav-baseline.toml`'s own header defines the protocol: "a page gains
  `title:` frontmatter, its entry is removed here deliberately … Removing an entry is
  the reviewable act that adopts a page's own title." Every one of the 84 had a label
  differing from the title replacing it, so none was a no-op.

  Reordered buckets: Architect/Tutorials, Cross-cutting/{Explanation,How-to},
  Desk Research/How-to, Experience Design/How-to, Governance Extras/How-to,
  Product Discovery/How-to, The Build Loop (core)/{Explanation,How-to}. Group move:
  `catalogue-format` from the removed "Reference material" to Cross-cutting/Reference.

  Approved 2026-08-18 against the Ask-first boundary on sidebar order. An earlier
  revision of this AC recorded 11 buckets and cited two examples that do not change,
  because the measurement passed an empty baseline and so bypassed the highest-
  precedence layer; the numbers above are from the shipping chain.
- [x] The built marketing and documentation sites enumerate all 125 affected
  pages and expose each reviewed title and summary wherever their current
  page-list, search, or description contracts consume guide metadata.
- [x] Complete public-guide coverage—including pages that already had valid
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
