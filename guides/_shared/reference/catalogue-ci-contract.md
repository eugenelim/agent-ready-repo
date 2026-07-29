---
title: "Catalogue CI contract"
summary: "The provider-neutral validation, packaging, publication, and evidence contract for an AgentBundle catalogue CI pipeline."
pack: _shared
kind: reference
status: stable
---

# Catalogue CI contract

This page defines the portable contract any CI system can implement to validate,
package, and publish an AgentBundle catalogue. It names the commands, outputs,
exit codes, publication ordering, and responsibility boundaries — without
prescribing a CI provider or a specific workflow shape.

## Responsibility boundary

Three parties share responsibility for a catalogue CI pipeline. No party may
silently assume another's obligations.

| Party | Owns | Never does |
|---|---|---|
| **AgentBundle CLI** | Correct catalogue validation; deterministic archive + SHA256 sidecar; stable JSON output shapes; stable exit-code contract | Read secrets; issue network calls; control upload order; manage retention |
| **Organization CI** | Secrets and credential injection; HTTPS upload; publication serialization (ensuring one release lands at a time); rollback policy; artifact retention | Implement validation logic; bypass exit-code signals; skip the admission command |
| **Host Repository** | CI workflow files and trigger config; internal governance gates; tests proving the portable commands work in this repository | Alter the portable command signatures; branch AgentBundle's output format |

## CI lifecycle phases

### Phase 1 — Tool acquisition

The CI environment must have `agentbundle` available before any catalogue
command runs. Two patterns are equally valid:

**Externally managed.** The CI step installs agentbundle from a package registry:

```bash
pip install agentbundle
```

Pin the version for reproducibility:

```bash
pip install 'agentbundle==<version>'
```

**Vendored.** The organization pre-installs agentbundle into a shared CI image or
tool layer. The CI step runs catalogue commands without an explicit install.

Either way, confirm the tool is present:

```bash
agentbundle --version
```

### Phase 2 — Change validation

Every pipeline run that touches catalogue content must pass the admission
command before proceeding to packaging:

```bash
agentbundle catalogue verify --root . --format json
```

`--format json` writes a machine-readable result to stdout and exits 0 (clean)
or 1 (failures). The CI step fails on any non-zero exit, blocking packaging.

`catalogue lint` runs as an earlier, faster check against pack sources only. It
is optional but recommended as a pre-commit or fast-path gate:

```bash
agentbundle catalogue lint --root . --format json
```

### Phase 3 — Release packaging

After verify exits 0, package the release:

```bash
agentbundle catalogue package \
  --root . \
  --bundle  "$BUNDLE" \
  --release "$RELEASE" \
  --channel "$CHANNEL" \
  --output  "$OUTPUT"
```

The command writes three artifacts under `$OUTPUT`:

```
$OUTPUT/
  catalogues/
    $BUNDLE/
      releases/
        $RELEASE/
          catalogue-$RELEASE.tar.gz       ← immutable archive
          catalogue-$RELEASE.tar.gz.sha256 ← SHA256 sidecar
      channels/
        $CHANNEL.json                      ← mutable channel descriptor
```

The archive is deterministic given the same source content. The SHA256 sidecar
is computed over the archive and stored alongside it. The channel descriptor is a
small JSON file that records which release the channel currently points to; it is
the live pointer consumers use to resolve the latest version.

Re-run `agentbundle catalogue verify --archive <path>.tar.gz` after packaging to
confirm the archive is valid before uploading it.

### Phase 4 — Publication

Upload artifacts in this exact order:

1. The archive (`.tar.gz`)
2. The SHA256 sidecar (`.sha256`)
3. The channel descriptor (`channels/<channel>.json`) — **upload last**

The channel descriptor is the live pointer. Writing it last minimises the window
during which the descriptor references an archive that has not yet landed in the
target store. A consumer that resolves the channel between steps 2 and 3 finds no
channel pointer and fails cleanly; a consumer that resolves after step 3 finds the
archive already present.

Publication serialization — preventing two concurrent releases from interleaving
their uploads — is the CI system's responsibility.

### Phase 5 — Post-publication verification

After the channel descriptor is published, download the archive and sidecar from
the publication store and verify them locally:

```bash
# Download from the store first (provider-specific step)
# Then verify the local copies:
agentbundle catalogue verify \
  --archive "/path/to/downloaded/catalogue-$RELEASE.tar.gz" \
  --sha256-file "/path/to/downloaded/catalogue-$RELEASE.tar.gz.sha256"
```

`--archive` accepts a local filesystem path only; pass the path to the downloaded
archive. This confirms the archive round-trips through the publication store
without corruption.

Optionally, smoke-test pack installation from the published catalogue to confirm
consumer-side resolution.

### Phase 6 — Evidence retention

The CI system is responsible for retaining the evidence needed for rollback,
audit, and incident response. Minimum retention artifacts:

- The archive and SHA256 sidecar for every published release
- The JSON output of `catalogue verify --format json` from Phase 2
- The JSON output of `catalogue verify --archive ...` from Phase 5

Retention period and storage location are Organization CI policy, not
AgentBundle's.

## Exit codes

All `agentbundle catalogue` commands follow the same convention:

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Validation or operational failure (errors in the catalogue, archive mismatch, internal error) |
| `2` | CLI usage error (missing required flag, unknown option) |

These codes are stable. A CI step that treats any non-zero exit as a failure
gets the correct behaviour.

## Secrets and network calls

`agentbundle catalogue lint`, `agentbundle catalogue verify`, and
`agentbundle catalogue package` do not read secrets and do not issue network
calls. They operate entirely on the local filesystem.

TLS certificate verification, bearer-token injection, proxy configuration, and
upload credentials are exclusively Organization CI responsibilities. The
`AGENTBUNDLE_HTTP_BEARER_TOKEN`, `AGENTBUNDLE_CA_BUNDLE`, and `HTTPS_PROXY`
environment variables control AgentBundle's behaviour when resolving a remote
catalogue source (used by install and upgrade verbs, not by the catalogue
pipeline commands above).

## Command reference

### `agentbundle catalogue lint`

```
agentbundle catalogue lint [--root ROOT] [--pack PACK] [--format {table,json}] [--deep]
```

Validates pack sources against contracts without building. Exits 0 when all
checks pass, 1 on any error.

`--format json` writes to stdout:

```json
{
  "schema_version": "1",
  "command": "catalogue lint",
  "operation": "lint",
  "agentbundle_version": "<version>",
  "catalogue_schema_version": "<version>",
  "ok": true,
  "diagnostics": []
}
```

Human-readable output (table format) goes to stderr and is absent when
`--format json` is used.

### `agentbundle catalogue verify`

```
agentbundle catalogue verify [--root ROOT] [--pack PACK]
                             [--archive ARCHIVE] [--sha256-file SHA256_FILE]
                             [--format {table,json}]
```

Runs the full source pipeline (source mode) or validates an archive against its
SHA256 sidecar and checks the extracted layout (archive mode).
Exits 0 on clean, 1 on any failure.

`--format json` writes the same JSON shape as `catalogue lint` to stdout.

### `agentbundle catalogue package`

```
agentbundle catalogue package --bundle BUNDLE --release RELEASE
                               --channel CHANNEL --output OUTPUT
                               [--root ROOT]
                               [--source-revision SOURCE_REVISION]
                               [--minimum-agentbundle-version VERSION]
                               [--published-at DATETIME]
```

Required flags: `--bundle`, `--release`, `--channel`, `--output`.
Optional: `--root` (defaults to `.`), `--source-revision`, `--minimum-agentbundle-version`,
`--published-at`.

`catalogue package` does not support `--format json`; its result is the output
directory layout described in [Phase 3](#phase-3--release-packaging). Exits 0
on success, 1 on failure, 2 on missing required flags.

## See also

- [`agentbundle` reference](agentbundle.md) — install the CLI, install a pack,
  configure the default adapter, source-resolution chain, environment variables.
- [Catalogue format](../../_reference/catalogue-format.md) — what makes a
  directory a valid catalogue, schema contracts, and validation.
