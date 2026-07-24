# Spec: product-strategy-adoption-doctrine

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0071](../../rfc/0071-digital-experience-doctrine.md) (ini-003 M2a), [spec/digital-experience-contract](../digital-experience-contract/spec.md) (Shipped — Strategy section contract that PS skills must populate)
- **Brief:** none
- **Contract:** product-strategy pack v0.1.2 → v0.2.0; 9 skill SKILL.md files; 9 skill eval files; web/src/content/packs/product-strategy.md; web/src/content/journeys/product-strategy.md; docs/guides/product-strategy/how-to/adoption-hypothesis-and-causal-metric-tree.md

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The product-strategy pack produces committed strategy artifacts — SWOT, PRFAQ, OKR cascade, UX strategy, content strategy — but none of its nine skills explicitly own the adoption hypothesis, first-success event, value loop, or causal metric tree. A strategy can ship polished and choice-free, with a compelling vision but no mechanism for adoption. First-success remains ownerless until a growth pack exists; the Digital Experience Contract's Strategy section fields go unfilled.

This spec delivers the **Product Strategy Adoption Doctrine**: a 14-point strategy output structure that makes adoption hypothesis and causal metric tree required outputs, a strategy-to-experience section that maps directly to the Digital Experience Contract's Strategy fields, anti-pattern detection across all PS skills, updated activation evals with weak fixtures, and a how-to guide for authoring adoption hypothesis and causal metric trees.

The deliverables are:

1. A **14-point strategy output structure** codified across the strategy-producing PS skills. The 14 points: (1) situation — macro environment, (2) competitive landscape, (3) portfolio position, (4) stakeholder perspectives, (5) diagnosis — SWOT synthesis, (6) strategic choices, (7) target user and context, (8) OKR-derived gaps, (9) adoption hypothesis, (10) first-success event, (11) repeat-value behavior, (12) value loop, (13) causal metric tree (north-star + leading indicators), (14) differentiation and moat. Together these produce the strategy-to-experience handoff that feeds the Digital Experience Contract's Strategy section.

2. A **strategy-to-experience section** with 7 named fields (matching the DEC's 7 Strategy h3 headers exactly) added as an explicit output step to `write-prfaq` and `run-okr-cascade`, and referenced in `define-ux-strategy`. The 7 fields map exactly to the Digital Experience Contract's `## Strategy` section h3 headers: Target User and Context, Diagnosis and Strategic Choices, Adoption Hypothesis, Value Loop, Metric Tree, Differentiation, Assumptions and Kill Criteria. (First-success event is nested inside the Adoption Hypothesis field, not a peer h3.)

3. **Anti-pattern detection** added to each of the five strategy-producing skills (`write-prfaq`, `run-swot`, `run-okr-cascade`, `define-ux-strategy`, `synthesize-stakeholder-research`): polished-but-choice-free, launch-as-adoption, metric-list-without-causal-tree, moat-without-mechanism, vision-without-adoption-path. Situation-analysis skills (`run-pestle-analysis`, `run-porters-five-forces`, `run-bcg-matrix`) each get framework-specific anti-patterns that guard against moat-without-mechanism and polished-but-choice-free patterns.

4. **Updated triggers and near-miss guards** across all 9 PS skills: natural-language activation triggers (what the user would say), explicit near-miss guards for adjacent disciplines, and the define-content-strategy / XD content-design boundary made explicit in frontmatter.

5. **Updated evals** for all 9 skills: `eval_queries.json` extended with weak fixtures (polished-but-choice-free requests, metric-list-without-causal-tree, unsupported moat claims); `evals.json` assertions tightened to require adoption hypothesis and causal metric tree fields in strategy-producing skills.

6. **`write-prfaq` internal FAQ update**: step 4 extended to require the success metric to be traceable to the first-success event.

7. **Pack version bump**: `pack.toml` version from `0.1.2` to `0.2.0` (new doctrine = minor bump).

8. **Web updates**: `web/src/content/packs/product-strategy.md` updated with jobs-first layout; `web/src/content/journeys/product-strategy.md` updated to reflect the 14-point output structure and strategy-to-experience handoff.

9. **How-to guide**: `docs/guides/product-strategy/how-to/adoption-hypothesis-and-causal-metric-tree.md` — Diátaxis how-to for authoring an adoption hypothesis and causal metric tree, with worked example.

## Boundaries

### Always do

- Make adoption hypothesis and causal metric tree **required outputs** in SKILL.md procedure steps for `write-prfaq`, `run-okr-cascade`, and `define-ux-strategy`
- Map the strategy-to-experience section fields to the Digital Experience Contract's `## Strategy` section exactly — same field names, same order
- Add all five adoption-doctrine anti-patterns to each strategy-producing skill; add framework-specific anti-patterns to situation-analysis skills
- Write descriptions as natural-language activation triggers (what the user would say), not artifact names
- Clarify the define-content-strategy / XD content-design boundary in `define-content-strategy` frontmatter: "Do NOT use to write per-surface content or microcopy — that belongs to content-design (experience-design pack)"
- Run `python3 tools/check-contract-drift.py --root .` and confirm exit 0
- Bump pack version in `pack.toml` from 0.1.2 to 0.2.0
- Add at least one weak fixture per skill to `eval_queries.json` covering polished-but-choice-free or moat-without-mechanism framing
- Tighten `evals.json` assertions for strategy-producing skills to require adoption hypothesis or causal metric tree outputs

### Ask first

- Renaming any field in the Digital Experience Contract's Strategy section
- Changing the scope of any skill beyond what the doctrine requires

### Never do

- Add a new skill (this spec updates existing skills; new skills go through RFC)
- Change the artifact output paths (agentbundle-layout.md governs those)
- Add governance or RFC citations in skill content

## Acceptance Criteria

- [x] AC1: `write-prfaq` SKILL.md procedure includes an explicit step to output the adoption hypothesis and first-success event; anti-patterns include moat-without-mechanism and launch-as-adoption
- [x] AC2: `write-prfaq` SKILL.md procedure step for the internal FAQ requires the success metric to be traceable to the first-success event
- [x] AC3: `run-swot` SKILL.md procedure includes a step that names adoption hypothesis and differentiation mechanism as required synthesis outputs; anti-patterns include vision-without-adoption-path
- [x] AC4: `run-okr-cascade` SKILL.md procedure includes an explicit step to derive the causal metric tree (north-star + leading indicators) from OKR gap analysis; anti-patterns include metric-list-without-causal-tree
- [x] AC5: `define-ux-strategy` SKILL.md procedure includes an explicit step to output the value loop and adoption hypothesis in Goals+Measures; anti-patterns include polished-but-choice-free and launch-as-adoption
- [x] AC6: `synthesize-stakeholder-research` SKILL.md anti-patterns include vision-without-adoption-path; procedure includes a step flagging when adoption signal is absent from research
- [x] AC7: `define-content-strategy` frontmatter near-miss guard explicitly states: "Do NOT use to write per-surface content or microcopy — that belongs to content-design (experience-design pack)"
- [x] AC8: `run-pestle-analysis`, `run-porters-five-forces`, `run-bcg-matrix` SKILL.md anti-patterns each include a moat-without-mechanism guard appropriate to their framework
- [x] AC9: All 9 PS skill descriptions use natural-language activation triggers (what the user would say, not artifact names)
- [x] AC10: `write-prfaq` `evals.json` has an assertion requiring the internal FAQ success metric to be traceable to the first-success event
- [x] AC11: `write-prfaq`, `run-swot`, `run-okr-cascade`, `define-ux-strategy` `evals.json` assertions require adoption hypothesis or causal metric tree outputs
- [x] AC12: All 9 skill `eval_queries.json` files include at least one weak fixture (should_trigger: false) for a polished-but-choice-free or moat-without-mechanism framing
- [x] AC13: `pack.toml` version is `0.2.0`
- [x] AC14: `web/src/content/packs/product-strategy.md` description reflects the adoption doctrine
- [x] AC15: `web/src/content/journeys/product-strategy.md` reflects the 14-point output structure and explicitly names the strategy-to-experience handoff to the Digital Experience Contract
- [x] AC16: `docs/guides/product-strategy/how-to/adoption-hypothesis-and-causal-metric-tree.md` exists as a Diátaxis how-to with a worked example
- [x] AC17: `python3 tools/check-contract-drift.py --root .` exits 0
- [x] AC18: `make build-check` passes

## Testing Strategy

All nine skills are pure-markdown SKILL.md files — no executable code. Verification mode: **goal-based check** throughout.

- For each SKILL.md change: `grep` confirms required phrases present
- For eval files: valid JSON confirmed; weak fixtures counted
- For drift check: `python3 tools/check-contract-drift.py --root .` exits 0
- For pack version: `grep 'version = "0.2.0"' packs/product-strategy/pack.toml`
- For how-to guide: file exists; contains worked example; Diátaxis format confirmed
- Build gate: `make build-check` passes

## Assumptions

1. The Digital Experience Contract's `## Strategy` section field names are frozen at schema-version "1.0".
2. All 9 PS skills are pure-markdown SKILL.md files; JSON validity is sufficient for eval verification.
3. The pack's `first-value` example uses `write-prfaq`; the changes here don't break the first-value path.

## Declined

- **New `adoption-hypothesis` skill**: adoption hypothesis and causal metric tree are outputs of existing strategy skills; a new skill would require an RFC
- **Automated content-quality validation**: content quality is a rubric judgment call (eval), not a buildtime check
- **Changing artifact output paths**: agentbundle-layout.md governs output paths; scope is doctrine additions only
