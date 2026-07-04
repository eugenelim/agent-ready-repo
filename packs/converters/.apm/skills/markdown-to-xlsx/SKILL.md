---
name: markdown-to-xlsx
description: "Fill a branded Excel template from a Markdown artifact — export this table to Excel, fill the .xlsx template, produce a spreadsheet or workbook. The deterministic script writes Markdown content into the named ranges and Excel Tables a designer defined (front-matter into single-cell names, a Markdown table into a Table data region), so the workbook's formatting, formulas, and charts survive. Use when the user wants Excel, a spreadsheet, or an .xlsx workbook out of Markdown. Tier-1 on openpyxl (the user installs it; the skill detects it and stops if absent)."
metadata:
  boundaries: [filesystem_write]
---

# Markdown to Excel

A thin wrapper around `scripts/render.py`. The script is the renderer; you
assemble nothing by hand. It writes Markdown content into the **data ranges** a
designer already defined in a `.xlsx` template — its **named ranges** and **Excel
Tables** — via [`openpyxl`](https://pypi.org/project/openpyxl/), rather than
building a workbook from scratch. The template's formatting, formulas, and any
chart that reads those ranges survive.

## Prerequisites

This skill is **Tier-1** on `openpyxl` (the exact canonical PyPI package).
Install it once:

```bash
python -m pip install 'openpyxl>=3.1.0'
```

`openpyxl` installs into **your** environment, **outside the repo's SCA**
(`pip-audit` / CodeQL never scan it), so you own keeping it current. The skill
never installs it for you. Verify before rendering:

```bash
python scripts/render.py --check
```

Exit `0` → proceed. Exit `2` → it's not installed; run the `pip install` above
and stop.

## The deterministic-renderer contract

You drive three verbs; the script does the rendering:

| Verb | What it does | Stdout markers |
|---|---|---|
| `--check` | Import-probe `openpyxl`; exit `0`/`2`. | — |
| `inspect <template>` | List the workbook's named ranges + Excel Tables. | `FILLPOINTS: kind=… name=… ref=…` (or `GUIDANCE:`) |
| `render <markdown> --template <tpl> [--output <path>]` | Fill the data ranges and write a `.xlsx`. | `OUTPUT: <path>`, `FILLED: <n>`, `WARNING: <msg>`, `GUIDANCE: <msg>` |

The mapping: front-matter `key: value` → the single-cell **named range** of the
same name; the first Markdown table → the first **Excel Table**'s data region
(columns aligned by header text, else by position). Detail and how to define
ranges in Excel are in [`references/fill-points.md`](references/fill-points.md).

**Your job** is to assemble the Markdown content and invoke the script. Do not
hand-write the `.xlsx` or its XML.

## Template flow

1. **Detect** — look for a `.xlsx` template on disk in the working directory.
2. **Confirm or elicit** — confirm the found one, or ask the user for theirs.
3. **No fill-points** — if the workbook has no named ranges and no Excel Tables,
   the script emits `GUIDANCE:` explaining how to add them (Define Name / Insert
   Table) rather than silently converting. Relay it; don't convert by hand.
4. **Opt-out** — only if the user explicitly declines a template, render
   **template-less** with a bare `openpyxl` workbook. Say so up front: the result
   carries no brand. Never invent a brand or ship a default template asset.

## Charts and shapes — the data-ranges-only contract

The script writes **only** into named-range and Excel-Table data cells. It never
creates, manipulates, or resizes chart or shape objects, and never resizes a
table's range — so a chart that reads a filled range keeps working. `openpyxl`
preserves the charts and images it can parse through a load-and-save, **but its
own tutorial warns that shapes it cannot read are lost when an existing file is
opened and saved**. For a template with complex Excel-authored drawings,
**re-open the produced file and confirm the visuals survived.** A Markdown table
with more rows than the Excel Table has room for is truncated (with a
`WARNING:`), never expanded, because resizing a range can break the charts that
read it.

## Trust model

A user-supplied template is **trusted-author input**, consistent with the
converters pack's local-files-trusted stance. `openpyxl` does not evaluate
workbook content as code, so there is no template-injection surface here; XXE or
a zip-bomb on a deliberately crafted Office archive is an accepted, out-of-scope
risk for a trusted-author template. The script still **confines its writes**: it
resolves `--output`/`--template` and refuses any path escaping the working
directory.

## Don't

- Don't hand-write the `.xlsx` or its XML — the script renders.
- Don't convert a workbook with no fill-points — relay the `GUIDANCE:` instead.
- Don't resize a table or named range to fit more data — that can break charts.
- Don't ship or invent a default template — an absent template is the user's
  explicit choice.
- Don't auto-install `openpyxl` — print the install line and stop.

## Edge cases

| Situation | Behavior |
|---|---|
| `openpyxl` not installed | `--check` exits `2` with the install line; stop. |
| Workbook has no named ranges or Tables | `GUIDANCE:` explains how to add them; no file written. |
| Markdown table longer than the Excel Table | Truncated with a `WARNING:`; the range is not resized. |
| Template carries complex Excel-authored shapes | Re-open and verify; `openpyxl` may drop shapes it can't parse. |
| A named range spans multiple cells | Skipped with a `WARNING:` (scalars target single-cell names). |
