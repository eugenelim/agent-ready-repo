# Convert Markdown to HTML, and email to Markdown

Two converters at the edges of your Markdown workflow. `markdown-to-html` takes a `.md` file out to a self-contained, styled HTML page you can share or print to PDF. `msg-to-markdown` brings an Outlook `.msg` email in, headers and all. This guide covers both.

## Markdown to a shareable HTML page

`markdown-to-html` renders a `.md` file into one HTML file with a sticky header, a sidebar nav, syntax-highlighted code, callout boxes, and a print stylesheet. It's for documents — not slides or pitch decks.

### Before you start

The renderer runs on Node.js with the `marked` and `highlight.js` packages (pinned in the skill's `package.json`). From the skill's own directory, check whether they're present:

```bash
node -e "require.resolve('marked'); require.resolve('highlight.js')"
```

Exit 0 and you're ready. Non-zero means they aren't installed yet — confirm `npm` is available, then run `npm install` once from the skill directory (the agent will ask before installing). If the skill lives in a tracked directory, add its `node_modules/` to your `.gitignore`.

### Render

```bash
node scripts/render.js report.md
```

By default the output is `report.html` next to the input. The script prints `OUTPUT:` (the path), `SECTIONS:` (how many h2/h3 anchors it built), and `MERMAID:` (`yes`/`no`). Open the file in a browser; don't paste the HTML into chat.

Useful flags:

- `--output FILE` — write somewhere other than the default.
- `--title` / `--subtitle` — header text (title defaults to the first H1, then the filename).
- `--theme navy|green|teal|amber|rose` — accent color, `navy` by default.
- `--no-mermaid` — skip the Mermaid CDN script for sources with no diagrams, or for fully-offline output.

The renderer handles a few things on its own: headings get stable IDs for the sidebar and print TOC; paragraphs starting with `**Note:**`, `**Tip:**`, `**Warning:**`, `**Important:**`, or `**Stop:**` become styled callout boxes; tables get a horizontal-scroll wrapper; and every page carries an `@media print` block so `Ctrl+P → Save as PDF` works out of the box. Feed it raw Markdown — don't hand-write the HTML.

### Offline diagrams

By default, ` ```mermaid ` blocks pass through as live-rendered diagrams via a CDN script. For fully-offline output, render the diagrams to images first with [`mermaid-renderer`](render-mermaid-diagrams.md), then run `markdown-to-html` on the rewritten Markdown so the images are baked in.

## Outlook `.msg` to Markdown

`msg-to-markdown` reads an Outlook `.msg` file and writes structured Markdown: a header table (From, To, CC, Date), the body, and attachment metadata.

### Before you start

The converter runs on Node.js and reads `.msg` files through an npm package — `@nicecode/msg-reader` (preferred) or `msgreader`. Install the preferred one once:

```bash
npm install @nicecode/msg-reader
```

Verify a reader is available from the skill's directory:

```bash
node -e "try{require.resolve('@nicecode/msg-reader')}catch{require.resolve('msgreader')}"
```

### Convert

```bash
node scripts/convert.js "important-update.msg"
```

The agent then summarizes the email — subject, sender, date, recipient count, body type (HTML vs plain text), and attachment count. If the body came from HTML, expect some complex formatting (embedded CSS, conditional Outlook markup) to be simplified.

To pull attachments out to a folder, run the attachments script:

```bash
node scripts/extract-attachments.js "important-update.msg"
```

For a folder of emails, loop the convert command over each `.msg` file.

### Pitfalls

- **RTF-only body.** Older messages may store the body only in RTF, with no HTML or plain text. The converter flags this; re-save the message as HTML from Outlook, or install an RTF parser.
- **Winmail.dat / TNEF.** TNEF-encoded content may not parse; `node-tnef` is the suggested alternative.
- **Inline images.** Images referenced via `cid:` URLs are stored as attachments and show as broken references until you extract them.
- **Reply chains.** Quoted replies (`-----Original Message-----`, `>`-prefixed lines) are preserved as nested blockquotes.
- **Garbled text.** A `.msg` may use an unusual encoding (UTF-16LE, Windows-1252); re-reading with the right one usually fixes it.

## Next steps

- The source for both skills: [`markdown-to-html`](../../../../packs/converters/.apm/skills/markdown-to-html/SKILL.md) and [`msg-to-markdown`](../../../../packs/converters/.apm/skills/msg-to-markdown/SKILL.md).
- Every flag and output marker: [Converter skills reference](../reference/converter-skills.md).
- Coming the other way? [Convert documents to Markdown](convert-documents-to-markdown.md).
