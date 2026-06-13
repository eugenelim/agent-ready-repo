# Render Mermaid diagrams to images

Your Markdown has ` ```mermaid ` fenced blocks, and the tool you're shipping to doesn't render Mermaid live — Confluence, a PDF pipeline, a slide deck. The `mermaid-renderer` skill extracts each fence, renders it to a PNG (or SVG), and writes a rewritten copy of your Markdown with every fence swapped for an image reference. Your original file stays untouched.

## Before you start

The renderer shells out to the Mermaid CLI (`mmdc`). Install it once:

```bash
npm install -g @mermaid-js/mermaid-cli
```

If your project already ships `mmdc` in a local `node_modules/`, that works too — the script finds `mmdc` on your `PATH`. There are no Python dependencies beyond the standard library.

Check it's wired up:

```bash
python scripts/render_mermaid.py --check
```

Exit 0 means `mmdc` is ready. Exit 2 means it isn't installed — run the `npm install` above. The skill won't install it for you.

## Render the diagrams

```bash
python scripts/render_mermaid.py --input report.md --output-dir ./rendered
```

That writes, into `./rendered/`:

- `mermaid-1.png`, `mermaid-2.png`, … — one image per block, numbered in document order.
- `report.md` — a rewritten copy where each fence is replaced by a standard Markdown image reference (`![](mermaid-1.png)`).

The stdout summary gives you `OUTPUT_DIR`, `REWRITTEN` (the rewritten file's path), and `DIAGRAMS` (the count). The images and the rewritten Markdown together are a self-contained bundle.

## Common variations

- **SVG instead of PNG:** add `--format svg`.
- **A different look:** `--theme forest|dark|neutral` (default is `default`), `--background transparent` or `--background "#f0f0f0"` (default `white`).
- **Fixed dimensions:** `--width` and `--height` pass straight through to `mmdc`.
- **Rename the outputs:** `--prefix diagram` gives you `diagram-1.png`.

The full flag list is in the [reference](../reference/converter-skills.md#mermaid-renderer).

## Pitfalls

- **No Mermaid blocks.** The script reports `DIAGRAMS: 0`, copies your input through unchanged, and exits 0. Nothing breaks.
- **A block fails to render.** The script keeps going on the rest, writes a `mermaid-N.error.txt` where the image would have been, leaves that fence intact in the rewritten Markdown, and exits non-zero with a failure count. Check the error file for the syntax problem.
- **Unknown theme.** `mmdc` rejects it and lists the valid choices. Pick one from the list.
- **Untrusted input.** The renderer runs `mmdc` on whatever fences it finds. Don't point it at Markdown from an untrusted source without a separate sanitization step.

## Next steps

- Feed the bundle onward: `confluence-publisher` turns the image refs into Confluence image macros, and [`markdown-to-html`](convert-markdown-to-html-and-email.md) uses the rendered images for fully-offline HTML.
- Need the source Markdown first? [Convert documents to Markdown](convert-documents-to-markdown.md).
- The skill itself: [`mermaid-renderer`](../../../../packs/converters/.apm/skills/mermaid-renderer/SKILL.md).
