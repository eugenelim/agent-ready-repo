---
title: How to publish and use a protected enterprise catalogue
summary: Publish AgentBundle catalogues through any CI runner, ship non-secret organization defaults, and configure the four supported reader-authentication providers.
pack: _shared
kind: how-to
---

# How to publish and use a protected enterprise catalogue

**Use this when:** Your organization distributes the AgentBundle wheel through
an internal Python package repository and catalogues through a protected
Artifactory Generic repository.

**Result:** CI publishes a verified catalogue without storing credentials in
the repository. The wheel sends users to the approved catalogue channel. The
reader resolves credentials automatically through a four-provider chain.

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
| Read a protected catalogue | AgentBundle's HTTPS client via `credbroker.resolve_http_access` | The process that launches AgentBundle | Resolves in priority order: `AGENTBUNDLE_HTTP_BEARER_TOKEN`, a JFrog CLI 2.105.0+ profile, an exact-machine `.netrc` record, then anonymous. |

The provider order is fixed and the resolution stops as soon as one provider
is configured. When a configured provider is broken (wrong token, unsafe file
permissions, named profile absent), the resolution fails rather than falling
back to the next provider.

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

## 7. Configure catalogue read authentication

AgentBundle resolves the catalogue reader's credentials through a four-provider
chain, in this order:

1. **Bearer token** — set `AGENTBUNDLE_HTTP_BEARER_TOKEN` in the process
   environment. AgentBundle attaches it as `Authorization: Bearer <token>`.
   Provision, scope, rotate, and revoke this token through the organization
   credential service.

2. **JFrog CLI profile** — configure a JFrog CLI 2.105.0+ profile with
   `jf login` or `jf config add` targeting the same Artifactory instance.
   AgentBundle selects the profile whose Artifactory URL has the longest
   matching prefix for the catalogue URL; set `JFROG_CLI_SERVER_ID` to name
   a specific profile when multiple profiles exist. AgentBundle delegates the
   actual fetch to `jf api`, which uses the stored token from the profile.

3. **Machine-bound `.netrc` record** — add a line of the form
   `machine <host> login <user> password <token>` to the user `.netrc` file
   (`~/.netrc` on POSIX; `%USERPROFILE%\.netrc` on Windows). AgentBundle
   uses the `host` or `host:port` key that matches the catalogue origin.
   The `default` key is never used. The file must be readable only by its
   owner (mode `0600` on POSIX).

4. **Anonymous** — no credential is sent. This path succeeds only when the
   catalogue is publicly accessible.

The chain stops at the first available provider. When a provider is
configured but broken (a malformed bearer token, unsafe `.netrc` permissions, a
named JFrog profile that is missing), resolution fails immediately — it does not fall back. Fix the
broken configuration rather than removing it.

Users can then run:

```bash
agentbundle install --pack core
```

No extra credential injection step is needed when a JFrog CLI profile or
`.netrc` record is already in place.

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

The package client and AgentBundle use different credential paths. Check which
provider AgentBundle selected and whether the credential is valid:

- Bearer: confirm `AGENTBUNDLE_HTTP_BEARER_TOKEN` is set and the token has
  read access to the channel and release paths.
- JFrog CLI: confirm the profile URL matches the catalogue origin and the
  stored token has not expired. Run `jf config show --format=json` to inspect.
- `.netrc`: confirm the `machine` key matches the catalogue host (or
  `host:port` for non-standard ports) and the file is `0600`.
- Anonymous: if no provider is configured and the catalogue requires auth,
  configure one of the providers above.

Do not print credential values while troubleshooting.

### A configured credential source fails with an error

When a provider is configured but broken, AgentBundle stops the resolution and
reports the provider class and failure code — no credential material appears in
the message. Common codes: `invalid_bearer` (whitespace or a non-ASCII character in the
token), `netrc_unsafe`
(wrong file permissions), `jfrog_profile_mismatch` (named profile not found).
Fix the broken configuration; do not remove it and expect fallback to the next
provider.

### TLS verification fails behind the corporate network

For direct HTTPS fetches (bearer, .netrc, anonymous), set `AGENTBUNDLE_CA_BUNDLE`
to the approved PEM CA bundle path. For the JFrog CLI path on Linux, set
`SSL_CERT_FILE` or `SSL_CERT_DIR` instead — `AGENTBUNDLE_CA_BUNDLE` does not
reach the `jf api` subprocess. Keep certificate bundles separate from tokens.
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
