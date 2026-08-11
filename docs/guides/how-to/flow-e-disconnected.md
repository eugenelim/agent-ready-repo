# Flow E — fully disconnected host

This flow covers installing a catalogue on a host that cannot reach the public internet or a
catalogue registry. It requires a pre-packaged archive produced on a connected host.

**Not supported:** resolving a channel descriptor (`channel.json`) from a local directory to
install packs. Local channel-descriptor resolution is NOT supported. The disconnected path is
archive-only: transfer archive + sidecar, verify, extract, and pass the trusted extraction path
explicitly to install commands.

## What you need

- `<bundle>-<release>.tar.gz` — the packaged archive
- `<bundle>-<release>.tar.gz.sha256` — the SHA-256 sidecar
- AgentBundle ≥ 0.14.0 installed on the disconnected host

The channel descriptor (`channel.json`) is NOT required on the disconnected host. It is audit
metadata for the connected-side registry only.

## Step 1 — Transfer

Copy the archive and sidecar to the disconnected host. Use whatever secure transfer mechanism your
environment provides (scp, a mounted network share, an internal Artifactory mirror).

```
/tmp/downloads/
  engineering-1.2.0.tar.gz
  engineering-1.2.0.tar.gz.sha256
```

Do NOT transfer `channel.json` — it is not used on the disconnected side.

## Step 2 — Verify the archive

```bash
agentbundle catalogue verify \
  --archive /tmp/downloads/engineering-1.2.0.tar.gz \
  --sha256-file /tmp/downloads/engineering-1.2.0.tar.gz.sha256
```

Verify must exit 0. Do not extract an archive that fails verification.

## Step 3 — Extract to a stable path

```bash
mkdir -p /opt/company/agentbundle/catalogues/engineering
tar -xzf /tmp/downloads/engineering-1.2.0.tar.gz \
    -C /opt/company/agentbundle/catalogues/engineering
```

The extracted layout contains:

```
/opt/company/agentbundle/catalogues/engineering/
  packs/
    core/
    governance-extras/
    ...
  .claude-plugin/marketplace.json  # only when Claude projection is included
```

## Step 4 — Confirm the layout

```bash
ls /opt/company/agentbundle/catalogues/engineering/packs/
```

`packs/` must exist before proceeding. The marketplace file is present only
when the published artifact includes the Claude projection.

## Step 5 — Use the extracted archive explicitly

```bash
agentbundle list-packs /opt/company/agentbundle/catalogues/engineering
```

An installable archive intentionally omits the source-only `catalogue.toml`
marker. Do not save its extracted directory as the default source; pass the
trusted local path explicitly to commands that consume the archive contents.

## Step 6 — Install from the verified path

```bash
agentbundle install --pack core /opt/company/agentbundle/catalogues/engineering
```

The selected pack installs from the verified extracted archive.

## Upgrading

To upgrade to a new release, repeat Steps 1–5 with the new archive, then pass
the new extraction path explicitly:

```bash
agentbundle upgrade --pack core /opt/company/agentbundle/catalogues/engineering
```

## Limitations

- Local channel-descriptor resolution (`channel.json` in a local directory) is **not supported**.
  The channel descriptor is a registry artifact, not a local install mechanism.
- Moving from an Artifactory-hosted source to an explicitly supplied local
  extraction path (or vice versa) is a source change. Follow the normal
  reinstall process required for installed packs to reflect the new source.
