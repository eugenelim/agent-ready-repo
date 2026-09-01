# agentbundle

[![PyPI](https://img.shields.io/pypi/v/agentbundle)](https://pypi.org/project/agentbundle/)
[![Python](https://img.shields.io/pypi/pyversions/agentbundle)](https://pypi.org/project/agentbundle/)
[![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue)](https://github.com/eugenelim/agent-ready-repo#license)

**The installer for [agent-ready-repo](https://github.com/eugenelim/agent-ready-repo).** Think npm, but for the skills, subagents, and hooks your coding agent runs on. One pack, one command, every major agent — Claude Code, Codex, Cursor, Copilot, Gemini, and Kiro (both the CLI and the IDE).

## Quick start

```bash
python -m pip install agentbundle
```

Requires Python 3.11+. Runs on macOS, Linux, and Windows.

## What's new in 0.41.0

`install` and `validate` now accept a skill folder, a `skills/` collection, or a
single pack taken straight from a repository — no catalogue required. A direct
source is admitted against explicit shape and size bounds, pinned to the commit
its bytes came from, and summarised for consent before anything is written.

## What's new in 0.40.3

Catalogue validation now checks bounded reviewer declarations and keeps their
least-privilege posture in supported adapter projections.

## What's new in 0.40.2

Catalogue seed lint now accepts the core pack's bounded rule router,
cognitive-load topic, and scoped docs guidance. Undeclared seed paths still
fail closed.

## What's new in 0.40.1

Workspace MCP lifecycle metadata now dispatches briefs to the canonical
`author-delivery-brief` owner. Existing workspace kinds, queues, paths, and
lifecycle semantics are unchanged.

## What's new in 0.40.0

Catalogue builds now produce offline-validatable Agent Plugins 1.0.0 packages
under `dist/agent-plugins/<pack>/` for every skills-only pack. The new route
preserves canonical skill bytes and executable bits, emits a privacy-minimal
root `plugin.json`, and reports every pack excluded by non-portable primitives.
The paired plugin and MCP schemas are bundled from an immutable upstream commit;
MCP behavior remains a separate follow-on.

Extension namespaces are closed and allocation-gated. Kiro and Copilot are
reserved, while active namespaces must name a versioned schema before their
manifest data or files can enter a portable artifact.

## What's new in 0.39.4

Codex-projected agents that declare `Read`, `Grep`, or `Glob` without `Bash`
can read and search local files again. AgentBundle now retains Codex's default
shell tool for those read intents while confining the agent to a read-only
sandbox; write and web capabilities still require their corresponding source
declarations.

Kiro IDE and CLI agents may also declare `resources: []` to suppress the
default skill-resource injection without emitting an empty consumer field. The
portable way to say the same thing is Claude Code's own `skills: []`, which now
suppresses that injection too — a non-empty `skills` list is a build error until
`skill://` URI templating exists.

**Breaking for Kiro agent sources:** the Kiro projectors now bound the field set
they emit rather than passing unmapped source frontmatter through verbatim.
Claude Code fields Kiro cannot read (`permissionMode`, `memory`, `maxTurns`, …)
and IDE-only keys that make the CLI loader drop an agent (`hooks`) are dropped,
each with a `kiro: dropping … agent field` line on stderr. If you relied on the
previous pass-through, check your build log after upgrading.
## What's new in 0.39.3

The bundled workspace-status engine now recognizes reviewed legacy work-intake
migrations, validates durable operation digests, and refuses linked or aliased
workspace input before projecting exact legacy bytes.

## What's new in 0.39.2

Level A packs can now provide an optional manual next step after installation.
When present, `agentbundle install` prints it after `Verify:`, so packs can guide
adopters even when a runtime hook does not execute. Existing packs without the
field keep their current output, and Level B packs still require it.

## What's new in 0.39.1

Catalogue seed lint now rejects generic directory-tree placeholders unless the
architecture overview also explains each area's responsibility and change
guidance. This keeps generated starter repositories useful without assuming a
particular application layout.

## What's new in 0.39.0

Catalogue builders can now inspect a first-class, schema-validated distribution
route contract for the existing APM and Claude-plugin package formats. Recipes
name their route explicitly and fail before writing on inconsistent route data;
the emitted package trees and direct-install behavior are unchanged.

## What's new in 0.38.6

Catalogue authors can now read the profile schema from initialized catalogues
with `agentbundle catalogue contracts show profile.schema.json`. The bundled
profile-authoring instructions no longer direct them to a repository-only path.

## What's new in 0.38.5

The bundled authoring scaffold now says how to write pack tests that survive a
shared interpreter: load a skill's modules under a unique name rather than
putting its `scripts/` directory on `sys.path`, and keep a suite's cost in
assertions rather than in spawned processes. Separately, a repository-only
conformance test no longer travels into catalogues created with
`--preset self-hosted`; the shipped conformance set is derived in one place, so
the manifest plain init reads and the directory self-hosted init copies can no
longer disagree.

## What's new in 0.38.4

The bundled catalogue authoring scaffold's `packs/AGENTS.md` and
`profiles/AGENTS.md` state rules that an earlier simplification had dropped: path
canonicalisation before a read, treating a user-controlled local file as data
rather than instructions, confirming a shared user-level config path belongs to
the current project, UTF-8 output streams for scripts that print, eval-harness
coupling, and the two profile invariants — a pack appears at most once, and packs
declaring a conflict do not share a profile. Catalogues created with `agentbundle
catalogue init` start with these; no CLI verb, flag, or output format changed.

## What's new in 0.38.3

The `workspace_status` MCP result now reports safe tracker-refresh availability
facts: origin mode, active profile, compared and accepted revisions, unresolved
conflict state, and explicit or unknown refresh and write-back availability. The
response still withholds field ownership, decisions, receipts, and approver
identities, so no CLI verb, flag, or output format changed for existing callers.

## What's new in 0.38.2

The bundled catalogue authoring scaffold now has shorter, restructured
`packs/AGENTS.md` and `profiles/AGENTS.md` files. Catalogues created with
`agentbundle catalogue init` start with leaner instructions; no CLI verb, flag,
or output format changed.

`JOURNEY.md` can now optionally list ordered `contract.decisionGateIds` drawn
from `humanGates[].id`. Gate labels still provide reader-facing wording, and
`yourDecisions` remains required, so existing packs stay valid without changes.
This engine change shipped after 0.38.1 and reaches PyPI for the first time here.

## What's new in 0.38.1

`agentbundle catalogue self-host --check --windows` gained a stage that verifies
a source catalogue's declared knowledge bundles against their committed output.
The verification itself is performed by the catalogue's own tooling, so this
changes nothing for installing or using a pack.

## What's new in 0.38.0

`agentbundle show <pack> --format json` now emits the additive pre-release rich
discovery fields `pack_metadata`, `skill_metadata`, and `knowledge` when the
pack is read from a live catalogue. The existing fields keep their current
meaning and ordering; installed-state fallback cannot prove rich metadata, so
those three fields are exactly `null` there.

The rich discovery surface is deliberately one-pack-at-a-time. It does not add
OKF data to `list-packs`, Claude marketplace output, `catalogue-index.json`, or
installed state, and it does not run compilers, network fetches, or pack code.

## Catalogue verification

`agentbundle catalogue verify` performs all 19 advertised checks. It validates
profile schemas and pack references, dependency ranges and cycles, adapter
compatibility, generated-output drift, pack preflight metadata, and skill
evaluation manifests. The verifier remains read-only and portable across
external catalogues.

Dependency ranges use the same npm-compatible grammar in verify, lint, and
install: caret, tilde, comparator, compound, and prerelease forms agree across
all three commands. In particular, caret ranges below `1.0.0` use normal semver
compatibility (`^0.2` does not include `0.3.x`).

`agentbundle catalogue index` now generates a deterministic, adapter-neutral
`catalogue-index.json` from catalogue, pack, profile, and optional journey
metadata. The command validates against its bundled public schema before an
atomic no-follow write; `--dry-run` writes nothing, and `--format json` emits one
closed result document for automation.

The generated index exposes content-addressable pack digests, structural content
and execution inventory, profile composition, declared external effects, and
forward and inverse pack integrations without relying on one agent host's
marketplace format.

## Catalogue authoring

New catalogue scaffolds document the `JOURNEY.md` convention: required and
optional frontmatter, external-effect declarations, reader-facing body sections,
and migration guidance. Existing packs without a journey remain valid and appear
with an empty `journeys` array.

The same authoring reference retains the guide callout contract: exact quoted
wording remains a blockquote, while guidance uses the documented typed aside.

Generate and validate a neutral index with:

```bash
agentbundle catalogue index . --dry-run
agentbundle catalogue index . --output catalogue-index.json
```

## Contract discovery

The bundled public contract inventory includes `distribution-routes.toml` and
its closed schema for package-route semantics, plus
`catalogue-index.schema.json` for generated neutral indexes. It also includes
the strict `knowledge-captured-observation.schema.json` contract used by the
core pack's project-knowledge capture handoff.

You can inspect the exact public contracts bundled with the installed
AgentBundle version without network access:

```bash
agentbundle catalogue contracts list
agentbundle catalogue contracts show pack.schema.json
agentbundle catalogue contracts export --output ./reference-contracts
```

`list` and `show` are read-only. `export` writes reference copies through a
no-follow, preflighted batch writer; those copies do not override the contracts
AgentBundle uses for validation.

Successful `agentbundle catalogue init` output points to the scaffolded
`guides/_shared/reference/catalogue-authoring-standards.md`, contract discovery,
and catalogue verification. JSON init output remains unchanged.

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

**Try a pack without committing it** — so the pack is live in this clone while
`git status` stays clean:

```bash
agentbundle install --pack core --scope local
```

Local scope projects the same runtime files as repo scope, then records them in
`.git/info/exclude`. It requires a Git work tree. Uninstalling removes both the
projected files and the managed exclude entries; local and repo installs of the
same pack cannot coexist.

The install auto-detects your agent (`--adapter` overrides). Multi-IDE? Install the same pack for each agent at the same scope — they coexist, and the agents that read `.agents/skills/` (codex, cursor, gemini, copilot) share one skill copy instead of fighting over it. To install from a **different** catalogue, pass it as a trailing argument — a git URL or a local path (`agentbundle install --pack core <catalogue>`); a `config set source <catalogue>` makes that the default, and an editable clone (`pip install -e`) defaults to itself.

## Claude Code marketplace

Claude Code users can install any pack that permits user scope without first
installing this CLI:

```bash
claude plugin marketplace add eugenelim/agent-ready-repo
claude plugin install architect@agent-ready-repo
```

The marketplace excludes repo-only packs because Claude plugins live in a
global cache. Install `core` and other repo-only packs with `agentbundle` so
their files land in the project. For hook-bearing user-scope packs, the
generated marketplace description lists the authored hook event, matcher,
timeout, interpreter, and body path before publication.

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

**`show <pack>`** answers "what skills and agents does this pack contain?" by walking the pack's source tree live on each call — so the answer can't drift, and nothing is persisted. `--format json` emits a stable object (`name`, `version`, `description`, `skills`, `agents`, `integrations`, `source`, `pack_metadata`, `skill_metadata`, `knowledge`) for scripts and agents. The three rich metadata fields are pre-release: they are source-backed only for live catalogue reads and are not a cross-pack OKF index. When the catalogue can't be resolved, an *installed* pack still reports its inventory from your state files (marked `source: installed-state`), with `pack_metadata`, `skill_metadata`, and `knowledge` set to `null`; a not-installed pack errors.

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

Build residue is excluded, so it does not matter whether you packaged a working
tree you had just tested or npm-installed in. Pruned at every level of a pack:
`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.tox`,
`.hypothesis`, `htmlcov`, `node_modules`, `.venv`, `venv` — plus `*.pyc`,
`*.pyo`, `.DS_Store`, `coverage.xml` and `.coverage*` shards. The drop is
silent, so do not name a directory you mean to ship after one of those.

**Source distribution for air-gapped or self-hosted catalogues:**

```bash
agentbundle catalogue package \
  --root /path/to/catalogue \
  --bundle my-packs \
  --release 1.0.0 \
  --flavor source \
  --output dist/
```

Produces a `catalogue-source-<release>.tar.gz` from a positive allowlist
(`catalogue.toml`, packs, profiles, guides, a marketplace manifest when
present, and legal files), with the same build-residue exclusions as the
default flavour. Includes a `self-hosted-source-manifest.json` with per-file
SHA-256 digests and provenance fields. `agentbundle install` refuses to install
a source archive, preventing accidental misuse.

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

See [Configure catalogue enterprise
distribution](https://github.com/eugenelim/agent-ready-repo/blob/main/guides/_shared/how-to/configure-catalogue-enterprise-distribution.md)
for channel setup, authentication, CI upgrades, disconnected hosts, and the
security boundary.

## Build your own catalogue

`agentbundle` isn't tied to the agent-ready-repo catalogue. A catalogue source
has two required root markers: a valid `catalogue.toml` and a literal `packs/`
directory. A custom `catalogue.paths.packs` value controls where pack content
is read from; it does not replace the root `packs/` marker.

**Bootstrap a new catalogue** in an empty directory:

```bash
agentbundle catalogue init --target /path/to/new-catalogue
```

Scaffolds `catalogue.toml`, the required directory tree (`packs/`, `profiles/`, `contracts/`, `.claude-plugin/`), and a starter `marketplace.json`. Skips files that already exist; reports conflicts without overwriting. Pass `--dry-run` to preview.

After initialization, use `agentbundle catalogue contracts list` to find the
contract names bundled with your installed version. `show` prints one contract;
`export --output <dir>` copies the full public set for offline reference.

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
  .apm/                      # runtime — projected by the build pipeline
    skills/<name>/
      SKILL.md               # the skill body; one folder per skill
      scripts/               # helper code the skill invokes
      references/            # progressive-disclosure docs, loaded on demand
      assets/                # templates the skill copies into the repo
      evals/                 # activation + output-quality evals, skill-local
    agents/<name>.md         # subagents
    hooks/<name>.py          # lifecycle hooks
    hook-wiring/<name>.toml  # adapter event wiring for a shipped hook body
  tests/                     # implementation tests — NEVER projected
    skills/<name>/
    hooks/
    pack/
  seeds/                     # files scaffolded into the adopter repo
```

Three boundaries: the **pack** owns and executes its tests, **`.apm/`** is the
runtime export boundary, and a **skill** owns its eval fixtures. Only `.apm/`
and `seeds/` are projected into an installed environment — `tests/` is visible
in a catalogue archive, so an extracted pack can verify itself, but `install`
never places it. Keep tests out of `.apm/` even though the installer would
ignore them there; the separation is structural, not incidental.

`pack.toml` is the **single source of truth** for a pack's metadata. Declare
`license`, `[[pack.maintainers]]`, `[pack.links]`, `categories`, and
`keywords` once; the build projects the cleanly-mappable subset — plus the
pack's `README.md` — into each distribution route's manifest (the `plugin.json`
/ `marketplace.json` entry), so the catalogue describes each pack richly rather
than with a single sentence. The Claude-plugin route carries only packs whose
`[pack.install] allowed-scopes` admits `user`: a plugin's code lands in the
adopter's global cache, so a repo-only pack gets no `marketplace.json` entry
and is reached with `agentbundle install` instead. A marketplace entry's `source` is a `git-subdir`
object (`url`, `path`, and one of `ref`/`sha`) pointing at the pack's directory
on the published distribution branch, and every entry is schema-validated at
build time against `marketplace-entry.schema.json`. Extra fields stay in `pack.toml`; the projection
is deliberately lossy per tool.

A hook-bearing pack that permits user scope must explicitly set
`[pack.install] user-scope-hooks = true`. On the Claude-plugin route,
`agentbundle` compiles supported Claude-shaped wiring into native plugin hooks
and rejects unsafe event, matcher, timeout, command, or body-path shapes before
creating output. Direct CLI installs keep their adapter-native wiring contract.

Point a catalogue URI (a git URL or a local path) at the repo that holds your packs. Then `validate` a pack against the adapter contract, `render` it to preview the projection, and `install` it into a target repo. `scaffold` drops a pack's seeds into a fresh directory to start from. The build pipeline (`agentbundle.build`) is the same engine `make build` runs.

**Org adapter default:** If your org ships a private `agentbundle` wheel (or a fork pinned to your internal catalogue), you can set a default adapter for all developers without requiring them to run `agentbundle config set` or pass `--adapter` on every install. Add an `[organization]` table to `_data/install-defaults.toml` in your fork:

```toml
[organization]
preferred_adapter = "cursor"
```

The org hint fires after the user-config but before the on-disk IDE probe — so `--adapter`, user-config, and upgrade state-hints all take priority. An invalid value exits 1 before writing anything. See the [`agentbundle` reference](https://github.com/eugenelim/agent-ready-repo/blob/main/guides/_shared/reference/agentbundle.md#org-adapter-default) for the full cascade.

**Bundled contracts** — the wheel ships the machine contracts used for offline validation:
`pack.schema.json`, `skill.schema.json`, `guide.schema.json`, `skill-manifest.schema.json`,
`profile.schema.json`, `catalogue.schema.json`, `plugin-manifest.schema.json`,
`plugin-manifest.derived.schema.json`, `marketplace-entry.schema.json`,
`target-vocab.toml`, and the adapter contract files. All are available without network access via `importlib.resources`.

**Lint your catalogue** — shallow structural checks run without extra dependencies:

```bash
agentbundle catalogue lint --root .
```

Lint validates both source markers and then checks the configured pack content.
It requires `.claude-plugin/marketplace.json` only when the effective self-host
adapters include `claude-code`. A Kiro-only catalogue can omit that Claude
artifact; the default Claude Code and Codex projection still requires it.

For full [agentskills.io spec](https://agentskills.io/specification) compliance (frontmatter key set, description policy, encoding, evals schema), install the `lint` extra and run with `--deep`:

```bash
pip install 'agentbundle[lint]'
agentbundle catalogue lint --root . --deep
```

**Verify a catalogue before you ship it** — runs the full read-only contract and
self-host checks in one command:

```bash
agentbundle catalogue verify --root .
```

For a self-host-enabled catalogue with `.adapt-discovery.toml`, that includes the
self-host classifier. It treats generated targets as projected and known
repository-owned paths as excluded from projection. A genuinely unknown Git-visible
path remains an informational `unclassified` notice; it does not fail an otherwise
clean catalogue. Missing, modified, or orphaned projections do fail verification,
including generated executables under `.agentbundle/bin/` and vendored user libraries
under `.agentbundle/lib/`. Git filenames are read losslessly, and a failed Git listing
is reported as a warning rather than mistaken for a fully classified inventory.

To check only self-host projection drift, or to regenerate projected files locally:

```bash
agentbundle catalogue self-host --check --root .
agentbundle catalogue self-host --write --root .
```

Both check commands are safe to run in CI. The write command changes projected files.

By default projects for `claude-code` and `codex`. Downstream repos that use a single adapter (e.g. `kiro-ide`) can declare it in `catalogue.toml` — only that adapter is then projected, and its output files participate in the drift check:

```toml
[distribution.agentbundle]
preferred-adapter = "kiro-ide"
```

When `preferred-adapter` names an adapter not in the upstream `SELF_HOST_ADAPTERS` list, the self-host engine switches to single-adapter mode: only the named adapter is projected; Claude Code-specific artifacts (`.claude/`, `.codex/`, `.claude-plugin/`, `CLAUDE.md`) are neither written nor drift-checked.

**Run Tier-A activation evals** to measure whether each covered skill fires on the prompts it should:

```bash
agentbundle pack evals run --pack <pack-name> --catalogue-root .
```

See the [pack layout reference](https://github.com/eugenelim/agent-ready-repo/blob/main/docs/architecture/pack-layout.md) and [authoring a skill](https://github.com/eugenelim/agent-ready-repo/blob/main/guides/_shared/how-to/author-a-skill.md).

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
| `workspace_status` | Returns the queue (ready / blocked / active / shaping items), active-run state, and safe tracker-refresh facts such as origin mode, profile, revisions, conflict, and known availability |
| `elicit` | Sends a question to the operator and blocks until they respond (300 s timeout) |
| `git_status` | Returns uncommitted changes (`git status --short`) |
| `git_branch` | Creates and checks out a feature branch scoped to the dispatched item |
| `git_commit` | Stages and commits only files under the item's configured output paths |
| `git_push` | Pushes the session branch to origin |

**Spawn it** (the harness does this, not the agent):

```bash
python3 -m agentbundle.workspace_mcp
```

> **Trusted checkout only.** This form runs whichever `agentbundle` is on
> `sys.path`. If the repo uses an editable install (`pip install -e .`), it
> runs the local checkout's code. Use only on repos you trust. An isolated
> spawn mode (`python3 -I -m agentbundle.workspace_mcp`) is planned for
> Stage 2 and will require a stable non-editable install.

In trusted mode, workspace status prefers an installed core-pack projection and
falls back to the byte-identical engine projection bundled with `agentbundle`.

**Inject the session instruction** so the agent knows to use the tools:

```python
from agentbundle.workspace_mcp import DEFAULT_SESSION_INSTRUCTION
```

Pass exactly one environment variable when spawning to set the session mode:
`WORKSPACE_MCP_SPEC_PATH` (path to the spec directory) for FSM/work-loop items,
or `WORKSPACE_MCP_DISPATCHED_ITEM` (`ini_slug/type:slug`) for non-FSM shaping
items. Setting neither gives discovery-only mode (git writes disabled). Setting
both is unsupported — only one selects the mode.

## Corporate networks

macOS is the only platform where Python ignores the operating system's trust
store, which is why the automatic fallback above is macOS-only:

| Platform | Trust source | Needs anything from you? |
| --- | --- | --- |
| **Windows** | Python loads the Windows `CA` and `ROOT` stores and honours each certificate's trust settings | No — a root pushed by Group Policy or Intune already works |
| **Linux** | OpenSSL reads `/etc/ssl/certs` | No, once the authority is installed there |
| **WSL** | Same as Linux — a WSL distribution does **not** inherit the Windows certificate store | **Yes** — see below |
| **macOS** | OpenSSL reads a PEM file; the keychain is invisible to it | No — this is the case the fallback handles |

If your IT team gives you a CA bundle, point AgentBundle at it directly:

```bash
export AGENTBUNDLE_CA_BUNDLE=/path/to/corporate-ca.pem
agentbundle install --pack core
```

On `git+https://` sources that bundle is **added** to the default trust store, so
a bundle holding only your private authority still verifies public hosts. On
`catalogue+https://` and `archive+https://` it **replaces** the store, pinning
verification to your own authority — useful for an internal Artifactory mirror.

**WSL** is the case most likely to catch out a Windows-standardised organisation:
your IT team pushes the authority to Windows, Windows tools pick it up, and
nothing inside the WSL distribution does. Export it from Windows (Certificate
Manager → Trusted Root Certification Authorities → Export as Base-64 X.509), then
install it in the distribution:

```bash
sudo cp corporate-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

Two things no certificate configuration can fix: a proxy that requires Kerberos
or NTLM authentication, and an egress allowlist that permits `github.com` but not
`codeload.github.com` — a GitHub archive fetch redirects across both hosts.

A note on virtualenvs, since it comes up: creating one does **not** change TLS
trust. A virtualenv inherits its base interpreter's certificate store unchanged.
If an install works under one `python3` and not another, the interpreters differ,
not the environment — compare them with
`python3 -c "import ssl; print(ssl.get_default_verify_paths())"`.

## Credentials

`agentbundle` doesn't resolve secrets. Credentialed skills use [`credbroker`](https://pypi.org/project/credbroker/), a standalone resolver that keeps cleartext out of the model's reach.

## Learn more

The full story — the loop, the reviewers, the pack catalogue — is in the [agent-ready-repo README](https://github.com/eugenelim/agent-ready-repo#readme).
