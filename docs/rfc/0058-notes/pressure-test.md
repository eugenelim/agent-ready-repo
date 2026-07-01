# Pressure-test: `converters` extraction skills (file-to-markdown, msg-to-markdown)

Companion to [`doc-extraction-survey.md`](doc-extraction-survey.md). Findings are
from **static read of the shipped scripts** plus **dynamic probes** against the
installed Docling and the image scripts (Pillow 12.2.0, Docling installed).
Each finding maps to a survey challenge (Cn) where relevant, and carries a
severity. "Confirmed" = reproduced by running the code; "Static" = from reading.

Scope target (per the request): the **Office / PDF** document branch
(`scripts/convert.py`, Docling) and the **image** branch (`split_image.py` +
agent vision + `reconcile.py`). `msg-to-markdown` skimmed for completeness.

---

## A. What is actually solid (don't touch)

Pressure-testing should be honest about what holds up:

- **Tiling coverage is correct.** Probed a 2500×900 image: tiles snap at
  x=0/800/1300 with 33% overlap, no gaps, **no duplicate crop boxes**. The
  edge-snapping (`x = max(0, img_w - viewport)`) works. The "every pixel in ≥1
  tile" invariant holds. `[Confirmed]`
- **Docling defaults are better than the survey's web sources implied.** Probed
  the installed version: `do_ocr=True`, `do_table_structure=True`, **table mode
  = ACCURATE**, `do_cell_matching=True`, OCR engine `auto`. So bare
  `DocumentConverter()` already gets accurate tables + OCR. The "FAST is default"
  web claim is stale for current Docling. `[Confirmed]`
- **Prescale + decompression-bomb handling** for huge images is present and
  reasonable (MAX_IMAGE_PIXELS disabled deliberately for trusted local files;
  8000px auto-downscale; 50 MB tile ceiling).
- **The image branch's frontmatter is exemplary** — provenance, confidence
  distribution, ambiguity count, `requires-review`. This is the bar the document
  branch fails to meet (see D1).

---

## B. Document branch (convert.py / Docling) — findings

### B1 — No provenance or quality metadata on document output. `[Static]` — HIGH
`export_to_markdown()` produces a bare string; the skill writes it to
`<basename>.md` with **no frontmatter at all**. No source path, page count,
extraction date, OCR-applied flag, confidence, or `requires-review`. This is
inconsistent with the image branch (which emits rich frontmatter) and directly
defeats the stated goal of "feeding context layers," where provenance is
first-class (survey F9). Maps to **C20**.

### B2 — Quality blindness: the only signal is `words < 20`. `[Static]` — HIGH
A scanned PDF that OCRs to plausible-but-wrong text, a mostly-image PDF that
yields 25 garbage words, or a partial extraction all pass silently. There is no
confidence score, no per-page coverage check, no "OCR was applied" surfacing
beyond the `<20 words` heuristic. Maps to **C4, C20**. Survey F5/F9: quality
signal must be first-class.

### B3 — All Docling enrichment is off; figures, formulas, code are dropped. `[Confirmed]`
Probed defaults: `do_formula_enrichment=False`, `do_code_enrichment=False`,
`do_picture_description=False`, `do_picture_classification=False`,
`generate_picture_images=False`. So math becomes garbled inline glyphs, code
blocks lose fidelity, and **every embedded image/chart is silently discarded**
with no placeholder or caption. Maps to **C6, C7, C16**. The skill can't even
tell the user a figure was dropped.

### B4 — No timeout / page bound. `[Confirmed]`
`document_timeout=None`. `convert.py` sets nothing. A pathological or very large
PDF (survey C19) can hang unbounded — bad for an interactive agent skill and for
any batch use. No `--max-pages` / page-range option either.

### B5 — Error handling is coarse; "fails fast" on password is not implemented. `[Static]`
SKILL.md claims "Password-protected file → Document branch fails fast. Tell the
user to remove the password." But `convert.py` has **no password/encryption
detection** — it just lets Docling raise, caught by the generic
`except Exception as e: print("ERROR: {e}")`. The user gets a raw stack-ish
message, not the documented guidance. Same for corrupt/truncated files (C17,
C18). Doc/skill drift.

### B6 — `.xls` (legacy binary) support is asserted but unverified. `[Static]`
`SUPPORTED` includes `.xls`. Docling's support for the old OLE2 `.xls` format is
shakier than `.xlsx`; the skill makes no distinction and has no fallback. Likely
silent failure or empty output on real `.xls`.

### B7 — Office-format semantics are lost with no acknowledgement. `[Static]` — MEDIUM
Via `export_to_markdown()` the skill inherits Docling's Office handling with no
routing or notice for: DOCX **tracked changes / comments** (C13 — accepted or
dropped? user isn't told), PPTX **speaker notes** (C14 — slide-body vs notes not
distinguished), XLSX **multi-sheet** layout and **merged cells / formulas** (C15
— Docling issue #1292 shows multi-sheet gaps; formulas collapse to values with
no sidecar). None of these are surfaced as caveats.

### B8 — Flat Markdown throws away the structured `DoclingDocument` + chunker. `[Static]` — HIGH (strategic)
The single most consequential gap for the "context layers" goal (survey F7/F8):
the skill collapses straight to a Markdown string, discarding reading order,
page provenance, table cell structure, and the ability to use Docling's
`HybridChunker`. Anyone feeding this into RAG must re-chunk a lossy string
downstream — the exact anti-pattern the survey warns against.

### B9 — OCR language is not configurable; non-Latin/RTL underserved. `[Confirmed]`
OCR `lang=[]` (auto). No skill-level way to set languages for CJK/Arabic/etc.
(survey C10). MinerU/Mistral lead here; the skill offers no path.

---

## C. Image branch (split_image + reconcile) — findings

### C1(img) — The branch only does *diagrams*, not the most common image needs. `[Static]` — HIGH
The whole image pipeline is a **diagram-element extractor** (architecture /
event-storm / process / domain / conceptual). The *typical* image-ingestion
need — a **screenshot or photo of prose**, a **table image**, a **receipt/form**,
an **infographic**, a **chart** — has no path. Feeding any of those forces the
agent to emit typed "elements" into a table, which is lossy nonsense for running
text or tabular data. There is no plain "OCR this image to Markdown text" mode.
This is the biggest scope gap versus what users actually hand a converter.
Maps to **C2, C4, C7, C8**.

### C2(img) — Silent merge of legitimately distinct same-label nodes. `[Confirmed]` — HIGH
`reconcile.py` collapses by `(type, normalized_name)` **before** any spatial
check. Probed: two `step "Validate"` at opposite corners (IoU = 0, 900px apart)
merged into **one** element — count 3→1 — **with `AMBIGUITIES: 0`**. Real
process/architecture diagrams routinely repeat labels ("Approve", "Review",
"Retry"). This is **silent data loss**, not flagged for review. The dedup should
be spatial-first, or same-label-but-disjoint-bbox should be preserved (or at
least recorded as an ambiguity).

### C3(img) — Unnamed elements silently dropped. `[Confirmed]` — MEDIUM
Same probe: an element with `name: ""` (an unlabeled box/connector — very common)
is dropped at `reconcile.py:146` (`if not name: continue`) and **not counted**
anywhere — not in elements, not in ambiguities. The output silently understates
the diagram.

### C4(img) — Reading order is bbox-centroid, not true reading order. `[Static]` — MEDIUM
`sort_canonical` sorts by global x or y from the structural-map `layout` hint.
For anything but a clean L-R / T-B flow (radial, nested, swimlane) the emitted
order can misrepresent sequence. Acceptable for a rough map; not for
process-step ordering (survey C1).

### C5(img) — Animated GIF / multi-frame: only frame 0. `[Static]` — LOW
`Image.open` reads the first frame; multi-frame TIFF/GIF lose the rest silently.

### C6(img) — Two-pass vision is token-expensive and has no cost guard. `[Static]` — LOW/MEDIUM
Overview + N detail tiles, each an agent vision read; `MAX_TILES_WARN=100` only
prints a warning. A large board can mean 50–100+ vision calls. No estimate
surfaced to the user before committing (survey: cost is a real axis).

---

## D. Cross-cutting

### D1 — Two branches, two contracts. `[Static]` — HIGH (coherence)
The document branch and image branch produce **structurally different outputs**
(bare Markdown vs rich-frontmatter typed-element Markdown), use different quality
models (word-count vs confidence distribution), and handle failure differently.
There is no unified "ingestion output contract." For "context layers" this
matters: a consumer can't rely on consistent provenance/quality fields.

### D2 — Format coverage gaps. `[Static]` — MEDIUM
No path for: **HTML**, **EPUB**, **RTF**, **ODT/ODS/ODP** (OpenDocument),
**CSV/TSV**, **`.eml`** email (only Outlook `.msg`), **Jupyter notebooks**,
plain **text/code** normalization. Several are one-liners for Docling/MarkItDown.

### D3 — No batch / directory mode. `[Static]` — LOW
`convert.py` loops argv; there is no recursive directory ingest, manifest, or
skip-on-error-continue for a corpus — the natural "build a context layer from a
folder" workflow.

### D4 — msg-to-markdown is narrow. `[Static]` — LOW
Outlook `.msg` only (no `.eml`/MIME), Node-only dependency, attachments are
metadata-listed but not recursively converted into the context layer.

---

## D5 — Deployment blocker: the document branch depends on banned ML models. `[Confirmed]` — CRITICAL

Field constraint (user, 2026-06-30): some corporate environments **ban optional
OCR/ML libraries** (e.g. Tesseract) — all AI/ML models require approval. Docling
downloads ML models on first run (layout, TableFormer, EasyOCR) and the SKILL.md
even warns about the "~1–2 min model download." **In a locked-down org this is
exactly the prohibited pattern**, and egress to fetch the models is often also
blocked. So the current document branch isn't just lower-fidelity there — it may
be **non-installable**. The pack currently offers **no non-ML fallback**: if
Docling can't be brought in, `file-to-markdown` has nothing for PDFs/Office.

**Required design shift — capability tiers with graceful degradation:**

| Tier | Needs | Handles | Approval bar |
|---|---|---|---|
| 0 — no ML | `pypdf`/`pdfminer.six`; `openpyxl`/`python-docx`/`python-pptx` (or pure `zipfile`+XML for OOXML) | digital PDFs, DOCX/PPTX/XLSX text | ordinary lib (or **zero new deps** for OOXML) |
| 1 — agent vision | non-ML rasterizer (`pymupdf`/`pdf2image`) + the **already-approved agent model** | scanned PDFs, images, tables-as-image | **no new model** — reuses Claude |
| 2 — approved ML | Docling/EasyOCR/Marker/MinerU | best-fidelity full pipeline | model approval required |
| 3 — managed API | Mistral OCR / Azure DI / Textract / Bedrock DA | outsourced OCR | cloud egress + vendor approval |

Tier 1 is the key unlock: the image branch already proves the "rasterize → agent
reads tiles → deterministic reconcile" pattern works **without installing any
OCR model**. Extending it to rasterized *PDF pages* gives locked-down orgs a
high-fidelity path that survives the ban. The skill must **detect** which tiers
are available, pick the best available, and **state per tier what needs sign-off**
rather than hard-failing when Docling is absent.

## E. Severity-ranked shortlist (what a spec should prioritize)

0. **D5 — Capability-tiered pipeline with a no-ML floor + agent-vision path.**
   Now the *governing* constraint: banned-ML environments make this a
   correctness/deployment issue, not an enhancement. Everything below is scoped
   to "within whichever tier is available."
1. **B8 / F7 — Stop discarding structure; emit structured output + wire the
   extractor's chunker** (Tier-2/3 where available). The core "context layers"
   enabler.
2. **C1(img) — Add a general image→text/table mode** (Tier-1 agent vision).
   Biggest real-use gap *and* the ban-resilient path.
3. **B1 + D1 — Unified ingestion output contract with provenance + quality
   frontmatter across both branches.**
4. **C2(img)/C3(img) — Fix silent data loss in the reconciler** (spatial-first
   dedup; preserve/flag unnamed and repeated-label nodes).
5. **B2 — Real quality/confidence signal + `requires-review` on the document
   branch** (parity with the image branch).
6. **B3 — Turn on / expose enrichment** (figures captioned or at least flagged,
   formulas→LaTeX, code) — opt-in, cost-aware.
7. **B4/B5 — Timeouts, page bounds, and honest failure** on encrypted/corrupt/
   oversized inputs (close the SKILL.md ↔ code drift).
8. **B7 — Surface Office-semantic caveats** (tracked changes, speaker notes,
   multi-sheet/merged cells) or handle them explicitly.
9. **B9/C10 — OCR language configuration.**
10. **D2 — Fill high-value format gaps** (HTML/EPUB/CSV/ODT/.eml) — cheap wins.

Deferred / watch (don't over-build): vision-LLM routing for degraded scans
(survey F5 — powerful but adds a model dependency and hallucination surface;
gate behind explicit opt-in), chart→data (C7, largely unsolved), batch mode (D3).
