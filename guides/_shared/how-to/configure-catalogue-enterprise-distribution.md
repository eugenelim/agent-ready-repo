---
title: "Set enterprise defaults"
summary: "Point every install at your organization's catalogue with no per-machine setup."
pack: _shared
kind: how-to
---

# Set enterprise defaults

Add your catalogue's location to `catalogue.toml`, and installs from your own `agentbundle` build use it by default.

## Record the coordinates

Add the location of your catalogue to `catalogue.toml`, the file that describes the catalogue:

```toml
[distribution.agentbundle.artifactory]
enabled    = true
base-url   = "https://artifactory.example.test/artifactory"
repository = "agentbundle-catalogues"
bundle     = "platform"
channel    = "stable"
```

All five fields are required when `enabled = true`, and `base-url` must use HTTPS. Never put a password, token, or authenticated URL in this file.

## Generate the defaults

Write `install-defaults.toml` from those coordinates:

```bash
agentbundle catalogue sync-defaults --root . --write
```

The generated file holds only the same non-secret coordinates. Run it again with `--check` in CI to catch drift.

## Ship them in your wheel

Commit `install-defaults.toml` beside `catalogue.toml`, then build and publish your organization wheel, the installable Python package. An installed copy builds its source from your coordinates:

```text
catalogue+<base-url>/<repository>/catalogues/<bundle>/channels/<channel>.json
```

Signing in to read the catalogue is separate, and [Host on Artifactory](create-a-self-hosted-catalogue.md) covers it.

## Install from the default

With no catalogue argument, an install uses your default:

```bash
agentbundle install --pack core
```

If it reaches the wrong catalogue, a personal source is set. Run `agentbundle config unset source` to let your default take over.

Next, [host the catalogue on Artifactory](create-a-self-hosted-catalogue.md), or see the full [Artifactory distribution reference](../reference/artifactory-catalogue-distribution.md) for CI, troubleshooting, and proxy settings.
