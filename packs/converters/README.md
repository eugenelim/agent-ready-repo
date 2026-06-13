# converters

File-format conversion skills for getting content into and out of Markdown.

## What's inside

- `file-to-markdown` — documents and images → Markdown.
- `markdown-to-html` — Markdown → styled HTML.
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
- "Convert this Outlook .msg export to Markdown."
