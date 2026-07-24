# How to publish a catalogue to Artifactory

**Use this when:** You are a CI operator or pack maintainer who owns an org Artifactory fork and wants to publish a new AgentBundle catalogue release so developers at your organisation can install or upgrade packs from it.
**Prerequisites:** JFrog CLI (`jf`) v2 on your PATH configured with a server ID; an Artifactory generic repository set up via [spec/organization-artifactory-bootstrap](../../../specs/organization-artifactory-bootstrap/spec.md); and `agentbundle package-catalogue` available (this command ships with spec/package-catalogue-command — ini-004 M5a; the guide documents the intended workflow regardless of whether that command is implemented yet).
**Result:** An immutable release archive, its SHA-256 checksum sidecar, and a mutable channel descriptor JSON are published to Artifactory in the correct order, so that every client following the channel can immediately install the new release without encountering a missing archive.

Publishing a catalogue requires uploading three files in a strict order. The channel descriptor JSON — the mutable pointer that tells clients which release is current — must be uploaded **last**, after the immutable release archive has been uploaded and confirmed reachable at its target URL.

> **Warning — ordering matters.** If you upload the channel descriptor JSON before the archive is available, every client that fetches the descriptor during that window will attempt to download a missing or corrupt archive and receive a 404. This window can last from seconds to minutes. The five-step sequence below eliminates this window: the channel JSON is written only after the archive is confirmed reachable and intact.

## Prerequisites

- JFrog CLI v2 (`jf`) on your PATH, with a server ID configured (`jf config add`).
- An Artifactory generic repository, set up via [spec/organization-artifactory-bootstrap](../../../specs/organization-artifactory-bootstrap/spec.md).
- `agentbundle package-catalogue` on your PATH. This command ships with spec/package-catalogue-command (ini-004 M5a); the guide documents the intended workflow regardless of whether that command is implemented yet.
- Credentials stored as CI/CD environment secrets (see [Credentials](#credentials)); never as literal values.

## Steps

1. **Package the catalogue locally.**

   Run `agentbundle package-catalogue` to produce the three output files in `dist/artifactory/`. The channel descriptor JSON is written locally at this step but is **not yet uploaded**.

   ```bash
   agentbundle package-catalogue \
     --root <catalogue-root> \
     --bundle <bundle> \
     --release <release> \
     --channel <channel> \
     --output dist/artifactory
   ```

   Output layout under `dist/artifactory/`:

   ```
   dist/artifactory/
   └── catalogues/
       └── <bundle>/
           ├── releases/
           │   └── <release>/
           │       ├── catalogue-<release>.tar.gz
           │       └── catalogue-<release>.tar.gz.sha256
           └── channels/
               └── <channel>.json
   ```

   The three output files are:

   - `catalogue-<release>.tar.gz` — the immutable release archive
   - `catalogue-<release>.tar.gz.sha256` — the SHA-256 checksum sidecar
   - `<channel>.json` — the mutable channel descriptor (uploaded in step 5)

2. **Upload the immutable release archive.**

   ```bash
   jf rt u \
     "dist/artifactory/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz" \
     "<repository>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz" \
     --server-id <server-id>
   ```

   This file is immutable once published. Configure your Artifactory repository to refuse overwrites on the `releases/` path prefix to enforce immutability.

3. **Upload the SHA-256 checksum sidecar.**

   ```bash
   jf rt u \
     "dist/artifactory/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz.sha256" \
     "<repository>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz.sha256" \
     --server-id <server-id>
   ```

4. **Verify the upload.**

   Download the archive from Artifactory and compare its SHA-256 against the local sidecar. If this check fails, **stop here** — do not proceed to step 5.

   ```bash
   jf rt dl \
     "<repository>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz" \
     dist/artifactory/verify/ \
     --server-id <server-id>

   sha256sum --check \
     "dist/artifactory/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz.sha256"
   ```

   This step confirms the archive is actually retrievable and intact at its target URL — not merely that Artifactory accepted the upload. Aborting here ensures the channel descriptor is never updated to point to an unavailable archive.

5. **Upload the channel descriptor JSON last.**

   Only after step 4 passes, upload the channel descriptor. The channel descriptor is uploaded last because the mutable pointer must not be replaced until the immutable archive is confirmed reachable at its target URL. Inverting steps 4 and 5 would leave a window in which clients fetch a descriptor pointing to a missing or not yet available archive.

   ```bash
   jf rt u \
     "dist/artifactory/catalogues/<bundle>/channels/<channel>.json" \
     "<repository>/catalogues/<bundle>/channels/<channel>.json" \
     --server-id <server-id>
   ```

   Uploading this file is the atomic act that makes the new release "current" for all clients following the channel.

## Credentials

All Artifactory upload credentials must be supplied as environment secrets — `${{ secrets.JFROG_ACCESS_TOKEN }}` in GitHub Actions, or the equivalent in your CI/CD platform. Never include a literal token, password, or API key in workflow YAML or guide prose.

Configure the JFrog CLI server ID using the secret at workflow runtime:

```bash
jf config add <server-id> \
  --url https://artifactory.example.test \
  --access-token "${JFROG_ACCESS_TOKEN}" \
  --interactive=false
```

Passing credentials via `jf config add` rather than `--access-token` flags on individual upload commands keeps secrets out of process lists and shell history.

## What Artifactory does (and doesn't do)

Artifactory stores and serves the release archive (`catalogue-<release>.tar.gz`) and channel descriptor (`<channel>.json`) unchanged. It does **not** parse, validate, or interpret AgentBundle's pack layout — the `packs/`, `profiles/`, and `docs/contracts/` hierarchy inside the archive is opaque to Artifactory. Pack layout validation is the responsibility of `agentbundle package-catalogue` (step 1) and the consuming `agentbundle install` command on the developer's machine.

## GitHub Actions workflow template

The fenced block below is a **template**. Copy it to `.github/workflows/publish-catalogue.yml` in your org fork, substitute every `<placeholder>` value for your environment, and verify the JFrog CLI command syntax against your installed version before use.

```yaml
# TEMPLATE: requires configuration before use — substitute all <placeholder> values.
# Copy to .github/workflows/publish-catalogue.yml in your org fork.
# Verify JFrog CLI syntax against your installed version before use.
name: Publish catalogue to Artifactory

on:
  workflow_dispatch:
    inputs:
      bundle:
        description: Bundle name (e.g. my-bundle)
        required: true
      release:
        description: Release version (e.g. 1.2.3)
        required: true
      channel:
        description: Channel name (e.g. stable)
        required: true

jobs:
  publish:
    runs-on: ubuntu-latest
    env:
      BUNDLE: ${{ github.event.inputs.bundle }}
      RELEASE: ${{ github.event.inputs.release }}
      CHANNEL: ${{ github.event.inputs.channel }}
      REPO: <your-artifactory-repository>
    steps:
      - uses: actions/checkout@v4

      - name: Set up JFrog CLI
        uses: jfrog/setup-jfrog-cli@v4

      - name: Configure JFrog CLI server
        env:
          JFROG_ACCESS_TOKEN: ${{ secrets.JFROG_ACCESS_TOKEN }}
        run: |
          jf config add prod-artifactory \
            --url https://artifactory.example.test \
            --access-token "${JFROG_ACCESS_TOKEN}" \
            --interactive=false

      - name: Package catalogue
        run: |
          agentbundle package-catalogue --root . --bundle "${BUNDLE}" --release "${RELEASE}" --channel "${CHANNEL}" --output dist/artifactory

      - name: Upload release archive
        run: |
          jf rt u "dist/artifactory/catalogues/${BUNDLE}/releases/${RELEASE}/catalogue-${RELEASE}.tar.gz" "${REPO}/catalogues/${BUNDLE}/releases/${RELEASE}/catalogue-${RELEASE}.tar.gz" --server-id prod-artifactory

      - name: Upload checksum sidecar
        run: |
          jf rt u "dist/artifactory/catalogues/${BUNDLE}/releases/${RELEASE}/catalogue-${RELEASE}.tar.gz.sha256" "${REPO}/catalogues/${BUNDLE}/releases/${RELEASE}/catalogue-${RELEASE}.tar.gz.sha256" --server-id prod-artifactory

      - name: Verify upload
        run: |
          jf rt dl "${REPO}/catalogues/${BUNDLE}/releases/${RELEASE}/catalogue-${RELEASE}.tar.gz" dist/artifactory/verify/ --server-id prod-artifactory
          sha256sum --check "dist/artifactory/catalogues/${BUNDLE}/releases/${RELEASE}/catalogue-${RELEASE}.tar.gz.sha256"

      - name: Upload channel descriptor (last)
        run: |
          jf rt u "dist/artifactory/catalogues/${BUNDLE}/channels/${CHANNEL}.json" "${REPO}/catalogues/${BUNDLE}/channels/${CHANNEL}.json" --server-id prod-artifactory
```

## Related

- [`agentbundle package-catalogue`](../reference/agentbundle.md) — the producer of the three output files uploaded by this workflow. Ships with spec/package-catalogue-command (ini-004 M5a). Run `agentbundle package-catalogue --help` for the full flag reference.
- [HTTPS Catalogue Channels spec](../../../specs/https-catalogue-channels/spec.md) (`spec/https-catalogue-channels`) — defines the channel descriptor JSON schema and the URL structure clients use to fetch the active release for a channel.
- [How to set up an org Artifactory fork](../../../specs/organization-artifactory-bootstrap/spec.md) (`spec/organization-artifactory-bootstrap`) — the prerequisite org-level bootstrap that provisions the Artifactory repository this guide targets.
