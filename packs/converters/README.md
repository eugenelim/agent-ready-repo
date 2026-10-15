# Converters

Your agent can turn documents, email, and diagrams into Markdown, and turn Markdown into branded Word, PowerPoint, Excel, and styled HTML.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it once for your user account:

```bash
agentbundle install --pack converters
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install converters@agent-ready-repo
```

## What your agent can do

- Read a PDF, Office file, HTML page, EPUB, spreadsheet, or image and hand back Markdown your agent can use as context.
- Convert an Outlook or `.eml` email to Markdown with its headers and an attachments table.
- Fill your branded Word, PowerPoint, or Excel template from a Markdown file.
- Turn Markdown into a shareable, styled HTML page, or an offline proof page for review.
- Render Mermaid diagrams in a Markdown file as images.

## Skills

- **`file-to-markdown`** — Converts documents and images to Markdown, with provenance and a quality signal in the output.
- **`msg-to-markdown`** — Converts Outlook `.msg` and `.eml` email to Markdown, keeping headers, body, and attachments.
- **`markdown-to-docx`** — Fills a branded Word template from a Markdown file.
- **`markdown-to-pptx`** — Fills a branded PowerPoint template from a Markdown file.
- **`markdown-to-xlsx`** — Fills a branded Excel template from a Markdown file.
- **`markdown-to-html`** — Makes a self-contained, styled HTML page with navigation, highlighted code, and diagrams.
- **`render-proof`** — Renders a Markdown draft as an offline HTML proof for human review.
- **`mermaid-renderer`** — Replaces each Mermaid block in a Markdown file with a rendered PNG or SVG.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, and Kiro IDE. [Architect](../architect/README.md) draws Mermaid diagrams that `mermaid-renderer` can turn into images. Guides: [Convert documents to Markdown](../../guides/converters/how-to/convert-documents-to-markdown.md), [Publish Markdown to Office](../../guides/converters/how-to/publish-markdown-to-office.md), and [Convert Markdown to HTML and email](../../guides/converters/how-to/convert-markdown-to-html-and-email.md).

## Questions

**Do I need machine-learning tools installed?** Not for common documents. `file-to-markdown` reads PDF, Office, HTML, EPUB, CSV, and email with plain parsers. Only `.xls` files and images need more.

**Does it need my own templates?** The Word, PowerPoint, and Excel skills fill templates your designer prepared. They do not invent a layout.

**What if a library is missing?** Each Office skill checks at run time and stops with the exact `pip install` line to run.

**How does it read an image?** It tiles the image, reads each tile with the model's vision, and merges the tiles by script.

## Details

Scope: user (default), repo · Version: 0.9.8 · Source: [packs/converters](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/converters)
