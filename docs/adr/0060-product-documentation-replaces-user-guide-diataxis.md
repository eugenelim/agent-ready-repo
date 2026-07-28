# ADR-0060: `product-documentation` replaces `user-guide-diataxis` as the canonical documentation pack

- **Status:** Accepted
- **Date:** 2026-07-28
- **Decision-makers:** eugenelim
- **Related:** `docs/specs/product-documentation-pack/spec.md`, `docs/specs/product-documentation-pack/plan.md`

## Decision summary

- **Decision:** Introduce a new `product-documentation` pack with the `author-product-docs` skill. Convert `user-guide-diataxis` to a deprecated compatibility shim that depends on `product-documentation`.
- **Because:** The old pack conflated structural scaffold (four empty Diátaxis quadrant directories) with authoring guidance. The scaffold created noise for adopters who didn't need all four directories. The new pack treats Diátaxis as a page contract, not a folder requirement.
- **Applies to:** `packs/product-documentation/`, `packs/user-guide-diataxis/`, `profiles/full-ceremony.toml`, `guides/product-documentation/`, `packages/agentbundle/` tests and self-host wiring.
- **Tradeoff accepted:** Adopters who installed `user-guide-diataxis` must install `product-documentation` and migrate to `author-product-docs`. A bare `agentbundle install --pack user-guide-diataxis` errors when `product-documentation` is absent — the dependency model does not auto-install.
- **Revisit if:** agentbundle gains a native alias/supersession mechanism, at which point the shim can be removed and a redirect registered in the catalogue index.

## Context

`user-guide-diataxis` shipped with a `new-guide` skill and a `seeds/` directory that scaffolded four Diátaxis quadrant directories (`tutorials/`, `how-to/`, `reference/`, `explanation/`) into every adopter repo. This was useful for teams starting from zero, but it imposed structure on repos that had different organization preferences.

The key design insight: Diátaxis is a page-authoring discipline, not a mandatory directory layout. A skill can enforce Diátaxis page contracts (tutorials are learning-oriented, how-tos are task-oriented, etc.) without requiring the physical directory shape.

The new `product-documentation` pack:
- Ships no seeds — no scaffold installed on first use.
- Supports five modes: create, revise, retrofit, audit, verify — inferred from natural requests.
- Routes by audience: external user content lands in `guides/<pack>/`; internal maintainer content lands in `docs/guides/`.
- Is portable: it inspects the host repo's existing layout rather than imposing catalogue-specific paths.
- Supports user and repo scope (removing the `core` dependency enables user-scope installs).

`user-guide-diataxis` 0.3.0 becomes a thin shim: no seeds, `new-guide` is a redirect, and the only `[[pack.dependencies.required]]` is `product-documentation ^0.1`. Existing adopters who depend on `user-guide-diataxis` continue to work as long as they install `product-documentation` first.

## Decision

Replace `user-guide-diataxis` as the canonical documentation pack with `product-documentation`. Keep `user-guide-diataxis` as a deprecated shim for backwards compatibility. The shim has no seeds and no evals; its only purpose is to provide the legacy `new-guide` redirect skill for adopters who have not yet migrated.

Migration path for adopters:

1. `agentbundle install --pack product-documentation <catalogue>`
2. `agentbundle install --pack user-guide-diataxis <catalogue>` (optional — only if the legacy `new-guide` redirect is needed during transition)
3. Update skill references from `new-guide` to `author-product-docs`.
