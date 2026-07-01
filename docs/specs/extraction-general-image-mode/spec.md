# Spec: extraction-general-image-mode

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0058, ADR-0045, ADR-0034 (no bundled per-vendor data / models), RFC-0007 (the converters pack this changes), and the predecessor slice `extraction-tier0-and-output-contract` (whose `contract.py` builder, tier enum, `safe_io` guards, and Tier-1 escalation hook this reuses)
- **Contract:** none — the output is a Markdown file with YAML frontmatter, not an API under `contracts/`. The frontmatter *is* a consumer-facing contract; its shape is the versioned unified contract the predecessor slice pinned (`contract.py`), and this slice adds only the `tier: "1-agent-vision"` value plus the general-mode body shape.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full (work-loop). Risk triggers fired: governance (implements accepted
RFC-0058 D4 + Tier-1, ADR-0045); new dependency (a PDF-page rasterizer — the
load-bearing new dep); security boundary (rasterized/extracted document text is
an untrusted prompt-injection vector fed to the in-session model); public-interface
change (a new image-branch strategy + a new `tier` value in the shipped output).
This is the SECOND RFC-0058 slice, sequenced after
`extraction-tier0-and-output-contract` (the no-ML floor + unified contract).
Deliberately deferred to the last slice (`extraction-higher-tiers`): D5
enrichment / vision-model / managed-API + D6 chunking. -->

## Objective

`file-to-markdown` reads the **non-diagram** image and PDF-page case — a
screenshot of prose, a table image, a form, a receipt, a scanned page — through a
**text/table read**, not the diagram-only extractor it forced everything through
before. This is **Tier 1 (agent-vision)**: the already-running in-session model
(e.g. Claude) reads a rendered image, and the deterministic tiling + reconcile
machinery the diagram branch already uses stitches the reads back together. For a
scanned or image-only PDF — the input the Tier-0 floor flags `requires-review`
and names Tier 1 for — the skill **rasterizes each page to an image** and feeds it
through that same read path, giving a locked-down environment a real path for
scans without an installed OCR/ML model. Every Tier-1 extraction carries the
versioned unified output contract with `tier: "1-agent-vision"` and an **honest**
`extraction-confidence` / `requires-review` signal, and is **cross-checked against
the PDF's text layer when one exists** so a hallucinated read is caught rather than
trusted. The read treats all rasterized and extracted document text as **untrusted
data to transcribe, never instructions to follow**. Tier 1 adds **no new network
egress from the skill**; where the in-session model is cloud-hosted, document
content reaches that already-approved endpoint (an air-gapped or local model sends
nothing) — the skill itself makes no network call and never reaches Tier 3.

## Boundaries

### Always do

- Keep source changes inside `packs/converters/.apm/skills/file-to-markdown/`
  (`SKILL.md`, `scripts/`, `references/`), plus the pack version files
  (`pack.toml`, `.claude-plugin/plugin.json`), the top-level
  `.claude-plugin/marketplace.json` (regenerated), and `docs/product/changelog.md`.
- **Reuse the existing machinery; do not fork it.** The general text/table mode
  reuses `split_image.py` tiling and `reconcile.py`'s bbox-translate → spatial
  dedup → reading-order machinery; the output contract is emitted through the
  existing `contract.build_frontmatter(...)` with `tier=contract.TIER_1`. No second
  tiling engine, no second reconcile engine, no second frontmatter builder.
- Route by the **existing overview classification**: a diagram routes to one of
  the five existing diagram strategies (`architecture` / `event-storm` / `process`
  / `domain` / `conceptual`), unchanged; anything else (prose, table, form,
  receipt, scan) routes to the **new general text/table strategy**, which emits
  Markdown prose and Markdown tables rather than typed diagram elements.
- Treat every rasterized page image and every string extracted from it as
  **untrusted data**: the Tier-1 read reference **wraps the document content in an
  explicit delimiter** (a tagged `<document_content>…</document_content>` region)
  and instructs the in-session model that everything inside it is *data to
  transcribe, never instructions to act on* — the OWASP LLM01 delimit-and-tag
  control, not a bare prose directive. A page reading "ignore prior instructions…"
  is transcribed into the Markdown body verbatim, not obeyed. (This is a
  security-boundary control — `security-reviewer` gates it at spec and diff.)
- Cross-check the Tier-1 read against the source's **text layer when one exists**
  (the whole-document `pypdf` text the Tier-0 floor already extracts) using a named
  overlap metric and threshold: below the threshold sets `requires-review: true` and
  surfaces the discrepancy, bounding hallucination. The comparison concatenates both
  sides whole-document (not per-page vs. whole-document) so a page-by-page read is
  not spuriously flagged.
- Emit an honest quality signal: a low-confidence, sparse, or contested read is
  `extraction-confidence: low` + `requires-review: true` — never emitted as a
  confident read silently.
- Resolve the PDF-page **rasterizer** pip-on-demand exactly like the floor's
  Tier-0 libraries — an import-probe reachable via a `--check` verb (a `PIP_INSTALL`
  constant carrying a **pinned floor version**, exit 0 present / 2 absent), never
  auto-installed. When the rasterizer or its system prerequisite is absent,
  `rasterize_pdf.py` exits with a clear, actionable, no-crash message; the **agent
  retains the Tier-0 `.md` `convert.py` already wrote** (per SKILL.md) rather than
  discarding it — the "keep the Tier-0 output" degradation is the agent's, not the
  standalone script's.
- Bound rasterization on **more than page count**: a capped render DPI (bounding
  per-page pixels) and a cumulative output-byte ceiling across pages, plus a coarse
  page cap — because a low-page-count PDF at pathological page dimensions or DPI is still
  unbounded allocation (the floor guarded resource exhaustion on multiple axes for
  the same reason).
- **Route every output write through `safe_io.confine`** (realpath + component
  containment). `reconcile.py`'s `--output-md` / `--output-json` writes are
  *unconfined today* — this slice adds the guard there (mirroring `convert.py`), so
  the general-mode output cannot be redirected outside its directory. The
  rasterizer's page-image work dir is likewise created under a caller-controlled,
  confined work root with **generated** page filenames (never derived from untrusted
  input). Every Tier-1 output carries the full unified contract.

### Ask first

- Adding the PDF-page rasterizer dependency. It is **`pdf2image`** (MIT-licensed;
  it wraps a system Poppler binary, `pdftoppm`/`pdftocairo`, invoked as a separate
  process — GPL, but a separate process, so no licence propagation to the skill's
  added Python dependency), resolved **pip-on-demand via `--check`** with a pinned
  floor version in `PIP_INSTALL` (not a hard `pack.toml` runtime dep). Because it
  resolves at runtime it sits outside lockfile SCA — the pin + a SKILL.md note are
  the compensating control. **`pymupdf` is explicitly rejected** for its AGPL
  licence. Any *other* new dependency is an escalation.
- Bumping the converters pack's **minor** version (this adds capability, so
  0.3.0 → 0.4.0 is expected — confirm the number).
- Extending the overview-classification schema or adding the sixth (general
  text/table) strategy — it changes the shape the agent produces in the image
  branch.

### Never do

- Add an ML or OCR **model** dependency (Tesseract, EasyOCR, RapidOCR, a
  layout/table model, an installed vision model, Docling for this path). Tier 1 is
  the *already-running in-session* model reading a rendered image — not an
  installed model. Installed OCR/ML is Tier 2+ and out of this slice's scope.
- Use **`pymupdf`** (AGPL) as the rasterizer.
- Introduce **any network egress from the skill** — no HTTP client, no API call.
  Tier 1's "no *new* egress" is a property of *reusing the already-approved
  in-session model*, not of the skill making a call.
- Treat rasterized or extracted document text as instructions rather than data.
- Reach Tier 3 (managed API), or make it reachable by automatic degradation or
  upgrade.
- Flatten, rename, re-nest, or reorder the frontmatter keys the five existing
  diagram strategies emit today — this slice is additive and byte-stable for them.
- Edit projected `.claude/` paths by hand — edit the `packs/converters/.apm/`
  source and regenerate.

## Testing Strategy

The in-session vision read itself is the model's judgement and cannot be
unit-asserted; everything deterministic around it is. Each user-visible outcome
from the Objective pairs with a mode:

- **General text/table render (D4) — TDD.** The Objective's "emits Markdown prose
  and tables, not diagram elements" outcome: a fixture per-tile extractions JSON
  for the general strategy, fed to `reconcile.py`, renders prose paragraphs and
  Markdown tables; overlapping tiles' repeated content is deduped and ordered in
  reading order (reusing the existing bbox/IoU machinery). TDD because it is a
  pure function of its input.
- **Tier-1 PDF-page rasterization (D4/Tier-1) — TDD + goal-based.** The "rasterize
  each page to an image" outcome: a unit test with `pdf2image` monkeypatched present
  asserts one image per page (within the ceiling) and `tier: "1-agent-vision"` on the
  assembled output; a unit test with it absent asserts `rasterize_pdf.py` exits with a
  clear no-crash message (retention of the Tier-0 `.md` is the agent's job per
  SKILL.md, not this script's, so the script test asserts only the message).
- **Rasterizer pip-on-demand probe — TDD.** The `--check` verb reports the
  rasterizer present/absent with the correct exit code (0/2) and the pinned-floor
  `PIP_INSTALL` hint, mirroring the floor's probe.
- **Text-layer cross-check (bounds hallucination) — TDD.** Whole-document reads that
  agree above the pinned Jaccard-overlap threshold → `requires-review` stays false;
  ones below it → `requires-review: true` + discrepancy surfaced; no text layer → the
  comparator is a no-op. Pure comparator ⇒ TDD.
- **Untrusted-data / prompt-injection defense (security boundary) — content check +
  documented eval + contract-non-forgery TDD.** The read reference's delimiter
  (`<document_content>…`) and data-not-instructions directive are asserted by a
  content check; the "transcribe, never obey" behavior is a documented eval (the read
  is the model's). Separately, a **contract-non-forgery** TDD test proves a fixture
  whose body contains `ignore all previous instructions …` lands in the body verbatim
  and never in the frontmatter — verifying the leading-block/first-fence guarantee,
  *not* claiming body escaping is the injection defense.
- **Multi-axis rasterization ceiling — TDD.** A PDF exceeding the page cap, the DPI
  cap, or the cumulative-byte ceiling is each refused with `requires-review` and
  an actionable message, not rasterized unbounded.
- **Byte-stability of the diagram strategies — TDD (golden).** The five diagram
  strategies' `reconcile.py` frontmatter is unchanged (keys, order, quoting) after the
  confinement guard is added to the write path; the general strategy is a new branch.
- **Output-path confinement on the reconcile write (added) — TDD.** A `--output-md`/
  `--output-json` path escaping via `..`, a symlink, or the sibling-prefix case is
  refused; an in-root path is accepted (the guard `reconcile.py` lacks today).
- **No new egress / no ML import — goal-based.** A grep/AST guard asserts the
  Tier-1 path imports no network client and no OCR/ML model package, and that
  `pymupdf` appears nowhere.
- **End-to-end agent-vision read — manual / visual QA.** On a real receipt image
  and a real scanned PDF (in an environment with Docling absent), run the documented
  flow and confirm the Markdown body and the `tier: "1-agent-vision"` contract — the
  locked-down happy path this slice exists for.
- **Release hygiene — goal-based.** `pack.toml` / `plugin.json` / `marketplace.json`
  version-consistent (0.3.0 → 0.4.0, regenerated); `lint-packs`, `validate`,
  `build`, `pytest` green; a `docs/product/changelog.md` `[Unreleased]` entry; the
  documented default `python scripts/convert.py "<input-file>"` invocation still the
  one-command floor.

## Acceptance Criteria

- [ ] **AC1 — General text/table strategy (D4), with a distinguishable output
  shape.** The image branch gains a sixth strategy for non-diagram inputs (prose,
  table, form, receipt, scan), selected by the existing overview classification. Its
  per-tile read emits text blocks and tables; `reconcile.py` renders them as Markdown
  **prose and Markdown tables**, not as typed diagram elements. Because every image
  read (diagram and general alike) carries `tier: "1-agent-vision"`, a consumer
  distinguishes the general mode by a **defined `content-category` value**
  (`general-text-table` — added to `reconcile.py`'s `CONTENT_CATEGORY` map, not left
  to fall through to the literal strategy name), which this AC pins as the observable
  contract for the sixth strategy. The five existing diagram strategies are unchanged.

- [ ] **AC2 — Reuse of tiling + reconcile pipeline, with a general-mode dedup key.**
  The general mode reuses `split_image.py` tiling and `reconcile.py`'s
  bbox-translate → dedup → reading-order **pipeline** — no second tiling engine,
  reconcile engine, or frontmatter builder. But the diagram core keys dedup on
  `(type, normalized_name)` + IoU, which prose (no stable name) and table rows (no
  name) do not satisfy; the general strategy therefore supplies a **defined keying
  function** — normalized-text match for text blocks, a row-signature for table rows
  — so overlapping-tile duplicates collapse. This AC names *how* dedup is keyed for
  the general shape; the guarantee is scoped to what that keying delivers (it does
  not claim byte-identical prose across tiles will always merge on IoU alone).

- [ ] **AC3 — Tier-1 PDF-page rasterization.** A scanned / image-only PDF is
  rasterized **page by page** to images and fed through the general read path; the
  assembled output carries `tier: "1-agent-vision"`. This is the path the Tier-0
  floor's sparse-text escalation (`escalation-target: 1-agent-vision`) points at.

- [ ] **AC4 — Rasterizer is MIT and pip-on-demand; no AGPL, no installed model;
  degradation owned correctly.** The rasterizer is **`pdf2image`** (MIT), resolved
  through a `--check` / `PIP_INSTALL` import-probe carrying a **pinned floor version**
  (never auto-installed, not a hard `pack.toml` dep); its system Poppler prerequisite
  and the runtime-resolution SCA gap are documented in SKILL.md. When the rasterizer
  or Poppler is absent, `rasterize_pdf.py` exits with a clear, actionable, no-crash
  message; **keeping the Tier-0 output is the agent's responsibility** — SKILL.md
  instructs the agent to retain the `.md` `convert.py` already wrote and not proceed
  past the escalation signal (the standalone script has no access to `convert.py`'s
  result, so this AC assigns the retention to the agent, and `rasterize_pdf.py`'s own
  test asserts only the no-crash message). `pymupdf` (AGPL) is not used, and no
  OCR/ML model is imported on this path.

- [ ] **AC5 — `tier: "1-agent-vision"` + honest confidence/requires-review.** Every
  Tier-1 extraction emits the unified contract via `contract.build_frontmatter(...,
  tier=contract.TIER_1)` with `extraction-confidence` and `requires-review`
  reflecting the read; a low-confidence, sparse, or contested read is flagged, never
  emitted as a confident read silently.

- [ ] **AC6 — Cross-check against the text layer bounds hallucination, with a named
  threshold and granularity.** When the source PDF has an extractable text layer (the
  `pypdf` text the floor extracts), the Tier-1 read is compared against it using a
  **defined overlap metric and numeric threshold** — Jaccard token-set overlap below
  a pinned value (calibrated at implementation, the way the floor pinned
  `SPARSE_WORD_THRESHOLD = 20`) sets `requires-review: true` and surfaces the
  discrepancy. The comparison is **whole-document on both sides** (the page-by-page
  vision reads concatenated, vs. `pypdf`'s whole-document blob) so a page read is not
  spuriously flagged against a document-wide text layer. When no text layer exists (a
  true scan), the comparator is a no-op and the read stands on its own confidence
  signal.

- [ ] **AC7 — Untrusted-data / prompt-injection defense (security boundary).** The
  **primary control is the read reference** (`strategy_text-table.md`): it wraps the
  rasterized/extracted document content in an explicit **delimiter** (a tagged
  `<document_content>…</document_content>` region) and directs the in-session model
  that everything inside it is **data to transcribe, never instructions to follow**
  (the OWASP LLM01 delimit-and-tag control). A content check asserts both the
  delimiter and the directive are present — not just a prose sentence. The document
  **body is not escaped** (only frontmatter *values* are, by `contract.py`); a `---`
  or injection string in the body is contained as content by the **leading-block-only
  + first-closing-fence** guarantee the predecessor's AC8 established — this AC
  carries that precision so the implementer does not mistake frontmatter escaping for
  the injection defense. The deterministic test — a fixture whose extracted text
  contains `ignore all previous instructions …` lands in the Markdown body verbatim
  and never in the frontmatter/contract — is a **contract-non-forgery** test (it
  verifies the leading-block guarantee), *distinct* from the prompt-injection defense,
  which lives in the reference wording and is exercised as a documented eval.
  `security-reviewer` reviews this AC at spec and on the diff.

- [ ] **AC8 — No new egress; Tier 1 is "no *new* egress," not "no egress."** The
  skill makes no network call anywhere (grep/AST guard); the vision read runs in the
  agent's already-running session. SKILL.md states the egress nuance plainly: an
  air-gapped/local in-session model sends nothing; a cloud-hosted one sends document
  content to the *already-approved* endpoint. Tier 3 is unreachable.

- [ ] **AC9 — The escalation hook now has a real path.** The Tier-0 floor's
  `escalation-target: 1-agent-vision` on sparse-PDF-text is actionable: SKILL.md
  documents that, on seeing the `requires-review` + escalation signal, the agent
  runs the rasterize → read → reconcile Tier-1 flow — closing the loop the floor
  left open.

- [ ] **AC10 — Multi-axis rasterization ceiling (resource exhaustion).** Rasterizing
  is bounded on the three axes that actually gate allocation, not page count alone: a
  **capped render DPI** (which bounds per-page pixels), a **cumulative output-byte
  ceiling** across pages, *and* a coarse **page cap** (`MAX_RASTER_PAGES`) — the last
  **calibrated for
  rasterization cost, not reused from the floor's `MAX_PDF_PAGES = 5000`** (rendering
  a page is far costlier than reading its text layer, so the cap is low-hundreds
  order, pinned at implementation). Any axis exceeded refuses with `requires-review`
  and an actionable message, never rasterizes unbounded.

- [ ] **AC11 — Output-path confinement (added, not assumed) + contract + diagram
  byte-stability.** Both write surfaces are confined: (a) `reconcile.py`'s
  `--output-md` / `--output-json` writes — **unconfined today** — are routed through
  `safe_io.confine` (realpath + component containment, mirroring `convert.py`), with
  `..`-traversal, symlink-escape, and **sibling-prefix** tests; (b) the rasterizer's
  page-image output lands only under a caller-controlled, confined work root with
  **generated** filenames (never derived from untrusted input). Every Tier-1 output
  carries the full unified contract. A golden test proves the five existing diagram
  strategies' *frontmatter* is byte-unchanged (adding the confinement guard to the
  write path does not alter emitted bytes; the general strategy is a new branch, not
  an edit to theirs).

- [ ] **AC12 — Tests + release hygiene + progressive-disclosure default.** New tests
  cover AC1–AC11's deterministic pieces (general render, rasterization invocation +
  degradation, `--check` probe, cross-check comparator, injection-as-data, page
  ceiling, byte-stability, no-egress/no-ML guard) and pass; the converters pack is
  bumped 0.3.0 → 0.4.0 across `pack.toml`, `plugin.json`, and the regenerated
  `marketplace.json`; `docs/product/changelog.md` records the user-visible
  additions; SKILL.md documents the general mode, the Tier-1 PDF flow, the egress
  nuance, and the rasterizer prerequisite as progressive disclosure, and the
  documented **default invocation stays the single `python scripts/convert.py
  "<input-file>"` form**.

## Assumptions

- Technical: the target skill is `file-to-markdown` in the `converters` pack
  (now **v0.3.0**, floor shipped); `contract.py` already exports `TIER_1 =
  "1-agent-vision"`, `build_frontmatter(...)`, and `now_iso()`, which this slice
  reuses unchanged. *(source: repo read of
  `packs/converters/.apm/skills/file-to-markdown/scripts/contract.py` + `pack.toml`,
  2026-07-01.)*
- Technical: the Tier-0 floor left a Tier-1 escalation hook — `convert.py`'s
  `_extract_pdf` returns `escalation=contract.TIER_1` on sparse text, and
  `assemble()` emits an `escalation-target` frontmatter key + a `WARNING:` line;
  this slice implements the path that hook points at. *(source: repo read of
  `convert.py`, 2026-07-01.)*
- Technical: the tiling + reconcile machinery this reuses is `split_image.py`
  (overview / detail / recommend tiling, Pillow-only, no ML) and `reconcile.py`
  (bbox translate → IoU spatial dedup → layout sort → Markdown + contract
  frontmatter); the image branch is agent-orchestrated via SKILL.md and today's five
  strategies are all diagram-typed. *(source: repo read of `split_image.py`,
  `reconcile.py`, `SKILL.md`, 2026-07-01.)*
- Technical: the PDF-page rasterizer is **`pdf2image`** — MIT-licensed on PyPI;
  it wraps the system Poppler binaries (`pdftoppm`/`pdftocairo`) invoked as a
  separate process (Poppler is GPL, but separate-process invocation carries no
  licence propagation to the skill's added Python dependency); `pymupdf` is rejected
  for its AGPL licence. Resolved pip-on-demand via `--check`, mirroring the floor's
  Tier-0 libraries. *(source: [pdf2image PyPI](https://pypi.org/project/pdf2image/)
  + RFC-0058 tier table / Evidence §; user confirmation 2026-07-01 that the
  rasterizer must be MIT-licensed.)*
- Technical: cross-checking the vision read against a deterministic text layer, plus
  low-confidence flagging, is the field's mitigation for vision-LLM hallucination on
  scans. *(source: RFC-0058 notes — survey findings F5, C12, C4.)*
- Product: the general mode rasterizes and reads **every page** of a scanned PDF
  page-by-page, bounded by a coarse page ceiling above which it refuses with
  `requires-review`. *(source: user confirmation 2026-07-01.)*
- Product: the general text/table strategy is **additive** — a sixth strategy
  selected by the existing overview classification, alongside the five unchanged
  diagram strategies. *(source: user confirmation 2026-07-01.)*
- Product: the consumer of the output is an AI **context layer**, for which
  Markdown + provenance + an honest quality signal is the right shape. *(source:
  RFC-0058 Problem & goals + Evidence F6.)*
- Process: RFC-0058 (Accepted 2026-06-30) is the governing decision and ADR-0045
  records the doctrine; this is the D4 + Tier-1 slice its Follow-on artifacts name,
  sequenced after the floor. *(source: `docs/rfc/0058-*.md`, `docs/adr/0045-*.md`.)*
- Process: `converters` is a user-scope-default pack (not in this repo's self-host
  projection), so the version bump drifts `marketplace.json` and the gate is
  `lint-packs` + `validate` + `build` + `pytest` (regenerating `marketplace.json`),
  **not** `build-self` / `pre-pr`. *(source: predecessor spec `plan.md` § Constraints
  + repo convention.)*
- Process: the pack bump is **minor** — 0.3.0 → 0.4.0 (adds capability). *(source:
  user confirmation 2026-07-01.)*

### Declined patterns

- Tempted to use **`pymupdf`** as the rasterizer (single self-contained wheel, no
  system prerequisite, fast); declining — it is **AGPL-3.0**, which the user's
  MIT-only constraint rules out. `pdf2image` (MIT) is the RFC-named MIT option; its
  system Poppler prerequisite is a documented install step, not a licence
  entanglement (separate-process invocation).
- Tempted to reach for **`pypdfium2`** (Apache-2.0 / BSD-3-Clause, self-contained
  wheels, no system Poppler — arguably the best fit for a locked-down org that
  cannot install a system binary); declining in this spec — it is **not MIT** (the
  user's stated constraint) and is **outside RFC-0058's named rasterizer set**
  (`pymupdf` / `pdf2image`), so adopting it would need an RFC erratum. Flagged as a
  follow-on worth revisiting if the system-Poppler prerequisite proves too heavy for
  the target locked-down environments.
- Tempted to build the general mode as a pure Python script that calls the model
  itself; declining — the skill makes **no network call** (Never do); the vision
  read is the agent's own in-session read, orchestrated through SKILL.md exactly as
  the diagram branch already is. A script that called a model would both add egress
  and fork the "agent-vision" mechanism.
- Tempted to run Tier 1 **automatically** whenever a PDF is opened; declining — the
  floor serves digital PDFs at Tier 0, and Tier 1 fires only on the sparse-text
  escalation (a true scan / image-only PDF) or when the agent classifies an image as
  non-diagram. Auto-running rasterization on every PDF would waste the model and
  bury the Tier-0 text path.
- Tempted to fold enrichment / higher-fidelity vision-model or managed-API reads in
  here (D5); declining — those are the last slice (`extraction-higher-tiers`) and
  cross the data-egress boundary D5 governs. This slice is D4 + Tier-1 only.
