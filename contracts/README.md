# `contracts/`

Catalogue-level, machine-readable contract files. These are *not* per-feature
specs — they're the published interface this catalogue exposes to consumers
(APM, Claude Code plugins, the `agentbundle` CLI, future adopters).

**Authority model:** `contracts/` is the canonical authored source for all
contracts listed below. `packages/agentbundle/agentbundle/_data/` carries
byte-identical copies only of contracts explicitly marked **yes** in the CLI
data column; repository-public contracts marked **no** remain authoritative here
without implying a second CLI copy. AGENTS.md and README files carry concise
operational guidance only. When an authored contract and a declared copy
disagree, `contracts/` is authoritative.

## Files

| File | What it pins | CLI data |
| --- | --- | --- |
| `adapter.toml` | Per-IDE adapter contract: every (primitive × adapter) projection rule | yes |
| `adapter.schema.json` | JSON Schema for `adapter.toml`'s shape | yes |
| `distribution-routes.toml` | Package-route identity, layout, projector, capability, marketplace, and lifecycle concerns | yes |
| `distribution-routes.schema.json` | Closed JSON Schema for the versioned distribution-route contract | yes |
| `agent-plugin-extension-namespaces.toml` | Agent Plugins reverse-domain extension allocations and lifecycle state | yes |
| `agent-plugin-extension-namespaces.schema.json` | Closed schema for extension namespace allocations | yes |
| `vendor/agent-plugins/1.0.0/plugin.schema.json` | Immutable upstream Agent Plugins 1.0.0 manifest schema | yes |
| `vendor/agent-plugins/1.0.0/mcp.schema.json` | Immutable upstream Agent Plugins 1.0.0 MCP schema, reserved for Phase 1B behavior | yes |
| `vendor/agent-plugins/1.0.0/LICENSE.md` | Upstream licence notice governing the vendored schemas | yes |
| `vendor/agent-plugins/1.0.0/PROVENANCE.md` | Upstream commit, paths, blob identities, schema IDs, and offline-use boundary | yes |
| `pack.schema.json` | JSON Schema for per-pack `pack.toml` manifests | yes |
| `plugin-manifest.schema.json` | JSON Schema for `.claude-plugin/plugin.json` | yes |
| `plugin-manifest.derived.schema.json` | Derived schema for `.claude-plugin/plugin.json` after adapter-rule merge | yes |
| `catalogue.schema.json` | JSON Schema for `catalogue.toml` manifests | yes |
| `profile.schema.json` | JSON Schema for profile TOML files | yes |
| `catalogue-index.schema.json` | JSON Schema for the generated neutral catalogue index | yes |
| `marketplace-entry.schema.json` | JSON Schema for one generated marketplace entry | yes |
| `guide.schema.json` | JSON Schema for guide frontmatter | yes |
| `skill.schema.json` | JSON Schema for skill frontmatter and body | yes |
| `skill-manifest.schema.json` | JSON Schema for skill manifest files | yes |
| `target-vocab.toml` | Vocabulary constraint for adapter target names | yes |
| `REGISTRY.md` | Backward spec pointers for contracts whose format carries no `x-spec` key | no |
| `jsonschema/knowledge-captured-observation.schema.json` | Captured project-knowledge observation envelope | yes |
| `jsonschema/loop-run-event.schema.json` | One `.loop-run/events.jsonl` line the work-loop engine writes per FSM transition | no |
| `jsonschema/loop-cohort-wave-decision.schema.json` | Read-only pre-dispatch verdict and refusal envelopes emitted by `loop-cohort wave-decision` | no |
| `jsonschema/delivery-lifecycle-record.schema.json` | Git-tracked delivery lifecycle record | no |
| `jsonschema/normalized-intake.schema.json` | Transient normalized work-intake envelope | no |
| `jsonschema/workspace-entry.schema.json` | Target structured `workspace.toml` entry | no |
| `jsonschema/work-intake-migration-selection.schema.json` | Human-reviewed legacy-route selection | no |
| `jsonschema/work-intake-migration-confirmation.schema.json` | Human-authored, single-use apply/rollback confirmation | no |
| `jsonschema/work-intake-migration-manifest.schema.json` | Repository-root reversible migration ledger | no |
| `jsonschema/work-intake-migration-result.schema.json` | Closed workspace-status migration result object | no |
| `delivery/delivery-subject.v1.schema.json` | Canonical delivery subject binding product, spec, evidence policy, exclusions, lineage, and acceptance fingerprint | no |
| `delivery/acceptance-property.v1.schema.json` | Normalized acceptance property from approved spec criterion with authority, selector, observations, freshness, satisfaction, and contradiction rules | no |
| `delivery/approval-record.v1.schema.json` | Spec-policy approval record binding authority, decision scope, base, lineage, and spec-policy fingerprint | no |
| `delivery/reviewed-execution-envelope.v1.schema.json` | Pure projection fingerprinting ordered references to separately owned approvals for criteria, scope, authority, contracts, outputs, and risk | no |
| `delivery/initial-plan-review.v1.schema.json` | Initial plan review record binding envelope fingerprint, plan hash, authorized terminal intent, reviewer, and decision | no |
| `delivery/semantic-evidence-transaction.v1.schema.json` | Checksummed semantic evidence transaction with ordered record IDs, acceptance fingerprint, and checksum | no |
| `delivery/evidence-receipt.v1.schema.json` | Evidence receipt from a producer through the evidence port, with acceptance fingerprint, lineage, selector, freshness mode, observation, outcome, and producer | no |
| `delivery/evidence-supersession.v1.schema.json` | Evidence supersession withdrawing prior receipts, with authority and provenance | no |
| `delivery/acceptance-verdict.v1.schema.json` | Derived acceptance verdict from the satisfaction evaluator, tracing criteria and receipts | no |
| `delivery/security-capability.v1.schema.json` | Security capability grant covering roots, operations, trust class, writes, read proof mode, control denies, network, children, and limits | no |
| `delivery/confined-file.v1.schema.json` | Confined file reference with canonical root and relative path for the path and mutation primitives | no |
| `delivery/safe-process.v1.schema.json` | Safe process specification with absolute executable, identity, fixed argv, grant, confined cwd, environment allowlist, stdin mode, and process-tree and output bounds | no |
| `delivery/containment-attestation.v1.schema.json` | Containment attestation from the verified launcher binding host mechanism, principal, roots, read enforcement, network, children, and limits | no |
| `delivery/security-event.v1.schema.json` | Security event from the primitive or broker to the audit sink with operation ID, correlation ID, event type, outcome, reason code, and timestamp | no |
| `delivery/content-safety-policy.v1.schema.json` | Content safety policy defining classification vocabulary, scanner corpus digest, and boundary profiles for every persistence boundary | no |
| `delivery/content-safety-decision.v1.schema.json` | Content safety decision from the persistence guard with source record, policy, profile, normalized-record digest, and decision code | no |
| `delivery/untrusted-data.v1.schema.json` | Typed inert-data wrapper for accepted free text ensuring downstream consumers treat content as data, not instructions or authority | no |

## Which design governs which file

- **Distribution routes and runtime adapters** — `distribution-routes.toml`,
  `distribution-routes.schema.json`, `adapter.toml`, `adapter.schema.json`,
  `pack.schema.json`, both `plugin-manifest` schemas, and `target-vocab.toml` —
  come from the [distribution-route decision][routes] and the
  [distribution-by-adapter design][adapters]. Routes own package identity,
  layout, package-manifest projection, component capabilities, marketplace
  projection, and lifecycle triggers; adapters continue to own direct-install
  projection rules.
- **The catalogue and profile manifests** — `catalogue.schema.json` and
  `profile.schema.json` — come from the [catalogue spec and CLI][cli], which
  also lifted these contracts into a published open standard with versioning and
  a conformance suite.
- **The neutral catalogue index** — `catalogue-index.schema.json` — comes from
  the [contracts composition and discovery design][composition] and pins the
  adapter-neutral discovery document emitted by `agentbundle catalogue index`.
- **The guide and skill schemas** — `guide.schema.json`, `skill.schema.json`,
  and `skill-manifest.schema.json` — implement the
  [agentskills.io standard](../guides/_shared/reference/agentskills-io-standard.md),
  which travels with this catalogue.
- **The work-intake JSON Schemas** under `jsonschema/` come from the
  [normalized intake/workspace contract][work-intake-contracts] and
  [migration contract][work-intake-migration]. They are public authored
  repository contracts, not declared AgentBundle CLI data copies.
- **The canonical delivery schemas** under `delivery/` come from the
  [acceptance authority and evidence spec][delivery-contracts]. They define the
  portable record shapes for acceptance properties, approvals, evidence,
  security primitives, and content safety decisions. These are test-time
  contracts only; no schema copy ships in the Core pack at runtime.

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
[routes]: https://github.com/eugenelim/agent-ready-repo/blob/main/docs/rfc/0092-first-class-distribution-routes.md
[work-intake-contracts]: https://github.com/eugenelim/agent-ready-repo/blob/main/docs/specs/normalized-intake-workspace-contracts/spec.md
[work-intake-migration]: https://github.com/eugenelim/agent-ready-repo/blob/main/docs/specs/work-intake-migration-docs/spec.md
[delivery-contracts]: https://github.com/eugenelim/agent-ready-repo/blob/main/docs/specs/acceptance-authority-and-evidence/spec.md
