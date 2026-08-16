# `contracts/`

Catalogue-level, machine-readable contract files. These are *not* per-feature
specs — they're the published interface this catalogue exposes to consumers
(APM, Claude Code plugins, the `agentbundle` CLI, future adopters).

**Authority model:** `contracts/` is the canonical authored source for all
contracts listed below. `packages/agentbundle/agentbundle/_data/` carries
byte-identical copies of every contract the CLI bundles; AGENTS.md and README
files carry concise operational guidance only. When these disagree, `contracts/`
is authoritative, and every contract listed here must be bundled byte-identically
in `agentbundle/_data/`.

## Files

| File | What it pins |
| --- | --- |
| `adapter.toml` | Per-IDE adapter contract: every (primitive × adapter) projection rule |
| `adapter.schema.json` | JSON Schema for `adapter.toml`'s shape |
| `pack.schema.json` | JSON Schema for per-pack `pack.toml` manifests |
| `plugin-manifest.schema.json` | JSON Schema for `.claude-plugin/plugin.json` |
| `plugin-manifest.derived.schema.json` | Derived schema for `.claude-plugin/plugin.json` after adapter-rule merge |
| `catalogue.schema.json` | JSON Schema for `catalogue.toml` manifests |
| `profile.schema.json` | JSON Schema for profile TOML files |
| `guide.schema.json` | JSON Schema for guide frontmatter |
| `skill.schema.json` | JSON Schema for skill frontmatter and body |
| `skill-manifest.schema.json` | JSON Schema for skill manifest files |
| `target-vocab.toml` | Vocabulary constraint for adapter target names |

## Which design governs which file

- **The adapter contract** — `adapter.toml`, `adapter.schema.json`,
  `pack.schema.json`, both `plugin-manifest` schemas, and `target-vocab.toml` —
  comes from the [distribution-by-adapter design][adapters], which defines every
  (primitive × adapter) projection rule.
- **The catalogue and profile manifests** — `catalogue.schema.json` and
  `profile.schema.json` — come from the [catalogue spec and CLI][cli], which
  also lifted these contracts into a published open standard with versioning and
  a conformance suite.
- **The guide and skill schemas** — `guide.schema.json`, `skill.schema.json`,
  and `skill-manifest.schema.json` — implement the
  [agentskills.io standard](../guides/_shared/reference/agentskills-io-standard.md),
  which travels with this catalogue.

The authority model stated above comes from the
[contracts composition, semantics, and discovery design][composition]. The
adapter contract itself was [introduced as a distribution proposal][origin],
originally authored at `docs/specs/adapter-contract/` and renamed to this
directory.

Future contracts land here too, each in its own PR.

<!-- Absolute URLs, not repo-relative paths: this directory ships inside a
     packaged catalogue archive (see the catalogue packager's always-included
     set), while docs/ does not — so a relative link out of contracts/ is
     dangling for every adopter who receives one. -->

[adapters]: https://github.com/eugenelim/agent-ready-repo/blob/main/docs/specs/distribution-adapters/spec.md
[origin]: https://github.com/eugenelim/agent-ready-repo/blob/main/docs/rfc/0001-bundle-distribution-by-adapter-spec.md
[cli]: https://github.com/eugenelim/agent-ready-repo/blob/main/docs/rfc/0003-spec-and-cli.md
[composition]: https://github.com/eugenelim/agent-ready-repo/blob/main/docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md
