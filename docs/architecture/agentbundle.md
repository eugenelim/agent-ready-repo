# `agentbundle` — package and bundler

The reference CLI and runtime library at
[`packages/agentbundle/`](../../packages/agentbundle/). Stdlib-only,
zipapp-distributable, and the single Python module every credentialed
primitive imports. Two surfaces in one install: a CLI on PATH
(`agentbundle <verb>`) and an importable module (`from agentbundle.credentials
import load_credentials`). This page describes the package as code; the
spec lives in [`docs/specs/agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md),
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
├── credentials.py        # public shim → re-exports from creds/loader.py
├── commands/             # one module per CLI verb
├── build/                # the bundler — recipe loader, adapters, projections
├── creds/                # credential loader internals (Tier 1/2/3 backends)
├── _data/                # bundled schemas + install-marker copy
└── templates/            # canonical install-marker.py (sync source)
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
    seeds/                            <repo>/.claude/                ← self-host overlay
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
   this repo's root. `make build-check` runs the same dry-run as a CI gate
   that fails on any byte-divergence between source and projection — the
   single biggest source of CI noise, so the error message names the seed
   path you should have edited.

### The adapter contract

The contract is published, semver'd, and lives at
[`docs/contracts/adapter.toml`](../contracts/adapter.toml). Currently
**v0.5** (RFC-0010). Shipped packs on disk target the older **v0.2**
contract today via their `[pack.adapter-contract]` table — bumping
packs to track v0.3 / v0.4 / v0.5 is a pending pack-revision cycle, so
the contract version and any given pack's targeted version are not the
same number. The contract declares:

- **Five primitives**: `skill`, `agent`, `hook-body`, `hook-wiring`, `command`.
  (RFC-0005's `kiro-ide-hook` adds a sixth in design but isn't declared
  in v0.5 yet.)
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
- **`[scope]`** table — `default-scope` ∈ `{repo, user}` and
  `allowed-scopes`. Three contract-level user-scope refusal rails
  (`check_seeds`, `check_hooks`, `check_markers`) live in
  [`build/scope_rails.py`](../../packages/agentbundle/agentbundle/build/scope_rails.py).
  The per-pack-default-plus-allowance shape itself is locked by
  [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md).

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
- [`docs/guides/explanation/install-routes.md`](../guides/explanation/install-routes.md) —
  adopter-facing companion to this page.
