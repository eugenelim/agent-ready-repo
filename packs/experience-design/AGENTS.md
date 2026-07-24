# AGENTS.md — experience-design pack

## Migration from `experience` (v0.6.x → v1.0.0)

The pack was renamed from `experience` to `experience-design` in v1.0.0
(RFC-0064 M3). `experience-design` is the canonical agency term (Experience
Design, abbreviated XD) — zero-ambiguity alignment with practitioner taxonomy.

### Name changes

| Before (≤ 0.6.x) | After (≥ 1.0.0) |
|---|---|
| Pack: `experience` | Pack: `experience-design` |

### What does not change (v1.0.0 rename)

The skills below kept their slugs through the v1.0.0 pack rename (from `experience` to `experience-design`):
`journey-mapping`, `user-flow`, `service-blueprint`, `process-mapping`,
`creative-direction`, `information-architecture`,
`interaction-design`, `design-review`, `content-design`, `tone-of-voice`,
`design-principles`, `conversion-design`, `documentation-design`,
`analytical-design`, `marketplace-design`, `informational-design`,
`workspace-design`.

**v1.3.0 update (ADR-0038 alias-free rename):** `design-system` was renamed to
`design-token-taxonomy` and `design-system-foundations` was added as a new skill.
The name table below records both changes. See `docs/specs/xd-design-system-foundations/spec.md`.

The `experience-reviewer` agent name is unchanged (functional, not pack-derived).

The `[design]` table key replaced `[experience]` in v1.0.0 — the section name
was updated alongside the pack rename to align with practitioner taxonomy.

### Adopter install-state impact

Your install state (`~/.agentbundle/state.toml`) tracks the old pack name
`experience`. After upgrading to the catalogue with v1.0.0:

1. Uninstall the old pack: `agentbundle uninstall experience --adapter <adapter>`
2. Reinstall: `agentbundle install experience-design --adapter <adapter>`

No alias is available — the installer does not support pack-level aliases
(the alias mechanism is adapter-scoped only). The migration is
documentation-only.
