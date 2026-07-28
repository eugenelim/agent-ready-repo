# agentbundle design

---

## 1. How agentbundle works

### Problem

AI agent tooling — skills, hooks, agents, commands — needs to be distributed
across multiple IDE adapters (Claude Code, Cursor, Kiro IDE, Kiro CLI,
GitHub Copilot, Codex, Gemini). Each adapter has a different file layout,
frontmatter schema, and capability surface. A single pack author should not
have to write and maintain seven versions of the same skill. agentbundle is
the build and distribution layer that translates one source into the right
shape per adapter, installs it into the right location, and tracks what
landed where.

### Core entities

**Pack** — the unit of authorship and installation. A pack groups skills,
agents, hooks, and commands by functional domain (`atlassian`, `github`,
`linear`, `core`, …). Metadata in `pack.toml`; source artifacts in `.apm/`.

**Catalogue** — a collection of packs from one source (git repo, tarball,
internal Artifactory bundle). Declares layout, build config, and
distribution settings in `catalogue.toml`.

**Adapter** — a target IDE or agent tool. agentbundle supports eight at
contract v0.17: `claude-code`, `kiro-ide`, `kiro-cli`, `kiro` (deprecated
alias for `kiro-ide`), `copilot`, `codex`, `cursor`, `gemini`.

**Primitive** — the nine artifact types a pack can ship: `skill`, `agent`,
`hook-body`, `hook-wiring`, `command`, `kiro-ide-hook`, `shared-libs`,
`adapter-root-bins`, `user-libs`. The adapter contract maps each
(primitive × adapter) pair to a projection recipe or `dropped`.

**Scope** — where projected files land: `repo` (current project, tracked by
`.agentbundle/state.toml` at the repo root) or `user` (home directory,
tracked by `~/.agentbundle/state.toml`). Each pack declares the scopes it
supports; the installer enforces them.

### Install flow

```
agentbundle install --pack <name> [<catalogue-uri>]
        │
        ▼
1. Source resolution (five-layer)
   explicit URI › user config › org Artifactory bootstrap ›
   editable-install detection (PEP 610) › packaged default
        │
        ▼
2. Catalogue fetch → tempdir
   local path | git+https:// | catalogue+https:// | archive+https://
        │
        ▼
3. Validate catalogue.toml and pack.toml against JSON schema + business rules
        │
        ▼
4. Build pack for the active adapter
   render each primitive through the adapter's projection recipe;
   apply adapter frontmatter mapping
        │
        ▼
5. Tier-classify each output path against the existing state.toml
   T1: CLI owns it, SHA matches    → overwrite
   T2: CLI owns it, SHA differs    → write .upstream.<ext> companion
   T3: not in any pack's state row → refuse
        │
        ▼
6. Write files under path jail (safety.write_jailed)
        │
        ▼
7. persist_state_locked: re-read state, merge new PackState row, os.replace
        │
        ▼
8. Write .adapt-install-marker.toml at scope root
   (session-start hook surfaces the adapt nudge on next session open)
```

Profiles install a curated set of packs in a single command; each profile
declares its own scope and pack list.

### Tier system

Every file the CLI knows about lives in exactly one tier at any point in
time. Computed by comparing the on-disk SHA with the SHA in state.toml:

| Tier | Condition | CLI behaviour on upgrade |
|------|-----------|--------------------------|
| **T1** | CLI projected it; on-disk SHA matches state | Overwrite freely |
| **T2** | CLI projected it; on-disk SHA differs (user edited) | Write `.upstream.<ext>` companion; leave original |
| **T3** | Not recorded in any pack row | Refuse to touch |

### Adapter contract

`_data/adapter.toml` (contract v0.17) is the enumerated source of truth for
the (primitive × adapter) matrix. It drives:

- which primitives a pack may declare per adapter
- how each primitive is rendered (projection recipe: `skill-md`,
  `agent-md`, `merge-json`, `codex-agent-toml`, …)
- where outputs land (`allowed-prefixes` per adapter per scope)
- which adapters support user-scope installs

`SPEC_VERSION` in `agentbundle/__init__.py` is parsed from the contract at
import time. Lint and build gates refuse packs referencing primitives not in
the contract for the target adapter.

### CLI surface

```
agentbundle install      --pack <name> | --profile <name>  [<catalogue>]
agentbundle upgrade      --pack <name>                     [<catalogue>]
agentbundle uninstall    --pack <name>
agentbundle list-installed   [--scope repo|user] [--check-drift] [--format table|json]
agentbundle list-packs       [<catalogue>]
agentbundle list-profiles    [<catalogue>]
agentbundle list-targets
agentbundle show         <pack>
agentbundle docs         <pack> [<file>]
agentbundle scaffold     --pack <name> --output <dir>
agentbundle adapt        <scope>
agentbundle render       --pack <name> --adapter <name> --output <dir>
agentbundle config       set source <uri> | set adapter <name> | get | unset
agentbundle validate     <pack-dir>
agentbundle catalogue    build | self-host | package | sync-defaults | lint | verify
agentbundle lint         packs [<path>]
agentbundle pack         evals run | evals show
agentbundle init-state   [--scope repo|user]
```

### State file

`state.toml` at `~/.agentbundle/` (user scope) or `<repo-root>/.agentbundle/`
(repo scope) records every installed pack. One row per `(pack, adapter)` pair:

```toml
[packs.atlassian.claude-code]
source     = "git+https://github.com/example/catalogue"
version    = "0.6.3"
scope      = "user"
installed  = "2026-07-15T10:22:00Z"
user_root  = "~/.agentbundle"            # § 4 addition
files      = { ".claude/skills/jira/SKILL.md" = "sha256:abc…" }
```

Concurrent writes are serialised by `statelock.persist_state_locked`
(`O_CREAT|O_EXCL` lockfile + re-read-merge-write-under-lock).

### User config

`~/.agentbundle/config.toml` (managed by `agentbundle config`) stores the
user's preferred adapter and default catalogue source:

```toml
[settings]
adapter = "claude-code"
source  = "git+https://github.com/example/my-catalogue"
```

---

## 2. Catalogue capability

### Catalogue structure

```
catalogue.toml          ← distribution metadata, build config, paths
packs/
  <pack-name>/
    pack.toml           ← pack identity, scopes, allowed-adapters, evals
    .apm/               ← primitive source tree
    seeds/              ← scaffold templates (dropped by `agentbundle scaffold`)
    docs/               ← pack-specific documentation
    guides/             ← (optional) pack guides mirroring guides/_shared layout
profiles/
  <name>.toml           ← curated pack sets
guides/
  _shared/              ← cross-cutting guides (any pack can reference)
  _reference/           ← catalogue-level reference docs
  <pack-name>/          ← pack-specific guide tree
```

### `catalogue.toml`

Key sections:

```toml
[catalogue]
name                     = "agent-ready-repo"
display-name             = "Agent Ready Repo"
description              = "…"
minimum-agentbundle-version = "0.13.0"
user-dir                 = "~/.agentbundle"   # § 4 addition — preferred user root

[catalogue.paths]
packs                    = "packs"
profiles                 = "profiles"
marketplace              = ".claude-plugin/marketplace.json"
build-output             = "dist"

[distribution.agentbundle]
preferred-adapter        = "claude-code"
default-source           = "git+https://github.com/example/my-catalogue"
install-defaults-output  = "packages/agentbundle/agentbundle/_data/install-defaults.toml"

[distribution.agentbundle.artifactory]
enabled                  = false

[pack-defaults.atlassian]          # § 4 addition — catalogue operator overrides
url         = "https://jira.yourorg.com/"
project-key = "INFRA"
```

### Distribution mechanisms

| URI form | Mechanism |
|----------|-----------|
| Local path | Used as-is |
| `git+https://<host>/<owner>/<repo>[@<ref>]` | GitHub archive tarball, extracted to tempdir — no git subprocess |
| `catalogue+https://<url>` | Enterprise: SHA-256-verified tarball, origin-locked redirects, member-by-member extraction |
| `archive+https://<url>` | Same without the origin lock |

All fetches use `urllib.request` only. SSH URIs are not supported.

### Artifactory enterprise distribution

For organisations that cannot use GitHub as a distribution channel (air-gapped
networks, private IP ranges, internal proxy policies), agentbundle supports
JFrog Artifactory as the catalogue host. This is the `catalogue+https://`
path end-to-end.

#### Catalogue author setup

The catalogue declares its Artifactory coordinates in `catalogue.toml`:

```toml
[distribution.agentbundle.artifactory]
enabled    = true
base-url   = "https://artifactory.example.com"
repository = "agent-catalogues"    # Artifactory generic repo name
bundle     = "my-catalogue"        # logical catalogue bundle name
channel    = "stable"              # release channel (required when enabled)
```

`catalogue lint` validates all five fields when `enabled = true`:
`base-url` must be `https://`, no credentials in the netloc, no query or
fragment. `repository`, `bundle`, and `channel` must each match
`[A-Za-z0-9._-]+` and must not be `..`. `channel` is required; an absent
or empty value raises `CatalogueConfigError` with `channel = "stable"` as
the example value.

`compile_defaults` bakes the coordinates into `install-defaults.toml`:

```toml
# _data/install-defaults.toml  (generated)
[organization.artifactory]
enabled    = true
base-url   = "https://artifactory.example.com"
repository = "agent-catalogues"
bundle     = "my-catalogue"
channel    = "stable"
```

#### URL construction

`read_org_bootstrap` constructs a `catalogue+https://` source URI from the
baked coordinates:

```
catalogue+https://<base-url>/<repository>/catalogues/<bundle>/channels/<channel>.json
```

Example:
```
catalogue+https://artifactory.example.com/agent-catalogues/catalogues/my-catalogue/channels/stable.json
```

This `.json` file is the channel manifest — a JSON document pointing to the
current bundle archive. The catalogue operator uploads it as part of the
release process (see `catalogue package`).

#### Runtime source resolution (Layer 3)

At install time, when the user provides no explicit source URI and has no
`source` in their user config, `resolve_default_source` reaches Layer 3:

```
Layer 1: explicit CLI arg
Layer 2: user config  (~/.agentbundle/config.toml [settings].source)
Layer 3: org Artifactory bootstrap  ← reads install-defaults.toml
Layer 4: editable-install detection (PEP 610 direct-url.json)
Layer 5: packaged default source    (install-defaults.toml [defaults].source)
```

Layer 3 is **fail-closed**: if `organization.artifactory.enabled = true` but
any field is malformed, `CatalogueError` is raised and the install aborts —
it never falls through to Layer 4/5 with a corrupt configuration. If
`enabled = false` (or the section is absent), Layer 3 returns `None` and
resolution continues.

**`AGENTBUNDLE_NO_REMOTE=1`** skips Layers 3 and 4 entirely, falling straight
through to Layer 5. Use it on air-gapped hosts or CI environments that cannot
reach Artifactory — the install resolves the packaged default source without
any network contact.

#### Fetch security

`https_catalogue.py` handles `catalogue+https://` URIs:

- **SHA-256 verification** — the channel manifest includes the expected
  digest of the bundle archive; the download is rejected if it doesn't match.
- **Origin-locked redirects** — HTTP redirects are followed only to the same
  origin (`netloc`); a redirect to a different host is a hard error.
- **Member-by-member extraction** — the tarball is not bulk-extracted; each
  member path is validated against the pack's declared `allowed-prefixes`
  before being written to disk.

#### Operator checklist

To enable Artifactory distribution:

1. Set `[distribution.agentbundle.artifactory] enabled = true` with all five
   fields (`base-url`, `repository`, `bundle`, `channel`, `enabled`) in `catalogue.toml`.
2. Run `agentbundle catalogue sync-defaults` to bake coordinates into
   `install-defaults.toml`.
3. Run `agentbundle catalogue package --channel stable` to produce the
   bundle archive and the `stable.json` channel manifest.
4. Upload the archive and manifest to Artifactory at the constructed path.
5. Distribute the updated agentbundle package (which carries the baked
   `install-defaults.toml`) to users — via PyPI, internal pip mirror, or
   direct install.

Users install packs with a bare `agentbundle install --pack <name>` — no
source URI needed. Layer 3 resolves it automatically from the baked
coordinates.

### install-defaults baking

`catalogue sync-defaults` runs `compile_defaults` and writes
`install-defaults.toml` into `_data/`. This file ships bundled with
agentbundle and is read at runtime without contacting the catalogue source.

```toml
# _data/install-defaults.toml  (generated — do not edit)
[organization]
preferred_adapter = "claude-code"

[defaults]
source = "git+https://github.com/example/my-catalogue"

[pack-defaults.atlassian]         # § 4 addition
url         = "https://jira.yourorg.com/"
project-key = "INFRA"
```

`check_defaults` does a byte-exact drift check; CI fails when
`install-defaults.toml` is out of sync with `catalogue.toml`.

### Build pipeline

The build processes one pack for one adapter:

1. Walk `.apm/<primitive>/` and load source files.
2. Apply the adapter's projection recipe per primitive.
3. Apply adapter frontmatter mapping (source keys → adapter-expected keys).
4. Compute output paths under `allowed-prefixes`.
5. Return a footprint: `{relpath: sha256}` for every output file.

Deterministic: same source + adapter + contract → same output.

### Catalogue operator tooling

`agentbundle catalogue` subcommands for pack authors and release engineers:

| Subcommand | Purpose |
|------------|---------|
| `lint` | Validate `catalogue.toml`, `pack.toml`(s), and source files against schema + business rules |
| `verify` | Check a built dist tree matches the source |
| `build` | Produce a distributable dist tree |
| `self-host` | Project core packs (+ governance-extras) into the repo's own workspace |
| `package` | Bundle into a distributable `catalogue+https://` tarball |
| `sync-defaults` | Regenerate `install-defaults.toml` from `catalogue.toml` |

---

## 3. How packs work

### Pack structure

```
packs/<name>/
├── pack.toml          ← identity, install constraints, evals list
├── README.md
├── config.toml        ← pack-source config defaults + schema  (§ 4 addition)
├── AGENTS.md          ← pack-specific agent context
├── .apm/
│   ├── skills/        ← one subdirectory per skill; contains SKILL.md [+ assets/]
│   ├── agents/        ← agent .md files
│   ├── hooks/         ← hook body scripts (.py or .sh)
│   ├── hook-wiring/   ← hook wiring .json files
│   ├── commands/      ← command scripts
│   └── kiro-ide-hooks/← Kiro IDE–specific hook files
├── seeds/             ← scaffold templates
└── docs/              ← pack documentation tree
```

### `pack.toml`

```toml
[pack]
name          = "atlassian"
version       = "0.6.3"
description   = "Jira / Confluence skills and workflows."
display_name  = "Atlassian"
license       = "Apache-2.0 OR MIT"
categories    = ["integrations", "project-management"]
keywords      = ["jira", "confluence"]

[pack.adapter-contract]
version       = "0.8"    # minimum contract version the pack was authored against

[pack.install]
default-scope    = "user"
allowed-scopes   = ["user", "repo"]
allowed-adapters = ["claude-code", "kiro-ide", "codex", "copilot", "cursor", "gemini"]

[pack.evals]
skills = ["jira", "jira-align", "jira-brief-intake", "flow-metrics", …]

[pack.links]
documentation = "https://github.com/example/catalogue/tree/main/guides/atlassian/"
```

`allowed-adapters` constrains which adapters the build will target. A pack
that uses only `skill` and `agent` primitives can set a broad list; a pack
that relies on adapter-specific primitives (e.g. `kiro-ide-hook`) narrows it.

### Primitives in detail

| Primitive | Source location | What the adapters receive |
|-----------|----------------|---------------------------|
| `skill` | `.apm/skills/<name>/SKILL.md` | A SKILL.md file at the adapter's configured skills path |
| `agent` | `.apm/agents/<name>.md` | An agent file at the adapter's agents path; frontmatter remapped per adapter |
| `hook-body` | `.apm/hooks/<name>.py` | A hook script at the adapter's hook body location |
| `hook-wiring` | `.apm/hook-wiring/<name>.json` | Merged into the adapter's hook config (e.g. `settings.json` for Claude Code) |
| `command` | `.apm/commands/<name>.md` | A slash-command file (Claude Code only; `dropped` on all other adapters) |
| `kiro-ide-hook` | `.apm/kiro-ide-hooks/<name>.md` | Kiro IDE–specific hook file |
| `shared-libs` | `.apm/shared-libs/` | Shared Python/shell libraries placed at the adapter's lib path |
| `adapter-root-bins` | `.apm/adapter-root-bins/` | Scripts placed at the adapter's root binary location |
| `user-libs` | `.apm/user-libs/` | User-scope shared libraries |

Primitives marked `dropped` in the contract for a given adapter are silently
excluded from the build for that adapter. A `dropped-primitives` warning
is emitted at install time when a pack ships a primitive the target adapter
cannot receive.

### Skills

A skill is the primary primitive. Each skill lives in its own subdirectory:

```
.apm/skills/<slug>/
├── SKILL.md       ← the skill definition — rendered as-is by all adapters
└── assets/        ← optional supporting files projected alongside the skill
```

`SKILL.md` frontmatter declares the skill's name, description (≤ 1024 chars
for Kiro compatibility), version, and optional metadata:

```markdown
---
name: jira
description: Use this skill to create, update, and query Jira issues.
---

# Skill: jira
…
```

The rendered output for Claude Code lands at `.claude/skills/<slug>/SKILL.md`.
For Kiro IDE at `.kiro/steering/<slug>.md`. For Copilot at
`.github/skills/<slug>/SKILL.md`. The adapter contract's projection recipe
handles path and frontmatter transformation automatically.

### Agents

Agent files live at `.apm/agents/<name>.md` with adapter-specific frontmatter
keys. The build applies the adapter's frontmatter mapping (declared in
`_data/adapter.toml`) to translate source keys into the format each adapter
expects. For example, Claude Code's `description` maps to Kiro's `description`
unchanged, but Codex expects its agent config under `.codex/agents/<name>.toml`
in a different schema entirely.

### Hooks

Two complementary primitives:

**`hook-body`** — the executable script (`.py`; `.sh` is also accepted but
`.py` is preferred for Windows portability). Projected to the adapter's
hook body location (e.g. `tools/hooks/<name>.py` for Claude Code).

**`hook-wiring`** — the JSON configuration that registers the hook body with
the adapter's hook mechanism (e.g. merged into `~/.claude/settings.json`
for Claude Code's `hooks` key). Multiple packs can wire hooks to the same
event; the `merge-json` recipe handles conflict-free merging.

### Profiles

A profile is a curated set of packs installed in a single command:

```toml
# profiles/starter.toml
[profile]
name        = "starter"
description = "Core + Atlassian + GitHub — a minimal engagement stack."
scope       = "user"

[[profile.packs]]
name = "core"

[[profile.packs]]
name = "atlassian"

[[profile.packs]]
name = "github"
```

Profiles declare their own scope; `--scope` is not allowed alongside
`--profile`.

### Pack evals

`agentbundle pack evals run` drives the pack's skill-activation evaluations,
checking that the adapter's agent activates the right skill for a given
natural-language prompt. The `[pack.evals]` field in `pack.toml` lists the
skill slugs under test. Results are streamed as JSONL and summarised in a
table.

---

## 4. Pack config and ops

### Motivation

Pack scripts (skills, hooks, tools) need to read site-specific settings —
system URLs, credential references, feature flags — that vary between
catalogue adopters. They also need a record of what they did so that
subsequent runs and human auditors can inspect history.

Neither `state.toml` (the CLI's install record) nor projected skill files
are the right home for this: state.toml is owned by the CLI, and projected
files are managed by the pack author. The user's home directory is the
natural place for per-pack runtime data.

This section specifies:

- **`pack_dir` / `load_pack_config`** added to `agentbundle.config`.
- **`agentbundle.oplog`** — atomic JSONL append.
- **CLI subcommands** — `agentbundle pack-config` and `agentbundle oplog`.
- **`guides/_shared/reference/pack-config-api.md`** — the pack-author reference.

Both modules are pure I/O layers. Schema parsing and business logic belong
to the pack script.

**Non-goals:** config encryption, remote config sync, multi-user sharing,
real-time oplog streaming.

---

### Directory layout

Each catalogue writes its pack directories into its own **user root**. The
default root is `~/.agentbundle/`; a catalogue declares an alternative in
`catalogue.toml`. The subdirectory name is the pack slug.

```
~/.agentbundle/               ← default root for agent-ready-repo catalogue
├── state.toml                ← existing CLI install record
├── atlassian/
│   ├── config.toml           ← pack-specific user config (not source-controlled)
│   └── ops.jsonl             ← operation log
├── github/
│   ├── config.toml
│   └── ops.jsonl
├── linear/
│   └── config.toml
└── core/
    └── ops.jsonl

~/agentcommander/             ← custom root declared by agent-commander catalogue
└── agent-commander/
    ├── config.toml
    └── ops.jsonl
```

Directories are created with mode `0o700`, matching `user_state_path`.

---

### Root resolution

**The authoritative root for each pack lives in `state.toml`.** `PackState`
gains a `user_root` field written at install time from `catalogue.toml`'s
`catalogue.user-dir`. This keeps the root under the existing
`persist_state_locked` machinery and prevents silent mislocation if any
side-file is deleted.

`pack_dir(pack_name, *, home=None)` resolution order:

0. **`home=` kwarg** — short-circuits everything else. Used in tests to
   pin the user root to a temp directory without touching env vars.
1. **`AGENTBUNDLE_USER_ROOT` env var** — routed through
   `scope.resolve_user_root()`. Test/CI escape hatch; shifts the entire
   user root.
2. **`user_root` in the *user*-scope `~/.agentbundle/state.toml` for this
   pack slug** — written at install time (e.g. `~/agentcommander`). Always
   the user-scope state.toml, even for packs installed at repo scope;
   pack config/oplog is a user-home concern regardless of install scope.
3. **`~/.agentbundle/`** — fallback when the pack is absent from
   user-scope state.toml (first-run or partial install). Correct
   first-run behaviour: `load_pack_config` returns `{}`.

`pack_dir` consults any `(pack_slug, *)` row in user-scope state.toml. If
multiple rows exist for the same slug (different adapters, or two catalogues
sharing a slug), all rows must agree on `user_root`. If they don't,
`pack_dir` raises `PackRootConflict` — install-time lint should prevent
this for catalogues with overlapping slugs.

Directory creation is delegated to a new `safety.make_pack_dir(base, pack_name)`
that carries the symlink/TOCTOU guard from `user_state_path` **and** jails
`base` to the user's home via `resolve_user_root()` — a catalogue setting
`user-dir` outside `$HOME` is rejected before any directory is created.

**`catalogue.toml` extension:**

```toml
[catalogue]
user-dir = "~/agentcommander"   # optional; default "~/.agentbundle"
minimum-agentbundle-version = "0.21.0"   # must be ≥ the release shipping §4
```

`catalogue lint` requires `minimum-agentbundle-version` ≥ the agentbundle
release that introduces `user-dir` whenever the key is present.

Schema: add `user-dir` as optional string to the `catalogue` object in
`_data/catalogue.schema.json`. Add `user_dir: str = "~/.agentbundle"` to
`CatalogueConfig` in `catalogue_tooling/config.py`.

**`PackState` extension:** add `user_root: str = "~/.agentbundle"` field,
written at install time via `persist_state_locked`. Pre-field rows
(installed before this version) are read with the default `"~/.agentbundle"`;
a subsequent `agentbundle upgrade` rewrites the row with the correct
`user_root` from the catalogue source.

---

### Config cascade

Three layers, merged in order (later wins):

```
1. Pack-source defaults    packs/<pack>/config.toml  [defaults]
2. Catalogue overrides     catalogue.toml  [pack-defaults.<pack>]
3. User overrides          ~/<root>/<pack>/config.toml
```

Layers 1 and 2 are **build-time**: `compile_defaults` merges them into
`install-defaults.toml` under `[pack-defaults.<pack>]`. At runtime,
`load_pack_config` reads two sources only — baked + user.

#### Pack-source `config.toml`

Each pack ships `packs/<pack-name>/config.toml`:

```toml
[defaults]
url         = "https://jira.example.com/"
project-key = "PROJ"

[schema]
url         = { type = "string", description = "Jira base URL" }
project-key = { type = "string", description = "Default Jira project key" }
```

`[defaults]` feeds into `compile_defaults`. `[schema]` is consumed by
`catalogue lint` for validation; not read at runtime.

#### Catalogue operator overrides

`[pack-defaults.<pack>]` is a **top-level** section in `catalogue.toml`
(not under `[distribution.agentbundle]` — pack config is adapter-agnostic):

```toml
[pack-defaults.atlassian]
url         = "https://jira.yourorg.com/"
project-key = "INFRA"
```

`compile_defaults` merges pack-source defaults with catalogue overrides and
emits to `install-defaults.toml`. Catalogue values override pack-source
values; keys present only in pack-source pass through unchanged.

#### User overrides

Users hand-edit `~/<root>/<pack>/config.toml` or use
`agentbundle pack-config set`. The file is created with mode `0o600`.
Merge is shallow: `{**baked_defaults, **user_overrides}`. Nested tables:
the later layer replaces the whole sub-table — prefer flat pack configs.

---

### API additions to `agentbundle.config`

Added to the existing `config.py` (not a new module — the names are
distinct from everything already there, and a separate module would
fragment a small surface):

```python
def pack_dir(pack_name: str, *, home: Path | None = None) -> Path:
    """Return <user_root>/<pack_name>/, creating it (0o700) on first access.

    Resolution order:
      0. home= kwarg (test override — short-circuits everything)
      1. AGENTBUNDLE_USER_ROOT env var (via resolve_user_root)
      2. user_root from user-scope state.toml for this pack slug
         (always user-scope state.toml, even for repo-scoped packs)
      3. ~/.agentbundle/ (fallback for packs not yet in state.toml)

    Raises PackRootConflict when multiple rows for the same slug disagree
    on user_root. Delegates directory creation to safety.make_pack_dir,
    which jails base to $HOME and carries the symlink/TOCTOU guard from
    user_state_path.
    """

def load_pack_config(
    pack_name: str,
    *,
    path: Path | None = None,
    home: Path | None = None,
) -> dict:
    """Merged pack config: baked catalogue defaults then user overrides.

    Layer 1: _data/install-defaults.toml [pack-defaults.<pack>]  (may be {})
    Layer 2: <pack_dir>/config.toml user overrides               (may be {})

    Shallow merge. Returns {} when both layers absent.
    Never raises on a missing file. path= overrides user-config for tests.
    """
```

**Usage in pack scripts:**

```python
from agentbundle.config import load_pack_config

cfg = load_pack_config("atlassian")
url = cfg.get("url", "https://jira.example.com/")
```

---

### New module: `agentbundle.oplog`

```python
def write_entry(
    pack_name: str,
    action: str,
    src: str,
    dst: str | None = None,
    *,
    extra: dict | None = None,
    home: Path | None = None,
) -> None:
    """Atomic JSONL append to <pack_dir>/ops.jsonl.

    Creates directory and file on first call. Entry shape (key order):

        {"action": "archive", "src": "/path/a", "dst": "/path/b",
         ...extra, "ts": "2026-07-27T14:32:01.234Z"}

    ts    — UTC ISO-8601 with milliseconds; captured after the payload
            and emitted as the LAST key so the entry reflects when it
            was fully assembled.
    dst   — omitted when None.
    extra — merged after dst, before ts; reserved keys (ts, action,
            src, dst, _truncated) in extra raise ValueError before any I/O.

    Oversized entries: if the base fields alone (action + src + dst)
    exceed PIPE_BUF, raises EntryTooLargeError before any I/O — the
    caller must shorten src/dst. If extra pushes the total over the cap,
    extra is dropped and "_truncated": true is written instead — the
    side-effect is already committed; raising after the fact is wrong.
    """
```

**Usage in pack scripts:**

```python
from agentbundle.oplog import write_entry

write_entry("atlassian", "sync", str(issue_key))
write_entry("atlassian", "archive", str(src), str(dst),
            extra={"ticket": "PROJ-42"})
```

#### Atomicity

**POSIX** (`os.name == "posix"`): `os.open(O_WRONLY | O_CREAT | O_APPEND)`,
then a **single `os.write()` call**. On Linux and macOS, a single
`write(2)` to an `O_APPEND` file is positioned atomically by the kernel's
inode lock — no other writer can interleave within one syscall. A retry
loop would allow interleaving *between* retries, so the entry must fit in
one call. Entries are serialised before calling `_append_line`; if the
serialised length exceeds `PIPE_BUF` (512 bytes minimum per POSIX — 4096
in practice on Linux/macOS), write raises `EntryTooLargeError` *before*
any I/O, preserving the atomicity guarantee. Known limitation: NFS-mounted
home directories — callers on NFS can wrap `write_entry` in a `state_lock`.

**Windows** (`os.name != "posix"`): `statelock.state_lock` with a sibling
`ops.jsonl.lock`.

```python
_POSIX = os.name == "posix"
_PIPE_BUF = 4096   # conservative; POSIX minimum is 512

def _append_line(path: Path, line: bytes) -> None:
    if len(line) > _PIPE_BUF:
        raise EntryTooLargeError(len(line), _PIPE_BUF)
    if _POSIX:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            n = os.write(fd, line)
            if n != len(line):
                raise EntryTooLargeError(len(line), n)  # short write — filesystem full
        finally:
            os.close(fd)
    else:
        from agentbundle.statelock import state_lock
        with state_lock(path):
            with open(path, "ab") as f:
                f.write(line)
```

**Durability:** no `fsync` per entry — an unflushed tail can be lost on
crash. Acceptable for an ops log. Callers that need durability call
`os.fsync` after `write_entry`.

---

### CLI surface

Pack scripts use the Python API. The CLI subcommands exist for users
setting up config manually, for shell-based scripts, and for debugging.

#### `agentbundle pack-config`

```
agentbundle pack-config get <pack> [<key>]
    Print resolved config (all keys as TOML, or a single value as plain
    string). Exit 1 with message if <key> is absent.

agentbundle pack-config set <pack> <key> <value>
    Write <key> = <value> into ~/<root>/<pack>/config.toml (0o600).
    Creates the file if absent. Preserves unrelated keys.
    Value is always written as a TOML basic string — no type coercion
    against [schema]. Pack scripts are responsible for parsing (e.g.
    int(cfg["port"]), cfg["enabled"].lower() == "true"). This is
    intentional: the CLI cannot safely infer type without a loaded schema,
    and string-only is always lossless.

agentbundle pack-config unset <pack> <key>
    Remove <key> from the user override file. No-op if absent.

agentbundle pack-config show <pack>
    Print merged config annotated with the source of each value:
      url = "https://jira.yourorg.com/"   # baked default
      project-key = "MYPROJ"             # user override
    "baked default" covers both pack-source defaults and catalogue
    overrides — install-defaults.toml merges them at build time and
    the runtime cannot distinguish which layer a baked value came from.
```

`pack-config set` uses the existing `_emit_basic_string` / `_toml_key`
serialisation helpers in `config.py` and the same read-modify-write shape
as `write_setting` in `user_config.py`.

#### `agentbundle oplog`

```
agentbundle oplog show <pack> [--last N]
    Print the last N entries (default 20) as human-readable lines.
    Exits 0 with "no entries" if the log is absent.

agentbundle oplog clear <pack> [--yes]
    Truncate <pack>/ops.jsonl. Prompts for confirmation unless --yes.
```

The CLI write path (`agentbundle oplog write`) is omitted until a real
non-Python caller exists.

---

### Pack-author reference

The canonical reference lives at `guides/_shared/reference/pack-config-api.md`.
Other catalogues adopt the same `guides/_shared/` convention at the same
path in their own repo — no projection, no external URL.

**What `packs/AGENTS.md` adds:**

```markdown
## Per-pack config and ops log

Pack scripts read site-specific config via the `agentbundle` Python API.
The catalogue operator pre-configures defaults in `catalogue.toml`; users
override in `~/<root>/<pack>/config.toml`.

**Reading config:**

    from agentbundle.config import load_pack_config

    cfg = load_pack_config("my-pack")
    url = cfg.get("url", "https://fallback.example.com/")

Returns the merged dict (baked defaults + user overrides). Never raises;
returns `{}` on first run.

**Writing an ops log entry:**

    from agentbundle.oplog import write_entry

    write_entry("my-pack", "archive", str(src), str(dst))

**Declaring config keys** — create `packs/<pack>/config.toml`:

    [defaults]
    url = "https://example.com/"

    [schema]
    url = { type = "string", description = "Service base URL" }

`catalogue lint` validates the declared schema.

**User setup:**

    agentbundle pack-config set my-pack url https://internal.example.com/
    agentbundle pack-config show my-pack

Full reference: `guides/_shared/reference/pack-config-api.md`
```

---

### Files to create / modify

All paths relative to `packages/agentbundle/` unless noted.

| Path | Change |
|------|--------|
| `agentbundle/config.py` | Add `pack_dir()` and `load_pack_config()`; add `user_root` to `PackState` |
| `agentbundle/oplog.py` | New module |
| `agentbundle/safety.py` | Add `make_pack_dir(base, pack_name)` with symlink/TOCTOU guard |
| `agentbundle/_data/catalogue.schema.json` | Add `catalogue.user-dir` (optional string); add top-level `pack-defaults` object |
| `agentbundle/catalogue_tooling/config.py` | Add `user_dir` to `CatalogueConfig`; parse `[pack-defaults.*]` |
| `agentbundle/catalogue_tooling/defaults.py` | Include `user_dir` and `[pack-defaults.*]` in `compile_defaults`; update `check_defaults` ordering |
| `agentbundle/commands/pack_config_cmd.py` | New: `pack-config get/set/unset/show` |
| `agentbundle/commands/oplog_cmd.py` | New: `oplog show/clear` |
| `agentbundle/cli.py` | Register new subcommands |
| `guides/_shared/reference/pack-config-api.md` *(repo root)* | New: pack-author reference guide |
| `packs/AGENTS.md` *(repo root)* | Add pack-config + oplog section |
| `tests/unit/test_pack_config.py` | New: root resolution, cascade merge, empty-dict on absent, env-var override |
| `tests/unit/test_oplog.py` | New: creates dir, JSONL shape, extra= merge, truncation marker, concurrent appends, reserved-key rejection |
| `tests/unit/test_pack_config_cmd.py` | New: CLI get/set/unset/show |

---

### Resolved design decisions

**Root storage — `user-scope state.toml`, not a side index.** A separate
index file is deletable and has no locking story. `state.toml` is the locked,
authoritative per-pack record; adding `user_root` reuses `persist_state_locked`
and prevents silent mislocation. Always the user-scope state.toml regardless
of install scope — pack config/oplog is a user-home concern.

**Slug collision across catalogues — `PackRootConflict` on disagreement.**
`pack_dir` asserts all `(slug, *)` rows in user-scope state.toml agree on
`user_root`. Catalogue operators must coordinate slugs across catalogues
they intend to co-install. This is a known design limitation and the right
failure mode (loud, not silent mislocation).

**`catalogue.user-dir` jailed to `$HOME`.** `make_pack_dir` rejects a resolved
base outside the user's home via `resolve_user_root()`. A catalogue cannot
write to `/etc/` or arbitrary absolute paths.

**`catalogue.user-dir` version-gated.** `catalogue lint` requires
`minimum-agentbundle-version` ≥ the introducing release when `user-dir` is
present. Older installs silently mislocate; the gate prevents that.

**`catalogue.toml` key for pack-defaults — top-level `[pack-defaults.*]`.**
Pack config is adapter-agnostic, so it does not belong under
`[distribution.agentbundle]`.

**Three-layer config cascade.** Pack-source defaults + catalogue overrides
merged at build time into `install-defaults.toml`; user overrides applied
at runtime. Two file reads at runtime; the full cascade is auditable via
`pack-config show`.

**`pack-config set` is string-only.** No type coercion against `[schema]`.
Pack scripts parse as needed. The CLI cannot safely infer type without a
loaded schema; string-only is always lossless.

**Oplog — single `os.write()` on POSIX, capped at PIPE_BUF.** A retry loop
would allow interleaving between calls; one syscall is atomic. Base-field
oversize raises before I/O; extra-field oversize truncates (side-effect
already committed). Windows uses `state_lock`.

**`pack-config show` labels baked values as "baked default"** — not
"catalogue default" or "pack default". `install-defaults.toml` merges both
layers at build time; the runtime cannot distinguish them without added
per-key provenance.

**Pre-field state.toml rows default to `~/.agentbundle/`.** On next
`upgrade`, the row is rewritten with the correct `user_root` from the
catalogue source.

**Self-hosted catalogue reference — `guides/_shared/reference/`, no PyPI
link.** Other catalogues place their reference at the same path in their
own repo.
