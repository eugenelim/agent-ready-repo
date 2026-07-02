# Pack shell — what a new pack needs to register

Scaffold these only after the area has cleared the additivity + four-principles
bar. All writes route through `agentbundle.safety.write_jailed`.

## Files
- `packs/<name>/pack.toml` — the metadata source of truth. Required: `[pack]`
  `name` + `version` + `description`; `[pack.adapter-contract] version`;
  `[pack.install] default-scope` + `allowed-scopes`; `[[pack.dependencies.required]]`
  (at least `core`, catalogue-scoped) if it composes around core; `[pack.links]`
  and `[[pack.maintainers]]`. Mirror an existing pack's `pack.toml`.
- `packs/<name>/.claude-plugin/plugin.json` — `{name, version, description}`,
  version matching `pack.toml`.
- `packs/<name>/README.md` — elevator pitch + a link to the pack's guide home.
- `packs/<name>/.apm/skills/` (and/or `.apm/agents/`) — at least one primitive,
  or the pack won't validate.

## Dependency shape
`[[pack.dependencies.required]]` names `catalogue` + `pack` + a `^X.Y` version.
A dependency on a non-`core` pack resolves compositionally (each pack's install
gate enforces its own direct deps) — but flag it as a novel shape in the RFC if
it's a first for the catalogue.

## Wiring (in the RFC's follow-on, not the scaffold)
- Repo-scope packs are added to the self-host recipe's include list to project
  locally. That recipe edit is declarative config (not engine behaviour).
- The per-pack guide home and a changelog entry are follow-on artifacts.

## Register check
`lint-packs` + the pack schema validate the shell; `lint-skill-spec` /
`lint-agent-artifacts` validate its primitives. A green run means the shell
registers.
