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

## Navigation is generated

`tools/build-site.py` collates this tree into an inventory, then projects it
into the sidebar. Writing the file is all that navigation requires — there is
no config to edit.

- **Group labels and order** are declared in `site.toml`'s `[[guide_groups]]`
  (`dir` + `label`). A directory with no entry still gets a group, labelled from
  its title-cased name and appended last.
- **`order`** sorts a page within its pack group **across kinds** — that is how
  a tutorial, a how-to, and an explanation form one reading sequence. Pages
  without it fall into kind buckets below the ordered run.
- **Labels** resolve `guide-nav-baseline.toml` → `title:` frontmatter →
  filename. An index page falling through to derivation reads `Overview`. The
  baseline is transitional: it froze the pre-generation labels so none
  regressed. Add `title:` to a page and delete its baseline entry — that
  deletion is the deliberate act, and the registry shrinks.

## Traps

- **No link checker.** Starlight does not fail the build on broken internal
  links. Verify targets exist before linking.
- Links out of `guides/` become GitHub blob URLs — they send the reader off the
  site. Prefer an in-tree target.
- `AGENTS.md`, and any `README.md` more than one directory below `guides/`,
  are mirrored but never enter navigation — today that is the four
  `_shared/<kind>/` authoring templates, which address guide *authors*, not
  adopters. They stay reachable by URL. Each prints a `note` at build time.
- **Renaming or deleting a page requires deleting its
  `guide-nav-baseline.toml` entry** in the same change, or the no-regression
  test fails with `labels or pages regressed: {'…': ('Label', '<ABSENT>')}`.

## Verify

```bash
python3 tools/validate_guides.py     # frontmatter + duplicate slugs
python3 tools/check-guide-index.py   # index coverage
python3 tools/build-site.py          # mirror; inspect reported paths
```

Build order for rendered checks: [`docs-site/AGENTS.md`](../docs-site/AGENTS.md) § Build.
