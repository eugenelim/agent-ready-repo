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
6. **Dark mode equivalents** — Note that Astro has no dark mode. Starlight dark mode via `[data-theme='dark']`. Token-resolved values table.
7. **Card icon parity decision** — ThreeLoops `.loop__n` badges (sequential steps) vs. catalogue/pack cards (unordered, no badge). Decision: intentional asymmetry.
8. **Starlight CSS audit** — Mostly token-compliant (imports `tokens.css`). Two known `#ffffff` deviations table.

### `tools/lint_zone_violations.py` design

```
parse args: path (default web/src/); exit 2 if path missing or not a dir
canonical_token = path / "styles/tokens.css"
rglob all .astro and .css files under path; exit 2 on OSError reading any file
for each file:
    state: in_root_block=False, in_block_comment=False,
           in_declaration=False, decl_buffer=""
    is_token_file = (file == canonical_token)  # only this file gets :root exemption
    for each line:
        skip if blank
        if in_block_comment:
            if "*/" found: clear state, keep code after "*/"; else: skip line
        strip inline /* ... */ from line; if unclosed /* remains: truncate, set in_block_comment=True
        skip if now blank, or line matches ^\s*// (JS/TS comment)
        if is_token_file and ":root {": in_root_block=True; continue
        if is_token_file and in_root_block: skip (token definitions exempt); clear on "}"
        skip SVG attribute lines (fill= stroke= xmlns= viewBox= etc.)
        if in_declaration:
            append line to decl_buffer; scan line for #hex (3/4/6/8 digits)
            if ";" or block boundary: scan decl_buffer for rgba(); clear state
        elif line matches CSS property: value; pattern:
            scan value for #hex (3/4/6/8 digits) and rgba()
            if no ";" in value: in_declaration=True, decl_buffer=value (multi-line)
exit 0 if no violations, 1 if any; exit 2 on unreadable file; print file:line: <value>
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
- `grep "Starlight\|text-invert" web/src/design-system.md` returns matches (Starlight deviation values documented)

### T3 — Write `tools/lint_zone_violations.py`

**Depends on:** none (parallel with T2; the lint is structurally self-contained and does not consume the T1 inventory)
**Mode:** Goal-based

Implement the state-machine parser per the LLD. Use Python stdlib `re`, `pathlib`, `sys`. Traverse with `Path.rglob` (simpler than `os.walk` for this use case). The `:root` block exclusion is gated by file path (only the canonical token file at `<root>/styles/tokens.css`) and assumes flat, single-line-brace `:root` blocks; the brace-tracking is a boolean toggle, not a depth counter. Comment exclusion must handle: CSS block comments `/* … */` (including multi-line and same-line trailing variants), and line-leading `//` (`^\s*//`, JS/TS comments in Astro frontmatter). Multi-line CSS declarations (property name and value on separate lines) require declaration-state tracking through the terminating semicolon. Line count is ~170 due to declaration and comment state tracking, plus inline-comment stripping.

**Verification:**
- `python tools/lint_zone_violations.py web/src/` exits 0 (AC9)
- Create a temp file `tmp_test_violation.css` (outside `web/src/`) with multi-line content:
  `.foo {\n  color: #e8952b;\n}` (property on its own line, matching the codebase's
  multi-line formatting convention), run `python tools/lint_zone_violations.py` against
  its directory, confirm exit 1 and a `tmp_test_violation.css:2:` report; delete the temp
  file (AC8 — keeps the Astro source tree clean). Note: inline single-line rules
  `.foo { color: #hex; }` are not detected — see lint docstring for the scope assumption.

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
