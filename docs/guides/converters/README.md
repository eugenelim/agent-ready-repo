# `converters` — guides

Get documents into Markdown and back out again. The `converters` pack: pull text out of office files and diagrams (`file-to-markdown`), bake Mermaid fences into real images (`mermaid-renderer`), turn Markdown into a self-contained styled HTML page (`markdown-to-html`), publish Markdown back out as a branded Word doc / PowerPoint deck / Excel workbook by filling your template (`markdown-to-docx`, `markdown-to-pptx`, `markdown-to-xlsx`), and read Outlook `.msg` email into Markdown (`msg-to-markdown`). Each one is a thin wrapper: the agent invokes a script and reports where the output landed.

New here? Start with [Convert documents to Markdown](how-to/convert-documents-to-markdown.md) — it's the entry point for most of what this pack does. Then chain the others: render the diagrams in your Markdown, or push it out as HTML.

## How-to

Task-oriented recipes for a problem you already have.

- [Convert documents to Markdown](how-to/convert-documents-to-markdown.md) — PDF, DOCX, PPTX, XLSX, and images into clean Markdown.
- [Render Mermaid diagrams to images](how-to/render-mermaid-diagrams.md) — bake `mermaid` fences into PNG or SVG for tools that don't render Mermaid live.
- [Convert Markdown to HTML and email to Markdown](how-to/convert-markdown-to-html-and-email.md) — Markdown out to a shareable HTML page, and Outlook `.msg` in to Markdown.
- [Publish Markdown as a branded Office file](how-to/publish-markdown-to-office.md) — fill your Word / PowerPoint / Excel template from a Markdown artifact, brand intact.

## Reference

Information-oriented, dry and complete.

- [Converter skills](reference/converter-skills.md) — every skill's inputs, outputs, flags, and the external tools each one needs.

---

Installing the pack, upgrading it, and the adapter support matrix live in [`../_shared/`](../_shared/).
