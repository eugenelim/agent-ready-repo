# Spec: xd-ia-archetypes-objects

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0071 (ini-003), ADR-0038
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `information-architecture` skill in the `experience-design` pack gains a
complete set of page-archetype references covering 12 surface types —
marketing landing, onboarding, product workspace, dashboard/admin,
transactional flow, pack/catalogue, journey, tutorial, task how-to, reference
index, explanation, and multi-surface. Each archetype names the primary user
and job, the first-screen contract, the primary action and expected result,
the next action, proof requirements, read/write consequence, critical states,
and navigation behavior. The skill also acquires four contracts that govern
how content and interaction are shaped on any archetype: a product-object
mapping contract (what the user creates, receives, inspects, changes, or
approves; visual weight rules), a card-use test with non-card alternatives, an
attention contract (no-action / optional-progress / decision-required /
blocked-pending), and a read/write permission contract (read-only / draft /
proposed-write / confirmed-write / destructive / undo-recovery).

A new IA how-to guide — "Page archetypes: when to use which" — gives adopters
a 12-archetype quick-reference and a decision procedure for picking the right
archetype. The design journey page is updated so that IA and product-object
mapping appear as named steps. The pack is bumped to 1.3.0 to reflect these
additions.

Success looks like: a designer invoking `information-architecture` on an
unknown surface can identify its archetype, name its first-screen contract,
and apply the correct permission and attention contract without needing to ask
a follow-up question.

## Boundaries

### Always do

- Keep new reference content inside the IA skill's own `references/` directory.
- Reference `quality-floor.md` by its existing sibling path; do not copy it.
- Update both `pack.toml` and `.claude-plugin/plugin.json` in the same commit when bumping the pack version.
- Keep SKILL.md changes additive — extend the procedure with archetype-routing and product-object mapping as named steps; do not remove existing steps.
- Cross-reference the new `references/page-archetypes.md` from the SKILL.md procedure.

### Ask first

- Any change to `docs/guides/experience-design/README.md` beyond adding the new how-to link.
- Adding evals for archetype routing (future follow-on, not in scope here).
- Changing the journey page's human gates or `humanTouches` counts.

### Never do

- Touch `design-review/references/quality-floor.md` — state coverage belongs to `spec/xd-state-reviewer-doctrine`.
- Add a new top-level XD skill or a new top-level directory.
- Introduce a dependency outside the existing pack structure.
- Copy archetype definitions into SKILL.md body — reference the file instead.

## Testing Strategy

All deliverables are documentation and configuration artifacts. Verification mode:
**goal-based check** for file presence and structural completeness, plus
**visual / manual QA** for content completeness.

- **File presence and linking:** grep and find verify files exist and that SKILL.md references the new file.
- **Archetype count:** grep -c on page-archetypes.md verifies >=12 archetype sections.
- **Required fields per archetype:** goal-based scan confirms all 10 field labels present per archetype.
- **Pack version parity:** grep compares version strings in pack.toml and plugin.json.
- **Content completeness:** visual / manual QA — reader verifies all 12+ archetypes are substantive, four contracts are coherent, and the how-to guide produces an unambiguous archetype selection.
- **Contract-drift check:** python3 tools/check-contract-drift.py --root . exits 0.
- **workspace.toml parse:** python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))" exits 0.

## Acceptance Criteria

- [x] `packs/experience-design/.apm/skills/information-architecture/references/page-archetypes.md` exists and covers >=12 surface types.
- [x] Each archetype section contains all 10 required fields: primary user, job, first-screen contract, primary action, expected result, next action, proof, read/write consequence, critical states, navigation behavior.
- [x] `references/page-archetypes.md` includes a product-object mapping section defining the five object roles (creates / receives / inspects / changes / approves) with visual weight guidance.
- [x] `references/page-archetypes.md` includes a card-use test section with criteria for when a card is appropriate and named non-card alternatives.
- [x] `references/page-archetypes.md` includes an attention contract section defining all four levels: no-action, optional-progress, decision-required, blocked-pending.
- [x] `references/page-archetypes.md` includes a read/write permission contract section defining all six levels: read-only, draft, proposed-write, confirmed-write, destructive, undo-recovery.
- [x] `information-architecture/SKILL.md` procedure references `references/page-archetypes.md` and names archetype-routing and product-object mapping as numbered steps.
- [x] `docs/guides/experience-design/how-to/page-archetypes.md` exists with all 12+ archetypes in a quick-reference table and a "when to use which" decision procedure.
- [x] `docs/guides/experience-design/README.md` lists the new how-to guide.
- [x] `web/src/content/journeys/experience-design.md` names IA and product-object mapping as explicit steps.
- [x] `packs/experience-design/pack.toml` version is 1.3.0 and `.claude-plugin/plugin.json` version is 1.3.0.
- [x] `python3 tools/check-contract-drift.py --root .` exits 0.
- [x] `workspace.toml` has `spec/xd-ia-archetypes-objects` in the `shipped` list.

## Assumptions

- Technical: XD pack is at version 1.2.1 (source: packs/experience-design/pack.toml).
- Technical: References live in packs/experience-design/.apm/skills/<skill>/references/ (source: existing reading-patterns.md and wayfinding-concepts.md).
- Technical: How-to guides live in docs/guides/experience-design/how-to/ (source: existing guides).
- Technical: Design journey page is at web/src/content/journeys/experience-design.md (source: file confirmed).
- Process: Pack bump requires both pack.toml and .claude-plugin/plugin.json in the same commit (source: process Rule 4).
- Process: Parallel M3c spec may also target 1.3.0; this spec targets 1.3.0 on the assumption M3c has not merged at PR-open time (user confirmation 2026-07-23).
- Product: 12 surface types and specific archetype list per task brief (user confirmation 2026-07-23).
- Product: Four attention-contract levels and six read/write permission levels as specified (user confirmation 2026-07-23).
