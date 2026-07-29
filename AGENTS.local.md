# AGENTS.local.md

Repo-local addendum for maintainers of this checkout. `AGENTS.md` is adopter-owned — edit it
directly. To propagate changes to new adopters, also update `packs/core/seeds/AGENTS.md`.

- **Pack and skill development** (version bumps, projection, skill authoring, eval coverage, plugin format):
  [`packs/AGENTS.md`](packs/AGENTS.md).
- **Python package development** (install-test rules, Windows compatibility, test conventions):
  [`packages/AGENTS.md`](packages/AGENTS.md).
- **Release coupling** (PyPI release requirements, version bump workflow, tagging):
  [`packages/AGENTS.local.md`](packages/AGENTS.local.md).
- **Catalogue CI** (portable commands, publication ordering, exit codes, responsibility boundary):
  [`guides/_shared/reference/catalogue-ci-contract.md`](guides/_shared/reference/catalogue-ci-contract.md).

**Read before modifying:** `packs/` → read [`packs/AGENTS.md`](packs/AGENTS.md) first — version bump rule requires both `pack.toml` + `.claude-plugin/plugin.json`. `packages/` → read [`packages/AGENTS.local.md`](packages/AGENTS.local.md) first — covers when a PyPI release is required.

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



