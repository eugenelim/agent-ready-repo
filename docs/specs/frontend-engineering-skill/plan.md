# Plan: frontend-engineering skill for core

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog.

## Approach

**Skill first, amendment second, build third.** The skill file must exist before
the work-loop amendment references it by name, so the tasks are ordered
accordingly. The skill is a single cohesive markdown file — no
`references/` subdirectory for v1. The work-loop amendment is additive only:
two short paragraphs inserted into existing sections, no deletions.

The riskiest part is the skill content itself: rules that are too vague provide
no improvement over the status quo; rules that are too prescriptive create
friction on legitimate variations. The bar is: every rule has a right/wrong form
that a future adversarial-reviewer can check mechanically.

## Constraints

- Skill must be framework-agnostic — readable by an implementer using plain
  HTML/CSS, Tailwind, or any other approach
- Work-loop amendment is additive only — existing behavior unchanged
- No new tooling shipped (CLI commands documented, not wrapped)
- `make build-self` is the final mechanical gate

## Construction tests

All tasks use goal-based or visual/manual QA modes — no TDD stubs apply.

Cross-cutting gate: after Task 3, `make build-self` exits 0 and
`diff packs/core/.apm/skills/frontend-engineering/SKILL.md .claude/skills/frontend-engineering/SKILL.md`
shows no unexpected differences (projection may add/strip a header comment).

## Tasks

### T1: Write the frontend-engineering skill file

**Depends on:** none

**Verification mode:** visual/manual QA

**Tests:**
Read the completed skill file top-to-bottom as if an implementer receiving it
cold. For each AC below, record pass or fail:

- AC1: valid frontmatter with `name:` and `description:` naming the trigger
- AC2: self-contained — no dangling forward-references to files that don't exist
- AC3: no framework-specific code: `grep -iE "react|vue|angular|jsx|usestate|useeffect|\bng-|@component|signal\(" packs/core/.apm/skills/frontend-engineering/SKILL.md` returns no hits
- AC4: named aesthetic reference section with canonical product list and
  purple-gradient failure explanation
- AC5: seed token block with three-tier architecture and `--ds-` prefix;
  all six minimum color roles present
- AC6: state matrix six-row table; skeleton rule and `aria-busy` pattern present
- AC7: print/PPT block with `@page`, `print-color-adjust`, `@media print`
  override, `pt` unit guidance, `page-break-*` rules
- AC8: AI aesthetic table with exactly 8 rows, each with a "why it's a problem"
  entry
- AC9: HTML rules — spot-check five (button/a/div rule; one `<main>`; form
  label rule; alt text rule; realistic content rule) — each has right/wrong form
- AC10: CSS rules — spot-check three (token-only, tabindex, hover/focus parity)
  — each has right/wrong form
- AC11: a11y rules — spot-check three (First Rule, reduced-motion guard,
  `aria-live` DOM-before-inject) — each has right/wrong form
- AC12–AC15: GATES section — confirm html-validate command is present and
  runnable, pa11y/axe command has CI flags, stylelint config snippet has at
  least the three named properties, visual QA checklist is enumerated
- AC16–AC17: Anti-patterns and Red flags sections present

**Approach:**

Write `packs/core/.apm/skills/frontend-engineering/SKILL.md` with these
sections in order:

**Frontmatter** (description must be a single line — multi-line descriptions
are silently truncated by lint-packs):
```
---
name: frontend-engineering
description: Load when a task's primary output is HTML, CSS, or JS. Provides design pre-flight, codified craft rules, and GATES verification commands for that surface.
---
```

**Section order:**
1. Overview (one paragraph: purpose, trigger, what it replaces, not-for cases)
2. PLAN phase — Design Pre-flight
   - Named aesthetic reference (canonical list, anti-adjective rule, why
     purple-gradient is the default, mapping of each reference to aesthetic goal)
   - Seed token block (three-tier architecture explanation, `--ds-` prefix,
     minimum viable property set as CSS snippet, print/PPT override block)
   - State matrix (six-row table with Wrong/Right columns, skeleton vs spinner
     rule, `aria-busy` + `aria-label` pattern)
3. EXECUTE phase — Craft Rules
   - "Avoid the AI Aesthetic" (8-row table: pattern / why it's a problem /
     production quality alternative)
   - HTML element selection rules (grouped by: interactive elements, landmark
     elements, headings, forms, images/media, content)
   - CSS rules (grouped by: values, selectors, z-index, layout, keyboard)
   - Accessibility rules (grouped by: ARIA discipline, dynamic state, contrast,
     motion, live regions, keyboard patterns, focus management)
4. GATES phase — Verification
   - html-validate (command, what it catches, no-browser note)
   - pa11y / axe-core (command with CI flags, WCAG level, headless note)
   - stylelint token enforcement (config snippet)
   - Visual QA checklist (enumerated items)
5. Anti-patterns / Common Rationalizations (declined-pattern register format)
6. Red flags (quick-scan list)

**Done when:** all 17 ACs above pass visual/manual QA read-through; no
framework-specific grep hits

---

### T2: Amend work-loop skill — add frontend trigger

**Depends on:** T1

**Verification mode:** goal-based check

**Tests:**
- `grep -n "frontend-engineering" packs/core/.apm/skills/work-loop/SKILL.md`
  returns matches in at least 2 locations (PLAN section and EXECUTE section)
- `grep -n "mandatory" packs/core/.apm/skills/work-loop/SKILL.md | grep -i "frontend"`
  returns at least one match (the mandatory upgrade in the design-intent pass)
- `git diff packs/core/.apm/skills/work-loop/SKILL.md` shows only additions,
  no deleted lines from the existing text (AC20a)
- `grep -c "risk-triggers:start" packs/core/.apm/skills/work-loop/SKILL.md`
  returns 1 and the block content is unchanged — spot-check that the
  risk-triggers wording between the comments is byte-identical to the original
  (AC20b); compare against `git show HEAD:packs/core/.apm/skills/work-loop/SKILL.md`
- The REVIEW specialist-reviewers roster paragraph (the one listing
  `security-reviewer`, `quality-engineer`, `experience-reviewer`) is
  byte-unchanged — confirm by diffing that section against HEAD (AC20c)
- `grep -ciE "primary output is HTML|HTML/CSS/JS primary output" packs/core/.apm/skills/work-loop/SKILL.md`
  returns ≥ 2 (trigger phrase present in both PLAN and EXECUTE amendments,
  AC21)

**Approach:**

Two targeted, additive amendments to
`packs/core/.apm/skills/work-loop/SKILL.md`:

**Amendment 1 — PLAN section, end of the "Pre-EXECUTE design-intent pass"
paragraph.** Current text ends with:
> "Applies in both light and full mode as a recommendation; the mandatory
> fresh-context gate (`experience-reviewer`) runs in REVIEW for full-mode work."

Append after this sentence:
> "**Frontend surface exception — mandatory, not recommended.** When the task's
> primary output is HTML, CSS, or JS (a new page, component, slide deck,
> dashboard, or standalone web artifact), this pass is mandatory in both modes:
> load the `frontend-engineering` skill inline before writing code. It carries
> the design pre-flight requirements (named aesthetic reference, seed token
> block, state matrix), the craft rules, and the GATES verification commands
> for that surface. The judgment call — whether the output is 'primary' HTML/CSS/JS
> or incidental — is the implementer's; when in doubt, load it."

**Amendment 2 — EXECUTE section, after the contract-grounding gate paragraph.**
The contract-grounding gate ends at `work-loop/SKILL.md:386`:
> `[`references/infra-verification.md`](references/infra-verification.md).)`

Insert a blank line then a new paragraph immediately after line 386:
> "**Frontend-triggered work (HTML/CSS/JS primary output).** When the frontend
> surface trigger fires, the `frontend-engineering` skill has already been
> loaded inline during PLAN. Its craft rules govern all HTML element selection,
> CSS token discipline, accessibility patterns, and state completeness during
> EXECUTE; its GATES section defines the verification commands to run at step 3."

**Done when:** all three grep tests pass; `git diff` shows only additions

---

### T3: Build and verify projection

**Depends on:** T1, T2

**Verification mode:** goal-based check

**Tests:**
- `make build-self` exits 0 (AC23)
- `ls .claude/skills/frontend-engineering/SKILL.md` exits 0 (AC24)
- `grep -c "frontend-engineering" .claude/skills/work-loop/SKILL.md` returns
  ≥ 2 (AC25 — work-loop projection reflects the amendment)
- `head -5 .claude/skills/frontend-engineering/SKILL.md` shows the frontmatter

**Approach:**
Run `make build-self`. If it fails, check the error — common causes are invalid
YAML frontmatter (unescaped colon in description; multi-line description) or
missing required fields. Fix at the source files only, never at projected paths.
Re-run until it exits 0.

**Done when:** all four one-liners pass

---

### T4: Add changelog entry

**Depends on:** T2

**Verification mode:** goal-based check

**Tests:**
- `grep -A3 "frontend-engineering" docs/product/changelog.md` returns an
  `Added` entry under `[Unreleased]`

**Approach:**
Add to the `### Added` block under `## [Unreleased]` in `docs/product/changelog.md`:

```
- **`frontend-engineering` skill added to core pack.** The work-loop now loads
  inline craft rules — design pre-flight, HTML semantics, CSS token discipline,
  accessibility, state completeness, and verification commands — whenever a
  task's primary output is HTML, CSS, or JS. The design-intent pass is mandatory
  (not a recommendation) for that surface.
```

**Done when:** grep test passes

---

## Rollout

Single PR to `main`. No flag-gating. The skill is additive; the work-loop
amendment is additive. Adopters who run `make build-self` pick it up
automatically at next install.

## Risks

- **Skill content too vague:** if rules aren't specific enough (right/wrong
  form), they provide no improvement. Mitigation: adversarial-reviewer pass
  with an explicit "are these rules specific or just principles?" check.
- **Work-loop amendment too broad:** if the frontend trigger is too broadly
  defined, it fires on every template/docs HTML touch and creates friction.
  Mitigation: the amendment text explicitly scopes to "primary output" and
  gives the implementer the judgment call.
- **build-self drift:** if the skill's frontmatter is malformed, build-self
  fails silently or noisily. Mitigation: run build-self as Task 3, before
  declaring done.

## Changelog

- 2026-07-16: initial draft
