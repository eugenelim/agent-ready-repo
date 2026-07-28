---
title: "Getting Started with Product Documentation"
summary: "Learn how to author, validate, and publish catalogue-facing product guides in this repository."
pack: product-documentation
kind: tutorial
slug: guides/product-documentation/getting-started
status: stable
---

This tutorial walks you through creating and publishing a product guide from scratch.

## Prerequisites

- Write access to the repository
- `pip install -r tools/requirements.txt` run once (installs PyYAML, jsonschema)

## Step 1 — Create your guide file

Place your guide under `guides/<pack-id>/` using a kebab-case filename:

```
guides/product-documentation/my-new-guide.md
```

For packs with many guides, add a topic folder:

```
guides/product-documentation/authoring/my-new-guide.md
```

## Step 2 — Add required frontmatter

Every published guide needs four required fields:

```yaml
---
title: "My New Guide"
summary: "One sentence: what the reader gains from this page."
pack: product-documentation
kind: how-to
---
```

Valid values for `kind`: `tutorial`, `how-to`, `reference`, `explanation`.

## Step 3 — Validate your frontmatter

```bash
python tools/validate_guides.py guides/product-documentation/my-new-guide.md
```

Exit 0 means the guide is valid. See `docs/guides/guide-source-model.md` for the full field reference.

## Step 4 — Preview locally

```bash
python tools/build-site.py   # mirrors guides/ into docs-site/
make site-serve              # starts the Starlight dev server
```

Open your browser to the URL printed by `make site-serve`.

## Step 5 — Open a pull request

Commit your guide source file under `guides/` (not the generated output
under `docs-site/`). The CI pipeline runs `validate_guides.py` and
rebuilds the site automatically.
