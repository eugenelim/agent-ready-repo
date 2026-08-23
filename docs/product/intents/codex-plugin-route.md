# Native Codex plugin route

- **Status:** Draft
- **Level:** feature

## Outcome

AgentBundle emits a native Codex plugin package and marketplace manifest from the same catalogue source as the Claude marketplace. Claude and Codex publication use the same user-scope pack eligibility rule and unrelated commits do not schedule either publisher.

## Opportunity

Codex has a documented native plugin ecosystem but the catalogue emits no native Codex package or marketplace, while the Claude publication workflow starts on every push to main.

## Assumptions

- The route ships components-only unless plugin root, persistent data, enablement, and consent prerequisites for adaptation are documented and verified; publisher/build-contract changes remain eligible trigger inputs so marketplace artifacts cannot go stale.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:329d3aec010ffd0f0b090022bac7faf35b85f337d9b3c719ab8063b7c74dbc45
