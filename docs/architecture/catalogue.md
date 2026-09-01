# The catalogue

> What a catalogue *is* on disk, how `agentbundle` finds one, and how you
> point it at your own. `packs/` in this repo is one catalogue; the same
> shape lets any org stand up theirs.

A catalogue is the thing `agentbundle install` reads packs *from*. This repo
ships one — the `packs/` tree — but nothing about the tool is bound to it.
Fork it, build a fresh one, or host one privately, and point the CLI at yours.

A catalogue is no longer the *only* thing install reads from. `install` also
accepts a **direct source**: a skill folder, a `skills/` collection, or a
single pack, taken straight from a repository with no catalogue around it.
Direct sources have their own admission rules and their own state provenance;
a repository carrying catalogue markers takes the catalogue route instead, and
the direct route refuses it and says so. Everything below describes the
catalogue route, which is unchanged.

## What a catalogue is

A catalogue source is a directory holding two adapter-neutral markers:

```
<catalogue-root>/
├── catalogue.toml                    # catalogue metadata and distribution config
├── packs/
│   └── <pack>/…                     # one directory per shippable pack (see pack-layout.md)
└── .claude-plugin/                  # present when Claude projection is enabled
    └── marketplace.json             # generated Claude marketplace listing
```

The source-identity contract is the root `catalogue.toml` plus the literal
root `packs/` directory. Anything missing either is refused. The check is one
function,
[`source_defaults._has_catalogue_markers`](../../packages/agentbundle/agentbundle/source_defaults.py),
while lint validates the configuration and configured operational paths.
There is no registry service or catalogue network protocol.

`marketplace.json` is the catalogue-level listing consumed by
`/plugin marketplace add`; the build aggregates version and metadata into it
from the `.claude-plugin/plugin.json` of every pack whose `allowed-scopes`
admits `user` *and* that declares `[pack.adapter-contract] version` — the
resolver gates on the contract version first, so a pack without one resolves
`repo` whatever its `allowed-scopes` says. The route installs at user scope, so repo-scoped packs are
excluded — see `docs/specs/claude-plugin-route-scope`. How a pack's
`pack.toml` projects into that entry is covered in
[`pack-manifest.md`](pack-manifest.md).

## How agentbundle finds a catalogue

Every source verb — `install`, `upgrade`, `list-packs`, `list-profiles`,
`list-installed` — takes an optional trailing catalogue argument. When you
omit it, the CLI resolves one through a five-layer, first-match-wins chain in
[`source_defaults.resolve_default_source`](../../packages/agentbundle/agentbundle/source_defaults.py):

| Layer | Source | Set by |
| --- | --- | --- |
| 1 | The explicit trailing argument | `agentbundle install core <catalogue>` — passed through verbatim |
| 2 | User config `[settings].source` | `agentbundle config set source <catalogue>` |
| 3 | Org Artifactory bootstrap | `[distribution.agentbundle.artifactory]` in `catalogue.toml`, baked into `_data/install-defaults.toml` |
| 4 | Editable-install detection | `pip install -e <clone>` — auto-detected |
| 5 | Packaged default | `_data/install-defaults.toml` — baked into the wheel |

Layer 4 is the one that makes a local clone "just work": when `agentbundle`
is installed editable, it reads its own PEP 610 `direct_url.json`, and walks
up from the package directory — bounded by the enclosing `.git` root — to the
first ancestor carrying `catalogue.toml` and literal root `packs/`. So a developer working inside
a clone gets that clone as their catalogue with no configuration.

Setting `AGENTBUNDLE_NO_REMOTE=1` skips Layers 3 and 4, falling through directly to Layer 5. See the [adopter reference](../../guides/_shared/reference/agentbundle.md) for the full env var list.

When no layer yields a source, the CLI refuses with a message naming the
recovery paths rather than silently falling back to the current directory:

```
no catalogue source: pass a catalogue argument, run 'agentbundle config set
source …', or pip install -e the catalogue
```

## Point agentbundle at your own catalogue

A catalogue source is either a **local path** (containing both markers) or a
**`git+https://` URL**. Two durable ways to switch, plus the one-off:

```bash
# Persist a default (layer 2) — survives across every verb, every repo.
agentbundle config set source git+https://github.com/acme/agent-kit
agentbundle config set source /abs/path/to/your/catalogue
agentbundle config unset source          # clear it; fall back to layers 3–5

# One-off (layer 1) — a trailing argument beats the configured default.
agentbundle install core git+https://github.com/acme/agent-kit

# Bind to a working clone (layer 4) — no config needed.
python -m pip install -e /abs/path/to/your/catalogue
```

The config value is stored in your OS config directory
(`~/Library/Application Support/agentbundle/config.toml` on macOS,
`$XDG_CONFIG_HOME/agentbundle/config.toml` on Linux). A `git+https://` value
is accepted as-is; a local path is validated for both markers at resolution
time, so a stale or wrong path fails loudly with a diagnostic rather than
installing nothing.

Note that `~/.agentbundle/` is a *destination* — the user-scope install root
packs are projected **into** — not a source. You never point `source` at it.

## Stand up your own catalogue

The minimum is a directory with a valid `catalogue.toml` and
`packs/<your-pack>/`, then any of the switches above. A Claude marketplace is
generated only when the effective adapter set includes `claude-code`. The full,
opinionated recipe — fork this catalogue, add an org pack carrying your house
conventions, blank the packaged upstream default so stray installs can't reach
it, and ship a one-command profile every engineer installs — lives in the
adopter how-to:
[Build an org stack pack](../../guides/_shared/how-to/build-an-org-stack-pack.md).

## Where to read next

- [`pack-layout.md`](pack-layout.md) — the on-disk shape of a single pack
  inside `packs/`.
- [`pack-manifest.md`](pack-manifest.md) — how `pack.toml` projects into the
  `marketplace.json` listing.
- [`skill-and-pack-format.md`](skill-and-pack-format.md) — the format map:
  the agentskills.io skill standard we conform to, wrapped by our pack
  envelope and projection.
- [Build an org stack pack](../../guides/_shared/how-to/build-an-org-stack-pack.md) —
  the full stand-up-your-own recipe.
