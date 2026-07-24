# Plan: product-engineering-shaping-doctrine

- **Spec:** [`spec.md`](spec.md)
- **Approach:** Sequential goal-based tasks; all verification is goal-based check. No TDD tasks.

## Declined patterns

- Tempted to update all 205 voice-and-microcopy occurrences including frozen historical docs — declining; ADR-0038 bridges frozen governance, does not rewrite it.
- Tempted to add thin-slice to ALL 15 PE skills — declining; only place-bet (the commitment gate) needs it as a required field.
- Tempted to create a new skill for post-launch learning contracts — declining; it is a how-to guide, not a new skill.
- Tempted to add place-bet to `[pack.evals]` — declining; requires calibration evidence; spec says Ask first.
- Tempted to also add diverge-solutions anti-patterns (minimum meaningful options) — declining for now; AC covers only evals weak fixtures.

## Tasks

### Task 1: Author spec + plan + update docs/specs/README.md
- **Depends on:** none
- **Verification:** goal-based check
- **Done when:** spec.md and plan.md exist; docs/specs/README.md lists this spec in the active section
- **Approach:** Write spec.md + plan.md; add entry to README.md

---

### Task 2: Rename voice-and-microcopy → ux-writing (PE pack internal)
- **Depends on:** Task 1
- **Verification:** goal-based check
- **Done when:** `ux-writing/` directory exists with SKILL.md + evals; old directory gone; `grep -r "voice-and-microcopy" packs/product-engineering/.apm/skills/ux-writing/` returns 0 (within the new skill dir itself)
- **Approach:**
  1. `cp -r packs/product-engineering/.apm/skills/voice-and-microcopy/ packs/product-engineering/.apm/skills/ux-writing/`
  2. Update SKILL.md frontmatter `name: ux-writing`; update self-references inside SKILL.md body
  3. Update `evals/evals.json` `skill_name` field
  4. Add 5 weak-fixture entries to `eval_queries.json` (copy-boundary cases + total `should_trigger: false` ≥ 14)
  5. `rm -rf packs/product-engineering/.apm/skills/voice-and-microcopy/`

---

### Task 3: Update PE pack references to ux-writing
- **Depends on:** Task 2
- **Verification:** goal-based check
- **Done when:** `grep -r "voice-and-microcopy" packs/product-engineering/ --include="*.md" --include="*.toml" --include="*.json"` returns 0
- **Files:** pack.toml (version 0.13.0 + evals list + description), README.md, discovery-loop SKILL.md, plugin.json

---

### Task 4: Update XD pack cross-references to ux-writing
- **Depends on:** Task 2
- **Verification:** goal-based check
- **Done when:** `grep -r "voice-and-microcopy" packs/experience-design/ --include="*.md"` returns 0
- **Files:** tone-of-voice SKILL.md (3 refs), user-flow SKILL.md (2 refs),
  user-flow/assets/screen-brief-template.md (1),
  user-flow/assets/design-tool-handover-template.md (1),
  user-flow/references/screen-flow.md (1),
  design-review/references/quality-floor.md (1),
  content-design SKILL.md (2), experience-design README.md (2)

---

### Task 5: Update other operational cross-references to ux-writing
- **Depends on:** Task 2
- **Verification:** goal-based check
- **Done when:** `grep -r "voice-and-microcopy" packs/product-strategy/ docs/guides/ --include="*.md"` returns 0; `grep "voice-and-microcopy" web/src/content/journeys/discovery.md web/src/components/marketing/PackCatalogue.astro` returns 0
- **Files:** packs/product-strategy/define-content-strategy/SKILL.md, docs/guides/README.md,
  docs/guides/experience-design/reference/experience-design.md,
  docs/guides/product-engineering/README.md,
  docs/guides/product-engineering/how-to/write-product-microcopy.md,
  web/src/content/journeys/discovery.md,
  web/src/components/marketing/PackCatalogue.astro

---

### Task 6: Update place-bet SKILL.md with new required fields
- **Depends on:** Task 1
- **Verification:** goal-based check
- **Done when:** betting table in SKILL.md includes all four new fields with required markers; Anti-patterns section names gate failures by outcome only
- **Approach:** Add four new fields to step 3 of the procedure (thin-slice, first-success-event, specialist-lenses, learning-contract); add three anti-pattern entries; update bet.md frontmatter field list; ensure no "step N" internal ID in anti-patterns

---

### Task 7: Update de-risk-intent SKILL.md with evidence ladder
- **Depends on:** Task 1
- **Verification:** goal-based check
- **Done when:** validation_hook code block includes `evidence_level` field; step 2 references "lowest evidence level" in assumption selection
- **Approach:** Extend the `validation_hook:` YAML block; update step 2 prose

---

### Task 8: Update diverge-solutions evals with weak fixtures — DEFERRED
- **Depends on:** Task 1
- **Verification:** goal-based check (deferred)
- **Done when:** N/A — deferred: `diverge-solutions` has no `evals/` directory; adding
  one and wiring it to `[pack.evals]` requires an Ask-first review per spec Boundaries.
  Fixture work deferred to a follow-on spec.
- **Approach:** DEFERRED — adding `diverge-solutions` evals is Ask-first (Boundary)

---

### Task 9: Update web pack page
- **Depends on:** Task 3
- **Verification:** goal-based check
- **Done when:** `web/src/content/packs/product-engineering.md` lists `ux-writing` in skills array; description updated to jobs-first prose
- **Approach:** Replace voice-and-microcopy with ux-writing in skills list; rewrite description prose

---

### Task 10: Create PE journey page
- **Depends on:** Tasks 6, 7
- **Verification:** goal-based check
- **Done when:** `web/src/content/journeys/product-engineering.md` exists with correct format; thin-slice + learning-contract steps visible; whatChanges references Digital Experience Contract
- **Approach:** Author following product-strategy.md format; include doctrine fields in journey stages

---

### Task 11: Update how-to guides
- **Depends on:** Tasks 6, 7
- **Verification:** goal-based check
- **Done when:** `place-a-bet.md` has `## How to define a thin slice`; `write-a-post-launch-learning-contract.md` exists
- **Approach:** Add thin-slice section to place-a-bet.md; create learning-contract how-to

---

### Task 12: Update workspace.toml and changelog
- **Depends on:** all above
- **Verification:** goal-based check
- **Done when:** spec in shipped list; `digital-experience-contract-pe-journey-xref` removed from backlog.open; changelog has [Unreleased] entry
- **Approach:** Move spec from queue to shipped; remove closed backlog item; add changelog entry

---

### Task 13: Run gates and final AC4 grep
- **Depends on:** Tasks 2–12
- **Verification:** goal-based check
- **Done when:** `make build-check` exits 0; `python3 tools/check-contract-drift.py --root .` exits 0; AC4 grep returns 0
- **Approach:** Run build-check; run drift check; run grep verification

## Changelog

_First version — no prior changelog for this spec._
