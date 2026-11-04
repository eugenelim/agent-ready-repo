# Kiro hook projection on the standalone v1 schema

- **Slug:** `kiro-hook-schema-v1`
- **Status:** Withdrawn
- **Level:** feature
- **Owner:** eugenelim

## Disposition — withdrawn 2026-11-04, folded into one hook-adapter intent

**Do not shape this intent on its own.** The owner folded the three hook-adapter
repairs the 2026-08-22 audit left to a separate decision into
[`adapter-hook-context-output`](adapter-hook-context-output.md): per-runtime
context output, the Kiro standalone v1 schema, and root-stable dispatch for
Claude Code and Codex. No execution evidence existed when this was withdrawn.
The survivor's Boundary carries this concern and its Unresolved questions.

## Outcome

Migrate direct Kiro IDE and CLI hook projection to the current standalone .kiro/hooks JSON v1 schema while preserving non-hook adapter behavior.

## Source

- Mode: repo-origin
- Locator: docs/specs/codex-hook-adaptation-handoff/hook-adapter-audit.md
- Revision: sha256-bytes-v1:3e6d9b52c6316d6fb13eacbd46737a12d5acd437b310ba1eb3d1876df959d8c1
