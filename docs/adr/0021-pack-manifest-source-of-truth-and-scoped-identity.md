# ADR-0021: `pack.toml` is the metadata source of truth, projected lossily per tool; pack identity is `@catalogue/pack`

- **Status:** Accepted
- **Date:** 2026-06-13
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0031](../rfc/0031-catalogue-package-manager-posture.md) (decisions D2 + D7 — this ADR is the decision record that RFC's follow-on artifacts call for), [`docs/specs/enriched-pack-manifest/`](../specs/enriched-pack-manifest/spec.md), [ADR-0001](0001-adopt-agents-md-and-doc-hierarchy.md), `docs/contracts/pack.schema.json`, `docs/contracts/plugin-manifest.derived.schema.json`

## Context

RFC-0031 (Accepted) set a package-manager posture for the pack catalogue. Two of its decisions are load-bearing architecture a future maintainer will ask "why" about, and RFC-0031's follow-on artifacts explicitly call for recording them in an ADR:

- **D2 — where pack metadata lives.** The aggregated index `marketplace.json` is **Anthropic's Claude Code format** (consumed by `/plugin marketplace add`); our `plugin-manifest.schema.json` only *constrains* it. It is not ours to own as a metadata home, and putting metadata there is lossy upward to every non-Claude tool. `pack.toml` is ours, schema-enforced, and already extensible.
- **D7 — pack identity.** Today a pack is referenced by a bare `name` plus a `catalogue` field inside dependency entries. As multiple catalogues/orgs appear, bare names collide. Retrofitting namespaces later is the documented PyPI regret.

## Decision

**D2 — `pack.toml` is the single rich source of truth for pack metadata; each tool's marketplace/manifest format receives a lossy, one-directional projection of the subset it understands.** Different fields land in different files per tool: Claude Code and Copilot take rich `marketplace.json` *entries*; Codex's richness lives in `.codex-plugin/plugin.json` plus an `interface` block; tool-specific knobs live in namespaced `[pack.metadata.<tool>]` tables the schema ignores. (The first increment projects only the Claude/Copilot `marketplace.json` entry; the Codex/Cursor per-tool projectors are sequenced to follow-on work, since their unknown-field handling is unverified — RFC-0031 D2.) Projection is `pack.toml → tool format` only and never round-trips. (This extends the established model: `.apm/` primitives already project per-tool, and the adapter contract is already a source-of-truth-plus-projection in `docs/contracts/adapter.toml` — ADR-0001 / RFC-0001.)

**D7 — pack identity is `@catalogue/pack` (npm-style), with a bare/unscoped `pack` resolving to the public default catalogue.** This lets a private/org catalogue and the public default host packs of the same short name without renaming. In the first increment it is **declare-only** — the `[pack].catalogue` field plus canonical rendering in `list-packs`; multi-catalogue *resolution* is deferred to the index-contract / virtual-catalogue follow-on RFC. Scope ownership-proof is deferred (a curated catalogue needs convention, not cryptography); if public third-party submission is ever opened, a scope is bound to a verified GitHub org/domain at publish time — a registry policy, not a syntax change.

## Consequences

**Positive:**
- One source of truth → no metadata drift between `pack.toml` and the projected manifests.
- Works with zero upstream cooperation — verified that every projected field is natively supported by the Claude marketplace entry.
- An identity model that scales to private + public catalogues, with extensibility via `[pack.metadata.<tool>]`.

**Negative:**
- Per-tool projectors are ongoing maintenance as marketplace formats evolve.
- Committing to the `@catalogue/pack` syntax before resolution exists (mitigated: declare-only, resolution is additive later).

**Neutral / to revisit:**
- A real range/transitive dependency resolver and a persisted, queryable index become warranted once a second catalogue or real diamond conflicts exist (the index-contract follow-on RFC).

## Alternatives considered

- **Keep metadata in `marketplace.json` / `plugin.json` (Claude's format).** Rejected: not ours to own, and lossy upward to every non-Claude tool.
- **Reverse-DNS identity (`com.acme/pack`), as the MCP Registry uses.** Rejected: high authoring cost, justified only by open public submission — a non-goal here.
- **Flat names mapped per-registry in config (Cargo model — today's state).** Rejected as the identity: the same flat name means different packs in different catalogues, with disambiguation only in local config.

## References

- RFC-0031 (package-manager posture; decisions D2, D7); [npm scopes](https://docs.npmjs.com/about-scopes); [Cargo manifest](https://doc.rust-lang.org/cargo/reference/manifest.html).
