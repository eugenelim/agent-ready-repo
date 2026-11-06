# Plugin publication has a reviewable trust boundary

- **Slug:** `plugin-publish-trust-boundary`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Parent intent:** capability:catalogue-publication
- **Governed by:** [spec/claude-plugin-route-scope](../../specs/claude-plugin-route-scope/spec.md); [spec/claude-plugin-hook-parity AC35](../../specs/claude-plugin-hook-parity/spec.md); [spec/marketplace-generator-single-source review concern 4](../../specs/marketplace-generator-single-source/spec.md)

## Outcome

Marketplace publication has an independently reviewable actor boundary, an approver preview, and current live-control evidence.

## Opportunity

The publish workflow still runs on a push to `main` without a build-job dependency, its environment approval has no description of the executable plugins being released, and its live ordinary-actor rejection canary is not recorded.

## What this absorbs

### plugin-publish-required-reviewer

`.github/workflows/publish-claude-plugins.yml` still triggers on `push: main` without `needs:` on the build-check job. The previously recorded `contents: write` grant has changed: the workflow's `permissions` block now gives `GITHUB_TOKEN` `contents: read` and the workflow mints a repository-scoped App token instead. The in-code half already shipped: `publish_claude_plugins.py` re-derives the predicate and refuses desynchronization. The remaining actor control is to gate publishing on `workflow_run` with `conclusion == success`, rather than rely on a GitHub Environment reviewer, which is not a control in a single-maintainer repository. `main` review and ruleset state require remote verification.

### publish-approval-preview-summary

The `claude-plugin-publish` environment gate on the `publish` job of `.github/workflows/publish-claude-plugins.yml` asks a human to release executable plugin code without showing what will publish. GitHub's approval UI supplies only the environment name and comment box. A summary step in the publish job cannot precede approval because `environment:` is job-level. Add a separate non-gated workflow on the same push that posts a run-summary preview: packs changed against current `claude-plugins-dist`, added or removed plugins, and hook entries that will register. It must not feed the publish job. AC35 clause 3 keeps build and publish in one job and permits a cross-job artifact handoff only when it verifies a producer-recorded digest before the token-bearing push. Add a spec note because this changes the approval step's practical meaning.

### publish-control-evidence-freshness-unbounded

Freshness is now bounded at 30 and 90 days, but `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json` still records `"live_branch_negative_tested": false`. Run and record the live ordinary-actor rejection canary, set `live_branch_negative_tested` true, and decide whether removal of a live settings-side ruleset must also be detected. **Unblocks when:** a maintainer runs the canary arm; settings writes are theirs. This was deferred because it needs a repository-settings action and live canary run rather than a code change a PR could carry.

## Assumptions

- `plugin-publish-required-reviewer` changed because the workflow now uses a repository-scoped App token while `main` review and ruleset state remain unverified locally.
- **Riskiest assumption:** a `workflow_run` publish job still builds the commit that passed the build job, because a `workflow_run` job starts on the default branch. Test it agent-only by extending `tools/lint-claude-plugin-publish-control.py` to assert the checked-out ref, with a passing and a failing fixture workflow.

## Current state — checked 2026-11-05

`.github/workflows/publish-claude-plugins.yml` still triggers on `push` to `main` with no `needs:` or `workflow_run`. `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json` still has `live_branch_negative_tested: false` and was observed on 2026-08-12. `tools/lint-claude-plugin-publish-control.py` warns past 30 days and fails past 90 days, which is 85 days today. **The lint starts failing after 2026-11-10 17:24 UTC unless the evidence is recaptured.** Recapturing needs the publisher App private key, so a maintainer must do it.

## Non-goals

- Detecting removal of a live settings-side ruleset, recorded as a documented residual.
- Recapturing the evidence or running the canary, which is an owner action outside the slices.
- Changing who holds repository settings or the publisher App.

## Readiness

- **Route:** brief. It is slices P2 and P3 of [`catalogue-publication-delivery`](../briefs/catalogue-publication-delivery.md). The workflow-gate slice extends the existing lint and its tests, and the preview is a separate non-gated workflow.
- **First slice:** gate publishing on a successful build run with `workflow_run` and `conclusion == success`, and make `lint-claude-plugin-publish-control.py` assert it. Check that the publish job still checks out the commit that was built, because a `workflow_run` job starts from the default branch.
- **Agent-only proof:** the lint's own test suite with fixture workflows, one that passes and one that publishes without the gate.
- **Answered:** detecting the removal of a live settings-side ruleset is out of scope. Record it as a documented residual in the AC35 spec note.
- **Blocking prerequisite, owner action:** the owner will recapture the publish-control evidence and run the ordinary-actor rejection canary (`tools/capture-publish-control-evidence.py`, then set `live_branch_negative_tested` true) before 2026-11-10. The first slice waits for it after that date.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
