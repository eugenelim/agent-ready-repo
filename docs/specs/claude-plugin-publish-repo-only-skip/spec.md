# Spec: Claude plugin publish skips repo-only pack changes

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** integration
- **Risk triggers:** security-boundary

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`, `What
> Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material.

## Outcome

Repository maintainers no longer get a Claude plugin deployment approval for a push that changes only repo-only packs, such as the `core` version bump that rides with most changes. A pack that is published, or that becomes publishable or unpublishable, still starts the publish run.

## What Changes

- Two catch-all path filters that match every pack's `pack.toml` and `plugin.json` are removed — `.github/workflows/publish-claude-plugins.yml`
- The roster lint's expected push paths drop the same two entries and its comment states the new reasoning — `tools/lint-plugin-roster.py`
- The lint's tests assert the narrower set and the cases that keep publication safe — `tools/test-lint-plugin-roster.py`
- The workflow header and the fleet and route descriptions state the current reach — `.github/workflows/publish-claude-plugins.yml`, `docs/architecture/verification-graph.md`, `docs/architecture/distribution-routes.md`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | The two docs describe the push filter | `docs/architecture/verification-graph.md`, `docs/architecture/distribution-routes.md` | repository owner | each statement about the filter matches the workflow | both passages read whole |
| Maintainer procedure | The workflow header explains the filter to the next editor | `.github/workflows/publish-claude-plugins.yml` header | repository owner | the header names what triggers a publish and why repo-only packs do not | header read whole |
| Release history | A tools and workflow change, no pack version moves | none — no published pack or package changes | n/a | n/a | n/a |

## Agent Rules

### Always do

- Keep every published pack's directory and every job input in the push filter.
- Change the workflow's path list and the roster lint's expected set in one commit.

### Ask first

- Any change to which packs are published, or to the `claude-plugin-publish` environment.

### Never do

- Add a `paths-ignore`, or a path pattern with a wildcard in the pack segment.
- Edit a roster so that the lint passes without confirming what is published.

## Testing Strategy

- **TDD** for the roster lint's expected set and for path matching: tests written before the filter changes.
- **Goal-based check** for the shipped workflow: the roster lint run against the real file.
- **Manual QA** by replaying recent `main` commits through the old and new filters and recording the counts.

## Acceptance Criteria

- [x] No push path of `publish-claude-plugins.yml` has a wildcard in the pack segment.
- [x] The roster lint's expected push paths are exactly the sixteen published pack globs and the ten job-input paths.
- [x] The roster lint rejects a workflow whose paths include `packs/*/pack.toml`.
- [x] The roster lint rejects a workflow whose paths include `packs/*/.claude-plugin/plugin.json`.
- [x] For each pack the roster lint lists as repo-only, its `pack.toml`, its `.claude-plugin/plugin.json`, and a skill file under it match no push path.
- [x] For each pack the roster lint lists as published, its `pack.toml` and its `.claude-plugin/plugin.json` match a push path.
- [x] The workflow file's own path is a push path, so a commit that moves a pack between the rosters starts a publish run.
- [x] The roster lint fails when a pack moves between its published and repo-only rosters and the workflow's path list does not change with it.
- [x] `tools/lint-plugin-membership.py` and `tools/lint-plugin-roster.py` are both steps of the gate chain that runs on every pull request.
- [x] The workflow keeps its `workflow_dispatch` trigger.
- [x] The workflow's publish job keeps `environment: claude-plugin-publish`.
- [x] `python3 tools/test-lint-plugin-roster.py` passes.
- [x] `python3 tools/lint-plugin-roster.py` passes on the repository.
- [x] `make lint-ruff` passes.
- [x] `make lint-mypy` passes.
- [x] `make precheck` passes.

## Follow-ons

- repository owner: exclude non-shipping files (such as `packs/*/tests/**`) of published packs from the push filter — not started; needs a check of what each plugin ships.

## Assumptions

none
