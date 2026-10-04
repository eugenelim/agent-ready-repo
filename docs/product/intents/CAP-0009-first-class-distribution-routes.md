# First-class distribution routes

- **Slug:** `first-class-distribution-routes`
- **Status:** Draft
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** none
- **Decomposed:** 2026-10-02 children
- **Governed by:** [RFC-0092](../../rfc/0092-first-class-distribution-routes.md)

## Outcome

- **Steerable input:** The share of route and canonical-primitive changes made through the declared route contract, capability map, and independently reviewable route profiles rather than route-name branches or vendor-specific exceptions.
- **Lagging outcome:** A maintainer can add or evolve a distribution route while every route states truthfully what it carries, direct installation keeps parity for canonical primitives, and unsupported or unsafe semantics fail closed.
- **Guardrail:** Existing package bytes and support claims remain evidence-backed; route-specific behavior stays behind declared handlers, and no route gains authority merely by declaring its own compatibility.

## Opportunity

- **Functional job:** Evolve one canonical pack model across several external package ecosystems without editing every consumer or weakening direct-install parity.
- **Emotional job:** Add a route or primitive without wondering which hidden list, branch, or support claim was missed.
- **Social job:** Show adopters one machine-readable account of what each route supports and the evidence behind that claim.
- **Struggling moment:** RFC-0092 and its delivery programme produced a sequence of independently shippable features, but those features have no capability parent and therefore read as unrelated backlog items.

## Boundary

This capability owns the route contract's usable evolution: portable projection,
contract-derived dispatch, opening the route set, same-wave primitive parity,
native route profiles, and evidence-backed migration and support claims.

It does not own runtime-adapter installation as a substitute for routes, a
universal agent/command/rules format, or route-decision static-analysis depth.
[`route-decision-analysis-depth`](route-decision-analysis-depth.md) remains a
sibling capability because its boundary explicitly excludes changes to the
route contract and consuming surfaces.

Registry-acquired MCP servers stay behind RFC-0092 D7's separate decision gate.
The feature is a child because it extends the capability's canonical MCP
surface, but it cannot enter delivery until its acquisition and execution trust
model is approved.

## Assumptions

- **Riskiest assumption:** the accepted RFC and the shipped contract, portable projection, and registry slices are sufficient evidence that the route abstraction is a durable capability rather than a temporary migration programme.
- The remaining features can ship independently in the dependency order recorded below.
- **Knowledge surface:** In-repository RFC-0092, ADR-0090, ADR-0091, the distribution-routes programme brief, shipped specs, intents, and Git history.

## Decomposition

The order preserves the programme's hard dependencies. The package-registry MCP
decision follows the core route programme because it needs its own RFC rather
than silently widening the delivered MCP boundary.

1. **Portable baseline** — [FEAT-0018: Portable Agent Plugin projection](FEAT-0018-portable-agent-plugin-projection.md)
2. **Contract-derived dispatch** — [FEAT-0019: Distribution route registry](FEAT-0019-distribution-route-registry.md)
3. **Open route set** — [FEAT-0020: Distribution route set opening](FEAT-0020-distribution-route-set-opening.md)
4. **Canonical primitive parity** — [FEAT-0021: Canonical MCP install parity](FEAT-0021-canonical-mcp-install-parity.md)
5. **Native Codex route** — [FEAT-0022: Codex plugin route](FEAT-0022-codex-plugin-route.md)
6. **Kiro profile** — [FEAT-0023: Kiro Power route profile](FEAT-0023-kiro-power-route-profile.md)
7. **Migration and claims** — [FEAT-0024: Claude manifest migration and support claims](FEAT-0024-claude-manifest-migration-support-claims.md)
8. **Deferred acquisition trust** — [FEAT-0025: Registry-acquired MCP servers](FEAT-0025-registry-acquired-mcp-servers.md)
