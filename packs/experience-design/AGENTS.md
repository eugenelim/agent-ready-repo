# AGENTS.md — experience-design pack

## Migration from `experience` (v0.6.x → v1.0.0)

The pack was renamed from `experience` to `experience-design` in v1.0.0
(RFC-0064 M3). `experience-design` is the canonical agency term (Experience
Design, abbreviated XD) — zero-ambiguity alignment with practitioner taxonomy.

### Name changes

| Before (≤ 0.6.x) | After (≥ 1.0.0) |
|---|---|
| Pack: `experience` | Pack: `experience-design` |

### What does not change

All 18 skill slugs are unchanged (all are function-named):
`journey-mapping`, `user-flow`, `service-blueprint`, `process-mapping`,
`creative-direction`, `design-system`, `information-architecture`,
`interaction-design`, `design-review`, `content-design`, `tone-of-voice`,
`design-principles`, `conversion-design`, `documentation-design`,
`analytical-design`, `marketplace-design`, `informational-design`,
`workspace-design`.

The `experience-reviewer` agent name is unchanged (functional, not pack-derived).

The `[experience]` table key in `agentbundle-layout.toml` is an activity-type
identifier, not a pack name — it stays.

### Adopter install-state impact

Your install state (`~/.agentbundle/state.toml`) tracks the old pack name
`experience`. After upgrading to the catalogue with v1.0.0:

1. Uninstall the old pack: `agentbundle uninstall experience --adapter <adapter>`
2. Reinstall: `agentbundle install experience-design --adapter <adapter>`

No alias is available — the installer does not support pack-level aliases
(the alias mechanism is adapter-scoped only). The migration is
documentation-only.
