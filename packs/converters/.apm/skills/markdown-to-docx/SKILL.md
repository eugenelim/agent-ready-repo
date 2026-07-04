---
name: markdown-to-docx
description: "Fill a branded Word template from a Markdown artifact — turn this Markdown into a Word doc, produce a report, a memo, a statement of work, or a branded .docx. The deterministic script fills the Jinja fill-points a designer placed in the template (front-matter, headings, lists, tables map onto them), so the cover page, styles, headers, and placed logo survive. Use when the user wants a Word document, report, memo, or .docx out of Markdown. Tier-1 on docxtpl (the user installs it; the skill detects it and stops if absent)."
metadata:
  boundaries: [filesystem_write]
---

# Markdown to Word

A thin wrapper around `scripts/render.py`. The script is the renderer; you
assemble nothing by hand. It **fills a user-provided, pre-tagged `.docx`
template** at the Jinja fill-points the designer placed, via
[`docxtpl`](https://pypi.org/project/docxtpl/) — rather than building a document
from scratch — so the cover page, paragraph styles, headers/footers, and any
placed logo survive.

## Prerequisites

This skill is **Tier-1** on `docxtpl` (the exact canonical PyPI package — a real
but lower-profile single-maintainer package, so install the exact name). Install
it once:

```bash
python -m pip install 'docxtpl>=0.16.0'
```

The `>=0.16.0` floor clears a version where
`get_undeclared_template_variables()` was broken. `docxtpl` installs into
**your** environment, **outside the repo's SCA** (`pip-audit` / CodeQL never
scan it), so you own keeping it current. The skill never installs it for you.
Verify before rendering:

```bash
python scripts/render.py --check
```

Exit `0` → proceed. Exit `2` → it's not installed; run the `pip install` above
and stop.

## The deterministic-renderer contract

You drive three verbs; the script does the rendering:

| Verb | What it does | Stdout markers |
|---|---|---|
| `--check` | Import-probe `docxtpl`; exit `0`/`2`. | — |
| `inspect <template>` | List the template's declared Jinja variables. | `FILLPOINTS: <variable>` (or `GUIDANCE:` if untagged) |
| `render <markdown> --template <tpl> [--output <path>]` | Fill the template and write a `.docx`. | `OUTPUT: <path>`, `FILLED: <n>`, `WARNING: <msg>`, `GUIDANCE: <msg>` |

The mapping: front-matter `key: value` → `{{ key }}` scalars; the first list →
an `items` list for a `{%p for it in items %}…{%p endfor %}` paragraph loop; the
first Markdown table → `rows` (a list of `{column: value}` dicts) for a
`{%tr for r in rows %}` row loop. Detail and how to add tags in Word are in
[`references/fill-points.md`](references/fill-points.md).

**Your job** is to assemble the Markdown content and invoke the script. Do not
hand-write the `.docx` or its XML.

## Template flow

1. **Detect** — look for a `.docx` template on disk in the working directory.
2. **Confirm or elicit** — confirm the found one, or ask the user for theirs.
3. **No fill-points** — if the template carries no Jinja tags, the script emits
   `GUIDANCE:` explaining how to add them (insert `{{ … }}`, `{%p … %}`,
   `{%tr … %}` tags in Word) rather than silently converting. Relay it; don't
   convert by hand.
4. **Opt-out** — only if the user explicitly declines a template, render
   **template-less** with the `docxtpl`/`python-docx` default document. Say so
   up front: the result carries no brand. Never invent a brand or ship a default
   template asset.

### Authoring tags in Word — run fragmentation

Word silently splits text into multiple "runs" when formatting or autocorrect
changes mid-word, and a Jinja tag split across runs (`{` + `{ title }` + `}`)
won't render. **Author each tag inside one uniform run:** type the whole tag in
one go with consistent formatting, or paste it as plain text. If a tag isn't
filling, this is the first thing to check.

## Trust model

A user-supplied template is **trusted-author input**, consistent with the
converters pack's local-files-trusted stance. Because a `.docx` template carries
Jinja2 *source*, a malicious template author could embed server-side template
injection (SSTI) — this is an **accepted, out-of-scope risk** for a
trusted-author template, as are XXE / zip-bomb on a deliberately crafted
archive. Two cheap controls hold regardless and are enforced:

- **`autoescape=True`** at the `docxtpl` `render()` call (it is **off** by
  default), so a user-content value containing `{{` or XML metacharacters is
  escaped, not interpolated as live markup.
- **Output-path confinement** — the script resolves `--output`/`--template` and
  refuses any path escaping the working directory (a model-influenced output
  path is a local control, independent of template trust).

## Don't

- Don't hand-write the `.docx` or its XML — the script renders.
- Don't convert an untagged document (Pandoc/Quarto) — relay the `GUIDANCE:`
  instead. Template-fill only.
- Don't ship or invent a default template — an absent template is the user's
  explicit choice.
- Don't auto-install `docxtpl` — print the install line and stop.

## Edge cases

| Situation | Behavior |
|---|---|
| `docxtpl` not installed | `--check` exits `2` with the install line; stop. |
| Template has no Jinja tags | `GUIDANCE:` explains how to add them; no file written. |
| A tag isn't filling | Likely run fragmentation — re-author the tag in one uniform run. |
| Template declares a variable with no Markdown source | The script emits `WARNING:` naming it; the rest still fills. |
