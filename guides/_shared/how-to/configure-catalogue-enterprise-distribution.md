---
title: How to publish and use a protected enterprise catalogue
summary: Publish AgentBundle catalogues through any CI runner, ship non-secret organization defaults, and account for the current reader-authentication limit.
pack: _shared
kind: how-to
---

# How to publish and use a protected enterprise catalogue

**Use this when:** Your organization distributes the AgentBundle wheel through
an internal Python package repository and catalogues through a protected
Artifactory Generic repository.

**Result:** CI publishes a verified catalogue without storing credentials in
the repository. The wheel sends users to the approved catalogue channel. The
reader setup also reflects an important limit: AgentBundle does not yet reuse
an existing JFrog CLI, Pip, uv, keyring, or browser login.

The sequence below first records the non-secret coordinates, then generates
organization defaults from them. Do not generate or publish defaults before
the Artifactory block is correct.

## Keep the three credential paths separate

The wheel, the catalogue publisher, and the catalogue reader are separate
clients. A login for one does not authenticate the others.

| Flow | Client | Credential owner | Current behavior |
| --- | --- | --- | --- |
| Install the `agentbundle` wheel | Pip, uv, Poetry, or another Python package client | The package client and its organization-managed configuration | May reuse that client's existing `.netrc`, keyring, or login support. AgentBundle does not read these credentials. |
| Publish a catalogue | JFrog CLI or another upload client in a protected CI job | The organization's CI or secrets platform | Use a restricted service identity or CI-issued OIDC token. Use a username only when the upload client requires one. |
| Read a protected catalogue | AgentBundle's HTTPS client | The process that launches AgentBundle | Reads only `AGENTBUNDLE_HTTP_BEARER_TOKEN`. It does not reuse JFrog CLI profiles, Pip or uv credentials, `.netrc`, keyrings, or browser SSO state. |

The environment variable carries an Artifactory-issued access token. It is not
an AgentBundle-specific token format. It is still a second credential injection
surface, so protected catalogue access is not transparent today.

## 1. Provision the repositories and identities

Create two Artifactory repositories unless your approved topology provides the
same separation another way:

- A PyPI repository for the `agentbundle` wheel. Your Python package client
  owns authentication to this repository.
- A Generic repository for catalogue archives, SHA256 sidecars, and channel
  descriptors.

Give the catalogue publisher write access only to the required Generic
repository paths. Give a separate read identity access to the published channel
and release paths. Prefer a restricted service identity or CI OIDC exchange over
an individual developer token.

Set the release paths to immutable. Allow controlled replacement only for
`channels/`, because a channel descriptor is the mutable pointer to the current
release.

## 2. Commit only non-secret catalogue coordinates

Add the Generic repository coordinates to `catalogue.toml`:

```toml
[distribution.agentbundle.artifactory]
enabled    = true
base-url   = "https://artifactory.example.test/artifactory"
repository = "agentbundle-catalogues"
bundle     = "platform"
channel    = "stable"
```

All five fields are required when `enabled = true`. `base-url` must use HTTPS
and must not contain user information or a query string. `repository`, `bundle`,
and `channel` must match `[A-Za-z0-9._-]+`.

Do not add a password, token, authenticated URL, or secret lookup instruction
to `catalogue.toml`. The schema closes this table to the five fields above.

## 3. Generate and ship organization defaults

Run:

```bash
agentbundle catalogue sync-defaults --root . --write
agentbundle catalogue sync-defaults --root . --check
```

Commit the generated `install-defaults.toml` with `catalogue.toml`, then build
and publish the organization wheel. The generated file contains only the same
non-secret coordinates.

When the wheel is installed, AgentBundle constructs this source:

```text
catalogue+<base-url>/<repository>/catalogues/<bundle>/channels/<channel>.json
```

This removes per-machine catalogue URL setup. It does not configure catalogue
credentials.

## 4. Build and verify without publication credentials

Install the wheel in the build job using your Python package client's approved
authentication path. Do not reuse catalogue upload credentials for package
installation.

The build job needs no Artifactory publication secret:

```bash
agentbundle catalogue sync-defaults --root . --check
agentbundle catalogue verify --root . --format json
agentbundle catalogue package \
  --root . \
  --bundle "$BUNDLE" \
  --release "$RELEASE" \
  --channel "$CHANNEL" \
  --output "$OUTPUT"
agentbundle catalogue verify \
  --archive "$OUTPUT/catalogues/$BUNDLE/releases/$RELEASE/catalogue-$RELEASE.tar.gz" \
  --sha256-file "$OUTPUT/catalogues/$BUNDLE/releases/$RELEASE/catalogue-$RELEASE.tar.gz.sha256"
```

Preserve the verification JSON and packaged output as protected CI artifacts for
the upload job.

## 5. Inject publisher credentials only in the upload job

Run publication only from an approved release tag or equivalent protected
release event. Serialize the job so two releases cannot update the same channel
at once.

Map the portable controls to your CI provider:

| Control | GitHub Actions example | GitLab CI example | Jenkins or another runner |
| --- | --- | --- | --- |
| Publisher secret | Environment or organization Actions secret | Protected, masked, and hidden CI/CD variable | Credential binding from the controller or external secret store |
| Non-secret coordinates | Actions variables | CI/CD variables | Job parameters or managed configuration |
| Release gate | Protected environment and release tag | Protected release tag | Restricted release job |
| Serialization | `concurrency` group | `resource_group` | Deployment lock or equivalent |

GitHub Actions and GitLab CI are examples, not requirements. The portable
contract is the control set in the table.

Configure the upload client inside the protected job. JFrog CLI supports a
restricted access token or an organization-configured OIDC exchange for
automation. Keep secret values out of commands that print their arguments,
workflow logs, artifacts, and receipts.

Upload in this order:

1. `catalogue-<release>.tar.gz`
2. `catalogue-<release>.tar.gz.sha256`
3. `channels/<channel>.json`

Upload the channel descriptor last. It makes the release visible to readers.

The repository's `publish-catalogue.yml` is one GitHub-hosted implementation
example. It is not the downstream contract.

## 6. Verify with a read identity and keep a safe receipt

After the channel descriptor lands, use a read-only identity to download the
archive and sidecar from Artifactory. Verify the downloaded files locally:

```bash
agentbundle catalogue verify \
  --archive "/path/to/downloaded/catalogue-$RELEASE.tar.gz" \
  --sha256-file "/path/to/downloaded/catalogue-$RELEASE.tar.gz.sha256"
```

Record a credential-free receipt containing the source revision, release and
channel names, artifact paths, archive digest, CI run reference, and verification
result. Do not record a token, username, authenticated URL, or secret-store
location.

## 7. Provide catalogue read authentication honestly

JFrog's interactive `jf login` flow can complete SSO, SAML, OAuth, or MFA and
store reusable access and refresh tokens in a JFrog CLI profile. Later
`jf rt download` commands reuse that profile. AgentBundle does not call JFrog
CLI or read its profile.

Pip and uv also have reusable authentication paths for the wheel install. Those
credentials belong to the package client and are not exposed to AgentBundle's
separate HTTPS implementation.

For a protected catalogue, the lowest-friction supported approach today is an
organization-managed shell, developer launcher, or endpoint policy that injects
`AGENTBUNDLE_HTTP_BEARER_TOKEN` into the AgentBundle process. Users can then run:

```bash
agentbundle install --pack core
```

Treat this as a managed workaround, not native credential reuse. The
organization must provision, scope, rotate, and revoke the Artifactory read
token. A user who is already signed in through JFrog CLI, Pip, uv, a keyring, or
browser SSO still needs this extra integration.

Transparent reuse requires a separately authorized runtime design change. The
current setup guide does not select or design that credential resolver.

## Troubleshooting

### AgentBundle uses the wrong catalogue

An explicit catalogue argument wins first. A user-set `[settings].source` wins
next and overrides the organization Artifactory bootstrap.

```bash
agentbundle config get source
agentbundle config unset source
```

Unset the user source only when the organization default should take over.

### The wheel installs but the catalogue returns 401 or 403

The package client and AgentBundle use different credential paths. Confirm that
the managed launcher injected a current read token and that the identity can read
both the channel descriptor and referenced release objects. Do not print the
value while checking.

### An existing JFrog or package-client login is ignored

That is current behavior. AgentBundle does not reuse JFrog CLI profiles, Pip or
uv authentication, `.netrc`, keyrings, or an SSO browser session for catalogue
retrieval.

### TLS verification fails behind the corporate network

Set `AGENTBUNDLE_CA_BUNDLE` to the approved PEM CA bundle path when the platform
trust store is not enough. Keep the certificate bundle separate from tokens.
AgentBundle keeps HTTPS and certificate verification enabled.

### Requests do not reach Artifactory

Set the standard `HTTPS_PROXY` and `NO_PROXY` variables through the managed
environment. Check whether the Artifactory host should use the proxy or bypass
it. Do not place proxy credentials in documentation or committed configuration.

### The token expired

Have the organization credential service or support process refresh the managed
read token. Do not ask users to paste tokens into issue reports, shell history,
or troubleshooting transcripts.

## Offline and air-gapped use

For a host that cannot reach Artifactory, pass a local catalogue explicitly and
disable remote default discovery:

```bash
AGENTBUNDLE_NO_REMOTE=1 agentbundle install --pack core /path/to/local-catalogue
```

This skips the organization Artifactory bootstrap and editable-install
detection. It does not turn a protected remote catalogue into an offline source.

## See also

- [`agentbundle` reference — source resolution and authentication](../reference/agentbundle.md#catalogue-source-resolution)
- [Catalogue CI contract](../reference/catalogue-ci-contract.md) — portable build, publication, verification, and evidence responsibilities
- [JFrog login](https://docs.jfrog.com/integrations/docs/jf-login) — JFrog CLI's interactive login and reusable profile
- [Configure JFrog CLI](https://docs.jfrog.com/integrations/docs/configuring-the-cli) — supported interactive and automation configuration
- [Artifactory Generic repositories](https://docs.jfrog.com/artifactory/docs/generic-files) — storage used for catalogue archives and channel descriptors
- [Artifactory PyPI repositories](https://docs.jfrog.com/artifactory/docs/pypi-repositories) — storage used for the AgentBundle wheel
- [Pip authentication](https://pip.pypa.io/en/stable/topics/authentication/) — package-client credential paths that remain separate from catalogue retrieval
