# Spec: frontend-engineering skill for core

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0023](../../adr/0023-reviewer-ceiling-scopes-core-code-review-lenses.md)
  (reviewer-ceiling — no new reviewer role); [ADR-0042](../../adr/0042-agent-additions-keyed-to-loop-and-work-type.md)
  (agent additions keyed to loop and work-type — context injection over domain
  subagents); [ADR-0047](../../adr/0047-experience-reviewer-as-work-loop-gate.md)
  (experience-reviewer gate — this skill supplements but does not replace it)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full (structural change — new module boundary in `packs/core`; public
interface adopted by the work-loop and all downstream agents; multi-task
dependency between skill authorship and work-loop amendment)

## Objective

Add a `frontend-engineering` depth skill to `packs/core` that the work-loop
loads inline when a task's primary output is HTML, CSS, or JS. The skill gives
the implementing agent codified, specific rules — not vague principles —
covering design pre-flight, HTML semantics, CSS token discipline, accessibility,
state completeness, and verification tooling. It also amends the work-loop's
PLAN section to make the design-intent pass **mandatory** (not a
recommendation) when the frontend trigger fires.

**The problem this solves:** AI-generated frontend code is consistently
technically correct but visually inconsistent, semantically wrong, and
inaccessible by default. This is not a subagent problem — domain-partitioned
subagents add coordination overhead and do not outperform context injection on
sequential coding tasks. The right lever is codified rules loaded inline before
EXECUTE begins.

## Acceptance Criteria

### Skill file

- [x] AC1: Skill exists at `packs/core/.apm/skills/frontend-engineering/SKILL.md`
  with valid frontmatter: `name: frontend-engineering` and a `description:` that
  names the trigger condition ("HTML, CSS, or JS as a primary output artifact")
- [x] AC2: Skill is self-contained — no unexplained terms and no dangling
  references to files or concepts not defined within the skill; verified by
  reading it cold and confirming every cross-reference resolves
- [x] AC3: Skill is framework-agnostic — the following grep returns no hits:
  `grep -iE "react|vue|angular|jsx|usestate|useeffect|\bng-|@component|signal\(" packs/core/.apm/skills/frontend-engineering/SKILL.md`

### Design pre-flight section (PLAN phase)

- [x] AC4: **Named aesthetic reference** — skill requires a product name from a
  named canonical set (Linear, Stripe, Vercel, Raycast, Arc, Notion, Toss),
  explains why vague adjectives ("beautiful", "modern") fail (purple-gradient
  default), and maps each reference to its aesthetic goal
- [x] AC5: **Seed token block** — skill specifies the three-tier token
  architecture (Primitive → Semantic → Component; one-way dependency only),
  names the `--ds-` prefix convention, and enumerates the minimum viable
  property set: color roles (`--ds-color-surface`, `--ds-color-on-surface`,
  `--ds-color-primary`, `--ds-color-on-primary`, `--ds-color-error`,
  `--ds-color-outline`), 8-step spacing scale (`--ds-space-1` through
  `--ds-space-8`, 4 px base), type scale (size / weight / line-height),
  radius scale, shadow scale, motion tokens (duration + easing)
- [x] AC6: **State matrix** — skill requires a six-row table for every async
  component: content / loading / empty / error / partial / disabled. Rules: use
  skeleton screen (not spinner) when layout is predictable; use
  `aria-busy="true"` and `aria-label="Loading <thing>"` on the skeleton
  container; empty state requires illustration + label + CTA; error state
  preserves prior content and offers retry; disabled state renders visibly with
  `aria-disabled="true"` and an explanation
- [x] AC7: **Print/PPT token block** — skill includes a conditional section (when
  output targets PPT/PDF) covering: `@page { size: 960px 540px; margin: 0; }`,
  `-webkit-print-color-adjust: exact; print-color-adjust: exact`,
  `@media print` override block for surface/shadow tokens, `pt` for
  typographic values, `page-break-after: always` for slide boundaries,
  `page-break-inside: avoid` on headings/figures/tables, and a warning that
  `box-shadow` and `text-shadow` are unreliable in print renderers

### EXECUTE craft rules

- [x] AC8: **"Avoid the AI Aesthetic" table** — skill contains an 8-row
  anti-pattern table (purple/indigo palette, excessive gradients, rounded
  everything, generic hero sections, lorem ipsum copy, oversized equal padding,
  uniform card grids, shadow-heavy design) with a "why it's a problem" column
  for each
- [x] AC9: **HTML element rules** — all rules are specific right/wrong form, not
  vague principles, covering:
  - Interactive: `<button>` for actions, `<a href>` for navigation; never
    `<div onclick>`; never cross them
  - Landmarks: exactly one `<main>`, one `<h1>`; sequential heading levels
    (never skip); `<section>` only when it has a heading; multiple `<nav>`
    requires `aria-label`
  - Forms: every `<input>`/`<textarea>`/`<select>` requires `<label for>` or
    `aria-labelledby`; `placeholder` is not a label; `aria-describedby` for
    errors; `autocomplete` on personal-data fields; `<fieldset>`+`<legend>` for
    checkbox/radio groups
  - Images: `alt=""` for decorative, descriptive text for informational (no
    "image of" prefix); CSS `background-image` for decorative backgrounds;
    SVG as image requires `role="img"` + `<title>`; decorative SVG requires
    `aria-hidden="true"`
  - Content: use realistic-length placeholder text, not lorem ipsum
- [x] AC10: **CSS rules** — specific, covering: token-only values (no hardcoded
  hex/rgb/hsl; all via `var(--ds-*)`); z-index via named custom property scale;
  unitless line-height; class selectors only (no `#id`); max 3 nesting levels;
  no qualified selectors; `tabindex` never positive; every `:hover` has matching
  `:focus-visible`; never `outline: none` without visible replacement
- [x] AC11: **Accessibility rules** — specific right/wrong form, covering:
  - First Rule of ARIA: use native HTML; ARIA only when HTML is insufficient;
    specific violation examples (never `<div role="button">` when `<button>`
    works)
  - Dynamic ARIA: `aria-expanded`, `aria-selected`, `aria-sort` must update on
    state change — they are not static attributes
  - Never add `aria-label` to elements with visible text (creates
    screen-reader/voice-control mismatch)
  - WCAG contrast floor: 4.5:1 body text, 3:1 large text (≥18 pt or ≥14 pt
    bold), 3:1 UI components (borders, focus rings, icons)
  - Reduced-motion guard: every `animation`/`transition`/`transform` wrapped in
    `@media (prefers-reduced-motion: no-preference)` (default: no motion)
  - `aria-live` container must be in DOM before content is injected; `polite`
    for informational, `assertive` + `aria-atomic="true"` for errors
  - APG modal pattern (concise): `role="dialog"`, `aria-modal="true"`,
    `aria-labelledby`, focus first focusable on open, Tab/Shift+Tab cycle inside
    only, Escape closes, focus returns to invoking element
  - Programmatic focus required after: modal open/close, route change, inline
    error appearance

### GATES verification

- [x] AC12: **html-validate** — skill provides the exact runnable command:
  `npx html-validate --preset standard,a11y --max-warnings 0 <file.html>`,
  notes it requires no browser, and names what it catches (landmark structure,
  heading hierarchy, label associations, ARIA role validity, alt presence)
- [x] AC13: **pa11y / axe-core** — skill provides an exact runnable command for
  at least one Chromium-based tool with CI-safe flags (`--no-sandbox`) and the
  correct WCAG tag (`WCAG2AA` / `wcag21aa`), and notes that Chromium runs
  headless without a display server
- [x] AC14: **stylelint token enforcement** — skill provides an exact
  `stylelint-declaration-strict-value` config snippet covering at minimum
  `color`, `background-color`, and `font-size` properties
- [x] AC15: **Visual QA checklist** — skill enumerates an agent-executable
  checklist (no tooling required) covering: all state variants present,
  no hardcoded values in CSS, print output correct if PPT/PDF context,
  screenshot taken and observed

### Anti-patterns and red flags

- [x] AC16: **Anti-patterns / Common Rationalizations** section names at least
  five refused rationalizations in declined-pattern register format, drawn from:
  "accessibility is a nice-to-have", "we'll make it responsive later",
  "this is just a prototype", "the AI aesthetic is fine for now",
  "I'll add the empty/error states later"
- [x] AC17: **Red flags** section provides a quick-scan list for review gates,
  covering: inline styles or magic pixel values, missing any state (empty/error/
  loading), no keyboard navigation, color as sole state indicator, generic AI
  look (purple gradients/oversized cards)

### Work-loop amendment

- [x] AC18: Work-loop PLAN section amended so the design-intent pass is
  **mandatory** (not "recommendation") when the frontend trigger fires — task's
  primary output is HTML, CSS, or JS — and names loading `frontend-engineering`
  inline as the required action
- [x] AC19: Work-loop EXECUTE section amended with one sentence routing
  implementers to the `frontend-engineering` skill's craft rules and GATES
  commands when the frontend trigger fires
- [x] AC20: The work-loop amendment adds text only — verified by: (a) `git diff`
  shows zero deleted lines in `work-loop/SKILL.md`; (b) the risk-triggers block
  (`<!-- risk-triggers:start -->` … `<!-- risk-triggers:end -->`) is
  byte-unchanged; (c) the REVIEW specialist-reviewers roster paragraph is
  byte-unchanged
- [x] AC21: The trigger concept "primary output is HTML, CSS, or JS" (or
  equivalent — "HTML/CSS/JS primary output" is accepted) appears in both
  work-loop amendment sites; verified by:
  `grep -ciE "primary output is HTML|HTML/CSS/JS primary output" packs/core/.apm/skills/work-loop/SKILL.md`
  returns ≥ 2. Consistency within the skill file itself (frontmatter + Overview)
  is verified by the T1 visual/manual QA read-through

### Changelog

- [x] AC22: `docs/product/changelog.md` `[Unreleased]` section has an `Added`
  entry noting the new `frontend-engineering` skill and the mandatory
  design-intent pass for the frontend trigger

### Build and projection

- [x] AC23: `make build-self` exits 0 after the new skill is added
- [x] AC24: Skill projects to `.claude/skills/frontend-engineering/SKILL.md`
  (confirmed by path existence after build-self)
- [x] AC25: Regenerated `.claude/skills/work-loop/SKILL.md` reflects the
  work-loop amendment (confirmed by `grep -c "frontend-engineering"
  .claude/skills/work-loop/SKILL.md` returning ≥ 2)

## Boundaries

**In scope:**
- New file: `packs/core/.apm/skills/frontend-engineering/SKILL.md`
- Amendment: `packs/core/.apm/skills/work-loop/SKILL.md` (PLAN and EXECUTE
  sections only — additive prose, ~3–5 sentences total)
- Amendment: `docs/product/changelog.md` (`[Unreleased]` entry only)
- Generated outputs: `.claude/skills/frontend-engineering/SKILL.md` (new),
  `.claude/skills/work-loop/SKILL.md` (regenerated with amendment)
- Core pack version bump (`pack.toml` + `.claude-plugin/plugin.json` → 0.11.0)
  and `marketplace.json` regeneration — user confirmed ship

**Out of scope:**
- Experience pack skills (aesthetic-direction, design-system-foundations,
  experience-reviewer) — not touched; they remain optional
- Other core skills (security-checklists, operational-safety, contract-
  acquisition, bug-fix, new-spec) — not touched
- Verification scripts under `tools/` — CLI commands documented in skill,
  not shipped as tooling
- `references/` subdirectory for the new skill — single cohesive file for v1
- Framework-specific content (React hooks, JSX, Vue SFCs) — not included
- Per-package `CHANGELOG.md` and `ROADMAP` files — not touched

## Testing Strategy

All tasks use **goal-based check** or **visual/manual QA** — the artifact is
markdown, not testable logic; no TDD mode applies.

- Task 1 (write skill): visual/manual QA — read the skill top-to-bottom as if
  an implementer receiving it; each AC2–AC17 is a checklist item verified by
  inspection; framework-agnosticism verified by grep (AC3)
- Task 2 (amend work-loop): goal-based check — greps for trigger language at
  two locations; risk-triggers and reviewer-roster spot-checks for unchanged
  bytes (AC20a/b/c); trigger-phrase consistency grep (AC21)
- Task 3 (build-self): goal-based check — `make build-self` exits 0;
  both projected files exist; work-loop projection grep passes (AC25)
- Task 4 (changelog): goal-based check — `grep` for the entry under
  `[Unreleased]` (AC22)

## Assumptions

**Trio:**
- Touching: `packs/core/.apm/skills/frontend-engineering/SKILL.md` (new),
  `packs/core/.apm/skills/work-loop/SKILL.md` (PLAN + EXECUTE only)
- Done when: all ACs pass, `make build-self` green, adversarial-reviewer
  returns Clean
- Not changing: any existing trigger condition, mode selection, gate sequence,
  reviewer roster, or other core skill

**Resolve-vs-surface disposition (pre-EXECUTE):**
- "Does the work-loop amendment require loop-cohort approve-plan?" → Resolved:
  yes — spec amendment + new module boundary fires the pre-EXECUTE adversarial
  review trigger per the work-loop's own rules
- "Should print/PPT content be a `references/print-ppt.md` depth file?" →
  Resolved: no — inline is right for v1; depth file is a follow-up if adopters
  request it
- "Should the frontend trigger fire on partial HTML (a component in a
  server-rendered template)?" → Resolved: yes — "primary output" judgment is
  left to the implementer; the skill notes this

## Declined patterns

- Tempted to add a `references/` subdirectory (like security-checklists
  modules): declining — v1 lacks adopter feedback on which sections need depth;
  single cohesive file is right
- Tempted to add verification scripts to `tools/` (html-validate wrapper,
  pa11y runner): declining — CLI commands are documented; tooling is a follow-up
  if adopters request it
- Tempted to make the trigger mandatory for all HTML edits (not just primary
  output): declining — incremental edits to existing HTML are covered by the
  existing work-loop design-intent recommendation
- Tempted to include React-specific examples (hooks, JSX, component file
  colocation): declining — core pack is framework-agnostic; React content
  belongs in an opt-in react pack
- Tempted to add domain-partitioned subagents (frontend-engineer,
  backend-engineer): declining — research is clear that context injection
  outperforms domain-partitioned subagents for sequential coding tasks
