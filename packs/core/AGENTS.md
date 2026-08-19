# AGENTS.md — core pack

Applies to `packs/core/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

Working inside the `core` pack.

Changes to this pack's `seeds/**` or `.apm/**` bump its version; see [Version bump rule](../AGENTS.md#version-bump-rule).

## Skill dependencies

Runtime dependencies that skills in this pack detect and use at invocation time.
Declared per the three-tier policy: detect → fail-clean (Tier 1).

| Skill | Dependency | Required for | Pin | Rationale |
|-------|-----------|-------------|-----|-----------|
| `workspace-status` | `tomlkit` | `repair-apply` only | `==0.15.1` | Comment-preserving TOML write — stdlib `tomllib` round-trips strip inline comments. Declared in `SKILL.md ## Prerequisites`. Detected at runtime; `repair-apply` exits 2 with `reason: "tomlkit_unavailable"` if absent. Install only with user consent. |
