# Output rendering directives

When a skill produces structured output, it declares which rendering shape
applies in a `## Output rendering` section near the top of its body.
Paste **only the line(s) that match what the skill actually emits** — a skill
that only ever outputs a diff gets the diff line and nothing else.

---

**Table** — When presenting several items that share the same fields, render a
Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail
list. Right-align numeric columns.

**Status list** — Lead each row with a status glyph — ● running, ✓ done,
○ idle, ⚠ blocked — status first, one item per line, labels aligned.

**Severity list** — Lead each finding with a severity glyph — 🟥 blocker,
🟧 major, 🟨 minor, ⚪ advisory — worst first, one finding per line, file:line
anchor aligned.

**Tree / hierarchy** — Render hierarchies as an ASCII tree (├─ └─ │) inside a
fenced block, not as nested bullets.

**Diagram / flow** — For relationships or flow, emit a fenced ```` ```mermaid ````
block (it renders in chat and artifacts). If the surface is terminal-only, fall
back to an ASCII box-and-arrow sketch.

**Key–value / one record** — For a single record's fields, use an aligned
`key: value` list, not a two-row table.

**Code change** — Show edits as a fenced ```` ```diff ```` block with +/− lines.
Never describe the change in prose or a table.

**Rationale / narrative** — Use short `##` headings and 2–3 sentence
paragraphs. Don't force narrative into a table.

**Progress** — Report progress inline as done/total (e.g. `3/8`). Only draw a
bar if you're animating in a terminal.

---

## How to add directives to a skill

Add an `## Output rendering` section **before the first procedural `##`
section** of the skill body. Include only the lines that match what this skill
actually emits:

```markdown
## Output rendering

Table — When presenting several items that share the same fields, render a
Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail
list. Right-align numeric columns.
```

Optionally open with the meta-rule line to establish the governing contract:

> Render output to match its shape — not all as prose.

Then list only the applicable directives below it.

## When to omit

Skills that produce only file artifacts (write a file, receipt it), interact
conversationally, or produce raw data streams (JSON/CSV for machine
consumption) need no rendering directive. The directive is for the
**human-readable chat output** the skill surfaces inline.

**Carve-out:** if a skill writes a file but also surfaces a structured receipt
inline in chat (e.g., a `new-adr` or `new-rfc` key–value summary confirming
what was created), the receipt portion warrants the appropriate directive
(`Key–value / one record`) even though the primary deliverable is a file.
