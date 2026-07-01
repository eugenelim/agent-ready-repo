---
name: file-to-markdown
description: Convert documents and images to Markdown for AI context layers. Documents (PDF, DOCX, XLSX, PPTX, HTML, EPUB, CSV/TSV, OpenDocument, .eml) go through `scripts/convert.py`, which extracts at a no-ML Tier-0 floor (pure-Python / stdlib parsers) and falls through to Docling (Tier 2) only for .xls and images; images go through a two-pass sliding-window vision pipeline whose tiling and reconciliation are deterministic (`scripts/split_image.py` and `scripts/reconcile.py`). Every output carries a versioned frontmatter contract (provenance + a quality/confidence signal). The agent's job is the per-tile vision read; tile dedup and ordering are handled by the script.
---

# File to Markdown

Convert documents and images to Markdown for AI context layers. The default,
covering almost every case, is one command:

```bash
python scripts/convert.py "<input-file>"
```

Writes `<basename>.md` next to the input. Don't pre-process; don't merge
multiple inputs in one call — loop the command.

| Input | Branch | Owner |
|---|---|---|
| PDF, DOCX, XLSX, PPTX, HTML, EPUB, CSV/TSV, ODT/ODS/ODP, `.eml`, `.xls`, images | document | `scripts/convert.py` |
| PNG, JPG, JPEG, TIFF, BMP, WEBP, GIF (diagram extraction) | image | `scripts/split_image.py` + agent vision + `scripts/reconcile.py` |

## Tiers — no ML first (progressive disclosure)

`convert.py` routes each input to the lowest tier that can handle it. You do
not choose a tier; the script does.

| Tier | What runs | Handles |
|---|---|---|
| **0 — no ML** | pure-Python / stdlib parsers, no model | PDF (text layer, via `pypdf`), DOCX/XLSX/PPTX, HTML, EPUB, CSV/TSV, ODT/ODS/ODP, `.eml` |
| **1 — agent vision** | in-session per-tile vision read | the image branch below; also the escalation target when Tier-0 PDF text is sparse |
| **2 — approved ML** | Docling | `.xls` and image OCR (the fall-through) |
| **3 — managed API** | — | never reached; the skill makes no network calls |

**Why this matters:** in a locked-down environment where Docling's ML models are
banned or un-fetchable, Tier 0 still converts a digital PDF, an Office file, and
the everyday text formats using only ordinary libraries or the standard library.

Tier-0 PDF and Office use libraries that install on demand (never auto-installed):

```bash
python scripts/convert.py --check          # report which optional libs are present
```

`pypdf` (PDF) and `python-docx` / `openpyxl` / `python-pptx` (Office) are each
optional. When an Office library is absent the extractor degrades to a stdlib
`zipfile` + XML path and still produces Markdown; when `pypdf` is absent PDF
extraction escalates to Tier 1 rather than failing. Docling (Tier 2) is only
needed for `.xls` and images:

```bash
python -m pip install docling Pillow    # only if you need the Tier-2 fall-through
```

## The output contract

Every conversion — document *and* image branch — writes a leading YAML
frontmatter block recording provenance and a quality signal, then the Markdown
body below it:

```yaml
---
contract-version: "1.0"
tier: "0-no-ml"
source-file: "report.pdf"
content-type: "pdf"
ingestion-date: "2026-06-30T12:00:00+00:00"
ingestion-quality:
  extraction-confidence: "high"   # high | medium | low
  requires-review: false
---
```

`contract-version` is how a consumer detects the shape. When extraction is
sparse or degraded, `extraction-confidence` is `low`, `requires-review` is
`true`, and an `escalation-target` names the tier to retry at — so low-quality
output is flagged, never emitted silently.

Stdout markers:

| Marker | Meaning |
|---|---|
| `OUTPUT: <path>` | Path to the written Markdown file |
| `LINES: <n>` / `WORDS: <n>` | Counts |
| `WARNING: <msg>` | Non-fatal (e.g., `requires-review`). Surface to user. |

## Trust posture

Document inputs are treated as **untrusted** (they feed AI context layers): XML
is parsed with an XXE-safe stdlib parser (DTDs refused), zip-based formats are
guarded against decompression bombs before decompression, the output path is
confined to the input's directory, and each parser enforces a coarse resource
ceiling. This is a deliberate divergence from the image branch's
local-files-trusted stance.

---

## Image branch

A two-pass sliding-window pipeline. The script tiles the image so every
element appears intact in at least one tile; the agent reads each tile;
the script reconciles.

### Step 1 — Recommend settings (optional but cheap)

```bash
python scripts/split_image.py recommend --input <image>
```

Returns JSON with source dimensions, whether a single pass suffices,
and recommended viewport/stride. If both dims ≤ 1200 px, you can skip
straight to a one-tile detail run with the original image.

### Step 2 — Generate the overview

```bash
python scripts/split_image.py overview \
  --input <image> --output-dir <work-dir>/ --max-dim 1200
```

Read `<work-dir>/overview.png` with vision. Produce a **structural map**:

```json
{
  "diagram_type": "<architecture | event-storming-... | process-... | domain-... | conceptual>",
  "layout": "left-to-right | top-to-bottom | radial | unspecified",
  "summary": "<one or two sentences>"
}
```

### Step 3 — Generate detail tiles

```bash
python scripts/split_image.py detail \
  --input <image> --output-dir <work-dir>/ \
  --viewport 1200 --stride 800
```

Writes `tile_W0_R<row>_C<col>.png` files plus
`<work-dir>/detail_manifest.json`.

### Step 4 — Read each tile and write extractions JSON

For each tile in the manifest, read its image and emit elements.
The shape of the per-tile elements depends on the strategy.

**Pick one strategy and load its reference file:**

| If the diagram is… | Read |
|---|---|
| C4 / architecture / deployment | [`references/strategy_architecture.md`](references/strategy_architecture.md) |
| Event-storming board | [`references/strategy_event-storm.md`](references/strategy_event-storm.md) |
| Process flow / swimlane / BPMN | [`references/strategy_process.md`](references/strategy_process.md) |
| Domain model / ER / class | [`references/strategy_domain.md`](references/strategy_domain.md) |
| Anything else | [`references/strategy_conceptual.md`](references/strategy_conceptual.md) |

Do **not** load any other strategy file unless you switch.

The full schema for the extractions file is at
[`references/extractions_schema.md`](references/extractions_schema.md).
Write it to `<work-dir>/extractions.json`.

### Step 5 — Reconcile

```bash
python scripts/reconcile.py \
  --manifest <work-dir>/detail_manifest.json \
  --extractions <work-dir>/extractions.json \
  --strategy <name> \
  --title "<document title>" \
  --output-json <work-dir>/merged.json \
  --output-md <output>.md
```

The script:

- translates `bbox_in_tile` → global source coordinates
- collapses duplicates by `(type, normalized_name)` and by IoU ≥ 0.5
  within the same type
- picks canonical records by confidence then tile-centrality
- sorts by the structural map's `layout`
- emits a Markdown file with YAML frontmatter (ingestion-quality
  fields, ambiguity counts, processing parameters)

Stdout: `OUTPUT_JSON`, `OUTPUT_MD`, `ELEMENTS`, `AMBIGUITIES`.

### Step 6 — Save and report

If the agent wrote `<output>.md` directly to the user's project, you're
done. Surface element count, confidence distribution, and any
ambiguities. Clean up `<work-dir>` (or keep it if the user wants to
re-extract).

---

## Don't

- Don't dedupe across tiles in chat. Emit every observation; the
  reconciler handles `(type, name)` collapse and IoU merging.
- Don't sort canonical order yourself. The reconciler reads the
  structural map's `layout` and sorts deterministically.
- Don't write the YAML frontmatter by hand. `reconcile.py` produces it.
- Don't load more than one strategy reference per call. They are
  mutually exclusive guides.
- Don't fabricate elements that aren't visible in the source. If
  confidence is `low`, mark it `low` — the script surfaces that as
  `requires-review: true` in the output.
- Don't bypass the script and write the merged JSON yourself. The
  reconciler is the single source of canonical order.

## Edge cases

| Situation | Action |
|---|---|
| Image ≤ 1200 px on both dims | Skip overview; run `detail` with `--viewport <max-dim>` and `--stride <max-dim>` so you get a single tile. |
| Source > 8000 px on a side | The script auto-prescales before tiling and records the scale factor in the manifest. No agent action needed. |
| First Docling run (`.xls` / image only) | Warn the user about the one-time model download (1–2 min). |
| Scanned / image-only PDF | Tier 0 finds little or no text layer, so the output is flagged `extraction-confidence: low` + `requires-review: true` and names Tier 1 (agent vision) as the escalation target. Surface the `WARNING:` line. |
| Password-protected file | Document branch fails fast. Tell the user to remove the password first. |
| Detail pass > 100 tiles | `split_image.py` warns. Increase `--stride` or reduce `--viewport`. |
| Tile read fails | Skip the tile; the reconciler reports the gap as a missing region in `ambiguities`. |
| Strategy unclear from overview | Default to `conceptual` and surface that decision in the agent's narration. |
