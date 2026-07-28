# How to export a catalogue for org-fork distribution

**Use this when:** Your org maintains a fork of `agentbundle` and you want developers to run `agentbundle install` against your internal Artifactory channel without a manual `config set source` step.
**Prerequisites:** A `catalogue.toml` with `[distribution.agentbundle.artifactory]` populated; Artifactory accessible from your build host; `agentbundle` ≥ 0.22.0 installed.
**Result:** An org `agentbundle` wheel whose baked `install-defaults.toml` points to your channel, so every developer who installs from your internal index gets the right source automatically.

The mechanism is the org bootstrap (Layer 3 of the source-resolution chain). When `agentbundle` starts and no explicit source or user config is set, it reads `_data/install-defaults.toml` from the installed wheel and picks up the Artifactory coordinates baked in at publish time. No developer config required.

## Step 1 — Add `[distribution.agentbundle.artifactory]` to `catalogue.toml`

```toml
[distribution.agentbundle.artifactory]
enabled    = true
base-url   = "https://artifactory.example.com"
repository = "agentbundle-catalogues"
bundle     = "engineering"
channel    = "stable"
```

All five fields are required when `enabled = true`. Use your real Artifactory hostname,
the repository key, the bundle name your platform team assigned, and the channel name
you use when publishing releases (typically `stable`).

## Step 2 — Regenerate `install-defaults.toml`

From your catalogue root:

```bash
agentbundle catalogue sync-defaults --root . --write
```

This overwrites `agentbundle/_data/install-defaults.toml` (the path set by
`distribution.agentbundle.install-defaults-output` in `catalogue.toml`). The file is
committed to your fork — it is not generated at install time.

Verify the output before committing:

```bash
grep channel packages/agentbundle/agentbundle/_data/install-defaults.toml
# → channel = "stable"
```

An empty `channel = ""` means the field was missing or blank in `catalogue.toml`.
Fix it there and rerun.

## Step 3 — Add a CI drift check

```bash
agentbundle catalogue sync-defaults --root . --check
```

`--check` exits 0 when the on-disk file matches what `--write` would produce and non-zero
on drift. Add this to your CI pipeline on every push so a stale `install-defaults.toml`
blocks the build before the wheel ships.

## Step 4 — Build the wheel

```bash
cd packages/agentbundle
python -m build --wheel
```

The generated `dist/agentbundle-<version>-py3-none-any.whl` bundles the updated
`install-defaults.toml`. Publish it to your org's internal PyPI index.

## Step 5 — Developer install

Once the wheel is published, developers install it once:

```bash
pip install agentbundle --index-url https://pypi.example.com/simple/
```

From that point:

```bash
agentbundle install --pack core
```

resolves the catalogue from your Artifactory channel automatically. No `config set source`
needed. The org bootstrap fires at Layer 3; if the developer has a `[settings].source` set
in their user config, that takes priority (Layer 2).

## Offline and air-gapped hosts

For developer machines or CI runners that cannot reach Artifactory, set `AGENTBUNDLE_NO_REMOTE=1`:

```bash
AGENTBUNDLE_NO_REMOTE=1 agentbundle install --pack core /path/to/local-catalogue
```

This skips the org Artifactory bootstrap (Layer 3) and editable-install detection (Layer 4).
`agentbundle` falls through to the packaged default source (`[defaults] source` in
`install-defaults.toml`) or to the explicit catalogue argument. Useful in:

- CI pipelines that run fully offline against a local copy.
- Developer machines on restricted networks where Artifactory isn't reachable.
- Air-gapped infrastructure where no external HTTP is allowed.

Set the variable in the shell profile, a CI environment variable, or a wrapper script —
it does not need to appear in any config file.

## Reverting to the public catalogue

Set `enabled = false` in `catalogue.toml`, rerun `sync-defaults --write`, and rebuild.
Developers who install the updated wheel fall through to the packaged default (Layer 5),
which resolves the public `agent-ready-repo` catalogue.

## What this does not affect

- `agentbundle catalogue package` — takes its `--bundle`, `--release`, and `--channel`
  flags at run time. The `catalogue.toml` block drives `install-defaults.toml` only.
- Developers who have run `agentbundle config set source <url>` — their Layer 2 user
  config always wins over the org bootstrap.
- `AGENTBUNDLE_HTTP_BEARER_TOKEN` — the bearer token env var is separate from the
  bootstrap config; set it per host or per CI job where Artifactory requires auth.

## See also

- [How to package a catalogue for enterprise app-store distribution](../../../docs/guides/how-to/enterprise-app-store.md) — the Artifactory upload workflow (connected → disconnected host).
- [Flow E — fully disconnected host](../../../docs/guides/how-to/flow-e-disconnected.md) — receive-side extraction and install.
- [`agentbundle` reference](../reference/agentbundle.md) — full source-resolution chain and all env vars.
