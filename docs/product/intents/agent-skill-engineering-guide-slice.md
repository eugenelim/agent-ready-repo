# Agent skill engineering has a dedicated guide route

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/agent-skill-engineering-foundation AC21](../../specs/agent-skill-engineering-foundation/spec.md)

## Outcome

The agent-skill-engineering pack has a dedicated guide that its site record links to.

## Opportunity

`agent-skill-engineering` is the only pack in `GUIDE_OPTIONAL_PACKS`, its site record sets `docsUrl: /docs/guides/`, and the planned documentation slice has not yet supplied the dedicated guide.

## What this absorbs

### agent-skill-engineering-guide-and-docsurl

- The owner decision is dated 2026-08-27.
- Add `guides/agent-skill-engineering/`.
- Link it from `guides/README.md`.
- Drop the `GUIDE_OPTIONAL_PACKS` exemption.
- Repoint the site `docsUrl` from the guides index to the dedicated guide.
- `tools/check-guide-index.py:29` records that the M1 slice shipped the portable pack and left the guide to a later planned documentation slice.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
