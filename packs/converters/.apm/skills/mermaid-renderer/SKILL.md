---
name: mermaid-renderer
description: Extract ` ```mermaid ` fenced blocks from a Markdown file, render each one to a PNG (or SVG) via the Mermaid CLI (`mmdc`), and write a rewritten Markdown file alongside with each fence replaced by an image reference. Use when the user wants Mermaid diagrams baked into images for downstream tools that don't render Mermaid natively (Confluence, PDF, slides). The agent only invokes the script.
metadata:
  boundaries: [filesystem_write]
---

# Mermaid Renderer

A thin wrapper around `<skill-dir>/scripts/render_mermaid.py`. The script walks a
Markdown file, extracts ` ```mermaid ` blocks, calls the Mermaid CLI
(`mmdc`) to render each to a PNG, and writes a rewritten Markdown file
where every fence is replaced by a standard Markdown image reference
pointing at the rendered file (e.g. `mermaid-1.png`).

## Output rendering

Key–value / one record — For a single record's fields, use an aligned key: value list, not a two-row table.

## Prerequisites

The renderer shells out to `@mermaid-js/mermaid-cli`. Install once:

```bash
npm install -g @mermaid-js/mermaid-cli
```

(Or `npm install --save-dev @mermaid-js/mermaid-cli` in a project that
ships its own `node_modules/`; the script finds `mmdc` on `PATH`.)

No Python deps beyond the standard library.

## Installed entry-point contract

Treat `<skill-dir>` as the installer-supplied directory containing this active
`SKILL.md`; never infer it from the current working directory, user input, an
environment variable, or a profile path. Replace `<skill-dir>` with that actual
validated directory before executing or relaying any command; never send the
placeholder to a runtime or user. Before every invocation of `render_mermaid.py`:

1. Canonicalize `<skill-dir>`, its `scripts/` child, and the expected entry
   point, resolving symlinks. Require the entry point to be a regular file and
   its resolved path to remain beneath the canonical `scripts/` directory.
2. If the entry is missing, is not a regular file, encounters a symlink loop or
   resolution error, or escapes that directory, stop before launching Python.
   Report only `error: installed skill entry point is unavailable: <entry>`,
   substituting the basename. Do not expose an absolute, home, profile,
   environment, or protected path; do not relay raw runtime stderr; and do not
   offer credential, SSO-capture, token, scope, or dependency remediation.
3. Invoke with a discrete argument vector, for example
   `["<python>", "<skill-dir>/scripts/render_mermaid.py", "..."]`, so spaces, both quote characters, `$()`, backticks, and
   variable-shaped text cannot be expanded by a shell. Keep the project root as
   the working directory so user content paths retain their documented meaning.
4. If only a shell string is available, use a single-quoted literal path on
   POSIX or PowerShell and refuse paths containing a single quote. On cmd.exe,
   use a double-quoted path and refuse paths containing `"`, `%`, or `!`.
   If the adapter cannot represent the path safely, refuse instead of invoking.

Interpret exit codes only after this preflight succeeds and the entry point
actually runs.

## Instructions

You are not the renderer. The script is. Invoke it and report what
landed where.

### Step 1 — Verify `mmdc` is available

```bash
python '<skill-dir>/scripts/render_mermaid.py' --check
```

- Exit code 0 → `mmdc` is on `PATH`, proceed.
- Exit code 2 → `mmdc` is not installed. Tell the user to run
  `npm install -g @mermaid-js/mermaid-cli` themselves. Don't try to
  install it for them.

### Step 2 — Render

```bash
python '<skill-dir>/scripts/render_mermaid.py' --input report.md --output-dir ./rendered [--format png|svg] [--theme default|forest|dark|neutral] [--background white|transparent|#hex] [--prefix diagram]
```

| Flag | Meaning |
|---|---|
| `--input PATH` | Source Markdown file. Required. |
| `--output-dir DIR` | Directory for rendered images **and** the rewritten Markdown. Default: `./mermaid-out`. |
| `--format` | `png` (default) or `svg`. |
| `--theme` | `default` (default), `forest`, `dark`, `neutral`. |
| `--background` | Background colour, e.g. `white`, `transparent`, `#f0f0f0`. Default: `white`. |
| `--prefix NAME` | Output filename prefix. Default: `mermaid`. |
| `--width N` | Output width in pixels (passes through to `mmdc -w`). |
| `--height N` | Output height in pixels (passes through to `mmdc -H`). |
| `--check` | Verify `mmdc` is on PATH; exit 0 or 2. |
| `--verbose` | Debug logging. |

The script writes:

- `<output-dir>/<prefix>-1.<ext>`, `<prefix>-2.<ext>`, … — one image
  per Mermaid block, numbered in document order.
- `<output-dir>/<input-basename>.md` — a rewritten copy of the input
  with each ` ```mermaid ` fence replaced by a standard Markdown image
  reference pointing at the rendered file
  (e.g. ` `` `mermaid-1.png` `` ` for the first block).

The original input file is **not** modified.

stdout summary:

```
OUTPUT_DIR: /abs/path/to/rendered
REWRITTEN: /abs/path/to/rendered/report.md
DIAGRAMS: 3
```

Surface the rewritten path and the diagram count.

### Step 3 — Composing with other skills

The rewritten Markdown plus the image files form a self-contained
bundle you can feed to:

- `confluence-publisher --input <rewritten>.md --attach <prefix>-1.png --attach <prefix>-2.png …`
  — image refs become `<ac:image>` macros on the Confluence side.
- `markdown-to-html` — the rendered images replace the live-CDN
  Mermaid renderer for fully-offline HTML output.
- Any PDF or slide pipeline that takes Markdown + images.

### Don't

- Don't write your own Mermaid renderer. Extend `mmdc` invocations in
  the script if a flag is missing.
- Don't pre-process the Markdown by hand to strip the fences — the
  script does that.
- Don't fall back to a Mermaid Live Editor URL — that would leak the
  diagram source to a third party.
- Don't try to install `mmdc` automatically. Tell the user the
  one-line install command and stop.
- Don't render to the input file's own directory by default — the
  script writes to `--output-dir` exactly so the original stays
  untouched.

### Edge cases

- **No Mermaid blocks in the input.** The script reports
  `DIAGRAMS: 0`, copies the input to `<output-dir>/<basename>.md`
  unchanged, and exits 0.
- **A block fails to render** (syntax error, `mmdc` non-zero). The
  script keeps going, writes a `mermaid-N.error.txt` next to where
  the image would have gone, leaves the fence intact in the rewritten
  Markdown, and exits non-zero at the end with a count of failures.
- **`mmdc` not on PATH.** `--check` exits 2 with the install command.
  Don't shell out to find it elsewhere.
- **Theme name not in the list.** `mmdc` exits with the list of valid
  choices; the script surfaces that. Don't invent a fifth.
- **Trust model.** Mermaid input is the user's own document. The
  renderer runs `mmdc` on whatever fences it finds; do not use this
  skill on Markdown from untrusted sources without a separate
  sanitization step.
