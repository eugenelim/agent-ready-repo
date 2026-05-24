---
name: markdown-to-html
description: Convert a Markdown file to a self-contained, styled HTML page (sticky header, sidebar nav, syntax-highlighted code, callout boxes, Mermaid diagrams, print-ready). Use when the user asks to render, convert, or export a `.md` file as a shareable HTML document — not for slides, presentations, or pitch decks. Rendering is deterministic via `marked` + `highlight.js`; the agent only invokes the script.
metadata:
  version: "2.0"
---

# Markdown to HTML

A thin wrapper around `scripts/render.js`. The renderer parses Markdown
deterministically with `marked` + `highlight.js`, post-processes for
callouts and table wraps, builds a sidebar nav and print TOC from
heading IDs, and stamps everything into `scripts/template.html`.

## Instructions

You are not the renderer. The script is. Invoke it and report the path.

### Step 1 — Verify dependencies

```bash
cd skills/converters/markdown-to-html
npm install   # installs marked + highlight.js per package.json
```

(One-time; subsequent runs are cached in `node_modules/`.)

### Step 2 — Render

```bash
node scripts/render.js <input.md> [--output OUT.html] [--title T] [--subtitle S] [--theme NAME] [--no-mermaid]
```

| Flag | Meaning |
|---|---|
| `--output FILE` | Output path. Default: input with `.html` extension. |
| `--title TEXT` | Page title. Default: first H1, then filename. |
| `--subtitle TEXT` | Header subtitle (small grey text next to the title). |
| `--theme NAME` | `navy` (default), `green`, `teal`, `amber`, `rose`. |
| `--no-mermaid` | Skip the Mermaid CDN script (for sources with no diagrams). |

The script writes the HTML and prints three lines to stdout:

```
OUTPUT: /path/to/file.html
SECTIONS: <number of h2/h3 anchors built>
MERMAID: yes|no
```

Surface the output path to the user and the section/mermaid summary if
relevant.

### Step 3 — What the renderer handles automatically

- **Headings** get stable `id` attributes used by sidebar links and the
  print TOC. Don't rewrite the markdown's headings.
- **Code blocks** are syntax-highlighted via `highlight.js`. Fenced
  blocks tagged ` ```mermaid ` pass through as `<div class="mermaid">`
  for the runtime CDN renderer.
- **Tables** are wrapped in `<div class="table-wrap">` for horizontal
  scrolling on narrow viewports.
- **Callouts**: paragraphs that begin with `**Note:**`, `**Tip:**`,
  `**Warning:**`, `**Important:**`, or `**Stop:**` are wrapped in a
  styled callout box. Don't try to add HTML manually — the script
  detects the bold lead-in.
- **Print**: every output includes an `@media print` block that hides
  the sidebar, builds a single-page TOC, and preserves background
  colors. `Ctrl+P → Save as PDF` works out of the box.

### Don't

- Don't write your own HTML. The script is the renderer; if the output
  is wrong, fix the script (or the template).
- Don't pre-process the markdown by hand. The renderer expects raw
  Markdown including any `**Note:**` lead-ins.
- Don't pass `--theme` unless the user asked for a specific accent
  color. `navy` is the default for a reason.
- Don't suggest pasting the rendered HTML into chat. Open the output
  file in a browser.

### Edge cases

- **Missing dependencies**: `node scripts/render.js` exits 1 with an
  install hint. Run `npm install` from the skill directory.
- **No headings**: sidebar shows `(no sections)`. Output still works,
  the sidebar just stays empty.
- **Custom theme requested by name not in the list**: the script exits
  with the list of valid choices. Ask the user which to use; don't
  invent a sixth.
- **Source contains a Mermaid block but you want fully offline output**:
  pass `--no-mermaid` and the diagram will fall back to a plain `<pre>`.
- **Trust model**: the renderer assumes the input markdown is the user's
  own document. Marked's default behavior is to pass through raw HTML
  embedded in markdown (e.g., a `<script>` tag in a `.md` file lands in
  the output as-is). This is fine for documents you authored; do not
  use this skill to render markdown from untrusted sources without a
  separate sanitization step.
