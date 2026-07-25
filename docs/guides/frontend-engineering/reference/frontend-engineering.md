---
title: Frontend Engineering Pack
description: Reference — all 9 skills and the frontend-reviewer agent in the frontend-engineering pack.
---

# `frontend-engineering` — the skills and the reviewer

The `frontend-engineering` pack installs 9 skills and one reviewer agent.
This page gives one-line descriptions and the correct trigger for each.

---

## Primary surface skill

### `frontend-engineering`

The entry point for all frontend work. Four modes — create (new surface),
retrofit (improving existing), audit (review only), verify (run gates).
Provides the design pre-flight (named aesthetic reference, genre routing,
seed token block, state matrix), craft rules, GATES verification commands,
and evidence manifest format. Load this skill whenever a task's primary output
is HTML, CSS, or JS.

**Load when:** the task's primary output is HTML, CSS, or JavaScript.

---

## Atomic craft skills

Load the skill that matches the specific concern of the task. Do not load
multiple atomic craft skills for a single task — load the one that addresses
the task's primary concern.

### `token-architecture`

Design and govern a three-tier CSS custom property token system
(primitive → semantic → component), including semantic alias layers,
light/dark theming, and DTCG-compatible source generation.

**Load when:** the primary task is designing or auditing a token system —
not seeding a token block for a single surface (the seed block in
`frontend-engineering` step 2 covers that).

### `a11y-engineering`

Deep accessibility engineering beyond automated tooling — focus management
architecture, ARIA role correctness under dynamic mutation, live-region
discipline, keyboard contract specification, and manual WCAG 2.2 AA
verification for the two criteria automated tools miss (2.4.11 Focus
Appearance, 2.5.8 Target Size).

**Load when:** accessibility is the primary task — a dedicated audit,
retrofitting broken patterns, or designing a complex interaction
(combobox, data grid, drag-and-drop) where the a11y contract is the
central deliverable.

**Near-miss:** for routine component work, use the accessibility section in
`frontend-engineering` — it covers baseline ARIA patterns and the WCAG
contrast floor. `a11y-engineering` is for the dedicated a11y task.

### `fe-performance`

Measure, diagnose, and remediate Core Web Vitals and asset budget violations
using structured profiling, causality analysis, and repeatable remediation
patterns.

**Load when:** the primary output is a CWV diagnosis or performance remediation
— not when Lighthouse runs as a gate at the end of a normal build (use the
GATES section of `frontend-engineering` for that).

### `rendering-strategy`

Select and implement the correct rendering model (CSR/SSR/SSG/ISR/RSC) for
each route based on data-access patterns, performance targets, and
personalization requirements.

**Load when:** selecting or auditing the rendering architecture of a route or
surface — not for routine component authoring where the rendering model is
already decided.

### `component-contract`

Design a UI component's public interface — props/slots/events, controlled
vs. uncontrolled ownership, composition patterns, lifecycle contract, and
usage documentation — before writing any implementation.

**Load when:** designing a new shared component (one that will be used by
multiple callers) before writing any implementation code.

### `responsive-layout`

Design and implement adaptive layouts using CSS Grid, Flexbox, container
queries, and fluid typography/spacing — the craft layer for layouts that work
correctly across all viewport sizes without JavaScript.

**Load when:** the primary task is designing or debugging a layout that must
work across breakpoints. Not for routine margin adjustments on an already-responsive surface.

### `css-architecture`

Organize CSS at scale using cascade layers, scoping strategies, and
specificity budgets — preventing specificity wars, enabling safe deletion,
and making CSS that other engineers can reason about.

**Load when:** setting up CSS architecture for a new codebase, or auditing
and refactoring CSS in an existing one with specificity conflicts or
hard-to-predict cascade behavior.

### `fe-status`

Orient skill — read the current surface's evidence manifest, known exceptions,
and gate history to return a surface-state summary against the frontend
engineering quality floor.

**Load when:** starting work on an existing surface to orient without reading
all the code. Returns a structured summary of covered states, gate results,
known exceptions, and the recommended next action.

---

## The reviewer agent

### `frontend-reviewer`

A **forked-context, read-only reviewer** for diffs whose primary output is
HTML/CSS/JS. Applies the fe-diff-review lens across five areas:

| Lens | What it checks |
|---|---|
| CSS token drift | Hardcoded hex/rgba/px/rem values where `--ds-*` tokens should be used |
| ARIA mutation completeness | `aria-expanded`, `aria-selected`, `aria-sort`, `aria-checked` set in HTML but never updated in JS |
| State coverage regression | States from the 18-state matrix present before the diff but absent after |
| WCAG 2.2 manual items | 2.4.11 Focus Appearance (ring size and contrast), 2.5.8 Target Size (touch target ≥24×24 CSS px) |
| CWV regression signals | Synchronous scripts, unsized images, lazy LCP candidates, route chunk size increase >10KB |

**Not in scope:** spec/plan drift (adversarial-reviewer), testability
(quality-engineer), aesthetic taste (experience-reviewer), security
boundaries (security-reviewer).

**When pack is absent:** the orchestrator records a named skip —
`frontend-reviewer: pack not installed; review skipped`. Absence is not
a silent pass.

---

## The quality floor

All surfaces built with this pack are held to one shared quality floor:

1. Handle all applicable states from the 18-state matrix.
2. WCAG 2.2 AA — automated `wcag21aa` gate plus two manual checks
   (2.4.11 and 2.5.8).
3. Token discipline — no hardcoded values outside the `:root` primitive block.
4. Evidence manifest — completion requires a manifest.
