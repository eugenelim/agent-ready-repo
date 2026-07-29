# `contracts/`

Catalogue-level, machine-readable contract files. These are *not* per-feature
specs — they're the published interface this catalogue exposes to consumers
(APM, Claude Code plugins, the `agentbundle` CLI, future adopters).

**Authority model (RFC-0076 D1):** `contracts/` is the canonical authored source
for all contracts listed below. `packages/agentbundle/agentbundle/_data/` carries
byte-identical copies of every contract the CLI bundles; AGENTS.md and README
files carry concise operational guidance only. When these disagree, `contracts/`
is authoritative.

## Files

| File | What it pins | Governing spec or RFC |
| --- | --- | --- |
| `adapter.toml` | Per-IDE adapter contract: every (primitive × adapter) projection rule | [distribution-adapters](../specs/distribution-adapters/spec.md) |
| `adapter.schema.json` | JSON Schema for `adapter.toml`'s shape | [distribution-adapters](../specs/distribution-adapters/spec.md) (AC #1) |
| `pack.schema.json` | JSON Schema for per-pack `pack.toml` manifests | [distribution-adapters](../specs/distribution-adapters/spec.md) (AC #3) |
| `plugin-manifest.schema.json` | JSON Schema for `.claude-plugin/plugin.json` | [distribution-adapters](../specs/distribution-adapters/spec.md) (AC #4) |
| `plugin-manifest.derived.schema.json` | Derived schema for `.claude-plugin/plugin.json` after adapter-rule merge | [distribution-adapters](../specs/distribution-adapters/spec.md) |
| `catalogue.schema.json` | JSON Schema for `catalogue.toml` manifests | [RFC-0003](../rfc/0003-spec-and-cli.md) |
| `profile.schema.json` | JSON Schema for profile TOML files | [RFC-0003](../rfc/0003-spec-and-cli.md) |
| `guide.schema.json` | JSON Schema for guide frontmatter | [agentskills.io standard](../guides/_shared/reference/agentskills-io-standard.md) |
| `skill.schema.json` | JSON Schema for skill frontmatter and body | [agentskills.io standard](../guides/_shared/reference/agentskills-io-standard.md) |
| `skill-manifest.schema.json` | JSON Schema for skill manifest files | [agentskills.io standard](../guides/_shared/reference/agentskills-io-standard.md) |
| `target-vocab.toml` | Vocabulary constraint for adapter target names | [distribution-adapters](../specs/distribution-adapters/spec.md) |

## Origin and publication

- [RFC-0001](../rfc/0001-bundle-distribution-by-adapter-spec.md) introduced
  the adapter contract as RFC-0001's F-spec. See § Amendments for the
  rename from `docs/specs/adapter-contract/` to here.
- [RFC-0003](../rfc/0003-spec-and-cli.md) lifts the contract to a published
  open standard with versioning and a conformance suite.
- [RFC-0076](../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)
  D1 establishes the authority model above; D2 requires all contracts listed here
  to be bundled byte-identically in `agentbundle/_data/`.

Future contracts land here too, each in its own PR.
