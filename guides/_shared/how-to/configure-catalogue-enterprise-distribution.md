# How to configure a catalogue for enterprise distribution

**Use this when:** You maintain a catalogue and want developers to run `agentbundle install` against your internal Artifactory channel without a manual `config set source` step.
**Prerequisites:** Artifactory accessible from your build host; bundle name and channel agreed with your platform team; `agentbundle` ≥ 0.22.0 installed.
**Result:** A `catalogue.toml` configured with your Artifactory coordinates, and a regenerated `install-defaults.toml` that bakes those coordinates into the distributed wheel — so every developer who installs from your internal index gets the right source automatically.

The mechanism is the org bootstrap. When `agentbundle` starts with no explicit source and no user config, it reads `_data/install-defaults.toml` from the installed wheel. If that file carries a valid `[organization.artifactory]` block, `agentbundle` resolves the catalogue source from Artifactory without any per-developer configuration.

## Step 1 — Add `[distribution.agentbundle.artifactory]` to `catalogue.toml`

```toml
[distribution.agentbundle.artifactory]
enabled    = true
base-url   = "https://artifactory.example.com"
repository = "agentbundle-catalogues"
bundle     = "engineering"
channel    = "stable"
```

All five fields are required when `enabled = true`. `base-url` must be HTTPS with no
credentials embedded. `repository`, `bundle`, and `channel` must each match
`[A-Za-z0-9._-]+` — no path separators.

## Step 2 — Regenerate `install-defaults.toml`

From your catalogue root:

```bash
agentbundle catalogue sync-defaults --root . --write
```

This rewrites `agentbundle/_data/install-defaults.toml` (the path declared by
`distribution.agentbundle.install-defaults-output` in `catalogue.toml`). The file is
committed to your repository — it is not generated at install time.

Confirm the channel was written correctly:

```bash
grep channel packages/agentbundle/agentbundle/_data/install-defaults.toml
# → channel = "stable"
```

If you see `channel = ""`, the `channel` field was absent or blank in `catalogue.toml`.
Correct it and rerun.

## Step 3 — Add a CI drift check

```bash
agentbundle catalogue sync-defaults --root . --check
```

`--check` exits 0 when the on-disk file matches the current `catalogue.toml`, non-zero
when they diverge. Add this to your CI pipeline so a stale `install-defaults.toml` fails
the build before the wheel ships.

## Step 4 — Commit and rebuild

Commit `install-defaults.toml` alongside the `catalogue.toml` change, then rebuild and
republish your agentbundle wheel as usual. Once the updated wheel is on your internal
index, developers get the right source automatically:

```bash
agentbundle install --pack core
```

No `config set source` needed. A developer who has set `[settings].source` in their user
config keeps that value (it takes priority at Layer 2).

## Offline and air-gapped environments

For hosts that cannot reach Artifactory, set `AGENTBUNDLE_NO_REMOTE=1`:

```bash
AGENTBUNDLE_NO_REMOTE=1 agentbundle install --pack core /path/to/local-catalogue
```

This skips the org Artifactory bootstrap and editable-install detection, falling through
to the packaged default source or an explicit catalogue argument. Set it in the shell
profile, a CI environment variable, or a wrapper script — no config file needed.

## Disabling the bootstrap

To revert to the public catalogue, set `enabled = false` in `catalogue.toml`, rerun
`sync-defaults --write`, and rebuild. Developers who install the updated wheel fall through
to the packaged default source.

## See also

- [`agentbundle` reference — source resolution and env vars](../reference/agentbundle.md#catalogue-source-resolution)
