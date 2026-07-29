# converters

Say "convert this PDF to Markdown" or "turn this Markdown into a branded Word doc" — and the agent handles it. `converters` moves content between every format your team touches: PDF, Office, HTML, EPUB, email, images, and Mermaid diagrams → Markdown, and Markdown back out to styled HTML, Word, PowerPoint, and Excel.

The `file-to-markdown` skill runs a no-ML **Tier-0** floor (pure-Python parsers for PDF, Office, HTML, EPUB, CSV, ODF, `.eml`) before reaching for Docling. Every output carries a versioned frontmatter contract — provenance and a quality/confidence signal — so downstream tools know what they received.

The Markdown → Office skills (`markdown-to-docx`, `markdown-to-pptx`, `markdown-to-xlsx`) fill your existing branded templates. Each detects its render library (`docxtpl` / `python-pptx` / `openpyxl`) at runtime and stops with the exact `pip install` line if it's absent.

## Skills

- `file-to-markdown` — PDF, Office, HTML, EPUB, CSV, ODF, `.eml`, images → Markdown
- `markdown-to-html` — Markdown → styled HTML
- `markdown-to-docx` — Markdown → branded Word document
- `markdown-to-pptx` — Markdown → branded PowerPoint deck
- `markdown-to-xlsx` — Markdown → branded Excel workbook
- `msg-to-markdown` — Outlook `.msg` → Markdown
- `mermaid-renderer` — render Mermaid diagrams

## Install

```
agentbundle install --pack converters <catalogue>
```

`converters` is user-scope by default — format conversion is a portable utility, not a project concern.

---

→ **Go deeper:** [`guides/converters/`](../../guides/converters/)
