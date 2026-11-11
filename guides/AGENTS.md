# AGENTS.md — `guides/`

Applies to `guides/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Audience and publication

`guides/` is adopter-facing; `docs/guides/` is maintainer material. This tree is
published by `tools/build-site.py`: writing a valid file is all publication and
navigation require. Use the `author-product-docs` skill for authoring work.

## Content traps

[`contracts/guide.schema.json`](../contracts/guide.schema.json) owns frontmatter;
`additionalProperties: false` means new fields belong there first. Keep `title`
and the leading body H1 identical: `_shared` guides ship without rendered
frontmatter, so no H1 leaves adopters without a page heading.

When deleting or renaming a page, delete its `guide-nav-baseline.toml` entry in
the same change. The nav-ineligible set is pinned by its inventory test.

- Prefer in-tree link targets: links out of `guides/` render as GitHub blob URLs
  and send readers off-site.

## Job pages

A page the docs sidebar lists is a job page. The CLI tab pages are the model.

- Open with one sentence on what the reader can do. No subtitle, no history.
- Each section: a lead-in sentence ending in a colon, one command or prompt,
  then one sentence on what happens. Put choices and decisions in prose.
- Say which packs the job needs and how to install them; never assume `core`.
- Explain a file or term where the reader first acts on it, in plain words.
- Flags, environment variables, edge cases, and errors go to a reference page.
- No callouts; a table only to compare options. About 150–400 words.
- No "Step N" in headings: verb-phrase H2s in reading order, H3 for sub-parts.
- Name no agent host outside the supported agents (no Conductor, Orca, etc.).
- Answer first: a section's first sentence is its point. One page, one job,
  one Diátaxis kind; link across kinds instead of mixing them.
- Label who acts where it could blur: you say, the agent does, you run in a
  terminal. Say where output lands and link
  [`find-and-open-your-files`](_shared/how-to/find-and-open-your-files.md)
  rather than repeating how to open it.
- Inline sample output is at most 10 lines and comes from a real run. Longer
  samples and templates go to a reference page. Never present invented output as real.
- Describe current state only: no "previously", "now", "no longer". Keep
  authoring scaffolding (kind labels, `<!-- rung: -->` comments, draft notes) out of reader text.
- Put sources in footnotes at the page foot. Use one name per thing.
- State what the job does not do. When a non-terminal route exists, name it and
  say what it lacks.
- End with one Next link whose text names the destination. The `summary`
  equals the page's card blurb.
- Run every command and prompt, and check the rendered page, before you publish.

## Essential commands

```bash
python3 tools/validate_guides.py
python3 tools/check-guide-index.py
python3 tools/lint-guide-titles.py
python3 tools/build-site.py
```

## Deeper pointers

`site.toml` and `tools/build-site.py` own navigation and projection details. For
rendered checks, follow [`docs-site/AGENTS.md` § Build](../docs-site/AGENTS.md#build).
