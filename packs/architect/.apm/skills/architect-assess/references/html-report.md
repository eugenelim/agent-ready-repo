# HTML report

`scripts/render_html.py <effort-dir> [--diagrams]` turns a saved `assessment.md` into one
offline page, `<effort-dir>/assessment.html`, beside it. Run it only when the user
asks for an HTML report, after the assessment is saved. If it is not saved, offer
to save it first and run nothing. Opening the page in a browser is a separate
request.

## How to run it

Pass the resolved effort directory, the one `references/output-layout.md`
derives, as the first argument. Add `--diagrams` as the second argument only when the user asks for drawn diagrams. The script treats the first argument as the path whatever its text, and refuses a path that contains a
symlink or a `..` component as supplied, so resolve it first. A second run
replaces the existing `assessment.html`.

| Exit | Meaning |
| --- | --- |
| 0 | The page was written. |
| 2 | The report or the command was refused. The reasons are: a wrong argument count or a second argument other than `--diagrams` (stderr then reads `render_html: usage: render_html.py <effort-dir> [--diagrams]`); an orientation subsection without a usable `Sources checked` table; an evidence class outside `observed`, `inferred`, `reported`, `unknown`; a source over 2 MiB; a source that is not UTF-8; and a rendered page over 16 MiB. The reason is on stderr. |
| 3 | Confinement or environment failure: a missing source, a missing or non-directory effort path, an existing `assessment.html` over 16 MiB, a symlink, an unexpected error, a host without descriptor walking (Windows included), a stylesheet asset that is missing, over 64 KiB, not UTF-8, or holds `</style`, `<!--`, `url(`, or `@import`, or, with `--diagrams`, a diagrams script asset that is missing or unsafe, over 64 KiB, not UTF-8, or holds `</script`, `<!--`, or a carriage return. No report is written. |

## How it looks

The page uses the maintainer-view style shared with the intents and decisions views: the same header, colour roles, type, pills, and light and dark themes. It reads as a document with a snapshot line under the title, a margin head per section, and a contents rail beside the text on wide screens; on narrow screens the contents are a closed control above the text. There is no search, filter, or theme switch, because the default page runs no script.

## What the page holds

- The orientation subsections, headings, lists, and tables of the saved report,
  with evidence classes shown as badges and heat-map cells shaded by value.
- A banner stating that the map and hotspot set were not user-confirmed unless
  the charter's single `Checkpoints:` line says `confirmed`.
- A notice that the page is built from repository text and model analysis, is
  unverified, and is not redacted. Read the saved report for secrets before you
  share the page.
- Diagrams as labeled source blocks, not drawings, on the default page. Author a
  diagram with `architect-diagram`; the page shows its source.

The default page runs no script and loads nothing from a network. The renderer
escapes every value from the report and treats the report as untrusted text.

## Drawn diagrams

With `--diagrams`, the page draws each safe Mermaid fence in place, above its
source block, in the page's light or dark theme. The page then loads Mermaid
12.2.0 from `cdn.jsdelivr.net`, bound by an integrity hash, and runs one script
of this pack's own. Opening such a report sends the reader's IP address, the
time, and browser details to that host, and it shows source blocks when offline.
Share a drawn report only with readers who accept that; the default report
stays offline. A fence that is unsafe to draw (a directive, a frontmatter
block, a click or link statement, an unlisted diagram type, an oversize fence,
or any of the first 20 passing fences being exceeded) or that fails to draw
stays as source and says so on its label.
