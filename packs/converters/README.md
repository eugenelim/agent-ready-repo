# converters

File-format conversion skills for getting content into and out of Markdown —
including publishing a Markdown artifact back out as a branded Office file.

## What's inside

- `file-to-markdown` — documents and images → Markdown.
- `markdown-to-html` — Markdown → styled HTML.
- `markdown-to-docx` — Markdown → a branded Word document (fills a `.docx` template).
- `markdown-to-pptx` — Markdown → a branded PowerPoint deck (fills a `.pptx` template).
- `markdown-to-xlsx` — Markdown → a branded Excel workbook (fills a `.xlsx` template).
- `msg-to-markdown` — Outlook `.msg` → Markdown.
- `mermaid-renderer` — render Mermaid diagrams.

## Install

`converters` is **user-scope by default** — format conversion is a portable
utility, not a project concern.

```
agentbundle install --pack converters <catalogue>
```

## Usage

Ask your agent, for example:

- "Convert this PDF to Markdown: <path>."
- "Render this Markdown file as styled HTML."
- "Turn this Markdown into a Word doc using our branded template."
- "Make this Markdown into a PowerPoint deck from our slide template."
- "Export this Markdown table to Excel, filling our workbook template."
- "Convert this Outlook .msg export to Markdown."

The Markdown→Office skills are **Tier-1** on their render libraries
(`docxtpl` / `python-pptx` / `openpyxl`): you install the library once, and the
skill detects it and stops with the exact `pip install` line if it's absent.

---

→ **Go deeper:** the [`converters` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/converters/).
