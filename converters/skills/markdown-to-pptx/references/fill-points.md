# PowerPoint fill-points: the placeholder model

`markdown-to-pptx` fills the **placeholders** a slide layout defines. This is
the reference for what those are and how Markdown projects onto them.

## What a placeholder is

A `.pptx` is built from **slide layouts** (e.g. "Title Slide", "Title and
Content"), each defined on the slide master. A layout carries **placeholders** —
the title box, the body/content box, a subtitle, a table region. Each
placeholder has:

- an **`idx`** — its stable identity within the layout. The script keys on this,
  never on list position, because a designer can reorder placeholders without
  changing their `idx`.
- a **type** — `TITLE`, `CENTER_TITLE`, `SUBTITLE`, `BODY`, `OBJECT` (a generic
  content box), `TABLE`, `PICTURE`, and so on.
- a **name** — the human label shown in PowerPoint's selection pane.

`inspect <template>` enumerates them:

```
FILLPOINTS: layout=0 idx=0 type=CENTER_TITLE name=Title 1
FILLPOINTS: layout=0 idx=1 type=SUBTITLE name=Subtitle 2
FILLPOINTS: layout=1 idx=0 type=TITLE name=Title 1
FILLPOINTS: layout=1 idx=1 type=OBJECT name=Content Placeholder 2
```

Because layouts already ship placeholders, **every** `.pptx` is fillable — there
is no "untagged template" case. (Contrast Word, which needs Jinja tags, and
Excel, which needs named ranges.)

## How Markdown maps onto placeholders

| Markdown | Content-model field | Lands in |
|---|---|---|
| Front-matter `title` / `subtitle` | `scalars` | The title slide's `TITLE` / `SUBTITLE` placeholders |
| Each `#` / `##` heading | a `section` | One new slide (a "Title and Content"-style layout) |
| List items under a heading | `section.bullets` | The slide's `BODY` / `OBJECT` placeholder, one bullet per paragraph |
| A Markdown table under a heading | `section.table` | A `TABLE` placeholder if the layout has one, else a table added to the slide |

A plain prose line under a heading (not a list item, not a table row) is mapped
to a body paragraph too — it lands in the slide's body placeholder as a
marker-less line alongside any bullets. So free text under a heading becomes deck
content rather than being dropped.

The script builds an intermediate content model —
`{scalars: {...}, sections: [{heading, bullets, table}]}` — then projects it onto
the layout's placeholders. The model is pure data; no slide is touched until the
render step writes the output file.

## Implementation notes

- **Re-fetch after insert.** Inserting a table into a placeholder replaces the
  placeholder object; the script re-fetches the table from the returned graphic
  frame rather than reusing the stale reference.
- **Layout selection.** The title slide uses the first layout exposing a
  `TITLE`/`CENTER_TITLE` placeholder; content slides use the first layout
  exposing a `BODY`/`OBJECT` placeholder. A branded template's custom layouts are
  matched the same way, by placeholder type.
- **Empty placeholders are left alone.** A layout's footer, date, or
  slide-number placeholders are not touched unless the Markdown supplies a value
  for them.
