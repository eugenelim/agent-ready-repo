# Required checks and Pages deployments preserve their intended ordering

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/ci-gate-parallelization AC3](../../specs/ci-gate-parallelization/spec.md)
- **Authority:** [spec/pages-concurrency-isolation AC3](../../specs/pages-concurrency-isolation/spec.md)

## Outcome

Repository controls preserve trustworthy pull-request gating and current Pages publication.

## Opportunity

The required-check control and Pages branch protection are partly external GitHub configuration, while the current Pages deployment lane serializes writers without ordering commits.

## What this absorbs

### ci-gate-parallelization-required-workflow-pinned-ref

AC3 makes the aggregator job the sole required status check. `pull_request` evaluates `build-check.yml` and its posture test, `tools/test-build-check-workflow.py`, from the PR's own ref. A coordinated PR that edits the workflow's `needs:`, the aggregator `env:` block, its `!= "success"` comparisons, and the posture test can present a green required check with gates that did not run. This is closable, not inherent. Decide whether to apply a repository ruleset requiring workflows resolved from a PINNED ref, preventing a PR from defining its gating check, and/or a `CODEOWNERS` entry for `.github/workflows/**` plus the posture test, requiring a second human for the bypass. The `CODEOWNERS` route was declined because it would block this repository's sole maintainer, and this repository has no `CODEOWNERS` today. Branch-protection changes are outside that spec's scope. `.github/workflows/build-check.yml:8` contains `"on:"`. Whether GitHub resolves a required workflow from a pinned reference requires the current sanitized ruleset configuration.

### pages-build-job-not-a-required-check

`.github/workflows/pages.yml:70` defines the `build:` job. That job carries both site builds, the plugin suite, rendered-output invariants, and the browser gate, but it may not be a required status check. Its `paths:` filter means it cannot simply be selected as one. Whether its status context is required requires current sanitized protection or ruleset configuration. This was observed on 2026-08-23 in PR #1036.

### pages-deploy-ordering-not-guaranteed

The Pages deploy lane serializes but does not order deployments, so an older commit can publish last after two close merges to `main`. `.github/workflows/pages.yml:234` contains `group: pages`; it has one concurrency group but no commit-order or “latest SHA only” guard. Unblocks when: ready now.

## Assumptions

- The required-workflow question needs the current sanitized repository ruleset configuration.
- The Pages required-context question needs current sanitized branch-protection or ruleset configuration.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
