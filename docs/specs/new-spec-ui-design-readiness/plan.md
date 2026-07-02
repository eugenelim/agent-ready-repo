# Plan: new-spec-ui-design-readiness

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Tasks

### Task 1 — Add step 4d to new-spec SKILL.md

- **Verification mode:** Visual / manual QA
- **Depends on:** none
- **Tests:** Read the amended file; confirm step 4d is present between 4c and 5;
  confirm trigger condition (Shape: ui), aesthetic-reference check, design-critique
  offer, design-intent AC requirement, select-or-note fallback, and work-loop
  cross-reference are all present.
- **Approach:** Edit `packs/core/.apm/skills/new-spec/SKILL.md`, inserting step 4d
  between the closing line of step 4c and the opening of step 5.

### Task 2 — Bump core pack to 0.9.0

- **Verification mode:** goal-based check
- **Depends on:** none
- **Tests:** `grep '"version"' .claude-plugin/marketplace.json | grep core` returns
  `0.9.0` after build-self.
- **Approach:** Edit `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  to `0.9.0`; run `make build-self FORCE=1`.

### Task 3 — Update changelog and backlog

- **Verification mode:** goal-based check
- **Depends on:** Tasks 1, 2
- **Tests:** `grep "new-spec-ui-design-readiness" docs/backlog.md` returns a Shipped
  tombstone; `grep "new-spec" docs/product/changelog.md` returns an Unreleased entry.
- **Approach:** Add `[Unreleased]` changelog entry; add Shipped tombstone to backlog
  `## experience-pack` section.
