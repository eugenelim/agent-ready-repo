# Catalogue release integrity

- **Status:** Draft
- **Level:** feature

## Outcome

Catalogue publishers can package releases with content digests, compare them with a prior archive, and refuse same-version archive mutation unless they explicitly override it.

## Opportunity

The neutral index describes catalogue contents, but the release process still needs durable evidence and a guard against silently changing an already-versioned archive.

## Assumptions

- The archive-level mutation boundary in RFC-0076 remains the baseline scope to refine.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
