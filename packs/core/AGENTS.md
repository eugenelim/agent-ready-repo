# AGENTS.md — core pack

Working inside the `core` pack. **Max 150 lines** (CI enforces it).

## Skill dependencies

Runtime dependencies that skills in this pack detect and use at invocation time.
Declared per the three-tier policy: detect → fail-clean (Tier 1).

| Skill | Dependency | Required for | Pin | Rationale |
|-------|-----------|-------------|-----|-----------|
| `workspace-status` | `tomlkit` | `repair-apply` only | `==0.15.1` | Comment-preserving TOML write — stdlib `tomllib` round-trips strip inline comments. Declared in `SKILL.md ## Prerequisites`. Detected at runtime; `repair-apply` exits 2 with `reason: "tomlkit_unavailable"` if absent. Install only with user consent. |
