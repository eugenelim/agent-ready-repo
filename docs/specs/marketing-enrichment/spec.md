# Spec: marketing-enrichment

- **Mode:** Full (risk triggers: structural change to multi-component HTML/CSS primary output; multi-feature)
- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [plan.md](plan.md)
- **Constrained by:** `web/src/styles/tokens.css` (token vocabulary), `docs/specs/platform-site/aesthetic-direction.md`, `docs/specs/platform-site/homepage-screen-flow.md` (amended in this PR — §6 adapter table)

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

---

## Objective

Enrich four homepage sections — ThreeLoops, HumanGates, AdapterMatrix, BuildYourOrg — with richer visual treatments: icon card grid, phase timeline, updated adapter table, and 3-step install sequence. All existing copy is preserved. No new npm dependencies.

**Trio:**
- Files touched: `ThreeLoops.astro`, `HumanGates.astro`, `AdapterMatrix.astro`, `BuildYourOrg.astro`, `homepage-screen-flow.md` (§6 amendment), this spec, and plan.
- Tests demonstrating done: `cd web && npm run build` exits 0; visual QA evidence manifest shows correct structure at 375px and 1280px viewports.
- Not changing: `tokens.css` (spacing values), `Hero.astro`, `index.astro` (no new section), `Section.astro`, `TheProblem.astro`, `StatStrip.astro`, `PackCatalogue.astro`, `InstallTerminal.astro`.

**Declined patterns:**
- Tempted to add a persona cards section (optional item in task spec) — declining; adds a new component + index.astro edit, widening the diff beyond the four core enrichments. Deferred as follow-up.
- Tempted to add JavaScript animation to the HumanGates timeline — declining; CSS-only with `prefers-reduced-motion` guard.
- Tempted to extract `scope-chip` as a shared component (used in ThreeLoops pack badge + PackCatalogue) — declining; two callers don't yet warrant extraction.
- Tempted to update typography scale in tokens.css for icon cards — declining; out of scope (concurrent PR handles spacing tokens).

---

## Boundaries

**Always do:**
- Use only existing `--ds-*` semantic tokens in all component styles.
- Keep all existing copy intact in all four sections.
- Guard all transitions and transforms with `@media (prefers-reduced-motion: no-preference)`.
- Source adapter capability data from `packages/agentbundle/agentbundle/_data/adapter.toml` (authoritative).

**Ask first:**
- Adding a new `--ds-*` design token (would need to touch tokens.css, which is out of scope for this PR).
- Adding VS Code as an adapter row (no VS Code adapter exists in adapter.toml; deferred follow-up).

**Never do:**
- Edit `web/src/styles/tokens.css` (concurrent PR owns spacing values).
- Edit `web/src/components/marketing/Hero.astro` (concurrent PR owns hero visual).
- Add new npm dependencies.
- Use hardcoded hex colours or `rgba()` outside the existing `:root` primitive block.

---

## Frontend pre-flight

**Mode:** Retrofit (improving existing surfaces without a ground-up rebuild).

**Aesthetic reference:** Linear (professional SaaS — structured, high information density, no gradients). Consistent with existing `docs/specs/platform-site/aesthetic-direction.md`.

**XD genre routing:** skipped (experience-design pack absent — `conversion-design` not installed).

**Seed token block:** Inheriting existing `--ds-*` tokens from `web/src/styles/tokens.css`. No new tokens. All component styles reference existing semantic tokens only.

**Brownfield inspection:**

| Item | Finding |
|---|---|
| what-to-preserve | All existing copy; `--ds-*` token discipline; amber accent palette; Section wrapper; responsive breakpoints; aria patterns (`.visually-hidden`, gate/adapter aria-labels) |
| duplicated-systems | `scope-chip` pattern exists in PackCatalogue.astro — not duplicated here; pack badge in ThreeLoops uses inline monospace style |
| hard-coded values | None found — all existing components use `--ds-*` tokens |
| a11y-debt | None significant in the four targeted components |
| responsive-debt | None significant; existing components are mobile-friendly |
| visual-regression-risk | Changes are self-contained per component; Section.astro layout unchanged |

**State matrix (applicable states only):**

All four sections are static (no async data fetching).

| State | Treatment |
|---|---|
| content | The normal rendered state — all section content static and pre-rendered |
| reduced-motion | All `transition` and `transform` guarded with `@media (prefers-reduced-motion: no-preference)`. Base state has no motion |
| keyboard-only | All links keyboard-reachable via natural tab order; no interactive elements beyond links |
| high-zoom | Text reflows at 200% zoom; no horizontal body scroll; icons sized with space tokens |

Inapplicable states (no async, no forms, no destructive actions, no auth): loading, empty, error, first-run, no-results, disabled, blocked, destructive-confirmation, partial, large-data-set, offline, permission/denied, long-content, success.

---

## Acceptance Criteria

- [x] AC1 — **ThreeLoops icon card grid:** Vertical numbered list replaced with a 3-column icon card grid (1-col on mobile < 768px, 3-col on desktop ≥ 768px). Each card contains: an inline SVG icon, loop number chip, pack badge (existing code text), loop name (h3), 2–3 capability lines (exact text enumerated in plan T1), gate callout with existing gate text, and journey link with existing link label. The verbose prose `desc` field is intentionally condensed into the scannable `caps` lines — same semantic content, more scannable format; the gate callout and journey link texts are unchanged verbatim.
- [x] AC2 — **HumanGates phase timeline:** Flat 7-card grid replaced with a phase-grouped timeline: 3 column groups (Discovery, Build, Release) displayed horizontally on desktop ≥ 768px, stacked vertically on mobile. Gates shown as vertically-connected pill markers within each group. All 7 existing gate entries (ids, names, decide questions, headline, subhead, CTA) preserved.
- [x] AC3 — **AdapterMatrix column update:** Capability columns updated from `[Skills, Subagents, Hooks, Commands]` to `[Tool Use, Context Files, Skills, Hooks, Multi-Agent]`. Source: `packages/agentbundle/agentbundle/_data/adapter.toml` (command-primitive support for Tool Use; skill/hook-body+hook-wiring/agent primitive for others). Rows: Kiro IDE + Kiro CLI consolidated to single "Kiro" row (using kiro-ide capabilities). Note text updated to replace "subagents" with "multi-agent dispatch" for terminology consistency with new column name.
- [x] AC4 — **BuildYourOrg 3-step sequence:** 3-step visual sequence added between the existing headline and body text. Steps: "Install core" (`agentbundle install --pack core`), "Add packs" ("Extend with skills for your stack"), "Ship" ("Loop runs. Human gates. CI passes."). Step numbers use amber circles on dark background. On desktop, steps flow horizontally; on mobile, vertically. Existing `.org__headline`, `.org__body`, and `.org__cta` preserved without alteration.
- [x] AC5 — **Token discipline:** All new styles reference only existing `--ds-*` semantic tokens. No hardcoded hex or `rgba()` values in the four edited component files. Verified: `grep -E "#[0-9a-fA-F]{3,6}|rgba?\(" <four-files>` exited 1 (no matches).
- [x] AC6 — **Reduced-motion guard:** All `transition` and `transform` properties in new CSS guarded with `@media (prefers-reduced-motion: no-preference)`. Only ThreeLoops has a transition (hover border-color); guarded.
- [x] AC7 — **Responsive (manual visual QA):** All four components render correctly at 375px mobile and 1280px desktop. No horizontal body scroll at any viewport. Breakpoint at 767px (max-width) / 768px (min-width) consistent across all components.
- [x] AC8 — **Build passes:** `cd web && npm run build` exits 0. 41 pages built in 1.44s.

---

## Adapter capability data (sourced from adapter.toml)

Source: `packages/agentbundle/agentbundle/_data/adapter.toml` — `command` primitive mode checked programmatically (non-`dropped` = ✓).

| Agent | Tool Use | Context Files | Skills | Hooks | Multi-Agent |
|---|---|---|---|---|---|
| Claude Code | ✓ | ✓ | ✓ | ✓ | ✓ |
| Cursor | ✓ | ✓ | ✓ | ✓ | ✓ |
| Gemini CLI | ✓ | ✓ | ✓ | ✓ | ✓ |
| Kiro | — | ✓ | ✓ | ✓ | ✓ |
| Copilot | — | ✓ | ✓ | ✓ | ✓ |
| Codex | — | ✓ | ✓ | ✓ | ✓ |

Note: "Tool Use" = `command` primitive support. Source: `mode != "dropped"` for each adapter's command entry in adapter.toml. Claude Code, Cursor, Gemini CLI have non-dropped command projections; Kiro, Copilot, Codex have `mode=dropped`.

---

## Testing Strategy

**Verification mode:** Goal-based check + Visual/manual QA.

- Goal-based: `cd web && npm run build` exits 0.
- Visual/manual QA: Describe rendered state at 375px (mobile) and 1280px (desktop) for each enriched section, asserting structure matches AC1–AC4.
- AC5 verified mechanically with scoped grep.
- AC6 verified by reading each component's `<style>` block.
- AC7 manual visual QA at 375px/1280px — evidence recorded in PR description.
