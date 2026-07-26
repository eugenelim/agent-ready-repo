# Convert documents to Markdown

**Use this when:** You have a PDF, Word doc, slide deck, spreadsheet, or diagram image and need clean Markdown output.
**Prerequisites:** Docling installed (`pip install docling Pillow`) for documents; the first run downloads ML models; Pillow alone suffices for images.
**Result:** A Markdown file written next to the input, with conversion statistics and any warnings surfaced inline.

You have a PDF, a Word doc, a slide deck, a spreadsheet, or a diagram image, and you want clean Markdown out of it. The `file-to-markdown` skill does this. You point it at a file; it picks the right branch and writes the Markdown next to the input.

## Before you start

The skill has two branches, and they need different tools.

- **Documents** — PDF, DOCX, PPTX, XLSX, XLS — go through [Docling](https://github.com/docling-project/docling).
- **Images** — PNG, JPG, JPEG, TIFF, BMP, WEBP, GIF — go through a vision pipeline that needs [Pillow](https://pypi.org/project/Pillow/).

Install both up front:

```bash
python -m pip install docling Pillow
```

The first Docling run downloads its ML models, which takes a minute or two. Every run after that is fast. If you only ever touch images, you need just Pillow.

## Convert a document

Ask your agent to convert the file, or invoke the document branch directly:

```bash
python scripts/convert.py "report.pdf"
```

It writes `report.md` next to the input and prints an `OUTPUT:` line with the path, plus `LINES:` and `WORDS:` counts. A `WARNING:` line means the conversion worked but something is worth knowing — sparse text on a scanned page, for example. The skill surfaces it.

One file per call. To convert a batch, loop the command over each file rather than passing several at once.

## Convert an image

Diagrams and screenshots don't have extractable text, so the image branch reads them with vision instead. The script tiles the image so every element lands intact in at least one tile, the agent reads each tile, and the script reconciles the reads into one deterministic Markdown file.

Let the agent drive this — it owns the per-tile vision read, which is the one step a script can't do. The flow is:

1. **Recommend settings** (optional, cheap): `python scripts/split_image.py recommend --input diagram.png` returns the source dimensions and suggested tiling.
2. **Overview pass** builds a downscaled `overview.png` the agent reads to classify the diagram (architecture, event-storm, process, domain, or conceptual).
3. **Detail pass** writes the tiles and a manifest.
4. The agent reads each tile and writes an extractions file.
5. **`reconcile.py`** collapses duplicates, sorts by the diagram's layout, and emits the final Markdown with YAML frontmatter.

You don't dedupe, sort, or write the frontmatter yourself — the reconciler is the single source of canonical order. The output records a confidence level per element and flags low-confidence reads as `requires-review: true`.

## Pitfalls

- **Scanned PDF.** Docling runs OCR automatically. Quality drops, and you'll see a `WARNING:` line. Take it as a hint to spot-check the output.
- **Password-protected file.** The document branch fails fast. Remove the password first, then re-run.
- **Small image (≤ 1200 px on both sides).** Skip the overview and run a single detail tile with the viewport and stride set to the image's longest side.
- **Huge image (> 8000 px on a side).** The script pre-scales before tiling and records the factor. No action needed.
- **Docling won't import.** That means it isn't installed. Run the `pip install` above; the skill won't install it for you.

## Next steps

- Got Mermaid in the result? [Render Mermaid diagrams to images](render-mermaid-diagrams.md).
- Want a shareable page? [Convert Markdown to HTML](convert-markdown-to-html-and-email.md).
- Every flag and output marker: [Converter skills reference](../reference/converter-skills.md).
- The skill itself: [`file-to-markdown`](../../../../packs/converters/.apm/skills/file-to-markdown/SKILL.md).
