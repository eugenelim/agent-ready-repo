# Converter skills

The four skills in the `converters` pack, their inputs, outputs, flags, and prerequisites. Each skill is a thin wrapper: the agent invokes a script and reports the result.

| Skill | Direction | Engine |
| --- | --- | --- |
| [`file-to-markdown`](#file-to-markdown) | documents/images → Markdown | Docling / vision pipeline |
| [`mermaid-renderer`](#mermaid-renderer) | Markdown → Markdown + images | Mermaid CLI (`mmdc`) |
| [`markdown-to-html`](#markdown-to-html) | Markdown → HTML | `marked` + `highlight.js` |
| [`msg-to-markdown`](#msg-to-markdown) | Outlook `.msg` → Markdown | `@nicecode/msg-reader` / `msgreader` |

---

## `file-to-markdown`

Convert documents and images to Markdown. Two branches, selected by input type.

**Source:** [`packs/converters/.apm/skills/file-to-markdown/`](../../../../packs/converters/.apm/skills/file-to-markdown/SKILL.md)

### Inputs

| Branch | Extensions | Path |
| --- | --- | --- |
| Document | PDF, DOCX, PPTX, XLSX, XLS | `scripts/convert.py` (Docling) |
| Image | PNG, JPG, JPEG, TIFF, BMP, WEBP, GIF | `scripts/split_image.py` + agent vision + `scripts/reconcile.py` |

### Prerequisites

| Branch | Needs | Install |
| --- | --- | --- |
| Document | Docling, Pillow | `python -m pip install docling Pillow` |
| Image | Pillow | `python -m pip install Pillow` |

The first Docling run downloads ML models (~1–2 min); later runs are fast. Confirm Docling is importable with `python -c "import docling"` (exit 0 → proceed; non-zero → not installed).

### Document branch

```bash
python scripts/convert.py "<input-file>"
```

Writes `<basename>.md` next to the input. One file per call — loop for a batch. Stdout markers:

| Marker | Meaning |
| --- | --- |
| `OUTPUT: <path>` | Path to the written Markdown file |
| `LINES: <n>` / `WORDS: <n>` | Counts |
| `WARNING: <msg>` | Non-fatal (e.g. sparse text); surfaced to the user |

### Image branch

A two-pass sliding-window pipeline:

| Step | Command | Output |
| --- | --- | --- |
| Recommend | `split_image.py recommend --input <image>` | JSON: source dims, single-pass flag, recommended viewport/stride |
| Overview | `split_image.py overview --input <image> --output-dir <dir>/ --max-dim 1200` | `<dir>/overview.png` (agent reads it for a structural map) |
| Detail | `split_image.py detail --input <image> --output-dir <dir>/ --viewport 1200 --stride 800` | `tile_W0_R<row>_C<col>.png` + `detail_manifest.json` |
| Reconcile | `reconcile.py --manifest … --extractions … --strategy <name> --title "…" --output-json <dir>/merged.json --output-md <output>.md` | merged JSON + final Markdown |

The agent reads each detail tile and writes `<dir>/extractions.json`, choosing one extraction strategy: `architecture`, `event-storm`, `process`, `domain`, or `conceptual`. `reconcile.py` then translates tile coordinates to global ones, collapses duplicates by `(type, normalized_name)` and by IoU ≥ 0.5, picks canonical records by confidence then tile-centrality, sorts by the structural map's layout, and emits Markdown with YAML frontmatter. Reconcile stdout: `OUTPUT_JSON`, `OUTPUT_MD`, `ELEMENTS`, `AMBIGUITIES`.

### Edge cases

| Situation | Behavior |
| --- | --- |
| Image ≤ 1200 px on both dims | Skip overview; run a single detail tile (`--viewport`/`--stride` = max dim) |
| Source > 8000 px on a side | Script auto-prescales before tiling, records the factor in the manifest |
| Scanned PDF | Docling applies OCR automatically; surfaces any `WARNING:` |
| Password-protected file | Document branch fails fast; remove the password first |
| Detail pass > 100 tiles | `split_image.py` warns; raise `--stride` or lower `--viewport` |
| Tile read fails | Skipped; reconciler reports the gap in `ambiguities` |

---

## `mermaid-renderer`

Extract ` ```mermaid ` fenced blocks from a Markdown file, render each to an image, and write a rewritten Markdown file with each fence replaced by an image reference. The original input is not modified.

**Source:** [`packs/converters/.apm/skills/mermaid-renderer/`](../../../../packs/converters/.apm/skills/mermaid-renderer/SKILL.md)

### Prerequisites

The Mermaid CLI (`mmdc`), installed via `npm install -g @mermaid-js/mermaid-cli` (or a project-local `node_modules/` on `PATH`). No Python deps beyond the standard library. Verify with `python scripts/render_mermaid.py --check` (exit 0 → ready; exit 2 → not installed).

### Command

```bash
python scripts/render_mermaid.py --input report.md --output-dir ./rendered [flags]
```

| Flag | Meaning |
| --- | --- |
| `--input PATH` | Source Markdown file. Required. |
| `--output-dir DIR` | Directory for images **and** the rewritten Markdown. Default: `./mermaid-out`. |
| `--format png\|svg` | Output format. Default: `png`. |
| `--theme default\|forest\|dark\|neutral` | Mermaid theme. Default: `default`. |
| `--background white\|transparent\|#hex` | Background color. Default: `white`. |
| `--prefix NAME` | Output filename prefix. Default: `mermaid`. |
| `--width N` | Output width in px (passes to `mmdc -w`). |
| `--height N` | Output height in px (passes to `mmdc -H`). |
| `--check` | Verify `mmdc` is on `PATH`; exit 0 or 2. |
| `--verbose` | Debug logging. |

### Outputs

- `<output-dir>/<prefix>-1.<ext>`, `<prefix>-2.<ext>`, … — one image per block, numbered in document order.
- `<output-dir>/<input-basename>.md` — rewritten copy with each fence replaced by a Markdown image reference.

Stdout: `OUTPUT_DIR`, `REWRITTEN`, `DIAGRAMS`.

### Edge cases

| Situation | Behavior |
| --- | --- |
| No Mermaid blocks | `DIAGRAMS: 0`, input copied through unchanged, exit 0 |
| A block fails to render | Writes `mermaid-N.error.txt`, leaves the fence intact, keeps going, exits non-zero with a failure count |
| Unknown theme | `mmdc` exits with the valid choices; surfaced |
| `mmdc` not on `PATH` | `--check` exits 2 with the install command |

---

## `markdown-to-html`

Convert a Markdown file to a self-contained, styled HTML page (sticky header, sidebar nav, syntax-highlighted code, callout boxes, Mermaid diagrams, print-ready). For documents, not slides.

**Source:** [`packs/converters/.apm/skills/markdown-to-html/`](../../../../packs/converters/.apm/skills/markdown-to-html/SKILL.md)

### Prerequisites

Node.js with `marked` and `highlight.js` (pinned in the skill's `package.json`). Verify from the skill directory with `node -e "require.resolve('marked'); require.resolve('highlight.js')"` (exit 0 → ready; non-zero → run `npm install` once). Add the skill's `node_modules/` to `.gitignore` if the skill lives in a tracked directory.

### Command

```bash
node scripts/render.js <input.md> [flags]
```

| Flag | Meaning |
| --- | --- |
| `--output FILE` | Output path. Default: input with `.html` extension. |
| `--title TEXT` | Page title. Default: first H1, then filename. |
| `--subtitle TEXT` | Header subtitle (small grey text). |
| `--theme navy\|green\|teal\|amber\|rose` | Accent color. Default: `navy`. |
| `--no-mermaid` | Skip the Mermaid CDN script. |

### Outputs

Writes the HTML file and prints three stdout lines:

| Marker | Meaning |
| --- | --- |
| `OUTPUT: <path>` | Path to the written HTML file |
| `SECTIONS: <n>` | Number of h2/h3 anchors built |
| `MERMAID: yes\|no` | Whether Mermaid handling was emitted |

### Handled automatically

- Headings get stable `id` attributes for sidebar links and the print TOC.
- Code blocks are syntax-highlighted; ` ```mermaid ` fences pass through as `<div class="mermaid">` for the runtime CDN renderer.
- Tables are wrapped in `<div class="table-wrap">` for horizontal scroll.
- Paragraphs beginning with `**Note:**`, `**Tip:**`, `**Warning:**`, `**Important:**`, or `**Stop:**` become styled callout boxes.
- Every output includes an `@media print` block; `Ctrl+P → Save as PDF` works out of the box.

### Edge cases

| Situation | Behavior |
| --- | --- |
| Missing dependencies | `render.js` exits 1 with an install hint |
| No headings | Sidebar shows `(no sections)`; output still works |
| Unknown theme | Exits with the list of valid choices |
| Offline output wanted with Mermaid present | Pass `--no-mermaid`; the block falls back to a plain `<pre>` |

---

## `msg-to-markdown`

Convert Outlook `.msg` email files to Markdown, preserving headers (From, To, CC, Date), body content, and attachment metadata.

**Source:** [`packs/converters/.apm/skills/msg-to-markdown/`](../../../../packs/converters/.apm/skills/msg-to-markdown/SKILL.md)

### Prerequisites

Node.js with one of `@nicecode/msg-reader` (preferred) or `msgreader`; `scripts/convert.js` uses whichever is installed. Install with `npm install @nicecode/msg-reader`. Verify from the skill directory:

```bash
node -e "try{require.resolve('@nicecode/msg-reader')}catch{require.resolve('msgreader')}"
```

### Commands

| Command | Purpose |
| --- | --- |
| `node scripts/convert.js "<file>.msg"` | Convert one `.msg` to Markdown |
| `node scripts/extract-attachments.js "<file>.msg"` | Extract attachments to a folder |

For a glob like `emails/*.msg`, loop over each file individually.

### Output

Structured Markdown with a header table (From/To/CC/Date), the body, and attachment metadata. HTML bodies are converted (complex CSS or conditional Outlook markup may be simplified).

### Edge cases

| Situation | Behavior |
| --- | --- |
| RTF-only body | Flagged; re-save as HTML in Outlook or install an RTF parser |
| Winmail.dat / TNEF | May not parse; `node-tnef` suggested |
| Inline images (`cid:`) | Stored as attachments; broken refs until extracted |
| Reply chains | Quoted replies preserved as nested blockquotes |
| Unusual encoding | Re-read as UTF-8 / UTF-16LE / Windows-1252 |
| Calendar `.ics` attachment | Offered for parsing into a structured section |
| Sensitivity labels | Included in the metadata table when present |

---

For task recipes, see the [how-to guides](../README.md#how-to). Installing and upgrading the pack live in [`../../_shared/`](../../_shared/).
