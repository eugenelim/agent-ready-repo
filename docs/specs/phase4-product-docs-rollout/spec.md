---
**Feature:** phase4-product-docs-rollout
**Status:** Shipped
**Mode:** full (multi-feature, structural/public-interface, unfamiliar territory)
---

# Phase 4 — Catalogue-wide Product Documentation Rollout

## Objective

Apply the Product Documentation authoring model proven by the Atlassian Phase 3
pilot to every remaining active pack. Every active pack must have a useful
outcome-led README, a canonical `JOURNEY.md` where the first-value experience
genuinely spans multiple stages, valid guide metadata, and accurate pack pages.

## Boundaries

**In scope:**
- Fixing guide metadata schema errors and warnings in `guides/frontend-engineering/` and `guides/release-engineering/`
- Creating canonical `JOURNEY.md` in each pack that warrants one (multi-stage workflow)
- Deleting the pre-Phase-3 hand-authored journey pages in `web/src/content/journeys/` that are replaced by generated ones
- Running `build-site.py --journeys-only` to regenerate journey pages with `generated: true`
- Improving outcome-led READMEs for `converters` and `frontend-engineering`
- Updating `web/src/content/packs/product-engineering.md` journeyUrl and `web/src/content/packs/release-engineering.md` journeyUrl to match canonical journey_ids
- Full guide validation and build-check confirmation

**Not in scope:**
- Redesigning the global homepage or site shell
- Changing pack behavior or skill content
- Adding frontmatter to the 163 guide files that currently show migration warnings (deferred)
- Migrating `contracts`, `figma`, `monorepo-extras`, `converters`, `credential-brokers`, `linear`, `github`, `user-guide-diataxis`, `catalogue-curation` journey pages (assessed as not needing JOURNEY.md — see migration matrix below)
- Publishing, tagging, or releasing externally

## Assumptions

1. The hand-authored files in `web/src/content/journeys/` are compatible with the `JOURNEY.md` schema; only `journey_id`, `start_state`, and `end_state` fields need to be added.
2. The `build-site.py --journeys-only` generator will correctly replace hand-authored files with `generated: true` files when the `journey_id` matches.
3. `lint-pack-journeys.py` validates JOURNEY.md files — all new files must pass.
4. Improving guide frontmatter in `guides/frontend-engineering/` requires changing `description:` → `summary:` and adding `pack:` and `kind:`.

**Declined patterns:**
- Tempted to add frontmatter to all 163 guide files with migration warnings — declining; this is a separate migration effort; the current warnings don't block Phase 4 ACs.
- Tempted to delete journey pages for atomic packs (contracts, figma, converters, etc.) — declining for now; these hand-authored pages serve users and removing them breaks journeyUrl links in pack pages; schedule as Wave 4 cleanup after all JOURNEY.md files land.
- Tempted to rewrite all pack READMEs to match the exact atlassian README structure — declining; most READMEs are already outcome-led; fixing only the inventory-first ones.

## Catalogue Migration Matrix

| Pack | Status | Archetype | JOURNEY.md? | Rationale | README action | Wave |
|------|--------|-----------|-------------|-----------|---------------|------|
| _example | excluded | - | n/a | Internal only | none | - |
| architect | active | C. Analysis | create | Design→review: 2 stages, 2 human gates, output passes between skills | verify ok | 1 |
| atlassian | done ✓ | B. Integration | exists ✓ | Phase 3 pilot complete | done ✓ | done |
| catalogue-curation | active | F. Platform | no | 4 independent catalogue operations; no user sequence | verify ok | 3 |
| contracts | active | E. Atomic | no | 2 independent contract skills; no sequential dependency | verify ok | 3 |
| converters | active | E. Atomic | no | 8 independent format conversion utilities; no user sequence | rewrite: outcome-led | 2 |
| core | active | A. Workflow | create | work-loop: 5 stages (orient→brief→plan→execute→merge), sequential, 2 human gates | verify ok | 1 |
| credential-brokers | active | F. Platform | no | Setup flow; not a multi-stage user workflow | verify ok | 3 |
| desk-research | active | C. Analysis | create | Project mode has phases (start→check→digest→synthesize); output passes between stages | verify ok | 1 |
| experience-design | active | C. Analysis | create | Design thread: journey→screens→craft→review; sequential, 3 human gates | verify ok | 1 |
| figma | active | B. Integration | no | Single atomic skill; reads only | verify ok | 3 |
| frontend-engineering | active | D. Engineering | no | 9 independent atomic craft skills; each is independently invoked | rewrite: outcome-led | 2 |
| github | active | B. Integration | no | 1 skill | verify ok | 3 |
| governance-extras | active | D. Engineering | create | RFC lifecycle: Draft→Open→Accept/Reject; multi-stage, 3 human gates | verify ok | 1 |
| iac-terraform | active | D. Engineering | create | generate→reconcile: 7 stages (0–6), 5 human gates (G-governance, G-plan, G4, G5, drift gate) | verify ok | 2 |
| linear | active | B. Integration | no | Intake+sync are separate operations | verify ok | 3 |
| monorepo-extras | active | E. Atomic | no | 1 skill | verify ok | 3 |
| product-documentation | done ✓ | F. Platform | exists ✓ | Already done | done ✓ | done |
| product-engineering | active | A. Workflow | create | discovery-loop: 6 stages, 4 human gates (G0, G1.5, G2, G3); shipped as product-engineering (was "discovery") | verify ok | 1 |
| product-strategy | active | C. Analysis | create | Strategy workflow: 3 artifact stages, human approvals | verify ok | 1 |
| release-engineering | active | D. Engineering | create | Release loop: deploy→verify→converge→G5; sequential, 1 human gate (currently "release") | add guide frontmatter | 1 |
| user-guide-diataxis | deprecated | - | no | Deprecated compatibility pack | none | - |

## Acceptance Criteria

- [x] AC1: Pre-flight gate complete — build-check green, lint-pack-journeys green, Atlassian pilot confirmed green
- [x] AC2: `guides/frontend-engineering/` guide files have valid metadata (no schema errors in validate_guides.py)
- [x] AC3: `guides/release-engineering/` guide files have frontmatter (no migration warnings for these files)
- [x] AC4: `packs/core/JOURNEY.md` created; `web/src/content/journeys/core.md` regenerated with `generated: true`; `lint-pack-journeys.py` exits 0
- [x] AC5: `packs/product-engineering/JOURNEY.md` created with `journey_id: product-engineering`; hand-authored `discovery.md` deleted; pack page `journeyUrl` updated; `lint-pack-journeys.py` exits 0
- [x] AC6: `packs/experience-design/JOURNEY.md` created; `lint-pack-journeys.py` exits 0
- [x] AC7: `packs/governance-extras/JOURNEY.md` created; `lint-pack-journeys.py` exits 0
- [x] AC8: `packs/architect/JOURNEY.md` created; `lint-pack-journeys.py` exits 0
- [x] AC9: `packs/desk-research/JOURNEY.md` created; `lint-pack-journeys.py` exits 0
- [x] AC10: `packs/product-strategy/JOURNEY.md` created; `lint-pack-journeys.py` exits 0
- [x] AC11: `packs/release-engineering/JOURNEY.md` created with `journey_id: release-engineering`; hand-authored `release.md` deleted; pack page `journeyUrl` updated; `lint-pack-journeys.py` exits 0
- [x] AC12: `packs/iac-terraform/JOURNEY.md` created; `lint-pack-journeys.py` exits 0
- [x] AC13: `packs/converters/README.md` rewritten to lead with outcome (natural first request within 120 words)
- [x] AC14: `packs/frontend-engineering/README.md` rewritten to lead with outcome (natural first request within 120 words)
- [x] AC15: `validate_guides.py guides/` exits with 0 errors (warnings for missing frontmatter are acceptable — deferred migration)
- [x] AC16: `lint-pack-journeys.py` exits 0 with all JOURNEY.md files valid
- [x] AC17: `python3 tools/build-site.py --journeys-only` exits 0 with no dual-ownership errors
- [x] AC18: `SKIP_SAST=1 make build-check` exits 0

## Testing Strategy

Goal-based verification:

```bash
python3 tools/validate_guides.py guides/  # AC15: 0 errors
python3 tools/lint-pack-journeys.py        # AC16: exits 0
python3 tools/build-site.py --journeys-only  # AC17: exits 0
SKIP_SAST=1 make build-check               # AC18: exits 0
```

Cold-read check: first natural request visible within 120 words on core, product-engineering, and the 6 new JOURNEY.md packs.
