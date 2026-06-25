# `agentbundle` — package and bundler

The reference CLI and build pipeline at
[`packages/agentbundle/`](../../packages/agentbundle/). Stdlib-only,
zipapp-distributable. One surface in one install: a CLI on PATH
(`agentbundle <verb>`) that drives pack install, validation, adapt,
and build. As of 0.2.0 the package no longer exposes a credential-
resolution module — credentialed primitives resolve credentials through
the pip-installable `credbroker` library (RFC-0023)
(see [`credentials.md`](credentials.md)). This page describes the
package as code; the spec lives in
[`docs/specs/agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md),
the contract in [`docs/contracts/adapter.toml`](../contracts/adapter.toml),
and the *why* in [RFC-0001](../rfc/0001-bundle-distribution-by-adapter-spec.md)
+ [RFC-0003](../rfc/0003-spec-and-cli.md).

## Package shape

```
packages/agentbundle/agentbundle/
├── cli.py                # argparse dispatcher, verb flag rewriting
├── catalogue.py          # pack discovery + pack.toml loading
├── config.py             # config resolution
├── render.py             # in-process renderer (shared with build pipeline)
├── safety.py             # Tier-1/2/3 enforcement on writes
├── scope.py              # scope resolution (repo vs user)
├── version.py            # CLI_VERSION, SPEC_VERSION
├── commands/             # one module per CLI verb
├── build/                # the bundler — recipe loader, adapters, projections
├── _data/                # bundled schemas + install-marker copy
└── templates/            # canonical install-marker.py (sync source)

(Credential resolution moved out of the wheel: first to the
build-projected `credentials_shim` per RFC-0013, then to the
pip-installable `credbroker` library per RFC-0023; see
[`credentials.md`](credentials.md). The `credentials.py`, `creds/`, and
`commands/creds.py` surfaces shipped in 0.1.x were removed in 0.2.0.)
```

## The CLI surface

Thirteen verbs, all stdlib-only. The catalogue layer is read-only — `install`,
`upgrade`, and `uninstall` are the only verbs that touch the working tree.

| Verb | What it does |
| --- | --- |
| `list-packs` | Enumerate packs in a catalogue source. |
| `list-targets` | Print the names of the four shipped adapter targets (`claude_code`, `codex`, `copilot`, `kiro`), derived from the runtime registry. |
| `scaffold` | Drop a pack's `seeds/` into a target path (brownfield governance). |
| `install` | Project a pack's primitives into the target. Drops `.adapt-install-marker.toml`, chains to `adapt`. |
| `validate` | Schema + semantic conformance. `--strict` runs fixture checks. |
| `render` | Re-render without writing — same engine as the build pipeline. |
| `adapt` | Deterministic non-LLM walk: substitute `<adapt:NAME>` markers, drop `.adapt-pending.md`. |
| `diff` | Compare on-disk projection against a freshly-rendered one. |
| `upgrade` | Per-pack or per-primitive; honours the file-safety contract. |
| `uninstall` | Per-pack removal; reads `.agentbundle-state.toml`. |
| `init-state` | One-shot hashing of already-installed paths (closes the safety gap for APM/plugin routes). |
| `reconcile` | `--scope user` only; read-only orphan reporter (RFC-0005). |
| `creds` | `setup`/`check`/`where`/`rm` — no `get`. See [`credentials.md`](credentials.md). |

`cli.py` rewrites unknown verb flags into a contract-shaped error message
("unknown flag `--foo` for `install`") so every wrapper around the CLI sees
the same shape.

## The bundler — `agentbundle.build`

The bundler is what turns `packs/<pack>/` source into `dist/<route>/<pack>/`
output and into the self-host overlay on this repo. The pipeline:

```
packs/                                dist/
  <pack>/                               apm/<pack>/                  ← per-pack APM
    pack.toml                           claude-plugins/<pack>/       ← per-pack plugin
    .claude-plugin/plugin.json          claude-plugins/marketplace.json
    .apm/{skills,agents,hooks,commands}
    seeds/                            <repo>/.claude/                ← Claude self-host
                                      <repo>/.codex/ + .agents/      ← Codex self-host
```

1. **Recipe load.** [`build/recipes/`](../../packages/agentbundle/agentbundle/build/recipes/)
   carries the canonical seven recipes — `per-pack-claude-plugin.toml`,
   `per-pack-apm-package.toml`, `marketplace.toml`, `per-pack-overlay.toml`,
   `composite-agents-md.toml`, `composite-marketplace.toml`, `self-host.toml`.
   Each has a `type` ∈ {`per-pack`, `aggregate`, `overlay`, `composite`}.
2. **Pack discovery.** `catalogue.py` globs `--packs-dir`, validates each
   `pack.toml` against [`pack.schema.json`](../../packages/agentbundle/agentbundle/_data/pack.schema.json),
   and rejects pack-internal name collisions before any adapter runs.
3. **Per-pack render.** For each pack, the dispatcher in
   [`build/main.py`](../../packages/agentbundle/agentbundle/build/main.py)
   asks the contract which adapters to run, then calls
   [`build/adapters/`](../../packages/agentbundle/agentbundle/build/adapters/)
   (`claude_code`, `codex`, `copilot`, `kiro`) which delegate to
   [`build/projections/`](../../packages/agentbundle/agentbundle/build/projections/).
4. **Aggregation.** `marketplace.json` lists every per-pack plugin entry.
5. **Self-host overlay.** `make build-self` runs `self-host.toml` against
   this repo's root for the Claude Code and Codex repo projections.
   `make build-check` runs the same dry-run as a CI gate that fails on
   any byte-divergence between source and projection — the single biggest
   source of CI noise, so the error message names the seed path you
   should have edited. On Windows (no `make`), run the whole gate chain in one
   command with the make-free chaining subcommands:
   `python -m agentbundle.build build-self` (lint-packs → self; add `--dry-run`
   for the diff) and `python -m agentbundle.build build-check` (lint-packs →
   build → check → pre-pr-catalogue → the spec-status and brief-coverage gates).
   `build-self` *writes* the projection into the tree; `build-check` is the
   read-only verify gate. These call the same handlers the Makefile targets do — in fact `make
   build-self` / `make build-check` route *through* them, so the step lists live
   once and can't drift. The fixture-overwrite guard is enforced in the CLI
   handler, so the direct entry is equally safe. The Windows-incompatible SAST
   leg (Semgrep) is not chained into `build-check`; it stays Makefile-appended,
   so a full SAST/SCA pass remains a `make build-check` (Linux/macOS) step.

### The adapter contract

The contract is published, semver'd, and lives at
[`docs/contracts/adapter.toml`](../contracts/adapter.toml). Currently
**v0.6** (RFC-0011 / pack-allowed-adapters). The four user-scope-capable
packs (`atlassian`, `figma`, `converters`, `contracts`) target v0.6 to
opt into the new resolver; the four repo-only packs still target the
older **v0.2** contract because they don't need v0.3+ features. Pack
versions and contract versions are independent; bumping a pack only
matters when it consumes a feature added past its current target.
The contract declares:

- **Five primitives**: `skill`, `agent`, `hook-body`, `hook-wiring`, `command`.
  (RFC-0005's `kiro-ide-hook` adds a sixth in design but isn't declared
  in v0.6 yet.)
- **Projection modes** drive how each primitive lands per adapter.
  The schema enum at
  [`adapter.schema.json`](../../packages/agentbundle/agentbundle/_data/adapter.schema.json)
  declares nine: `direct-directory`, `direct-file`, `merge-json`,
  `merge-into-agent-json`, `user-merge-json`, `instruction-file`,
  `managed-block-inline`, `degraded-info-log`, `dropped`. Seven are in
  active production use today; `managed-block-inline` survives only as
  the Codex one-shot migration helper in
  [`adapters/codex.py`](../../packages/agentbundle/agentbundle/build/adapters/codex.py)
  (scheduled for removal per RFC-0009), and `degraded-info-log` has no
  live caller after RFC-0005 lifted Kiro `hook-wiring` out of it.
- **`install-routes`** array per adapter: `cli`, `claude-plugins`, `apm`
  (and the draft `codex-native`).
- **`[adapter.<name>.scope]`** table — `repo`, `user`, and
  `allowed-prefixes.user`. Three adapters declare a user-scope root
  today: `claude-code` (`~/.claude/`), `kiro` (`~/.kiro/`), and `codex`
  (`~/.agents/skills/`, added in v0.6 per RFC-0011). Copilot is
  repo-only by construction.
- **`[pack.install]`** table on packs — `default-scope` ∈ `{repo, user}`,
  `allowed-scopes`, and (v0.6+) the optional `allowed-adapters` array
  declaring which user-scope-capable adapters a pack travels with.
  Three contract-level user-scope refusal rails (`check_seeds`,
  `check_hooks`, `check_markers`) live in
  [`build/scope_rails.py`](../../packages/agentbundle/agentbundle/build/scope_rails.py).
  The per-pack-default-plus-allowance shape itself is locked by
  [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md).

### User-scope adapter resolution (RFC-0011)

At install time, when `--scope user` is requested, the CLI picks
which adapter's home tree receives the pack via a six-step lookup
in
[`commands/install.py:_resolve_user_scope_target_adapter`](../../packages/agentbundle/agentbundle/commands/install.py):

1. **Publisher-vs-installer drift refusal** — every entry in the
   pack's `allowed-adapters` must be both shipped by the bundled
   contract and user-scope-capable. A mismatch refuses with a pinned
   message that names the pack, the offending adapter, the contract
   version, and the CLI version.
2. **`--adapter <name>`** — explicit adopter override, validated
   against the pack's `allowed-adapters` (or the live contract's
   user-scope-capable set when the pack omits the field). Bound to
   `--scope user`; rejected at repo scope.
3. **State-hint short-circuit** — on upgrade, `PackState.adapter`
   from `~/.agentbundle/state.toml` wins when admissible. This is
   what stops the cross-adapter refusal at
   [`upgrade.py`](../../packages/agentbundle/agentbundle/commands/upgrade.py)
   from firing when an adopter populates a second `~/.<ide>/`
   between install and upgrade.
4. **Per-adapter probe** — walk `allowed-adapters` in declared order
   against the populated `~/.<ide>/` homes (`~/.claude/`, `~/.kiro/`,
   and either `~/.codex/` or `~/.agents/skills/` for codex — the
   OR-probe handles both CLI shapes); first match wins.
5. **Greenfield fallback** — `DEFAULT_USER_SCOPE_ADAPTER` in
   [`scope.py`](../../packages/agentbundle/agentbundle/scope.py)
   (default `"claude-code"`) if it's in the pack's set, else
   `allowed-adapters[0]`.
6. **Legacy heuristic** — `< 0.6` packs and v0.6+ packs omitting
   `allowed-adapters` fall through to the original
   `.apm/agents/`-presence inference: pack ships agents ⇒ Kiro;
   otherwise Claude Code.

The resolved adapter is recorded on the state file unconditionally
for every user-scope install (not just hook-bearing kiro installs as
in earlier contract versions), so projection and state agree on
which IDE owns the pack.

The schemas at [`_data/`](../../packages/agentbundle/agentbundle/_data/) —
`adapter.schema.json`, `pack.schema.json`, `plugin-manifest.schema.json` —
let third-party validators check conformance without importing this
package. The invariant `default-scope ∈ allowed-scopes` is enforced in
the pack schema's `if`/`then`, not just in code.

## The install→adapt chain

Three install routes share one mechanism: each route drops
`.adapt-install-marker.toml` at the scope-correct root; `core`'s
`session-start.py` hook reads it and nudges the agent into
`adapt-to-project` on the next session.

| Route | Marker writer | Trigger |
| --- | --- | --- |
| `agentbundle install` (CLI) | The CLI command writes it in-process and chains to `agentbundle adapt`. | Run by user. |
| `claude plugin install` | A `SessionStart` hook derived into each pack's `.claude-plugin/plugin.json` runs the canonical writer template. | First session after install. |
| `apm install` | `.apm/hooks/install-marker.{json,py}` projected via APM's `HookIntegrator`, same template. | First session after install. |

The writer template lives at
[`packages/agentbundle/templates/install-marker.py`](../../packages/agentbundle/templates/install-marker.py)
— **the canonical copy**. The drift gate keeps three copies in lockstep:
the template, the bundled
[`_data/install-marker.py`](../../packages/agentbundle/agentbundle/_data/install-marker.py),
and every `dist/<route>/<pack>/.../install-marker.py` projection. Edit
the template; `make build` syncs the rest. The writer takes a required
`--install-route {claude-plugins,apm}` flag and resolves the data
directory via a portability shim (`${CLAUDE_PLUGIN_DATA}` →
`${PLUGIN_ROOT}/.data` → `${CURSOR_PLUGIN_ROOT}/.data` → exit 0).

## Where to read next

- [`credentials.md`](credentials.md) — the secret-handling subsystem inside
  this package.
- [`docs/specs/agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md) —
  authoritative spec for the CLI verbs.
- [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md) —
  authoritative spec for the contract, primitives, and projection modes.
- [`docs/guides/_shared/explanation/install-routes.md`](../guides/_shared/explanation/install-routes.md) —
  adopter-facing companion to this page.
