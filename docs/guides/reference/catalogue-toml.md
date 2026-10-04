# catalogue.toml reference

`catalogue.toml` sits at the root of any source catalogue. Together with a
literal root `packs/` directory, it identifies that directory as a catalogue;
neither marker is sufficient by itself.

## Required fields

```toml
[catalogue]
name = "my-catalogue"          # slug — kebab-case, globally unique within your org
version = "0.1.0"              # SemVer; bump on every published change
description = "One sentence."  # shown in agentbundle show output
```

## Optional fields

```toml
[catalogue]
display-name = "My Catalogue"        # human-readable name for UIs
homepage     = "https://example.com" # project home page URL
maintainers  = [{ name = "Platform Team", email = "platform@example.test" }]
keywords     = ["security", "platform"]
```

### `[catalogue.channels]`

Declares the publish channels this catalogue supports.

```toml
[catalogue.channels]
stable  = "https://registry.example.com/catalogues/my-catalogue/stable.json"
preview = "https://registry.example.com/catalogues/my-catalogue/preview.json"
```

Channel names are arbitrary strings. `stable` is conventional for the production channel.

### `[catalogue.install-defaults]`

Controls which packs are installed by default when an adopter runs `agentbundle install`.

```toml
[catalogue.install-defaults]
packs    = ["core", "governance-extras"]
adapters = ["claude-code"]
```

Run `agentbundle catalogue sync-defaults --root .` to sync these values into the self-hosted adapters'
install manifests.

### `[catalogue.package]`

Controls which packs are included in a packaged archive.

```toml
[catalogue.package]
include  = []                              # default: all packs
required = ["LICENSE-APACHE", "LICENSE-MIT"]
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `include` | array of strings | `[]` (all packs) | Pack paths to include in a packaged archive. An empty list includes all packs. |
| `required` | array of strings | `["LICENSE-APACHE", "LICENSE-MIT"]` | Required root-level file paths. Overrides the default `LICENSE-APACHE` / `LICENSE-MIT` constraint when set. Absent or empty means use the default requirement. |

### `[distribution.agentbundle]`

Top-level options for the `agentbundle` distribution channel.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `install-defaults-output` | string | required | Repo-relative path where `agentbundle catalogue sync-defaults --write` writes the baked defaults TOML. |
| `preferred-adapter` | string | — | Adapter name used for `agentbundle catalogue self-host`. When set to an adapter **not** in the upstream `SELF_HOST_ADAPTERS` list (e.g. `"kiro-ide"`), only that adapter's folder is projected and Claude-specific root files (`CLAUDE.md`, `.claude-plugin/marketplace.json`) are omitted. When absent or set to an adapter already in `SELF_HOST_ADAPTERS`, the default set (claude-code + codex) is used. |
| `default-source` | string | — | Default catalogue source URL baked into the wheel's `install-defaults.toml`. |

### `[distribution.agentbundle.artifactory]`

Configures the Artifactory org bootstrap. When present and `enabled = true`, `agentbundle catalogue sync-defaults --write` bakes these coordinates into `_data/install-defaults.toml` so that developers who install your wheel resolve the catalogue URL from Artifactory automatically — no per-developer `config set source` step. Authentication remains separate, as described below.

```toml
[distribution.agentbundle.artifactory]
enabled    = true
base-url   = "https://artifactory.example.test/artifactory"
repository = "agentbundle-catalogues"
bundle     = "platform"
channel    = "stable"
```

All five fields are required when `enabled = true`. This table contains only
distribution coordinates. The schema rejects unknown fields, and the URL
validator rejects user information and credential query parameters.

No credentials go in this file or the generated defaults. AgentBundle's HTTPS
catalogue client resolves credentials through a four-provider chain: bearer
token (`AGENTBUNDLE_HTTP_BEARER_TOKEN`), JFrog CLI 2.105.0+ profile,
exact-machine `.netrc` record, then anonymous. The Pip, uv, keyring, and
browser-login credentials used to install the wheel are separate and are not
available to the catalogue client.
See the [public setup guide](../../../guides/_shared/how-to/configure-catalogue-enterprise-distribution.md#keep-the-three-credential-paths-separate).

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Whether the Artifactory bootstrap is active. Set `false` to revert to the public catalogue. |
| `base-url` | string | Artifactory base URL (`https://` only; no embedded credentials). |
| `repository` | string | Artifactory repository name. Must match `[A-Za-z0-9._-]+`. |
| `bundle` | string | Catalogue bundle name. Must match `[A-Za-z0-9._-]+`. |
| `channel` | string | Channel name (e.g. `stable`, `preview`). Must match `[A-Za-z0-9._-]+`. |

See [Publish and use a protected enterprise catalogue](../../../guides/_shared/how-to/configure-catalogue-enterprise-distribution.md) for the step-by-step setup guide.

## Valid values

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | kebab-case, 1–64 chars |
| `version` | string | SemVer (`MAJOR.MINOR.PATCH`) |
| `description` | string | ≤ 280 chars recommended |
| `display-name` | string | free text |
| `homepage` | string | valid URL |
| `maintainers[].name` | string | required when maintainer present |
| `maintainers[].email` | string | optional |
| `keywords` | array of strings | free text |
| `catalogue.package.include` | array of strings | pack paths; empty = all packs |
| `catalogue.package.required` | array of strings | root-level file paths; absent = `["LICENSE-APACHE", "LICENSE-MIT"]` |
| `distribution.agentbundle.preferred-adapter` | string | any valid adapter name (`"claude-code"`, `"kiro-ide"`, `"kiro-cli"`, `"codex"`, …) |
| `distribution.agentbundle.artifactory.enabled` | boolean | `true` or `false` |
| `distribution.agentbundle.artifactory.base-url` | string | `https://` only, no credentials |
| `distribution.agentbundle.artifactory.repository` | string | `[A-Za-z0-9._-]+` |
| `distribution.agentbundle.artifactory.bundle` | string | `[A-Za-z0-9._-]+` |
| `distribution.agentbundle.artifactory.channel` | string | `[A-Za-z0-9._-]+` |

## Example

```toml
[catalogue]
name         = "internal-platform"
version      = "2.3.1"
description  = "Internal platform packs for security, compliance, and delivery."
display-name = "Internal Platform Catalogue"
homepage     = "https://intranet.example.test/agentbundle"
maintainers  = [{ name = "Platform Team", email = "platform@example.test" }]
keywords     = ["security", "compliance", "ci"]

[catalogue.channels]
stable  = "https://registry.example.test/agentbundle/stable.json"

[catalogue.install-defaults]
packs    = ["core", "security-baseline"]
adapters = ["claude-code", "cursor"]

[catalogue.package]
include  = []                              # empty = all packs
required = ["LICENSE-APACHE", "LICENSE-MIT"]

[distribution.agentbundle.artifactory]
enabled    = false
base-url   = "https://artifactory.example.test/artifactory"
repository = "agentbundle-catalogues"
bundle     = "internal-platform"
channel    = "stable"
```
