---
name: render-proof
description: Render a Markdown file as a self-contained, offline HTML proof artifact styled for human review. Use when the user asks to "render this for review", "proof this draft", "give me a proof of this document", "show me this markdown rendered", or "make this readable for a reviewer". Outputs a single HTML file that opens in any browser with no server or network access at view time. Not for slides, presentations, or publication — use markdown-to-html for that. The rendered output uses a muted stone/slate palette deliberately distinct from the publication look.
metadata:
  boundaries: [filesystem_write]
---

# Render Proof

A thin wrapper around `scripts/render-proof.js`. The renderer parses Markdown with
`markdown-it` + `markdown-it-task-lists`, highlights fenced code with Shiki, sanitizes
the result with DOMPurify (including a CSS `url()` allow-list hook), passes it through
the A2UI Basic Catalog SSR pipeline (`MessageProcessor` → `A2uiSurface` →
`renderToStaticMarkup`), and stamps it into a self-contained HTML file with the muted
proof stylesheet. The output embeds all CSS inline and contains no JavaScript.

## Output rendering

Key–value / one record — For a single record's fields, use an aligned key: value list, not a two-row table.

## Instructions

You are not the renderer. The script is. Invoke it and report the output path.

### Step 1 — Verify dependencies

From the skill's own directory, check whether npm packages are installed:

```bash
node -e "require('@a2ui/react'); require('@a2ui/web_core'); require('markdown-it'); require('shiki'); require('dompurify')"
```

- Exit 0 → dependencies present; go to Step 2.
- Non-zero → not installed yet. Confirm `npm` is available (`npm --version`);
  if it isn't, tell the user to install Node.js and stop. If it is, **ask the user
  before installing**, then run the one-time install and re-verify:

  ```bash
  npm install
  node -e "require('@a2ui/react'); require('@a2ui/web_core'); require('markdown-it'); require('shiki'); require('dompurify')"
  ```

(The install is one-time; subsequent runs are cached in `node_modules/`.)

### Step 2 — Render

```bash
node scripts/render-proof.js <input.md> [--output OUT.html]
```

| Arg | Meaning |
|---|---|
| `<input.md>` | Path to the Markdown file to render (must be within the working directory). |
| `--output OUT.html` | Output path. Default: input with `.html` extension. Must be within the working directory. |

On success, the script prints:
```
OUTPUT: /absolute/path/to/output.html
```

Surface the output path to the user.

### Step 3 — What the renderer handles automatically

- **GFM elements**: headings, bold/italic/inline-code, ordered/unordered/task lists,
  GFM tables, fenced code, blockquotes, horizontal rules.
- **Syntax highlighting**: fenced code blocks are highlighted with Shiki (`github-dark` theme).
  Unknown languages fall back to a plain `<pre><code>` block without throwing.
- **DOMPurify sanitization**: all markdown-rendered HTML is sanitized before output —
  `<script>` tags, event handlers, and unsafe CSS `url()` references are stripped.
  Safe `data:image/` URIs and same-document anchors (`#`) in CSS `url()` are preserved.
- **Offline**: the output embeds all CSS inline. No CDN, no external fonts, no tracking.
- **Path confinement**: input must be within the current working directory (symlinks are
  followed and checked). Output must also be within cwd.

### Don't

- Don't write your own HTML. The script is the renderer.
- Don't pass `--output` to a path outside the working directory — the script rejects it.
- Don't use this skill to render markdown from untrusted third-party sources for display
  to untrusted viewers. The DOMPurify hook covers the most common XSS vectors, but
  CSS property allow-listing (e.g. `position:fixed`) is out of scope for v1.
- Don't run arbitrary shell commands. The only tool-permission surface for this skill is
  `node` (specifically `npm install` for one-time dependency setup and
  `node scripts/render-proof.js` for rendering). No other shell commands are needed.
- Don't read files other than the single input `.md` file per invocation.

### Edge cases

- **Missing dependencies**: `node scripts/render-proof.js` exits 1 with an install hint.
  Follow Step 1 — install on user consent, then re-verify; don't install without asking.
- **Input file ≥ 10 MB**: the script exits 1 with a message naming the file size and limit.
  Split the file or confirm the user intends to render something that large.
- **Raw `<script>` in markdown**: DOMPurify strips it. The output is safe.
- **Unknown code-fence language**: Shiki falls back to a plain `<pre><code>` block.
  No throw; output still renders.
- **Output path outside cwd**: the script exits 1. Use a relative path within cwd.
- **CSS custom property overrides**: the output defines `--proof-bg`, `--proof-text`,
  `--proof-border`, `--proof-muted`, and `--proof-code-bg` as CSS custom properties
  in `:root`. A downstream viewer can override them with an injected stylesheet.
