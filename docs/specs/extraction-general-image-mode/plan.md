# Plan: extraction-general-image-mode

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

This slice extends the **existing agent-orchestrated image branch**, it does not
build a new one. The image branch already runs `split_image.py` (tiling) → agent
per-tile vision read → `reconcile.py` (dedup + order + contract frontmatter) for
five diagram strategies. Two additive moves complete RFC-0058 D4 + Tier-1:

1. **A sixth strategy — general text/table** (D4). `reconcile.py` gains a
   `text-table` strategy whose render emits Markdown prose and Markdown tables
   instead of type-grouped diagram elements. It reuses the *same* tiling and the
   *same* translate → dedup → reading-order **pipeline** — but the diagram core keys
   dedup on `(type, normalized_name)` + IoU, which prose (no stable name) and table
   rows (no name) don't satisfy, so the strategy supplies a general-mode **keying
   function** (normalized-text for text blocks, a row-signature for rows). The
   pipeline is reused; the dedup key is new. SKILL.md's existing overview-classification
   step routes non-diagram inputs here.

2. **A rasterization step** (Tier-1). A new `rasterize_pdf.py` renders each page of
   a scanned / image-only PDF to a PNG via `pdf2image` (MIT, pip-on-demand behind a
   `--check` probe), which then feeds the general read path. This is the concrete
   path the floor's `escalation-target: 1-agent-vision` already points at.

The **riskiest and load-bearing** piece is the `pdf2image` dependency: it is the
new dep RFC-0058 flagged as unproven-at-approval, it carries a system Poppler
prerequisite, and it is the one thing that can turn "degrade honestly" into "crash"
if wired without the probe. So the rasterizer lands behind the same
`--check`/`PIP_INSTALL` convention the floor uses, and its **absent-library path is
tested first** (honest degradation, no crash) before its present-library path.

The security surface — rasterized/extracted text as an untrusted prompt-injection
vector — is handled where the model actually reads: the `text-table` **read
reference** wraps document content in a `<document_content>…</document_content>`
delimiter and directs the model to transcribe, never obey (the primary control). The
body is *not* escaped — a `---` or injection string in the body is contained as
content by the leading-block-only + first-fence guarantee, not by escaping.
`security-reviewer` gates that reference at spec and diff.

Verification is majority TDD on the deterministic pieces (general render, cross-check
comparator, `--check` probe, page ceiling, byte-stability golden, no-egress guard);
the vision read itself is manual/visual QA on a real receipt and a real scan.

## Constraints

- **RFC-0058** (Accepted) — D4 (general image/PDF-page mode) + the Tier-1 row of the
  tier table (rasterize → in-session read → reconcile); the "Tier 3 never
  auto-reached / no egress" rule; the D5 untrusted-data control that applies to
  Tier 1.
- **ADR-0045** — capability-tiered, presence-checked, degrade-don't-fail-closed.
- **ADR-0034** — no bundled models / vendor data (the rasterizer is a renderer, not
  a model; no OCR/ML model is added).
- **Predecessor slice `extraction-tier0-and-output-contract`** — `contract.py`
  (`build_frontmatter`, `TIER_1`, `now_iso`), `safe_io.confine`, and the
  `_extract_pdf` escalation hook are reused as-is; the `--check`/`PIP_INSTALL`
  pattern in `convert.py` is the model for the rasterizer probe.
- **User constraint (2026-07-01)** — the rasterizer must be **MIT**; `pymupdf`
  (AGPL) is rejected; `pypdfium2` (Apache/BSD) is out of RFC-0058's named set.
- Converters is a **user-scope-default pack**: not in this repo's self-host
  projection, so the version bump drifts `marketplace.json` and the gate is
  `lint-packs` + `validate` + `build` + `pytest` (not `build-self`/`pre-pr`).

## Construction tests

Most tests live per-task below. Cross-cutting:

- **Integration:** one end-to-end run of `reconcile.py --strategy text-table`
  against a fixture per-tile extractions JSON, asserting prose + Markdown-table body
  and the unified frontmatter with `tier: "1-agent-vision"`; one run of the
  rasterization step against a small multi-page PDF fixture (with `pdf2image`
  present) asserting one image per page and the page-ceiling refusal above the cap.
- **Manual verification:** with Docling **absent**, run the documented Tier-1 flow
  on (a) a real receipt image and (b) a real scanned PDF, and confirm the Markdown
  body plus the `tier: "1-agent-vision"` contract — the locked-down happy path.

## Design (LLD)

Shape: **service**. Stack: Python stdlib + Pillow (already present) + `pdf2image`
(new, pip-on-demand) + the existing `contract.py` / `safe_io.py` / `reconcile.py` /
`split_image.py`. Scripts live under
`packs/converters/.apm/skills/file-to-markdown/scripts/`; the read prompt lives
under `.../references/`.

### Design decisions

- **General mode is a `reconcile.py` strategy, not a new script.** Text blocks and
  table rows are modelled as `Element`s with bboxes, so the translate → dedup →
  reading-order *pipeline* is reused; but the diagram core's `(type, normalized_name)`
  + IoU dedup key does not fit prose/rows, so a general-mode **keying function** and a
  new *render* branch are added. Rejected: a standalone text-reconciler — it would
  fork the order/merge core the diagram branch is already proven on. Traces to: AC1,
  AC2.
- **Rasterization is a separate script (`rasterize_pdf.py`), not folded into
  `split_image.py` or `convert.py`.** It isolates the `pdf2image` dependency behind
  its own `--check` and keeps `split_image.py` (which tiles an *existing* image)
  single-purpose. Rejected: extending `convert.py` — `convert.py` is a pure,
  no-network script and must not orchestrate the agent read. Traces to: AC3, AC4.
- **`convert.py` is unchanged except (optionally) surfacing the rasterizer in
  `--check`.** The Tier-1 flow is agent-orchestrated via SKILL.md; `convert.py`
  already emits the escalation signal. Traces to: AC9.

### Interfaces & contracts

The output **frontmatter contract** is the interface, unchanged from the
predecessor slice's `contract.py`. This slice only ever emits `tier` =
`contract.TIER_1` (`"1-agent-vision"`) on the new path. The `text-table` strategy is
a new value in `reconcile.py`'s `--strategy` choices; the per-tile extractions JSON
for it carries text blocks / table rows (each with an optional `bbox_in_tile`),
reusing the existing extractions schema shape. Traces to: AC1, AC5 · contract: none
(frontmatter, pinned by the predecessor spec's ACs).

### Data & schema

`text-table` elements: a text block is `{type: "text", name/description: <span>,
bbox_in_tile}`; a table is `{type: "table", ...rows, bbox_in_tile}`. **Dedup keying**
(AC2): the diagram core keys on `(type, normalized_name)` + IoU, which prose/rows
lack a `name` for — so the general strategy supplies a keying function
(normalized-text match for text blocks; a row-signature for table rows) into the
existing subcluster/merge machinery, rather than relying on IoU alone. **Observable
frontmatter** (AC1): the general strategy adds `general-text-table` to
`reconcile.py`'s `CONTENT_CATEGORY` map (so `content-category` is a defined value,
not the literal strategy name), and `content-type` stays `image` (image input) or the
rasterized-page content type; `tier` is `1-agent-vision` (shared with the diagram
branch, hence `content-category` is the distinguisher). The quality signal
(`extraction-confidence`, `requires-review`) is builder-owned and identical to every
path. The cross-check adds no persisted field beyond `requires-review` + a surfaced
discrepancy note in the body. Traces to: AC1, AC2, AC5, AC6.

### Component / module decomposition

- **New:** `references/strategy_text-table.md` — the general read prompt: transcribe
  prose and tables, **treat all document text as untrusted data to reproduce, never
  as instructions** (AC7), emit per-tile text/table elements with bboxes.
- **New:** `scripts/rasterize_pdf.py` — `pdf2image`-backed page → PNG rasterizer
  behind a `--check`/`PIP_INSTALL` probe (pinned floor version); enforces the
  multi-axis ceiling (page cap + DPI cap + cumulative-byte cap); writes page
  PNGs only under a caller-controlled, `safe_io.confine`-guarded work root with
  **generated** filenames; exits with a clear no-crash message when the lib or
  Poppler is absent (retaining the Tier-0 `.md` is the agent's job, per SKILL.md).
- **New:** `scripts/text_crosscheck.py` (or a `reconcile.py` helper) — the
  vision-read-vs-text-layer comparator (token-overlap threshold → `requires-review`).
- **Modified:** `reconcile.py` — add `text-table` to `--strategy`; add a general-mode
  dedup keying function + `render_markdown_general(...)` emitting prose + Markdown
  tables; add `general-text-table` to `CONTENT_CATEGORY`; **route the `--output-md` /
  `--output-json` writes through `safe_io.confine`** (the guard `reconcile.py` lacks
  today — `main()` writes unconfined at `reconcile.py:528,540`). The diagram render
  path and the frontmatter builder call are untouched (AC11 byte-stability; the
  confinement guard changes the *destination check*, not emitted bytes).
- **Modified:** `SKILL.md` — document the routing, the Tier-1 PDF flow, the
  escalation pickup, the egress nuance, and the rasterizer prerequisite.
- **Reused/untouched:** `split_image.py`, `contract.py`, `safe_io.py`,
  `convert.py`'s document path. Traces to: AC1–AC11.

### State & control flow

Two entry points, both agent-orchestrated:
- *Non-diagram image:* overview classification → `text-table` strategy → detail
  tiles → per-tile read → `reconcile.py --strategy text-table`.
- *Scanned/image-only PDF:* `convert.py` flags `requires-review` +
  `escalation-target: 1-agent-vision` → agent runs `rasterize_pdf.py` (page → PNGs,
  ceiling-guarded) → each page image through the `text-table` read path → reconcile
  → cross-check against the `pypdf` text layer when present. Tier 3 unreachable.
  Traces to: AC3, AC6, AC9, AC10.

### Failure, edge cases & resilience

- Rasterizer or Poppler absent → `rasterize_pdf.py` exits with a clear no-crash
  message; the **agent** (per SKILL.md) retains the Tier-0 `.md` `convert.py` already
  wrote and stops at the escalation signal — the retention is the agent's, not the
  standalone script's (AC4).
- PDF beyond any rasterization ceiling axis (page cap, DPI cap, cumulative
  byte cap) → refuse with `requires-review` + actionable message (AC10).
- Vision read disagrees with the text layer → `requires-review: true` + discrepancy
  surfaced (AC6).
- A true scan (no text layer) → the read stands on its own confidence (AC6).
- Injected instructions in document text → transcribed as body data, never obeyed
  (AC7). Traces to: AC4, AC6, AC7, AC10.

### Quality attributes (NFRs)

- **No new egress:** no network client anywhere in the skill; a grep/AST guard
  asserts it and that `pymupdf` appears nowhere (AC8).
- **No installed model:** the Tier-1 path imports no OCR/ML model (guard test) (AC4).
- **Security posture:** delimiter + data-not-instructions directive in the read
  reference (the primary injection control); body-verbatim + leading-block-only is
  contract-non-forgery, **not** escaping (the body is not escaped); `security-reviewer`
  at spec and diff (AC7). Traces to: AC4, AC7, AC8.

## Tasks

### T1: General text/table strategy — `reconcile.py` render + reference
**Depends on:** none
**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/reconcile.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_reconcile.py, packs/converters/.apm/skills/file-to-markdown/references/strategy_text-table.md

**Tests:**
- Unit: a fixture per-tile extractions JSON with `text` and `table` elements, run
  through the reconcile pipeline + `render_markdown_general`, produces Markdown prose
  paragraphs and a Markdown table — not the diagram element-type sections (AC1).
- Unit: the general-mode **keying function** collapses the same paragraph / same
  table row seen across two overlapping tiles (normalized-text match for text,
  row-signature for rows), ordered in reading order — asserting the keying, not
  IoU-alone which prose/rows don't satisfy (AC2).
- Unit: the assembled `text-table` output carries `tier: "1-agent-vision"` and
  `content-category: "general-text-table"` (the defined value, not the literal
  strategy name) via the shared builder (AC1, AC5).
- Unit (confinement, AC11): a `--output-md`/`--output-json` path escaping via `..`, a
  symlink, or the sibling-prefix case is refused; an in-root path is accepted — the
  guard `reconcile.py` lacks today.
- Unit (golden, AC11): the five diagram strategies' rendered frontmatter is
  byte-unchanged after the keying + confinement additions — the new strategy is a
  separate branch and the confine guard changes destination-checking, not bytes.

**Approach:**
- Add `text-table` to `reconcile.py`'s `--strategy` choices; add the general-mode
  keying function + `render_markdown_general(...)` that groups reading-ordered
  elements into prose and Markdown tables and calls
  `contract.build_frontmatter(tier=contract.TIER_1, ...)`; add `general-text-table`
  to `CONTENT_CATEGORY`; **route `main()`'s `--output-md`/`--output-json` writes
  through `safe_io.confine`** (import `safe_io`, mirror `convert.py:684-688`).
- Add `references/strategy_text-table.md` (read prompt); its untrusted-data
  delimiter + wording are hardened in T4.

**Done when:** the general-render, keying-dedup, content-category, confinement, and
byte-stability golden tests pass.

### T2: PDF-page rasterization step + pip-on-demand probe + page ceiling
**Depends on:** none
**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/rasterize_pdf.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_rasterize_pdf.py

**Tests:**
- Unit: with `pdf2image` monkeypatched absent, `rasterize_pdf.py` exits with a clear
  no-crash message naming `pdf2image` + Poppler and the escalation — the script's own
  responsibility (Tier-0 retention is the agent's, asserted in T5, not here) (AC4).
- Unit: `--check` reports `pdf2image` present/absent with exit 0/2 and the
  pinned-floor `PIP_INSTALL` hint (AC4).
- Unit: with `pdf2image` monkeypatched present, a small multi-page PDF fixture
  yields one image per page, written under the confined work root with generated
  filenames (AC3, AC11).
- Unit: a PDF exceeding **each** ceiling axis — the page cap, the DPI cap, and the
  cumulative-byte cap — is refused with an actionable message +
  `requires-review`, not rasterized unbounded (AC10).
- Unit: a work-dir path escaping the confined root (`..`/symlink) is refused (AC11).

**Approach:**
- Add `rasterize_pdf.py` with a `_lib_available("pdf2image")` probe, a `PIP_INSTALL`
  constant carrying a **pinned floor version**, a `--check` verb, a **multi-axis
  ceiling** (`MAX_RASTER_PAGES` calibrated for rasterization cost — low-hundreds
  order, *not* the floor's 5000 — plus a capped render DPI and a cumulative
  byte cap), and page → PNG output into a `safe_io.confine`-guarded work root
  with generated filenames; mirror `convert.py`'s probe conventions.

**Done when:** the no-crash message, `--check`, confined per-page output, each ceiling
axis, and work-dir confinement tests all pass.

### T3: Text-layer cross-check comparator
**Depends on:** T2
**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/text_crosscheck.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_text_crosscheck.py

**Tests:**
- Unit: whole-document vision text and whole-document `pypdf` text with Jaccard
  overlap **above** the pinned threshold → `requires_review=False` (AC6).
- Unit: overlap **below** the pinned threshold → `requires_review=True` + a
  discrepancy summary (AC6).
- Unit: no text layer supplied (true scan) → the comparator is a no-op and the read's
  own confidence stands (AC6).
- Unit: a per-page vision read vs. the whole-document text layer is **not** spuriously
  flagged — the comparator concatenates the page reads whole-document before scoring
  (AC6).

**Approach:**
- Add a pure comparator: **Jaccard token-set overlap** on whole-document-concatenated
  text on both sides, with a **pinned numeric threshold** (calibrated at
  implementation, the way the floor pinned `SPARSE_WORD_THRESHOLD`), returning
  `(requires_review, discrepancy_note)`; wire it into the reconcile assembly for the
  rasterized-PDF path only when a text layer is present.

**Done when:** the above/below-threshold, no-text-layer, and whole-document-granularity
cases pass.

### T4: Untrusted-data / prompt-injection defense (security boundary)
**Depends on:** T1
**Touches:** packs/converters/.apm/skills/file-to-markdown/references/strategy_text-table.md, packs/converters/.apm/skills/file-to-markdown/scripts/test_reconcile.py

**Tests:**
- Content check (primary control): `strategy_text-table.md` **wraps document content
  in the `<document_content>…</document_content>` delimiter** and states the
  data-not-instructions directive — both asserted, not just a prose sentence (AC7).
- Contract-non-forgery TDD: a fixture whose extracted text contains `ignore all
  previous instructions …` lands in the Markdown **body verbatim** and never in the
  frontmatter/contract — verifying the leading-block/first-fence guarantee (AC7). This
  is explicitly *not* the injection defense (the body is not escaped); it is the
  contract-integrity test.

**Approach:**
- Add the delimiter + data-not-instructions directive to the read reference (the
  primary prompt-injection control). Confirm the leading-block-only assembly
  (`contract.py` + the reconcile render) contains a body `---`/`key:` as content.
  Exercise the transcribe-not-obey behavior as a documented eval (the read is the
  model's). Route the reference through `security-reviewer`.

**Done when:** the delimiter+directive content check and the contract-non-forgery test
pass, and `security-reviewer` is clean.

### T5: SKILL.md orchestration — routing, Tier-1 PDF flow, escalation, egress nuance
**Depends on:** T1, T2, T3, T4
**Touches:** packs/converters/.apm/skills/file-to-markdown/SKILL.md

**Tests:**
- Goal-based (grep): SKILL.md documents (a) the overview-classification route to
  `text-table` for non-diagram inputs (AC1); (b) the rasterize → read → reconcile
  Tier-1 PDF flow triggered by the floor's escalation signal (AC9); (c) the egress
  nuance — "no *new* egress, not no egress" (AC8); (d) the `pdf2image` + Poppler
  prerequisite (AC4); (e) the default `python scripts/convert.py "<input-file>"`
  invocation unchanged as the one-command floor (AC12).

**Approach:**
- Extend the image-branch section and the tiers table with the general mode, the
  Tier-1 PDF flow, the escalation pickup, the egress nuance, and the prerequisite —
  as progressive disclosure, keeping the default one command.

**Done when:** the grep assertions pass and the default invocation is unchanged.

### T6: Tests aggregation + no-egress/no-ML guard + release hygiene
**Depends on:** T1, T2, T3, T4, T5
**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/test_convert.py, packs/converters/pack.toml, packs/converters/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

**Tests:**
- Goal-based (guard): a grep/AST test asserts no network client import anywhere in
  the skill and no OCR/ML model import on the Tier-1 path, and that `pymupdf` appears
  nowhere (AC4, AC8).
- Goal-based: `lint-packs`, `validate`, `build`, and `pytest` (pack scripts +
  `packages/agentbundle`) are green; `pack.toml` / `plugin.json` / `marketplace.json`
  are version-consistent (0.3.0 → 0.4.0, regenerated — not hand-edited); a
  `docs/product/changelog.md` `[Unreleased]` entry records the user-visible
  additions (AC12).

**Approach:**
- Add the no-egress/no-ML guard test; bump the pack **minor** version across the
  three manifests via the pack build; add the changelog entry.

**Done when:** the guard test passes, the gate suite is green, and the manifests are
drift-clean.

## Rollout

- **Delivery:** additive. Today's diagram branch and the Tier-0 document floor are
  unchanged; the general mode and the Tier-1 PDF flow are new paths layered on. No
  data migration, no published event.
- **Reversibility:** code-only in one skill; rollback is a revert. The one forward
  commitment is the new `text-table` strategy value and the `tier: "1-agent-vision"`
  output — both already reserved in `contract.py`, so no contract-version change.
- **Infrastructure / external systems:** none in-repo. The **adopter** must install
  `pdf2image` (pip, on demand) and a **system Poppler** binary to use the Tier-1 PDF
  path; SKILL.md documents this. No egress, no new services.
- **Deployment sequencing:** the general render (T1) before the rasterization flow
  that feeds it (T2/T3); publish is the pack version bump (T6). No
  consumer-before-producer ordering beyond that.

## Risks

- **`pdf2image` needs a system Poppler binary a locked-down org may not be able to
  install.** This is the residual friction the MIT constraint leaves (the
  self-contained `pypdfium2` is Apache/BSD, not MIT, and outside the RFC's set).
  Mitigate by honest degradation (the standalone rasterizer exits with a no-crash
  message and the agent retains the Tier-0 `.md` per SKILL.md) and by documenting the
  prerequisite.
  If the friction bites in practice, revisit `pypdfium2` via an RFC erratum (noted in
  the spec's declined patterns).
- **Vision-read hallucination on scans.** Bounded by the text-layer cross-check
  (T3) and honest `requires-review`; a true scan with no text layer relies on the
  read's own confidence — an accepted, flagged limitation (survey F5/C12).
- **Pip-on-demand dep sits outside lockfile SCA.** `pdf2image` resolves at runtime,
  so repo SCA won't see it; pin a floor version in `PIP_INSTALL` and document the gap
  (same posture the floor took for `pypdf`).
- **PR size.** D4 render + Tier-1 rasterization + cross-check is broad. If the PR
  grows past ~400 lines, prefer keeping the whole slice together — every task maps to
  a shipping (un-deferred) AC, so splitting one out would leave its AC unmet. If a
  split is truly needed, it is only legal by **pre-registering a `docs/backlog.md`
  anchor** and marking the deferred AC `(deferred: <anchor>)` per CONVENTIONS §4 —
  never a silent unchecked AC. Note any split in this changelog.

## Changelog

- 2026-07-01: initial plan — second RFC-0058 slice (D4 general text/table mode +
  Tier-1 PDF-page rasterization). Reuses the predecessor floor's `contract.py`,
  `safe_io`, the reconcile machinery, and the `_extract_pdf` escalation hook. General
  mode as a `reconcile.py` strategy (T1); `pdf2image` (MIT) rasterizer behind a
  `--check` probe with absent-lib degradation tested first (T2); text-layer
  cross-check (T3); untrusted-data defense on the read reference (T4);
  SKILL.md orchestration (T5); no-egress/no-ML guard + release (T6). `pymupdf`
  rejected (AGPL) per user MIT constraint; `pypdfium2` flagged as a follow-on.
- 2026-07-01: spec-stage review (adversarial + security). Hardened: (S1/AC11)
  `reconcile.py`'s writes are *unconfined today* — route them through `safe_io.confine`
  rather than claiming reuse; (S2/AC11) confine the rasterizer's page-image work dir +
  generated filenames; (S3+S4/AC7) reworded — the read reference's delimiter+directive
  is the injection defense, the "verbatim body" test is a contract-non-forgery test
  (body is not escaped); (S5+A6/AC10) multi-axis rasterization ceiling (DPI + bytes +
  a calibrated page cap, *not* the floor's 5000); (S6/AC4) pinned `PIP_INSTALL` +
  SCA-gap note; (A1/AC2) general-mode dedup keying function (prose/rows lack a
  diagram `name`); (A2/AC4) degradation ownership — the *agent* retains the Tier-0
  `.md`, not `rasterize_pdf.py`; (A3/AC1) pinned `content-category: general-text-table`
  as the distinguisher (tier alone can't); (A4+A5/AC6) named Jaccard threshold +
  whole-document granularity; (A7) dropped the `§ Errata` citation qualifier; (A8)
  removed the invitation to split T3 (would leave AC6 unmet) — split now legal only
  via a pre-registered backlog anchor.
