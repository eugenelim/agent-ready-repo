# Native Codex plugin route

- **Slug:** `codex-plugin-route`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:first-class-distribution-routes
- **Depends on:** intent:canonical-mcp-install-parity, intent:distribution-route-set-opening
- **Decomposed:** 2026-11-05 brief

## Outcome

AgentBundle emits a native Codex plugin package and marketplace manifest from the same catalogue source as the Claude marketplace. Claude and Codex publication use the same user-scope pack eligibility rule and unrelated commits do not schedule either publisher.

## Opportunity

Codex has a documented native plugin ecosystem but the catalogue emits no native Codex package or marketplace, while the Claude publication workflow starts on a push to main whose changed paths match its published-pack allowlist.

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

## Readiness

- **Route:** delivery brief [`codex-plugin-route-delivery`](../briefs/codex-plugin-route-delivery.md), four slices. The first (extend the roster parity check from one hard-wired publisher to a declared list of publishers, against the one shared eligibility rule in `tools/pack_scope.py`) has no dependency and can ship first; the Codex publish workflow does not exist yet and slice C4 creates it.
- **Verified 2026-11-05:** no Codex route exists in `contracts/distribution-routes.toml`; the dependencies FEAT-0020 and FEAT-0021 are both still open, so slices C2 to C4 wait.
- **Agent-only proof:** golden fixtures, offline schema validation against a vendored schema, and workflow posture tests. The support claim stays `documentation-verified`.
- **Owner decision, 2026-11-05:** the Codex route records MCP as `dropped` and refuses a declaring pack until a documented MCP path is recorded.
- **Manual residue, non-blocking:** one real Codex install and enable check, filed in the runtime-verification record.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:329d3aec010ffd0f0b090022bac7faf35b85f337d9b3c719ab8063b7c74dbc45
