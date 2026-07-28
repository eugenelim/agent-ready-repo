# How to package a catalogue for enterprise app-store distribution

This guide covers the Artifactory-based packaging workflow for distributing a catalogue to
disconnected hosts within an enterprise network.

## Overview

The workflow has two sides:

- **Connected host** — has access to the catalogue source repo and Artifactory; builds and publishes.
- **Disconnected host** — can reach the internal Artifactory registry; downloads and installs.

## Prerequisites

- Catalogue passes `agentbundle catalogue verify --root .` on the connected host.
- Artifactory repository accessible from the connected host.
- Bundle identifier, release version, and channel name agreed with your platform team.

## Configuration

Add the Artifactory block to `catalogue.toml`:

```toml
[distribution.agentbundle.artifactory]
enabled = true
base-url = "https://artifactory.example.com"
repository = "agentbundle-catalogues"
bundle = "engineering"
channel = "stable"
```

Run `agentbundle catalogue sync-defaults --write` after adding or updating this block.
The generated `install-defaults.toml` baked into the wheel will contain the channel value,
so downstream installs resolve the correct Artifactory path.

## Step 1 — Build the dist tree

```bash
agentbundle catalogue build --root . --output dist
```

## Step 2 — Verify (confirm pre-package state)

```bash
agentbundle catalogue verify --root .
```

The verify step must exit 0 before packaging.

## Step 3 — Package

```bash
agentbundle catalogue package \
  --root . \
  --bundle engineering \
  --release 1.2.0 \
  --channel stable \
  --output dist/artifactory \
  --source-revision "$(git rev-parse HEAD)"
```

Output layout:

```
dist/catalogues/engineering/releases/1.2.0/
  catalogue-1.2.0.tar.gz
  catalogue-1.2.0.tar.gz.sha256
  channels/stable.json
```

## Step 4 — Upload to Artifactory

Upload the archive and sidecar (not the channel descriptor — it is audit metadata only and is not
used by the disconnected host to resolve a local catalogue):

```bash
jf rt upload \
  "dist/artifactory/catalogues/engineering/releases/1.2.0/stable/engineering-1.2.0.tar.gz*" \
  "agentbundle-catalogues/engineering/releases/1.2.0/stable/"
```

## Step 5 — Download on the disconnected host

```bash
jf rt download \
  "agentbundle-catalogues/engineering/releases/1.2.0/stable/engineering-1.2.0.tar.gz" \
  /tmp/downloads/

jf rt download \
  "agentbundle-catalogues/engineering/releases/1.2.0/stable/engineering-1.2.0.tar.gz.sha256" \
  /tmp/downloads/
```

## Step 6 — Verify and extract

See [Flow E — fully disconnected host](flow-e-disconnected.md) for the complete receive-side
workflow.

## CI integration

For automated packaging in CI:

```yaml
- name: Package catalogue
  run: |
    agentbundle catalogue verify --root .
    agentbundle catalogue package \
      --root . \
      --bundle ${{ env.BUNDLE }} \
      --release ${{ env.RELEASE }} \
      --channel ${{ env.CHANNEL }} \
      --output dist/artifactory \
      --source-revision ${{ github.sha }}
```

Never embed production Artifactory URLs, credentials, or bearer tokens in workflow YAML. Use
secrets or a credentials broker.

## Environment variables

| Variable | Description |
|---|---|
| `AGENTBUNDLE_HTTP_BEARER_TOKEN` | Bearer token for authenticated HTTPS catalogue sources. Never forwarded across origins; not logged. |
| `AGENTBUNDLE_NO_REMOTE` | When set to `1`, skips the Artifactory org bootstrap (Layer 3) and editable-install detection (Layer 4). Useful for offline and air-gapped deployments. |
| `AGENTBUNDLE_CA_BUNDLE` | Path to a PEM file containing one or more CA certificates. Use when your Artifactory instance uses a private or self-signed CA. Example: `export AGENTBUNDLE_CA_BUNDLE=/etc/ssl/corp-ca.pem` |
