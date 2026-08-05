# catalogue.toml reference

`catalogue.toml` sits at the root of any pack catalogue (the same directory that contains `packs/`).
It is the single file that makes a directory a recognised catalogue.

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
maintainers  = [{ name = "Alice", email = "alice@example.com" }]
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

Configures the Artifactory org bootstrap. When present and `enabled = true`, `agentbundle catalogue sync-defaults --write` bakes these coordinates into `_data/install-defaults.toml` so that developers who install your wheel resolve the catalogue from Artifactory automatically — no per-developer `config set source` step.

```toml
[distribution.agentbundle.artifactory]
enabled    = true
base-url   = "https://artifactory.example.com"
repository = "agentbundle-catalogues"
bundle     = "engineering"
channel    = "stable"
```

All five fields are required when `enabled = true`. No credentials go in this file — authenticate via [`AGENTBUNDLE_HTTP_BEARER_TOKEN`](../../guides/_shared/reference/agentbundle.md#environment-variables).

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Whether the Artifactory bootstrap is active. Set `false` to revert to the public catalogue. |
| `base-url` | string | Artifactory base URL (`https://` only; no embedded credentials). |
| `repository` | string | Artifactory repository name. Must match `[A-Za-z0-9._-]+`. |
| `bundle` | string | Catalogue bundle name. Must match `[A-Za-z0-9._-]+`. |
| `channel` | string | Channel name (e.g. `stable`, `preview`). Must match `[A-Za-z0-9._-]+`. |

See [Configure a catalogue for enterprise distribution](../../guides/_shared/how-to/configure-catalogue-enterprise-distribution.md) for the step-by-step setup guide.

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
name         = "acme-platform"
version      = "2.3.1"
description  = "ACME platform packs — security, compliance, and delivery tooling."
display-name = "ACME Platform Catalogue"
homepage     = "https://intranet.acme.example/dev/agentbundle"
maintainers  = [{ name = "Platform Engineering", email = "pe@acme.example" }]
keywords     = ["security", "compliance", "ci"]

[catalogue.channels]
stable  = "https://registry.acme.example/agentbundle/stable.json"

[catalogue.install-defaults]
packs    = ["core", "security-baseline"]
adapters = ["claude-code", "cursor"]

[catalogue.package]
include  = []                              # empty = all packs
required = ["LICENSE-APACHE", "LICENSE-MIT"]

[distribution.agentbundle.artifactory]
enabled    = false
base-url   = "https://artifactory.example.com"
repository = "agentbundle-catalogues"
bundle     = "acme-platform"
channel    = "stable"
```
