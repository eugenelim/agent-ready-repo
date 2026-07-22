# How-to guides

> *Task-oriented.* Recipes for solving specific problems the reader brought with them. Assumes baseline competence; doesn't teach.

## Writing a how-to

A good how-to:

- **Solves one named problem.** The title is the problem: "Configure X for production", "Migrate from Y to Z", "Debug a failing W".
- **Assumes the reader is competent.** Doesn't reteach the basics. Links to tutorials for foundational concepts.
- **Is goal-oriented.** Skip context that isn't needed to accomplish the goal. The reader is here to *do something*, not to learn.
- **Handles the realistic version.** Cover the common variations and pitfalls — that's what makes how-tos different from "just read the reference."
- **Is named for what the reader was searching for.** "How to configure rate limiting" beats "Rate limiting configuration guide."

## What goes in a how-to

- A clear problem statement at the top.
- Prerequisites and assumptions.
- The steps to accomplish the goal — terser than a tutorial.
- Variations the reader is likely to need.
- Pitfalls and how to recognize them.
- Links to relevant reference material.

## What does NOT go in a how-to

- Step-by-step beginner instruction. That's a tutorial.
- Complete authoritative description of every option. That's reference.
- Why-this-design explanations. That's an explanation page.

## Maintenance

How-tos drift when the product changes underneath them. Make doc updates part of the spec workflow: when a spec ships, check whether any how-to references the changed behavior, and update in the same PR.

## Pages in this directory

- [`author-a-skill.md`](author-a-skill.md) — frontmatter, body structure, naming, directory layout, dependency tiers, and eval authoring for skills in any pack.
- [`build-an-org-stack-pack.md`](build-an-org-stack-pack.md) — scaffold and populate a pack for an org's own tools and conventions.
- [`configure-adapter.md`](configure-adapter.md) — set up or change the active adapter for a pack.
- [`design-a-profile.md`](design-a-profile.md) — four design tests for a profile, worked examples from the three shipped profiles, and how to propose a new one via RFC.
- [`install-a-profile.md`](install-a-profile.md) — install a named profile in one command.
- [`install-agentbundle-from-clone.md`](install-agentbundle-from-clone.md) — install from a local clone instead of the registry.
- [`install-user-scope-pack-into-codex.md`](install-user-scope-pack-into-codex.md) — user-scope pack install on the Codex adapter.
- [`install-user-scope-pack-into-kiro.md`](install-user-scope-pack-into-kiro.md) — user-scope pack install on the Kiro adapter.
- [`preview-install-or-upgrade.md`](preview-install-or-upgrade.md) — dry-run an install or upgrade before committing.
- [`run-a-full-inception.md`](run-a-full-inception.md) — run the inception sequence on a new repo.
- [`upgrade-packs.md`](upgrade-packs.md) — upgrade one or all installed packs to the latest version.
- [`choose-a-tracker-integration.md`](choose-a-tracker-integration.md) — pick the right brief-intake skill for your tracker (GitHub, Linear, Jira, Jira Align, or none).
