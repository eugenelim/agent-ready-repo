# ADR-0052: Nine experience-pack skill renames — live surface renamed, frozen governance bridged, no install-time alias

- **Status:** Accepted
- **Date:** 2026-07-19
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0066 (driving RFC — Decision 7 specifies all 9 renames), ADR-0038 (the rename-without-alias precedent this ADR follows exactly), ADR-0024 (agnosticism guardrails, unchanged by this rename)

## Decision summary

- **Decision:** We rename nine experience-pack skills from the invented pack-scoped slugs used in v0.5.x to the canonical industry names used by practitioners — renaming the live surface and bridging frozen governance, with no install-time alias.
- **Because:** The invented slugs (`map-customer-journey`, `aesthetic-direction`, `design-critique`, etc.) described the artifact produced; the canonical names (`journey-mapping`, `creative-direction`, `design-review`, etc.) name the discipline and match the vocabulary practitioners, hiring managers, and industry standards already use. Renaming at 0.6.0 costs less than renaming post-stable.
- **Applies to:** the nine skill directories and all live surfaces that carry their names (SKILL.md frontmatter, SKILL.md bodies, evals, templates, guides, marketing site, cross-pack references).
- **Tradeoff accepted:** adopters who reference old skill slugs by name in their own prompts or workflows must update to the canonical names (no alias mechanism exists). The user-scope install window keeps the migration cost low.
- **Revisit if:** a skill-alias mechanism is ever designed (deferred, none planned) — a future rename could then smooth the transition tail.

## Context

RFC-0066 (surface-genre uplift, experience pack 0.6.0) identified nine skills whose invented slugs had drifted from the canonical vocabulary practitioners use. The pack uses `map-customer-journey` where the discipline says `journey-mapping`; it uses `aesthetic-direction` where the discipline says `creative-direction`; it uses `design-critique` where the discipline says `design-review`. Each invented slug is technically accurate but unfamiliar to a practitioner arriving fresh — they must learn the pack's vocabulary before they can use it, rather than finding the skill they already know under the name they already use.

No skill-alias mechanism exists in this repo (grep-confirmed in RFC-0048). Inventing one is a distribution-mechanism RFC, not in scope here. The rename precedent is ADR-0038 (the `design-craft → experience` pack rename), which renamed the live surface, bridged frozen governance with a new ADR, and accepted the no-alias tradeoff. This ADR follows that precedent exactly.

## The nine renames

| Old slug (v0.5.x and earlier) | New slug (v0.6.0 canonical) | Rationale |
|------------------------------|----------------------------|-----------|
| `map-customer-journey` | `journey-mapping` | Industry standard (NN/g, Patton, Torres). The skill maps; the artifact is a map. |
| `blueprint-service` | `service-blueprint` | Industry standard (NN/g). Artifact-first → discipline-first. |
| `map-screen-flow` | `user-flow` | Industry standard (UX discipline, Shneiderman). The map produces a user flow. |
| `map-internal-process` | `process-mapping` | Industry standard (APQC, BPMN, BABOK). Discipline-first. |
| `aesthetic-direction` | `creative-direction` | Industry standard (art direction discipline). "Creative direction" names the role; "aesthetic direction" named an output. |
| `layout-and-information-architecture` | `information-architecture` | Industry standard (Rosenfeld, Morville). The layout IS the IA; the compound was redundant. |
| `design-critique` | `design-review` | Aligns with the skill's actual mode (structured review with severity ratings, not informal critique). |
| `design-system-foundations` | `design-system` | Industry standard. "-foundations" was a qualifier that added friction without adding meaning. |
| `copy-direction` | `tone-of-voice` | Industry standard (brand/content discipline). "Tone of voice" is the recognized term for brand voice guidelines. |

## Frozen-governance bridge

The following frozen governance documents name old experience-pack skill slugs as historical records. They are **not updated** — their naming is accurate as of the time they were written, and altering frozen governance is out of scope per ADR-0038 precedent. This ADR serves as the bridge: readers encountering old slug names in frozen documents (accepted/rejected RFCs, ADRs with Status: Accepted) should consult this ADR for the mapping.

Frozen documents that name old slugs: RFC-0050 (experience-pack pressure test, 2026-Q2), RFC-0033 (design-craft pack origin, pre-experience), ADR-0038 (pack rename, references old skill names in historical context), `docs/specs/experience-pack-0.5.x/` (frozen spec, if present).

## No alias

No install-time or runtime alias maps old slug names to new slug names. No alias mechanism exists in this repo; inventing one is out of scope. Adopters who name old skill slugs by string in their own prompts must update to the canonical names in this table. The user-scope default and the pre-stable version window keep the migration cost acceptable.
