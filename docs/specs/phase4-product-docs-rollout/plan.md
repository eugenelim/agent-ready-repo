---
**Feature:** phase4-product-docs-rollout
**Status:** Shipped
---

# Phase 4 — Implementation Plan

## Tasks

### Wave 0 — Pre-flight and guide metadata

**Task 0.1 — Fix guide metadata schema errors in `guides/frontend-engineering/`**
- Depends on: none
- Verification mode: goal-based check (`python3 tools/validate_guides.py guides/frontend-engineering/` — 0 errors)
- Files: `guides/frontend-engineering/README.md`, `how-to/run-an-audit.md`, `reference/frontend-engineering.md`, `tutorials/scaffold-a-component.md`
- Change: `description:` → `summary:`, add `pack: frontend-engineering`, add `kind: <quadrant>` to each article file; remove broken frontmatter from README

**Task 0.2 — Add missing frontmatter to `guides/release-engineering/` files**
- Depends on: none
- Verification mode: goal-based check (`python3 tools/validate_guides.py guides/release-engineering/` — 0 warnings)
- Files: `guides/release-engineering/README.md`, `tutorials/your-first-release.md`, `how-to/run-a-release.md`, `reference/release-readiness-record.md`, `explanation/the-release-loop.md`
- Change: add `title`, `summary`, `pack: release-engineering`, `kind: <quadrant>` to each file

---

### Wave 1 — Core workflow packs (JOURNEY.md + cleanup)

**Task 1.1 — Create `packs/core/JOURNEY.md`; delete hand-authored `web/src/content/journeys/core.md`**
- Depends on: none
- Verification mode: goal-based check (`python3 tools/lint-pack-journeys.py` exits 0)

**Task 1.2 — Create `packs/product-engineering/JOURNEY.md` (journey_id: product-engineering); delete `discovery.md`; update pack page journeyUrl**
- Depends on: none
- Verification mode: goal-based check (lint-pack-journeys exits 0; pack page journeyUrl points to /journeys/product-engineering/)

**Task 1.3 — Create `packs/experience-design/JOURNEY.md`; delete hand-authored experience-design.md**
- Depends on: none
- Verification mode: goal-based check (lint-pack-journeys exits 0)

**Task 1.4 — Create `packs/governance-extras/JOURNEY.md`; delete hand-authored governance-extras.md**
- Depends on: none
- Verification mode: goal-based check (lint-pack-journeys exits 0)

**Task 1.5 — Create `packs/architect/JOURNEY.md`; delete hand-authored architect.md**
- Depends on: none
- Verification mode: goal-based check (lint-pack-journeys exits 0)

**Task 1.6 — Create `packs/desk-research/JOURNEY.md`; delete hand-authored desk-research.md**
- Depends on: none
- Verification mode: goal-based check (lint-pack-journeys exits 0)

**Task 1.7 — Create `packs/product-strategy/JOURNEY.md`; delete hand-authored product-strategy.md**
- Depends on: none
- Verification mode: goal-based check (lint-pack-journeys exits 0)

**Task 1.8 — Create `packs/release-engineering/JOURNEY.md` (journey_id: release-engineering); delete `release.md`; update pack page journeyUrl**
- Depends on: none
- Verification mode: goal-based check (lint-pack-journeys exits 0; pack page journeyUrl points to /journeys/release-engineering/)

---

### Wave 2 — Engineering packs and READMEs

**Task 2.1 — Create `packs/iac-terraform/JOURNEY.md`; delete hand-authored iac-terraform.md**
- Depends on: none
- Verification mode: goal-based check (lint-pack-journeys exits 0)

**Task 2.2 — Rewrite `packs/converters/README.md` outcome-led**
- Depends on: none
- Verification mode: manual — first natural request visible in first sentence

**Task 2.3 — Rewrite `packs/frontend-engineering/README.md` outcome-led**
- Depends on: none
- Verification mode: manual — first natural request visible in first sentence

---

### Wave 3 — Site component updates

**Task 3.1 — Update hardcoded journey links in `PackCatalogue.astro` and `ThreeLoops.astro`**
- Depends on: 1.2, 1.8 (discovery.md and release.md must be deleted first)
- Verification mode: goal-based check (no 404s at `/journeys/discovery/` or `/journeys/release/`)

---

### Gate verification tasks (depend on all waves)

**Task G.1 — Run `validate_guides.py` — 0 errors**
- Depends on: 0.1, 0.2
- Verification mode: goal-based check (exit 0)

**Task G.2 — Run `lint-pack-journeys.py` — all valid**
- Depends on: 1.1–1.8, 2.1
- Verification mode: goal-based check (exit 0)

**Task G.3 — Run `build-site.py --journeys-only` — exit 0**
- Depends on: G.2, all JOURNEY.md files present
- Verification mode: goal-based check (exit 0, 11 journeys synced)

**Task G.4 — Run `SKIP_SAST=1 make build-check` — exit 0**
- Depends on: G.1, G.2, G.3, loop-cohort approve-plan
- Verification mode: goal-based check (exit 0)
