# Document → Markdown extraction for LLM context layers — applied survey

> Discipline: applied (practitioner-pattern survey)

**Question.** What are the leading methods and tools (2025–2026) for extracting
documents (Office formats, PDF, images) into text/markdown to feed LLM context
layers, what are the typical challenges, and what are the best practices for
chunking / serialization / provenance? Grounding for improvements to the
`converters` pack's `file-to-markdown` (and `msg-to-markdown`) skills.

**Confidence schema.** `[high]` / `[moderate]` / `[low]` / `[uncertain]` per the
research pack's GRADE + applied overlay. Vendor-published benchmarks are
downgraded for `survivorship bias`; fast-moving-domain patterns carry a
`stale prior art` caveat where relevant. Independence is calibrated against the
practitioner taxonomy (same-vendor sources count as one).

---

## 1. Landscape — the tool classes

The field has split into three approaches, and the 2025–2026 consensus is that
**they are complementary, not competitive** — the right architecture routes by
input.

### F1 — There is no single winner; route by document class. `[high]`

Every independent comparison lands on "pick the specialist." Marker is the
safest single default; Docling for enterprise/multi-format + framework
integration; MinerU for CJK and complex layouts; PyMuPDF4LLM for
already-digital PDFs (quick-and-dirty, no ML); MarkItDown for breadth + speed +
zero-GPU. This is stated across multiple independent practitioner comparisons.
*Sources:* [themenonlab 2026](https://themenonlab.blog/blog/best-open-source-pdf-to-markdown-tools-2026),
[jimmysong 2026](https://jimmysong.io/blog/pdf-to-markdown-open-source-deep-dive/),
[LlamaIndex "Best LLM Document Parsers 2025"](https://www.llamaindex.ai/insights/best-llm-document-parser-2025),
[Reducto "LLM-ready parsers 2025"](https://llms.reducto.ai/best-llm-ready-document-parsers-2025).

### F2 — The open-source pipeline tools (Docling / Marker / MinerU / Unstructured). `[moderate]`

- **Docling** (IBM, Apache-2.0): PDF, DOCX, PPTX, XLSX, HTML, images, audio,
  LaTeX. Layout model + TableFormer + OCR + optional VLM pipeline. First-class
  `LangChain`/`LlamaIndex` integration and a native `HybridChunker`. Best for
  enterprise multi-format RAG. Speed ~0.49 s/page on an L4 GPU.
- **MinerU** (OpenDataLab): strongest on complex layouts + CJK; PaddleOCR +
  custom layout models; outputs Markdown *and* JSON; broadest hardware support;
  fastest of the three (~0.21 s/page L4). MinerU 2.5 moved to a decoupled
  vision-language model.
- **Marker** (Datalab): Surya OCR, multilingual, GPU/CPU/MPS; strong structure
  fidelity and image/table handling; ~0.86 s/page L4.
- **Unstructured**: broad connector ecosystem, no GPU benefit, "balanced";
  favored for its ingestion connectors more than raw fidelity.

Speed figures are from a single benchmark ([themenonlab](https://themenonlab.blog/blog/best-open-source-pdf-to-markdown-tools-2026))
→ `[moderate]`, directionally corroborated by the Docling arXiv paper
([2501.17887](https://arxiv.org/pdf/2501.17887)) and [MinerU 2.5 arXiv](https://arxiv.org/pdf/2509.22186).

### F3 — MarkItDown (Microsoft) is the breadth/convenience floor, not the accuracy ceiling. `[moderate]`

MarkItDown converts many formats (Office, PDF, images, audio, HTML) to Markdown
with **no GPU**, ~100 pages in ~12 s, and is widely adopted. It scored ~82% F1
vs Docling ~88% and LlamaParse ~92% in one independent benchmark — i.e. it wins
on speed/breadth/ops-simplicity, loses on fidelity for hard documents. Notably
MarkItDown for PDFs is a thin wrapper (no layout model) — it is weak exactly
where layout matters. *Sources:* [aibuilderclub](https://www.aibuilderclub.com/blog/markitdown-microsoft-convert-files-markdown-llm),
[LlamaIndex OCR-to-markdown eval](https://www.llamaindex.ai/insights/ocr-to-markdown-evaluation).
The F1 numbers are single-benchmark → `[low]` on the exact figures, `[moderate]`
on the ordering.

### F4 — Managed / API OCR now spans a 15–30× price band at converging accuracy. `[moderate]`

- **Mistral OCR** (v3 $2 / 1k pages standard, $1 batch; v4 $4/$2, +$5 tier for
  schema-driven JSON, bounding boxes, typed blocks, 170 languages, self-host):
  the cost-efficiency leader; vendor benchmarks claim table 96.6% and
  handwriting 88.9%.
- **Azure Document Intelligence**: enterprise leader on committed-volume,
  layout/prebuilt models; ~$3,000 / 100k pages custom-extraction tier.
- **AWS Textract**: AWS-native forms/tables; ~$65 / 1k pages for
  forms-and-tables; strong but pricey.
- **AWS Bedrock Data Automation**: newer managed multi-modal extraction (docs,
  images, audio, video) — see Known Unknowns for the gap in independent data.
- **Google Document AI**: layout-critical extraction inside GCP.

Pricing figures come from [aiproductivity.ai cost comparison](https://aiproductivity.ai/blog/document-ai-cost-comparison/)
and [Mistral's own announcements](https://mistral.ai/news/mistral-ocr/) → the
*price band* is `[moderate]`; the *accuracy* claims are **vendor-internal →
`[low]`, survivorship-biased**. Independent table-accuracy figures
(RD-TableBench via Reducto: Reducto 90.2%, Azure DI 82.7%, Textract 80.9%,
Google 64.6%) are **also vendor-published (Reducto) → `[low]`**.

### F5 — Vision-LLM OCR (Gemini / GPT-4o / Claude) wins on degraded/scanned inputs but carries hallucination risk. `[moderate]`

Gemini 2.5 Pro / Flash lead independent scanned-invoice benchmarks (~94% vs
GPT+OCR 91%, Claude 90%), and Gemini Flash is extraordinarily cheap
(~$0.17–$1 per 1k pages). The tradeoff is **fabrication**: LLMs "satisfy" the
prompt and can conjure plausible-but-absent content, and struggle on complex
table structure. Claude 3.5 Sonnet is the practitioner pick for
compliance-sensitive workflows *because* it minimizes hallucination.
Mitigations in the literature: uncertainty-aware grounding, occlusion tests,
and cross-checking against a deterministic OCR pass. *Sources:*
[Parsli LLM-OCR benchmark](https://parsli.co/blog/llm-ocr-vs-traditional-ocr),
[Vellum LLMs-vs-OCR](https://www.vellum.ai/blog/document-data-extraction-llms-vs-ocrs),
["Seeing is Believing?" arXiv 2506.20168](https://arxiv.org/html/2506.20168v2),
[Vectara hallucination leaderboard](https://github.com/vectara/hallucination-leaderboard).

### F6 — Markdown is the empirically-best context format for LLMs. `[moderate]`

Across token count, cost, retrieval accuracy, and answer quality, Markdown beat
other common formats in a GPT-4o evaluation — every table question answered
correctly from Markdown tables. This validates the pack's target format; the
open question is *fidelity of the Markdown*, not the choice of Markdown.
*Source:* [MDSpin best-format benchmark](https://www.mdspin.app/blog/best-document-format-for-llms)
(single source → `[low]` on the magnitudes, `[moderate]` on the direction, which
matches the broad RAG-tooling consensus).

---

## 2. What Docling supports that the current skill does not use

The current `file-to-markdown` document branch calls bare `DocumentConverter()`
then `export_to_markdown()`. That leaves a large, free capability surface on the
table. `[high]` (Docling docs, primary source).

- **Table mode.** `TableStructureOptions.mode` = `FAST` vs `ACCURATE`; also
  `do_cell_matching`. ACCURATE is materially better on hard tables.
  ⚠️ Sources conflict on the *default*: one says ACCURATE has been default since
  1.16.0; a 2.5.2 benchmark reports FAST as the observed default. **Must be
  pinned explicitly rather than relied on.** → default is `[uncertain]`; the
  knob's existence is `[high]`.
- **OCR engine + languages.** Default engine is **EasyOCR** (slow on CPU,
  English-biased defaults). Swappable to Tesseract / RapidOCR / OcrMac, each
  with language lists and confidence thresholds. `[high]`.
- **Enrichment (default OFF):** `do_formula_enrichment` (math → LaTeX),
  `do_code_enrichment`, `do_picture_description` (figure captioning via a VLM),
  `do_picture_classification`. All default disabled → figures/formulas/code in
  the current output are dropped or mangled. `[high]`.
- **Image generation:** `generate_picture_images`, `generate_page_images`,
  `generate_table_images` — needed if you want to persist figures alongside the
  Markdown. Default OFF. `[high]`.
- **VLM pipeline:** `VlmPipeline` (SmolDocling / Granite-Docling, and remote
  VLMs) — an end-to-end vision path for scanned/complex docs, an alternative to
  the layout+OCR pipeline. `[high]`.
- **Execution control:** `document_timeout`, `accelerator_options`,
  `batch_polling_interval_seconds` — none set today, so a pathological PDF can
  hang unbounded. `[high]`.
- **The `DoclingDocument` model + `HybridChunker`.** `export_to_markdown()`
  discards the structured document (reading order, page provenance, bounding
  boxes, table cells). The `HybridChunker` does tokenizer-aware,
  structure-preserving chunking aligned to an embedding model — **exactly the
  "feed context layers" goal**, and it is thrown away today. `[high]`.

*Sources:* [Docling pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/),
[vision models](https://docling-project.github.io/docling/usage/vision_models/),
[hybrid chunking](https://docling-project.github.io/docling/examples/hybrid_chunking/),
[Granite-Docling writeup](https://medium.com/@visrow/ibm-granite-docling-super-charge-your-rag-2-0-pipeline-32ac102ffa40).

---

## 3. The typical-challenge catalogue (and who solves what)

The exhaustive list of "hard things" in document ingestion, each tagged with the
mitigation the field uses. `[moderate]` unless noted.

| # | Challenge | Why it's hard | Field's mitigation |
|---|---|---|---|
| C1 | **Reading order (multi-column, sidebars)** | PDF stores draw commands, not logical order; no marker for column breaks | Layout/reading-order model (Docling layout, MinerU, Marker); vision-LLM often gets this right natively |
| C2 | **Complex tables** (merged cells, nested headers, spanning rows) | Cell→row/col assignment; header inference | TableFormer-ACCURATE, Reducto/Azure table models, Mistral OCR; serialize to GFM + keep cell JSON as sidecar |
| C3 | **Multi-page tables** | Header only on page 1; rows split across page boundary | Cross-page stitching (TurboLens, MinerU); basic tools corrupt partial rows |
| C4 | **Scanned / image-only PDFs** | No text layer; OCR quality gates everything | OCR pass (EasyOCR/Tesseract/RapidOCR) or vision-LLM; **detect and route**, don't silently emit empty |
| C5 | **Headers / footers / page numbers / footnotes** | Noise with no place in reading flow; footnotes float | Layout classifier suppresses running elements; footnotes relocated or tagged |
| C6 | **Math / formulas** | Rendered glyphs, not LaTeX | `do_formula_enrichment`; vision-LLM → LaTeX |
| C7 | **Charts / graphs** | Data encoded visually, no text | Picture description/classification; chart-to-data VLM (largely unsolved → `[low]`) |
| C8 | **Forms (key-value)** | Spatial K:V, checkboxes | Textract/Azure forms models; Mistral typed blocks |
| C9 | **Handwriting** | High OCR error | Mistral OCR / vision-LLM lead here |
| C10 | **Mixed / non-Latin / RTL languages** | Engine language config; script detection | MinerU (CJK), configure OCR languages, Mistral 170-lang |
| C11 | **Rotated / skewed / low-DPI scans** | Deskew, resolution floor | Preprocessing (deskew, upscale); DPI floor before OCR |
| C12 | **Hallucination on vision-LLM reads** | Model invents plausible content | Deterministic cross-check, uncertainty grounding, low-confidence flagging (F5) |
| C13 | **DOCX tracked changes / comments** | Metadata layer outside body | docx2python / Datalab redline extraction; decide accept/reject/annotate |
| C14 | **PPTX speaker notes** | Notes vs slide-body distinction | Extract notes as a labeled section (kaos-office) |
| C15 | **XLSX multi-sheet / merged cells / formulas** | Merged cells expand; formulas → values; sheets need separation | One table per sheet with headings; keep formula text as sidecar; Docling issue #1292 shows multi-sheet gaps |
| C16 | **Embedded images inside Office/PDF** | Dropped by text-only export | `generate_picture_images` + captioning |
| C17 | **Password-protected / encrypted** | Hard fail | Detect early, clear message, never silent-empty |
| C18 | **Corrupt / truncated / zip-bomb files** | Crash or resource exhaustion | Validate, bound resources, fail cleanly |
| C19 | **Huge documents (1000s of pages)** | Time/memory blowup | Timeouts, page ranges, streaming/batched |
| C20 | **Quality blindness** | Output looks fine but is garbage | Confidence/quality scoring + `requires-review` flag on the *document* branch (the image branch already does this) |

*Sources:* [Omdena document-parsing guide 2026](https://www.omdena.com/blog/document-parsing-for-rag),
[compdf "what's hard about PDF text extraction"](https://www.compdf.com/blog/what-is-so-hard-about-pdf-text-extraction),
[TurboLens multi-page tables](https://www.turbolens.io/blog/2026-05-20-multi-page-table-extraction-from-pdfs-without-losing-context),
[Nutrient PDF extraction guide](https://www.nutrient.io/blog/pdf-data-extraction-developer-guide/),
[Datalab tracked-changes extraction](https://www.datalab.to/blog/extract-tracked-changes-metadata),
[kaos-office](https://pypi.org/project/kaos-office/0.1.6/),
[docx2python](https://github.com/ShayHill/docx2python),
[Docling multi-sheet xlsx issue #1292](https://github.com/docling-project/docling/issues/1292).

---

## 4. Chunking / serialization / provenance best practice

### F7 — Extraction quality dominates chunking strategy. `[high]`

The strongest cross-source signal: "clean extraction solves this problem" —
input quality matters more than chunking-algorithm choice for most workloads.
Fix fidelity first, then chunk. This reframes the whole effort: the pack should
prioritize *fidelity + structure preservation* over clever downstream chunking.
*Sources:* [Firecrawl chunking 2026](https://www.firecrawl.dev/blog/best-chunking-strategies-rag)
+ the F1/F6 consensus.

### F8 — Structure-aware chunking, ~400–512 tokens, headings-preserved; overlap is now questioned. `[moderate]`

Recommended default: recursive/structure-aware splitting at 400–512 tokens,
breaking on section headers so "headers stay with their content." Page-level
chunking wins on paginated PDFs (NVIDIA 2024, 0.648 accuracy). A Jan-2026
analysis found chunk overlap gave "no measurable benefit and only increased
indexing cost" — a `stale prior art` flag on the old 10–20%-overlap default.
Semantic and late chunking help recall but cost more. *Source:* [Firecrawl](https://www.firecrawl.dev/blog/best-chunking-strategies-rag).

### F9a — In locked-down enterprises, the ML dependency IS the constraint. `[high]` (user-supplied, decisive)

Constraint from the field: some corporate environments **ban optional OCR/ML
libraries** (Tesseract named as an example) because every AI/ML model must go
through an approval process. You cannot assume you can install a model to handle
PDFs. This inverts the survey's tool ranking:

- **Every leading OSS parser is ML-model-heavy.** Docling (layout model +
  TableFormer + EasyOCR — downloaded on first run), Marker (Surya), MinerU
  (PaddleOCR + layout models), Unstructured (models) — **none are usable where
  unapproved models are banned or egress is blocked.** So "adopt MinerU/Marker"
  is not a portable recommendation; it presumes approval.
- **Docling's first-run model download is exactly the banned pattern.** The
  *current* `file-to-markdown` document branch therefore may be **dead on
  arrival** in these orgs, not merely lower-fidelity.
- **Non-ML parser libraries clear a far lower bar.** `pypdf`/`pdfminer.six`
  (digital-PDF text), `python-docx`/`python-pptx`/`openpyxl` (OOXML) are ordinary
  software, not "AI/ML models" — and Office files are ZIP+OOXML, so a **zero-new-
  dependency** stdlib floor (`zipfile` + XML) exists for DOCX/PPTX/XLSX.
- **The agent's own vision is the sanctioned model.** Where the org has deployed
  Claude Code, *the model is already approved*. Rasterizing pages/images and
  having the agent read them (the image branch's existing pattern) adds **no new
  model** — it reuses the approved one. This makes agent-vision the highest-
  fidelity path that survives the ban, needing only a non-ML rasterizer.

**Design consequence:** the right architecture is **capability-tiered with
graceful degradation and an honest approval posture**, not a single best tool:
- *Tier 0 — no ML:* digital-PDF text (`pypdf`) + OOXML text (stdlib/`openpyxl`).
- *Tier 1 — agent vision:* rasterize → agent reads → reconcile (reuses the
  approved model; no installed OCR).
- *Tier 2 — approved ML pipeline:* Docling/EasyOCR etc., only where approved.
- *Tier 3 — managed API:* Mistral OCR / Azure DI / Textract / Bedrock DA, only
  where cloud egress + vendor are approved (a different approval axis).
The skill detects what's available and degrades loudly, declaring per tier what
needs sign-off. *Source: user constraint (2026-06-30), corroborated by Docling's
documented first-run model download.*

### F9 — Provenance is a first-class output, not an afterthought. `[moderate]`

Chunks must carry traceable metadata (source file, page, section, and ideally
bounding box) so retrieval results are auditable. LlamaExtract 2025 shipped
field-level confidence scoring and self-correction loops; this is the direction
of travel. The current document branch emits **zero** provenance frontmatter
(the image branch already emits rich ingestion-quality frontmatter — an
internal inconsistency). *Sources:* [Firecrawl](https://www.firecrawl.dev/blog/best-chunking-strategies-rag),
[LlamaIndex parsers 2025](https://www.llamaindex.ai/insights/best-llm-document-parser-2025).

---

## 5. Synthesis — the shape of "good" here

1. **Route by input class, then by difficulty.** Digital PDF → fast text path;
   scanned/complex → OCR/VLM path; the choice is not one tool.
2. **Preserve structure end-to-end**, then serialize to Markdown + emit a
   structured sidecar (tables as cell-JSON, provenance per block). Don't collapse
   to a flat string early.
3. **Always emit provenance + a quality/confidence signal**, and set
   `requires-review` when confidence is low or content is sparse — parity with
   the image branch.
4. **Fidelity beats chunking cleverness.** Wire the extractor's own
   structure-aware chunker (Docling `HybridChunker`) rather than re-chunking a
   lossy Markdown string downstream.
5. **Vision-LLM is a capability, not a default** — reach for it on degraded
   inputs, and cross-check to bound hallucination.
6. **Fail loudly** on encrypted/corrupt/oversized inputs; bound resources.

---

## Known unknowns

- **Known-unknown:** The current skill's *actual* output fidelity on real hard
  documents (multi-column PDF, merged-cell XLSX, scanned PDF). Would be closed
  by: running the shipped scripts against a fixture corpus (see the pressure-test
  doc — partially closed by static analysis, fully closed by execution).
- **Known-unknown:** Whether Docling's default table mode is FAST or ACCURATE in
  the version the skill pins. Would be closed by: reading the installed Docling's
  `TableStructureOptions` default, or pinning it explicitly (the safe move).
- **Known-unknown:** AWS Bedrock Data Automation independent accuracy/cost.
  Would be closed by: a third-party benchmark; only AWS-native and vendor
  material found.
- **Unknowable (from public evidence):** True head-to-head accuracy of the
  managed APIs on *your* document mix. Every published table-accuracy number is
  vendor-run on a vendor-chosen corpus (Reducto's RD-TableBench, Mistral's
  internal set); the only settling evidence is a benchmark on the adopter's own
  documents. This is a `do-not-resolve` — pick by constraints (cost, sovereignty,
  ecosystem), not by the leaderboard.
- **Unknowable:** Chart/graph → structured-data extraction (C7) has no
  reliable general solution in the current generation; treat as best-effort.
