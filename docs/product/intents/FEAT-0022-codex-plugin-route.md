# Native Codex plugin route

- **Slug:** `codex-plugin-route`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:first-class-distribution-routes

## Outcome

AgentBundle emits a native Codex plugin package and marketplace manifest from the same catalogue source as the Claude marketplace. Claude and Codex publication use the same user-scope pack eligibility rule and unrelated commits do not schedule either publisher.

## Opportunity

Codex has a documented native plugin ecosystem but the catalogue emits no native Codex package or marketplace, while the Claude publication workflow starts on every push to main.

## Boundary

This feature owns native Codex plugin packaging, marketplace metadata, and
publication parity from the catalogue source.

It does not adapt unsupported plugin capabilities by assumption, widen
user-scope eligibility, or let unrelated commits schedule marketplace
publication.

## Assumptions

- **Riskiest assumption:** the route can stay components-only unless plugin root, persistent data, enablement, and consent prerequisites for adaptation are documented and verified.
- Publisher/build-contract changes remain eligible trigger inputs so marketplace artifacts cannot go stale.
- **Knowledge surface:** In-repository RFC-0092, distribution-routes programme brief, Codex route contract evidence, and publication constraints.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:329d3aec010ffd0f0b090022bac7faf35b85f337d9b3c719ab8063b7c74dbc45
