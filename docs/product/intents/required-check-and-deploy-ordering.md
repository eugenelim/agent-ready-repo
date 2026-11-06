# Required checks and Pages deployments preserve their intended ordering

- **Slug:** `required-check-and-deploy-ordering`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [spec/ci-gate-parallelization AC3](../../specs/ci-gate-parallelization/spec.md); [spec/pages-concurrency-isolation AC3](../../specs/pages-concurrency-isolation/spec.md)

## Outcome

Repository controls preserve trustworthy pull-request gating and current Pages publication.

## Opportunity

The required-check control and Pages branch protection are partly external GitHub configuration, while the current Pages deployment lane serializes writers without ordering commits.

## What this absorbs

### ci-gate-parallelization-required-workflow-pinned-ref

AC3 made the aggregator job the required status check; branch protection read on 2026-11-04 requires it together with `gate-main`, `gate-sast`, `gate-export-boundary`, and `gate-credbroker`. `pull_request` evaluates `build-check.yml` and its posture test, `tools/test-build-check-workflow.py`, from the PR's own ref. A coordinated PR that edits the workflow's `needs:`, the aggregator `env:` block, its `!= "success"` comparisons, and the posture test can present a green required check with gates that did not run. This is closable, not inherent. Decide whether to apply a repository ruleset requiring workflows resolved from a PINNED ref, preventing a PR from defining its gating check, and/or a `CODEOWNERS` entry for `.github/workflows/**` plus the posture test, requiring a second human for the bypass. The `CODEOWNERS` route was declined because it would block this repository's sole maintainer, and this repository has no `CODEOWNERS` today. Branch-protection changes are outside that spec's scope. The `on:` block of `.github/workflows/build-check.yml` is where its triggers are declared. Whether GitHub resolves a required workflow from a pinned reference requires the current sanitized ruleset configuration.

### pages-build-job-not-a-required-check

`.github/workflows/pages.yml` defines the `build:` job. That job carries both site builds, the plugin suite, rendered-output invariants, and the browser gate, but it may not be a required status check. Its `paths:` filter means it cannot simply be selected as one. Whether its status context is required requires current sanitized protection or ruleset configuration. This was observed on 2026-08-23 in PR #1036.

### pages-deploy-ordering-not-guaranteed

The Pages deploy lane serializes but does not order deployments, so an older commit can publish last after two close merges to `main`. The `deploy` job of `.github/workflows/pages.yml` declares `group: pages`; it has one concurrency group but no commit-order or “latest SHA only” guard. Unblocks when: ready now.

## Assumptions

- The required-workflow question needs the current sanitized repository ruleset configuration.
- The Pages required-context question needs current sanitized branch-protection or ruleset configuration.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

## Non-goals

- No repository ruleset requiring a pinned-ref workflow and no `CODEOWNERS` entry; the owning spec accepts that residual and a second-reviewer rule would block the sole maintainer.
- No branch-protection or ruleset change is made by an agent; reading the sanitized ruleset stays a manual follow-up.

**Riskiest assumption:** comparing `github.sha` with the tip of `main` inside the `deploy` job is enough to stop an older commit publishing last. Agent-only test: `tools/test-pages-concurrency.py` with a mutation that removes the guard must fail, and a case where the SHA differs from the tip must skip the deploy.

## Readiness

Route: direct-light for the agent part, with the ruleset questions split off as a named manual follow-up.

Checked 2026-11-05: the `deploy` job in `.github/workflows/pages.yml` still has `group: pages` and no commit-order guard. First slice: the deploy job runs only when `github.sha` still equals the tip of `main`, proved by `tools/test-pages-concurrency.py` with a mutation that removes the guard. Recommended answer on the pinned-ref ruleset: do not pursue it. The owning spec accepts the residual, and a second-reviewer rule would block the sole maintainer. Whether the Pages `build:` job is a required context is a read of the sanitized ruleset through `gh api`; that read and any decision from it is a manual, non-blocking follow-up and does not gate the guard.
