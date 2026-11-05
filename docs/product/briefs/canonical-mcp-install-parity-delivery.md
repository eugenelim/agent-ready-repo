# Brief: MCP becomes a canonical primitive with install and route parity in one wave

- **Slug:** `canonical-mcp-install-parity-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Ready
- **Ready confirmed:** 2026-11-05 by eugenelim, lifecycle owner. Bound to the file as committed in `a96a878c4`, which an independent delivery-brief review returned `Clean` with no open Ready gap. Slice membership and status are the Spec map's; this line does not restate them.
- **Source / provenance:** [`FEAT-0021-canonical-mcp-install-parity.md`](../intents/FEAT-0021-canonical-mcp-install-parity.md), under [RFC-0092](../../rfc/0092-first-class-distribution-routes.md) and the [distribution-routes programme](distribution-routes-programme.md), Phase 1B
- **Parent intent:** intent:canonical-mcp-install-parity

## Outcome

A pack can declare an MCP server once. `agentbundle install` projects it through every runtime adapter that can hold one, and every distribution route whose capability map claims MCP carries it. A server the build cannot admit safely is refused, not degraded.

## Success metrics

- Every adapter and route that claims MCP has a projection, proved by one parity test (built in M1, extended in M2 and M3) that fails when any claimant lacks one. Before M2 and M3 it runs over synthetic claimant fixtures, so it cannot pass on empty state.
- A stdio server that bundles a command or names a launcher is refused. A secret-bearing `Authorization` header is refused. `streamable-http` and `sse` servers are admitted on endpoint controls.
- Uninstall and upgrade remove exactly the MCP entries the install recorded and leave foreign entries alone.

## Scope / Non-goals

In scope: the MCP source schema and normalized model, the adapter-contract declaration of which adapters can hold MCP, direct-install projection, projection on the three existing routes, diagnostics, and one guide.

Out of scope: servers acquired from package registries ([FEAT-0025](../intents/FEAT-0025-registry-acquired-mcp-servers.md)), route-only MCP semantics, and any new route.

## Constraints / Appetite

Three slices, three sessions. Baseline checked 2026-11-05: no route in `contracts/distribution-routes.toml` has an `mcp` capability row (each lists nine component rows, none for MCP); `PRIMITIVE_DIRS` in `packages/agentbundle/agentbundle/build/main.py` lists five primitives and no MCP, `contracts/adapter.toml` has no MCP field, and the portable `mcp.schema.json` is already vendored under `contracts/vendor/agent-plugins/1.0.0/`. Protected `packages/agentbundle/**` needs an `Engine-Change-RFC:` trailer naming RFC-0092.

## Proposed slices

| # | Slice | Primary owning surface | Verification | Gating |
| --- | --- | --- | --- | --- |
| M1 | MCP source schema, normalized model, admission rules, the adapter-contract field that declares MCP-capable adapters, an `mcp` capability row on all three routes (M1 writes `dropped` on all three; M3 changes two to `native`), and the parity test, whose only home is M1, over synthetic claimants. Until M2 lands, the build and install refuse any pack that declares MCP, so a declaration is never silently dropped. | `contracts/`, pack model, `build/validate.py` | Offline fixtures: valid, stdio-refused, header-secret-refused, remote-admitted; a pack declaring MCP is refused; the parity test fails on a synthetic claimant with no projection | None |
| M2 | Direct-install projection and ownership tracking for each declared adapter, with uninstall and upgrade; lifts the M1 refusal for direct install | `agentbundle install`, state | Install, upgrade, uninstall round trip per adapter on temp roots; foreign entry survives; M1's parity test is extended to cover every declared adapter | After M1 |
| M3 | Set the `mcp` row to `native` on `agent-plugin` and `claude-plugins`, add their projections, lift the M1 refusal for those two routes, and write the guide. `apm` stays `dropped`: a pack declaring MCP is refused for that route until APM documents an MCP path and a later change records it. | route projectors, guides | Golden fixtures; M1's parity test is extended to cover every route with a non-`dropped` row | After M1; parallel with M2 |

## Decisions

Owner, 2026-11-05: `agent-plugin` and `claude-plugins` claim MCP as native. `apm` records MCP as `dropped` and refuses a declaring pack until a documented path is recorded. Each adapter's MCP capability is recorded from client documentation as `documentation-verified`.

## Assumptions / Risks

- **Riskiest assumption:** same-wave parity is checkable mechanically. The parity test over the adapter contract and capability map is the proof; it lives in M1 and asserts that every adapter declaring MCP and every route with a non-`dropped` MCP row has a projection.
- The capable-adapter set comes from the contract, never from a hand list in code.

## Ready gaps (Draft only)

None.

## Rabbit holes

- Do not reject remote servers by reusing the stdio command rules.
- Do not rely on schema validity to protect credentials.

## Manual residue (named, non-blocking)

- A live client check that each adapter loads a projected server is manual. It belongs to the runtime-verification record in [FEAT-0024](../intents/FEAT-0024-claude-manifest-migration-support-claims.md).

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

Derived from FEAT-0021 and the programme brief's Phase 1B row.
