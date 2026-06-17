# Excel fill-points: the named-range and Table model

`markdown-to-xlsx` writes into the **data ranges** a designer defined in a
`.xlsx` template, via [`openpyxl`](https://openpyxl.readthedocs.io/). This is the
reference for what those are, how Markdown projects onto them, and how to define
them in Excel.

## What a fill-point is

Like Word (and unlike PowerPoint), an Excel workbook has **no fill-points until
you add them**. There are two kinds:

| Kind | What it is | Good for |
|---|---|---|
| **Named range** | A name bound to a cell or range (Formulas → Define Name) | A single scalar — a title, a date, a prepared-by line |
| **Excel Table** | A structured data block (Insert → Table) with a header row | Tabular content — a metrics table, a line-item list |

`inspect <template>` reports both:

```
FILLPOINTS: kind=defined_name name=report_title ref=Data!$D$1
FILLPOINTS: kind=table name=metrics ref=Data!A1:B3
```

If the workbook has neither, `inspect` (and `render`) emit `GUIDANCE:` telling
the user how to add them — the skill never silently converts a workbook with no
fill-points, because that would discard its formatting and any chart wiring.

## How Markdown maps onto fill-points

| Markdown | Content-model field | Lands in |
|---|---|---|
| Front-matter `key: value` | `scalars[key]` | The single-cell named range named `key` |
| The first Markdown table | `table` (`{header, rows}`) | The first Excel Table's data region |

Front-matter keys are matched to named ranges **by name** — a `report_title:`
front-matter line fills the named range called `report_title`, and only if that
name exists and points to a single cell. Markdown table columns are matched to
the Excel Table's columns **by header text** where they match, else by position.

## Defining fill-points in Excel

- **Named range:** select the cell, then Formulas → Define Name, and give it a
  name (e.g. `report_title`). Use the same name as the Markdown front-matter key.
- **Excel Table:** select the data block including its header row, then Insert →
  Table (or Ctrl/Cmd+T). Name it under Table Design → Table Name. The header row
  labels should match your Markdown table's column headers.

## Why data-ranges-only

The script writes **only** into named-range and Table data cells. It never
touches chart or shape objects, and never resizes a Table's range. This is the
mitigation for openpyxl's documented round-trip limitation:

> openpyxl does currently not read all possible items in an Excel file so shapes
> will be lost from existing files if they are opened and saved with the same
> name. *(openpyxl tutorial)*

In practice openpyxl preserves the charts and images it **can** parse, so a
chart reading a filled range keeps working. But for a template with complex
Excel-authored drawings, **re-open the produced file and confirm the visuals
survived** — the skill deliberately avoids resizing ranges (which would feed
larger data into a chart) precisely so the chart wiring it can't see stays
intact.
