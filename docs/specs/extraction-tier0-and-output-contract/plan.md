# Plan: extraction-tier0-and-output-contract

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog.

## Approach

Land the **contract and the defensive helpers first**, then the **Tier-0
extractors** beneath a small input-routing dispatch, then the **D7 formats**,
then **release**.

The riskiest and most valuable piece is the unified output contract (AC1–AC3):
it is the interface every downstream slice (`extraction-general-image-mode`,
`extraction-higher-tiers`) builds on, and getting the additive-not-breaking shape
right (AC2) is what protects existing image-branch consumers. So T1 extends the
existing hand-rolled emitter into a single shared builder and its byte-parity test
locks the image branch's pre-existing block before any extractor changes.

`convert.py` has **two paths in one output shape** today — a document path and an
image-via-Docling path (its `SUPPORTED`/`IMAGE_EXTS` sets, one `convert_file`);
`reconcile.py` is the separate diagram/image shape. `convert.py` grows a thin
**tier/format dispatch** in front of today's Docling call: route by input class to
a Tier-0 extractor when one applies, fall through to Docling (Tier 2) otherwise,
wrap every path's output in the shared contract, and write via the confinement
helper. `reconcile.py` is refactored to emit the same contract (T1). Tier-0
extractors are independent (PDF, Office, D7) so they parallelize after the
dispatch, builder, and defensive helpers exist. Docling stays the fall-through and
its returned body is passed through unmodified (AC10).

**Defensive parsing (AC9) and output confinement (AC12) are built early (T2,
before the readers)** so every reader routes through the real guards from its
first write — not stubbed-then-hardened. `msg-to-markdown` is **not** in this plan
— it is a Node.js skill; its contract adoption is a follow-on Python-port slice
(backlog: `extraction-msg-to-markdown-python-contract`).

Verification is majority TDD on the pure functions (frontmatter builder, per-
format Markdown mappers, sparse-text assessor, defensive guards) plus one
end-to-end subprocess run per documented invocation — the same shape the
preceding `converters-extraction-fixes` spec used.

## Constraints

- **RFC-0058** (Accepted) — the tier model, the sanctioned Tier-0 dep (`pypdf`),
  and the "Tier 3 never auto-reached / no egress" rule. This spec is D2+D3+D7.
- **ADR-0045** — capability-tiered, presence-checked, degrade-don't-fail-closed.
- **ADR-0034** — no bundled models / vendor data.
- The sibling `markdown-to-*` pip-on-demand pattern is the model for Office libs.
- Converters is a **user-scope-default pack**: it is not in this repo's self-host
  projection, so the version bump drifts `marketplace.json` and the gate is
  `lint-packs` + `validate` + `build` + `pytest` (not `build-self`/`pre-pr`).

## Construction tests

Most tests live per-task below. Cross-cutting:

- **Integration:** one end-to-end subprocess run of `python scripts/convert.py`
  per input class (digital PDF, docx, xlsx, pptx, HTML, EPUB, CSV, ODT, `.eml`)
  asserting Markdown body + unified frontmatter; one run of the `reconcile.py`
  image branch asserting the pre-existing frontmatter is intact plus the two new
  keys.
- **Manual verification:** exercise SKILL.md's documented default invocation on a
  real digital PDF in an environment with Docling **absent** and confirm Tier-0
  produces Markdown (the locked-down-org happy path this spec exists for).

## Design (LLD)

Shape: **service**. Stack: Python stdlib + ordinary parser libraries; no ML.
Scripts live under `packs/converters/.apm/skills/file-to-markdown/scripts/`.

### Interfaces & contracts
The output **frontmatter contract** is the interface this spec defines. Required
keys (AC1): `contract-version` (str), `source-file` (str), `content-type` (str),
`tier` (str enum: `0-no-ml` | `1-agent-vision` | `2-approved-ml` | `3-managed-api`),
`ingestion-date` (ISO-8601), `extraction-confidence` (`high|medium|low`),
`requires-review` (bool). Branch-specific keys ride alongside (the image branch's
`content-category`, `diagram-type`, `processing.*`, `ingestion-quality.*` — AC2).
The document branch's stdout markers (`OUTPUT`/`LINES`/`WORDS`) are preserved.
Traces to: AC1, AC2, AC3 · contract: none (frontmatter, pinned by ACs).

### Data & schema
`extraction-confidence` and `requires-review` are the quality signal. The image
branch keeps them nested under `ingestion-quality`; the shared builder emits the
same nested block for the document branch, and the two new keys
(`contract-version`, `tier`) are top-level on every branch. `contract-version`
starts at `"1.0"`. Traces to: AC1, AC2, AC6.

### Component / module decomposition
- **New:** `contract.py` — the shared frontmatter builder, extending the skill's
  existing **hand-rolled stdlib** emitter (no PyYAML): pure; takes tier, source,
  confidence, review flag, branch-extras → a fenced YAML block whose values are
  escaped/quoted so extracted content cannot break out, with the body kept below
  the closing `---` (AC8). Reused by both output shapes: `convert.py` (document +
  image-via-Docling) and `reconcile.py` (diagram branch).
- **New:** `_safe_xml` / `_safe_zip` / `_safe_out_path` helpers — XXE-safe XML
  (stdlib `xml.etree`/`defusedxml`), multi-axis decompression-bomb guard
  (ratio + cumulative-bytes + entry-count + nested-archive), and realpath +
  component-containment output confinement (AC9, AC12). Built **before** the
  readers so every reader is routed through the real guards from first write.
- **New:** Tier-0 extractors, one function per input class: `_extract_pdf`
  (pypdf, via `--check`), `_extract_docx`/`_extract_xlsx`/`_extract_pptx`
  (ordinary-lib → stdlib `_safe_zip`/`_safe_xml` fallback), and the D7 readers
  (`_extract_html`, `_extract_epub`, `_extract_csv`, `_extract_odf`,
  `_extract_eml`). Each enforces a coarse resource ceiling (AC13).
- **Modified:** `convert.py` gains a `dispatch(path)` that routes by extension/
  sniffing to a Tier-0 extractor or falls through to Docling, then wraps output
  in `contract.py`. **Reused/untouched:** the Docling call itself — the body it
  returns is passed to the builder unmodified (AC10, in-process identity).
Traces to: AC3, AC4, AC5, AC7, AC8, AC9, AC10, AC12, AC13.

### State & control flow
Tier detection/degradation: `dispatch` picks the input class; for PDFs it tries
Tier 0 (`pypdf`), and on sparse/empty text (AC6) marks low-confidence +
requires-review and names Tier 1 as the escalation target (Tier 1 itself ships in
`extraction-general-image-mode`); for Office/D7 it uses the Tier-0 extractor,
degrading ordinary-lib → stdlib. Docling is the fall-through when no Tier-0
extractor applies or when the caller selects it. Tier 3 is unreachable from this
code (no egress). Traces to: AC4, AC5, AC6, AC10.

### Failure, edge cases & resilience
- Sparse/empty PDF text → low confidence + requires-review, not silent output (AC6).
- Missing Office library → stdlib `zipfile`+XML fallback, not failure (AC5).
- Untrusted XML → external entities disabled (AC9); zip → decompression-bomb
  guard (AC9).
- Corrupt/unsupported file → the existing actionable-failure path
  (`converters-extraction-fixes` AC3) is preserved.
Traces to: AC5, AC6, AC9.

### Quality attributes (NFRs)
- **No-ML floor:** no import of Docling or any model on the Tier-0 path (AC4/AC5)
  — asserted by a test that the Tier-0 code path imports neither `docling` nor a
  known OCR/model package.
- **No egress:** no network I/O anywhere in the skill (Never-do); grep/AST guard.
Traces to: AC4, AC5.

## Tasks

### T1: Shared unified-contract frontmatter builder
**Depends on:** none
**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/contract.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_contract.py

**Tests:**
- Unit: builder given (tier, source-file, content-type, confidence, review,
  extras) returns a YAML block with all required keys (AC1) and the extras merged
  under the correct nesting.
- Unit: `contract-version` present and equals `"1.0"`; `tier` is one of the enum.
- Unit (AC2 byte-parity): the builder applied to the image branch's current
  extras produces a block byte-identical to today's `reconcile.py` frontmatter
  except for the two added keys — same keys, **same order**, same quoting (proves
  the refactor didn't reorder/re-quote).
- Unit (AC8 injection-safety): building frontmatter for a source whose values /
  extras contain `---`, newlines, and `contract-version: 9.9` produces a block
  where the hand-rolled emitter escapes/quotes the hostile strings, the real
  builder values win, and the closing `---` fence is intact — the body cannot
  inject or truncate the contract.

**Approach:**
- Add `contract.py` with `build_frontmatter(...)` (pure) and the `tier` enum
  constants by **extending `reconcile.py`'s existing hand-rolled `_yaml_block`
  emitter** (no PyYAML). The existing emitter escapes `\` and `"` but **not
  newlines** — a value with `\n` currently emits a raw newline inside a `"..."`
  scalar and breaks the fence (the AC8 vector); the builder must add
  **newline-escaping**. This is **byte-neutral for AC2**: no current image-branch
  frontmatter value carries a newline, so escaping it changes no existing bytes.
  Repoint `reconcile.py` at the shared builder so its output is byte-unchanged
  except for the two additive keys (AC2).

**Done when:** `test_contract.py` is green, the AC2 byte-parity test passes, and
`reconcile.py` emits via the shared builder.

### T2: Defensive helpers — XXE-safe XML, decompression-bomb guard, output-path confinement
**Depends on:** none
**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/safe_io.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_safe_io.py

**Tests:**
- Unit: `_safe_xml` parsing a document with an external entity does **not**
  resolve it (no file/network fetch); uses stdlib `xml.etree`/`defusedxml` only (AC9).
- Unit: `_safe_zip` refuses, before full decompression, a zip that trips each
  axis — size ratio, cumulative-bytes cap, entry-count cap (AC9); and reads only
  known-name members by path without recursing into an embedded archive member
  (the EPUB/ODF reconciliation, AC7/AC9).
- Unit: `_safe_zip` reading an entry named `../evil` never yields a filesystem
  path (path-join guard — reads are in-memory by known name, AC9).
- Unit: `_safe_out_path` refuses a target escaping the confinement root via `..`
  traversal, via a symlink, and via the **sibling-prefix** case (`<root>-evil` vs
  root `<root>`); accepts an in-root path (AC12).

**Approach:**
- Add `safe_io.py` with `_safe_xml`, `_safe_zip`, `_safe_out_path` (realpath +
  path-component containment — **not** `str.startswith` — mirroring
  `markdown-to-office-publishing`). Built first so every reader (T5/T6) and every
  write routes through the real guards.

**Done when:** every guard test passes.

### T3: Document-branch dispatch + contract wrapping + confined write
**Depends on:** T1, T2
**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/convert.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_convert.py

**Tests:**
- Unit: `dispatch(path)` routes each extension to the right extractor and falls
  through to Docling for unhandled classes.
- E2E: `python scripts/convert.py <docling-handled file>` still works and now
  emits the unified frontmatter with `tier: "2-approved-ml"` (AC3).
- Unit: the output `.md` is written via `_safe_out_path` (AC12).
- Unit (AC8 full-document): a document whose extracted **body** contains `---` and
  `contract-version:` lines, run through the assemble+write path, produces output
  a frontmatter parser reads as the builder's leading block only — the body's
  `---` is content, not a second frontmatter.
- Unit (dispatch guard order): a zip renamed `.csv` still hits `_safe_zip` (each
  parser applies its own format guard regardless of how dispatch classified it).

**Approach:**
- Introduce `dispatch(path)` in `convert.py`; wrap every return path through
  `contract.build_frontmatter(...)`; write via `_safe_out_path`; preserve
  `OUTPUT`/`LINES`/`WORDS` markers. Dispatch selects the parser, but **every
  parser applies its own format guard** (zip-based parsers always route through
  `_safe_zip`), so a misleading extension can't bypass the matching guard —
  defence-in-depth backed by the AC13 ceiling.

**Done when:** the E2E run emits frontmatter above the Markdown body, the write is
confined, the body-injection parse test passes, and the Docling path is unchanged.

### T4: Tier-0 digital-PDF extraction (pypdf) + sparse-text self-assessment + ceiling
**Depends on:** T3
**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/convert.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_convert.py

**Tests:**
- Unit: `_extract_pdf` returns text for a digital PDF fixture with `tier:
  "0-no-ml"` and imports neither `docling` nor an OCR model (AC4).
- Unit: an empty/near-empty text result yields `extraction-confidence: low` +
  `requires-review: true` and names Tier 1 as the escalation target (AC6).
- Unit: a PDF exceeding the page/byte ceiling is refused with `requires-review`
  rather than parsed unbounded (AC13).
- E2E: `python scripts/convert.py <digital.pdf>` with Docling importable OR not
  produces Tier-0 Markdown.

**Approach:**
- Add `_extract_pdf` using `pypdf` behind the sibling `--check`/`PIP_INSTALL`
  probe convention; add a sparse-text threshold assessor and a coarse ceiling.

**Done when:** the unit tests pass and the E2E run shows `tier: "0-no-ml"`.

### T5: Tier-0 Office extraction (docx/xlsx/pptx, ordinary-lib → stdlib)
**Depends on:** T2, T3
**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/convert.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_convert.py

**Tests:**
- Unit: `_extract_docx`/`_extract_xlsx`/`_extract_pptx` map to Markdown using the
  ordinary lib when present (AC5).
- Unit: with the ordinary lib monkeypatched absent, the extractor uses the stdlib
  `_safe_zip`/`_safe_xml` fallback and still returns Markdown (AC5, AC9).
- Unit: the ceiling (rows/slides/bytes) refuses an oversized input (AC13).
- E2E: `python scripts/convert.py evals/files/sample.docx` produces Tier-0
  Markdown + frontmatter.

**Approach:**
- Add the three extractors + a `cmd_check()`/`PIP_INSTALL` probe mirroring
  `markdown-to-*`; the stdlib OOXML fallback routes through the T2 `_safe_zip`/
  `_safe_xml` helpers (no stub — the real guards already exist).

**Done when:** both lib and stdlib-fallback unit tests pass and the docx E2E run
succeeds.

### T6: D7 format coverage (HTML, EPUB, CSV/TSV, ODT/ODS/ODP, `.eml`)
**Depends on:** T2, T3
**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/convert.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_convert.py

**Tests:**
- Unit per family: the reader returns Markdown from a small real sample (HTML via
  stdlib `html.parser`; EPUB/ODF via `_safe_zip`+`_safe_xml`; CSV/TSV via stdlib
  `csv`; `.eml` via stdlib `email`), each within the ceiling (AC13).
- E2E per family: `python scripts/convert.py <sample>` emits Markdown + unified
  frontmatter (AC7).

**Approach:**
- Add one reader per family, stdlib-first; zip/XML families use the T2 helpers;
  register each in `dispatch`.

**Done when:** each family's unit + E2E run is green with no ML import.

### T7: Docling (Tier-2) path gains the additive contract keys
**Depends on:** T1, T3
**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/convert.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_convert.py

**Tests:**
- Unit (in-process identity): the Docling body handed to `build_frontmatter`
  equals the body `DocumentConverter().convert(...).export_to_markdown()` returned
  — the builder wraps, never rewrites — and the frontmatter carries
  `tier: "2-approved-ml"` + `contract-version` (AC10).

**Approach:**
- Ensure the Docling branch wraps through `contract.build_frontmatter` with
  `tier="2-approved-ml"`; no change to the Docling call or its output body.

**Done when:** the identity assertion passes and the only delta is the two keys.

### T8: SKILL.md docs, tests aggregation, release hygiene
**Depends on:** T1-T7
**Touches:** packs/converters/.apm/skills/file-to-markdown/SKILL.md, packs/converters/pack.toml, packs/converters/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

**Tests:**
- Goal-based: `lint-packs`, `validate`, `build`, and `pytest` (in
  `packages/agentbundle` and the pack scripts) are green; `pack.toml` /
  `plugin.json` / `marketplace.json` version-consistent (regenerated, not
  hand-edited); changelog grep finds the `[Unreleased]` entry.
- Goal-based (AC11 default-one-command): grep SKILL.md's quickstart asserts the
  documented default invocation is still the single
  `python scripts/convert.py "<input-file>"` form.

**Approach:**
- Document the four tiers, the new formats, and the contract as progressive
  disclosure in SKILL.md, keeping the default invocation one command; bump the
  pack **minor** version (0.2.3 → 0.3.0) across the three manifests via the pack
  build; add the changelog entry.

**Done when:** the gate suite is green, the default-invocation grep passes, and
the manifests are drift-clean.

## Rollout

- **Delivery:** additive. Today's invocation stays valid; Docling (Tier 2) is
  what runs today and is unchanged (AC10). The floor and the contract are new
  behavior layered beneath it. No data migration, no published event.
- **Reversibility:** the change is code-only in one skill (`file-to-markdown`);
  rollback is a revert. The one non-trivial forward commitment is the frontmatter
  `contract-version` — once consumers key on it, changing its meaning is a
  contract change (hence the version field).
- **Infrastructure / external systems:** none — no egress, no new services.
- **Deployment sequencing:** contract builder (T1) before any extractor; publish
  is the pack version bump (T8). No consumer-before-producer ordering beyond that.

## Risks

- **Tier-0 Office fidelity is lower than Docling's.** Stdlib OOXML extraction
  loses layout/tables Docling would keep. Accepted: the floor's job is a working
  path where ML is banned, not parity; `extraction-confidence` signals it.
- **`pypdf` version/API drift.** Pin the version at implementation and gate the
  import through the `--check` probe so a missing/old lib fails clean.
- **PR size.** D2+D3+D7 is broad. If the PR grows past ~400 lines, split D7 (T6)
  into a follow-on slice — the contract + PDF + Office floor is the load-bearing
  minimum; D7 formats are independent tasks. Note the split in this changelog if
  taken.
- **Pip-on-demand deps sit outside lockfile SCA.** `pypdf` and the Office libs
  resolve at runtime, so Dependabot / `pip-audit` over the repo lockfile won't see
  them (security-reviewer note). Mitigate by pinning a floor version in the
  `PIP_INSTALL` string and documenting the SCA gap; a CI fuzz target over
  `_safe_xml`/`_safe_zip` is a recommended follow-on hardening.

## Changelog

- 2026-06-30: initial plan — floor-first slice of RFC-0058 (D2 Tier-0 + D3
  unified contract + D7 formats); T1 contract builder first, extractors
  parallelize after dispatch, defensive-parsing and release hygiene last.
- 2026-06-30: spec-stage review (round 1) — removed the `msg-to-markdown` task (it
  is Node.js; contract adoption is a follow-on Python-port slice, backlog
  `extraction-msg-to-markdown-python-contract`); clarified `convert.py` carries
  both a document and an image-via-Docling surface; added frontmatter-injection
  safety and zip-slip/output-path notes. 9 tasks → 8.
- 2026-06-30: spec-stage review (round 2, adversarial + security) — resolved the
  serializer tension: **keep the hand-rolled stdlib emitter (no PyYAML), make it
  injection-safe by escaping** instead of `yaml.safe_dump` (which adds a dep and
  reorders keys, breaking AC2/AC10 byte-stability). Reframed to **two output
  shapes** not three; **moved the defensive helpers to T2 (before the readers)**
  to close the unguarded-window DAG hazard; added `_safe_out_path`; extended the
  bomb guard to ratio + cumulative + entry-count + nested; added **AC12
  output-path confinement** and **AC13 resource ceiling**; reframed AC10 to an
  **in-process identity** assertion (Docling output is unpinnable); pinned the
  **XXE parser allowlist** and the ordinary-lib transitive-`lxml` caveat; fixed
  `pypdf` to pip-on-demand. 11 ACs → 13; tasks stay 8 (reordered).
- 2026-06-30: spec-stage review (round 3, no blockers — polish only) — AC8 now
  pins **newline-escaping** as the load-bearing emitter fix (the existing emitter
  escapes `\`/`"` but not `\n`) and adds a **full-document body-injection** parse
  test; AC12 adds the **sibling-prefix** confinement case; AC9 reworded "zip-slip"
  → **path-join guard** (reads are in-memory) and reconciled **EPUB/ODF** legit
  members vs. the nested-archive axis (read known-name members, never recurse);
  added a **dispatch guard-order** test (renamed extension still hits its format
  guard); D7 Testing-Strategy mode label aligned to "E2E + unit mappers".
