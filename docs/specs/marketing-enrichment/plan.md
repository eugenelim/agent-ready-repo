# Plan: marketing-enrichment

- **Spec:** [spec.md](spec.md)
- **Status:** Done

## Tasks

### T1 — ThreeLoops: icon card grid
**Depends on:** none
**Verification mode:** Visual/manual QA
**Done when:** `npm run build` exits 0; rendered HTML has `.loop-card` elements in a 3-column grid with SVG icon, pack badge, capability list, and gate callout per card.

**Capability lines (exact copy, sourced from existing `desc` and `gate` fields):**
- Discovery Loop: "Raw idea → ratified brief", "Five candidate shapes, four specialist lenses", "Product, UX, architecture, safety"
- Build Loop: "Spec → shipped code", "Lint, typecheck, and tests must pass", "Three specialist reviewers, each cold"
- Release Loop: "Built → production", "Autonomous e2e on ephemeral environments", "Deployed findings feed back automatically"

**Approach:**
- Add `caps` array to each loop entry (3 strings each, from above).
- Replace `<ol class="loops">` layout from vertical flex list to 3-column CSS Grid: `grid-template-columns: repeat(3, 1fr)` at ≥ 768px; `grid-template-columns: 1fr` below.
- Each `<li class="loop-card">` contains:
  1. Icon container (32×32 inline SVG, amber bg `--ds-accent-subtle`, icon `--ds-accent-deep`)
  2. Meta row: number chip + pack code badge (existing `l.pack` value)
  3. `h3` loop name
  4. Caps list (`→`-prefixed items, `--ds-on-surface-2`)
  5. Gate callout (amber left border, `--ds-accent-subtle` bg)
  6. Journey link (existing link label + arrow)
- Pipeline visualization at top: keep unchanged (already good).
- SVG icons (inline, `aria-hidden="true"`, 24×24 viewBox):
  - Discovery: magnifying glass (circle + line)
  - Build: code brackets (`< >`)
  - Release: upward arrow / send
- Sizing: icon wrapper `var(--ds-space-7)` wide × `var(--ds-space-7)` tall (48px); SVG 24×24 centred.
- Border on card: `1px solid var(--ds-border)` + `border-top: 3px solid var(--ds-accent)`.
- All transitions (hover border-color change) guarded with `@media (prefers-reduced-motion: no-preference)`.

**No stub (mode: visual/manual QA).**

---

### T2 — HumanGates: phase timeline
**Depends on:** none
**Verification mode:** Visual/manual QA
**Done when:** `npm run build` exits 0; rendered HTML has `.timeline__phase` groups for Discovery, Build, Release; each phase has `.timeline__gate` items connected by vertical lines; phases connected by `→` arrows on desktop.

**Phase grouping (exact gate data preserved):**
- Discovery: G0 (Go/No-go), G1.5 (Shape sign-off), G2 (Brief ratification), G3 (Handoff to build)
- Build: Plan (Plan approval), G4 (PR merge)
- Release: G5 (Prod ship)

**Approach:**
- Restructure `gates` flat array into `phases` array with `{ label, gates[] }`.
- Remove existing `gates__grid` layout.
- New timeline layout: `display: flex; gap: var(--ds-space-5); align-items: flex-start` on desktop; `flex-direction: column` on mobile.
- Each `.timeline__phase`: flex column, `flex: 1`.
  - Phase header: uppercase label `--ds-on-surface-muted`, `--ds-type-xs`, `letter-spacing: var(--ds-track-label)`, `border-bottom: 1px solid var(--ds-border)`, `margin-bottom: var(--ds-space-4)`.
  - Gate list `<ol class="timeline__gates">`: flex column, `gap: 0`.
- Each gate item (`<li class="timeline__gate">`): flex row, `gap: var(--ds-space-3)`.
  - Left side `.timeline__gate-left` (flex column, `align-items: center`):
    - Marker pill: `min-width: var(--ds-space-7)` (48px), `height: var(--ds-space-6)` (32px), `border-radius: var(--ds-radius-pill)`, `background-color: var(--ds-accent-subtle)`, `border: 1px solid var(--ds-accent)`.
    - Gate ID text: mono, `--ds-type-xs`, `--ds-accent-deep`, `letter-spacing: var(--ds-track-label)`.
    - Connector line (`.timeline__gate-line`): `width: 1px`, `flex: 1`, `min-height: var(--ds-space-4)` (16px), `background-color: var(--ds-border)`; hidden via `.timeline__gate:last-child .timeline__gate-line { display: none }`.
  - Right side `.timeline__content`:
    - Gate name (h4): `--ds-type-sm`, `--ds-weight-semibold`.
    - Decide question (p): `--ds-type-sm`, `--ds-on-surface-muted`.
- Phase connector (`.timeline__connector`): decorative `→` between phases; `display: flex; align-items: flex-start; padding-top: var(--ds-space-6)` (aligns with first gate marker); hidden on mobile.
- Existing headline, subhead, and CTA link: preserved, kept above `.timeline`.

**No stub (mode: visual/manual QA).**

---

### T3 — AdapterMatrix: column update
**Depends on:** none
**Verification mode:** Visual/manual QA
**Done when:** `npm run build` exits 0; rendered HTML `<thead>` contains 5 capability columns [Tool Use, Context Files, Skills, Hooks, Multi-Agent]; 6 adapter rows; Kiro (consolidated) present; note text updated.

**Capability data (sourced from adapter.toml — see spec § Adapter capability data):**
```javascript
const capabilities = ['Tool Use', 'Context Files', 'Skills', 'Hooks', 'Multi-Agent'];
const agents = [
  { name: 'Claude Code', caps: [true, true, true, true, true] },
  { name: 'Cursor',      caps: [true, true, true, true, true] },
  { name: 'Gemini CLI',  caps: [true, true, true, true, true] },
  { name: 'Kiro',        caps: [false, true, true, true, true] },
  { name: 'Copilot',     caps: [false, true, true, true, true] },
  { name: 'Codex',       caps: [false, true, true, true, true] },
];
```

**Approach:**
- Update `capabilities` array and `agents` array as above.
- Note text: update from "…skills, subagents, and hooks project…" to "…skills, multi-agent dispatch, and hooks project…".
- Table `min-width`: increase from `520px` to `560px` to accommodate 6 columns.
- All existing table CSS unchanged.
- No new CSS rules needed — existing table styles handle the updated column count.

**No stub (mode: visual/manual QA).**

---

### T4 — BuildYourOrg: 3-step sequence
**Depends on:** none
**Verification mode:** Visual/manual QA
**Done when:** `npm run build` exits 0; rendered HTML has `.org__steps` element with 3 `.org__step` items; existing `.org__headline`, `.org__body`, `.org__cta` still present and unmodified.

**Step content:**
- Step 1: label "Install core", description code `agentbundle install --pack core`
- Step 2: label "Add packs", description "Extend with skills for your stack"
- Step 3: label "Ship", description "Loop runs. Human gates. CI passes."

**Approach:**
- Insert `<ol class="org__steps" aria-label="Three steps to get started">` between `.org__headline` and `.org__body`.
- Each step `<li class="org__step">`:
  - Number circle: `var(--ds-space-6)` (32px) wide × `var(--ds-space-6)` tall, `border-radius: var(--ds-radius-pill)`, `background-color: var(--ds-accent)`, `color: var(--ds-cta-primary-fg)`, centered number text.
  - Step body `.org__step-body`: h3 (step label, `--ds-hero-fg`) + p or code (description, `--ds-hero-fg-2`).
- Between steps: `<li class="org__step-arrow" aria-hidden="true">→</li>` connector.
- Layout: `display: flex; align-items: flex-start; gap: var(--ds-space-5); flex-wrap: wrap; margin-bottom: var(--ds-space-7)` on desktop; on mobile (< 768px) `flex-direction: column; gap: var(--ds-space-4)` with arrows hidden.
- Dark zone: step labels use `--ds-hero-fg`; descriptions use `--ds-hero-fg-2`; code uses existing `--ds-accent-subtle-dk` bg + `--ds-accent` fg.
- Existing `.org__headline`, `.org__body` (and its `code` child), `.org__cta` styles: unchanged.

**No stub (mode: visual/manual QA).**

---

### T5 — Amend homepage-screen-flow.md §6
**Depends on:** none
**Verification mode:** Goal-based check
**Done when:** §6 adapter table and note text in homepage-screen-flow.md reflect new columns and consolidated Kiro row.

**Approach:**
- Update the `| Agent | Skills | Subagents | Hooks | Commands |` table to `| Agent | Tool Use | Context Files | Skills | Hooks | Multi-Agent |` with 6 rows.
- Update the `**Note below table:**` text to replace "subagents" with "multi-agent dispatch".

---

### T6 — Build verify + evidence manifest
**Depends on:** T1, T2, T3, T4, T5
**Verification mode:** Goal-based check
**Done when:** `cd web && npm run build` exits 0; AC5 grep returns no matches; evidence manifest recorded.

**Approach:**
- Run `cd web && npm run build`.
- Run AC5 grep on the four edited files.
- Record evidence manifest in PR description.
