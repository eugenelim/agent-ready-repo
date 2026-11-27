# Spec: Durable Outputs contract alignment

- **Status:** Draft
- **Owner:** repository maintainer
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none
- **Risk triggers:** security-boundary

## Outcome

Spec authors and reviewers receive one consistent rule for Durable Outputs.
Approval protects that section, so a later change follows the amendment path.

## What Changes

- The new-spec template identifies Durable Outputs as protected after approval.
- The template points to the existing amendment reference for the full rule.
- Tests and an eval cover the distinction between protected outputs and working material.

## Scope and Non-goals

The change covers the new-spec template, its tests and eval, required core release
metadata, and generated adapters. Supervisor behavior, amendment authority,
other protected sections, and shipped historical specs retain their contracts.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Author guidance | Required | packs/core/.apm/skills/new-spec/assets/spec.md | core maintainer | Section classification check | Template agrees with the amendment reference |
| Release history | Required | docs/product/changelog.d/ | core maintainer | Core patch fragment | Correction recorded with matching release metadata |

## Agent Rules

```gate-declaration
[
  {"argv": ["python3", "-m", "pytest", "packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py", "packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py", "packs/core/tests/skills/new-spec/test_wave4_durable_outputs.py", "packs/core/tests/skills/work-loop/test_supervisor_projector.py", "-q"], "cwd": ".", "expected_exit": 0},
  {"argv": ["make", "lint-ruff", "lint-mypy"], "cwd": ".", "expected_exit": 0}
]
```

### Always do

- Keep the amendment reference as the owner of the full protected-section rule.
- Edit pack sources and regenerate installed copies.

### Ask first

- Changes to the existing amendment authority or supervisor behavior.

### Never do

- Relabel Durable Outputs as freely editable working material.
- Rewrite shipped specs to retrofit the corrected template.

## Testing Strategy

AC-0001 uses a bounded content check of the template tier note against the
amendment reference. The existing supervisor protected-edit test verifies the
runtime protection. The skill eval exercises an author correcting an approved
Durable Outputs section. Source lint, type checks, precheck, and a rendered
Codex install verify packaging and generated parity.

## Acceptance Criteria

- [ ] **AC-0001:** The new-spec template identifies Durable Outputs as protected after approval, requires an amendment for changes, and excludes it from the working-material list, in agreement with the amendment reference and supervisor.

## Accepted Risk

none

## Terminal Intent

`code` — align the template and ship the regression coverage.

## Follow-ons

none

## Assumptions

none
