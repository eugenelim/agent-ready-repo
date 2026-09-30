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

## Account for current reader authentication

Organization defaults select the protected catalogue URL. They do not
authenticate it.

AgentBundle's HTTPS client currently reads only
`AGENTBUNDLE_HTTP_BEARER_TOKEN`. It does not reuse a JFrog CLI profile, Pip or
uv authentication, `.netrc`, a keyring, browser SSO state, or `credbroker`.

The lowest-friction supported path is an organization-managed shell, launcher,
or endpoint policy that injects the Artifactory-issued read token into the
AgentBundle process. This is a workaround and a second credential surface, not
transparent reuse. A runtime change to reuse provider-native credentials needs
separate authorization and security review.

## Troubleshoot without exposing secrets

- **Wrong source:** `agentbundle config get source` shows whether a user source
  overrides the organization bootstrap. Use `agentbundle config unset source`
  only when the organization default should take over.
- **401 or 403:** confirm that the read identity can fetch both the channel
  descriptor and its referenced release objects. Do not print its token.
- **TLS failure:** configure `AGENTBUNDLE_CA_BUNDLE` with the approved PEM CA
  bundle path. Do not disable certificate verification.
- **Proxy failure:** configure `HTTPS_PROXY` and `NO_PROXY` through the managed
  environment. Keep proxy credentials out of repository files and transcripts.
- **Expired credentials:** rotate the publisher or reader identity through the
  owning secret platform. Do not paste values into CI output or issue reports.

## Disconnected hosts

A fully disconnected host must receive a local archive through the approved
transfer path. See [Flow E — fully disconnected host](flow-e-disconnected.md).
`AGENTBUNDLE_NO_REMOTE=1` disables remote default discovery; it does not make a
protected Artifactory source available offline.
