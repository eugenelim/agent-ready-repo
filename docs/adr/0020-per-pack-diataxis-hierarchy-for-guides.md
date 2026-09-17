# ADR-0020: Per-pack Diátaxis hierarchy for `guides/`

- **Status:** Accepted
- **Date:** 2026-06-13
- **Areas:** documentation
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0001 D3
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0001; RFC-0031; RFC-0030; `docs/CONVENTIONS.md` §5c

## Context

RFC-0031 set a package-manager posture for the catalogue: each pack's manifest carries a `documentation` link back to that pack's guides. The catalogue is a *many-pack* product — 12 packs today (`product-engineering` landed via RFC-0030) — and growing.

ADR-0001 chose [Diátaxis](https://diataxis.fr/) for `guides/` with the **four content types at the top level** (`tutorials/`, `how-to/`, `reference/`, `explanation/`). That fits a single-product view. For a many-pack catalogue, a reader (and a `documentation` link) needs a *per-pack* home, and Diátaxis explicitly permits a second hierarchy dimension: its [complex-hierarchies guidance](https://diataxis.fr/complex-hierarchies/) sanctions putting the product *segment* at the top level with the four types within each — chosen by "how do users see the product?" For a catalogue, users see it *by pack*.

Two constraints bound the shape:
- **The README is the only portable per-pack doc.** Deep guides are *not* installed into packs or adopter repos: 8 of 12 packs are user-scope and the seeds-rail (`scope_rails.py:87`) forbids them shipping `seeds/`, and installing guides isn't spec-compliant. Deep guides stay repo-internal and are reached via the `documentation` link-out.
- **`CONVENTIONS.md` is a Living doc** that must match reality, so the §5c wording and the actual guide migration land *together* (see Decision → deferred implementation), not ahead of the move.

## Decision

**We will organize `guides/` by pack at the top level, preserving the four Diátaxis types within each pack:** `guides/<pack>/{tutorials,how-to,reference,explanation}/`. The four-type discipline (one piece of content per type; "link out" rather than mix) is unchanged — it now applies *within* each pack's subtree. This **amends ADR-0001's guides sub-decision** (four types at the top level); every other ADR-0001 decision stands.

- **D1:** `guides/` is organized by pack at the top level, as
  `guides/<pack>/{tutorials,how-to,reference,explanation}/`.
- **D2:** The four-type Diátaxis discipline — one piece of content per type, link
  out rather than mix — applies within each pack's subtree.
- **D3:** Cross-cutting guides that are not specific to one pack keep a single
  shared home rather than being duplicated per pack.
- **D4:** The adopter-facing `user-guide-diataxis` seed scaffold stays
  type-at-top, and that internal/adopter divergence is documented.
- **D5:** Each pack's `pack.toml` `[pack.links].documentation` targets
  `guides/<pack>/`.

Boundaries on the decision:
- **Cross-cutting guides** that aren't specific to one pack (repo-wide workflow, contributing) keep a shared home (a top-level `guides/_shared/<quadrant>/` or equivalent), not duplicated per pack.
- **The adopter-facing seed scaffold** (the `user-guide-diataxis` pack) stays **type-at-top** — an adopter is one product, not a catalogue of packs. The internal/adopter divergence is intentional and documented.
- Each pack's `pack.toml` `[pack.links].documentation` targets `guides/<pack>/`.

**Implementation:** carried out by the [`enriched-pack-manifest`](../specs/enriched-pack-manifest/plan.md) spec — migrating the ~30 existing guides into per-pack folders (T12), updating the `new-guide` skill's write path to `guides/<pack>/<quadrant>/<slug>.md`, and amending `CONVENTIONS.md §5c` (T13) — all co-landing so the Living doc matches reality. (This ADR records the decision; the spec/plan PR defines the tasks, and the file moves run in that spec's execution.)

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

**Revisit if:** guides that genuinely span packs become common enough that the
shared home (D3) plus cross-links no longer avoids duplication, or the internal
pack-at-top layout and the adopter type-at-top scaffold (D4) can no longer be kept
legibly distinct.

## Alternatives considered

- **Keep type-at-top (ADR-0001 status quo) + a per-pack landing page in `explanation/`.** Rejected: a single landing page per pack doesn't scale into a real per-pack docs home, and the catalogue's natural reader entry point is the pack.
- **Co-locate guides under `packs/<pack>/` and ship them with the pack.** Rejected: not portable — the seeds-rail blocks the 7 user-scope packs — and not spec-compliant; it also muddies the repo-owned-vs-shipped boundary. The README (link-out) is the portable layer instead.
- **Free-form, non-Diátaxis docs.** Rejected, per ADR-0001's original reasoning (mixing types is the dominant cause of bad docs).

## References

- [Diátaxis — complex hierarchies](https://diataxis.fr/complex-hierarchies/)
- ADR-0001 (the guides sub-decision this amends); RFC-0031 (package-manager posture); `scope_rails.py:87` (the seeds-rail constraint).

## Errata

The Decision's implementation note says to amend `CONVENTIONS.md §5c`. In
practice `docs/CONVENTIONS.md` is **projected** from the adopter seed
`packs/core/seeds/docs/CONVENTIONS.md` (it sits in `self_host.py`'s
`PROJECTED_README_OVERRIDES`), so `make build-self` overwrites any direct
edit, and whatever §5c says **ships to adopters** — whose scaffold this ADR
keeps by-quadrant. Amending §5c to the per-pack hierarchy would contradict
this ADR's own "seed scaffold unchanged" boundary.

**Resolution (carried by the guide-migration PR):** §5c stays by-quadrant
(adopter-correct); this repo's per-pack guides convention is recorded in
`AGENTS.local.md` instead. The other half of the instruction *was* done — the
`new-guide` skill is now **layout-aware** (writes per-pack when the repo is
organized that way, by-quadrant otherwise), so it serves both the catalogue
and single-product adopters. Ratified on merge by the ADR's decider.
