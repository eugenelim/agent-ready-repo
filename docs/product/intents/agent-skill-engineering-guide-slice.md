# Agent skill engineering has a dedicated guide route

- **Slug:** `agent-skill-engineering-guide-slice`
- **Status:** Fulfilled
- **Fulfilled:** 2026-11-12 eugenelim: added the dedicated guide and both incoming routes and removed the exemption; all 22 packs pass index coverage and all four guide-index tests pass.
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **De-risked:** 2026-11-05
- **Governed by:** [spec/agent-skill-engineering-foundation AC21](../../specs/agent-skill-engineering-foundation/spec.md)

## Outcome

An adopter of the agent-skill-engineering pack finds a dedicated guide from the guides index and from the pack's site page, and the guide gate no longer exempts the pack.

## Opportunity

Adopters need a dedicated guide route from both the guides index and the pack site page. The guide-index gate must require the same direct home link for this pack as for every other active public pack.

## What this absorbs

### agent-skill-engineering-guide-and-docsurl

- The owner decision is dated 2026-08-27.
- Add `guides/agent-skill-engineering/`.
- Link it from `guides/README.md`.
- Drop the `GUIDE_OPTIONAL_PACKS` exemption.
- Repoint the site `docsUrl` from the guides index to the dedicated guide.
- The M1 exemption deferred a dedicated guide after the portable-pack slice; this documentation slice removes that exemption.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

## Readiness

Route: direct-light, documentation and removal of the guide-index exemption. Add `guides/agent-skill-engineering/README.md`, its direct link in `guides/README.md`, and the dedicated site `docsUrl`; remove `GUIDE_OPTIONAL_PACKS` and its obsolete explanation from `tools/check-guide-index.py`. Verify guide schema, index, titles, repository-only references, and the existing guide-index tests. Route proof must show the source guide exists and both incoming links resolve; a schema that accepts any string does not prove a route exists.

## Non-goals

- Other packs' guides, and any change to the guide-index gate beyond removing this pack's exemption.
- New agent-skill-engineering skills or behavior.
- Pack release metadata and generated site output, which belong to integration.

## Riskiest assumption

A dedicated guide home and matching incoming links can remove the exemption without changing the guide-index API or other packs' routes. The existing index tests and guide checks verify this; rendered route verification requires the site build.

## De-risk result

2026-11-12. Source inspection confirms 22 active public packs and the single agent-skill-engineering exemption. Its manifest permits repository and user scope. The authoring skill starts in read-only framing, requires an explicit transition and authorization for creation/update, and the reviewer requires an observed failure or measured baseline before authorized optimization. The guide follows those boundaries. The site schema types `docsUrl` as a string, so the route is checked through its actual destination and incoming links, not a purported standalone web content schema test. Site rendering remains a separate integration check when it cannot run offline.
