# AGENTS.local.md

Repo-local addendum for maintainers of this checkout. This is a **pack catalogue** — it ships packs
into adopter repositories via APM, Claude plugins, and the CLI.

- **Pack and skill development** (version bumps, projection, skill authoring, eval coverage, plugin format):
  [`packs/AGENTS.md`](packs/AGENTS.md).
- **Python package development** (install-test rules, Windows compatibility, release coupling):
  [`packages/AGENTS.md`](packages/AGENTS.md).

## Design against the adopter's projected state, not this repo's internal state

When designing or validating any pack-shipped feature:

- Validate against the **pack template/seed** (e.g. `packs/core/.apm/skills/new-spec/assets/spec.md`),
  not this repo's hand-authored examples.
- Ask: *does this happen in a fresh adopter's template-shaped tree, or only in this repo's internal
  corpus?* The former is a design bug; the latter is a self-host edge case.
- Coverage that matters is the per-adapter projected layout and the installed runtime surface, not
  what happens to be true in this checkout.

## House style for internal docs

Applies to prose that stays in this repo and never ships (this file, `docs/architecture/`, `docs/specs/`, RFCs, ADRs).

- Write prose that reads like a person wrote it. Cut hedges, uniform rhythm, em-dash overuse.
- State what is — don't leak rationale or identity.
- Soft-wrap `docs/guides/`. Older docs (README, CONVENTIONS) are hard-wrapped near 72 columns.

## AGENTS.md line caps — enforced by CI

Root `AGENTS.md` ≤ 250 lines; every sub-directory `AGENTS.md` ≤ 150 lines. Exceeding the cap blocks
all three CI jobs. Keep files tight — they load into agent context.

## `docs/guides/` is organized by pack in this repo

This catalogue organizes user docs **by pack**: `docs/guides/<pack>/{tutorials,how-to,reference,explanation}/`
for pack-specific guides; `docs/guides/_shared/{quadrant}/` for cross-cutting ones.

## New tool scripts: Python, not bash

New additions to `tools/` must be pure-stdlib Python (`.py`). Existing `.sh` files stay. Path triggers
in `.github/workflows/docs.yml` must match `python3 <script>`.
