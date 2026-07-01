# Spec: extraction-tier0-and-output-contract

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0058, ADR-0045, ADR-0034 (no bundled per-vendor data / models), RFC-0007 (the converters pack this changes; § Errata)
- **Contract:** none — the output is a Markdown file with YAML frontmatter, not an API under `contracts/`. The frontmatter *is* a consumer-facing contract, and its shape is pinned by the Acceptance Criteria below (the `contract-version` field is how consumers detect it).
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full (work-loop). Risk triggers fired: governance (implements accepted
RFC-0058 + ADR-0045), new dependency (pypdf), security boundary (parses untrusted
document files — file I/O + XML/zip deserialization), public-interface change (the
skill's output frontmatter shape). This is the floor-first slice of RFC-0058:
D2 (Tier-0 no-ML floor), D3 (unified output contract), D7 (Tier-0 format coverage).
Deliberately deferred to later specs: D4 general image/PDF-page mode + Tier-1
rasterization (extraction-general-image-mode); D5 enrichment/vision/managed-API +
D6 chunking (extraction-higher-tiers). -->

## Objective

`file-to-markdown` produces trustworthy Markdown for AI context layers **without
any ML dependency** — the no-ML **Tier-0 floor**. Today the document branch is a
bare Docling wrapper, so where Docling's ML models are banned or un-fetchable the
skill has no path at all for PDFs or Office files. After this spec, a user in a
locked-down environment can convert a digital PDF, a `.docx`/`.xlsx`/`.pptx`, and
the everyday text formats (HTML, EPUB, CSV/TSV, OpenDocument, `.eml`) to Markdown
using only ordinary parser libraries or the standard library — and every
extraction `file-to-markdown` produces, across **both** of its output shapes
(`convert.py` — which covers the document path *and* the image-via-Docling path
in one `convert_file` shape — and `reconcile.py`, the diagram/image branch),
carries one versioned **unified output contract**: YAML frontmatter recording
provenance and a quality/confidence signal, so a scanned
PDF that yields garbage or sparse text is flagged `requires-review` instead of
passing silently. Docling stays available and unchanged as the higher-fidelity
**Tier 2**; this spec makes Tier 0 the floor beneath it, not the base.

## Boundaries

### Always do

- Keep source changes inside `packs/converters/.apm/skills/file-to-markdown/`,
  plus the pack version files (`pack.toml`, `.claude-plugin/plugin.json`), the
  top-level `.claude-plugin/marketplace.json` (regenerated), and
  `docs/product/changelog.md`. **`msg-to-markdown` is out of scope** — it is a
  Node.js skill and cannot share the Python contract builder; its contract
  adoption is a follow-on Python-port slice (deferred:
  extraction-msg-to-markdown-python-contract).
- Make the output contract **additive** and **byte-stable for the image branch**:
  keep every frontmatter key `reconcile.py` emits today, *in its current order*;
  *add* the new `contract-version` and `tier` keys; have `convert.py` (document +
  image-via-Docling) emit the same shape via the one shared builder. Stamp
  `contract-version` so consumers can detect the shape.
- Keep using the skill's existing **hand-rolled stdlib YAML emitter** (extended
  into the shared builder), *not* `yaml.safe_dump` — `safe_dump` adds PyYAML (a
  new dependency the skill deliberately avoids) and reorders keys alphabetically
  (breaks the byte-stability above). Make the hand-rolled emitter **injection-safe
  by escaping/quoting every value** so extracted content containing `---`,
  newlines, or `key:` lines cannot break out of the block, and keep the extracted
  body below the closing `---` fence.
- Write the output `.md` only to a path that is **resolved (realpath) and
  confined by path-component containment** to the intended output directory
  (mirroring the `markdown-to-office-publishing` spec's confinement), so a crafted
  input/target path or a symlink cannot redirect the write outside it. Zip entry
  names are read by known path and **never** joined into a filesystem path.
- Mirror the sibling rendering skills' **pip-on-demand** pattern for `pypdf`
  *and* any ordinary Office parser (`python-docx`/`openpyxl`/`python-pptx`): an
  early import-probe (`cmd_check()` + a `PIP_INSTALL` constant + a `--check` verb
  returning exit 0 present / 2 absent), never auto-install, and degrade (Office →
  stdlib `zipfile`+XML; PDF → the sparse-text escalation path) when the library
  is unapproved.
- Parse untrusted document input defensively: use only an XXE-safe XML parser
  (see *Never do*), and guard zip-based formats (OOXML/ODT/EPUB) against
  decompression bombs on **every** axis — a declared-vs-compressed size ratio, a
  total-cumulative-uncompressed-bytes cap, an entry-count cap, and refusal of
  nested-archive entries — all *before* full decompression.
- When Tier 0 yields sparse or low-confidence text (a scanned/image-only PDF
  whose text layer is thin or empty), mark the extraction `extraction-confidence:
  low` and `requires-review: true` and name Tier 1 (agent-vision) as the
  escalation target — never emit silent low-quality output.

### Ask first

- Adding any **new dependency**. `pypdf` is the one Tier-0 PDF dependency
  RFC-0058 D2 sanctions adding to the pack's adopter footprint — resolved
  **pip-on-demand via `--check`** (not eagerly imported / not a hard `pack.toml`
  runtime dep), exactly like the Office parsers. Office and D7 libraries are
  likewise pip-on-demand or stdlib. **PyYAML is explicitly not added** (the
  hand-rolled emitter stays); any other new dep is an escalation.
- **Changing or removing** any frontmatter key the image branch emits today (as
  opposed to adding keys) — existing consumers may parse them.
- Relying on an ordinary Office lib's *internal* XML parsing for XXE-safety:
  `python-docx`/`openpyxl`/`python-pptx` pull `lxml` transitively and parse OOXML
  themselves, so confirm (contract-grounding at EXECUTE) that the pinned version
  disables external-entity resolution — otherwise route that format through the
  stdlib XXE-safe path instead.
- Bumping the converters pack's **minor** version vs. patch (this adds
  capability, so minor is expected — confirm the number).

### Never do

- Add an ML or OCR **model** dependency (Docling, Tesseract, EasyOCR, a layout/
  table model, a vision model). Those are Tier 2+ and out of this floor's scope.
- Reach Tier 3, or introduce **any network egress** from the skill.
- Parse untrusted XML with `lxml`, `xml.dom.minidom`, or `xml.sax` at default
  settings (they resolve external entities / are billion-laughs-prone). The only
  sanctioned parsers for the skill's *own* XML reads are stdlib
  `xml.etree.ElementTree` (which refuses external entities) or `defusedxml`.
- Flatten, rename, re-nest, or **reorder** the image branch's existing
  frontmatter keys in a way that breaks a consumer parsing today's output — the
  contract is additive and byte-stable.
- Bundle any ML model, managed-OCR vendor config, or per-vendor knowledge base
  (ADR-0034 holds).
- Edit projected `.claude/` paths by hand — edit the `packs/converters/.apm/`
  source and regenerate.

## Testing Strategy

- **Unified contract shape (both output shapes) — TDD + goal-based.** Unit tests
  on the shared frontmatter builder assert every required key (`contract-version`,
  `source-file`, `content-type`, `tier`, `ingestion-date`, `extraction-confidence`,
  `requires-review`) is present; a **byte-parity golden test** asserts
  `reconcile.py`'s emitted frontmatter is unchanged (keys, order, quoting) except
  for the two added keys; one end-to-end run of each documented invocation
  (`convert.py`, `reconcile.py`) greps the emitted frontmatter.
- **Frontmatter-injection safety — TDD.** A fixture whose extracted values/extras
  contain `---`, newlines, and `contract-version: 9.9` produces frontmatter where
  the hand-rolled emitter escapes/quotes them so the real builder values win, the
  closing `---` fence is intact, and the hostile text appears only in the body —
  the contract is not forged or truncated.
- **Tier-0 PDF text extraction (`pypdf`) — TDD + goal-based.** Unit test on the
  extraction/normalization function; one end-to-end `python scripts/convert.py`
  run against a real digital PDF asserting Markdown body + `tier: "0-no-ml"`
  frontmatter.
- **Tier-0 Office extraction (docx/xlsx/pptx; ordinary-lib and stdlib paths) —
  TDD + goal-based.** Unit tests on the Markdown-mapping functions for each
  format, plus one that forces the stdlib `zipfile`+XML fallback path; one
  end-to-end run per format against a real file (the pack already ships
  `evals/files/sample.docx`).
- **Sparse-text self-assessment — TDD.** A digital PDF whose extracted text is
  empty/near-empty produces `extraction-confidence: low` + `requires-review:
  true` and names Tier 1 as the escalation target.
- **D7 formats (HTML, EPUB, CSV/TSV, ODT/ODS/ODP, `.eml`) — goal-based E2E +
  per-family unit mappers.** One end-to-end run per format family against a real
  sample asserting the Markdown body and the unified frontmatter, plus a unit test
  on each family's reader/mapper.
- **Defensive parsing — TDD.** A crafted OOXML/ODT file carrying an external XML
  entity does not resolve it (no network/file fetch); zips are refused before
  full decompression on each axis — implausible size ratio, cumulative-bytes cap,
  entry-count cap; a zip with a `../`-prefixed entry name is never joined into a
  filesystem path (path-join guard).
- **Output-path confinement — TDD.** A target/output path resolving outside the
  intended directory via `..` traversal, and via a symlink escape, is refused;
  the written `.md` never lands outside the confinement root.
- **Resource ceiling — TDD/goal-based.** An input exceeding the coarse ceiling
  (max bytes and/or max pages/rows/entries) is refused with
  `requires-review`/actionable error rather than parsed unbounded.
- **Release hygiene — goal-based.** `pack.toml` / `plugin.json` / `marketplace.json`
  are version-consistent; `lint-packs`, `validate`, `build`, and `pytest` are
  green; a `docs/product/changelog.md` `[Unreleased]` entry records the
  user-visible additions; SKILL.md's documented default invocation is still the
  single `python scripts/convert.py "<input-file>"` form.

## Acceptance Criteria

- [ ] **AC1 — Unified output contract, versioned.** Both of `file-to-markdown`'s
  output shapes — `convert.py` (the document path *and* the image-via-Docling
  path, one `convert_file` shape) and `reconcile.py` (the diagram/image branch) —
  emit YAML frontmatter carrying at minimum `contract-version` (a string, e.g.
  `"1.0"`), `source-file`, `content-type`, `tier`, `ingestion-date`,
  `extraction-confidence` (`high|medium|low`), and `requires-review` (bool). A
  single shared builder (`contract.py`) produces the frontmatter so the call
  sites cannot drift. (`msg-to-markdown` is Node.js and adopts the contract in a
  follow-on Python-port slice — deferred: extraction-msg-to-markdown-python-contract.)

- [ ] **AC2 — Additive and byte-stable for the image branch (no consumer break).**
  Every frontmatter key `reconcile.py` emits today (`title`, `source-file`,
  `content-type`, `content-category`, `ingestion-date`, `diagram-type`,
  `processing.*`, `ingestion-quality.*`) is still present and unchanged in name,
  nesting, order, and meaning; the image branch gains only the new
  `contract-version` and `tier` keys. A **byte-parity golden test** locks the
  pre-existing block (proving the shared-builder refactor did not reorder or
  re-quote it).

- [ ] **AC3 — Document branch is context-layer-ready.** `convert.py` (the
  document branch) emits the unified frontmatter above its Markdown body — where
  today it emits none. Its `extraction-confidence` and `requires-review` reflect
  the extraction (see AC6).

- [ ] **AC4 — Tier-0 digital-PDF text extraction with no ML.** A digital
  (text-layer) PDF is converted to Markdown using `pypdf` — a pure-Python,
  no-model dependency — with `tier: "0-no-ml"` in the frontmatter, and without
  importing Docling or any ML/OCR model.

- [ ] **AC5 — Tier-0 Office extraction, degrading to stdlib.** `.docx`, `.xlsx`,
  and `.pptx` are converted to Markdown at Tier 0. When `python-docx` /
  `openpyxl` / `python-pptx` are present the extractor uses them (verified via a
  `--check` import-probe mirroring the sibling `markdown-to-*` skills); when they
  are absent the extractor degrades to stdlib `zipfile`+XML and still produces
  Markdown. Neither path imports an ML model.

- [ ] **AC6 — Sparse-text self-assessment escalates honestly.** When Tier-0 PDF
  extraction returns empty or sparse text (below a defined threshold), the output
  is marked `extraction-confidence: low` and `requires-review: true`, and the
  skill's output names Tier 1 (agent-vision) as the escalation target — it does
  not silently emit low-quality Markdown.

- [ ] **AC7 — Tier-0 format coverage (D7).** HTML, EPUB, CSV/TSV, OpenDocument
  (ODT/ODS/ODP), and `.eml` inputs each convert to Markdown at Tier 0 using
  stdlib or ordinary libraries (no ML), each carrying the unified frontmatter.

- [ ] **AC8 — Extracted content cannot forge the contract.** The hand-rolled
  emitter escapes/quotes every frontmatter *value* — including embedded newlines,
  `"`, and `\` — so a value can never break out of its scalar and split the block
  (a raw `\n` inside a `"..."` scalar would break the fence; escaping it is the
  load-bearing part). The contract is the **leading** `---`-fenced block only; the
  extracted body sits below it, and a `---` line *in the body* is content, not a
  second frontmatter (the guarantee rests on leading-block-only + a compliant
  parser stopping at the first closing fence, since a literal `---` body line
  cannot be escaped without corrupting content). Two tests: a builder-level test
  on hostile values/extras (fence intact, values escaped), and a **full-document**
  test whose extracted *body* contains `---` and `contract-version:` lines,
  asserting a frontmatter parser reads only the builder's leading block.

- [ ] **AC9 — Defensive parsing of untrusted input.** The skill's own XML reads
  use only an XXE-safe parser (stdlib `xml.etree.ElementTree` or `defusedxml`);
  `lxml`/`minidom`/`sax` at defaults are not used (see Boundaries). Reading a
  zip-based format is refused **before full decompression** on every axis — an
  implausible declared-vs-compressed size ratio, a total-cumulative-uncompressed
  cap, and an entry-count cap. Zip **entry names** are read by known path, never
  joined into a filesystem path (a **path-join guard**, not `extractall` — the
  readers read members in-memory, so the risk is entry-name→path construction,
  not a write escaping a dir). For EPUB/ODF (which legitimately contain many
  members), the reader reads only the **known-name** text/XML members it needs by
  path and **never recurses into an embedded archive member** — that is how the
  nested-archive bomb axis and legitimate EPUB/ODF structure are reconciled (AC7).
  Tests exercise the XXE guard, each bomb axis, and a `../`-entry-name fixture.

- [ ] **AC10 — Docling path body is passed through unmodified.** The Docling
  (Tier-2) path gains only the two additive contract keys (`contract-version`,
  `tier: "2-approved-ml"`); an **in-process identity assertion** proves the
  Markdown body handed to the builder equals the body Docling returned (byte-parity
  against Docling's own output, not against an unpinned external golden file), so
  a Docling-running environment behaves identically apart from the richer
  frontmatter.

- [ ] **AC11 — Tests + release hygiene + progressive-disclosure default.** New
  tests cover AC1–AC10, AC12, AC13 (unit + per-format end-to-end subprocess runs
  of the documented invocations) and pass; the converters pack version is bumped
  consistently across `pack.toml`, `.claude-plugin/plugin.json`, and the
  regenerated `.claude-plugin/marketplace.json`; `docs/product/changelog.md`
  records the user-visible additions; SKILL.md documents the tiers, the new
  formats, and the contract as progressive disclosure, and a goal-based check
  confirms its documented **default invocation is still the single
  `python scripts/convert.py "<input-file>"` form**.

- [ ] **AC12 — Output-path confinement.** The written `.md` path is resolved
  (`Path.resolve()`/realpath) and confined to the intended output directory by
  path-component containment (not string-prefix); a target path escaping via `..`
  traversal or via a symlink is refused. Tests cover the `..`-traversal, the
  symlink-escape, **and the sibling-prefix case** (`<root>-evil` against root
  `<root>` — the one case a naive `str.startswith` prefix check passes and
  component-containment must reject), mirroring the `markdown-to-office-publishing`
  benchmark.

- [ ] **AC13 — Resource ceiling on Tier-0 parsers.** Each Tier-0 parser enforces
  a coarse upper bound (max input bytes and/or max pages/rows/entries); an input
  exceeding it is refused with an actionable error and `requires-review` rather
  than parsed unbounded, so an attacker-supplied huge file cannot hang context
  ingestion. (This is the newly-introduced surface the nine new parsers add; the
  predecessor `converters-extraction-fixes` deferral no longer covers it.)

## Assumptions

- Technical: the target skill is `file-to-markdown` in the `converters` pack
  (v0.2.3), whose document branch (`convert.py`) is a bare Docling wrapper
  emitting **no** frontmatter and whose image branch (`reconcile.py`) emits a
  nested `ingestion-quality.*` / `processing.*` frontmatter set. *(source: repo
  read of `packs/converters/.apm/skills/file-to-markdown/` + `pack.toml`,
  2026-06-30.)*
- Technical: the sibling `markdown-to-docx`/`-xlsx`/`-pptx` skills declare their
  Office libraries via a pip-on-demand pattern — a `cmd_check()` import-probe, a
  `PIP_INSTALL` constant, and a `--check` verb returning exit 0/2 — which Tier-0
  Office extraction mirrors. *(source: repo read of
  `packs/converters/.apm/skills/markdown-to-*/scripts/render.py`, 2026-06-30.)*
- Technical: `pypdf` is a pure-Python PDF library that extracts the text layer of
  digital PDFs with no ML model and no first-run model download, so it clears an
  ordinary-library approval bar that an ML/OCR model would not; it is resolved
  **pip-on-demand via `--check`** (not a hard `pack.toml` dep). *(source: RFC-0058
  D2 + Evidence §; version pinned at implementation. Web search unavailable in
  this harness — the "pure-Python, no model" property is asserted from RFC-0058
  and adopter-verifiable at install.)*
- Security posture: this slice treats document inputs as **untrusted** (guard-on:
  XXE-safe parser, decompression-bomb guards, output-path confinement, resource
  ceiling), a deliberate divergence from the image branch's / existing
  `convert.py`'s "local-files-trusted" carve-out (which disables the bomb guard
  for local files, per `markdown-to-office-publishing/spec.md`). The floor's
  inputs are documents fed into AI context layers, where the trust assumption does
  not hold. *(source: RFC-0058 Problem & goals; sibling-spec trust-posture note.)*
- Technical: the ordinary Office libs (`python-docx`/`openpyxl`/`python-pptx`)
  parse OOXML via `lxml` transitively, so their XXE-safety is theirs, not the
  skill's; the spec requires confirming it at EXECUTE (contract-grounding) or
  routing that format through the stdlib XXE-safe path. *(source: repo read +
  security-reviewer spec-stage pass, 2026-06-30.)*
- Process: RFC-0058 (Accepted 2026-06-30) is the governing decision and
  ADR-0045 records the doctrine; this spec is the floor-first slice its Follow-on
  artifacts name. *(source: `docs/rfc/0058-*.md`, `docs/adr/0045-*.md`.)*
- Product: the consumer of the output is an AI **context layer** (retrieval
  stores / injected reference material), for which Markdown + provenance +
  quality signal is the right shape. *(source: RFC-0058 Problem & goals +
  Evidence F6.)*

### Declined patterns

- Tempted to flatten the image branch's nested `ingestion-quality.extraction-
  confidence` / `.requires-review` to top-level to match RFC-0058 D3's flat field
  list; declining — flattening renames existing keys and breaks any current
  consumer. The additive choice (keep nested keys, add `contract-version`+`tier`,
  doc branch adopts the same nested shape) satisfies "unified contract" without a
  breaking change. The top-level names in D3 are read as *logical* fields the
  contract must carry, not a mandate to move the physical keys.
- Tempted to switch the frontmatter emitter to `yaml.safe_dump` for
  injection-safety; declining — it adds PyYAML (a new dependency the skill has
  deliberately avoided with its hand-rolled stdlib emitter) and sorts keys
  alphabetically, reordering the image branch's block and breaking AC2/AC10
  byte-stability. Injection-safety is instead achieved by making the existing
  hand-rolled emitter escape/quote values (AC8) — same guarantee, no new dep, no
  reorder.
- Tempted to build the Tier-1 agent-vision escalation (rasterize → in-session
  model read) here so a scanned PDF has a real path; declining — Tier-1
  rasterization is the `extraction-general-image-mode` spec (D4), and the floor
  degrades honestly (`requires-review`) without it. Building it here would merge
  two specs and pull in the rasterizer dependency this floor deliberately avoids.
- Tempted to have `msg-to-markdown` adopt the contract in this spec (RFC-0058
  Open-Q2's recommended default); declining — it is a **Node.js** skill and
  cannot import the Python builder, so adopting the contract means either forking
  it in JS (violates AC1's single-builder/no-drift property) or porting the skill
  to Python. The port is the right move but is a distinct, sizable change (new
  Python `.msg` dependency, full rewrite, parity validation) that belongs in its
  own slice, not this floor (deferred:
  extraction-msg-to-markdown-python-contract). `.eml`/MIME for that skill defers
  with it (deferred: extraction-tier0-eml-mime); `.eml` as a *file-to-markdown
  input format* stays in this spec at Tier 0 (AC7).
- Tempted to add a general HTML→Markdown dependency (e.g. `markdownify`) for
  richer D7 HTML output; declining unless a stdlib `html.parser`-based reduction
  proves inadequate — a new hard dep is an "Ask first", and the floor's job is
  coverage, not fidelity.
