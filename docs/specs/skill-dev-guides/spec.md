# Spec: Skill development guides

**Status:** Shipped

## Objective

Add skill-authoring reference guides to `guides/_shared/`, wire them into `author-a-skill.md` and the shared README, move the output-rendering directive catalog from `guides/core/reference/` to `guides/_shared/reference/` (where skill authors can find it), and trim the duplicated spec-compliance bullets from `packs/AGENTS.md` in favour of pointers to the guides.

## Testing Strategy

Goal-based: verify each artifact exists at its declared path and `agentbundle catalogue lint --root . --deep` exits 0.

## Acceptance Criteria

- [x] `guides/_shared/reference/skill-ux-patterns.md` exists — column alignment, truncation limits, persistent command bar, delete-gate box, card format, progress reporting, cross-link to `output-rendering.md`
- [x] `guides/_shared/reference/skill-script-conventions.md` exists — CLI flag conventions, usage docblocks, shortcut IDs, `.apm/shared-libs/` pattern, idempotent setup, correct first-value onboarding key semantics, pack-config API usage examples
- [x] `guides/_shared/how-to/browser-automation-skill.md` exists — persistent Chrome profile auth, bearer token interception, Teams/Entra caveats, session check, two-mode Playwright usage, `ui-patterns.md` maintenance, probe files as data layer
- [x] `guides/_shared/reference/output-rendering.md` exists (moved from `guides/core/reference/`); old location has a redirect note; `.claude/skills/README.md` reference updated
- [x] `guides/_shared/how-to/author-a-skill.md` updated — `tools/lint-*` replaced with `agentbundle catalogue lint`, kebab-case `name` rule added, Kiro-truncation rationale added, new sections (Output rendering, Script conventions, Setup skills, Runtime config), See also expanded
- [x] `guides/_shared/README.md` indexes all new/moved files under their correct quadrant sections
- [x] `packs/AGENTS.md` spec-compliance bullets replaced with pointer to `author-a-skill.md` plus three catalogue-specific craft pointers; pack-workflow-specific rules remain
- [x] `agentbundle catalogue lint --root . --deep` passes
