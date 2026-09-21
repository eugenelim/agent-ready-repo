# Promote marooned changelog releases to published sections

- **Slug:** `changelog-marooned-entry-promotion`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim

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
- Land each promoted entry with exactly one blank line above and below its
  `##` heading. Since 2026-09-13,
  `tools/test_build_site_routing.py::test_every_changelog_section_is_separated`
  fails any pull request into `main` that does not. The separator defects that
  sat around five of these entries were normalized that day; their marooning
  was not touched, and the count here is unchanged.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
