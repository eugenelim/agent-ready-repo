# Plan: m2-frame-intent-jtbd

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Five files change: `SKILL.md` (step 5 elicitation text), `intent-template.md`
(four new Opportunity sub-fields), a new `references/jtbd-job-categories.md`
(three-tier definitions shared with `identify-opportunities`), the existing
`shape-a-feature-intent.md` guide (JTBD subsection), and `pack.toml` (version
bump to 0.12.0). All changes are additive prose — no executable code, no schema
migration. Riskiest part is the SKILL.md step 5 edit: the boundary with
`identify-opportunities` must be visible and enforced in the prose (no scoring,
explicit handoff). Author the reference file first so both `SKILL.md` and the
guide link to a concrete file rather than describing the categories inline.

## Constraints

- Constrained by RFC-0064 (scopes this work at M2.7; must not re-open boundary
  decisions already settled in RFC-0064's Known Unknowns / Resolved sections)
- The `frame-intent` vs `identify-opportunities` boundary is settled: no Ulwick
  scoring or ranked job list in `frame-intent` (RFC-0064 Resolved, 2026-07-18)
- Template changes must be additive: existing free-form Opportunity prose remains
  valid (back-compat commitment in the spec)

## Construction tests

All tests are goal-based checks (grep / file-existence probes). Per-task tests
below are self-contained; no cross-task integration tests are needed — each task
verifies a single file, and the spec's AC checklist is the end-to-end smoke.

**Integration tests:** none beyond per-task goal-based checks  
**Manual verification:** run `frame-intent` in a scratch session on a feature
description; confirm the skill prompts for all four dimensions with one-line
guidance each; confirm the emitted intent artifact's Opportunity section contains
all four sub-fields populated with the elicited answers — not empty template labels
(direct gate for AC8 / spec:129-132); verify vocabulary matches
`identify-opportunities`' category names; verify guide examples are concrete
(one per dimension). This QA is owned by T2's Done-when and gates T4.

## Design (LLD)

Shape: service — only the "behavior & rules" and "quality attributes" sub-sections
are relevant; the rest are pruned.

### Design decisions

- **Reference file first (T1 → T2, T3, T4 in parallel):** `jtbd-job-categories.md`
  is the single vocabulary source for both the skill and the guide. Authoring it
  first lets T2/T3/T4 link directly rather than each defining the categories
  inline. Traces to: AC5, AC6.
- **Four structured sub-fields, not three:** adding "Struggling moment" alongside
  the three job categories gives the framing a concrete failure-state anchor —
  the point where a practitioner can immediately see where the current situation
  breaks. Traces to: AC1, AC3.
- **Bullet label style, not sub-headers:** `- Functional job:` keeps the Opportunity
  section scannable and avoids inflating the template's visual weight. Chosen per
  spec Boundaries ("Ask first" default). Traces to: AC3.
- **Optional fields via comment, not conditional template:** the four sub-fields
  appear in the template's comment block with "optional" wording; the Opportunity
  body itself remains a single blank line so free-form prose is still the path of
  least resistance. Traces to: AC4.
- **Singular labels, not plural:** the sub-fields use "Functional job" (singular)
  rather than "Functional jobs" (which `identify-opportunities` uses for its
  multi-item discovery list). This is deliberate — frame-intent elicits one primary
  job per dimension as a lightweight intake pass; the plural would imply a list
  the user must enumerate, conflating the two skills. Vocabulary consistency
  (identical category names) still holds for the noun itself. Traces to: AC5.

### Behavior & rules

- Step 5 in `SKILL.md` runs the four-dimensional elicitation unconditionally (both
  greenfield and brownfield) — brownfield already has the maturity gate at step 1;
  JTBD categories are not maturity-gated.
- The handoff pointer to `identify-opportunities` appears at the end of step 5, not
  as a redirect: frame-intent still completes the intent before the pointer fires.
- `jtbd-job-categories.md` must not duplicate the Ulwick scoring formula — a
  one-line cross-reference naming `identify-opportunities` as the scoring home is
  the boundary.

### Quality attributes

- **Back-compat:** the intent template's optional-field comment must ensure any
  agent reading an existing intent (free-form Opportunity prose) does not misread
  it as malformed.
- **Vocabulary consistency:** the three category names in `SKILL.md`,
  `jtbd-job-categories.md`, the template, and the guide must be identical
  ("Functional", "Emotional", "Social") — no synonyms (e.g. "Relational") that
  would split the mental model across docs.

## Tasks

### T1: Author `jtbd-job-categories.md` reference file

**Depends on:** none  
**Touches:** `packs/product-engineering/.apm/skills/frame-intent/references/jtbd-job-categories.md`

**Tests:**
- `test -f packs/product-engineering/.apm/skills/frame-intent/references/jtbd-job-categories.md` — file exists
- `grep -c "Functional\|Emotional\|Social" packs/product-engineering/.apm/skills/frame-intent/references/jtbd-job-categories.md` — all three category names present
- `grep "identify-opportunities" packs/product-engineering/.apm/skills/frame-intent/references/jtbd-job-categories.md` — cross-reference present
- `grep -i "ulwick\|opportunity score\|importance.*satisfaction" packs/product-engineering/.apm/skills/frame-intent/references/jtbd-job-categories.md` — zero hits outside the "Going deeper" section (check by reading; the section must be the last heading in the file, so hits below that heading are acceptable)

**Approach:**
- Create `packs/product-engineering/.apm/skills/frame-intent/references/jtbd-job-categories.md`
- Define each category with a one-sentence definition and one example, matching the vocabulary in `packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md` steps 3–5
- Add a "Struggling moment" subsection (the complement that frame-intent surfaces alongside the job categories)
- Add a closing "Going deeper" paragraph naming `identify-opportunities` as the skill for full job discovery and Ulwick opportunity scoring — do NOT reproduce the scoring formula; a pointer naming the skill and the technique (Ulwick scoring) is sufficient

**Done when:** all four grep tests pass.

---

### T2: Update `SKILL.md` step 5 with three-tier JTBD elicitation

**Depends on:** T1  
**Touches:** `packs/product-engineering/.apm/skills/frame-intent/SKILL.md`

**Tests:**
- `grep "Functional job" packs/product-engineering/.apm/skills/frame-intent/SKILL.md` — present
- `grep "Emotional job" packs/product-engineering/.apm/skills/frame-intent/SKILL.md` — present
- `grep "Social job" packs/product-engineering/.apm/skills/frame-intent/SKILL.md` — present
- `grep "struggling moment" packs/product-engineering/.apm/skills/frame-intent/SKILL.md` — present
- `grep "identify-opportunities" packs/product-engineering/.apm/skills/frame-intent/SKILL.md` — handoff pointer present
- `grep -i "ulwick\|opportunity score\|importance.*satisfaction" packs/product-engineering/.apm/skills/frame-intent/SKILL.md` — zero hits

**Approach:**
- In `SKILL.md` step 5, after the existing "Frame what the user is trying to get done" opening sentence, insert a four-dimension elicitation block: functional job (what they're trying to accomplish), emotional job (how they want to feel), social job (how they want to be perceived), struggling moment (where the current situation fails)
- Each dimension: one sentence of guidance, no scoring prompt
- End step 5 with: "For full job discovery and opportunity scoring, run `identify-opportunities` after framing." (exact wording can vary; the pointer to `identify-opportunities` must be present; do NOT mention importance/satisfaction ratings, scoring mechanics, or ranking in the step-5 body — those terms must stay out of `SKILL.md` entirely per AC10)
- The step instruction must make clear that the skill writes the user's elicited answers into the corresponding Opportunity sub-fields in the intent artifact before proceeding to step 6 — not just prompts and moves on. This is normal frame-intent behavior (the skill fills the template as it goes) but must be explicit so the "output appears in the artifact" AC is unambiguous
- Do not change any other step

**Done when:** all six grep tests pass, `SKILL.md` line count stays under 220 (current is 187; expansion is ~20–30 lines), AND a scratch run of `frame-intent` on a sample feature confirms the emitted artifact's Opportunity section contains the populated sub-field answers — not empty labels (manual QA, gates T4 onwards).

---

### T3: Update `intent-template.md` Opportunity section

**Depends on:** T1  
**Touches:** `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`

**Tests:**
- `grep "Functional job" packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md` — present
- `grep "Emotional job" packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md` — present
- `grep "Social job" packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md` — present
- `grep "Struggling moment" packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md` — present
- `awk '/## Opportunity/,/## Product-vision fields/' packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md | grep -i "optional"` — optional marker present in the Opportunity section (scoped; pre-existing "optional" elsewhere in the template does not satisfy this check)

**Approach:**
- In `intent-template.md`, find the `## Opportunity` section (currently: comment + `<the opportunity>`)
- Expand the comment to add: "Optional JTBD sub-fields — include when framing a job-shaped opportunity; free-form prose above is still valid." followed by four bullet label definitions
- Replace the single `<the opportunity>` line with:
  ```
  <the opportunity — one sentence summary, or use the sub-fields below>

  <!-- optional structured JTBD fields (omit for free-form prose) -->
  - **Functional job:** <what the user is trying to accomplish>
  - **Emotional job:** <how they want to feel during or after the job>
  - **Social job:** <how they want to be perceived by others>
  - **Struggling moment:** <where the current situation fails them>
  ```
- No other section of the template changes

**Done when:** all five grep tests pass.

---

### T4: Update `shape-a-feature-intent.md` guide with JTBD subsection

**Depends on:** T2, T3  
**Touches:** `docs/guides/product-engineering/how-to/shape-a-feature-intent.md`

**Tests:**
- `grep -i "functional job\|jtbd" docs/guides/product-engineering/how-to/shape-a-feature-intent.md` — JTBD section present
- `grep "Emotional job" docs/guides/product-engineering/how-to/shape-a-feature-intent.md` — present
- `grep "Social job" docs/guides/product-engineering/how-to/shape-a-feature-intent.md` — present
- `grep "Struggling moment" docs/guides/product-engineering/how-to/shape-a-feature-intent.md` — present

**Approach:**
- In the "## 1. Frame the intent" section of the guide, after the existing Opportunity bullet (which currently says "what the user is trying to get done, framed without a solution"), insert a "### JTBD enrichment" subsection
- The subsection explains the four dimensions with one-line definitions and one concrete example per dimension (e.g., "Functional job: 'get back into my account on my own'"; "Emotional job: 'feel in control, not at the mercy of support'"; "Social job: 'look capable and self-sufficient to my team'"; "Struggling moment: 'the reset link email arrives 15 minutes late after a failed login'")
- End the subsection with a pointer to `identify-opportunities` for deeper scoring

**Done when:** all four grep tests pass and the guide reads naturally as a prose extension of the existing section (verify by reading — subjective, not a gate).

---

### T5: Bump PE pack version to 0.12.0

**Depends on:** T2, T3, T4  
**Touches:** `packs/product-engineering/pack.toml, packs/product-engineering/.claude-plugin/plugin.json`

**Tests:**
- `grep -m1 "^version" packs/product-engineering/pack.toml` — reads `version = "0.12.0"` (the `[pack]` version; `[pack.adapter-contract]` version must remain unchanged)
- `grep '"version"' packs/product-engineering/.claude-plugin/plugin.json` — reads `"version": "0.12.0"`
- `grep -A15 '"name": "product-engineering"' .claude-plugin/marketplace.json | grep -m1 '"version"'` — reads `0.12.0` in the PE block (after build-self; the marketplace.json is the repo-root aggregate at `.claude-plugin/marketplace.json`, not under `packs/`)

**Approach:**
- Edit `version = "0.11.1"` → `version = "0.12.0"` in `packs/product-engineering/pack.toml`
- Edit `"version": "0.11.1"` → `"version": "0.12.0"` in `packs/product-engineering/.claude-plugin/plugin.json`
- Run `make build-self FORCE=1` to regenerate the repo-root `.claude-plugin/marketplace.json` — confirm the `product-engineering` block in that file reads `0.12.0` (use the scoped grep from T5 Tests)
- Confirm build-self exits 0

**Done when:** all three grep tests pass and build-self exits 0.

---

### T6: Add changelog entry for JTBD enrichment

**Depends on:** T2, T3, T4  
**Touches:** `docs/product/changelog.md`

**Tests:**
- `grep -i "jtbd" docs/product/changelog.md` — must be present ("jtbd" does not pre-exist in the file; any hit confirms the entry landed)

**Approach:**
- In `docs/product/changelog.md`, add a `### Changed` bullet under `## [Unreleased]`:
  `**\`frame-intent\` skill (product-engineering pack 0.12.0) — three-tier JTBD elicitation in step 5.** The Opportunity framing step now explicitly elicits a functional job, emotional job, social job, and struggling moment. The intent template carries four corresponding optional sub-fields. Existing intents with free-form Opportunity prose remain valid without migration.`
- Follow the file's entry style (bold feature name + pack version, then description)

**Done when:** grep test passes.

---

### T7: Mark RFC-0064 AC [M2.7] complete

**Depends on:** T5, T6  
**Touches:** `docs/rfc/0064-ini-001-ai-native-ecosystem.md`

**Tests:**
- `grep "\[x\].*JTBD framing embedded in.*frame-intent" docs/rfc/0064-ini-001-ai-native-ecosystem.md` — marked complete

**Approach:**
- In `docs/rfc/0064-ini-001-ai-native-ecosystem.md`, locate the AC line:
  `- [ ] JTBD framing embedded in \`frame-intent\`…`
- Change `- [ ]` to `- [x]`
- No other lines in the RFC change

**Done when:** grep test passes.

## Rollout

Pure markdown and TOML changes — no compiled artefacts, no data migration, no
infrastructure change, no external-system dependency. Ships as a single PR.
Rollback is trivially a revert of the PR. No flag, no canary.

## Risks

- **Vocabulary drift:** if the three category names in `SKILL.md`, the template,
  the reference file, and the guide don't all use the same exact strings
  ("Functional job" not "Functional Job"), the shared vocabulary splits. Mitigated
  by the per-task grep tests which lock in the exact strings before each task is
  called done.
- **Step 5 expansion scope-creep:** the step 5 edit could drift toward describing
  Ulwick scoring inline (feels natural when you're writing about job categories).
  Mitigated by the zero-hit grep test for "ulwick" in SKILL.md.
- **plugin.json / marketplace drift:** bumping only `pack.toml` and missing
  `.claude-plugin/plugin.json` is the canonical version-bump failure mode for PE
  pack changes. T5 explicitly tests both files and the regenerated marketplace.json.

## Changelog

- 2026-07-21: initial plan
