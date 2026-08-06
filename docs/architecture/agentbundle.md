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
the contract in [`contracts/adapter.toml`](../../contracts/adapter.toml),
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

The verbs below are all stdlib-only. The catalogue *source* is never written —
reads resolve it, and the verbs that touch a working tree write only into the
install target, the adopter's config, or a catalogue you own. Run
`agentbundle --help` for the authoritative surface; this table is the map.

| Verb | What it does |
| --- | --- |
| `list-packs` | Enumerate packs in a catalogue URI (local path or `git+https`). |
| `list-profiles` | Enumerate the catalogue's curated single-scope install profiles. `install --profile <name>` installs one. |
| `list-targets` | Print the shipped adapter targets, derived from the runtime registry: `claude_code`, `codex`, `copilot`, `cursor`, `gemini`, `kiro_ide`, `kiro_cli`, and `kiro` (deprecated alias for `kiro_ide`). |
| `list-installed` | Read state files (both scopes) and report each installed `(pack, adapter)` with its version and an up-to-date / upgrade-available / unknown status. Read-only. |
| `show` | Show a pack's skills and agents, derived live from its `.apm/` tree; falls back to install state when the catalogue is unresolvable. |
| `docs` | Read pack documentation from the catalogue source — `index.md` by default, `--list` to enumerate. |
| `scaffold` | Drop a pack's `seeds/` into `--output`, honouring Tier-1/2/3 file-safety (brownfield governance). |
| `install` | Project a pack's primitives into the target. Drops `.adapt-install-marker.toml`, chains to `adapt`. |
| `validate` | Schema + semantic conformance against the bundled schemas. `--strict` runs fixture checks. |
| `render` | Render a pack to `--output` via the F-build pipeline — byte-identical to `make build`. |
| `adapt` | Deterministic non-LLM walk: substitute `<adapt:NAME>` markers, report `.upstream.*` companions. |
| `diff` | Compare the on-disk projection against a fresh render; non-zero on drift. |
| `upgrade` | Per-pack or per-primitive; honours the file-safety contract. |
| `uninstall` | Per-pack removal; removes Tier-1 files, preserves Tier-2 and Tier-3. |
| `init-state` | One-shot hashing of already-installed paths into `.agentbundle-state.toml` (closes the safety gap for APM/plugin routes). |
| `config` | Get or set adapter-scoped user settings. |
| `reconcile` | `--scope user` only; read-only orphan reporter over Claude Code `settings.json` and Kiro agent JSONs named in user-scope state (RFC-0005). No `--apply`. |
| `package-catalogue` | Package a catalogue repository into an Artifactory artifact layout (maintainer/CI only). |
| `catalogue` | Portable catalogue engine: `lint`, `verify`, `build`, `self-host`, `package`, `sync-defaults`, `init`. |
| `lint` | Lint commands — `packs` today. |
| `pack` | Pack-level commands — `evals run` today. |
| `pack-config` | Per-pack configuration: `get`, `set`, `unset`, `show`. |
| `oplog` | Pack operation log: `show`, `clear`. |

There is no `creds` verb — it went out with the rest of the credential surface
in 0.2.0 (see [Package shape](#package-shape) above).

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
    seeds/                            <repo>/.claude/ + CLAUDE.md    ← Claude self-host (claude-code)
                                      <repo>/.codex/ + .agents/      ← Codex self-host (codex)
                                      <repo>/.kiro/                  ← Kiro self-host (kiro-ide / kiro-cli)
```

> Self-host output is determined by the effective adapter set. When `catalogue.toml` sets
> `preferred-adapter` to an adapter not in the default `SELF_HOST_ADAPTERS` list (e.g. `kiro-ide`),
> only that adapter's folder is projected and `CLAUDE.md` / `.claude-plugin/marketplace.json` are
> omitted. When `preferred-adapter` is absent or names an adapter already in `SELF_HOST_ADAPTERS`,
> the default set (claude-code + codex) is used.

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
   (`claude_code`, `codex`, `copilot`, `cursor`, `gemini`, `kiro_ide`,
   `kiro_cli`, and `kiro` — the deprecated alias for `kiro_ide`) which delegate to
   [`build/projections/`](../../packages/agentbundle/agentbundle/build/projections/).
4. **Aggregation.** `marketplace.json` lists every per-pack plugin entry.
5. **Self-host overlay.** `make build-self` runs `self-host.toml` against
   this repo's root. The effective adapter set — which folders are written —
   is determined by `preferred-adapter` in `catalogue.toml`; see the diagram
   note above for the conditionality rules.
   `make build-check` runs the same dry-run as a CI gate that fails on
   any byte-divergence between source and projection — the single biggest
   source of CI noise, so the error message names the seed path you
   should have edited. On Windows (no `make`), run the whole gate chain in one
   command with the make-free repo-native script:
   `python tools/build_gate_chain.py build-self` (lint-packs → self; add
   `--dry-run` for the diff) and `python tools/build_gate_chain.py build-check`
   (lint-packs → build → check → pre-pr-catalogue → the spec-status and
   brief-coverage gates). `build-self` *writes* the projection into the tree;
   `build-check` is the read-only verify gate. The script calls the same
   `agentbundle.build` handlers the Makefile targets do — in fact `make
   build-self` / `make build-check` route *through* it, so the step lists live
   once and can't drift. It lives in `tools/` rather than the `agentbundle`
   package because `build-check` spawns repo-only scripts (`pre-pr-catalogue.py`,
   the projected skill linters) that never ship to adopters; the reusable engine
   (`lint-packs` / `build` / `check` / `self`) stays in the package. The
   fixture-overwrite guard is enforced in the `cmd_self` handler, so the entry is
   equally safe. The Windows-incompatible SAST leg (Semgrep) is not chained into
   `build-check`; it stays Makefile-appended, so a full SAST/SCA pass remains a
   `make build-check` (Linux/macOS) step.

### The adapter contract

The contract is published, semver'd, and lives at
[`contracts/adapter.toml`](../../contracts/adapter.toml). Currently
**v0.17** (RFC-0052 / shared-prefix registry). No pack targets the
latest contract: each pins the *minimum* version whose behaviour it
needs, and the pinned values today spread across the v0.7–v0.13 range.
Pack versions and contract versions are independent; bumping a pack only
matters when it consumes a feature added past its current target.
The contract declares:

- **Primitives**: the pack-authored `skill`, `agent`, `hook-body`,
  `hook-wiring`, and `command`, plus `kiro-ide-hook` (activated at v0.9
  for the Kiro IDE adapter, per RFC-0005) and the projection-support
  types `shared-libs`, `adapter-root-bins`, and `user-libs`. The
  authoritative list is the `[primitive.*]` tables in the contract.
- **Projection modes** drive how each primitive lands per adapter.
  The schema enum at
  [`adapter.schema.json`](../../packages/agentbundle/agentbundle/_data/adapter.schema.json)
  is the authoritative list. Alongside the portable modes
  (`direct-directory`, `direct-file`, `merge-json`,
  `merge-into-agent-json`, `user-merge-json`, `instruction-file`,
  `managed-block-inline`, `degraded-info-log`, `dropped`) it carries the
  adapter-specific `codex-agent-toml` (v0.8), `copilot-agent-md` and
  `copilot-hooks-json` (v0.10), and `gemini-command-toml` (v0.13).
  `managed-block-inline` survives only as
  the Codex one-shot migration helper in
  [`adapters/codex.py`](../../packages/agentbundle/agentbundle/build/adapters/codex.py)
  (scheduled for removal per RFC-0009), and `degraded-info-log` has no
  live caller after RFC-0005 lifted Kiro `hook-wiring` out of it.
- **`install-routes`** array per adapter — `cli`, `claude-plugins`, `apm`.
  Only `claude-code` declares it; the other adapters install via the CLI
  route alone.
- **`[adapter.<name>.scope]`** table — `repo`, `user`, and
  `allowed-prefixes.{repo,user}`. Every shipped adapter declares a
  user-scope root (`~`) today; what differs is the prefix set it may write
  beneath it — `.claude/` for `claude-code`, `.kiro/` for the Kiro
  adapters, and the shared `.agents/skills/` home for `codex` (added in
  v0.6 per RFC-0011), which `cursor`, `gemini`, and `copilot` joined at
  v0.17 alongside their own native prefixes. Copilot gained its user
  scope at v0.10 and is no longer repo-only. Every adapter also declares
  `.agentbundle/` so credentialed packs can reach the broker.
- **`[contract.shared-prefixes]`** registry (v0.17) — classifies each
  allowed-prefix as *shared* (named here, with its reader cohort) or
  *private* (absent). It is what lets one pack coexist across adapters
  that write the same path.
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
- [`guides/_shared/explanation/install-routes.md`](../../guides/_shared/explanation/install-routes.md) —
  adopter-facing companion to this page.
