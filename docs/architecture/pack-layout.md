# Pack layout

Every pack in this catalogue ships the same on-disk shape — the
bundler refuses anything that doesn't conform. This page maps each
directory and file to its role. The authoritative format spec lives in
[`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md);
contributor conventions on *what goes where* live in
[`docs/CONVENTIONS.md § Pack source-of-truth split`](../CONVENTIONS.md#pack-source-of-truth-split).

## The shape

A pack sits under `packs/<name>/` with this skeleton:

```
packs/<name>/
├── pack.toml                       # pack metadata, scope rules, contract version
├── .claude-plugin/
│   └── plugin.json                 # Claude Code plugin manifest (hand-authored)
├── .apm/                           # primitives — projected by the build pipeline
│   ├── skills/
│   │   └── <skill-name>/SKILL.md
│   ├── agents/
│   │   └── <agent-name>.md
│   ├── hooks/                      # hook bodies (executable code)
│   │   └── <name>.{py,sh}
│   ├── hook-wiring/                # bindings of bodies to events (TOML)
│   │   └── <event>.toml
│   └── commands/
│       └── <name>.md
└── seeds/                          # Tier-1 governance seeds (projected to repo root)
    ├── AGENTS.md
    ├── _agents-footer.md
    ├── .gitignore
    └── docs/
        ├── CHARTER.md
        ├── CONVENTIONS.md
        └── ...
```

Every pack ships `pack.toml` (schema-enforced) and a hand-authored
`.claude-plugin/plugin.json` (build-convention-required — the bundler
reads it directly). Beyond that, two orthogonal axes shape the
contents:

- **Scope**, declared in `pack.toml`'s `[pack.install]`, governs where
  the projection lands (repo's working tree vs. user-scope root). The
  three scope rails in
  [`build/scope_rails.py`](../../packages/agentbundle/agentbundle/build/scope_rails.py)
  refuse `seeds/`, `.apm/hooks/`, and `.apm/hook-wiring/` on user-scope
  packs at build time.
- **Content shape**, declared by which directories are populated. The
  `core` pack is the only one with a full `.apm/` set (skills, agents,
  hooks, hook-wiring, commands); the other repo-only packs
  (`governance-extras`, `user-guide-diataxis`, `monorepo-extras`) ship
  `.apm/skills/` plus `seeds/` and nothing else. User-scope packs
  (`converters`, `atlassian`, `figma`, `contracts`) ship `.apm/skills/`
  only. A repo-only pack omitting `seeds/` or `.apm/hooks/` is fine —
  it just didn't need them.

## What each file does

### `pack.toml`

Pack metadata, declared scope shape, and the adapter-contract version
the pack targets. Three required tables:

- **`[pack]`** — `name`, `version`, `description`. The build pipeline
  reads these and emits derived per-tool metadata into
  `dist/apm/<pack>/apm.yml` and
  `dist/claude-plugins/<pack>/.claude-plugin/plugin.json`.
- **`[pack.adapter-contract]`** — `version`, must reference a
  published contract version. The contract itself is at **v0.5**
  today; every shipped pack on disk currently targets **v0.2** (the
  bump to track v0.3 / v0.4 / v0.5 is a pending pack-revision cycle).
  When authoring a new pack, copy the value from a sibling pack rather
  than the contract.
- **`[pack.install]`** — `default-scope` ∈ `{repo, user}` and
  `allowed-scopes`. The `default-scope ∈ allowed-scopes` invariant is
  enforced in
  [`_data/pack.schema.json`](../../packages/agentbundle/agentbundle/_data/pack.schema.json)'s
  `if`/`then`. [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md)
  locked the per-pack default-plus-allowance shape.

### `.claude-plugin/plugin.json`

Hand-authored Claude Code plugin manifest — Source category, never
projected. The build pipeline reads it directly when emitting the
`dist/claude-plugins/<pack>/.claude-plugin/plugin.json` projection.

### `.apm/` — primitives

The five primitives declared in the adapter contract
([`docs/contracts/adapter.toml`](../contracts/adapter.toml)):

| Primitive | On-disk path | Notes |
| --- | --- | --- |
| `skill` | `.apm/skills/<name>/SKILL.md` (+ optional `scripts/`, `references/`, `assets/`, `evals/`) | [agentskills.io](https://agentskills.io/specification)-compliant. |
| `agent` | `.apm/agents/<name>.md` | Frontmatter declares `name`, `description`, `tools`, `model`; body is the system prompt. |
| `hook-body` | `.apm/hooks/<name>.{py,sh}` | The executable. The bundler projects to each harness's hook directory. |
| `hook-wiring` | `.apm/hook-wiring/<name>.toml` | Declarative binding of a body to an editor event. |
| `command` | `.apm/commands/<name>.md` | Slash-command primitive (Claude Code today; other harnesses degrade per the contract). |

A sixth primitive — `kiro-ide-hook`, for native Kiro IDE-event hooks —
is designed in [RFC-0005](../rfc/0005-user-scope-hook-support.md) but
isn't declared in `adapter.toml` v0.5 yet; the implementation work is
tracked separately and the source path will be `.apm/kiro-ide-hooks/<name>.kiro.hook`
once it lands.

### `seeds/`

Governance content the pack drops at the repo root on install. Every
file under `seeds/` is **Tier-1** under the
[file-safety contract](../guides/explanation/file-safety-contract.md) —
collisions land as `*.upstream.<ext>` companions, never silent
overwrites. Typical contents: `AGENTS.md`, `docs/CHARTER.md`,
`docs/CONVENTIONS.md`, quadrant READMEs.

A pack with `default-scope = "user"` cannot ship seeds at all — the
contract's user-scope seeds-rail (in
[`build/scope_rails.py:check_seeds`](../../packages/agentbundle/agentbundle/build/scope_rails.py))
refuses to build a user-scope pack that declares `seeds/`.

### `_agents-footer.md` (optional)

Managed-block content the build pipeline composes into the
per-instance AGENTS.md via the `composite-agents-md.toml` recipe.
Multiple packs' footers merge in recipe order; only present in packs
that contribute to the AGENTS.md managed block.

## How the bundler reads a pack

1. [`agentbundle/catalogue.py`](../../packages/agentbundle/agentbundle/catalogue.py)
   globs `packs/*/`, validates each `pack.toml` against
   `_data/pack.schema.json`, and rejects pack-internal name collisions
   before any adapter runs.
2. The build dispatcher reads
   [`docs/contracts/adapter.toml`](../contracts/adapter.toml) to learn
   which projection mode applies to each primitive per adapter.
3. [`build/adapters/`](../../packages/agentbundle/agentbundle/build/adapters/)
   projects `.apm/<primitive-type>/` into the per-tool output
   directory using the
   [`build/projections/`](../../packages/agentbundle/agentbundle/build/projections/)
   handlers.
4. [`build/recipes/`](../../packages/agentbundle/agentbundle/build/recipes/)
   sequences which adapter targets to run for which output route. See
   [`agentbundle.md`](agentbundle.md) for the seven canonical recipes
   and the phases they participate in.

## Where to read next

- [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md) —
  the authoritative format spec.
- [`docs/CONVENTIONS.md § Pack source-of-truth split`](../CONVENTIONS.md#pack-source-of-truth-split) —
  why `seeds/` and `.apm/` are separate roots, and the rules for
  authoring inside each.
- [`agentbundle.md`](agentbundle.md) — how the bundler reads this
  shape into `dist/<route>/<pack>/`.
- [`pack-catalogue.md`](../guides/explanation/pack-catalogue.md) —
  the adopter-facing companion to this page.
