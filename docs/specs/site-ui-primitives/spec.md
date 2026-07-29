# Spec: site-ui-primitives

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none <!-- ADR-NNNN, RFC-NNNN, or "none" -->
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The platform site's web/ and docs-site/ renderers share design tokens and
aesthetic direction but lack the reusable component vocabulary needed to
render task-first, conversation-first product documentation coherently.
Inline styling is duplicated across at least four components, interactive
primitives (copy button, tab switcher) are embedded and not extractable,
and no components exist for the concepts unique to agentic product
documentation: agent clarification dialogs, write-consequence confirmations,
decision gates, journey rails, and skill reference records.

This spec defines sixteen reusable UI primitives — their content models,
state vocabulary, interaction contracts, accessibility requirements, and
responsive behavior — across both renderers. The renderers share semantic
token names and component contracts; where code cannot be shared, each
renderer has its own implementation but the same observable behavior.

The aesthetics must satisfy the "precision authority" ranked goal from
`docs/specs/platform-site/aesthetic-direction.md`: every primitive reads as
specific and traceable, avoids decorative chrome, and communicates
consequence explicitly rather than through color alone.

Phase 1's Product Documentation authoring contract is assumed complete and
provides the source content that these primitives render.

## Boundaries

### Always do

- Reference `--ds-*` semantic tokens exclusively; never raw primitives or
  hex values in component CSS.
- Include visible text, an accessible name, and a non-color semantic
  indicator for every state.
- WCAG 2.2 AA is the accessibility baseline; every AC asserting "accessible"
  means this standard.
- Run `astro build` for both web/ and docs-site/ before closing any task.
- Add new Astro components to the appropriate renderer's existing
  `src/components/` directory — no new top-level directories.
- Use `<style>` scoped blocks inside each `.astro` file for component CSS.
- For docs-site components, handle both light and dark Starlight color
  schemes by referencing `--sl-color-*` variables mapped through
  `starlight.css`.
- Extract the `.scope-chip` duplicated style into `StatusChip.astro` and
  replace inline copies in PackCard.astro, PackHero.astro, JourneyHero.astro,
  PackCatalogue.astro, and web/src/pages/catalogue/index.astro in the same PR.

### Ask first

- Any change to `web/src/styles/tokens.css` — it is the shared token source
  of truth for both renderers.
- Any new npm devDependency added to either web/package.json or
  docs-site/package.json.
- Any new component that introduces a JavaScript runtime dependency in a
  path where Astro would currently produce zero JS.
- Any change to `docs-site/src/styles/starlight.css` (Starlight theme).
- If the Phase 1 Product Documentation authoring contract artifact cannot be
  located before T19 (fixture page), ask before proceeding — the fixture's
  realistic content depends on it.

### Never do

- Add a parallel token system or hardcode visual values outside tokens.css.
- Redesign global navigation, the homepage hero, or the site footer.
- Retrofit Atlassian pages or change guide source ownership.
- Introduce a new top-level directory without an RFC.
- Build a public component library product or standalone Storybook.
- Use icons or color as the sole accessibility signal for any state.
- Add a modal dialog for WriteConfirmation unless the interruption is
  justified — use an in-flow confirmation panel by default.
- Create a fixture page that is indexed by search engines or linked from
  site navigation (it must carry `<meta name="robots" content="noindex">`
  and be excluded from the Astro sitemap).

## Testing Strategy

| Behavior | Mode | Surface |
|---|---|---|
| Token extension resolves without CSS syntax errors | Goal-based | `astro build` (both renderers) |
| Badge/chip components render correct visible text for each state | TDD | vitest unit (jsdom) |
| Badge/chip components carry correct ARIA role and accessible name | TDD | vitest + axe-core matcher |
| PromptBlock copy action writes to clipboard and announces success | Visual/manual QA | Browser interaction test (playwright) |
| TaskSwitcher keyboard navigation (Tab, Enter, arrow keys) | Visual/manual QA | Browser interaction test (playwright) |
| JourneyRail accordion behavior at 390px | Visual/manual QA | Browser interaction + screenshot |
| WriteConfirmation in-flow panel shows exact fields and counts | Visual/manual QA | Browser interaction test (playwright) |
| DecisionBand has greater visual prominence than adjacent content | Visual/manual QA | Screenshot review |
| All components pass axe-core automated accessibility checks | Goal-based | axe-core on fixture page |
| All components render correctly at 1440, 1024, 390px | Visual/manual QA | Playwright screenshot at each width |
| Both astro builds complete without errors | Goal-based | `astro build` |
| Fixture page is not indexed | Goal-based | grep for noindex in built output |
| No existing public pages regress | Visual/manual QA | Screenshot diff against baseline |

**FE pre-flight:** skipped — frontend-engineering pack exists at
`packs/frontend-engineering/` but its SKILL.md is not installed in
`.claude/skills/`. Proceeding without pack-guided pre-flight.

## Acceptance Criteria

- [x] AC1: All sixteen primitives (PageHero, PageMeta, TaskSwitcher,
  PromptBlock, CopyPrompt, AgentClarification, ExpectedResult/ResultPreview,
  StatusChip, ReadWriteBadge, CoverageBadge, PermissionBadge, DecisionBand,
  JourneyRail, SkillRecord, WriteConfirmation, NextAction) have explicit
  content models and interaction contracts implemented in web/ and/or
  docs-site/.

- [x] AC2: Shared semantic state tokens — informational, read-only, draft,
  proposed-write, confirmed-write, approval-required, complete, partial,
  blocked, failed, unavailable — are defined in tokens.css and applied
  consistently across all badge and status components in both renderers.

- [x] AC3: PromptBlock is visually distinct from a code block: different
  background, left-border treatment, speaker label, and font rendering; a
  reviewer shown both in isolation can identify which is which without
  instructions.

- [x] AC4: ReadWriteBadge communicates read-write consequence in visible text
  (not icon or color alone) for all six states: Read-only, Draft only,
  Proposed write, Confirmed write, Publish, Destructive action.

- [x] AC5: CoverageBadge provides a visible explanation or accessible
  description for all five states: Complete result, Filtered result, Partial
  result, Capped result, Permission-limited result.

- [x] AC6: DecisionBand is visually more prominent than adjacent explanatory
  content (e.g. greater background contrast, left border, or colored band)
  and includes decision summary, consequence text, primary action, safe
  secondary action, and protected/unchanged scope indicator.

- [x] AC7: WriteConfirmation shows exact objects, exact fields, protected
  fields, total write count, consequence statement, cancel, and confirm; the
  in-flow panel form is used unless a modal interruption is explicitly
  justified.

- [x] AC8: JourneyRail at desktop (≥768px) shows connected stages with
  current, completed, and upcoming states and visible decision boundaries; at
  mobile (<768px) it renders as an accessible accordion or sequential stage
  list — not a compressed desktop rail. Screenshots verified at 1440px, 1024px,
  390px, and at least 430px (material mobile risk).

- [x] AC9: SkillRecord uses aligned rows or compact records (not large
  equal-weight cards) to display skill name, natural user goals, reads,
  writes, returns, limits, and likely follow-up.

- [x] AC10: Each primitive is authorable through one supported Astro-native
  syntax per renderer (Astro component props for web/; Astro component props
  or Starlight aside/MDX for docs-site/); no raw HTML is required for common
  authoring use. Verified by T23 (maintainer guide includes authoring examples
  that are actually used in the fixture page and docs-site components).

- [x] AC11: A deterministic fixture page at `web/src/pages/primitives-fixture.astro`
  renders all sixteen primitives across their material states (including long
  content, partial results, errors, read/write states) and carries
  `<meta name="robots" content="noindex">` and is excluded from the sitemap.

- [x] AC12: Automated axe-core accessibility checks pass on the fixture page
  (T19), at least one existing public web page (T20), and at least one built
  documentation page (T21) with no critical violations; confirmed exceptions
  (if any) are documented in this spec with the specific violation and reason.

- [ ] AC13: All components verified at 1440px, 1024px, and 390px viewports
  via Playwright screenshots; components with material mobile risk additionally
  verified at 375px and 430px. Screenshots committed under
  `docs/specs/site-ui-primitives/notes/screenshots/`.

- [x] AC14: Keyboard-only navigation is verified for TaskSwitcher, PromptBlock
  copy action, JourneyRail accordion, WriteConfirmation, and DecisionBand
  actions — each documented in notes with the input sequence and observed
  result.

- [x] AC15: Neither astro build for web/ nor docs-site/ introduces new
  console errors, network errors, or layout shift relative to the pre-change
  baseline.

- [x] AC16: Maintainer documentation exists under `docs/guides/` covering
  when to use each primitive, card-use rules, source syntax, state semantics,
  responsive expectations, accessibility expectations, and common
  anti-patterns with examples.

- [x] AC17: No public page content has been broadly rewritten; the scope of
  changes is strictly the new component files, the token extension, and
  wiring of new components into pages/docs that use them.

## Assumptions

- Technical: Astro 7.1.0 renders both web/ (marketing) and docs-site/
  (Starlight docs); separate package.json per renderer (web/package.json,
  docs-site/package.json).
- Technical: Design tokens use a 3-tier Primitive → Semantic → Component
  architecture in web/src/styles/tokens.css; docs-site tokens are a
  build-time copy via tools/build-site.py (docs/specs/platform-site/
  design-system-foundations.md).
- Technical: No test infrastructure exists in either renderer — no
  vitest/playwright/jest/cypress config, no test devDependencies. Task zero
  is establishing the test runner.
- Technical: Badge/chip style is duplicated verbatim in PackCard.astro,
  PackHero.astro, JourneyHero.astro, PackCatalogue.astro, and
  web/src/pages/catalogue/index.astro (grep-verified 2026-07-28); extracting
  StatusChip is a clean refactor with no behavior change.
- Technical: CopyButton is embedded in InstallTerminal.astro (clipboard API,
  amber states, 2s flash) — extraction preserves existing behavior.
- Technical: docs-site uses @astrojs/starlight 0.41.4 with light/dark mode
  switching; Expressive Code handles all code blocks.
- Technical: frontend-engineering SKILL.md not installed; FE pre-flight
  named-skipped.
- Technical: Grounded aesthetic direction established at
  docs/specs/platform-site/aesthetic-direction.md — Option B, amber-gold,
  "precision authority" dominant goal.
- Process: platform-site spec is Shipped; design-system-foundations contract
  is authoritative for all token decisions.
- Process: New component files within existing web/src/components/ and
  docs-site/src/components/ do not require RFC.
- Product: Phase 1 Product Documentation authoring contract is established
  (stated assumption in brief; proceeding without locating specific artifact).
