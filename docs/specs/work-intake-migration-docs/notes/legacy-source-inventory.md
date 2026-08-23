# Legacy source inventory for RFC-0083 migration

- **Acceptance ref:** `352595bd2bcf25bbbffb03deabfa8f5a9e4b248d`
- **Acceptance date:** 2026-08-08
- **Decision source:** `docs/rfc/0083-work-intake-and-artifact-routing.md`
  § 10, “Migrate without preserving two contracts”

This frozen inventory defines “released workflows and workspace shapes at RFC
acceptance” for AC1. T1 copies exact TOML slices and writer-produced forms from
this ref; later files or private extensions do not expand the compatibility
window.

## Workspace representations

- `workspace.toml`
- `packs/core/seeds/workspace.toml`
- `packs/core/.apm/skills/workspace-status/evals/files/workspace.toml`

## Released writer contracts

- `packs/core/.apm/skills/capture-work/SKILL.md`
- `packs/core/.apm/skills/author-brief/SKILL.md`
- `packs/core/.apm/skills/receive-brief/SKILL.md`
- `packs/atlassian/.apm/skills/jira-brief-intake/SKILL.md`
- `packs/atlassian/.apm/skills/jira-align-brief-intake/SKILL.md`
- `packs/atlassian/.apm/skills/jira-story-triage/SKILL.md`
- `packs/github/.apm/skills/github-brief-intake/SKILL.md`
- `packs/linear/.apm/skills/linear-brief-intake/SKILL.md`

## Accepted shapes

- Bare `spec/<slug>` strings in work arrays.
- Bare shaping slugs.
- `{slug, type, needs}` shaping objects.
- Brief-path strings in `brief_queue`.
- Comment-rich `[backlog].open` entries.

Completeness means every distinct representation of those five shapes found in
the workspace representations or produced by the writer contracts at the
pinned ref has an exact migration fixture. Missing artifacts/plans and malformed
variants are negative fixtures; they do not add supported shapes.
