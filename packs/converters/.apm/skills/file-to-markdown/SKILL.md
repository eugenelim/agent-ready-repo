---
name: file-to-markdown
description: >
  Convert documents and images to Markdown. Documents (PDF, DOCX, PPTX,
  XLSX, XLS) go through Docling text extraction (`scripts/convert.py`);
  images (PNG, JPG, JPEG, TIFF, BMP, WEBP, GIF) go through a two-pass
  sliding-window vision pipeline whose tiling and reconciliation are
  deterministic (`scripts/split_image.py` and `scripts/reconcile.py`).
  The agent's job is the per-tile vision read; tile dedup and ordering
  are handled by the script.
metadata:
  version: "2.0"
---

# File to Markdown

A skill with two branches:

| Input | Branch | Owner |
|---|---|---|
| PDF, DOCX, PPTX, XLSX, XLS | document | `scripts/convert.py` (Docling) |
| PNG, JPG, JPEG, TIFF, BMP, WEBP, GIF | image | `scripts/split_image.py` + agent vision + `scripts/reconcile.py` |

## Prerequisites

```bash
python -m pip install docling Pillow
```

First Docling run downloads ML models (~1–2 min). Subsequent runs are
fast. Image-only flows need only Pillow.

---

## Document branch

```bash
python scripts/convert.py "<input-file>"
```

Writes `<basename>.md` next to the input. Stdout markers:

| Marker | Meaning |
|---|---|
| `OUTPUT: <path>` | Path to the written Markdown file |
| `LINES: <n>` / `WORDS: <n>` | Counts |
| `WARNING: <msg>` | Non-fatal (e.g., sparse text). Surface to user. |

That's it. Don't pre-process. Don't merge multiple inputs in one call —
loop the command.

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
| First Docling run | Warn the user about the one-time model download (1–2 min). |
| Scanned PDF | Docling applies OCR automatically; output may be lower quality. Surface any `WARNING:` line. |
| Password-protected file | Document branch fails fast. Tell the user to remove the password first. |
| Detail pass > 100 tiles | `split_image.py` warns. Increase `--stride` or reduce `--viewport`. |
| Tile read fails | Skip the tile; the reconciler reports the gap as a missing region in `ambiguities`. |
| Strategy unclear from overview | Default to `conceptual` and surface that decision in the agent's narration. |
