# Portable Agent Plugin projection

- **Slug:** `portable-agent-plugin-projection`
- **Status:** Fulfilled
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:first-class-distribution-routes
- **Decomposed:** 2026-08-26 spec
- **Accepted:** 2026-09-24 by eugenelim, on an owner waiver rather than an independent shaping review. This intent reached a delivered state without ever passing `Draft` → `Accepted`, so the ratification is taken now rather than reconstructed from a review that never ran; the owner waived the intent-mode review that gate names, for this one-off migration only. Basis: `docs/specs/lifecycle-transition-contract/notes/migration-record.md`.
- **Fulfilled:** 2026-09-24 by eugenelim, on an independent fulfilment verification against the repository rather than against this artifact's own account. The projection ships as declared data with a schema: `agentbundle/_data/agent-plugin-extension-namespaces.toml` beside `agent-plugin-extension-namespaces.schema.json`. Its spec `docs/specs/portable-agent-plugin-projection/spec.md` is `Shipped`. Record written by the 2026-09-24 corpus migration.

## Outcome

A deterministic portable Agent Plugin package projects existing canonical skills and validated extension namespaces after the route contract exists.

## Opportunity

The catalogue has no portable Agent Plugin distribution output.

## Boundary

This fulfilled feature owns deterministic package projection for user-scope
packs that Agent Plugins 1.0.0 can represent.

It does not claim Agent Plugins are the preferred distribution bet, emit partial
packages for packs with unsupported primitives, or extend the Agent Plugins
standard.

## Assumptions

- **Riskiest assumption:** Agent Plugins 1.0.0 remains useful as portability groundwork even though it cannot represent sub-agent-bearing packs.
- This slice introduces no new canonical primitive; existing direct agentbundle skill installation remains the parity baseline.
- **Knowledge surface:** In-repository RFC-0092, distribution-routes programme brief, shipped projection spec, and fulfilment evidence.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:329d3aec010ffd0f0b090022bac7faf35b85f337d9b3c719ab8063b7c74dbc45
