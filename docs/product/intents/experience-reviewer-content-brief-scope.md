# Extend experience-reviewer to review content briefs

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0062 OQ1](../../rfc/0062-content-design-and-copy-direction-skills.md)

## Outcome

`experience-reviewer` reviews the content briefs produced by `content-design`.

## Opportunity

`experience-reviewer` does not yet review the content briefs produced by `content-design`.

## What this absorbs

### experience-reviewer-content-brief-scope

RFC-0062 OQ1 records a follow-on: extend `experience-reviewer` to include content briefs (`type: content-brief`) as a reviewable artifact type. RFC-0062's `content-design` skill produces that artifact. The recorded fix is a follow-on RFC extending RFC-0062 to add `content-brief` to the `experience-reviewer` reviewable-artifact set. The RFC-0062 `content-design-skill` spec is Shipped, so this item is actionable.

Unblocks when: the follow-on RFC extends the reviewable-artifact set.

## Assumptions

- The shipped `content-design-skill` makes this reviewer-scope follow-on actionable.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 768c0a90b87e635220c3c784d7cdae67644d7e1d
