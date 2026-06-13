# ADR-0020: Per-pack Diátaxis hierarchy for `docs/guides/`

- **Status:** Accepted
- **Date:** 2026-06-13
- **Deciders:** eugenelim
- **Supersedes:** none — **amends** ADR-0001's `docs/guides/` organization sub-decision only (the rest of ADR-0001 stands; ADR-0001 remains Accepted)
- **Related:** [ADR-0001](0001-adopt-agents-md-and-doc-hierarchy.md), [RFC-0031](../rfc/0031-catalogue-package-manager-posture.md), [RFC-0030](../rfc/0030-product-engineering-pack.md), [`docs/specs/enriched-pack-manifest/`](../specs/enriched-pack-manifest/spec.md), [`docs/CONVENTIONS.md` §5c](../CONVENTIONS.md)

## Context

RFC-0031 set a package-manager posture for the catalogue: each pack's manifest carries a `documentation` link back to that pack's guides. The catalogue is a *many-pack* product — 12 packs today (`product-engineering` landed via RFC-0030) — and growing.

ADR-0001 chose [Diátaxis](https://diataxis.fr/) for `docs/guides/` with the **four content types at the top level** (`tutorials/`, `how-to/`, `reference/`, `explanation/`). That fits a single-product view. For a many-pack catalogue, a reader (and a `documentation` link) needs a *per-pack* home, and Diátaxis explicitly permits a second hierarchy dimension: its [complex-hierarchies guidance](https://diataxis.fr/complex-hierarchies/) sanctions putting the product *segment* at the top level with the four types within each — chosen by "how do users see the product?" For a catalogue, users see it *by pack*.

Two constraints bound the shape:
- **The README is the only portable per-pack doc.** Deep guides are *not* installed into packs or adopter repos: 8 of 12 packs are user-scope and the seeds-rail (`scope_rails.py:87`) forbids them shipping `seeds/`, and installing guides isn't spec-compliant. Deep guides stay repo-internal and are reached via the `documentation` link-out.
- **`CONVENTIONS.md` is a Living doc** that must match reality, so the §5c wording and the actual guide migration land *together* (see Decision → deferred implementation), not ahead of the move.

## Decision

**We will organize `docs/guides/` by pack at the top level, preserving the four Diátaxis types within each pack:** `docs/guides/<pack>/{tutorials,how-to,reference,explanation}/`. The four-type discipline (one piece of content per type; "link out" rather than mix) is unchanged — it now applies *within* each pack's subtree. This **amends ADR-0001's guides sub-decision** (four types at the top level); every other ADR-0001 decision stands.

Boundaries on the decision:
- **Cross-cutting guides** that aren't specific to one pack (repo-wide workflow, contributing) keep a shared home (a top-level `docs/guides/_shared/<quadrant>/` or equivalent), not duplicated per pack.
- **The adopter-facing seed scaffold** (the `user-guide-diataxis` pack) stays **type-at-top** — an adopter is one product, not a catalogue of packs. The internal/adopter divergence is intentional and documented.
- Each pack's `pack.toml` `[pack.links].documentation` targets `docs/guides/<pack>/`.

**Implementation:** carried out by the [`enriched-pack-manifest`](../specs/enriched-pack-manifest/plan.md) spec — migrating the ~30 existing guides into per-pack folders (T12), updating the `new-guide` skill's write path to `docs/guides/<pack>/<quadrant>/<slug>.md`, and amending `CONVENTIONS.md §5c` (T13) — all co-landing so the Living doc matches reality. (This ADR records the decision; the spec/plan PR defines the tasks, and the file moves run in that spec's execution.)

## Consequences

**Positive:**
- Clean, scalable per-pack `documentation` link-backs — each pack has a real docs home, matching the package-manager posture.
- Diátaxis discipline preserved (four types, within each pack).
- The choice is the one Diátaxis itself sanctions for a segmented product.

**Negative:**
- Migrating ~30 guides + updating the `new-guide` skill is real, deferred work.
- A shared home for cross-cutting guides must be defined and policed (not everything is pack-specific).
- Intentional divergence between our internal layout (pack-at-top) and the adopter seed scaffold (type-at-top) must be documented so it doesn't read as drift.

**Neutral / to revisit:**
- A guide that genuinely spans packs: prefer a shared doc + cross-links over duplication.

## Alternatives considered

- **Keep type-at-top (ADR-0001 status quo) + a per-pack landing page in `explanation/`.** Rejected: a single landing page per pack doesn't scale into a real per-pack docs home, and the catalogue's natural reader entry point is the pack.
- **Co-locate guides under `packs/<pack>/` and ship them with the pack.** Rejected: not portable — the seeds-rail blocks the 7 user-scope packs — and not spec-compliant; it also muddies the repo-owned-vs-shipped boundary. The README (link-out) is the portable layer instead.
- **Free-form, non-Diátaxis docs.** Rejected, per ADR-0001's original reasoning (mixing types is the dominant cause of bad docs).

## References

- [Diátaxis — complex hierarchies](https://diataxis.fr/complex-hierarchies/)
- ADR-0001 (the guides sub-decision this amends); RFC-0031 (package-manager posture); `scope_rails.py:87` (the seeds-rail constraint).
