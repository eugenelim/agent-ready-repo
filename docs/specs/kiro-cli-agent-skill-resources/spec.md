# Spec: Kiro agent skill-resources injection (CLI + IDE)

Mode: light (no risk trigger fired by file count; one published-interface
edit — the adapter contract — proceeds in light mode per explicit user
direction, with the single bounded adversarial pass + gates as the net).
The kiro-ide extension was added in the same session at the user's request.

- **Status:** Shipped

> Slug retained as `kiro-cli-agent-skill-resources` (the CLI was the original
> driver); scope now covers **both** Kiro targets.

## Objective

Make Kiro **custom** agents — on **both** the CLI and the IDE — reach the
bundle's skills. On each target, only the *default* agent auto-discovers
`.kiro/skills/**/SKILL.md` and `~/.kiro/skills/**/SKILL.md`; a **custom** agent
does **not** inherit skill discovery and must declare skills in its `resources`
field via the `skill://` URI scheme (Kiro CLI + IDE docs; kiro #6887/#6888/#4993).
Our adapters projected agents (`.kiro/agents/<name>.json` for CLI, `.kiro/agents/
<name>.md` for IDE) **without** a `resources` field, so any pack agent run via
`--agent` / as an IDE subagent had zero skill awareness.

The fix injects a fixed skill-resources glob into every projected agent via a
new typed `inject-resources` field on the **agent projection entry** of each
adapter contract block (`kiro-cli` and `kiro-ide`), consumed by
`_project_agent_as_json` (CLI, JSON) and `_project_agent_as_md` (IDE, YAML
frontmatter) in `build/adapters/`. The IDE path emits the glob as a quoted,
real-YAML-valid `resources:` flow sequence (the serializer now quotes
flow-sequence items carrying YAML-special chars). An agent that declares its own
`resources` keeps it (author override wins). The deprecated `kiro` alias
resolves to kiro-ide, so it inherits the IDE behavior automatically.

(The `frontmatter-mapping` `default` grammar was the first approach tried but
rejected — the hand-rolled schema validator types `default` as a string and
has no union support, so it cannot hold the two-element glob list; see Declined.)

## Acceptance Criteria

- [x] **AC1** — A kiro-cli-projected agent JSON contains a `resources` array
  with exactly `["skill://.kiro/skills/**/SKILL.md", "skill://~/.kiro/skills/**/SKILL.md"]`
  when the agent source declares no `resources` frontmatter.
- [x] **AC2** — An agent whose source frontmatter *does* declare `resources`
  keeps its declared value (author override wins; the default does not clobber).
- [x] **AC3** — A kiro-ide-projected `.md` agent carries the same two-glob
  `resources` (when the source declares none); the deprecated `kiro` alias
  inherits it (alias output stays byte-identical to kiro-ide).
- [x] **AC3b** — The IDE `.md` `resources` is emitted as **real-YAML-valid**
  quoted frontmatter — it parses (PyYAML) back to the exact two-element list,
  guarding the IDE's fail-silent parser against the `skill://` URIs / `**` globs.
- [x] **AC4** — `[contract] version` is bumped 0.14 → 0.15 in both
  `docs/contracts/adapter.toml` and `_data/adapter.toml` (byte-identical drift
  gate holds), and every pinned-version test is updated.
- [x] **AC5** — RFC-0022 records the omission + correction as erratum E4
  (Approver-signed errata table), covering both CLI and IDE.
- [x] **AC6** — `docs/product/changelog.md` `[Unreleased]` carries the
  user-visible behavior entry (both targets).

## Boundaries

- **Never do**: touch agent source frontmatter in any pack; leak `skill://`
  syntax into canonical `.apm/agents/*.md`. (Adapter code is limited to the
  `inject-resources` consuming branch in each agent projector plus the
  flow-sequence quoting fix in the IDE serializer; no new module, layer, or
  adapter-name branching.)
- **Ask first**: extending to other adapters' subagents (Claude Code subagents
  can't invoke skills at all, so there's nothing to wire there).

## Tasks

1. (TDD) Add regression tests: AC1 + AC2 in `test_adapter_kiro_cli.py`;
   AC3/AC3b + author-override in `test_adapter_kiro_ide.py`. Red first.
2. Add the typed `inject-resources` array field to **both** the kiro-cli and
   kiro-ide **agent** projection entries in both `adapter.toml` copies; add the
   `inject-resources` array property to the projection-entry schema in both
   `adapter.schema.json` copies; bump `[contract] version` 0.14 → 0.15 + header
   note. Keep all four mirrors byte-identical.
3. Add the consuming branch to `_project_agent_as_json` (kiro.py, CLI) and
   `_project_agent_as_md` (kiro_ide.py, IDE); quote flow-sequence items with
   YAML-special chars in `_serialize_frontmatter_md`. Author override wins on both.
4. Update the five pinned-version tests 0.14 → 0.15.
5. RFC-0022 erratum E4 (both targets).
6. Changelog `[Unreleased]` entry (both targets).

## Declined

- *Tempted to reuse the `frontmatter-mapping` `default` grammar* (the first
  attempt) — rejected; the schema types `default` as a string and the
  hand-rolled validator has no union support, so it cannot carry the glob list,
  and resources-injection is an adapter output concern, not a per-field
  frontmatter transform. Chose a typed `inject-resources` projection-entry field.
- *Tempted to widen the schema `default` type to an array* — declining; it
  would regress the (currently unused) scalar-default capability and the
  validator can't express string-or-array.
- *Tempted to add the glob to each pack's agent frontmatter* — declining;
  pollutes the canonical source and every other adapter.
