# ADR-0067: Lifecycle manifest — built-in defaults and workspace-types.d/ extension

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision-makers:** eugenelim

## Decision summary

- **Decision:** The lifecycle manifest — the mapping from workspace item types (work, research, shape, etc.) to output directories and dispatch skills — is stored in two layers: (1) built-in defaults embedded in workspace-mcp for the known type taxonomy (work, research, shape/signal/design/strategy, brief); (2) third-party extension files projected to `workspace-types.d/` by pack.toml-installed packs. workspace-types.d/ files are merged additively at startup; conflicts (same type key in two files) are logged and the last-writer wins.
- **Because:** pack.toml is source-only and is not projected to adopters; it cannot carry the lifecycle manifest. A projected pack artifact is the natural alternative, but no single projected location can serve as the canonical manifest without creating a clobber conflict between multiple packs that each want to add their own types. The `workspace-types.d/` directory pattern (each pack writes its own file, no clobber) is the established solution for multi-contributor extension without clobbering.
- **Applies to:** `packages/agentbundle/agentbundle/workspace_mcp.py` (the manifest loading logic); third-party pack projections that add custom types; adopter documentation for the `workspace-types.d/` directory.
- **Tradeoff accepted:** The last-writer-wins conflict resolution for duplicate type keys is non-deterministic across pack install orderings. Adopters who install multiple packs that define the same type key may observe inconsistent behavior depending on install order. This is logged as a warning; authoritative behavior requires the packs to coordinate on type keys (or the adopter to override in a top-level `workspace-types.override.d/` file — a future extension).
- **Revisit if:** A canonical manifest location becomes available that does not create clobber conflicts (e.g., pack.toml gains a projected-manifest section that agentbundle merges at install time); or the number of conflicting type keys across packs becomes a recurring adopter pain point.

## Context

The lifecycle manifest maps each workspace item type to:
- `output_dirs`: where artifacts for this type are written (used by the artifact watcher)
- `dispatch_skill`: the skill the control plane should invoke to process this item
- `elicits_output_dir`: whether this type asks for output directory on first run (affects watcher binding)

For the known type taxonomy (the types defined in CONVENTIONS.md and workspace.toml schema), built-in defaults in workspace-mcp are authoritative. Third-party packs (accelerator packs, domain packs) may introduce new item types with their own output directories and dispatch skills; they need a way to register these types without modifying workspace-mcp's source.

The `workspace-types.d/` directory pattern is used elsewhere in the repo (e.g., adapter projections in agentbundle) for exactly this multi-contributor extension problem. Each pack projects a `workspace-types.d/<pack-name>.toml` file listing its types; workspace-mcp merges all files at startup using a simple last-writer-wins strategy.

pack.toml cannot carry the manifest because it is source-only: it is not projected to adopters. A single `workspace-types.toml` file projected by the core pack would be clobbered by any other pack that also projects the same file.

## Alternatives rejected

**Single `workspace-types.toml` projected by core.** One canonical file, all types in one place. Rejected because a second pack that also projects `workspace-types.toml` clobbers the core file, losing all core types. The clobber problem is fundamental to single-file shared registration.

**Types in pack.toml under a `[pack.workspace_types]` section.** pack.toml is source-only; it is not projected to adopters. workspace-mcp running in an adopter's environment cannot read pack.toml files that are not projected. Unless agentbundle adds a pack.toml projection for workspace types (a separate RFC-scope change), this approach is not viable.

**Dynamic type discovery via MCP tool call.** Each pack exposes a `register_types()` MCP tool; workspace-mcp queries all registered pack tools at startup. Requires packs to run MCP servers of their own, introducing a dependency cycle (workspace-mcp coordinates packs; packs cannot be workspace-mcp's orchestrators). Rejected as architecturally incoherent.
