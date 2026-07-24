# Plan: product-strategy-adoption-doctrine

- **Status:** Executing <!-- Drafting | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)
- **Mode:** Full (structural + public-interface change — updates 9 published skill SKILL.md files and evals)

## Tasks

### T1: Update `write-prfaq` SKILL.md — adoption hypothesis + anti-patterns
- **Depends on:** none
- **Verification:** goal-based check
- **Done when:** `grep -i "adoption hypothesis" packs/product-strategy/.apm/skills/write-prfaq/SKILL.md` returns a match; `grep -i "moat-without-mechanism" packs/product-strategy/.apm/skills/write-prfaq/SKILL.md` returns a match
- **Approach:** Add step 5a to procedure: "Derive the adoption hypothesis and first-success event from the solution definition. The adoption hypothesis states what behavior constitutes first success. The first-success event is the one action that proves first value." Update step 4 (internal FAQ) to require: "Name the first-success event and confirm the success metric in the internal FAQ is traceable to it." Add anti-patterns: moat-without-mechanism, launch-as-adoption. Update description to natural-language trigger.

### T2: Update `run-swot` SKILL.md — adoption synthesis + anti-patterns
- **Depends on:** none
- **Verification:** goal-based check
- **Done when:** `grep -i "adoption hypothesis" packs/product-strategy/.apm/skills/run-swot/SKILL.md` returns a match; `grep -i "vision-without-adoption-path" packs/product-strategy/.apm/skills/run-swot/SKILL.md` returns a match
- **Approach:** Extend step 6 (strategic implications synthesis) to require: "Name the adoption hypothesis — how the identified opportunities translate into a first-success event. Name the differentiation mechanism — the Strength-Opportunity pair that produces a defensible moat." Add anti-patterns: vision-without-adoption-path, polished-but-choice-free. Update description to natural-language trigger.

### T3: Update `run-okr-cascade` SKILL.md — causal metric tree + anti-patterns
- **Depends on:** none
- **Verification:** goal-based check
- **Done when:** `grep -i "causal metric tree" packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md` returns a match; `grep -i "metric-list-without-causal-tree" packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md` returns a match
- **Approach:** Add step 3a: "Derive the causal metric tree. Name the north-star metric (the one outcome metric that captures value delivery). Name the 2–4 leading indicators that causally predict the north-star. Each leading indicator must connect to a specific OKR gap." Add anti-patterns: metric-list-without-causal-tree, polished-but-choice-free. Update description to natural-language trigger.

### T4: Update `define-ux-strategy` SKILL.md — value loop + adoption hypothesis + anti-patterns
- **Depends on:** none
- **Verification:** goal-based check
- **Done when:** `grep -i "value loop" packs/product-strategy/.apm/skills/define-ux-strategy/SKILL.md` returns a match; `grep -i "polished-but-choice-free" packs/product-strategy/.apm/skills/define-ux-strategy/SKILL.md` returns a match
- **Approach:** Add step 3a to procedure: "For each Vision statement, derive the value loop — how value compounds with each successive use of the product. Name the reinforcing mechanism that brings the user back." Add step 3b: "State the adoption hypothesis in Goals+Measures: the UX-level behavior that constitutes first success, and the repeat-value behavior that constitutes retention." Add anti-patterns: polished-but-choice-free, launch-as-adoption, vision-without-adoption-path. Update description to natural-language trigger.

### T5: Update `synthesize-stakeholder-research` SKILL.md — adoption signal + anti-patterns
- **Depends on:** none
- **Verification:** goal-based check
- **Done when:** `grep -i "vision-without-adoption-path" packs/product-strategy/.apm/skills/synthesize-stakeholder-research/SKILL.md` returns a match
- **Approach:** Add step 5a: "Flag adoption signal absence: if no stakeholder group names a behavior that constitutes first success or describes why they would return after first use, surface: 'Adoption signal absent — the research covers intent and awareness but no first-success event is named by any stakeholder group.'" Add anti-pattern: vision-without-adoption-path. Update description to natural-language trigger.

### T6: Update `define-content-strategy` SKILL.md — near-miss boundary + trigger
- **Depends on:** none
- **Verification:** goal-based check
- **Done when:** `grep -i "content-design (experience-design pack)" packs/product-strategy/.apm/skills/define-content-strategy/SKILL.md` returns a match
- **Approach:** Update frontmatter description to add explicit near-miss: "Do NOT use to write per-surface content or microcopy — that belongs to content-design (experience-design pack)." (The existing text already says "belongs in the experience-design pack's content-design skill" — make it explicit in the description field.) Update description to natural-language trigger.

### T7: Update situation-analysis skills — moat-without-mechanism anti-patterns
- **Depends on:** none
- **Verification:** goal-based check
- **Done when:** `grep -i "moat-without-mechanism" packs/product-strategy/.apm/skills/run-pestle-analysis/SKILL.md packs/product-strategy/.apm/skills/run-porters-five-forces/SKILL.md packs/product-strategy/.apm/skills/run-bcg-matrix/SKILL.md` returns matches in all three
- **Approach:**
  - `run-pestle-analysis`: Add anti-pattern "Macro analysis as moat claim: identifying a macro trend does not constitute a competitive moat. A PESTLE entry that names a tailwind but doesn't name a mechanism by which this specific organization captures it preferentially is incomplete."
  - `run-porters-five-forces`: Add anti-pattern "Force profile without moat derivation: rating the forces produces an industry portrait, not a competitive position. A Five Forces analysis that ends with 'rivalry is high' without naming the structural mechanism that protects this player is incomplete."
  - `run-bcg-matrix`: Add anti-pattern "Quadrant as strategy substitute: BCG positions products; it does not name the mechanism that defends a Star's position or moves a Question Mark to Star. A BCG analysis without investment implications per quadrant is a labeling exercise."
  - Update descriptions to natural-language triggers for all three.

### T8: Update evals for all 9 skills
- **Depends on:** T1, T2, T3, T4, T5, T6, T7
- **Verification:** goal-based check
- **Done when:** each `eval_queries.json` has at least one `should_trigger: false` weak fixture; strategy-producing skill `evals.json` assertions include adoption hypothesis or causal metric tree; `python3 -c "import json; [json.load(open(p)) for p in ...]"` exits 0
- **Approach:** For each of the 9 skills:
  - Add 1–2 weak fixtures to `eval_queries.json` (polished-but-choice-free requests, moat-without-mechanism)
  - For `write-prfaq`, `run-swot`, `run-okr-cascade`, `define-ux-strategy`: tighten `evals.json` assertions to require adoption hypothesis/causal metric tree
  - For `write-prfaq`: add assertion that internal FAQ success metric is traceable to first-success event

### T9: Bump pack version to 0.2.0
- **Depends on:** none
- **Verification:** goal-based check
- **Done when:** `grep 'version = "0.2.0"' packs/product-strategy/pack.toml` returns a match
- **Approach:** Edit `pack.toml` version field from `0.1.2` to `0.2.0`

### T10: Update `web/src/content/packs/product-strategy.md`
- **Depends on:** T1, T2, T3, T4, T5, T6, T7
- **Verification:** goal-based check
- **Done when:** File contains "adoption hypothesis" and "causal metric tree" in description or skill list
- **Approach:** Update the pack tagline and description to reflect adoption doctrine. Jobs-first layout: lead with what the pack enables (committed adoption hypothesis + causal metric tree), not what it outputs. Update the pack description to note that PS skills now own the Digital Experience Contract's Strategy section.

### T11: Update `web/src/content/journeys/product-strategy.md`
- **Depends on:** T1, T2, T3, T4, T5, T6, T7
- **Verification:** goal-based check
- **Done when:** File contains "14-point strategy output structure" or equivalent, and "strategy-to-experience handoff" or equivalent reference to the Digital Experience Contract
- **Approach:** Update the `whatChanges` field to describe the 14-point output structure. Update the journey stage descriptions to include the adoption hypothesis and causal metric tree steps. Add a reference to the Digital Experience Contract's Strategy section as the handoff target.

### T12: Create how-to guide
- **Depends on:** none
- **Verification:** goal-based check
- **Done when:** `docs/guides/product-strategy/how-to/adoption-hypothesis-and-causal-metric-tree.md` exists and `grep -i "worked example\|example:" docs/guides/product-strategy/how-to/adoption-hypothesis-and-causal-metric-tree.md` returns a match
- **Approach:** Write Diátaxis how-to guide (Use when / Prerequisites / Result header; step-by-step procedure; worked example using a concrete product scenario; connection to Digital Experience Contract Strategy section)

### T13: Run drift check and build-check
- **Depends on:** T1–T12
- **Verification:** goal-based check
- **Done when:** `python3 tools/check-contract-drift.py --root .` exits 0; `make build-check` passes
- **Approach:** Run drift check; if it fails, diagnose and sync the four contract copies. Run build-check.
