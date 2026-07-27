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

### `[catalogue.packaging]`

Controls archive output paths for `agentbundle catalogue package`.

```toml
[catalogue.packaging]
output-root = "dist/artifactory"
bundle      = "engineering"
release     = "1.0.0"
channel     = "stable"
```

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
```
