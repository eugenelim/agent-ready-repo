---
**Feature:** phase4b-product-docs-completion
**Status:** Shipped (the `/guides/<pack>/` `docsUrl` direction at lines 24 and AC7, and line 66's "docsUrl wrong" row, were corrected to `/docs/guides/<pack>/` by [`spec/marketing-docs-link-repair`](../marketing-docs-link-repair/spec.md) on 2026-08-06; [ADR-0055](../../adr/0055-starlight-replaces-mkdocs-for-reference-docs.md), Accepted 2026-07-25, already mounted reference docs there when this spec shipped, so this is a correction of an instruction that was contrary to it — not a supersession of any decision made here. Every decision in this spec stands.)
**Mode:** full (multi-feature, structural/public-interface change — public routes, guide index, cross-pack READMEs)
---

# Phase 4B — Product Documentation Rollout Completion and Catalogue Convergence

## Objective

Close every remaining gap in the Product Documentation contract across all active packs, and converge the shared catalogue surfaces (guide index, guide-author doctrine, pack grouping, machine-fact parity).

Phase 4 shipped READMEs and JOURNEYs for the core workflow packs. Phase 4B retrofits the five remaining packs (product-strategy, frontend-engineering, catalogue-curation, iac-terraform, release-engineering) and fixes the shared convergence gaps the Phase 4 migration matrix left open.

## Boundaries

**In scope:**
- Rewrite `packs/product-strategy/README.md` — replace framework-first entry with strategic-question-led entry
- Rewrite `packs/frontend-engineering/README.md` — add "Start here", common jobs, task-led entry
- Rewrite `packs/catalogue-curation/README.md` — add "Start here", operator-job-led entry, confirmation/permission boundaries, maintainer-vs-adopter distinction
- Rewrite `packs/iac-terraform/README.md` — add "Start here", explicit plan/apply/destructive-action/state/secret boundaries
- Add `## Start here` to `packs/release-engineering/README.md`
- Update `web/src/content/packs/product-strategy.md` — user-job-first tagline and description
- Fix `web/src/content/packs/frontend-engineering.md` `docsUrl` — `/docs/guides/...` → `/guides/frontend-engineering/`
- Update `guides/README.md` — add iac-terraform, product-strategy, catalogue-curation, frontend-engineering to All packs table; update guide-author doctrine to describe metadata-based kinds
- Fix `packs/user-guide-diataxis/pack.toml` lifecycle field (`active` → `deprecated`)
- Bump patch versions for all packs with distributed README changes
- Add `tools/check-guide-index.py` — drift check: active pack missing from guides/README.md All packs table
- Sync plugin metadata after version bumps: `FORCE=1 make build-self`

**Not in scope:**
- Phase 5 deployment-integrity system
- Redesigning the global homepage or documentation shell
- Removing `user-guide-diataxis`
- Rewriting already-conforming packs (architect, atlassian, contracts, core, credential-brokers, desk-research, experience-design, figma, github, governance-extras, linear, monorepo-extras, product-documentation, product-engineering)
- Adding missing guide frontmatter to the 159 migration-warning guides (deferred from Phase 4)
- Adding JOURNEY.md to atomic packs (converters, contracts, figma, github, linear, monorepo-extras)

## Assumptions

1. All Phase 4 packs remain green — pre-flight baseline confirms build-check passed, lint-pack-journeys 11 files valid, pre-pr-catalogue clean.
2. Patch version bumps are appropriate for README-only distributed content changes.
3. `FORCE=1 make build-self` regenerates plugin metadata and marketplace files after version bumps.
4. The guide-author doctrine update in guides/README.md does not change any canonical skill or schema — it corrects the prose description to match the already-shipped Phase 2A metadata model.

**Declined patterns:**
- Tempted to add frontmatter to all 159 migration-warning guides — declining; deferred from Phase 4 and not a blocker for Phase 4B ACs.
- Tempted to add JOURNEY.md to release-engineering (workflow has stages) — declining; the pack is a single-skill pack where the journey is the skill itself; adding a JOURNEY.md would duplicate the skill's own description.
- Tempted to add first-value metadata starter-task/prompt to catalogue-curation, iac-terraform, release-engineering — declining; these are advanced technical packs; level-b is for non-technical first-value workflows.
- Tempted to create a multi-check catalogue audit tool — declining; a lightweight guide-index parity check is sufficient for Phase 4B regression prevention; Phase 5 handles full attestation.

## Residual Migration Matrix

| Pack | Lifecycle | Archetype | JOURNEY? | README issue | Pack page issue | Phase 4B action |
|------|-----------|-----------|----------|--------------|-----------------|-----------------|
| architect | active | C. Analysis | ✓ exists | ✓ Start here, outcome-led | OK | Verified complete |
| atlassian | active | B. Integration | ✓ exists | ✓ Outcome-led, boundary visible | OK | Verified complete |
| catalogue-curation | active | F. Platform | no — correct | ✗ No Start here; skill table leads | OK | Lane C rewrite |
| contracts | active | E. Atomic | no — correct | ✓ Start here, outcome-led | OK | Verified complete |
| converters | active | E. Atomic | no — correct | ✓ Outcome-led (Phase 4 rewrite) | OK | Verified complete |
| core | active | A. Workflow | ✓ exists | ✓ Start here, outcome-led | OK | Verified complete |
| credential-brokers | active | F. Platform | no — correct | ✓ Platform description | OK | Verified complete |
| desk-research | active | C. Analysis | ✓ exists | ✓ Start here, outcome-led | OK | Verified complete |
| experience-design | active | C. Analysis | ✓ exists | ✓ Start here, outcome-led | OK | Verified complete |
| figma | active | B. Integration | no — correct | ✓ Outcome-led | OK | Verified complete |
| frontend-engineering | active | D. Engineering | no — correct | ✗ No Start here; skills list early | docsUrl wrong | Lane B rewrite |
| github | active | B. Integration | no — correct | OK (1-skill pack) | OK | Verified complete |
| governance-extras | active | D. Engineering | ✓ exists | ✓ Start here, outcome-led | OK | Verified complete |
| iac-terraform | active | D. Engineering | ✓ exists | ✗ No Start here; skills table leads | OK | Lane B rewrite |
| linear | active | B. Integration | no — correct | OK (3-skill pack) | OK | Verified complete |
| monorepo-extras | active | E. Atomic | no — correct | ✓ Outcome-led | OK | Verified complete |
| product-documentation | active | F. Platform | ✓ exists | ✓ Outcome-led, Get started visible | OK | Verified complete |
| product-engineering | active | A. Workflow | ✓ exists | ✓ Start here, outcome-led | OK | Verified complete |
| product-strategy | active | C. Analysis | ✓ exists | ✗ Framework-first; skill inventory leads | Framework-first tagline | Lane A rewrite |
| release-engineering | active | D. Engineering | ✓ exists | ✗ Architecture-first; no Start here | OK | Lane B small fix |
| user-guide-diataxis | deprecated (README) / active (pack.toml) | — | no | ✓ Shows deprecated notice | — | Lane E: fix lifecycle |

## Acceptance Criteria

- [x] AC0: Pre-flight baseline — build-check green, lint-pack-journeys 11 files valid, pre-pr-catalogue clean (confirmed)
- [x] AC1: `packs/product-strategy/README.md` leads with strategic questions, shows decision/artifact before skill list
- [x] AC2: `packs/frontend-engineering/README.md` has "Start here", common jobs, natural first request, side-effect/approval/rollback visible
- [x] AC3: `packs/catalogue-curation/README.md` has "Start here", operator-job-led, confirms local-only, distinguishes maintainer from adopter
- [x] AC4: `packs/iac-terraform/README.md` has "Start here", plan/apply boundary explicit, destructive-action boundary visible
- [x] AC5: `packs/release-engineering/README.md` has "Start here" with natural first request
- [x] AC6: `web/src/content/packs/product-strategy.md` tagline and description are user-job-first
- [x] AC7: `web/src/content/packs/frontend-engineering.md` docsUrl is `/guides/frontend-engineering/`
- [x] AC8: `guides/README.md` All packs table includes iac-terraform, product-strategy, catalogue-curation, frontend-engineering
- [x] AC9: `guides/README.md` guide-author doctrine section describes `kind` as frontmatter metadata, flat source paths, no mandatory quadrant folders
- [x] AC10: `packs/user-guide-diataxis/pack.toml` — no schema `lifecycle` field exists; deprecated status already expressed via `display_name = "User Guide (Diátaxis) — Deprecated"` and `keywords: ["deprecated"]`; no change required
- [x] AC11: Pack versions bumped for all packs with distributed README changes; plugin metadata synchronized via `FORCE=1 make build-self`
- [x] AC12: `tools/check-guide-index.py` exits 0 on current repo; exits 1 when an active pack is absent from guides/README.md All packs table
- [x] AC13: `SKIP_SAST=1 make build-check` passes after all changes
- [x] AC14: `python3 tools/lint-pack-journeys.py` exits 0 (11 files still valid)
- [x] AC15: `python3 tools/validate_guides.py guides/` exits with 0 errors
- [x] AC16: `python3 tools/pre-pr-catalogue.py` passes
- [x] AC17: Cold-read verified for all 5 residual packs — product-strategy, frontend-engineering, catalogue-curation, iac-terraform, release-engineering all answer the 7 cold-read questions
- [x] AC18: adversarial-reviewer returns `Clean — ready to commit.`

## Testing Strategy

Goal-based verification for each README change (cold-read: first request visible within 120 words).
Goal-based for drift tool (exits 0 on clean, exits 1 when pack missing).
Mechanical gates:
```bash
python3 tools/validate_guides.py guides/          # AC15: 0 errors
python3 tools/lint-pack-journeys.py               # AC14: 0 errors
python3 tools/pre-pr-catalogue.py                  # AC16: all green
python3 tools/check-guide-index.py                # AC12: exits 0
SKIP_SAST=1 make build-check                       # AC13: exits 0
```
