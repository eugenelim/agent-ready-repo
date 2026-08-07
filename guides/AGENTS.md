# AGENTS.md — `guides/` (adopter-facing guide tree)

Source for every adopter guide published to `/agent-ready-repo/docs/guides/`.
Not installed into adopter repos — packs ship seeds; adopters read this on the web.

Write and restructure pages with the `author-product-docs` skill.

## Audience

`guides/` is adopters. `docs/guides/` is repo maintainers (CI, seeds, adapters,
internal tooling). Maintainer guidance written here ships to the public site.

## Publication

`tools/build-site.py` mirrors this tree into the Starlight site on every Pages
build — writing the file is all that publishing requires.

- `guides/<pack>/<kind>/<slug>.md` → `/docs/guides/<pack>/<kind>/<slug>/`
- `README.md` → the directory's index
- `slug:` frontmatter overrides path placement entirely

## Frontmatter

Required: `title`, `summary`, `pack`, `kind`. Optional: `slug`, `order`,
`journey`, `aliases`, `status`. Schema is `contracts/guide.schema.json` with
`additionalProperties: false` — add a field there first, and teach
`build-site.py` to strip it, or it leaks into the rendered page.

`kind` (`tutorial` | `how-to` | `reference` | `explanation`) is a page contract,
not a directory choice — it records what the page does for the reader.

## Traps

- **The sidebar is hand-maintained** in `docs-site/astro.config.ts`. A new page
  publishes but stays out of navigation until you add an entry there in the same
  PR. `generate_sidebar_config()` covers the pack catalogue only, not guides.
- **No link checker.** Starlight does not fail the build on broken internal
  links. Verify targets exist before linking.
- Links out of `guides/` become GitHub blob URLs — they send the reader off the
  site. Prefer an in-tree target.

## Verify

```bash
python3 tools/validate_guides.py     # frontmatter + duplicate slugs
python3 tools/check-guide-index.py   # index coverage
python3 tools/build-site.py          # mirror; inspect reported paths
```

Build order for rendered checks: [`docs-site/AGENTS.md`](../docs-site/AGENTS.md) § Build.
