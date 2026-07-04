---
name: markdown-to-pptx
description: "Fill a branded PowerPoint template from a Markdown artifact — turn this into slides, build a slide deck or presentation, produce a branded .pptx. The deterministic script inspects the template's layout placeholders and projects your Markdown (front-matter, headings, lists, tables) onto them, so the user's slide master, theme, and placed assets survive. Use when the user wants a PowerPoint, a slide deck, or a presentation out of Markdown. Tier-1 on python-pptx (the user installs it; the skill detects it and stops if absent)."
metadata:
  boundaries:
    - filesystem_write
---

# Markdown to PowerPoint

A thin wrapper around `scripts/render.py`. The script is the renderer; you
assemble nothing by hand. It **fills a user-provided, branded `.pptx` template**
at the placeholders the designer already laid out, rather than building a deck
from scratch — so the slide master, theme, fonts, and any placed logo survive.

## Prerequisites

This skill is **Tier-1** on [`python-pptx`](https://pypi.org/project/python-pptx/)
(the exact canonical PyPI package — not a look-alike). Install it once:

```bash
python -m pip install 'python-pptx>=1.0.0'
```

`python-pptx` installs into **your** environment, **outside the repo's SCA**
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
| `--check` | Import-probe `python-pptx`; exit `0`/`2`. | — |
| `inspect <template>` | List the template's layout placeholders. | `FILLPOINTS: layout=<i> idx=<i> type=<NAME> name=<text>` |
| `render <markdown> --template <tpl> [--output <path>]` | Fill the template and write a `.pptx`. | `OUTPUT: <path>`, `FILLED: <n>`, `WARNING: <msg>` |

Placeholders are keyed by their **`idx`** (their stable identity), never by list
position. The mapping: front-matter `title`/`subtitle` → the title slide; each
H1/H2 heading → one slide; list items → bullet rows; a Markdown table → a table
on the slide. Detail and the placeholder model are in
[`references/fill-points.md`](references/fill-points.md).

**Your job** is to assemble the Markdown content and invoke the script. Do not
hand-write the `.pptx`, the slide XML, or the placeholder objects.

## Template flow

1. **Detect** — look for a `.pptx` template on disk in the working directory.
2. **Confirm or elicit** — if you find one, confirm it's the brand to use; if you
   find none, ask the user for their template.
3. **Opt-out** — only if the user explicitly declines a template, render
   **template-less** with the `python-pptx` default master. **Say so up front:**
   the result carries no brand. Never invent a brand and never ship a default
   template asset.

PowerPoint layouts already carry placeholders, so a `.pptx` template is always
fillable — there's no "untagged template" case as there is for Word/Excel.

## Trust model

A user-supplied template is **trusted-author input**, consistent with the
converters pack's local-files-trusted stance. `python-pptx` does not evaluate
template content as code, so there is no template-injection surface here; XXE or
a zip-bomb on a deliberately crafted Office archive is an accepted, out-of-scope
risk for a trusted-author template. The script still **confines its writes**: it
resolves `--output`/`--template` and refuses any path that escapes the working
directory (a model-influenced output path is a local control, independent of
template trust).

## Don't

- Don't hand-write the `.pptx` or its slide XML — the script renders.
- Don't convert Markdown to a fresh deck (Pandoc/Quarto) — that discards the
  user's brand. Template-fill only.
- Don't ship or invent a default template — an absent template is the user's
  explicit choice.
- Don't auto-install `python-pptx` — print the install line and stop.

## Edge cases

| Situation | Behavior |
|---|---|
| `python-pptx` not installed | `--check` exits `2` with the install line; stop. |
| No template found | Ask for one; render template-less only on explicit opt-out. |
| A layout exposes no body placeholder | The script emits `WARNING:` and drops those bullets. |
| A section carries a table | Filled into a `TABLE` placeholder if the layout has one, else a table is added to the slide. |
