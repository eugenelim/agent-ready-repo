# ADR-0010: A normative `reference.md` is the repo's golden path — template-instantiated on demand, never a core seed, populated by repo context

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-01
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0020 (reference-architecture foundation — the accepted proposal these decisions record); RFC-0019 + ADR-0009 (the LLD lives in the plan and reads `reference.md` when present — the *consumer* of what this ADR's artifact provides); RFC-0021 (greenfield inception — its foundation step authors the first `reference.md`); RFCs 0001–0003 (the pack-catalogue model opt-in stack packs extend); ADR-0008 (the prior "agnostic, convention-first core seam" precedent); `reference-architecture` spec; `docs/architecture/overview.md`; the `adapt-to-project` skill (Class-3 discovery, extended for harvest); `docs/CHARTER.md` §Principles

## Context

`core` (always installed) ships a **descriptive** architecture document —
`docs/architecture/overview.md`, the code map, in the spirit of matklad's
`ARCHITECTURE.md` ("only specify things unlikely to frequently change"). RFC-0019
(recorded in ADR-0009) then gave every feature a low-level design that lives in
the plan, with Decision 9 having that LLD **read `docs/architecture/reference.md`
when present**.

That consumer was shipped against an artifact that did not exist. The forces:

- **No normative anchor.** `overview.md` answers *"where is the thing that does
  X"*; nothing answers *"what golden path must a design conform to"* — the stack,
  the internal framework building blocks, the component stereotypes, the
  cross-cutting standards (security, observability, resilience defaults). Without
  it, the LLD re-derives the stack on every feature and the org's golden path has
  no home.
- **Core must stay stack-neutral** (CHARTER Principle 1). The foundation cannot
  bake React/Spring/etc. into universal core; a non-matching adopter would carry
  rot.
- **A pre-placed core seed would guarantee a collision.** If `core` seeded
  `reference.md`, every opt-in stack pack that shipped its own would collide at
  the bundler — `self_host.py` `_project_seeds` errors on differing-content seed
  collision; the install path writes a `.upstream` companion. The bundler has
  **no pack-override field**, by design.
- **Three repo contexts must each reach a populated foundation** — greenfield
  (no code to read yet), brownfield (existing code to mine), enterprise (a
  reusable stack the org already standardized on).
- **Reuse over new mechanism.** The repo already has a template-instantiation
  pattern (`new-spec`'s `spec.md`/`plan.md`), a discovery engine with a path-jail
  and propose-and-confirm (`adapt-to-project` Class-3), and an opt-in pack model
  (`atlassian`, `converters`).

## Decision

> We will add a **normative** reference-architecture document —
> `docs/architecture/reference.md`, the repo's golden path that low-level designs
> *conform to* as **steering** — kept distinct from the **descriptive**
> `overview.md`; **instantiated on demand from an arc42-shaped template asset, not
> pre-placed as a core seed**; populated by repo context (greenfield authoring,
> brownfield harvest, or stack-pack pre-bake); with brownfield harvest delivered
> by **extending `adapt-to-project` Class-3 discovery**, and stack specifics
> carried **only by opt-in stack packs**.

Specifically:

1. **Artifact + name (RFC-0020 D1).** `reference.md` is a normative doc distinct
   from `overview.md`. (`foundation.md` was the considered fallback name.)
2. **Sections (D2).** Four arc42 sections — Constraints (§2), Solution strategy
   (§4), Building-block view / component catalogue (§5), Crosscutting concepts /
   standards (§8) — not invented headings.
3. **Distribution (D3).** Generated on demand from a template asset (the
   `spec.md`/`plan.md` pattern), **not** a pre-placed core seed. `overview.md`
   stays a core seed because it has exactly one producer ever and nothing competes
   to provide it; `reference.md` has multiple potential producers, so pre-seeding
   would make a collision universal rather than a narrow two-producer case.
4. **Population (D4).** By repo context: greenfield authoring (RFC-0021),
   brownfield harvest (`adapt-to-project`, fed by detection), stack-pack pre-bake.
5. **Harvest (D5).** Extend `adapt-to-project` Class-3 discovery to *propose a
   draft* `reference.md` the adopter confirms — not a new harvester skill.
6. **Stack specifics (D6).** Pre-baked by opt-in stack packs (each a downstream
   follow-on clearing the charter bars on its own), never baked into core.

`reference.md` is **steering** — always-applied golden-path context a design
conforms to and a reviewer checks against (the posture `AGENTS.md` already holds
for conventions) — not a reference an LLD optionally consults. The boundary: it
is durable golden-path, not per-feature design (that stays in the plan) and not
live infrastructure state.

## Consequences

**Positive:**

- The LLD (RFC-0019/ADR-0009) gains the org-specific anchor it was already coded
  to read; the stack is curated once and read thereafter, not re-derived per spec.
- A clean descriptive/normative split: `overview.md` (map) and `reference.md`
  (golden path) are siblings under `docs/architecture/`, each with one job.
- Core stays stack-neutral; the collision surface is minimized — the sole-producer
  case has nothing to collide against, so the bundler needs no new override field.
- All three repo contexts reach a populated foundation by reusing existing
  machinery (template instantiation, Class-3 discovery, the pack model).

**Negative:**

- A new template asset to own, an `adapt-to-project` extension to build and test,
  and a stack-pack contract to specify — surface area that must be maintained.
- The foundation can rot if written once and never revisited; the LLD would then
  conform to a lie. Mitigated by its normative, low-churn nature, a named owner,
  and a verification cadence matched to its volatility.
- "Reference architecture" can be misread as a vendor/cloud blueprint;
  `foundation.md` is the fallback name if that reading proves common.

**Neutral / to revisit:**

- The two-producer case (two stack packs, or a stack pack atop an adopter's own
  `reference.md`) routes through the `.upstream` companion + `adapt-to-project`
  merge — the path adopter customization and copier-style updates already use.
- Greenfield authoring is realized by RFC-0021's `init-project`, sequenced
  separately; this decision ships the template that path will consume.
- Whether arc42's four chosen sections are universal enough to hold any adopter's
  golden path is a falsifiable assumption to watch as adopters fill them.

## Alternatives considered

- **Fold the normative content into `overview.md`** — rejected: conflates "where
  things are" with "what to conform to" and violates matklad's descriptive-only
  rule for the code map.
- **Put it in `CHARTER.md` / `CONVENTIONS.md`** — rejected: CHARTER is product
  mission, CONVENTIONS is process; neither is the technical golden path.
- **Ship `reference.md` as a core document seed (parallel to `overview.md`)** —
  rejected: *guarantees* a collision with every stack pack that ships its own,
  forcing a build error or a `.upstream` dance on every install. This is the flaw
  the on-demand template avoids.
- **arc42 vs. C4 vs. invented headings (D2)** — C4 is a visualization model, not a
  normative-standards vocabulary; invented headings are bespoke and re-litigated
  per repo. arc42's four sections map exactly to constraints/stack/components/
  standards.
- **A new harvester skill (D5)** — rejected: duplicates `adapt-to-project`'s
  discovery engine, path-jail, and propose-and-confirm; harvest *is* discovery.
- **Harvest-only or authoring-only population (D4)** — each fails a context:
  harvest-only has nothing to read on greenfield; authoring-only ignores existing
  code and is high-cost on brownfield.
- **Bake the stack into core (D6)** — rejected: violates universality (Principle
  1) and rots for non-matching adopters.

## References

- RFC-0020 — `docs/rfc/0020-reference-architecture-foundation.md` (the accepted
  proposal; Decisions 1–6, §Delivery, §Follow-on artifacts).
- ADR-0009 — `docs/adr/0009-product-brief-layer-and-plan-owned-lld.md` (the LLD
  reads `reference.md` when present — the consumer of this artifact).
- `reference-architecture` spec — `docs/specs/reference-architecture/spec.md` (the
  implementation contract for the producer side).
- [arc42 template](https://arc42.org/overview); [matklad — ARCHITECTURE.md](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html); [GitHub spec-kit](https://github.com/github/spec-kit) (the constitution as a normative anchor).
