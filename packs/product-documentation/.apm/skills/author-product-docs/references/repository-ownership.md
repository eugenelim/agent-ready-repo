# Repository ownership

Defines which documentation tree owns which content. The most common documentation bug is writing external product docs to the internal maintainer tree, or the reverse.

## The ownership split (this catalogue)

| Tree | Audience | Ships to adopters? | Owns |
|---|---|---|---|
| `guides/` | **External — catalogue users and pack adopters** | Yes (via docs-site and web/) | Pack guides, user how-tos, tutorials, references, explanations, journey documentation |
| `docs/guides/` | **Internal — repo maintainers and contributors** | No | Maintainer how-tos (CI workflows, pack authoring, catalogue operations), internal reference |
| `packs/<pack>/README.md` | **External — pack discoverers and users** | Yes (via plugin manifests and catalogue) | Pack landing page: what it does, how to start, install |
| `packs/<pack>/DESIGN.md` | **Internal — pack maintainers** | No (stays in pack source) | Architecture decisions, design rationale, maintainer notes |
| `packs/<pack>/JOURNEY.md` | **External — pack users** | Proposed optional | First-value journey: start-to-finish user flow |
| `web/` and `docs-site/` | Rendering systems | Consumed from `guides/` | Route generation only — not where new documentation is authored |

**Decision rule:** if the reader is an external user of the catalogue (someone who installed a pack and wants to use it), write in `guides/`. If the reader is a person working inside this repo on the catalogue itself (authoring skills, maintaining packs, operating CI), write in `docs/guides/`.

When in doubt: would someone following the public install guide ever need this? If yes → `guides/`. If it requires repo access and context → `docs/guides/`.

---

## This catalogue's guide structure

External guides in `guides/` are organized by pack:

```
guides/
  <pack-name>/
    README.md          ← guide index for this pack
    tutorials/
    how-to/
    reference/
    explanation/
  _shared/
    tutorials/         ← cross-cutting user guides
    how-to/
    reference/
    explanation/
```

Internal guides in `docs/guides/` use a flat structure:

```
docs/guides/
  how-to/              ← maintainer how-tos
  reference/           ← internal reference
  explanation/         ← internal explanations
```

Neither structure is mandatory for adopter repositories. See the adopter layout section below.

---

## Pack README and DESIGN ownership

`packs/<pack>/README.md` is the **canonical pack landing and discovery document**. It is the source of truth for the pack's human-facing description; the `pack.toml` is the source of truth for machine facts (version, scope, dependencies).

When both exist and diverge, `pack.toml` is authoritative for machine facts. Do not duplicate version numbers, scope, or dependency declarations in `README.md` when they can go stale.

`packs/<pack>/DESIGN.md` is the **maintainer design record**. This skill reads it during audit and verify modes for architecture claims. It does not author `DESIGN.md` by default; maintainers own that file.

---

## Journey ownership (proposed)

`packs/<pack>/JOURNEY.md` is reserved as the optional first-value journey. The concept and ownership boundary are established but the convention is not yet fully enforced. Create a journey file when:

- The pack has a clear first-value sequence (step-by-step from installation to the first meaningful outcome)
- The journey is not already documented well in the pack README
- The journey needs to be referenced by the docs-site or web renderer

Do not migrate existing journey content from other locations in this phase.

---

## Rendered output (do not edit directly)

`web/` and `docs-site/` are rendering systems. Their output is generated from canonical sources in `guides/` and `packs/`. Editing a generated file does not change the canonical content and the edit will be overwritten on the next build.

The canonical source for a pack page is `web/src/content/packs/<pack>.md` (Astro content collection). The canonical source for guide pages is the file in `guides/<pack>/`. Edit those; let the build render the output.

---

## Adopter repositories (portable use)

This skill is portable. When running in an adopter repository (not the agent-ready-repo catalogue), do not impose the `guides/` + `docs/guides/` split.

Instead:
1. **Inspect** the host repo's existing documentation structure before writing anything.
2. **Ask once** if the structure is absent and the destination affects the artifact type.
3. **Write to the structure the repo already uses.**
4. Describe the ownership concept (user-facing vs. maintainer-facing) rather than prescribing specific paths.

An adopter that uses `docs/` for everything and `src/docs/` for API docs has a valid layout. Don't override it with this catalogue's conventions.
