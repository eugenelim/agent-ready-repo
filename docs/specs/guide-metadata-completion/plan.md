# Plan: Guide metadata completion

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; substantive changes are recorded below.

## Approach

Lock the validator and exception contract first, then author metadata in
reviewable editorial batches. Each batch is schema-checked before projection;
the final pass builds both sites and verifies emitted descriptions, routes, and
links. The repetitive file edits are deterministic only after each title,
summary, pack, and kind decision has received human review.

## Constraints

- `contracts/guide.schema.json` remains the metadata authority.
- User-facing guides remain under `guides/`; `docs/guides/` is maintainer-only.
- `guide-title-clarity` owns the four approved title changes.
- [`metadata-decisions.md`](metadata-decisions.md) is the accepted 125-row
  editorial ledger; implementation does not regenerate or reclassify it.
- Catalogue-format moves to shared reference source ownership while an
  explicit slug preserves its old route. No other public route, alias, or
  navigation destination changes.

## Construction tests

**Integration tests:** build the marketing site and Starlight site in their
required order, enumerate and inspect emitted metadata for all 125 affected
pages, then run complete public-guide and combined page/fragment coverage.

**Manual verification:** an editorial reviewer records approval for every
summary and classification batch; emitted representative pages are checked for
useful, non-duplicative descriptions.

## Design (LLD)

### Design decisions

- An explicit allowlist identifies the five structural files; folder-wide or
  basename-wide exemptions are rejected because they could hide future public
  content. Traces to: AC2-AC4.
- Metadata is authored in bounded batches and reviewed as content; automatic
  extraction is rejected because it cannot prove editorial usefulness. Traces
  to: AC1, AC5-AC7.
- Source ownership and public route identity are separate: catalogue-format
  moves to `_shared/reference`, while an explicit slug preserves its current
  emitted route. Traces to: AC8.

### Data & schema

- Required fields keep the types and vocabulary defined by
  `contracts/guide.schema.json`. Optional routing fields remain untouched.
  Traces to: AC1, AC7, AC10 · `contracts/guide.schema.json`.

### Interfaces & contracts

- `tools/validate_guides.py` consumes source frontmatter; the site generator
  projects validated metadata into renderer inputs and emitted pages. Traces
  to: AC3, AC4, AC11, AC12 · `contracts/guide.schema.json`.

## Tasks

### T1: The validator proves complete metadata and only the five approved exceptions

**Depends on:** none

**Touches:** tools/validate_guides.py, tools/test_validate_guides.py

**Tests:**
- TDD: add failing fixtures for each missing required field and for a sixth
  attempted exception (AC1-AC4).
- TDD: prove all five exact structural paths pass without a warning, while the same
  basename at another path does not (AC2, AC3).

**Approach:**
- Replace incidental warnings for the five files with one explicit path
  allowlist.
- Keep every publishable Markdown file subject to the schema.

**Done when:** the focused validator tests fail on seeded omissions and pass for
the exact approved exception set.

### T2: Batch 1 completes root, shared, and catalogue metadata

**Depends on:** T1

**Touches:** guides/README.md, guides/_shared/**/*.md, guides/_reference/**/*.md

**Tests:**
- Goal-based: compare all 23 rows field-by-field with the accepted ledger and
  run the validator and global duplicate scan (AC1, AC4-AC7).
- Goal-based: prove the catalogue-format source move preserves its existing
  route and navigation behavior (AC8).
- Visual/manual QA: verify the pack-journey opening exactly matches its approved
  correction and no other body copy changes (AC9).

**Approach:**
- Apply only ledger batch 1.
- Move catalogue-format to shared reference ownership, set the compatibility
  slug, and remove the empty old group only after route/navigation proof.
- Apply the one approved pack-journey opening correction. Leave the five
  structural exceptions and all other body and optional routing fields alone.

**Done when:** all 23 rows match, validation and duplicate checks pass, the old
route resolves, and the body diff is limited to the approved opening.

### T3: Batch 2 completes Architect, Atlassian, and Catalogue Curation

**Depends on:** T2

**Touches:** guides/architect/**/*.md, guides/atlassian/**/*.md, guides/catalogue-curation/**/*.md

**Tests:**
- Goal-based: compare all 23 rows field-by-field with ledger batch 2, then run
  the validator and global duplicate scan (AC1, AC4-AC7).

**Approach:**
- Apply only ledger batch 2 and make no body edits.

**Done when:** all 23 rows match and the scoped and global checks pass.

### T4: Batch 3 completes Contracts, Converters, and Core

**Depends on:** T3

**Touches:** guides/contracts/**/*.md, guides/converters/**/*.md, guides/core/**/*.md

**Tests:**
- Goal-based: compare all 24 rows field-by-field with ledger batch 3, then run
  the validator and global duplicate scan (AC1, AC4-AC7).

**Approach:**
- Apply only ledger batch 3; coordinate any title-owned row with
  `guide-title-clarity` so the approved title is applied once.

**Done when:** all 24 rows match and the scoped and global checks pass.

### T5: Batch 4 completes six pack groups

**Depends on:** T4

**Touches:** guides/credential-brokers/**/*.md, guides/desk-research/**/*.md, guides/experience-design/**/*.md, guides/figma/**/*.md, guides/frontend-engineering/**/*.md, guides/github/**/*.md

**Tests:**
- Goal-based: compare all 22 rows field-by-field with ledger batch 4, then run
  the validator and global duplicate scan (AC1, AC4-AC7).

**Approach:**
- Apply only ledger batch 4; coordinate any title-owned row with
  `guide-title-clarity` so the approved title is applied once.

**Done when:** all 22 rows match and the scoped and global checks pass.

### T6: Batch 5 completes five pack groups

**Depends on:** T5

**Touches:** guides/governance-extras/**/*.md, guides/linear/**/*.md, guides/monorepo-extras/**/*.md, guides/product-documentation/**/*.md, guides/product-strategy/**/*.md

**Tests:**
- Goal-based: compare all 17 rows field-by-field with ledger batch 5, then run
  the validator and global duplicate scan (AC1, AC4-AC7).

**Approach:**
- Apply only ledger batch 5; coordinate any title-owned row with
  `guide-title-clarity` so the approved title is applied once.

**Done when:** all 17 rows match and the scoped and global checks pass.

### T7: Batch 6 completes Product Engineering

**Depends on:** T6

**Touches:** guides/product-engineering/**/*.md

**Tests:**
- Goal-based: compare all 16 rows field-by-field with ledger batch 6, then run
  the validator and global duplicate scan (AC1, AC4-AC7).

**Approach:**
- Apply only ledger batch 6; coordinate any title-owned row with
  `guide-title-clarity` so the approved title is applied once.

**Done when:** all 16 rows match and the scoped and global checks pass.

### T8: Emitted guide metadata and all routes satisfy the published contract

**Depends on:** T7, spec:guide-title-clarity/T2

**Touches:** tools/test_build_site_routing.py, tools/test_check_rendered_site_links.py

**Tests:**
- Goal-based: enumerate all 125 affected ledger rows and assert each emitted page uses
  the reviewed title and summary in every current consumer surface (AC11).
- Goal-based: build both sites, enumerate the complete public-guide route
  inventory—including already compliant pages—and run combined page-and-
  fragment checking, including catalogue-format's compatibility route and
  unchanged aliases (AC8, AC12).

**Approach:**
- Prefer emitted-behavior assertions over source-shape checks.
- Add a seeded broken metadata/route case to prove each construction test can
  fail.

**Done when:** full builds, all-125 affected-page metadata assertions, complete
public-guide route/alias inventory, and combined link checks pass.

## Rollout

Ship as content-only batches followed by the emitted-site verification task.
Rollback is a normal source revert; there is no infrastructure, migration, or
external-system change.

## Risks

- Large editorial batches can conceal generic or duplicated summaries; bounded
  review batches and recorded approvals reduce that risk.
- Title work could be applied twice; the explicit cross-spec dependency makes
  `guide-title-clarity` authoritative for its four files.

## Changelog

- 2026-08-17: initial plan after approval of the five-file exception contract.
- 2026-08-17: fixed the 125-row ledger, six review batches,
  catalogue-format ownership move with route compatibility, same-page content
  correction, and exhaustive emitted-output proof.
