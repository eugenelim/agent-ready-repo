# agentbundle

[![PyPI](https://img.shields.io/pypi/v/agentbundle)](https://pypi.org/project/agentbundle/)
[![Python](https://img.shields.io/pypi/pyversions/agentbundle)](https://pypi.org/project/agentbundle/)
[![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue)](https://github.com/eugenelim/agent-ready-repo#license)

**The installer for [agent-ready-repo](https://github.com/eugenelim/agent-ready-repo).** Think npm, but for the skills, subagents, and hooks your coding agent runs on. One pack, one command, every major agent — Claude Code, Codex, Cursor, Copilot, Gemini, and Kiro (both the CLI and the IDE).

## Quick start

```bash
pip install agentbundle
```

Requires Python 3.11+. Runs on macOS, Linux, and Windows.

**Install into a repo** — so everyone who clones it gets the pack. `core` is the flagship pack, the loop itself:

```bash
agentbundle install --pack core
```

No catalogue argument needed: it defaults to the agent-ready-repo catalogue. It lands in the repo's agent config — subagents and skills included — and you commit it like any other project file. This is the default scope: the pack belongs to the project and the whole team.

**Install for yourself, everywhere** — so a pack follows you across every project, with no per-repo setup:

```bash
agentbundle install --pack desk-research --scope user
```

User-scope packs land in your home directory, not the repo — they're yours, not the team's, and they're there in every project you open.

The install auto-detects your agent (`--adapter` overrides). Multi-IDE? Install the same pack for each agent at the same scope — they coexist, and the agents that read `.agents/skills/` (codex, cursor, gemini, copilot) share one skill copy instead of fighting over it. To install from a **different** catalogue, pass it as a trailing argument — a git URL or a local path (`agentbundle install --pack core <catalogue>`); a `config set source <catalogue>` makes that the default, and an editable clone (`pip install -e`) defaults to itself.

## More commands

```bash
# See what the catalogue offers (bare uses the default; or name one explicitly)
agentbundle list-packs
agentbundle list-profiles

# See what a single pack contains — skills and agents, derived live from its tree
agentbundle show core
agentbundle show core --format json          # stable object for scripts/agents

# See what YOU have installed — pack, adapter, scope, version, and whether
# an upgrade is available (both scopes by default)
agentbundle list-installed
agentbundle list-installed --no-check       # skip the catalogue check (offline, fast)
agentbundle list-installed --check-drift    # also count locally edited files
agentbundle list-installed --format json    # machine-readable JSON (schema_version 1)
agentbundle list-installed --updates-only   # show only rows needing attention

# Install a whole curated profile — a single-scope set of packs — in one command
agentbundle install --profile inception

# Preview any install without writing a file
agentbundle install --pack core --dry-run

# Upgrade to the version the catalogue ships — shows installed → target, asks first
agentbundle upgrade --pack core
agentbundle upgrade --pack core --yes  # skip the prompt (CI)

# Uninstall — previews remove (Tier-1) vs keep (your edits), asks first
agentbundle uninstall --pack core --dry-run
agentbundle uninstall --pack core --yes
```

**`list-installed`** reads your state files (not the catalogue) and reports every installed `(pack, adapter)` at each scope with its version and a four-value status — `up-to-date`, `upgrade-available`, `ahead` (installed version is newer than catalogue), or `unknown`; it degrades to `unknown` (never an error) when the catalogue can't be resolved, and `--no-check` skips the check entirely. `--format json` emits a stable JSON contract (`schema_version: 1`) to stdout — useful for CI automation of upgrade decisions. `--updates-only` hides `up-to-date` rows.

**`show <pack>`** answers "what skills and agents does this pack contain?" by walking the pack's source tree live on each call — so the answer can't drift, and nothing is persisted. `--format json` emits a stable object (`name`, `version`, `description`, `skills`, `agents`, `source`) for scripts and agents. When the catalogue can't be resolved, an *installed* pack still reports its inventory from your state files (marked `source: installed-state`); a not-installed pack errors.

A **profile** is a catalogue-curated, single-scope set of packs you install in one command — it declares its own scope, so `--scope` doesn't apply. **Upgrade takes no version** — the target is whatever the catalogue you point at declares; to pin a past version, point the catalogue at that git ref. Install a pack that's **already there** and `agentbundle` offers to `upgrade` it instead (`--yes` runs it straight away).

**Mutating commands ask first.** `uninstall`, the `--force` cleanup, and the upgrade offer all preview what they'll do and confirm before touching anything; `--dry-run` previews without writing, and `--yes` skips the prompt for non-interactive / CI use (where, without it, they refuse rather than hang).

## Enterprise distribution

For organizations running an internal Artifactory mirror or any static HTTPS server,
agentbundle's enterprise distribution capabilities handle the full adoption loop —
from org-wide channel configuration to CI-driven bulk upgrades.

**Install from an internal Artifactory channel:**

```bash
# Point agentbundle at your org's channel descriptor (one-time per machine,
# or pre-configured in your org fork — see Org bootstrap below)
agentbundle config set source catalogue+https://artifactory.example.test/agentbundle/catalogues/core/channels/stable.json

agentbundle install --pack core
```

The channel descriptor points to an immutable versioned archive; agentbundle
fetches, verifies its SHA-256 digest, and installs. Pass a bearer token via
`AGENTBUNDLE_HTTP_BEARER_TOKEN` — it is never stored in state, never printed, and
never forwarded to a different host.

**JSON output for CI pipelines:**

```bash
# See what's installed and what needs upgrading — machine-readable
agentbundle list-installed --format json
agentbundle list-installed --format json --updates-only
```

Returns a stable JSON contract (`schema_version` 1) with per-row status
(`up-to-date` / `upgrade-available` / `ahead` / `unknown`) and machine-readable
reason codes for unknown rows. Pipe into `jq` or your CI annotation step.

**Bulk upgrade in one scoped command:**

```bash
# Upgrade all installed packs in a scope — preflights before any write
agentbundle upgrade --all --scope repo --yes
agentbundle upgrade --all --scope user --format json --yes
```

Preflights all rows before writing anything; a blocked row stops the run before the
filesystem is touched. Partial failure is reported honestly — not described as a
rollback. Never silently downgrades an `ahead` row.

**Package your catalogue for Artifactory:**

```bash
agentbundle catalogue package \
  --root /path/to/catalogue \
  --bundle my-packs \
  --release 1.0.0 \
  --channel stable \
  --output dist/
```

Produces a deterministic, reproducible gzip archive (versioned) and a mutable channel
descriptor JSON (`stable.json`), ready to upload to Artifactory. Identical inputs
produce byte-identical archives (honors `SOURCE_DATE_EPOCH`).

**Source distribution for air-gapped or self-hosted catalogues:**

```bash
agentbundle catalogue package \
  --root /path/to/catalogue \
  --bundle my-packs \
  --release 1.0.0 \
  --flavor source \
  --output dist/
```

Produces a `catalogue-source-<release>.tar.gz` from a positive allowlist (packs, profiles, guides, marketplace manifest, legal files). Includes a `self-hosted-source-manifest.json` with per-file SHA-256 digests and provenance fields. `agentbundle install` refuses to install a source archive, preventing accidental misuse.

**Org bootstrap — ship the default channel in your fork:**

Add an `[organization.artifactory]` block to
`agentbundle/_data/install-defaults.toml` in your org's agentbundle fork:

```toml
[organization.artifactory]
enabled = true
base-url = "https://artifactory.example.test"
repository = "agentbundle"
bundle = "core"
channel = "stable"
```

Developers installing from your fork get the internal channel without a manual
`config set source` step. The block ships `enabled = false` in the public package.
A malformed `enabled = true` config fails closed — no silent fallback to the public
source.

**Offline and air-gapped hosts:** set `AGENTBUNDLE_NO_REMOTE=1` to skip the org
Artifactory bootstrap and editable-install detection entirely. `agentbundle` falls
straight through to the packaged default, so hosts without network access to Artifactory
still resolve a source without errors.

See the full enterprise adoption guide at
`docs/guides/_shared/how-to/use-an-artifactory-catalogue.md` for all six flows
(org bootstrap, repo-scope CI upgrade, user-scope MDM, source-conflict remediation,
disconnected hosts, and security controls).

## Build your own catalogue

`agentbundle` isn't tied to the agent-ready-repo catalogue. Any repo that lays its packs out the same way can use it.

**Bootstrap a new catalogue** in an empty directory:

```bash
agentbundle catalogue init --target /path/to/new-catalogue
```

Scaffolds `catalogue.toml`, the required directory tree (`packs/`, `profiles/`, `contracts/`, `.claude-plugin/`), and a starter `marketplace.json`. Skips files that already exist; reports conflicts without overwriting. Pass `--dry-run` to preview.

**Bootstrap a self-hosted enterprise catalogue** from an existing source:

```bash
agentbundle catalogue init \
  --preset self-hosted \
  --source /path/to/source-catalogue.tar.gz \
  --tooling vendored \
  --attribution white-label \
  --repository-url https://github.com/your-org/your-catalogue \
  --owner-email admin@example.com
```

Copies selected packs and profiles from the source archive, generates `catalogue.toml` with your identity, runs a fail-closed leak check, and writes `.agentbundle/self-host-state.json` to track managed files. `--tooling vendored` also copies the `agentbundle` source and `catalogue-curation` pack into `.agentbundle/tooling/` for air-gapped deployments. Re-run to apply updates; stale owned files are removed (sha256-guarded, user-modified files are skipped).

A pack is a directory:

```text
my-pack/
  pack.toml                  # name, version, adapter-contract, install scope,
                             # plus rich metadata (license, maintainers, links,
                             # categories, keywords) and a README pointer
  .claude-plugin/
    plugin.json              # Claude Code plugin manifest (hand-authored)
  README.md                  # the pack's portable doc — projected with the pack
  .apm/                      # primitives — projected by the build pipeline
    skills/<name>/
      SKILL.md               # the skill body; one folder per skill
      references/            # progressive-disclosure docs, loaded on demand
      assets/                # templates the skill copies into the repo
    agents/<name>.md         # subagents
    hooks/<name>.py          # lifecycle hooks
  seeds/                     # files scaffolded into the adopter repo
```

`pack.toml` is the **single source of truth** for a pack's metadata. Declare
`license`, `[[pack.maintainers]]`, `[pack.links]`, `categories`, and
`keywords` once; the build projects the cleanly-mappable subset — plus the
pack's `README.md` — into each distribution route's manifest (the `plugin.json`
/ `marketplace.json` entry), so the catalogue describes each pack richly rather
than with a single sentence. Extra fields stay in `pack.toml`; the projection
is deliberately lossy per tool.

Point a catalogue URI (a git URL or a local path) at the repo that holds your packs. Then `validate` a pack against the adapter contract, `render` it to preview the projection, and `install` it into a target repo. `scaffold` drops a pack's seeds into a fresh directory to start from. The build pipeline (`agentbundle.build`) is the same engine `make build` runs.

**Org adapter default:** If your org ships a private `agentbundle` wheel (or a fork pinned to your internal catalogue), you can set a default adapter for all developers without requiring them to run `agentbundle config set` or pass `--adapter` on every install. Add an `[organization]` table to `_data/install-defaults.toml` in your fork:

```toml
[organization]
preferred_adapter = "cursor"
```

The org hint fires after the user-config but before the on-disk IDE probe — so `--adapter`, user-config, and upgrade state-hints all take priority. An invalid value exits 1 before writing anything. See the [`agentbundle` reference](https://github.com/eugenelim/agent-ready-repo/blob/main/docs/guides/_shared/reference/agentbundle.md#org-adapter-default) for the full cascade.

**Bundled contracts** — the wheel ships the machine contracts used for offline validation:
`pack.schema.json`, `skill.schema.json`, `guide.schema.json`, `skill-manifest.schema.json`,
`profile.schema.json`, `catalogue.schema.json`, `target-vocab.toml`, and the adapter
contract files. All are available without network access via `importlib.resources`.

**Lint your catalogue** — shallow structural checks run without extra dependencies:

```bash
agentbundle catalogue lint --root .
```

For full [agentskills.io spec](https://agentskills.io/specification) compliance (frontmatter key set, description policy, encoding, evals schema), install the `lint` extra and run with `--deep`:

```bash
pip install 'agentbundle[lint]'
agentbundle catalogue lint --root . --deep
```

**Check self-host projection drift** — verifies that adapter-projected files (skills, agents, hooks) match their `.apm/` sources without writing anything:

```bash
agentbundle catalogue self-host --check --root .
```

Exits non-zero if any projected file is out of date. Safe to run in CI as a required check; use `--write` locally to regenerate.

**Run Tier-A activation evals** to measure whether each covered skill fires on the prompts it should:

```bash
agentbundle pack evals run --pack <pack-name> --catalogue-root .
```

See the [pack layout reference](https://github.com/eugenelim/agent-ready-repo/blob/main/docs/architecture/pack-layout.md) and [authoring a skill](https://github.com/eugenelim/agent-ready-repo/blob/main/docs/guides/_shared/how-to/author-a-skill.md).

## Catalogue defaults and pack config API

**Catalogue defaults** let operators ship sensible starting values for every pack they distribute. Add a `[pack-defaults.<pack-name>]` table to `catalogue.toml` and the defaults are baked in at publish time. They slot into the three-layer cascade: pack-source defaults → operator defaults → user config. A custom install root is also supported via `[catalogue] user-dir = "~/custom/path"`.

**Pack scripts** can resolve their user-scope directory and read the merged config at runtime using the `agentbundle.config` API:

```python
from agentbundle.config import pack_dir, load_pack_config

directory = pack_dir("my-pack")                 # ~/.agentbundle/my-pack/
config = load_pack_config("my-pack")            # merged dict: pack defaults + operator + user
```

**Operation log** — scripts can append structured JSONL records to `<pack_dir>/ops.jsonl` for lightweight audit trails:

```python
from agentbundle.oplog import write_entry

write_entry("my-pack", "install", src="git+https://example.com/my-pack")
```

**CLI commands** to read, write, and inspect pack config and operation logs:

```bash
agentbundle pack-config show my-pack            # all config values for a pack
agentbundle pack-config get  my-pack api-key    # single value
agentbundle pack-config set  my-pack api-key v  # write to user config.toml

agentbundle oplog show  my-pack                 # JSONL operation history
agentbundle oplog clear my-pack                 # wipe history (asks first)
```

## Per-session MCP server (workspace-mcp)

The `core` pack ships a per-session MCP server that a control harness can inject into
each Claude Code session. It exposes six tools over MCP stdio:

| Tool | What it does |
|---|---|
| `workspace_status` | Returns the queue (ready / blocked / active / shaping items) and active-run state — current phase, whether a gate is pending, and the gate question |
| `elicit` | Sends a question to the operator and blocks until they respond (300 s timeout) |
| `git_status` | Returns uncommitted changes (`git status --short`) |
| `git_branch` | Creates and checks out a feature branch scoped to the dispatched item |
| `git_commit` | Stages and commits only files under the item's configured output paths |
| `git_push` | Pushes the session branch to origin |

**Spawn it** (the harness does this, not the agent):

```bash
python3 -m agentbundle.workspace_mcp
```

**Inject the session instruction** so the agent knows to use the tools:

```python
from agentbundle.workspace_mcp import DEFAULT_SESSION_INSTRUCTION
```

Pass exactly one environment variable when spawning to set the session mode:
`WORKSPACE_MCP_SPEC_PATH` (path to the spec directory) for FSM/work-loop items,
or `WORKSPACE_MCP_DISPATCHED_ITEM` (`ini_slug/type:slug`) for non-FSM shaping
items. Setting neither gives discovery-only mode (git writes disabled). Setting
both is unsupported — only one selects the mode.

## Credentials

`agentbundle` doesn't resolve secrets. Credentialed skills use [`credbroker`](https://pypi.org/project/credbroker/), a standalone resolver that keeps cleartext out of the model's reach.

## Learn more

The full story — the loop, the reviewers, the pack catalogue — is in the [agent-ready-repo README](https://github.com/eugenelim/agent-ready-repo#readme).
