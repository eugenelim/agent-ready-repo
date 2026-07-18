# Plan: content-design-skill

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Pure-markdown skill authoring. No runtime code, no new dependencies, no
application logic. The change lives entirely under
`packs/experience/.apm/skills/content-design/` plus a one-line `pack.toml`
update.

The riskiest part is SKILL.md authoring: a skill that looks compliant but
(a) reprints framework text verbatim (ADR-0024 Guardrail A violation caught by
`lint-experience-agnostic.py`) or (b) under-specifies the procedure to the point
that cold-prompting produces structurally incomplete content briefs. The
mitigation is writing the procedure against the RFC-0062 proposal's specificity
level and verifying with a manual cold-prompt in both surface-type modes before
declaring done.

Order of operations: scaffold the directory first (T1), then author the SKILL.md
body in full (T2) — this locks the procedure and anti-patterns that drive
everything else. References files expand what the procedure names (T3); the asset
template makes the content brief artifact concrete (T4); evals and pack.toml
update (T5) close the mechanical gates.

**Declined patterns:**
- Tempted to write a combined spec covering both `content-design` and
  `copy-direction` — declining because RFC-0062 explicitly specifies two separate
  spec directories, allowing each skill to be tracked, reviewed, and shipped
  independently.
- Tempted to extend the acquisition sub-path to cover email and mobile onboarding
  — declining per RFC-0062: the sub-path is web-optimized by design; a
  cross-platform extension is deferred to a follow-on amendment.
- Tempted to add a `content-review` step that calls `experience-reviewer` inline
  — declining per RFC-0062 OQ1 resolution: experience-reviewer scope extension is
  a follow-on RFC, not this spec.
- Tempted to author a new ADR for the content-design skill addition — RFC-0062's
  follow-on artifacts list one, but the add-a-skill bar is already governed by
  ADR-0024 + RFC-0050 D6; a new ADR would duplicate without adding a decision. The
  RFC's ADR mention will be resolved by the implementing PR note (drop the item as
  subsumed) rather than authoring an empty record.

**Co-shipping constraint:** This plan ships in the same PR as `copy-direction-skill`.
Landing content-design alone adds a public skill with no semver bump and no backlog
record. The version bump (0.4.2 → 0.5.0), `plugin.json` update, `build-self` run,
and all three backlog entries — `copy-direction-skill-rfc`,
`content-strategy-and-marketing-copy-lens`, and
`experience-reviewer-content-brief-scope` (the OQ1 deferral anchor required by
content-design AC "Experience-reviewer scope extension") — are all created in
copy-direction T7, which carries a cross-spec dependency on this plan's T5.

## Constraints

- **RFC-0062** D1–D5 — binding decisions: `content-design` name (D1), surface-type
  routing with `surface-type` flag (D2), conversion architecture inside the
  acquisition sub-path (D3), no SEO in either skill (D5).
- **ADR-0024** — Guardrails A (point to standards, never reprint values) and B
  (concepts, not platform primitives). Enforced by `tools/lint-experience-agnostic.py`.
- **RFC-0050** — experience pack design-thread completeness bar; `content-brief`
  artifact extends the pack's discover-by-marker set per D6's layout contract.
- **ADR-0028 / RFC-0037** — pack-activation-eval coverage shape (`eval_queries.json`
  + `evals.json`).

## Construction tests

**Integration tests:**
- `tools/lint-experience-agnostic.py` exits 0 on `packs/experience/` after every
  new file lands — the standing guard that no SKILL.md edit leaked a values table or
  stack token.

**Manual verification:**
- Cold-prompt `content-design` (acquisition surface mode) with: persona = "technical
  team leads at growth-stage SaaS companies, most-aware audience." Confirm the output
  content brief includes surface type declaration, audience awareness level (Most
  Aware, Schwartz stage 5), narrative arc (CCD — bottom-of-funnel applicability),
  scroll sections with per-section jobs, above-fold structure (headline + subheadline
  contract), primary CTA, success metric, and artifact path.
- Cold-prompt `content-design` (product/reference surface mode) with: persona =
  "developers integrating the API for the first time." Confirm user task elicitation,
  format selection (steps — procedural task type), content hierarchy
  (must-say → probably-say → might-say), and completion metric (task completion rate).

## Tasks

### T1: Content-design skill directory scaffolded

**Depends on:** none

**Tests:**
- `find packs/experience/.apm/skills/content-design/ -type f | sort` returns at
  minimum: `SKILL.md`, `references/.gitkeep` (or first reference file),
  `assets/.gitkeep` (or template), `evals/.gitkeep` (or eval files)
- `python3 tools/lint-experience-agnostic.py` exits 0 (empty stub has no violations)

**Approach:**
- Create `packs/experience/.apm/skills/content-design/` with subdirectories
  `references/`, `assets/`, `evals/`
- Create `SKILL.md` stub with frontmatter `name: content-design` and
  `description:` placeholder; add section heading stubs (When to invoke, Procedure,
  Anti-patterns) with no body content yet

**Done when:** Directory tree exists; lint exits 0 on empty stub.

---

### T2: SKILL.md fully authored

**Depends on:** T1

**Tests:**
- `python3 tools/lint-experience-agnostic.py` exits 0
- `awk '/^## Procedure/,/^## [^#]/' packs/experience/.apm/skills/content-design/SKILL.md | grep -c "^[0-9]\+\."` returns ≥5 (numbered procedure steps scoped to the Procedure section only)
- `grep "Anti-patterns" packs/experience/.apm/skills/content-design/SKILL.md` matches
- Manual cold-prompt: acquisition mode produces content brief with all six acquisition
  components (awareness level, arc, scroll sections, above-fold, CTAs, success metric)
- Manual cold-prompt: product/reference mode produces content brief with all four
  components (user task, format, hierarchy, completion metric)

**Approach:**
- Write frontmatter `description:` matching RFC-0062 D1 naming rationale ("Use when a
  designer or product person needs to decide what a surface should say, for whom, in
  what form, and to what objective — before any wireframe or screen flow is opened…")
- Write **When to invoke** with four pre-conditions: (1) real surface with a defined
  purpose, (2) no content brief already exists for this surface, (3) you are deciding
  direction not writing final copy, (4) you know or can elicit the target audience
- Write **Procedure** (5 steps):
  1. Confirm `surface-type` (acquisition | product-or-reference); `docs` surfaces
     route as product-or-reference
  2. Elicit or confirm persona and outcome; consume `map-customer-journey` output if
     available; elicit inline if not
  3. Route to sub-path; run elicitation questions for that type (load references)
  4. Resolve and write the content brief to `docs/design/content/<slug>.md`
  5. Hand off: name `copy-direction` (for copy voice), `map-screen-flow` (for screen
     sequencing) as downstream consumers; note OQ1 deferral for experience-reviewer
- Write **Anti-patterns**: refuse reprinting frameworks verbatim, producing copy
  templates, producing analytics, running user research, producing SEO plans,
  substituting a single "global" brief for per-surface briefs

**Done when:** Cold-prompt in both surface-type modes produces structurally complete
briefs (per manual verification above); lint clean.

---

### T3: References directory authored

**Depends on:** T2 (SKILL.md procedure defines which references are named)

**Tests:**
- `ls packs/experience/.apm/skills/content-design/references/` shows ≥4 files
- Each file cited in SKILL.md procedure (`references/*.md`) exists (no dangling
  references)
- `python3 tools/lint-experience-agnostic.py` exits 0 after each file is added

**Approach:**
- `references/surface-routing.md` — the two sub-paths with their elicitation
  question sequences; acquisition elicitation covers: business objective, target
  audience, audience awareness level (Schwartz 1–5), primary action; product/reference
  elicitation covers: user task, completion definition, content format, known gaps in
  existing help material
- `references/narrative-arc.md` — names StoryBrand (seven-element arc: Character +
  Problem + Guide + Plan + CTA + Stakes + Success) and CCD (seven principles:
  Attention, Context, Clarity, Congruence, Credibility, Closing, Continuance) by
  name with applicability conditions: StoryBrand for cold/warm audiences (awareness
  levels 1–3); CCD for bottom-of-funnel audiences (levels 4–5). Names each principle
  without reprinting the framework text verbatim
- `references/content-hierarchy.md` — the must-say → probably-say → might-say
  prioritisation method per Nava PBC text-prototype model; definition of each tier
  (must-say = no-page-without-it; probably-say = helps most readers; might-say =
  edge-case detail); application to scroll section sequencing for acquisition surfaces
- `references/agentbundle-layout.md` — the RFC-0050 D6 three-tier path resolution for
  `content-brief` artifacts: config key `[experience] content_brief_dir`, default
  `docs/design/content/`, discover-by-marker `type: content-brief`; `content-brief`
  named as an extension to the pack's existing marker set

**Done when:** All referenced files exist; lint clean across all new files.

---

### T4: Content-brief asset template authored

**Depends on:** T3

**Tests:**
- `ls packs/experience/.apm/skills/content-design/assets/` shows
  `content-brief-template.md`
- `grep "type: content-brief" packs/experience/.apm/skills/content-design/assets/content-brief-template.md`
  returns a match
- `python3 tools/lint-experience-agnostic.py` exits 0

**Approach:**
- Mirror the shape of `packs/experience/.apm/skills/aesthetic-direction/assets/aesthetic-direction-template.md`
- Frontmatter: `type: content-brief`, `surface-type:`, `persona:`, `date:`
- Sections (acquisition variant): Surface Objective, Audience Awareness Level,
  Narrative Arc Selection, Scroll Sections (table: section | job | copy notes),
  Above-Fold Structure (headline contract, subheadline contract), CTAs
  (primary | label | action), Success Metric, Open Questions
- Sections (product/reference variant): Surface Objective, User Task, Content Format,
  Content Hierarchy (must-say / probably-say / might-say), Completion Metric,
  Open Questions
- Template uses placeholder text in square brackets `[…]` — no pre-written values
  or copy strings

**Done when:** Template exists with correct frontmatter and both variant section
sets; lint clean.

---

### T5: Evals authored; content-design added to pack.toml

**Depends on:** T2

**Tests:**
- `cat packs/experience/pack.toml | grep "content-design"` returns a match in
  `[pack.evals] skills`
- `ls packs/experience/.apm/skills/content-design/evals/` shows `eval_queries.json`
  and `evals.json`
- `python3 tools/lint-experience-agnostic.py` exits 0 on full `packs/experience/` tree

**Approach:**
- `eval_queries.json`: activation trigger phrases for pack-activation-evals
  (e.g. "what should this landing page say", "write a content brief for our onboarding
  flow", "what's the narrative arc for this marketing page", "what does this feature
  page need to communicate", "help me decide the above-fold structure")
- `evals.json`: Tier-4 LLM-judge rubric per ADR-0028 / RFC-0037; rubric checks:
  surface type declared, awareness level named (acquisition), narrative arc selected
  with applicability rationale, artifact path named, no copy strings produced (only
  direction)
- Add `"content-design"` to the `[pack.evals] skills` list in
  `packs/experience/pack.toml` (append — order is not semantically load-bearing for
  the evals list, but keep alphabetically adjacent to existing entries)

**Done when:** Lint clean; grep confirms pack.toml updated; both eval files present.

## Rollout

Pure-markdown skill addition — no infrastructure, no data migration, no
deployment sequencing. Ships as a normal PR to main; no flag or canary required.
The one reversibility concern: if `content-design`'s procedure violates ADR-0024
post-merge, the agnosticism lint catches it in CI and the fix is a follow-up PR
removing the violation — fully reversible.

## Risks

- **Procedure under-specifies the acquisition sub-path** — producing content briefs
  that are structurally complete but too vague to drive `map-screen-flow`. Mitigation:
  manual QA cold-prompt gate before T2 is declared done.
- **D3 boundary drift** — the acquisition sub-path creeps toward conversion analytics
  ("track CTA click-through"). Mitigation: anti-patterns explicitly refuse analytics
  outputs; the lint checks for values-table shape (a CRO measurement framework would
  likely produce one).
- **Eval phrases too narrow** — the activation evals only trigger on exact phrases,
  missing paraphrase variants. Mitigation: eval_queries.json covers 5+ distinct
  trigger phrasings.

## Changelog

- 2026-07-18: initial plan
