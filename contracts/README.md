# `contracts/`

Catalogue-level, machine-readable contract files. These are *not* per-feature
specs — they're the published interface this catalogue exposes to consumers
(APM, Claude Code plugins, the `agentbundle` CLI, future adopters).

**Authority model:** `contracts/` is the canonical authored source for all
contracts listed below. Membership in the catalogue specification, and each
contract's role (member, bundled or vendored), is declared in
[`catalogue-spec.toml`](catalogue-spec.toml); the sections below follow it. `packages/agentbundle/agentbundle/_data/` carries
byte-identical copies only of contracts explicitly marked **yes** in the CLI
data column; repository-public contracts marked **no** remain authoritative here
without implying a second CLI copy. AGENTS.md and README files carry concise
operational guidance only. When an authored contract and a declared copy
disagree, `contracts/` is authoritative.

## Files

### Specification members

| File | What it pins | CLI data |
| --- | --- | --- |
| `pack.schema.json` | JSON Schema for per-pack `pack.toml` manifests | yes |
| `catalogue.schema.json` | JSON Schema for `catalogue.toml` manifests | yes |
| `profile.schema.json` | JSON Schema for profile TOML files | yes |
| `skill.schema.json` | JSON Schema for skill frontmatter and body | yes |
| `skill-manifest.schema.json` | JSON Schema for skill manifest files | yes |
| `target-vocab.toml` | Vocabulary constraint for adapter target names | yes |
| `catalogue-index.schema.json` | JSON Schema for the generated neutral catalogue index | yes |
| `adapter.toml` | Per-IDE adapter contract: every (primitive × adapter) projection rule | yes |
| `adapter.schema.json` | JSON Schema for `adapter.toml`'s shape | yes |
| `catalogue-manifest.schema.json` | JSON Schema for the `catalogue-manifest.json` inside a catalogue archive (shape only) | yes |

### Bundled, not members

| File | What it pins | CLI data |
| --- | --- | --- |
| `marketplace-entry.schema.json` | JSON Schema for one generated marketplace entry | yes |
| `plugin-manifest.schema.json` | JSON Schema for `.claude-plugin/plugin.json` | yes |
| `plugin-manifest.derived.schema.json` | Derived schema for `.claude-plugin/plugin.json` after adapter-rule merge | yes |
| `distribution-routes.toml` | Package-route identity, layout, projector, capability, marketplace, and lifecycle concerns | yes |
| `distribution-routes.schema.json` | Closed JSON Schema for the versioned distribution-route contract | yes |
| `agent-plugin-extension-namespaces.toml` | Agent Plugins reverse-domain extension allocations and lifecycle state | yes |
| `agent-plugin-extension-namespaces.schema.json` | Closed schema for extension namespace allocations | yes |
| `guide.schema.json` | JSON Schema for guide frontmatter | yes |
| `jsonschema/knowledge-captured-observation.schema.json` | Captured project-knowledge observation envelope | yes |

### Vendored

| File | What it pins | CLI data |
| --- | --- | --- |
| `vendor/agent-plugins/1.0.0/plugin.schema.json` | Immutable upstream Agent Plugins 1.0.0 manifest schema | yes |
| `vendor/agent-plugins/1.0.0/mcp.schema.json` | Immutable upstream Agent Plugins 1.0.0 MCP schema, reserved for Phase 1B behavior | yes |

### Vendored notices

| File | What it pins | CLI data |
| --- | --- | --- |
| `vendor/agent-plugins/1.0.0/LICENSE.md` | Upstream licence notice governing the vendored schemas | yes |
| `vendor/agent-plugins/1.0.0/PROVENANCE.md` | Upstream commit, paths, blob identities, schema IDs, and offline-use boundary | yes |

### Repository only

| File | What it pins | CLI data |
| --- | --- | --- |
| `catalogue-spec.toml` | The catalogue specification manifest: every contract file the specification names, each with one role (`member`, `bundled` or `vendored`) | no |
| `REGISTRY.md` | Backward spec pointers for contracts whose format carries no `x-spec` key | no |
| `renames/pack-renames.toml` | Retired pack names mapped to the packs that replaced them; the CLI reads it to hint at a rename. To add a rename, append a `[[rename]]` table; never remove or reuse an old name, which stays reserved permanently; point `to` at a pack in the same catalogue | no |
| `renames/pack-renames.schema.json` | JSON Schema for `renames/pack-renames.toml` | no |
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
| `delivery/review-subject.v1.schema.json` | Canonical review subject binding Slice 1 delivery identity, review policy, normalized paths, normalized statuses, and review lineage | no |
| `delivery/review-obligation.v1.schema.json` | Selected review obligation for one role, review subject, policy, and mandatory/optional/waived kind | no |
| `delivery/review-report.v1.schema.json` | Terminal structured reviewer report with role, subject, lineage, status, and embedded findings | no |
| `delivery/finding.v1.schema.json` | Reviewer finding fields required for actual-failure assessment | no |
| `delivery/finding-assessment.v1.schema.json` | Current finding assessment bound to report, subject, evidence, and assessment lineage | no |
| `delivery/finding-disposition.v1.schema.json` | Authorized disposition for a supported material finding without mutating acceptance support | no |
| `delivery/delivery-fact-feed.v1.schema.json` | One bounded page of a reproducible read-only snapshot of committed delivery facts, each with its knowledge candidate or an explicit none, or an unread-source report | no |
| `delivery/knowledge-observation.v1.schema.json` | Attributed, reproducible knowledge candidate projected from one eligible delivery fact, with every free-text field typed as untrusted data | no |
| `delivery/task-contract.v1.schema.json` | One task the work-loop supervisor projects from the approved plan, with its title identity, pinned-field revision, stubs, and declared effects | no |
| `delivery/execution-request.v1.schema.json` | One deterministic request the work-loop supervisor issues to the trusted controller, closed over nine request kinds, including the reviewer-selection request (`candidates`, `selection_key`) | no |
| `delivery/execution-result.v1.schema.json` | The controller's report for one supervisor request: gate outcome, criterion results, review records, a reviewer selection, a `human-decision` answer, or effect outcome | no |
| `delivery/mechanical-journal.v1.schema.json` | One advisory, deletable line of the supervisor's local journal; no decision reads it | no |
| `delivery/effect-resolution.v1.schema.json` | One durable external-effect line: intent, dispatch, receipt, named-human decision, or retry claim | no |

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
- **The structured review delivery schemas** under `delivery/` come from the
  [structured review boundary spec][review-contracts]. They define review
  subjects, obligations, reports, findings, assessments, and dispositions.
  These are test-time contracts only; no schema copy ships in the Core pack at
  runtime.
- **The delivery knowledge projection schemas** under `delivery/` come from the
  [delivery knowledge projection spec][projection-contracts]. They define the
  fact feed page and the knowledge observation. These are test-time contracts
  only; no schema copy ships in the Core pack at runtime.

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
[projection-contracts]: https://github.com/eugenelim/agent-ready-repo/blob/main/docs/specs/delivery-knowledge-projection/spec.md
[review-contracts]: https://github.com/eugenelim/agent-ready-repo/blob/main/docs/specs/structured-review-boundary/spec.md
