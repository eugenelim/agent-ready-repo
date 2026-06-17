# Activation grading — markdown-to-{docx,pptx,xlsx}

Recorded manual-QA pass (T4) over the three skills' `description` frontmatter and
`evals/evals.json`, confirming the load-bearing decision of RFC-0036 §177: that
three per-format skills disambiguate cleanly on natural phrasing. Graded by
reading each skill's activation surface against representative prompts —
**this file is the durable record** (the PR description rots after merge).

Date: 2026-06-17 · Grader: eugenelim (implementing agent)

## Activation surface per skill

Each `description` seeds both the noun keywords and the imperative trigger
phrasings RFC-0036 §2 names:

| Skill | Noun keywords | Imperative triggers |
|---|---|---|
| `markdown-to-docx` | Word document, report, memo, statement of work, branded .docx | "turn this Markdown into a Word doc" |
| `markdown-to-pptx` | PowerPoint, slide deck, presentation, branded .pptx | "turn this into slides" |
| `markdown-to-xlsx` | Excel, spreadsheet, workbook, .xlsx | "export this table to Excel", "fill the .xlsx template" |

## Graded prompts → expected activation

| Prompt | Should fire | Fires? | Note |
|---|---|---|---|
| "Make this a PowerPoint." | `markdown-to-pptx` | ✓ | "PowerPoint" is unique to pptx. |
| "Turn this Markdown into a Word doc." | `markdown-to-docx` | ✓ | Verbatim imperative in the docx description. |
| "Export this table to Excel." | `markdown-to-xlsx` | ✓ | "Excel" + "export … to Excel" unique to xlsx. |
| "Turn this into slides." | `markdown-to-pptx` | ✓ | "slides"/"slide deck" unique to pptx. |
| "Make a statement of work .docx." | `markdown-to-docx` | ✓ | "statement of work" + ".docx" unique to docx. |
| "Build a spreadsheet from this." | `markdown-to-xlsx` | ✓ | "spreadsheet"/"workbook" unique to xlsx. |
| "Render this Markdown as HTML." | `markdown-to-html` (existing) | ✓ | No Office keyword; the three new skills don't claim HTML. |
| "Convert this PDF to Markdown." | `file-to-markdown` (existing) | ✓ | Inward direction; new skills are outward-only. |

## Disambiguation check

The three descriptions share the stem "Fill a branded … template from a Markdown
artifact" but each names a **distinct format and its synonyms** (Word/.docx vs
PowerPoint/.pptx vs Excel/.xlsx). No two share a format noun, and each carries a
distinct imperative trigger. There is no overlap with the inward
`file-to-markdown` (which converts *into* Markdown) or with `markdown-to-html`
(HTML, not Office). Risk of cross-firing among the three: **low** — the format
nouns are mutually exclusive.

## Verdict

All eight graded prompts route to the intended skill. The three-skills
decision (RFC-0036 §177) holds on the authored activation surface. No
description edits were needed during grading.
