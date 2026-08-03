# AGENTS.local.md

Repo-local addendum for maintainers of this checkout. `AGENTS.md` is adopter-owned — edit it
directly. To propagate changes to new adopters, also update `packs/core/seeds/AGENTS.md`.

- **Pack and skill development** (version bumps, projection, skill authoring, eval coverage, plugin format):
  **Read [`packs/AGENTS.md`](packs/AGENTS.md) and [`packs/AGENTS.local.md`](packs/AGENTS.local.md) before acting** whenever any file under `packs/` is in scope.
- **Python package development** (install-test rules, Windows compatibility, test conventions, PyPI release requirements):
  **Read [`packages/AGENTS.md`](packages/AGENTS.md) and [`packages/AGENTS.local.md`](packages/AGENTS.local.md) before acting** whenever any file under `packages/` is in scope.
- **Marketing site** (Astro build, Node.js deps, dev server, mobile viewport, link rules):
  [`web/AGENTS.md`](web/AGENTS.md).
- **Catalogue CI** (portable commands, publication ordering, exit codes, responsibility boundary):
  [`guides/_shared/reference/catalogue-ci-contract.md`](guides/_shared/reference/catalogue-ci-contract.md).

## Catalogue authoring scaffold — release-impact policy

The catalogue authoring scaffold is bundled into the `agentbundle` wheel as package data under
`agentbundle/_data/catalogue-scaffold/`. Any change to the scaffold files listed below is
an **agentbundle engine change** and requires:

1. Bumping `packages/agentbundle/pyproject.toml` `version`.
2. Including an `Engine-Change-RFC:` footer in the commit message.
3. Running `python3 tools/catalogue/sync_authoring_scaffold.py --write` before committing.
4. Verifying `python3 tools/catalogue/sync_authoring_scaffold.py --check` exits 0.

**Scaffold files (changes require bump + Engine-Change-RFC marker):**
- `packs/README.md`, `packs/AGENTS.md`
- `packs/_example/` (any file under it)
- `profiles/README.md`, `profiles/AGENTS.md`
- `profiles/_example/` (any file under it)

`build-check` runs `sync_authoring_scaffold.py --check` and fails on drift.

## No AC citation comments in .apm/ scripts

`# AC14:`, `# AC36:` and similar prefixes in source files under `.apm/**` leak spec vocabulary to adopters. Strip the identifier; keep the invariant description. Write `# must not traverse symlinks` not `# AC14: must not traverse symlinks`.

## House style for internal docs

Applies to prose that stays in this repo and never ships: this file, `docs/architecture/`, `docs/specs/`,
RFCs, ADRs, internal READMEs. The adopter-facing version ships in the `product-documentation` pack's
`author-product-docs` skill (`references/clear-prose.md`).

- **Write prose that reads like a person wrote it.** Cut hedges ("it's worth noting"), uniform sentence
  rhythm, em-dash overuse, throat-clearing openers, inflated verbs ("leverage", "utilize", "delve").
  Vary sentence length; one claim per sentence; concrete number or example over adjective.
- **Catch structural tells.** Check each draft: does the argument advance paragraph to paragraph, or
  restate? Does each list item earn its slot? Is there a position the text can be disagreed with?
  Is any specific detail grounded (a name, a date, a count), or only performed? Watch for: treadmill
  effect, symmetrical lists that pad a template, false precision, performative thoroughness, nice-nice
  wrap (both sides hedged, no stance).
- **State what is — don't leak rationale or identity.** Cut asides that justify mid-sentence;
  give the "why" its own sentence or drop it. No self-narration ("internally we…", "our goal here is…").
- **Soft-wrap guides.** Under `docs/guides/`, one line per paragraph, blank line between paragraphs,
  list items one line each. Older docs (README, CONVENTIONS) are hard-wrapped near 72 columns; match
  the file you're editing.



