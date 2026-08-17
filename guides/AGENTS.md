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

`summary` is published: `build-site.py` maps it onto Starlight's `description`,
which becomes the page's `<meta name="description">`, its search snippet, and
the deck rendered under the title. Write it for a reader who has not opened the
page.

**`title` and the body H1 must agree.** Starlight renders `title:` as the page
`<h1>`, so `build-site.py` strips a *leading* body H1 to avoid a second one.
Keep the H1 and make it match — `guides/_shared/**` ships verbatim into adopter
catalogues and bundles where frontmatter never renders, so a page with no H1
opens with no heading there. `tools/lint-guide-titles.py` fails CI on a
divergence, and on a body H1 that is not the first block (the build cannot strip
that one, so it renders as a second `<h1>`).

## Navigation is generated

`tools/build-site.py` collates this tree into an inventory, then projects it
into the sidebar. Writing the file is all that navigation requires — there is
no config to edit.

- **Group labels and order** are declared in `site.toml`'s `[[guide_groups]]`
  (`dir` + `label`). **An entry is required for every directory, and an entry
  with no directory fails the same test** — delete a pack's entry when you
  delete the pack. The title-cased fallback is a safety net, not a supported path:
  it would render `iac-terraform` as "Iac Terraform" rather than its curated
  label.
- **`order`** sorts a page within its pack group **across kinds** — that is how
  a tutorial, a how-to, and an explanation form one reading sequence. Pages
  without it fall into kind buckets below the ordered run.
- **Labels** resolve `guide-nav-baseline.toml` → `title:` frontmatter →
  filename. An index page falling through to derivation reads `Overview`. The
  baseline is transitional: it froze the pre-generation labels so none
  regressed. Add `title:` to a page and delete its baseline entry — that
  deletion is the deliberate act, and the registry shrinks.

## Traps

- **Starlight itself does not fail the build on broken internal links** — but
  the repository does check them, after both sites are built, with
  `tools/check-rendered-site-links.py`. Run `make site-link-check` locally; CI
  runs the same checker in `.github/workflows/pages.yml`. Verify targets exist
  before linking rather than waiting for the gate.
- Links out of `guides/` become GitHub blob URLs — they send the reader off the
  site. Prefer an in-tree target.
- `AGENTS.md`, and any `README.md` more than one directory below `guides/`,
  are mirrored but never enter navigation — today that is the four
  `_shared/<kind>/` authoring templates, which address guide *authors*, not
  adopters. They stay reachable by URL. Each prints a `note` at build time.
- **The nav-ineligible set is pinned by a test.** Adding a section index below
  kind level (`<pack>/how-to/README.md`) fails
  `test_nav_ineligible_set_is_exactly_the_declared_exceptions`; update it and
  the spec's § Intent carve-out in the same change.
- **Renaming or deleting a page requires deleting its
  `guide-nav-baseline.toml` entry** in the same change, or the no-regression
  test fails with `labels or pages regressed: {'…': ('Label', '<ABSENT>')}`.

## Verify

```bash
python3 tools/validate_guides.py     # frontmatter + duplicate slugs
python3 tools/check-guide-index.py   # index coverage
python3 tools/lint-guide-titles.py   # title vs body H1
python3 tools/build-site.py          # mirror; inspect reported paths
```

Build order for rendered checks: [`docs-site/AGENTS.md`](../docs-site/AGENTS.md) § Build.
