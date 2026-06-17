# Word fill-points: the Jinja-tag model

`markdown-to-docx` fills the **Jinja tags** a designer placed in a `.docx`
template, via [`docxtpl`](https://docxtpl.readthedocs.io/). This is the
reference for what those tags are, how Markdown projects onto them, and how to
add them in Word.

## What a fill-point is

Unlike PowerPoint (whose layouts ship placeholders) and Excel (whose workbooks
carry named ranges), a Word document has **no fill-points until you add them**.
A fill-point is a Jinja tag typed into the document text:

| Tag | Where | Fills |
|---|---|---|
| `{{ variable }}` | inline, anywhere | a scalar value |
| `{%p for it in items %}` … `{%p endfor %}` | each directive on its own paragraph; the paragraph(s) between repeat | a list, one paragraph per item |
| `{%tr for r in rows %}` … `{%tr endfor %}` | each directive in its own table row; the row(s) between repeat | a table, one row per item |

`inspect <template>` reports them via docxtpl's
`get_undeclared_template_variables()`:

```
FILLPOINTS: items
FILLPOINTS: rows
FILLPOINTS: title
```

If a template carries no tags, `inspect` (and `render`) emit `GUIDANCE:` telling
the user how to add them — the skill never silently converts an untagged
document, because that would discard the brand.

## How Markdown maps onto tags

| Markdown | Context field | Tag it feeds |
|---|---|---|
| Front-matter `key: value` | `key` (scalar) | `{{ key }}` |
| The first list | `items` (list of strings) | `{%p for it in items %}{{ it }}{%p endfor %}` |
| The first Markdown table | `rows` (list of `{column: value}` dicts) | `{%tr for r in rows %}{{ r.Column }}{%tr endfor %}` |

The script also provides a `sections` list mirroring the document structure, for
templates that loop over headings. The context is pure data; the template
decides where each value lands.

**Reserved context names.** `items`, `rows`, and `sections` are the
convenience handles the mapper always injects. A front-matter key with one of
those exact names is shadowed by the handle — name your scalar front-matter keys
something else (e.g. `summary`, not `sections`).

## Adding tags in Word — the run-fragmentation trap

Word stores text as **runs**, and it silently starts a new run whenever
formatting changes — including mid-word from autocorrect, a stray bold toggle,
or a spell-check fix. A Jinja tag whose characters land in different runs
(`{` `{ title }` `}`) is invisible to docxtpl and won't render.

**To author a tag safely:**

- Type the entire tag in one motion with consistent formatting, or
- paste it as plain text (so Word doesn't fragment it), and
- if a tag stubbornly won't fill, re-type it from scratch in a clean paragraph.

A symptom of fragmentation is a tag that `inspect` doesn't list even though you
can see it in the document — the characters are there but split across runs.

## Why `autoescape=True`

The renderer passes `autoescape=True` to docxtpl's `render()` (autoescape is
**off** by default). User content containing `<`, `&`, or `{{` is then
XML-escaped and rendered as literal text rather than injected as live markup
into the document XML. This is a cheap, always-on control independent of whether
the template author is trusted.
