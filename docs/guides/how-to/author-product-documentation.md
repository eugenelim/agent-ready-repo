# How to author product documentation for this catalogue

**Audience:** contributors and maintainers of this catalogue repository.
**Purpose:** explains the documentation ownership split, where to write each kind of content, and how to use the `author-product-docs` skill.

---

## Two guide trees

This repository has two separate documentation trees with distinct audiences.

| Tree | Audience | Ships? |
|---|---|---|
| `guides/` | External — catalogue users and pack adopters | Yes, via docs-site and web/ |
| `docs/guides/` | Internal — repo maintainers and contributors | No |

**The rule:** if the reader is an adopter who installed a pack and wants to use it, write in `guides/`. If the reader works inside this repository on the catalogue itself, write in `docs/guides/`.

When in doubt: would someone following the public install guide ever need this page? Yes → `guides/`. It requires repo-internal context → `docs/guides/`.

---

## Where each artifact lives

| Artifact | Location | Updated by |
|---|---|---|
| Pack user guides, tutorials, how-tos, references, explanations | `guides/<pack>/` | `author-product-docs` skill or hand |
| Guide index for a pack | `guides/<pack>/README.md` | Same PR as new guide |
| Pack landing and discovery page | `packs/<pack>/README.md` | `author-product-docs` or hand |
| Pack maintainer design record | `packs/<pack>/DESIGN.md` | Pack maintainers (hand) |
| Proposed first-value journey | `packs/<pack>/JOURNEY.md` | `author-product-docs` or hand |
| Maintainer how-tos (this file) | `docs/guides/how-to/` | Hand |
| Maintainer reference | `docs/guides/reference/` | Hand |
| Maintainer explanations | `docs/guides/explanation/` | Hand |

---

## How to use the `author-product-docs` skill

The skill is in the `product-documentation` pack. Install it once at repo scope:

```bash
agentbundle install --pack product-documentation
```

Then describe what you need:

```
Write a how-to guide for the desk-research pack covering how to start a research project
```

```
The architect pack README leads with skill names — update it to lead with outcomes
```

```
Audit the credential-brokers guides and tell me what's missing or out of date
```

The skill infers the mode (create, revise, retrofit, audit, or verify), reads canonical sources before making claims, routes to the correct tree, and picks one artifact unless more are clearly needed.

---

## Avoiding common mistakes

**Writing adopter-facing docs to `docs/guides/`** — `docs/guides/` is never projected or shipped. A guide about how to *use* a pack belongs in `guides/<pack>/`, not here. The pages in `docs/guides/` are for maintainers of this repo.

**Editing rendered output** — `web/` and `docs-site/` are rendering systems. Their output is generated from canonical sources in `guides/` and `packs/`. Editing a rendered file is overwritten on the next `make build-self`. Edit the source file and let the build regenerate.

**Using `docs/guides/` as the public documentation tree** — historically this repo's internal convention was to call the public guide tree `docs/guides/`, which conflicts with the convention that `docs/` is internal. The canonical assignment is: `guides/` for adopters, `docs/guides/` for maintainers.

---

## See also

- [guides/README.md](../../../guides/README.md) — the catalogue-wide guide index for adopters
- [How to use author-product-docs](../../../guides/product-documentation/how-to/use-author-product-docs.md) — the user-facing how-to for the skill
- [packs/AGENTS.md](../../../packs/AGENTS.md) — pack authoring conventions including version bumps and projection
