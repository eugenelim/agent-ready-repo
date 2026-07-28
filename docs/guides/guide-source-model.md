# Guide source model — maintainer reference

This document is for repository maintainers and contributors. It explains how catalogue-facing product documentation is structured, validated, and built in this repository.

---

## 1. `guides/` versus `docs/guides/`

| Location | Audience | Built into |
|---|---|---|
| `guides/` | Adopters and end users of the catalogue | Docs site (`build/docs/guides/`) |
| `docs/guides/` | Repository maintainers and contributors | Not in the external docs site |

**`guides/`** is the canonical source for catalogue-facing product documentation. Its files are mirrored into `docs-site/src/content/docs/guides/` by `tools/build-site.py` and rendered at public URLs.

**`docs/guides/`** (this directory) is internal maintainer material. It is not mirrored by `build-site.py` and never appears in the external docs site. Do not add external user content here.

---

## 2. Guide metadata contract

Every catalogue-facing guide under `guides/` should carry YAML frontmatter. The schema is defined in `contracts/guide.schema.json` and enforced by `tools/validate_guides.py`.

**Required fields:**

```yaml
---
title: "Page title for the docs-site renderer"
summary: "One sentence: what the reader gains from this page."
pack: product-documentation   # must be a packs/ directory name or _shared
kind: tutorial                # tutorial | how-to | reference | explanation
---
```

**Optional fields:**

```yaml
slug: guides/product-documentation/getting-started   # override public URL
journey: product-documentation-first-run             # journey association
order: 1                                             # sort weight for navigation
aliases:                                             # former public slugs → redirect here
  - guides/product-documentation/old-name
status: stable                                       # draft | review | stable | deprecated
```

**Diátaxis kind is metadata, not a directory.** A file at `guides/atlassian/work-with-jira.md` may declare `kind: how-to` without living in a `how-to/` folder. The physical directory determines nothing about the page's role.

**Valid pack IDs:** any directory name in `packs/` (e.g. `core`, `product-documentation`, `architect`), plus `_shared` for cross-cutting guides under `guides/_shared/`.

---

## 3. Flat versus topic-first organization

**Flat (preferred for new guides):**
```
guides/product-documentation/getting-started.md
guides/product-documentation/guide-source-overview.md
```

**Topic-first (use when a pack genuinely needs grouping):**
```
guides/atlassian/jira/work-with-jira.md
guides/atlassian/confluence/crawl-confluence.md
```

Use topic folders when:
- A pack has five or more guides that fall into coherent functional groups (e.g. jira, confluence).
- The grouping reflects the reader's mental model, not just a Diátaxis kind.

Do not create `tutorial/`, `how-to/`, `reference/`, `explanation/` subdirectories for new guides. Diátaxis kind belongs in frontmatter. Existing guides in kind-named directories continue to work — no need to move them.

---

## 4. How public routes are preserved

The public URL of a guide is determined by **where `build-site.py` writes the file**, not where the source lives.

**Default routing:** if the source has no `slug:` frontmatter, the output path mirrors the source path relative to `guides/`. A source at `guides/core/explanation/core-pack.md` produces the Starlight slug `guides/core/explanation/core-pack`.

**Slug override:** if the source has `slug: guides/core/explanation/core-pack` in frontmatter, `build-site.py` writes the file to that exact path regardless of the source location. This lets a guide move from a nested path to a flat path without breaking the public URL:

```yaml
---
title: "The Core Pack"
summary: "…"
pack: core
kind: explanation
slug: guides/core/explanation/core-pack   # preserves the old URL after a source flatten
---
```

After confirming the new URL works and links are updated, remove the `slug:` override and the old source file.

---

## 5. How aliases work

An alias declares that a former public URL should redirect to the current page. `build-site.py` generates a meta-refresh redirect stub at each alias path when building the docs site.

```yaml
---
title: "Work with Jira"
summary: "…"
pack: atlassian
kind: how-to
aliases:
  - guides/atlassian/how-to/old-jira-guide   # redirects here from this former URL
---
```

The redirect stub at `guides/atlassian/how-to/old-jira-guide` contains a meta-refresh pointing to the canonical page. Readers with bookmarks, search-engine hits, or inbound links at the old URL are redirected automatically.

Aliases must be unique across the entire guides corpus — two guides cannot claim the same alias. The validator (`tools/validate_guides.py`) enforces this.

---

## 6. How to migrate one guide

1. **Move or rewrite the canonical source.** Create `guides/<pack>/<new-slug>.md` (or `guides/<pack>/<topic>/<new-slug>.md`) with valid frontmatter. If the guide already exists at a nested path and you want to flatten it, add `slug: <old-path>` in the frontmatter to preserve its URL for now.
2. **Preserve its route or add an approved alias.** If the URL changes, add the old URL to `aliases:` in the frontmatter.
3. **Update links.** Search for links pointing to the old guide path and update them to the new path. Check `guides/`, `docs/`, and any pack READMEs.
4. **Build and verify.** Run `python tools/build-site.py --dry-run` to confirm the output path is correct. Run `python tools/validate_guides.py guides/<pack>/` to confirm the frontmatter is valid.
5. **Remove the old canonical source and confirm no duplicate.** Delete the old source file, then run `python tools/validate_guides.py guides/` to confirm no two files claim the same canonical slug and the exit code is 0.

---

## 7. How to validate guide ownership

Run the validator on any subset of guides:

```bash
# Validate one pack's guides
python tools/validate_guides.py guides/product-documentation/

# Validate all guides
python tools/validate_guides.py guides/

# Validate a single file
python tools/validate_guides.py guides/product-documentation/getting-started.md
```

Exit 0 means all checked files passed. Exit 1 means one or more errors. Warnings (dangling aliases, `_reference` pack, no-frontmatter files) are printed to stderr but do not affect the exit code.

---

## 8. How to avoid editing generated output

The docs site at `docs-site/src/content/docs/guides/` is **generated output** — do not edit it directly. All changes must be made to source files under `guides/` (or `docs/guides/` for internal material). The generated directory is gitignored; your edits will be overwritten the next time `python tools/build-site.py` runs.

To preview your changes:
```bash
python tools/build-site.py          # regenerate
make site-serve                     # start local Starlight dev server
```

---

## 9. Running the validator

```bash
# One-time setup (if not already installed)
pip install -r tools/requirements.txt

# Validate a pack
python tools/validate_guides.py guides/product-documentation/

# Validate all guides
python tools/validate_guides.py

# Show help
python tools/validate_guides.py --help
```

The validator is also wired into `make test` (`tools/test_validate_guides.py`). It checks schema compliance, pack IDs, kind values, and cross-guide uniqueness (slugs, aliases). It does **not** scan `docs/guides/` — that directory is internal and not subject to the external guide metadata contract.
