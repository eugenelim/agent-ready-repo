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
- No dependency, public route, alias, or navigation destination changes.

## Construction tests

**Integration tests:** build the marketing site and Starlight site in their
required order, inspect emitted metadata for representative shared and
pack-owned guides, then run the combined page-and-fragment checker.

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

### Data & schema

- Required fields keep the types and vocabulary defined by
  `contracts/guide.schema.json`. Optional routing fields remain untouched.
  Traces to: AC1, AC7, AC8 · `contracts/guide.schema.json`.

### Interfaces & contracts

- `tools/validate_guides.py` consumes source frontmatter; the site generator
  projects validated metadata into renderer inputs and emitted pages. Traces
  to: AC3, AC4, AC9, AC10 · `contracts/guide.schema.json`.

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

### T2: Shared and root guide metadata is complete and editorially approved

**Depends on:** T1

**Touches:** guides/README.md, guides/_shared/**/*.md, guides/_reference/**/*.md

**Tests:**
- Goal-based: run the validator against the batch after each review round (AC1, AC4-AC7).
- Visual/manual QA: record an editorial checklist covering title/H1 coherence, outcome-led
  summary, pack ownership, and kind (AC5-AC7).

**Approach:**
- Author metadata for publishable shared and reference content.
- Leave the five structural exceptions and optional route fields unchanged.

**Done when:** the batch has no validation findings and every summary has a
recorded human approval.

### T3: Pack-owned guide metadata is complete in bounded review batches

**Depends on:** T1

**Touches:** guides/*/**/*.md

**Tests:**
- Goal-based: run the validator for each alphabetically bounded batch (AC1, AC4-AC8).
- Visual/manual QA: record the same editorial checklist used by T2 for every changed guide.

**Approach:**
- Split pack-owned guides into review-sized alphabetical batches.
- Coordinate the four title-owned files with `guide-title-clarity` so one
  approved title is applied once.

**Done when:** all pack batches have zero findings and recorded editorial
approval.

### T4: Emitted guide metadata and all routes satisfy the published contract

**Depends on:** T2, T3, spec:guide-title-clarity/T2

**Touches:** tools/test_build_site_routing.py, tools/test_check_rendered_site_links.py

**Tests:**
- Goal-based: assert representative shared and pack pages emit the reviewed title and
  summary in their current consumer surfaces (AC9).
- Goal-based: build both sites, verify the pre-change route inventory, and run combined
  page-and-fragment checking (AC10).

**Approach:**
- Prefer emitted-behavior assertions over source-shape checks.
- Add a seeded broken metadata/route case to prove each construction test can
  fail.

**Done when:** full builds, emitted metadata assertions, route inventory, and
combined link checks pass.

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
