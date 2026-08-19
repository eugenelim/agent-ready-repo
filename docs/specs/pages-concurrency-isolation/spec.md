# Spec: pages-concurrency-isolation

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [plan.md](plan.md)

> **Spec contract:** This document defines the accepted behavior and boundaries for this change. Implementation and verification must satisfy every acceptance criterion.

<!-- Mode: light (work-loop). No risk trigger fired: the change adds no dependency, crosses no security boundary, is not structural or a public-interface change, and is reversible rather than destructive. -->

## Objective

Prevent Pages validation runs from cancelling unrelated sessions while preserving a single, non-cancelling production deployment lane.

## Acceptance Criteria

- [x] AC1 — The workflow-level concurrency group is keyed so a `pull_request` run groups by `github.ref` and every non-PR event receives a unique `github.run_id` group; no two distinct refs share a group, while repeated runs of the same PR ref intentionally do so a superseded run is cancelled, and `github.head_ref` is not used.
- [x] AC2 — `cancel-in-progress` is true only for `pull_request` events.
- [x] AC3 — The `deploy` job carries its own repo-wide bare `pages` lane with `cancel-in-progress: false`, preserving rollout ordering with in-flight old-workflow runs that hold the workflow-level `pages` group while serializing main deployments without cancelling an in-flight deployment.
- [x] AC4 — `python3 tools/test-pages-workflow.py` exits 0; the deploy-blocking posture contract for path filters, gate presence, gate ordering, and `deploy-needs-build` is unchanged.
- [x] AC5 — Only the two concurrency blocks and their directly associated explanatory comments change; `paths:` filters, steps, gate ordering, `permissions:`, and action pins remain byte-identical.

## Boundaries

Always do:

- Keep build concurrency isolated per PR and non-cancelling for non-PR events.
- Serialize production Pages writers in the deploy job.

Never do:

- Use `github.head_ref` for the concurrency key.
- Change path filters, steps, gate ordering, permissions, action pins, or other workflows.

## Testing Strategy

Goal-based verification:

```bash
python3 tools/test-pages-workflow.py
python3 .claude/skills/work-loop/scripts/lint-spec-status.py
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pages.yml'))"
make lint-ruff
SKIP_SAST=1 make build-check
```

## Assumptions

- About 45% of recent Pages runs were cancelled; allowing qualifying runs to complete will increase Pages CI consumption.
- GitHub concurrency allows one running and one pending run per group, so a third queued deployment can still displace the pending deployment.
- The deploy lane gives mutual exclusion, NOT ordering. Because builds now run in distinct workflow groups, two Pages-relevant merges to `main` build concurrently and their deploy jobs enter the shared `pages` lane in build-completion order, which need not match merge order — so the older commit's content can be published last. This is a TRADE, not a pure win: under the previous unkeyed group the newer run cancelled the older one outright, so inversion was impossible. The window needs two Pages-relevant merges inside one build duration AND inverted build completion; it self-heals on the next Pages-relevant merge, and it does not lose data. A "deploy only if still the tip of `main`" guard is deliberately NOT added here — no acceptance criterion requires it and it introduces its own skip path. Tracked as `pages-deploy-ordering-not-guaranteed`.

## Deferred

No required-CI assertion covers `pages.yml` concurrency; `tools/test-pages-workflow.py` deliberately does not cover it. The gap is tracked as `pages-concurrency-has-no-regression-gate` in `workspace.toml`.
