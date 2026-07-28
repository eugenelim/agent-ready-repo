# Repository ownership

This reference defines which location owns which documentation concern. The
ownership split prevents catalogue-specific paths from leaking into adopter
repositories and prevents public product documentation from landing in internal
maintainer trees.

## This catalogue (agent-ready-repo)

### `guides/` — catalogue-facing product documentation

Top-level `guides/` contains tutorials, how-to guides, reference pages, and
explanations intended for users of the catalogue and its packs. Organized by
pack: `guides/<pack>/<kind>/<slug>.md`.

- Do not write internal maintainer guidance here.
- Do not write feature specifications or ADRs here.
- The `guides/<pack>/README.md` is the pack's guide-section landing page.

### `docs/guides/` — internal maintainer and contributor guidance

`docs/guides/` contains authoring how-tos, operating procedures, and contributor
guidance for people who maintain or extend this catalogue. Not intended for end
users of the catalogue's packs.

- Do not delete or repurpose this tree as a public guide tree.
- Preserve useful internal maintainer guides here.

### `packs/<pack>/README.md` — pack landing and discovery source

The pack's canonical landing document. Source of truth for what the pack does,
the first useful request, major jobs, install information, and links to deeper
documentation. Machine facts (version, scope, dependencies) are validated
against `pack.toml`.

### `packs/<pack>/DESIGN.md` — maintainer design source

Maintainer-facing design and architecture notes. Read to verify facts when
authoring product documentation. Not a product-documentation page; not authored
by default.

### `packs/<pack>/JOURNEY.md` — proposed optional canonical journey

Reserved as the canonical location for a pack's first-value journey page.
Concept and ownership boundary defined in Phase 1. Do not migrate existing
journey files from other locations until a later phase.

### `web/` and `docs-site/` — rendering systems

These render canonical content but are not sources of new or duplicate pack
documentation. Do not edit rendered output directly. When a web or docs-site
entry is stale, update the source content (`guides/`, `packs/*/README.md`) and
regenerate.

---

## Adopter repositories

The skill is portable. When running in an adopter repository (not this
catalogue), inspect the host's configured and existing documentation locations
rather than assuming any of the paths above.

- Look for a `docs/` tree, a `guides/` tree, or a documentation root declared
  in the project's `AGENTS.md` or `CLAUDE.md`.
- Distinguish user-facing from maintainer-facing content by what the host
  already has, not by imposing the catalogue's structure.
- Do not create `guides/` or `docs/guides/` in an adopter repo if neither
  exists and neither is requested.

---

## Summary table

| Source | Audience | Authored by this skill by default |
|---|---|---|
| `guides/<pack>/` | External product users | Yes |
| `docs/guides/` | Internal maintainers | Yes (maintainer-facing requests only) |
| `packs/<pack>/README.md` | External users evaluating the pack | Yes |
| `packs/<pack>/DESIGN.md` | Pack maintainers | No (read-only input) |
| `packs/<pack>/JOURNEY.md` | External users: first-value journey | Yes |
| `web/`, `docs-site/` | Rendering systems | No (update sources, regenerate) |
| Adopter `docs/` or `guides/` | Adopter users | Yes (inspect host layout first) |
