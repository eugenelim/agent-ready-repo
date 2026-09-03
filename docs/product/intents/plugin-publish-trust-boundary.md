# Plugin publication has a reviewable trust boundary

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/claude-plugin-route-scope](../../specs/claude-plugin-route-scope/spec.md)
- **Authority:** [spec/claude-plugin-hook-parity AC35](../../specs/claude-plugin-hook-parity/spec.md)
- **Authority:** [spec/marketplace-generator-single-source review concern 4](../../specs/marketplace-generator-single-source/spec.md)

## Outcome

Marketplace publication has an independently reviewable actor boundary, an approver preview, and current live-control evidence.

## Opportunity

The publish workflow still runs on a push to `main` without a build-job dependency, its environment approval has no description of the executable plugins being released, and its live ordinary-actor rejection canary is not recorded.

## What this absorbs

### plugin-publish-required-reviewer

`.github/workflows/publish-claude-plugins.yml` still triggers on `push: main` without `needs:` on the build-check job. The previously recorded `contents: write` grant has changed: line 51 now gives `GITHUB_TOKEN` `contents: read` and the workflow mints a repository-scoped App token instead. The in-code half already shipped: `publish_claude_plugins.py` re-derives the predicate and refuses desynchronization. The remaining actor control is to gate publishing on `workflow_run` with `conclusion == success`, rather than rely on a GitHub Environment reviewer, which is not a control in a single-maintainer repository. `main` review and ruleset state require remote verification.

### publish-approval-preview-summary

The `claude-plugin-publish` environment gate at `.github/workflows/publish-claude-plugins.yml:56` asks a human to release executable plugin code without showing what will publish. GitHub's approval UI supplies only the environment name and comment box. A summary step in the publish job cannot precede approval because `environment:` is job-level. Add a separate non-gated workflow on the same push that posts a run-summary preview: packs changed against current `claude-plugins-dist`, added or removed plugins, and hook entries that will register. It must not feed the publish job. AC35 clause 3 keeps build and publish in one job and permits a cross-job artifact handoff only when it verifies a producer-recorded digest before the token-bearing push. Add a spec note because this changes the approval step's practical meaning.

### publish-control-evidence-freshness-unbounded

Freshness is now bounded at 30 and 90 days, but `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json:31` still records `"live_branch_negative_tested": false`. Run and record the live ordinary-actor rejection canary, set `live_branch_negative_tested` true, and decide whether removal of a live settings-side ruleset must also be detected. **Unblocks when:** a maintainer runs the canary arm; settings writes are theirs. This was deferred because it needs a repository-settings action and live canary run rather than a code change a PR could carry.

## Assumptions

- `plugin-publish-required-reviewer` changed because the workflow now uses a repository-scoped App token while `main` review and ruleset state remain unverified locally.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
