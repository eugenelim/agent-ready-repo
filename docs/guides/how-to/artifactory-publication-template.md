# Artifactory publication template

A safe, six-step sequence for publishing a packaged catalogue to Artifactory.
The channel descriptor (`channel.json`) is uploaded LAST — only after the
archive and sidecar are verified on the receiving end.

All values in this template use `example.test` as the Artifactory domain.
Substitute your real domain from CI secrets; never hard-code credentials or
production URLs in workflow YAML.

## Required secrets

| Secret name | Description |
|-------------|-------------|
| `ARTIFACTORY_URL` | Base URL of your Artifactory instance (e.g. `https://artifactory.example.test/artifactory`) |
| `ARTIFACTORY_USER` | Service account username |
| `ARTIFACTORY_TOKEN` | API token or password; never embed in YAML |
| `ARTIFACTORY_REPO` | Target repository name (e.g. `agentbundle-catalogues`) |

## Publication workflow

```yaml
name: publish-catalogue

on:
  workflow_dispatch:
    inputs:
      bundle:
        description: "Bundle identifier (e.g. engineering)"
        required: true
      release:
        description: "Release version (e.g. 1.0.0)"
        required: true
      channel:
        description: "Channel (e.g. stable)"
        required: true
        default: stable

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install agentbundle
        run: pip install -e packages/agentbundle

      # Step 1 — verify the source catalogue before packaging
      - name: Verify catalogue (source)
        run: agentbundle catalogue verify --root .

      # Step 2 — build the distributable archive + sidecar
      - name: Package catalogue
        run: |
          agentbundle catalogue package \
            --root . \
            --bundle "${{ github.event.inputs.bundle }}" \
            --release "${{ github.event.inputs.release }}" \
            --channel "${{ github.event.inputs.channel }}" \
            --output dist/artifactory \
            --source-revision "${{ github.sha }}"

      # Step 3 — upload archive to Artifactory
      - name: Upload archive
        env:
          ART_URL:   ${{ secrets.ARTIFACTORY_URL }}
          ART_USER:  ${{ secrets.ARTIFACTORY_USER }}
          ART_TOKEN: ${{ secrets.ARTIFACTORY_TOKEN }}
          ART_REPO:  ${{ secrets.ARTIFACTORY_REPO }}
          BUNDLE:    ${{ github.event.inputs.bundle }}
          RELEASE:   ${{ github.event.inputs.release }}
          CHANNEL:   ${{ github.event.inputs.channel }}
        run: |
          ARCHIVE="dist/artifactory/catalogues/${BUNDLE}/releases/${RELEASE}/${CHANNEL}/${BUNDLE}-${RELEASE}.tar.gz"
          TARGET="${ART_URL}/${ART_REPO}/catalogues/${BUNDLE}/releases/${RELEASE}/${CHANNEL}/${BUNDLE}-${RELEASE}.tar.gz"
          curl -fsS -u "${ART_USER}:${ART_TOKEN}" -T "$ARCHIVE" "$TARGET"

      # Step 4 — upload SHA-256 sidecar
      - name: Upload sidecar
        env:
          ART_URL:   ${{ secrets.ARTIFACTORY_URL }}
          ART_USER:  ${{ secrets.ARTIFACTORY_USER }}
          ART_TOKEN: ${{ secrets.ARTIFACTORY_TOKEN }}
          ART_REPO:  ${{ secrets.ARTIFACTORY_REPO }}
          BUNDLE:    ${{ github.event.inputs.bundle }}
          RELEASE:   ${{ github.event.inputs.release }}
          CHANNEL:   ${{ github.event.inputs.channel }}
        run: |
          SIDECAR="dist/artifactory/catalogues/${BUNDLE}/releases/${RELEASE}/${CHANNEL}/${BUNDLE}-${RELEASE}.tar.gz.sha256"
          TARGET="${ART_URL}/${ART_REPO}/catalogues/${BUNDLE}/releases/${RELEASE}/${CHANNEL}/${BUNDLE}-${RELEASE}.tar.gz.sha256"
          curl -fsS -u "${ART_USER}:${ART_TOKEN}" -T "$SIDECAR" "$TARGET"

      # Step 5 — download archive + sidecar back and verify integrity
      - name: Verify uploaded artifact
        env:
          ART_URL:   ${{ secrets.ARTIFACTORY_URL }}
          ART_USER:  ${{ secrets.ARTIFACTORY_USER }}
          ART_TOKEN: ${{ secrets.ARTIFACTORY_TOKEN }}
          ART_REPO:  ${{ secrets.ARTIFACTORY_REPO }}
          BUNDLE:    ${{ github.event.inputs.bundle }}
          RELEASE:   ${{ github.event.inputs.release }}
          CHANNEL:   ${{ github.event.inputs.channel }}
        run: |
          REMOTE_BASE="${ART_URL}/${ART_REPO}/catalogues/${BUNDLE}/releases/${RELEASE}/${CHANNEL}"
          curl -fsS -u "${ART_USER}:${ART_TOKEN}" \
            -o /tmp/verify.tar.gz "${REMOTE_BASE}/${BUNDLE}-${RELEASE}.tar.gz"
          curl -fsS -u "${ART_USER}:${ART_TOKEN}" \
            -o /tmp/verify.tar.gz.sha256 "${REMOTE_BASE}/${BUNDLE}-${RELEASE}.tar.gz.sha256"
          agentbundle catalogue verify \
            --archive /tmp/verify.tar.gz \
            --sha256-file /tmp/verify.tar.gz.sha256

      # Step 6 — upload channel descriptor LAST (only after archive is verified)
      - name: Upload channel descriptor
        env:
          ART_URL:   ${{ secrets.ARTIFACTORY_URL }}
          ART_USER:  ${{ secrets.ARTIFACTORY_USER }}
          ART_TOKEN: ${{ secrets.ARTIFACTORY_TOKEN }}
          ART_REPO:  ${{ secrets.ARTIFACTORY_REPO }}
          BUNDLE:    ${{ github.event.inputs.bundle }}
          RELEASE:   ${{ github.event.inputs.release }}
          CHANNEL:   ${{ github.event.inputs.channel }}
        run: |
          DESCRIPTOR="dist/artifactory/catalogues/${BUNDLE}/releases/${RELEASE}/${CHANNEL}/channel.json"
          TARGET="${ART_URL}/${ART_REPO}/catalogues/${BUNDLE}/releases/${RELEASE}/${CHANNEL}/channel.json"
          curl -fsS -u "${ART_USER}:${ART_TOKEN}" -T "$DESCRIPTOR" "$TARGET"
```

## Key invariants

- **Channel descriptor last.** Clients poll `channel.json` to discover new releases. Upload it only after the archive and sidecar are verified — never before. An early upload directs clients to an archive that hasn't passed integrity checks.
- **Credentials from secrets only.** Never embed `ARTIFACTORY_URL`, `ARTIFACTORY_USER`, or `ARTIFACTORY_TOKEN` directly in workflow YAML. Pass them through GitHub Actions secrets.
- **Verify before upload, verify after.** Step 1 verifies the source catalogue; Step 5 verifies the uploaded artifact. Both must pass. A failure at Step 5 means the upload was corrupted in transit — stop before uploading the channel descriptor.
- **No bearer tokens in generated files.** `agentbundle catalogue package` never embeds credentials in `channel.json` or the archive. The sidecar is a hash only.
