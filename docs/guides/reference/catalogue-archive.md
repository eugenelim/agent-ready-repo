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

### Manifest (`catalogue-manifest.json`)

The runtime archive carries `catalogue-manifest.json` with `schema` `2`. It lists every other
archived file in `files[]` as `{path, sha256}`; it does not list itself. Two more lists name the
installable units:

| List | Entry | Source |
|------|-------|--------|
| `packs[]` | `{name, version, path, digest}` | one entry per `packs/<dir>/pack.toml`; `path` is `packs/<dir>` |
| `profiles[]` | `{name, path, digest}` | one entry per `profiles/<name>.toml` directly under `profiles/`; sorted by name |

A `.toml` file in a subdirectory of `profiles/` stays in `files[]` and gets no profile entry.
`profiles[]` entries were plain name strings before release 0.53.0; the verifier still accepts
that older shape.

**Unit digest.** `digest` is `sha256:` followed by the lowercase hex SHA-256 of a UTF-8 text with one
line per member file, `<file sha256 hex>  <relative path>\n` (two spaces), sorted by relative path
in byte order. For a directory path, the members are the archived files whose path starts with
`path + "/"`, each relative to that prefix. For a file path, the only member is the archived file at
exactly `path`, with its basename as the relative path. Files that packaging excludes, such as
build residue and anything under a `_`-prefixed directory of `packs/` or `profiles/`, never reach
`files[]` and so never change a digest.

**Checks.** `catalogue verify --archive` (and the staged check inside `catalogue package`) adds two
diagnostics:

- `CAT-V-ARC-018`: an entry's declared `digest` differs from the digest recomputed over `files[]`
  for its `path`. A `path` with no member file counts as different.
- `CAT-V-ARC-019`: the manifest has a malformed shape. Cases: the top level is not an object; a
  `files[]` item lacks a string `path` or `sha256`; `profiles` is present and not a list; a
  `packs[]` item lacks a string `name` or `version`; a `profiles[]` item is neither a string nor an
  object with a string `name`; an object item has a `path` or `digest` that is not a string; or an
  object item has a `digest` but no `path`. Verification stops after these errors, so no digest
  check reads a malformed entry.

An older manifest whose `packs[]` entries are `{name, version}` and whose `profiles` are name strings
or absent raises neither diagnostic.

**What the digests prove.** A unit digest shows that an entry agrees with the archive's own
`files[]`. It does not show who published the archive. The SHA-256 sidecar and the channel
descriptor remain the provenance evidence. `catalogue package --compare` uses the same rule, so
it derives every prior digest from the prior archive's verified `files[]` and ignores a digest the
prior manifest declares.

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
