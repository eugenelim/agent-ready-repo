# Promote marooned changelog releases to published sections

- **Slug:** `changelog-marooned-entry-promotion`
- **Status:** Accepted
- **De-risked:** 2026-11-05
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
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
- Lower `_MAROONED_RELEASE_BASELINE` as entries land. `tests/roster/test_workspace_status_projection.py` still sets `_MAROONED_RELEASE_BASELINE = 59`, and the baseline has not decreased.
- Restore Keep a Changelog ordering with `[Unreleased]` first. That heading is now first, but the promotion work remains.
- Land each promoted entry with exactly one blank line above and below its
  `##` heading. Since 2026-09-13,
  `tools/test_build_site_routing.py::test_every_changelog_section_is_separated`
  fails any pull request into `main` that does not. The separator defects that
  sat around five of these entries were normalized that day; their marooning
  was not touched, and the count here is unchanged.

## Assumptions

- None.
- **Riskiest assumption:** moving the 59 entries leaves each one's text unchanged and does not reorder what `/now/` publishes beyond adding them. Test it agent-only by running the scripted promotion on a copy, comparing entry text byte for byte, and comparing the projection before and after.

## Current state — checked 2026-11-05

`docs/product/changelog.md` still holds 59 versioned entries nested under `[Unreleased]` (the ratchet in `tests/roster/test_workspace_status_projection.py` reads 59 and the nested-entry function counts 59), and 48 bare sections sit beside them (a stricter parse of the prototype found 49). The file has `## [Unreleased]` openers at lines 66, 6912 and 9234.

A prototype transform run on a copy (outside the repository tree) promotes all 59 entries to `##` with their subheadings shifted up one level and folds the 48 bare sections under the first `[Unreleased]`. The nested count on the copy is 0 and exactly one `[Unreleased]` heading remains. The separation check `_unseparated_sections` reported 3 double-blank defects on that copy, which a final blank-line collapse removes. The real file passes the check today.

## Non-goals

- Rewriting the text of any changelog entry.
- Changing the `/now/` projection rules or the RFC-0095 D3 obligation.
- The package changelogs under `packages/*/CHANGELOG.md`.

## De-risk result

- **Date:** 2026-11-05.
- **Ran:** a comment-aware prototype transform on a copy under `.context/`, with `parse_changelog_releases` and `generate_now_projection` from `tools/build-site.py` run on the original and the copy, plus the nested-entry function and the separation check.
- **Observed:** the original parses 457 releases, 59 flagged unreleased; the copy parses 457 with 0 flagged. The nested count falls from 59 to 0 and one `[Unreleased]` heading remains of four. Ignoring blank lines and heading level, the copy has exactly the original's lines except the three removed `[Unreleased]` headings (no line changed or added). The `/now/` projection has 234 groups before and after, with 0 headings different. After collapsing blank runs above headings, the separation check reports 0 defects (3 before). A first prototype split the template comment at the file's end and dropped 124 releases from the projection, so the real transform must skip HTML comments.
- **Verdict:** supported for the stated assumption: entry text is unchanged and `/now/` is not reordered. One premise is weaker than the intent said: none of the 59 entries carries `Highlights`, so promoting them adds nothing to `/now/`. The gain is the ratchet reaching 0 and a structurally correct changelog. Consider rewording the Outcome from "publishes to `/now/`" to "is a free-standing version section".

## Readiness

- **Route:** direct-light, one session, in `docs/product/changelog.md` and the ratchet constant.
- **First slice:** run the scripted promotion, collapse blank lines, and lower `_MAROONED_RELEASE_BASELINE` to 0.
- **Agent-only proof:** `tests/roster/test_workspace_status_projection.py` and `tools/test_build_site_routing.py::test_every_changelog_section_is_separated` pass; the nested count is 0; the `/now/` projection is identical before and after (see De-risk result).
- **Risk:** promoted entries reorder the `/now/` projection. Compare the projection before and after, and keep each entry's text unchanged.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
