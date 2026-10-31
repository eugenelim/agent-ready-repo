# HTML report

`scripts/render_html.py <effort-dir>` turns a saved `assessment.md` into one
offline page, `<effort-dir>/assessment.html`, beside it. Run it only when the user
asks for an HTML report, after the assessment is saved. If it is not saved, offer
to save it first and run nothing. Opening the page in a browser is a separate
request.

## How to run it

Pass the resolved effort directory, the one `references/output-layout.md`
derives, as the single argument. The script refuses a path that contains a
symlink or a `..` component as supplied, so resolve it first. A second run
replaces the existing `assessment.html`.

| Exit | Meaning |
| --- | --- |
| 0 | The page was written. |
| 2 | The report was refused: an orientation subsection lacks a usable `Sources checked` table, an evidence class is outside `observed`, `inferred`, `reported`, `unknown`, the source is over 2 MiB, or it is not UTF-8. The reason is on stderr. |
| 3 | Confinement or environment failure: a missing source or directory, a symlink, an unexpected error, or a host without descriptor walking, Windows included. No report is written on such a host. |

## What the page holds

- The orientation subsections, headings, lists, and tables of the saved report,
  with evidence classes shown as badges and heat-map cells shaded by value.
- A banner stating that the map and hotspot set were not user-confirmed unless
  the charter's single `Checkpoints:` line says `confirmed`.
- A notice that the page is built from repository text and model analysis, is
  unverified, and is not redacted. Read the saved report for secrets before you
  share the page.
- Diagrams as labeled source blocks, not drawings. Author a diagram with
  `architect-diagram`; the page shows its source.

The page runs no script and loads nothing from a network. The renderer escapes
every value from the report and treats the report as untrusted text.
