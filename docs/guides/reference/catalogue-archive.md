# Catalogue archive format

A packaged catalogue is a set of three files produced by `agentbundle catalogue package`. Together
they form the distributable unit for fully-disconnected hosts.

## Output files

```
<output>/catalogues/<bundle>/releases/<release>/<channel>/
  <bundle>-<release>.tar.gz        # archive
  <bundle>-<release>.tar.gz.sha256 # SHA-256 sidecar
  channel.json                     # channel descriptor
```

### Archive (`<bundle>-<release>.tar.gz`)

A gzip-compressed tar archive containing the installable subset of the
catalogue. It is not a source-tree mirror and may omit source-only files such
as `catalogue.toml`:

```
packs/
  <pack-name>/
    pack.toml
    .claude-plugin/plugin.json
    .apm/
      skills/<name>/SKILL.md
      agents/<name>.md
      hooks/<name>.py
      ...
    seeds/
    evals/
```

### SHA-256 sidecar (`.sha256`)

A single line containing the hex SHA-256 digest of the archive, followed by two spaces and the
archive filename:

```
3a7b9c... <bundle>-<release>.tar.gz
```

This matches `sha256sum` output format. The sidecar is what the receiving host uses to verify
integrity before extraction.

### Channel descriptor (`channel.json`)

JSON metadata about this release, including the channel name, release version, bundle identifier,
published-at timestamp, and minimum agentbundle version. It is audit context for the connected-side
registry and is NOT used by the disconnected host to resolve a local catalogue.

## Verification

Before extracting on the receiving host, verify the archive against its sidecar:

```bash
agentbundle catalogue verify \
  --archive <bundle>-<release>.tar.gz \
  --sha256-file <bundle>-<release>.tar.gz.sha256
```

Exits 0 on success. Do not extract an archive that fails verification.

## Transfer

Transfer only the archive and sidecar to the disconnected host:

- `<bundle>-<release>.tar.gz`
- `<bundle>-<release>.tar.gz.sha256`

The channel descriptor (`channel.json`) is not needed on the disconnected host — it is registry
audit metadata for the connected side only.

## Extraction

After successful verification:

```bash
mkdir -p /opt/company/agentbundle/catalogues/<bundle>
tar -xzf <bundle>-<release>.tar.gz -C /opt/company/agentbundle/catalogues/<bundle>
```

An installable archive is a published artifact, not a source catalogue. It
intentionally need not contain the source-only `catalogue.toml` marker, so do
not configure its extracted directory as a local source. Use the verified
archive through the publication or installation workflow. For a local source,
use a checkout or source distribution containing both root `catalogue.toml`
and literal root `packs/`.
