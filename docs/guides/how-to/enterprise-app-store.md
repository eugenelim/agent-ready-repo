# How to operate the repository's enterprise Artifactory release path

Use this maintainer guide to relate this repository's GitHub workflows to the
provider-neutral enterprise distribution contract. Downstream organizations
should start with the [public protected-catalogue guide](../../../guides/_shared/how-to/configure-catalogue-enterprise-distribution.md).

## Keep the two repositories and three identities distinct

The supported Artifactory topology uses:

- a PyPI repository for the AgentBundle wheel;
- a Generic repository for catalogue archives, sidecars, and channel
  descriptors.

The Python package client authenticates the wheel install. A restricted CI
publisher uploads the catalogue. A read-only identity verifies and consumes the
protected catalogue. These credentials are not interchangeable.

## Commit only distribution coordinates

The catalogue source may contain:

```toml
[distribution.agentbundle.artifactory]
enabled    = true
base-url   = "https://artifactory.example.test/artifactory"
repository = "agentbundle-catalogues"
bundle     = "platform"
channel    = "stable"
```

Run:

```bash
agentbundle catalogue sync-defaults --root . --write
agentbundle catalogue sync-defaults --root . --check
```

The generated defaults carry only those coordinates. Do not put credentials,
authenticated URLs, or secret-store instructions in either file.

## Build, verify, and package without publication secrets

```bash
agentbundle catalogue verify --root . --format json
agentbundle catalogue package \
  --root . \
  --bundle "$BUNDLE" \
  --release "$RELEASE" \
  --channel "$CHANNEL" \
  --output "$OUTPUT" \
  --source-revision "$SOURCE_REVISION"
agentbundle catalogue verify \
  --archive "$OUTPUT/catalogues/$BUNDLE/releases/$RELEASE/catalogue-$RELEASE.tar.gz" \
  --sha256-file "$OUTPUT/catalogues/$BUNDLE/releases/$RELEASE/catalogue-$RELEASE.tar.gz.sha256"
```

The output is:

```text
$OUTPUT/catalogues/$BUNDLE/
  releases/$RELEASE/
    catalogue-$RELEASE.tar.gz
    catalogue-$RELEASE.tar.gz.sha256
  channels/$CHANNEL.json
```

The build job requires no Artifactory publication credential. Preserve the
verification JSON and packaged directory as protected CI artifacts for the
upload job.

## Publish from a protected, serialized job

Inject a restricted publisher identity only into the upload job. Run that job
from a protected release tag or equivalent release event. Serialize updates to
each channel.

Upload in this order:

1. The immutable archive.
2. The immutable SHA256 sidecar.
3. The mutable channel descriptor.

The descriptor is the live pointer used by connected AgentBundle consumers. It
is not audit-only metadata.

After publishing the descriptor, use a read-only identity to download the
archive and sidecar. Run `agentbundle catalogue verify --archive ...` on the
downloaded files. Record only a credential-free receipt.

## Map the portable contract to CI providers

| Portable control | This repository's GitHub example | GitLab equivalent | Other runners |
| --- | --- | --- | --- |
| Publisher secret | Actions secret consumed by the upload job | Protected, masked, hidden CI/CD variable | Credential binding or external secret store |
| Release gate | Tag condition and protected environment | Protected release tag | Restricted release job |
| Serialization | Workflow `concurrency` | `resource_group` | Deployment lock |
| Upload client | JFrog CLI in `publish-catalogue.yml` | JFrog CLI or approved equivalent | JFrog CLI or approved equivalent |

The repository workflows are host-specific examples:

- `.github/workflows/release-agentbundle.yml` builds the Python distribution and
  uses Twine for this repository's Artifactory wheel publication path.
- `.github/workflows/publish-catalogue.yml` packages catalogue releases and uses
  JFrog CLI for Generic repository publication.

Do not copy their GitHub syntax as the portable contract. The public
[Catalogue CI contract](../../../guides/_shared/reference/catalogue-ci-contract.md)
owns the provider-neutral sequence and responsibility boundary.

## Reader authentication providers

Organization defaults select the protected catalogue URL. They do not
authenticate it.

AgentBundle resolves catalogue credentials through a four-provider chain via
`credbroker.resolve_http_access`. Providers are evaluated in priority order:
bearer token (`AGENTBUNDLE_HTTP_BEARER_TOKEN`), JFrog CLI 2.105.0+ profile,
exact-machine `.netrc` record, then anonymous. The chain stops at the first
available provider. When a configured provider is broken, resolution fails
immediately — no fallback to the next provider.

For the JFrog CLI path, AgentBundle delegates fetches to `jf api` —
`AGENTBUNDLE_CA_BUNDLE` does not reach the subprocess. On Linux, use
`SSL_CERT_FILE` or `SSL_CERT_DIR` to trust a private CA for `jf api`. On
macOS, add the corporate CA to the system keychain instead — `jf api` reads
only the system keychain there. `jf api` ignores `~/.jfrog/security/certs/`,
so a passing `jf rt ping` does not prove the catalogue fetch will succeed.

## Troubleshoot without exposing secrets

- **Wrong source:** `agentbundle config get source` shows whether a user source
  overrides the organization bootstrap. Use `agentbundle config unset source`
  only when the organization default should take over.
- **401 or 403:** check which provider AgentBundle selected. For bearer, confirm
  the token has read access to the channel and release paths. For JFrog CLI,
  run `jf config show --format=json` to confirm the profile matches the catalogue
  origin and the stored token has not expired; access failures on the JFrog CLI
  path surface as `jfrog_fetch_failed` rather than an HTTP status code. For
  `.netrc`, confirm the `machine` key matches the catalogue host and the file is
  mode `0600`. Do not print token values.
- **Configured-but-broken error:** a failure code such as `netrc_unsafe` or
  `jfrog_profile_mismatch` means a provider was detected but broken. Fix the
  broken configuration — the chain will not fall back past it.
- **TLS failure (direct path):** configure `AGENTBUNDLE_CA_BUNDLE` with the
  approved PEM CA bundle path. Do not disable certificate verification.
- **TLS failure (JFrog CLI path):** `AGENTBUNDLE_CA_BUNDLE` does not reach `jf
  api`; TLS failures there surface as `jfrog_fetch_failed`. On Linux, set
  `SSL_CERT_FILE` or `SSL_CERT_DIR` to trust a private CA. On macOS, add the
  corporate CA to the system keychain — `jf api` reads only the system keychain
  there.
- **Proxy failure:** configure `HTTPS_PROXY` and `NO_PROXY` through the managed
  environment. Keep proxy credentials out of repository files and transcripts.
- **Expired credentials:** rotate the publisher or reader identity through the
  owning secret platform. Do not paste values into CI output or issue reports.

## Disconnected hosts

A fully disconnected host must receive a local archive through the approved
transfer path. See [Flow E — fully disconnected host](flow-e-disconnected.md).
`AGENTBUNDLE_NO_REMOTE=1` disables remote default discovery; it does not make a
protected Artifactory source available offline.
