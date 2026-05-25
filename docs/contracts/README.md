# `docs/contracts/`

Catalogue-level, machine-readable contract files. These are *not* per-feature
specs — they're the published interface this catalogue exposes to consumers
(APM, Claude Code plugins, the `agentbundle` CLI, future adopters).

## Files

| File | What it pins | Governing spec |
| --- | --- | --- |
| `adapter.toml` | Per-IDE adapter contract: every (primitive × adapter) projection rule | [distribution-adapters](../specs/distribution-adapters/spec.md) |
| `adapter.schema.json` | JSON-Schema for `adapter.toml`'s shape | [distribution-adapters](../specs/distribution-adapters/spec.md) (AC #1) |
| `pack.schema.json` | JSON-Schema for per-pack `pack.toml` manifests | [distribution-adapters](../specs/distribution-adapters/spec.md) (AC #3) |
| `plugin-manifest.schema.json` | JSON-Schema for `.claude-plugin/plugin.json` | [distribution-adapters](../specs/distribution-adapters/spec.md) (AC #4) |

## Origin and publication

- [RFC-0001](../rfc/0001-bundle-distribution-by-adapter-spec.md) introduced
  the adapter contract as RFC-0001's F-spec. See § Amendments for the
  rename from `docs/specs/adapter-contract/` to here.
- [RFC-0003](../rfc/0003-spec-and-cli.md) lifts the contract to a published
  open standard with versioning and a conformance suite.

Future contracts (`.agentbundle-state.toml`, `.adapt-discovery.toml`, recipe
schema) land here too, each in its own PR.
