# Publish Markdown as a branded Office file

You've got a polished Markdown artifact — a report, a deck outline, a tabular
summary — and a stakeholder who wants it as a real Word doc, PowerPoint, or Excel
file, on-brand. Three `converters` skills do that by **filling your branded
template** at the fill-points a designer already laid out, so the cover page,
slide master, logo, and named cell regions survive. They never convert Markdown
into a fresh document, and they never invent a brand.

| Want | Skill | Asks for |
|---|---|---|
| A Word document | `markdown-to-docx` | A `.docx` template with Jinja tags |
| A PowerPoint deck | `markdown-to-pptx` | A `.pptx` template (layouts already have placeholders) |
| An Excel workbook | `markdown-to-xlsx` | An `.xlsx` template with named ranges / Tables |

## Just ask

Lead with the file you have and the template to fill — the agent picks the right
skill and runs the script:

- "Turn `q3-report.md` into a Word doc using our `report-template.docx`."
- "Make `q3-report.md` into a PowerPoint deck from `brand-deck.pptx`."
- "Export the metrics table in `q3-report.md` to Excel, filling `metrics.xlsx`."

The agent confirms the render library is installed, inspects the template's
fill-points, projects your Markdown onto them, and reports the output path. You
don't describe the placeholders or write any code.

## The one thing each skill needs: a template with fill-points

This is template-fill, not conversion — so each format needs somewhere to put
the content:

- **PowerPoint** is ready by construction. Every `.pptx` layout already carries
  placeholders, so any deck works as a template.
- **Word** needs **Jinja tags** typed into the `.docx`: `{{ title }}` for a
  scalar, a `{%p for it in items %}{{ it }}{%p endfor %}` paragraph loop for a
  list, a `{%tr for r in rows %}` row loop for a table. Author each tag in **one
  uniform run** — if Word splits a tag across runs (a stray autocorrect mid-tag),
  it won't fill. If the template has no tags, the skill tells you how to add them
  rather than converting blindly.
- **Excel** needs **named ranges** (Formulas → Define Name) for scalars and an
  **Excel Table** (Insert → Table) for tabular data. Front-matter keys fill the
  named range of the same name; a Markdown table fills the Table's data region.
  If the workbook has none, the skill tells you how to add them.

## How the Markdown maps

Front-matter and document structure map onto the template the same way across
the three skills:

| Markdown | Where it lands |
|---|---|
| Front-matter `key: value` | A scalar fill-point named `key` (title placeholder / `{{ key }}` / named range) |
| `#` / `##` headings | A slide per heading (pptx); a `sections` loop (docx) |
| Lists | Bullet rows (pptx); a paragraph loop (docx) |
| Tables | A slide table (pptx); a `{%tr %}` row loop (docx); an Excel Table data region (xlsx) |

## Before the first run

Each skill is **Tier-1** on its render library — you install it once, and the
skill stops with the exact command if it's missing (it never installs for you):

```bash
python -m pip install 'python-pptx>=1.0.0'   # markdown-to-pptx
python -m pip install 'docxtpl>=0.16.0'       # markdown-to-docx
python -m pip install 'openpyxl>=3.1.0'       # markdown-to-xlsx
```

These libraries install into **your** environment, outside the repo's security
scanning, so you own keeping them current.

## What to watch for

- **No template?** Say so explicitly. The skill will render with the library
  default and tell you up front that the result is unbranded — it won't silently
  guess a brand.
- **Excel charts.** `markdown-to-xlsx` writes only into data cells and never
  resizes a range, so a chart reading that range keeps working. For a workbook
  with complex Excel-authored drawings, re-open the result and confirm the
  visuals survived — openpyxl can drop shapes it can't parse.
- **Untrusted templates.** Treat a template like any file you'd open — these
  skills assume a trusted author. A `.docx` carries Jinja source, so don't fill a
  template you didn't vet.

## Next steps

- Every flag and stdout marker: [Converter skills reference](../reference/converter-skills.md).
- Coming the other way? [Convert documents to Markdown](convert-documents-to-markdown.md).
- The skill sources:
  [`markdown-to-docx`](../../../../packs/converters/.apm/skills/markdown-to-docx/SKILL.md),
  [`markdown-to-pptx`](../../../../packs/converters/.apm/skills/markdown-to-pptx/SKILL.md),
  [`markdown-to-xlsx`](../../../../packs/converters/.apm/skills/markdown-to-xlsx/SKILL.md).
