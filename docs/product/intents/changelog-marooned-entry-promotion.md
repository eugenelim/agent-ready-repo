# Promote marooned changelog releases to published sections

- **Status:** Draft
- **Level:** feature

## Outcome

Every released changelog entry is a free-standing version section that publishes to `/now/`, while genuinely unreleased content remains under the first `[Unreleased]` heading.

## Opportunity

Fifty-nine versioned releases remain nested under `[Unreleased]` and therefore do not publish to `/now/`; 48 genuinely unreleased bare sections are interleaved across three `[Unreleased]` regions.

## What this absorbs

### changelog-promote-marooned-entries

- **Authority:** [RFC-0095 D3](../../rfc/0095-changelog-entry-obligation.md)
- Promote the 59 nested versioned changelog entries to free-standing `##` sections, separating them from 48 interleaved genuinely-unreleased bare sections across three `[Unreleased]` regions.
- Lower `_MAROONED_RELEASE_BASELINE` as entries land. `tests/roster/test_workspace_status_projection.py` line 143 still sets `_MAROONED_RELEASE_BASELINE = 59`, and the baseline has not decreased.
- Restore Keep a Changelog ordering with `[Unreleased]` first. That heading is now first, but the promotion work remains.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
