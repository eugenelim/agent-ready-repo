# Plan: communication-modes-editorial

- **Spec:** [`spec.md`](spec.md)
- **Wave schedule:** 0 (done) → 1 (parallel) → 2 (parallel, depends on Wave 1) → 3 (sequential) → 4 (sequential)

---

## Wave 0 — Complete (pre-work)

Pack audit completed in-session. Findings:
- experience-design: 18 skills + 1 agent; gap at composition + mode layers
- product-engineering: 15 skills + 3 agents; no mode concept
- product-strategy: 9 skills; no mode concept
- Repo's own public-facing copy: already strong; Phase 12 will be conservative

---

## Wave 1 — Reference file creation (parallel)

### Task 1a — Create communication-modes.md

- **Verification mode:** Goal-based check
- **Depends on:** nothing
- **Touches:** `packs/experience-design/.apm/skills/content-design/references/communication-modes.md` (new)
- **Approach:** Write the 3-mode framework — optimization target, information hierarchy, anti-patterns for each. This is the canonical copy; Task 3a update to SKILL.md will reference it.
- **Done when:** File exists; `grep "product-copy\|technical-editorial\|reference-documentation"` returns all 3 mode names; file includes the information hierarchy (Problem → Insight → Outcome → Proof → Mechanism → Detail) for product-copy mode.

### Task 1b — Create editorial-quality-gates.md (canonical in tone-of-voice)

- **Verification mode:** Goal-based check
- **Depends on:** nothing
- **Touches:** `packs/experience-design/.apm/skills/tone-of-voice/references/editorial-quality-gates.md` (new)
- **Approach:** Write anti-AI-smell checklist (flag words as warning signals, editorial judgment criteria), deletion pass (10-question protocol), and human copy tests (5-second, specificity, POV, human tests). This is the canonical copy; Task 1c copies it to conversion-design.
- **Done when:** File exists; contains the word list (unlock, empower, seamless, robust, etc.); contains all 10 deletion questions; contains the 4 copy tests; includes the "warning signal not forbidden word" editorial judgment framing.

### Task 1c — Copy editorial-quality-gates.md to conversion-design

- **Verification mode:** Goal-based check
- **Depends on:** Task 1b
- **Touches:** `packs/experience-design/.apm/skills/conversion-design/references/editorial-quality-gates.md` (new)
- **Approach:** Copy Task 1b's file; add intra-pack duplication note at top ("intentionally duplicated from `tone-of-voice`'s `references/editorial-quality-gates.md`").
- **Done when:** File exists; `diff` against Task 1b shows only the duplication note differs.

---

## Wave 2 — SKILL.md and agent updates (parallel, depends on Wave 1)

### Task 2a — Update content-design SKILL.md

- **Verification mode:** Goal-based check
- **Depends on:** Task 1a (communication-modes.md)
- **Touches:** `packs/experience-design/.apm/skills/content-design/SKILL.md`
- **Approach:**
  1. Step 1 ("Confirm the surface type"): add a third route — "documentation/API/CLI surface" → `reference-documentation` mode. Load `references/communication-modes.md`.
  2. Step 4 ("Resolve and write the content brief"): add `communication_mode: <mode>` to the frontmatter written into the artifact.
  3. Step 5 ("Hand off"): note that downstream skills (`tone-of-voice`, `conversion-design`) read the mode declaration.
- **Done when:** Read the SKILL.md; Step 1 mentions 3 surface types including documentation/API/CLI; Step 4 includes `communication_mode:` in the artifact frontmatter; references/communication-modes.md is cited.

### Task 2b — Update tone-of-voice SKILL.md

- **Verification mode:** Goal-based check
- **Depends on:** Task 1b (editorial-quality-gates.md)
- **Touches:** `packs/experience-design/.apm/skills/tone-of-voice/SKILL.md`
- **Approach:**
  1. Step 3 ("Ground each goal in stable referents"): add — "If a content brief is upstream and declares `communication_mode: product-copy`, load `references/editorial-quality-gates.md` and run the anti-AI-smell check against each candidate copy goal before recording it. Flag any goal whose referent uses compensatory language."
  2. Step 7 ("Hold the plain-language floor"): add the anti-AI-smell pass as a fourth check alongside the existing three (no jargon, no idioms, no identity assumptions).
- **Done when:** Read the SKILL.md; Steps 3 and 7 contain the anti-AI-smell references; editorial-quality-gates.md is cited.

### Task 2c — Update conversion-design SKILL.md

- **Verification mode:** Goal-based check
- **Depends on:** Task 1c (editorial-quality-gates.md in conversion-design/references/)
- **Touches:** `packs/experience-design/.apm/skills/conversion-design/SKILL.md`
- **Approach:** Add a new final section "## Editorial quality gate" as the last section before any existing hand-off or anti-patterns. The section:
  1. Deletion pass: load `references/editorial-quality-gates.md`; run the 10-question deletion protocol against the above-fold spec and scroll story.
  2. Human copy tests: run all 4 tests (5-second, specificity, point-of-view, distinctiveness); note which passed and which raised concerns.
  3. The spec output must include a one-line summary of the gate results.
- **Done when:** Read the SKILL.md; "## Editorial quality gate" is the last content section before anti-patterns; contains deletion pass and human copy tests; references/editorial-quality-gates.md is cited.

### Task 2d — Update experience-reviewer agent

- **Verification mode:** Goal-based check
- **Depends on:** Tasks 1a, 1b (both references; inlined criteria rather than referenced as files, since agent has no references/ directory)
- **Touches:** `packs/experience-design/.apm/agents/experience-reviewer.md`
- **Approach:**
  1. Marketing clarity lens scope: change "Fires when the artifact includes above-fold copy with a persuasion or conversion goal" to "Fires when the artifact includes above-fold copy with a persuasion or conversion goal, OR when the artifact's frontmatter declares `communication_mode: product-copy`."
  2. Add three sub-checks under the marketing clarity lens (after the existing tweet test / 5-second scan / painkiller-first):
     - **Anti-AI-smell scan**: flag instances of compensatory language (unlock, empower, seamless, robust, comprehensive, powerful, innovative, transformative, next-generation, best-in-class, end-to-end, at scale, revolutionize, leverage). Each flagged word earns a question: "Is this carrying a specific meaning, or compensating for lack of specificity?" Also flag: generic three-part lists, repeated triads, long paragraphs reducible to one sentence, copy that could describe 10,000 other products unchanged.
     - **Deletion audit**: "Assume this draft is 30% too long. Identify the weakest paragraph, the most generic sentence, the most AI-sounding sentence, and any repeated idea." These become findings, not automatic blockers.
     - **Specificity test**: "Could this paragraph appear unchanged on another company's website with only the product name swapped?" If yes, flag as a major concern.
  3. Update the frontmatter description to mention the extended scope.
- **Done when:** Read the agent file; marketing clarity lens scope includes `communication_mode: product-copy`; three new sub-checks are present; frontmatter description updated.

---

## Wave 3 — Integration test (sequential, depends on Wave 2)

### Task 3 — Test against 3 real examples

- **Verification mode:** Visual / manual QA
- **Depends on:** Tasks 2a, 2b, 2c, 2d
- **Touches:** `docs/specs/communication-modes-editorial/test-results.md` (new, documenting before/after)
- **Approach:** For each example, run the relevant improved skill(s) and document before/after:
  1. **Example 1 — Marketing surface**: Pick a pack card or web component (e.g. `web/src/content/packs/experience-design.md` or similar). Run `conversion-design` workflow on it. Compare before/after: word count, specificity, generic language, editorial gate results.
  2. **Example 2 — Pack README**: Run `content-design` (mode: technical-editorial or product-copy depending on README purpose) + `tone-of-voice` on a pack description. Document mode routing decision.
  3. **Example 3 — Product doc**: Run the workflow on `docs/product/shaping/product-vision-INI-001.md` or a prfaq. Document anti-AI-smell findings.
- **Done when:** `test-results.md` exists with before/after for all 3 examples; evaluation covers word count, specificity, generic language, mode-awareness.

---

## Wave 4 — Pack bump and conservative copy updates

### Task 4a — Bump pack version and validate build

- **Verification mode:** Goal-based check
- **Depends on:** Tasks 2a, 2b, 2c, 2d
- **Touches:** `packs/experience-design/pack.toml`; `packs/experience-design/.claude-plugin/plugin.json` (if exists)
- **Approach:** Increment patch version in pack.toml. Update plugin.json to match. Run `make build-self` and `make build-check` to regenerate projected artifacts and validate no marketplace drift.
- **Done when:** `grep version packs/experience-design/pack.toml` shows incremented version; `make build-check` exits 0.

### Deferred: Phase 12 conservative copy updates

Deferred to a follow-up PR based on Task 3 test results. If testing reveals genuine gaps, targeted updates will be scoped in a separate task. Not tracked in this spec to avoid an unverifiable no-op task.
