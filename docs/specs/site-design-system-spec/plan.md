# Plan: site-design-system-spec

> This plan is the implementation strategy. The contract is [`spec.md`](spec.md).

## Approach

Docs-only with one stdlib Python lint script. No CSS changes, no Astro build changes, no new package dependencies. All token values are read from `web/src/styles/tokens.css` — the implementation authority. T3 can run in parallel with T2 since both depend only on the T1 inventory.

## Design (LLD)

### `web/src/design-system.md` structure

Eight H2 sections:

1. **Color tokens** — Two tables (Tier 1 primitive, Tier 2 semantic). Tier 1 table: token name | hex value | role note. Tier 2 table: token name | primitive target | zone (hero/dark | content/light | accent | CTA). Followed by the layering rule prose.
2. **Typography** — Sub-sections for font families, size scale (table: token | clamp/value | px range | usage), weight scale, tracking scale, leading scale.
3. **Spacing, radius, shadow, motion, z-index** — Space scale table. Section/layout tokens. Radius steps. Shadow philosophy (overlay only). Motion tokens. Z-index stack.
4. **Component vocabulary** — One H3 per component. Each entry: zone assignment, BEM classes used, semantic tokens referenced. Components: Hero, StatStrip, ThreeLoops, HumanGates, AdapterMatrix, InstallTerminal (terminal + CSS-only tabs), Copy button, PackCatalogue (loop-cards + pack-cards + scope chip), BuildYourOrg, Section band wrapper, SiteNav, SiteFooter, PackCard, `cat-card`.
5. **Zone rules** — Prose: dark zone vs. content/light zone. Token-to-zone mapping table.
6. **Dark mode equivalents** — Note that Astro has no dark mode. MkDocs dark mode via Material. List of dark-scheme values in `extra.css`.
7. **Card icon parity decision** — ThreeLoops `.loop__n` badges (sequential steps) vs. catalogue/pack cards (unordered, no badge). Decision: intentional asymmetry.
8. **Material-injected component audit** — Why `extra.css` uses raw hex. Overridden component families. Four known deviation values table.

### `tools/lint_zone_violations.py` design

```
parse args: path (default web/src/)
walk all .astro and .css files under path
for each file:
    state: inside_root_block = False
    for each line:
        skip if blank, or line matches ^\s*/\* (CSS block comment), or line matches ^\s*// (line-leading JS/TS comment — covers Astro frontmatter)
        if ":root" and "{": inside_root_block = True; continue
        if inside_root_block and "}": inside_root_block = False; continue
        if inside_root_block: continue  # token definitions — exempt
        skip SVG attribute lines (fill= stroke= xmlns= viewBox= etc.)
        if line matches CSS property: value; pattern:
            if value contains #[0-9a-fA-F]{3,6} or rgba(...): VIOLATION
exit 0 if no violations, 1 if any; print file:line: <value>
```

## Tasks

### T1 — Inventory tokens and component classes

**Depends on:** none
**Mode:** Goal-based (internal work material)

Read `web/src/styles/tokens.css` section by section; build working tables. Read each `.astro` file in `web/src/components/` and `web/src/pages/`; note BEM classes and `var(--ds-*)` tokens each uses. This output informs T2 and is not committed.

**Verification:** Inventory contains every token name from `tokens.css` (spot-check: grep for `ds-accent-subtle-dk`, `ds-lead-mono`, `ds-z-toast`).

### T2 — Write `web/src/design-system.md`

**Depends on:** T1
**Mode:** Goal-based (read-through against `tokens.css`)

Author the eight-section document per the LLD. All hex and clamp values copy verbatim from `tokens.css`.

**Verification:**
- `grep "ds-type-display" web/src/design-system.md` returns a match
- `grep "loop__n" web/src/design-system.md` returns a match
- `grep "#f8fafc\|#1a202c" web/src/design-system.md` returns matches (Material deviation values documented)

### T3 — Write `tools/lint_zone_violations.py`

**Depends on:** none (parallel with T2; the lint is structurally self-contained and does not consume the T1 inventory)
**Mode:** Goal-based

Implement the state-machine parser per the LLD. Use Python stdlib `re`, `os.walk`, `sys`. Keep under 120 lines. The `:root` block exclusion assumes flat, single-line-brace `:root` blocks (the current `tokens.css` shape); note this assumption in a comment so a future maintainer knows the brace-tracking is a boolean toggle, not a depth counter. Comment exclusion must handle both `/* … */` (CSS) and line-leading `//` (`^\s*//`, JS/TS comments in Astro frontmatter).

**Verification:**
- `python tools/lint_zone_violations.py web/src/` exits 0 (AC9)
- Create a temp file `tmp_test_violation.css` (outside `web/src/`) with `.foo { color: #e8952b; }`, run `python tools/lint_zone_violations.py` against its directory, confirm exit 1 and a `tmp_test_violation.css:1:` report; delete the temp file (AC8 — keeps the Astro source tree clean)

### T4 — Verify lint exits 0 on current codebase

**Depends on:** T3
**Mode:** Goal-based

`python tools/lint_zone_violations.py web/src/ && echo OK` exits 0. If exit 1, diagnose: false positive → tighten exclusion logic; real violation → file separately.

### T5 — Update `docs/specs/README.md`

**Depends on:** T2
**Mode:** Goal-based

Add row to active specs table.

**Verification:** `grep site-design-system-spec docs/specs/README.md` returns a match.

## Changelog

- 2026-07-23: Initial plan authored.
