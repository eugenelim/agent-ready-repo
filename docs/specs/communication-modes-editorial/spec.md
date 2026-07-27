# Spec: communication-modes-editorial

- **Status:** Draft
- **Mode:** full (structural + public-interface triggers)
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Add explicit communication-mode routing and editorial quality gates to the
`experience-design` pack so that when its skills are composed for public-facing
writing tasks, they declare the **Product Copy** mode and apply sharper
editorial discipline to Product Copy output specifically.

**Why this matters.** The system already has strong product and experience
skills — `content-design`, `tone-of-voice`, `conversion-design`,
`experience-reviewer` — each with substantive craft rules. The gap is not
capability; it is composition and mode-blindness. When these skills chain (e.g.
`tone-of-voice` → `conversion-design` → `experience-reviewer`), no step
declares "this output is Product Copy, not a strategy document," so downstream
skills don't shift editorial register. The result can be technically correct but
rhetorically generic — complete rather than persuasive, polished rather than
specific.

The fix is the smallest change that produces a large improvement:

1. `content-design` declares `communication_mode:` in its artifact frontmatter.
2. Two new reference files define the modes and the editorial quality gates.
3. `tone-of-voice` and `conversion-design` consume the mode declaration and
   apply mode-appropriate editorial criteria.
4. `experience-reviewer` extends its existing marketing clarity lens to cover
   anti-AI-smell, deletion, and copy tests for Product Copy mode artifacts.

## Boundaries

**In scope:**
- `packs/experience-design/.apm/skills/content-design/SKILL.md` — add mode declaration in output procedure and artifact frontmatter
- `packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` — add anti-AI-smell step when mode = `product-copy`
- `packs/experience-design/.apm/skills/conversion-design/SKILL.md` — add deletion pass + human copy tests before hand-off
- `packs/experience-design/.apm/agents/experience-reviewer.md` — extend marketing clarity lens scope and add anti-AI-smell + deletion + copy-test sub-checks
- New reference files in each affected skill's `references/` directory:
  - `communication-modes.md` — the 3-mode framework
  - `editorial-quality-gates.md` — anti-AI-smell checklist, deletion pass protocol, human copy tests
- `packs/experience-design/pack.toml` — version bump (patch)
- `packs/experience-design/README.md` — update if skill descriptions need updating

**Not in scope:**
- No new skills or agents. Extending existing ones only.
- No changes to `voice-and-microcopy` (product UI states, not public-facing copy)
- No changes to product-engineering or product-strategy pack skills
- No changes to the `experience-reviewer`'s non-marketing-clarity lenses
- No changes to `design-review` skill (authoring-time; experience-reviewer is the right extension point)
- Phase 12 copy updates: conservative; addressed only if testing reveals genuine gaps

## Acceptance Criteria

- [ ] **AC1 — Mode declaration in content-design.** `content-design` SKILL.md instructs the agent to include `communication_mode: product-copy | technical-editorial | reference-documentation` in the content brief artifact's frontmatter. `communication_mode` is an editorial label orthogonal to the existing two elicitation sub-paths (which remain unchanged): acquisition surfaces → `product-copy`; product/reference surfaces that are help, feature explanation, or onboarding → `technical-editorial`; product/reference surfaces that are API, CLI, configuration, installation, or troubleshooting → `reference-documentation`. The content-design SKILL.md frontmatter `description:` is updated to reflect the mode concept. SKILL.md:21 ("Documentation surfaces route as product/reference") is updated to note that documentation surfaces map to `reference-documentation` mode.

- [ ] **AC2 — communication-modes.md reference exists.** `packs/experience-design/.apm/skills/content-design/references/communication-modes.md` defines the 3 modes (optimization target, hierarchy, anti-patterns) and is referenced from `content-design` SKILL.md Step 1.

- [ ] **AC3 — editorial-quality-gates.md reference exists.** `packs/experience-design/.apm/skills/tone-of-voice/references/editorial-quality-gates.md` and `packs/experience-design/.apm/skills/conversion-design/references/editorial-quality-gates.md` (copy with duplication note) define the anti-AI-smell checklist, deletion pass protocol (10 questions), and human copy tests (5-second, specificity, point-of-view, distinctiveness tests).

- [ ] **AC4 — tone-of-voice applies anti-AI-smell when mode = product-copy.** `tone-of-voice` SKILL.md Step 3 (ground each goal) includes: "If a content brief is upstream and declares `communication_mode: product-copy`, load `references/editorial-quality-gates.md` and check each copy goal against the anti-AI-smell criteria before recording." Step 7 (plain-language floor) adds the anti-AI-smell pass as a mandatory parallel check alongside the existing three floor checks.

- [ ] **AC5 — conversion-design requires deletion pass and human copy test.** `conversion-design` SKILL.md adds a final step (after Numbered product tour spine, before canonical aesthetic reference): run the deletion pass (load `references/editorial-quality-gates.md`) and the human copy test suite. The output spec must note which copy tests passed and which questions raised concerns.

- [ ] **AC6 — experience-reviewer marketing clarity lens extended.** `experience-reviewer` agent:
  - Scope change: marketing clarity lens fires on **copy-bearing Product Copy mode artifacts** (landing pages, pack cards, README openings, product descriptions with `communication_mode: product-copy`). Does NOT fire on content briefs or tone-of-voice docs (direction artifacts, not final copy).
  - Three new sub-checks added under marketing clarity: anti-AI-smell scan (flag compensatory words — unlock, empower, seamless, robust, comprehensive, powerful, next-generation, best-in-class, at scale, revolutionary — as warning signals requiring editorial judgment, not automatic findings), deletion audit ("assume 30% too long — identify the weakest paragraph and any repeated idea"), and the specificity check ("could this paragraph appear unchanged on another company's website with only the product name swapped?").
  - The anti-AI-smell word list is inlined in the agent file with a comment noting it mirrors `tone-of-voice`'s `references/editorial-quality-gates.md` and must be kept in sync.
  - Existing tweet test, 5-second scan, and painkiller-first criteria are unchanged.

- [ ] **AC7 — tested against 3 real examples.** At least 3 artifacts from this repo run through the improved skills with before/after documented:
  1. A copy-bearing marketing surface (e.g. a web component or pack card)
  2. A pack README description
  3. A product document (e.g. a prfaq or vision doc)

- [ ] **AC8 — pack version bumped.** `packs/experience-design/pack.toml` version incremented (patch). If `plugin.json` exists, updated in the same commit.

## Testing Strategy

**Mode:** Mixed — goal-based check for reference/SKILL.md/agent edits (grep/read); visual/manual QA for the integration test (AC7).

**Verification for each task:**
- Reference file tasks (AC2, AC3): `grep` for key terms (mode names, anti-AI-smell word list, deletion pass questions) in the created files.
- SKILL.md update tasks (AC1, AC4, AC5): Read the modified SKILL.md and confirm the new procedure steps appear and reference the correct files.
- experience-reviewer update (AC6): Read the modified agent file and confirm scope change + new sub-checks appear under the marketing clarity lens.
- Integration test (AC7): Run each modified skill on a real surface, compare before/after on at least: word count, specificity, generic language, mode-awareness.
- Pack bump (AC8): `grep` version in pack.toml confirms increment.

## Assumptions

**Verified:**
- Technical: `packs/experience-design/.apm/skills/content-design/references/` exists and accepts new .md files (ls check confirms structure)
- Technical: experience-reviewer is a flat agent file (.apm/agents/experience-reviewer.md) with no external references/ directory — additions must be inline
- Technical: reference files within a pack are copied per-skill with a duplication note (verified via `well-architected-pillars.md` intra-pack pattern and `digital-experience-contract.md` cross-pack pattern)
- Product: content-design already routes between "acquisition" and "product/reference" — adding a third bucket (reference-documentation) for docs/API/CLI surfaces is a natural extension of existing routing logic

**Unverified:**
- Product: adopters reading existing content briefs won't be confused by the new `communication_mode:` frontmatter field (risk: low — the field is additive and self-describing)

## Declined patterns

- Tempted to create a new editorial-review agent; declining — extending experience-reviewer is sufficient and preserves the existing review architecture
- Tempted to add editorial guidance to all 18 experience-design skills; declining — only the 4 skills directly in the copy-production chain need changes
- Tempted to create a pack-level shared references directory; declining — the pack convention is per-skill copies with duplication notes, not a shared directory (documented in packs/AGENTS.md)
- Tempted to update voice-and-microcopy in product-engineering; declining — that skill targets UI states, not public-facing copy, and is out of scope
