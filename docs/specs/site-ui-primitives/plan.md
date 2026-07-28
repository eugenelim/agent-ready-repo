# Plan: site-ui-primitives

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Executing | Done -->

## Approach

Implement in six waves ordered by dependency depth. Every wave is gated by
`astro build` passing for both renderers. Wave 0 is a prerequisite for all
subsequent waves; Wave 5 is integration-only and closes all remaining ACs.

**Architecture decision — renderer isolation with shared contracts.**
Both renderers are separate Astro projects with separate npm installs; they
cannot directly import each other's component files. They share: token names
(`--ds-*`), content model (component props interface), state vocabulary
(enum values), HTML semantics (element choices), interaction contract
(keyboard behavior), and visual acceptance tests (screenshot baselines). Code
is duplicated across renderers only where necessary; where a component is
web/-only (journey pages) or docs-site/-only (guide pages), one implementation
suffices.

**docs-site component strategy.** Starlight uses `--sl-color-*` variables for
its own color scheme; `docs-site/src/styles/starlight.css` already maps these
to `--ds-*` tokens. New docs-site components should reference `--sl-color-*`
for theme-sensitive surfaces (so they adapt to Starlight's light/dark switch)
and `--ds-*` directly only for values the Starlight theme does not control
(spacing, radius, motion, typography scale).

**Testing architecture.** Zero infrastructure exists today; T1 wires vitest +
jsdom + axe-core for unit/a11y tests (web/ only); T20 wires Playwright for
browser interaction and screenshot tests (web/); T21's docs-site axe check
runs the axe-core CLI against `astro preview` of docs-site — no docs-site
vitest infra required.

**Simplification scope.** StatusChip extraction replaces inline `.scope-chip`
duplication in five files (PackCard, PackHero, JourneyHero, PackCatalogue,
web/src/pages/catalogue/index.astro) in the same PR as T2, under the
bundled-fixes carve-out.

## Constraints

- All token values sourced from `web/src/styles/tokens.css` — never raw hex.
- Starlight component overrides follow the `components:` API in
  `docs-site/astro.config.ts`.
- New devDependencies require explicit ask-first approval before adding.
- No new top-level directories without RFC.

## Construction tests

Cross-cutting (per-task tests are in each task's `Tests:` subsection):

**Integration:** build verification — after each wave, `cd web && npm run build`
and `cd docs-site && npm run build` must both exit 0.

**Manual verification:** Keyboard-only walkthrough of TaskSwitcher, PromptBlock
copy, JourneyRail accordion, WriteConfirmation, and DecisionBand using only Tab,
Shift+Tab, Enter, Space, and arrow keys; document the input sequence and outcome
for each in `notes/keyboard-qa.md`.

## Design (LLD)

### Design decisions

- **Shared contracts, renderer-isolated code.** Avoids a shared npm package
  (build complexity) and symlinks (fragile). Component props interfaces are
  documented here; each renderer implements them separately. Traces to: AC1,
  AC10.
- **Semantic state tokens in tokens.css Tier 2.** State colors map one color
  role to one semantic role (success/danger/warning/info/neutral) — not a
  rainbow palette. Reviewer/purple is deferred (no AC maps to it). Amber-gold
  accent is NOT used for states; the existing accent is for CTA and stat only.
  Traces to: AC2.
- **StatusChip is the state-display atom.** ReadWriteBadge, CoverageBadge,
  PermissionBadge all compose StatusChip (pass `state` + `label`); they add
  semantic meaning and explicit consequence text on top. Traces to: AC2, AC4,
  AC5.
- **PromptBlock uses a left amber border + light tinted background.** Code
  blocks (Expressive Code in docs-site; terminal style in web/) use
  monospace, dark background, and no left-border treatment. PromptBlock uses
  Inter (sans-serif), `--ds-accent-subtle` fill, amber left border, and a
  speaker label. The contrast is deliberate and sufficient for AC3.
  Traces to: AC3.
- **JourneyRail uses `<details>/<summary>` for mobile accordion.** Native
  HTML disclosure; zero JS required; Starlight already demonstrates this
  pattern in GateDetail.astro (web/ has a `<details>/<summary>` pattern for
  expandable gate cards). Traces to: AC8.
- **WriteConfirmation is an in-flow panel, not a `<dialog>`.** The spec
  Boundaries section forbids modal unless justified. In-flow panel avoids
  focus-trap complexity and is sufficient for the non-blocking confirmation
  use case. Traces to: AC7.
- **Fixture page excluded from sitemap.** Astro's `@astrojs/sitemap` respects
  `noindex` meta tags if configured with `filter`; we add the fixture URL to
  the sitemap exclusion list in `astro.config.ts`. Traces to: AC11.

### Component / module decomposition

**web/ component tree:**
```
web/src/components/primitives/
  StatusChip.astro         — state + label atom (replaces .scope-chip copies)
  ReadWriteBadge.astro     — composes StatusChip, adds consequence text
  CoverageBadge.astro      — composes StatusChip, adds explanation
  PermissionBadge.astro    — composes StatusChip, communicates access
  CopyButton.astro         — extracted from InstallTerminal; standalone
  CopyPrompt.astro         — copy-ready prompt string with CopyButton
  PromptBlock.astro        — speaker + multiline prompt + CopyPrompt + status
  AgentClarification.astro — question + options + reason + blocked indicator
  DecisionBand.astro       — decision summary + consequence + actions + scope
  ExpectedResult.astro     — summary + counts + records + status + follow-up
  NextAction.astro         — single next step (prompt | guide | stage | decision)
  PageHero.astro           — outcome + audience + actions + trust indicator
  PageMeta.astro           — compact metadata bar (mode, permissions, coverage)
  TaskSwitcher.astro       — nav links (destinations) or tabs (same-page panels)
  JourneyRail.astro        — connected stages with mobile accordion form
  SkillRecord.astro        — aligned rows: goals, reads, writes, returns, limits
  WriteConfirmation.astro  — in-flow panel: objects, fields, counts, actions
```

**docs-site/ component tree** (subset — docs-specific surfaces):
```
docs-site/src/components/primitives/
  StatusChip.astro         — same interface; Starlight-theme-aware colors
  ReadWriteBadge.astro     — same interface
  CoverageBadge.astro      — same interface
  PermissionBadge.astro    — same interface
  PromptBlock.astro        — same interface; adapts to Starlight font stack
  AgentClarification.astro — same interface
  DecisionBand.astro       — same interface
  SkillRecord.astro        — same interface
  NextAction.astro         — same interface
```

PageHero, PageMeta, TaskSwitcher, JourneyRail, WriteConfirmation, and
ExpectedResult are web/-only in Wave 1; docs-site ports are Wave 2+.

### State & control flow

**Semantic state vocabulary** (CSS classes and token names):
```
state: informational     → --ds-state-info-{bg,fg,border}
state: read-only         → --ds-state-info-{bg,fg,border}    (synonym)
state: draft             → --ds-state-neutral-{bg,fg,border}
state: proposed-write    → --ds-state-warn-{bg,fg,border}
state: confirmed-write   → --ds-state-success-{bg,fg,border}
state: approval-required → --ds-state-warn-{bg,fg,border}
state: complete          → --ds-state-success-{bg,fg,border}
state: partial           → --ds-state-warn-{bg,fg,border}
state: blocked           → --ds-state-danger-{bg,fg,border}
state: failed            → --ds-state-danger-{bg,fg,border}
state: unavailable       → --ds-state-neutral-{bg,fg,border}
```

**Additional badge-specific state mappings** (ReadWriteBadge + CoverageBadge):
```
ReadWriteBadge mode: publish           → --ds-state-success-{bg,fg,border}
  (committed forward action — same role as confirmed-write)
ReadWriteBadge mode: destructive       → --ds-state-danger-{bg,fg,border}
  (irreversible — same role as blocked/failed)
CoverageBadge coverage: filtered       → --ds-state-info-{bg,fg,border}
  (informational — filter is active; no data lost)
CoverageBadge coverage: capped         → --ds-state-warn-{bg,fg,border}
  (warning — results truncated at a limit)
CoverageBadge coverage: permission-limited → --ds-state-warn-{bg,fg,border}
  (warning — access constraint is restricting results)
```

Five semantic color roles (never amber-gold, which is CTA/stat only):
```
success  → green family   (--prim-green-*)  — to be added to tokens.css
danger   → red family     (--prim-red-*)    — to be added
warning  → orange family  (--prim-orange-*) — to be added (distinct from amber)
info     → blue family    (--prim-blue-*)   — to be added
neutral  → existing neutrals
```
(Reviewer/purple family deferred: no AC2 state maps to it; add if a consuming
component requires a distinct reviewer-action semantic.)

**TaskSwitcher semantics:**
- `type="nav"` → renders `<nav>` with `<a>` links; no ARIA role needed.
- `type="tabs"` → renders `role="tablist"` with `role="tab"` buttons and
  associated `role="tabpanel"` elements; manages `aria-selected` and
  `aria-controls`; handles arrow-key navigation per ARIA authoring practices.

**JourneyRail mobile form:**
- Desktop (≥768px): horizontal rail, `<ol>` with CSS flex layout, stage state
  communicated via `aria-current="step"` on current stage.
- Mobile (<768px): `<details>/<summary>` per stage, with `open` attribute on
  current stage; native `<details>` manages `aria-expanded` — do not author it
  manually.

### Quality attributes (NFRs)

- WCAG 2.2 AA: color contrast ≥4.5:1 for text, ≥3:1 for UI components;
  focus visible per SC 2.4.11; touch targets ≥44×44px. Traces to: AC12, AC14.
- Responsive: compositional behavior (not just stacking) at 390px; JourneyRail
  switches form, PageMeta wraps to prioritized rows, SkillRecord records become
  stacked rows. Traces to: AC8, AC13.
- Performance: no new JavaScript bundles introduced; copy button uses a minimal
  inline script (< 200 bytes); tab component uses minimal inline script only
  when `type="tabs"`. Traces to: AC15.
- No layout shift: components use fixed height or min-height where content
  lengths vary. Traces to: AC15.

## Tasks

### T0: Extend tokens.css with semantic state tokens *(Wave 0)*

**Depends on:** none

**Touches:** web/src/styles/tokens.css

**Tests:**
- `astro build` exits 0 for both web/ and docs-site/ after token addition.
- No existing component references break (grep for `--ds-state-` before and
  after; zero references before = zero regressions possible).
- Color contrast of each state role fg/bg pair ≥4.5:1 (manual APCA/WCAG check;
  values recorded in notes/contrast-checks.md). Traces to: AC2, AC12.

**Approach:**
- Add Tier 1 primitives: `--prim-green-*`, `--prim-red-*`, `--prim-orange-*`,
  `--prim-blue-*` (5 values each: 100/300/500/700/900). Purple family deferred.
- Add Tier 2 semantic state tokens under a new `/* ── State roles ──── */`
  block: `--ds-state-success-{bg,fg,border}`, `--ds-state-danger-{bg,fg,border}`,
  `--ds-state-warn-{bg,fg,border}`, `--ds-state-info-{bg,fg,border}`,
  `--ds-state-neutral-{bg,fg,border}`.
- Record contrast ratios for each pair in `notes/contrast-checks.md`.
- Run build for both renderers.

**Done when:** both builds pass; contrast-checks.md exists with ratios for all
5 state roles (success/danger/warn/info/neutral; reviewer/purple deferred);
no existing component breaks.

---

### T1: Set up test infrastructure (vitest + axe-core) *(Wave 0)*

**Depends on:** none

**Touches:** web/package.json, web/vitest.config.ts (new), web/vitest.setup.ts (new)

**Tests:**
- A trivial test that imports a fixture string passes under `npm test` in web/.
- An axe-core check on a simple HTML string with a missing label attribute
  returns a violation (confirms the matcher works). Traces to: AC12.

**Approach:**
- Add devDependencies to web/package.json: vitest, @vitest/ui, jsdom, axe-core
  (after ask-first approval per Boundaries). Note: `@axe-core/vitest` does not
  exist on npm (verified 2026-07-28); `axe-core` is used directly in tests via
  `import axe from 'axe-core'` and `axe.run(element)`.
- Add `test` script to web/package.json.
- Create web/vitest.config.ts with jsdom environment.
- Create web/vitest.setup.ts importing axe-core matchers.
- Create web/src/test/ directory for unit tests.
- **Astro component rendering in vitest:** Use the Astro Container API from
  `'astro/container'`. Verify the exact export name at T1 start — stable Astro
  5+ exports `AstroContainer`; pre-stable builds used `experimental_AstroContainer`.
  Confirm against `node_modules/astro/container.d.ts` before writing tests, and
  record the resolved import in notes/test-architecture.md. If the Container API
  is unavailable, fall back to Playwright for all component rendering tests.
- Record devDependencies added in web/AGENTS.md (create if absent) under a
  `## Test dependencies` section, per AGENTS.md §Check before acting.
- Note: Playwright for browser/screenshot tests is deferred to T20 to keep
  this task focused.

**Done when:** `cd web && npm test` exits 0 with the trivial + axe-core tests
green; web/AGENTS.md updated with devDep record.

---

### T2: StatusChip — extract shared badge atom *(Wave 1)*

**Depends on:** T0, T1

**Touches:** web/src/components/primitives/StatusChip.astro (new),
web/src/components/pack/PackCard.astro,
web/src/components/pack/PackHero.astro,
web/src/components/journey/JourneyHero.astro,
web/src/components/marketing/PackCatalogue.astro,
web/src/pages/catalogue/index.astro,
web/src/test/StatusChip.test.ts (new)

**Tests:**
- StatusChip renders the `label` prop as visible text. Traces to: AC1, AC2.
- StatusChip carries `role="status"` when `live` prop is true. Traces to: AC12.
- StatusChip renders `data-state` attribute matching the `state` prop.
- axe-core finds no violations on the rendered chip. Traces to: AC12.
- `astro build` passes after PackCard, PackHero, JourneyHero, PackCatalogue, and
  catalogue/index.astro are updated to use StatusChip. Traces to: AC17.

**Approach:**
- Create `web/src/components/primitives/StatusChip.astro` with props:
  `state?: string`, `label: string`, `live?: boolean`.
- Style replicates the exact existing `.scope-chip` values (amber bg, mono
  font, uppercase, `--ds-radius-sm`) — no visual change.
- Replace inline `.scope-chip` blocks in all five existing locations: the
  four component files (PackCard, PackHero, JourneyHero, PackCatalogue) and
  `web/src/pages/catalogue/index.astro` (bundled-fixes carve-out).
- Write unit tests.

**Done when:** existing chip rendering is visually identical (screenshot diff
at 1440px confirms); unit tests green; axe-core clean; build passes.

---

### T3: ReadWriteBadge — read/write consequence indicator *(Wave 1)*

**Depends on:** T0, T1, T2

**Touches:** web/src/components/primitives/ReadWriteBadge.astro (new),
web/src/test/ReadWriteBadge.test.ts (new)

**Tests:**
- Each of the six states renders correct visible consequence text. Traces to: AC4.
- "Destructive action" state uses `--ds-state-danger-*` tokens. Traces to: AC2.
- axe-core clean. Traces to: AC12.

**Approach:**
- Create `ReadWriteBadge.astro` with props:
  `mode: 'read-only' | 'draft' | 'proposed-write' | 'confirmed-write' | 'publish' | 'destructive'`.
- Map each mode to: a StatusChip state, a visible consequence label, and an
  optional icon aria-label (icon is decorative; text is the semantic carrier).
- Consequence labels: "Read only", "Draft — no changes saved",
  "Review before writing", "Writing confirmed", "Publishing now",
  "Destructive — cannot undo".

**Done when:** unit tests green; build passes; all six states visible in manual
review with correct text.

---

### T4: CoverageBadge — result completeness indicator *(Wave 1)*

**Depends on:** T0, T1, T2

**Touches:** web/src/components/primitives/CoverageBadge.astro (new),
web/src/test/CoverageBadge.test.ts (new)

**Tests:**
- Each of the five states renders visible explanation text. Traces to: AC5.
- "Permission-limited result" state carries an accessible description of
  the limitation. Traces to: AC5, AC12.
- axe-core clean.

**Approach:**
- Props: `coverage: 'complete' | 'filtered' | 'partial' | 'capped' | 'permission-limited'`,
  `detail?: string`.
- Map each coverage value to state token, visible label, and tooltip/
  aria-describedby explanation.

**Done when:** unit tests green; build passes.

---

### T5: PermissionBadge — required access indicator *(Wave 1)*

**Depends on:** T0, T1, T2

**Touches:** web/src/components/primitives/PermissionBadge.astro (new),
web/src/test/PermissionBadge.test.ts (new)

**Tests:**
- "Missing access" state is visually and semantically distinct from
  "has access" state. Traces to: AC1.
- No raw credential values render in the output. Traces to: AC17 (Boundaries).
- axe-core clean.

**Approach:**
- Props: `access: 'granted' | 'missing' | 'unknown'`, `permission: string`.
- "Missing" state uses `--ds-state-warn-*`; renders the permission name but
  never a secret or raw credential.

**Done when:** unit tests green; build passes.

---

### T6: CopyButton — standalone copy action *(Wave 1)*

**Depends on:** T0, T1

**Touches:** web/src/components/primitives/CopyButton.astro (new),
web/src/components/marketing/InstallTerminal.astro (refactor),
web/src/test/CopyButton.test.ts (new)

**Tests:**
- CopyButton renders as a `<button>` with accessible label. Traces to: AC12.
- On success, a live-region announcement is injected. Traces to: AC1 (Copy
  success announced to AT requirement).
- axe-core clean.
- InstallTerminal still builds and its copy functionality is unchanged after
  extracting CopyButton (goal-based: build + visual check). Traces to: AC17.

**Approach:**
- Extract copy logic from InstallTerminal into `CopyButton.astro`.
- Props: `content: string`, `label?: string` (accessible name), `successLabel?: string`.
- Inline `<script>` (< 200 bytes) handles clipboard write + live-region injection.
- Refactor InstallTerminal to use CopyButton; no behavior change.

**Done when:** unit tests green; InstallTerminal build passes and is visually
identical; clipboard copy verified manually; live-region announced in browser
devtools accessibility panel.

---

### T7: CopyPrompt — shareable prompt string *(Wave 1)*

**Depends on:** T0, T6

**Touches:** web/src/components/primitives/CopyPrompt.astro (new)

**Tests:**
- Renders the prompt string inside a `<code>` element with mono font. Traces to: AC1.
- CopyButton is wired and copy action works. Traces to: AC6 (implicit — copy
  available at AC1).
- axe-core: deferred to T19 fixture page run (no test file in this task). Traces to: AC12.

**Approach:**
- Props: `prompt: string`.
- Minimal wrapper: mono typeface, neutral border, copy button in top-right corner.
- Used by PromptBlock as its copy target.

**Done when:** build passes; copy works.

---

### T8: PromptBlock — conversation-first prompt display *(Wave 1)*

**Depends on:** T0, T1, T6, T7

**Touches:** web/src/components/primitives/PromptBlock.astro (new),
web/src/test/PromptBlock.test.ts (new)

**Tests:**
- PromptBlock background and border differ from an Expressive Code block at
  the same viewport (screenshot regression; manual review). Traces to: AC3.
- Speaker label rendered above the prompt. Traces to: AC1.
- ReadWriteBadge visible when `mode` prop is passed. Traces to: AC4.
- axe-core clean.

**Approach:**
- Props: `speaker?: string`, `prompt: string`, `mode?: ReadWriteMode`,
  `context?: string`, `variables?: Record<string, string>`.
- Amber left border (`3px solid --ds-accent`), `--ds-accent-subtle` fill,
  Inter font (not monospace), speaker label in `--ds-on-surface-muted`.
- CopyPrompt for the copy action; ReadWriteBadge if `mode` is provided.
- Variable slots (`{variable}`) highlighted with amber text for editability cue.

**Done when:** unit tests green; screenshot diff confirms visual distinction
from code block; build passes.

---

### T9: AgentClarification — pre-action question display *(Wave 1)*

**Depends on:** T0

**Touches:** web/src/components/primitives/AgentClarification.astro (new)

**Tests:**
- Component does not apply danger/error styling when `blocked=false`. Traces to: AC1.
- Blocked state (`blocked=true`) uses `--ds-state-warn-*`, not danger. Traces to: AC1.
- axe-core: deferred to T19 fixture page run (no test file in this task). Traces to: AC12.

**Approach:**
- Props: `question: string`, `options?: string[]`, `reason?: string`, `blocked?: boolean`.
- Renders as a bordered panel, neutral by default; `--ds-state-warn-*` when blocked.
- Options as a `<ul>` list. Reason as `<p>` in muted text.
- Never styled as an error/danger state. Traces to: AC1 (do not style as error).

**Done when:** build passes; screenshot of both blocked and non-blocked states
committed to notes/screenshots/agentclarification/.

---

### T10: DecisionBand — human decision gate *(Wave 2)*

**Depends on:** T0, T1

**Touches:** web/src/components/primitives/DecisionBand.astro (new),
web/src/test/DecisionBand.test.ts (new)

**Tests:**
- DecisionBand's computed background contrast against adjacent `.ds-surface`
  meets ≥3:1 UI component contrast (manual check, value recorded). Traces to: AC6.
- Primary action button is the first focusable element inside the band. Traces to: AC14.
- axe-core clean.

**Approach:**
- Props: `summary: string`, `consequence: string`, `primaryAction: {label, href|onclick}`,
  `secondaryAction?: {label, href|onclick}`, `scope?: string`.
- Full-width band with `--ds-state-warn-bg` fill (amber-orange tint) and a
  `4px solid --ds-accent` left border.
- Consequence in bold, larger than adjacent body text.
- Scope (protected/unchanged) in muted text below actions.

**Done when:** unit tests green; visual prominence confirmed in screenshot;
build passes.

---

### T11: PageHero — page outcome and primary action *(Wave 2)*

**Depends on:** T0

**Touches:** web/src/components/primitives/PageHero.astro (new)

**Tests:**
- Build passes; existing JourneyHero and PackHero are not broken. Traces to: AC17.
- Title, outcome, and at least one action render correctly. Traces to: AC1.

**Approach:**
- Props: `title: string`, `outcome: string`, `primaryAction?: {label, href}`,
  `secondaryAction?: {label, href}`, `badge?: BadgeProps`, `proof?: string`.
- Generalized from JourneyHero/PackHero without replacing them — new primitive
  for future page templates.
- Light zone by default (does not assume dark hero canvas — uses `--ds-surface`).
- No centered text or decorative backgrounds per spec.

**Done when:** build passes; renders correctly at 1440, 1024, 390px.

---

### T12: PageMeta — compact metadata bar *(Wave 2)*

**Depends on:** T0, T3, T4, T5

**Touches:** web/src/components/primitives/PageMeta.astro (new)

**Tests:**
- Wraps to prioritized rows at 390px (screenshot confirms). Traces to: AC1, AC13.
- axe-core: deferred to T19 fixture page run (no test file in this task). Traces to: AC12.

**Approach:**
- Props: `items: PageMetaItem[]` where each item has `type` (mode/permission/coverage/skill/prerequisite) and relevant props.
- Renders as a flex row that wraps at narrow viewports.
- Each item is a badge from the T3–T5 components.

**Done when:** renders at all three breakpoints; build passes.

---

### T13: TaskSwitcher — job-based navigation *(Wave 2)*

**Depends on:** T0, T1

**Touches:** web/src/components/primitives/TaskSwitcher.astro (new),
web/src/test/TaskSwitcher.test.ts (new)

**Tests:**
- `type="nav"` renders `<nav>` with `<a>` elements; no `role="tab"`. Traces to: AC1.
- `type="tabs"` renders `role="tablist"` with `role="tab"` and `role="tabpanel"`.
  Traces to: AC1.
- Active tab has `aria-selected="true"`. Traces to: AC12.
- axe-core clean for both variants.
- Arrow key navigation cycles tabs in `type="tabs"` mode (visual/manual QA,
  documented in notes/keyboard-qa.md). Traces to: AC14.

**Approach:**
- Props: `type: 'nav' | 'tabs'`, `items: {label, href?, id?}[]`, `activeId?: string`.
- `type="nav"`: pure CSS, zero JS.
- `type="tabs"`: minimal inline `<script>` handles `aria-selected` toggle and
  arrow-key navigation per ARIA authoring practices Tab widget pattern.

**Done when:** unit tests green; keyboard QA documented; build passes.

---

### T14: ExpectedResult / ResultPreview *(Wave 2)*

**Depends on:** T0

**Touches:** web/src/components/primitives/ExpectedResult.astro (new)

**Tests:**
- Long content does not overflow horizontally (screenshot at 390px). Traces to: AC8.
- Follow-up actions render below result records. Traces to: AC1.
- axe-core: deferred to T19 fixture page run (no test file in this task). Traces to: AC12.

**Approach:**
- Props: `summary: string`, `records?: ResultRecord[]`, `status?: string`,
  `warnings?: string[]`, `followUp?: {label, href}[]`.
- Records rendered as a `<table>` with `scope="col"` headers.
- Table becomes scrollable horizontally on narrow viewports (not overflow-hidden).

**Done when:** build passes; no horizontal overflow at 390px.

---

### T15: SkillRecord — structured reference lookup *(Wave 2)*

**Depends on:** T0

**Touches:** web/src/components/primitives/SkillRecord.astro (new)

**Tests:**
- Renders as aligned rows, not cards. Traces to: AC9.
- Table switches to stacked records at 390px (screenshot). Traces to: AC8.
- axe-core: deferred to T19 fixture page run (no test file in this task). Traces to: AC12.

**Approach:**
- Props: `goals: string[]`, `name: string`, `reads: string`, `writes: string`,
  `returns: string`, `limits?: string`, `followUp?: string`.
- Desktop: CSS grid aligned rows.
- Mobile: each row becomes a `<dl>` definition list.

**Done when:** build passes; desktop/mobile layout confirmed in screenshots.

---

### T16: JourneyRail — connected stage navigator *(Wave 2)*

**Depends on:** T0

**Touches:** web/src/components/primitives/JourneyRail.astro (new)

**Tests:**
- Desktop renders as `<ol>` with CSS flex and `aria-current="step"` on current
  stage. Traces to: AC8.
- Mobile (<768px) renders as `<details>/<summary>` with `open` on current stage.
  Traces to: AC8.
- Screenshot at 767px confirms the accordion form is active just below the
  768px breakpoint. Traces to: AC8, AC13.
- Native `<details>` disclosure does not use author-set `aria-expanded`; axe-core
  on the fixture page (T19) verifies no manual ARIA override is present. Traces to: AC12.
- axe-core: deferred to T19 fixture page run (no test file in this task). Traces to: AC12.
- Keyboard navigation: Tab moves focus to each stage summary; Enter/Space
  toggles open/closed (documented in keyboard-qa.md). Traces to: AC14.

**Approach:**
- Props: `stages: JourneyStage[]`, `currentId: string`.
- Desktop CSS via `@media (min-width: 768px)`.
- Connecting line between stages via CSS `::before` pseudo-element.
- Decision boundaries marked with a diamond marker class.

**Done when:** both forms render at correct breakpoints; keyboard QA documented;
build passes.

---

### T17: WriteConfirmation — in-flow confirmation panel *(Wave 2)*

**Depends on:** T0, T1

**Touches:** web/src/components/primitives/WriteConfirmation.astro (new),
web/src/test/WriteConfirmation.test.ts (new)

**Tests:**
- All required fields visible: objects, fields, protected fields, write count,
  consequence, cancel, confirm. Traces to: AC7.
- Cancel button is keyboard-focusable before confirm button (safe-path-first
  focus order). Traces to: AC14.
- No `<dialog>` element used (in-flow panel). Traces to: AC7.
- axe-core clean.

**Approach:**
- Props: `objects: string[]`, `fields: WriteField[]`, `protectedFields?: string[]`,
  `writeCount: number`, `consequence: string`, `onConfirm?: string` (href),
  `onCancel?: string` (href).
- In-flow panel (a `<section>` with role="region" and aria-label).
- Cancel is the first action button; confirm is styled with `--ds-state-warn-*`.
- Mobile: one decision section at a time via scroll, not modal.

**Done when:** unit tests green; all fields visible; keyboard QA documented;
build passes.

---

### T18: NextAction — single next step *(Wave 2)*

**Depends on:** T0

**Touches:** web/src/components/primitives/NextAction.astro (new)

**Tests:**
- Renders exactly one action. Traces to: AC1.
- `type="decision"` uses DecisionBand styling conventions. Traces to: AC6.
- axe-core: deferred to T19 fixture page run (no test file in this task). Traces to: AC12.

**Approach:**
- Props: `type: 'prompt' | 'guide' | 'stage' | 'decision'`, `label: string`,
  `href?: string`, `prompt?: string`.
- Single focused call to action; no link collection.

**Done when:** build passes; renders clearly.

---

### T19: Component fixture page *(Wave 3)*

**Depends on:** T0–T18

**Touches:** web/src/pages/primitives-fixture.astro (new),
web/astro.config.ts (sitemap exclusion)

**Tests:**
- `<meta name="robots" content="noindex">` present in built HTML. Traces to: AC11.
- Fixture URL not present in `sitemap.xml` output. Traces to: AC11.
- All sixteen components render with representative content including: long
  text, partial results, errors, read/write states. Traces to: AC11.
- axe-core automated check on the built fixture page exits clean. Traces to: AC12.

**Approach:**
- Render all components in all material states with deterministic fixture content.
- Include light-zone rendering (default) for all components.
- Exclude from sitemap via `astro.config.ts` filter.
- Add `<meta name="robots" content="noindex">`.

**Done when:** fixture page renders all components; noindex and sitemap
exclusion verified; axe-core clean.

---

### T20: Playwright browser tests + screenshot baselines *(Wave 4)*

**Depends on:** T19

**Touches:** web/package.json (playwright devDep), web/playwright.config.ts (new),
web/src/test/e2e/ (new), docs/specs/site-ui-primitives/notes/screenshots/ (new)

**Tests:**
- Screenshots captured at 1440px, 1024px, 390px for all components. Traces to: AC13.
- Screenshots at 375px and 430px for JourneyRail, SkillRecord, PageMeta (material
  mobile risk). Traces to: AC13.
- CopyPrompt copy action: text written to clipboard, live-region announces success.
  Traces to: AC1.
- TaskSwitcher arrow-key navigation cycles tabs. Traces to: AC14.
- JourneyRail: accordion opens/closes at 390px. Traces to: AC8.
- WriteConfirmation: cancel and confirm fire on keyboard Enter. Traces to: AC14.

**Approach:**
- Add Playwright devDependency to web/package.json (ask-first approval).
- Capture screenshot baselines and commit to notes/screenshots/.
- Browser interaction tests for the five interaction patterns above.

**Done when:** screenshots committed; browser tests pass; keyboard-qa.md updated;
Playwright devDependency recorded in `web/AGENTS.md` under `## Test dependencies`.

---

### T21: docs-site component implementations *(Wave 4)*

**Depends on:** T2–T9 (badge family + PromptBlock)

**Touches:** docs-site/src/components/primitives/ (new directory)

**Tests:**
- Each docs-site component renders correctly in Starlight light mode and dark
  mode (screenshot per component × mode). Traces to: AC1, AC2.
- `cd docs-site && npm run build` passes. Traces to: AC15.
- axe-core clean on one built documentation page that uses the components,
  run via `axe-core` CLI against `astro preview` of docs-site (or equivalent
  browser-based axe runner). Traces to: AC12.

**Approach:**
- Implement docs-site versions of: StatusChip, ReadWriteBadge, CoverageBadge,
  PermissionBadge, PromptBlock, AgentClarification, DecisionBand, SkillRecord,
  NextAction.
- Use `--sl-color-*` for theme-sensitive colors; `--ds-*` for spacing/radius/motion.
- Update `docs-site/astro.config.ts` `components:` array if any replace a
  Starlight built-in.

**Done when:** docs-site builds; docs-site components visible in at least one
actual documentation page; axe-core clean.

---

### T22: Performance + console/network check *(Wave 4)*

**Depends on:** T19, T20

**Touches:** notes/performance-check.md (new)

**Tests:**
- No new JavaScript bundles > 5kB gzipped introduced. Traces to: AC15.
- Zero new console errors or network errors on the fixture page or any
  existing public page. Traces to: AC15.
- No layout shift (CLS = 0) on fixture page. Traces to: AC15.

**Approach:**
- Run `astro build` and measure JS bundle sizes with `du -sh dist/`.
- Open fixture page and existing public pages in Chrome DevTools; record
  console output and network errors; record CLS in Performance tab.

**Done when:** performance-check.md committed with measurements and pass/fail
against the criteria above.

---

### T23: Maintainer documentation *(Wave 5)*

**Depends on:** T0–T21

**Touches:** docs/guides/ (new files under appropriate category)

**Tests:**
- Guide exists at `docs/guides/<category>/how-to/ui-primitives.md` or
  equivalent. Traces to: AC16.
- Guide covers all sixteen primitives with when-to-use guidance, source syntax
  examples, card-use test, state semantics, responsive expectations,
  accessibility expectations, common anti-patterns. Traces to: AC16.
- Examples include: prompt followed by result; read-only followed by decision;
  reference record; write confirmation; mobile journey presentation. Traces to: AC16.

**Approach:**
- Write a single how-to guide in the appropriate guides/ category.
- Include code snippets for each component's common usage.
- Explicitly document the card-use test from the brief.

**Done when:** guide file exists; covers all 16 components; examples present.

---

### T24: Independent UI review *(Wave 5)*

**Depends on:** T19, T20, T21

**Tests:**
- Reviewer assesses: first-screen clarity, hierarchy, component semantics,
  responsive composition, accessibility, interaction usefulness, cross-renderer
  consistency, overuse of cards. Traces to: AC17 (independent review).
- All Blocker findings from review resolved.

**Approach:**
- Dispatch `experience-reviewer` subagent (available as a system-level agent type
  via the Agent tool; not a project-scoped `.claude/agents/` file) with the built
  fixture page description, screenshots from T20, and the aesthetic direction
  grounding (`docs/specs/platform-site/aesthetic-direction.md`).
- Record findings and fixes in notes/review-findings.md.

**Done when:** reviewer returns Clean or all Blockers resolved; findings documented.

## Rollout

Pure-static components in a static-site Astro build. No infrastructure changes,
no migrations, no flags. Rollback is a git revert. Ships as a normal PR per wave.

## Risks

- **Token extension name collision.** `--ds-state-*` names are new; but
  searching the codebase confirms zero references before T0, so no collision is
  possible.
- **docs-site Starlight version constraint.** Starlight 0.41.x has specific
  component override APIs; confirm the `components:` API before adding
  docs-site overrides in T21.
- **Playwright in Astro.** Astro's static output requires a local server for
  Playwright; `astro preview` is the test server. Confirm this before T20.
- **Color palette additions.** Adding green/red/orange/blue primitive families
  expands the token surface significantly. Ensure the colors are visually
  coherent with the existing amber-gold identity and pass contrast.
  The amber-gold accent must remain the single chromatic identity accent;
  state colors are functional, not identity.

## Changelog

- 2026-07-28: initial plan
