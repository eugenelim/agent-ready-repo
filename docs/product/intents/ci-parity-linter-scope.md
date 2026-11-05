# Extend CI parity to each remaining workflow

- **Slug:** `ci-parity-linter-scope`
- **Status:** Withdrawn
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [spec/local-gate-ci-parity](../../specs/local-gate-ci-parity/spec.md)

## Disposition — withdrawn 2026-11-05, decided: not worth doing now

remote CI is the gating authority since ADR-0113, nothing depends on this intent, and `WORKFLOW_SCOPE` in `tools/lint-ci-parity.py` states a reason for every workflow it leaves out; `python3 tools/lint-ci-parity.py` passes today (169 steps in the one in-scope workflow, all dispositioned). Reopen if a gate lands in `docs.yml`, `ci-security.yml` or `catalogue-tooling-ci-gates.yml` with no local counterpart and that causes a missed failure.

## Outcome

Each newly admitted CI workflow has a local-correspondence check and a workflow-specific exemption inventory.

## Opportunity

`tools/lint-ci-parity.py` only gates local-to-CI correspondence for `build-check.yml`, leaving the other 17 workflows classified out of scope.

## What this absorbs

### ci-parity-docs-yml-out-of-scope

`docs.yml`, `catalogue-tooling-ci-gates.yml`, and `ci-security.yml` are out of scope in `tools/lint-ci-parity.py`'s `WORKFLOW_SCOPE` map. The `docs.yml` entry of `WORKFLOW_SCOPE` says: `Out of scope for this gate. \`make pre-pr\` overlaps much of it`. A gate added to any of those workflows can land without a local counterpart or signal. `make pre-pr` overlaps much of `docs.yml`, but nothing verifies that overlap; the honest current claim is “one workflow is parity-gated.” Extend the in-scope set one workflow at a time. Each workflow needs its own exemption inventory; `docs.yml`'s per-layer jobs and lifecycle-hook job are the bulk of the work. This is not a one-line change. Unblocks when picked up; it has no dependency.

## Assumptions

- Workflow admission remains incremental so each exemption inventory is reviewable.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
