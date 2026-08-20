# Plan: pages-concurrency-isolation

- **Spec:** [spec.md](spec.md)
- **Status:** Done

> **Plan contract:** This plan records the smallest implementation and verification sequence required to satisfy the linked specification.

<!-- Lean fill: only the workflow edit and its goal-based verification are recorded. Dependency, rollout, migration, and test-stub sections are omitted because this is a reversible CI configuration change with no new code path. -->

## Approach

Separate build isolation from deployment serialization: apply the ratified AC12 workflow-level expression, then add the non-cancelling bare `pages` job-level lane to the sole Pages writer so it preserves rollout ordering with in-flight old-workflow runs holding the workflow-level `pages` group.

## Tasks

1. Replace the workflow-level Pages concurrency block with the AC12 PR/non-PR expression.
   Tests: no stub (goal-based).
   Done when: PR runs group by `github.ref`, while every non-PR run uses `github.run_id` and is not cancelled.

2. Add the bare `pages` non-cancelling concurrency lane to the `deploy` job, preserving rollout ordering with in-flight old-workflow runs holding the workflow-level `pages` group.
   Tests: no stub (goal-based).
   Done when: main deploys share the bare `pages` job-level lane without cancelling an in-flight deployment.

3. Run the workflow posture, specification-status, YAML, lint, and build-check gates.
   Tests: no stub (goal-based).
   Done when: all requested verification commands complete successfully.
