# AGENTS.md — desk-research pack

## Migration from `research` (v0.6.x → v1.0.0)

The pack was renamed from `research` to `desk-research` in v1.0.0 (RFC-0064 M3).

### Name changes

| Before (≤ 0.6.x) | After (≥ 1.0.0) |
|---|---|
| Pack: `research` | Pack: `desk-research` |
| Skill: `/research` | Skill: `/desk-research` |
| Skill: `/research-project-start` | Skill: `/desk-research-project-start` |
| Skill: `/research-project-digest` | Skill: `/desk-research-project-digest` |
| Skill: `/research-project-check` | Skill: `/desk-research-project-check` |
| Skill: `/research-project-synthesize` | Skill: `/desk-research-project-synthesize` |

### What does not change

- `workspace.toml` `type = "research"` entries — activity-type field, not pack name.
- `agentbundle-layout.toml [research]` section key — activity-type identifier.
- The six function-named skills: `build-outline`, `compare-hypotheses`,
  `decision-archaeology`, `devils-advocate`, `identify-perspectives`, `source-map`.

### Adopter install-state impact

Your install state (`~/.agentbundle/state.toml`) tracks the old pack name `research`.
After upgrading to the catalogue with v1.0.0:
1. Uninstall the old pack: `agentbundle uninstall research --adapter <adapter>`
2. Reinstall: `agentbundle install desk-research --adapter <adapter>`

No alias is available — the installer does not support pack-level aliases.
