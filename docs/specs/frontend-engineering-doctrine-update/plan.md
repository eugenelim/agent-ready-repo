# Plan: frontend-engineering-doctrine-update

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> note why in the changelog at the bottom.

## Approach

Restructure `packs/core/.apm/skills/frontend-engineering/SKILL.md` to prepend a mode-selection preamble and add four `### Mode: <mode>` conditional sections, then expand the existing state matrix to 18 states (6 existing + 4 from XD quality-floor + 8 new), update the WCAG baseline declaration to 2.2 AA (reword compliance line carefully — see T1 approach step 9), and add CWV targets, asset budgets, brownfield inspection checklist, evidence manifest, page/screen contract, and multi-surface shell contract. All existing craft rules, GATES, and anti-patterns remain; hard-coded state-count enumerations inside craft rules (visual-QA checklist, red flags) are generalized to reference the 18-state matrix. Five companion changes ship in the same PR: two new guide files (how-to, reference), two web page updates (journey, pack), packs/core/README.md update, and a pack version bump.

## Constraints

- RFC-0071 D5: four modes in one SKILL.md, not separate skills
- RFC-0071 D9: minor version bump per doctrine spec
- `digital-experience-contract.md` must stay byte-identical across four pack copies (no changes to that file in this spec)
- No new dependency; no new top-level directory

## Construction tests

**Integration tests:** none beyond per-task goal-based checks.

**Manual verification (AC13):** cold read of SKILL.md's verify mode section as a practitioner — confirm it explicitly references the full GATES suite.

**Manual QA (AC15–AC17):** cold read of the two new guides; check journey page and pack page describe the new features coherently.

## Design (LLD)

### Component / module decomposition

Additions to SKILL.md structure:

1. **Mode-selection preamble** (new H2 section before PLAN phase): four-row table with activation condition.
2. **`### Mode: create`** — page/screen contract (12 fields) + shared pre-flight reference.
3. **`### Mode: retrofit`** — brownfield inspection checklist (6 items) + shared pre-flight + evidence manifest.
4. **`### Mode: audit`** — audit report against 18 states/a11y/CWV. Evidence manifest records findings.
5. **`### Mode: verify`** — full GATES suite + evidence manifest + 18-state coverage confirmation.
6. **18-state matrix expansion** — 6 + 4 + 8 = 18.
7. **WCAG 2.2 AA** — updated baseline declaration; legal-compliance line reworded accurately; tooling ceiling annotated.
8. **Baseline Widely Available** — browser policy added.
9. **CWV targets + asset budgets** (7 categories).
10. **Evidence manifest** (11 fields).
11. **Conditional public-surface guidance** (5 items).
12. **Multi-surface shell contract** — shared tokens, navigation patterns, terminology.
13. **Craft-rule generalization** — visual-QA checklist and red flags updated to reference 18-state matrix, not hard-coded 6/4 subsets.

### Quality attributes (NFRs)

- All existing SKILL.md content preserved (no deletion, only generalization of hard-coded state counts)
- No "WCAG 2.1 AA" standalone baseline claim remains
- `digital-experience-contract.md` byte-identical after changes

## Tasks

### T1: Add four-mode structure and expand state matrix in SKILL.md

**Depends on:** none
**Verification mode:** goal-based check (plus manual QA for AC13)

**Touches:** `packs/core/.apm/skills/frontend-engineering/SKILL.md`

**Tests:**

*Mode structure (AC1–AC4):*
- `grep -c "### Mode:" packs/core/.apm/skills/frontend-engineering/SKILL.md` returns 4

*Page/screen contract fields (AC5) — all 12 named:*
- `grep "target user" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "primary job" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "primary action" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "expected result" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "next action" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "first-screen content" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "product proof" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "read/write consequence" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "critical states" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "responsive behavior" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "a11y requirements" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "measurement event" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0

*Brownfield inspection checklist (AC6) — all 6 items named:*
- `grep "what-to-preserve" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "duplicated-systems" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "hard-coded values" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "a11y-debt" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "responsive-debt" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "visual-regression-risk" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0

*WCAG update (AC7):*
- `grep "WCAG 2.2 AA" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep -c "WCAG 2.1 AA" packs/core/.apm/skills/frontend-engineering/SKILL.md` returns 0 (no standalone "WCAG 2.1 AA" remains; the legal-compliance line uses different phrasing)
- `grep "exceeds the WCAG 2.1 minimum" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0 (new legal-compliance line present)
- `grep "2.4.11" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0 (2.2-only SC noted)
- `grep "2.5.8" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0 (2.2-only SC noted)

*Browser policy (AC8):*
- `grep "Baseline Widely Available" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0

*CWV targets with literal values (AC9):*
- `grep "2.5s" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep -E "INP.*200\.?ms|200\.?ms.*INP" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep -E "CLS.*0\.1|0\.1.*CLS" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "p75" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep -iE "mobile|desktop" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0 (AC9: mobile/desktop CWV dimension per RFC-0071 Area E)

*Asset budget categories (AC10) — all 7 categories:*
- `grep -iE "\bJS\b|JavaScript" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "images" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "fonts" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "third-party" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "hydration" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "route-level" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "long tasks" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0

*State matrix (AC11) — all 18 states present, correct count:*
- `grep "loading" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "success" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "first-run" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "no-results" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "permission/denied" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "offline" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "blocked" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "destructive-confirmation" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "long-content" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "large-data-set" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "high-zoom" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "reduced-motion" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "keyboard-only" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- Count check: `awk 'BEGIN{f=0;c=0} /\| State \|/{f=1;next} f && /^\|---/{next} f && /^\|[^-]/{c++} f && /^[^\|]/{f=0} END{print c}' packs/core/.apm/skills/frontend-engineering/SKILL.md` — verify output is 18 (resets on the next non-blank non-table line; requires the matrix header to remain exactly `| State |`)

*Evidence manifest (AC12) — all 11 fields:*
- `grep "evidence manifest" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "routes" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "viewports" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "browsers" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "screenshots" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "a11y result" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "perf result" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "console/network" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "analytics events" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "known exceptions" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "unverified items" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- The `states` manifest field is verified by manual inspection of the evidence manifest section alongside AC13 — a bare `grep "states"` is tautological against the state matrix

*AC13 (manual QA):* read the `### Mode: verify` section cold — confirm it explicitly names the GATES suite.

*Public-surface guidance (AC14) — all 5 items:*
- `grep "metadata" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "canonical URLs" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "sitemaps" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "structured data" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "search indexing" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0

*Multi-surface shell contract (AC24):*
- `grep "multi-surface" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0
- `grep "shared tokens" packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 0

*Existing content preserved:*
- All existing SKILL.md section headers (aesthetic reference, seed token block, HTML rules, CSS rules, accessibility rules, GATES, anti-patterns, red flags) remain — verify by grepping representative headers from each section
- Craft-rule generalization (AC spec Boundaries): `grep -c "loading / empty / error / partial / content / disabled" packs/core/.apm/skills/frontend-engineering/SKILL.md` returns 0 (hard-coded 6-state string removed from visual-QA checklist)

**Approach:**
1. Read the current SKILL.md in full to understand exact section boundaries
2. Add mode-selection H2 section before the PLAN phase, with a four-row table: create / retrofit / audit / verify
3. Rename "## PLAN phase" to "## PLAN phase (shared pre-flight for all modes)" — it stays shared
4. Add `### Mode: create` section: step 0 = page/screen contract (all 12 fields: target user, primary job, primary action, expected result, next action, first-screen content, product proof, read/write consequence, critical states, responsive behavior, a11y requirements, measurement event); proportional-to-risk guidance
5. Add `### Mode: retrofit` section: brownfield inspection checklist (all 6 items: what-to-preserve, duplicated-systems, hard-coded values, a11y-debt, responsive-debt, visual-regression-risk); evidence manifest required at completion
6. Add `### Mode: audit` section: output format = audit report against 18 states/a11y/CWV; evidence manifest records findings
7. Add `### Mode: verify` section: **explicitly name the full GATES suite** (from the existing GATES phase); generate evidence manifest; confirm all 18 states covered
8. Expand the state matrix table from 6 rows to 18 rows (all 18 states with treatment descriptions) — **keep as one contiguous table under a single `| State |` header** (required for the awk row-count check; do not split into three sub-tables)
9. Update WCAG references: (a) update the general accessibility baseline declaration to "WCAG 2.2 AA"; (b) reword the legal-frameworks compliance line to read "WCAG 2.2 AA is our baseline — it exceeds the WCAG 2.1 minimum currently cited by EU EAA, ADA, and AODA" (preserving factual accuracy about what the legal frameworks cite while declaring our higher target); (c) annotate the tooling-ceiling note (wcag21aa audit tool cap) as a named manual-verification gap for WCAG 2.2-only success criteria: 2.4.11 Focus Appearance and 2.5.8 Target Size Minimum; (d) verify no "WCAG 2.1 AA" string remains as a standalone baseline claim
10. Add Baseline Widely Available browser policy statement
11. Add CWV targets subsection with literal values: LCP ≤2.5s / INP ≤200ms / CLS ≤0.1 at p75; asset budgets section naming all 7 categories (JS, images, fonts, third-party, hydration, route-level, long tasks)
12. Add evidence manifest definition: all 11 required fields — routes, viewports, browsers, states, screenshots, a11y result, perf result, console/network result, analytics events, known exceptions, unverified items
13. Add conditional public-surface guidance subsection: metadata, canonical URLs, sitemaps, structured data, search indexing intent
14. Add multi-surface shell contract section: shared tokens (reference the design system), consistent navigation patterns across surfaces, consistent product terminology
15. Generalize hard-coded state-count enumerations inside craft rules: update the visual-QA checklist (currently lists 6 states) and the red flags section (currently lists 4) to reference "all 18 states in the state matrix" rather than naming a fixed subset

**Done when:** all grep tests above pass; AC13 manual QA passes (verify mode section names GATES suite); `make build-check` exits 0; full SKILL.md read confirms no content loss from existing sections.

---

### T2: Add page/screen contract how-to guide

**Depends on:** T1
**Verification mode:** goal-based check

**Touches:** `docs/guides/core/how-to/page-screen-contract.md`

**Tests:**
- `ls docs/guides/core/how-to/page-screen-contract.md` exits 0
- `grep "target user" docs/guides/core/how-to/page-screen-contract.md` exits 0
- `grep "primary job" docs/guides/core/how-to/page-screen-contract.md` exits 0
- `grep "measurement event" docs/guides/core/how-to/page-screen-contract.md` exits 0
- File contains a section on when the contract is required (proportional application)
- File contains at least two examples

**Approach:**
1. Create `docs/guides/core/how-to/page-screen-contract.md` following the Diátaxis how-to format
2. Structure: when required (proportional to risk/scope, not for trivial components) → the 12 fields (each with a one-line description) → two examples (lightweight: single component; significant: new page)
3. Cross-link to the SKILL.md

**Done when:** file exists and passes the grep tests above.

---

### T3: Add performance targets quick-reference

**Depends on:** T1
**Verification mode:** goal-based check

**Touches:** `docs/guides/core/reference/performance-targets.md`

**Tests:**
- `ls docs/guides/core/reference/performance-targets.md` exits 0
- `grep "2.5s" docs/guides/core/reference/performance-targets.md` exits 0
- `grep "200ms" docs/guides/core/reference/performance-targets.md` exits 0
- `grep "0.1" docs/guides/core/reference/performance-targets.md` exits 0
- `grep "p75" docs/guides/core/reference/performance-targets.md` exits 0
- `grep "hydration" docs/guides/core/reference/performance-targets.md` exits 0
- `grep -iE "mobile|desktop" docs/guides/core/reference/performance-targets.md` exits 0 (mobile/desktop dimension per RFC-0071 Area E)

**Approach:**
1. Create `docs/guides/core/reference/performance-targets.md` as a Diátaxis reference page
2. Structure: CWV targets table (metric / target / percentile; with mobile and desktop columns where field data exists) → asset budget table by surface type
3. Brief contextual note per metric

**Done when:** file exists and passes the grep tests above.

---

### T4: Update web/src/content/journeys/core.md

**Depends on:** T1
**Verification mode:** goal-based check

**Touches:** `web/src/content/journeys/core.md`

**Tests:**
- `grep "page/screen contract" web/src/content/journeys/core.md` exits 0
- `grep "evidence manifest" web/src/content/journeys/core.md` exits 0
- `grep -iE "CWV|Core Web Vitals|performance" web/src/content/journeys/core.md` exits 0

**Approach:**
1. Read the current `web/src/content/journeys/core.md`
2. Update the frontend-engineering workflow description to name page/screen contract, evidence manifest, and CWV gate as identifiable items

**Done when:** grep tests pass.

---

### T5: Update web/src/content/packs/core.md

**Depends on:** T1
**Verification mode:** goal-based check

**Touches:** `web/src/content/packs/core.md`

**Tests:**
- `grep "create" web/src/content/packs/core.md` exits 0
- `grep "retrofit" web/src/content/packs/core.md` exits 0

**Approach:**
1. Read current `web/src/content/packs/core.md`
2. Update the body paragraph to describe frontend-engineering's four-mode structure in jobs-first language

**Done when:** both grep tests pass.

---

### T5b: Update packs/core/README.md (feeds site/ pack page)

**Depends on:** T1
**Verification mode:** goal-based check

**Touches:** `packs/core/README.md`

**Tests:**
- `grep "create" packs/core/README.md` exits 0
- `grep "retrofit" packs/core/README.md` exits 0

**Approach:**
1. Read current `packs/core/README.md`
2. Update the sentence describing `frontend-engineering` to name the four modes concisely

**Done when:** both grep tests pass.

---

### T6: Bump pack version, run drift check, run build-check, update workspace.toml, flip metadata

**Depends on:** T1, T2, T3, T4, T5, T5b
**Verification mode:** goal-based check

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `workspace.toml`, `docs/specs/frontend-engineering-doctrine-update/spec.md`, `docs/specs/frontend-engineering-doctrine-update/plan.md`

**Tests:**
- `grep 'version = "0.14.0"' packs/core/pack.toml` exits 0
- `grep -F '"version": "0.14.0"' packs/core/.claude-plugin/plugin.json` exits 0
- `python3 tools/check-contract-drift.py --root .` exits 0
- `make build-check` exits 0
- `grep -A30 'shipped = \[' workspace.toml | grep "frontend-engineering-doctrine-update"` exits 0 (entry present in shipped block)
- `grep -c 'path = "spec/frontend-engineering-doctrine-update"' workspace.toml` returns 0 (queue object form removed)
- `grep -F '- **Status:** Shipped' docs/specs/frontend-engineering-doctrine-update/spec.md` exits 0
- `grep -F '- **Status:** Done' docs/specs/frontend-engineering-doctrine-update/plan.md` exits 0

**Approach:**
1. Edit `packs/core/pack.toml`: change `version = "0.13.7"` to `version = "0.14.0"`
2. Edit `packs/core/.claude-plugin/plugin.json`: change `"version": "0.13.7"` to `"version": "0.14.0"`
3. Run `make build-self` (with `FORCE=1` if the working tree is dirty: `make build-self FORCE=1`) to reproject SKILL.md to `.claude/skills/frontend-engineering/SKILL.md` and regenerate `marketplace.json`
4. Run `python3 tools/check-contract-drift.py --root .` — confirm exit 0
5. Run `make build-check` — fix any failures before proceeding
6. Edit `workspace.toml`: move the M4 entry from `["ini-003".work].queue` to `["ini-003".work].shipped` as a bare string; verify the queue form is absent
7. Flip `spec.md` Status from `Implementing` to `Shipped`
8. Check all 24 ACs as `[x]` in spec.md
9. Flip `plan.md` Status from `Executing` to `Done`

**Done when:** all eight tests pass; `git status` shows only the expected changes.

## Rollout

Pure documentation/skill restructure + version bump. No infra, no deployment, no migration. Ships in one PR. Reversible — reverts cleanly.

## Risks

- SKILL.md is long and has carefully structured sections; insertion order matters. Risk: accidentally removing or duplicating content. Mitigation: read the full file before editing; confirm all existing section headers remain after the edit.
- The 18 states need accurate treatment guidance. Mitigation: derive from the XD quality-floor.md for the 4 quality-floor states; use workspace.toml M3d descriptions for the 8 new states.
- WCAG 2.1 → 2.2 update: legal-compliance line must be reworded accurately (not blind-replaced). Mitigation: `grep -c "WCAG 2.1 AA"` test in T1 returns 0; approach step 9b spells out the correct new wording.
- Hard-coded state enumerations in craft rules will contradict the 18-state matrix if not generalized. Mitigation: T1 approach step 15 explicitly generalizes them.

## Changelog

- 2026-07-23: initial plan
- 2026-07-23: after adversarial review pass 1 — added T5b; fixed 18-state count; added verification mode per task; tightened T5 grep tests; addressed multi-surface/card-use; updated spec Status to Implementing
- 2026-07-23: after adversarial review pass 2 — added AC24 and T1 step 14 for multi-surface shell contract; expanded T1 greps for all 7 asset budget categories; added completeness greps for AC5/6/11/12/14; added WCAG 2.1 AA negative grep; added 18-state canonical definition to spec
- 2026-07-23: after adversarial review pass 3 — Blocker: added T6 steps 5-7 to flip spec/plan Status and check ACs; Concern 2: reworded WCAG compliance line approach to preserve legal accuracy; Concern 3: fixed awk count (stops on non-table line); Concern 4: expanded AC5/6/12 greps to full sets; Concern 5: reclassified AC13 as manual QA; Concern 6: added T1 step 15 to generalize craft-rule state enumerations; Nit 7: T1/T3 greps now use literal numeric values
- 2026-07-23: after adversarial review pass 4 — Concern 1: qualified INP/CLS and JS/images greps to avoid false positives against existing SKILL.md tokens; Concern 2: added negative grep for hard-coded 6-state string; Concern 3: added states manifest field grep (context-qualified); Nit 4: fixed Testing Strategy goal-based AC range in spec to exclude AC13; Nit 5: added positive grep for legal-compliance WCAG reword; Nit 6: reworded awk comment
- 2026-07-23: after adversarial review pass 5 — Blocker 1: T6 now bumps plugin.json + runs make build-self FORCE=1; Blocker 2: Status greps fixed to grep -F format matching bold markdown; Concern 3: states manifest field moved to manual QA note; Concern 4: AC23 greps now verify shipped-block presence + queue removal; Concern 5: mobile/desktop CWV dimension added to AC9 (spec) and T3 (plan); Nit 6: AC18 moved to goal-based in spec Testing Strategy; Nit 7: T1 step 8 notes one contiguous table
- 2026-07-23: after adversarial review pass 6 — Blocker 1: actually applied grep -F Status format (prev replacement did not match); Concern 2: added mobile/desktop grep to T1 for SKILL.md AC9; Concern 3: added plugin.json version grep to T6 Tests; Nit 4: fixed Construction tests manual-QA range to AC15-17; Nit 5: updated T6 Done-when count to eight tests
