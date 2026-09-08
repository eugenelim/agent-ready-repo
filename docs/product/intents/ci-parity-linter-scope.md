# Extend CI parity to each remaining workflow

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/local-gate-ci-parity](../../specs/local-gate-ci-parity/spec.md)

## Outcome

Each newly admitted CI workflow has a local-correspondence check and a workflow-specific exemption inventory.

## Opportunity

`tools/lint-ci-parity.py` only gates local-to-CI correspondence for `build-check.yml`, leaving three workflows explicitly out of scope.

## What this absorbs

### ci-parity-docs-yml-out-of-scope

`docs.yml`, `catalogue-tooling-ci-gates.yml`, and `ci-security.yml` are out of scope in `tools/lint-ci-parity.py`'s `WORKFLOW_SCOPE` map. `tools/lint-ci-parity.py:92` says: `Out of scope for this gate. \`make pre-pr\` overlaps much of it`. A gate added to any of those workflows can land without a local counterpart or signal. `make pre-pr` overlaps much of `docs.yml`, but nothing verifies that overlap; the honest current claim is “one workflow is parity-gated.” Extend the in-scope set one workflow at a time. Each workflow needs its own exemption inventory; `docs.yml`'s per-layer jobs and lifecycle-hook job are the bulk of the work. This is not a one-line change. Unblocks when picked up; it has no dependency.

## Assumptions

- Workflow admission remains incremental so each exemption inventory is reviewable.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
