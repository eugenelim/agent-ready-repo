# Spec: spec-A-workspace-status-rename

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0067](../../rfc/0067-session-arc-conventions-and-pack-workflow-guide.md) — driving RFC; Change A defines the rename scope, operative/historical classification, and lint gate
  - [ADR-0054](../../adr/0054-session-arc-verb-taxonomy-and-pack-type-classification.md) — verb taxonomy and clean-retire decision
  - [RFC-0050](../../rfc/0050-the-experience-pack.md) — clean-retire rename precedent: no install-time alias for skill/pack renames; operative references swept in the same PR (established for the design-craft → experience-design rename)
- **Contract:** none — skill directory rename and documentation changes; no API contract.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A user reading or invoking the workspace-level cold-start orient skill encounters it only under its new name, `workspace-status`. Every operative reference in the repo has been updated; historical records (frozen ADR bodies, changelog entries, shipped spec bodies) are preserved as-is. The `docs/guides/_shared/how-to/author-a-skill.md` guide gains a `## Naming your skill` section embedding the verb taxonomy from ADR-0054. A lint gate over operative files returns zero `check-workspace` hits. Pack authors opening `author-a-skill.md` see the taxonomy and an intro pointer to the pack workflow design guide (Spec D).

## Boundaries

### Always do

- Derive the full operative reference list from `git ls-files | xargs grep -l "check-workspace"` before editing, not from the RFC's illustrative list (~46 files).
- Classify each hit as operative or historical using the RFC-0067 §Change A classification rules before rewriting.
- Update `packs/core/pack.toml` skills array, `packs/core/.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json` in the same commit as the directory rename.
- Rebuild projected paths via `make build-self` after all source edits, and commit the regenerated projected tree in the same PR.
- Run the lint gate (`grep -rn "check-workspace"` scoped to the operative path set, excluding the explicit historical set) and confirm zero hits before opening the PR.

### Ask first

- Removing or reordering entries in the `description:` trigger list beyond the RFC-specified additions.
- Changing the wording of the verb taxonomy table (beyond correcting a typo); the table is ADR-0054-normative.
- Any operative file that, after inspection, appears to carry both an operative and a historical reference in the same location.

### Never do

- Edit frozen ADR bodies (ADR-0051, ADR-0053): their `check-workspace` references are historical records per CONVENTIONS §2.
- Edit `docs/product/changelog.md` shipping entries that named `check-workspace` — those are dated release history.
- Edit files under `docs/specs/` for this purpose — spec prose is excluded from the lint as spec content, not as a projected surface. (The new Draft specs spec-A..D legitimately reference `check-workspace` in their prose and are correct to exclude.)
- Edit this RFC's own body (`docs/rfc/0067-*.md`): it is the source of the classification rules, not a target of the rename.
- Add an alias or backward-compatibility shim for `check-workspace` — the clean retire is the decision (ADR-0054).

## Testing Strategy

All criteria use **goal-based check**: each corrected reference is verifiable by running a grep or diff against the oracle (the renamed source path, the verb taxonomy, or the lint gate output). No production code changes; no TDD-mode tasks.

One **manual QA** step: after `make build-self`, confirm the skill appears in the projected `.claude/skills/workspace-status/` directory and is absent from `.claude/skills/check-workspace/`.

## Acceptance Criteria

- [ ] **AC1.** `packs/core/.apm/skills/workspace-status/SKILL.md` exists; `packs/core/.apm/skills/check-workspace/` does not.
- [ ] **AC2.** `SKILL.md` frontmatter `name:` field reads `workspace-status`; `description:` includes all RFC-0067 §A1 trigger phrases: "workspace status", "where am I", "orient me", "session start", "what's ready", "show the queue", "what's next", and any cold-start orientation phrasing.
- [ ] **AC3.** `packs/core/pack.toml` skills array entry updated from `check-workspace` to `workspace-status`.
- [ ] **AC4.** `packs/core/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` updated.
- [ ] **AC5.** Lint gate: `grep -rn "check-workspace"` over all `git ls-files` output, excluding the explicit historical set (frozen ADR-0051, ADR-0053, `docs/product/changelog.md`, `docs/specs/`, `docs/rfc/0067-*.md`), returns zero hits.
- [ ] **AC6.** Projected path `.claude/skills/workspace-status/` exists; `.claude/skills/check-workspace/` does not.
- [ ] **AC7.** `docs/guides/_shared/how-to/author-a-skill.md` gains a `## Naming your skill` section (after `## Body structure`) with the verb table from ADR-0054 §Decision and the banned-label list.
- [ ] **AC8.** `author-a-skill.md` intro gains the sentence: "If you're authoring the first skill in a new pack, read [Pack workflow design](../explanation/pack-workflow-design.md) first — it tells you how to design the pack's arc before writing individual skills."
- [ ] **AC9.** All operative references in `AGENTS.md`, `packs/core/seeds/AGENTS.md`, `packs/core/README.md`, `.claude/skills/README.md`, `docs/CONVENTIONS.md`, `docs/product/journeys/`, `docs/product/roadmap.md`, `docs/product/workspace-toml-deps.md`, `docs/product/projects/_template.md`, `docs/product/findings/README.md`, cross-pack routing references, `site/docs/`, `web/`, `docs/rfc/README.md`, and `docs/rfc/0064-ini-001-ai-native-ecosystem.md` (Draft — body editable) are updated to `workspace-status`.
- [ ] **AC10.** `make build-check` exits 0 (no projected-path drift detected).
- [ ] **AC11.** `docs/product/changelog.md` gains an `[Unreleased]` entry noting the rename.

## Assumptions

- Technical: the repo has approximately 30–46 operative `check-workspace` references at time of implementation; the exact list is derived from `git ls-files | xargs grep -l "check-workspace"` at implementation time (source: RFC-0067 §Change A).
- Technical: `make build-self` regenerates all projected paths including `.claude/skills/`, adapter skill directories, `plugin.json`, and `marketplace.json` (source: CONVENTIONS §Pack source-of-truth split).
- Process: frozen ADR bodies (ADR-0051, ADR-0053) contain `check-workspace` as historical record; they must not be edited (source: CONVENTIONS §2).
- Process: `docs/rfc/0064-ini-001-ai-native-ecosystem.md` is Draft status and its body is editable (source: RFC-0067 §Change A operative reference list).
