# Plan: OKF catalogue discovery

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as implementation evidence changes.

## Approach

Treat the complete `show --format json` response as one versioned behavioral
contract. First lock its catalogue and installed-state variants with the JSON
Schema and golden fixtures. Then add pure, standard-library metadata extractors
for pack, Skill, and OKF bundle summaries; compare their generated markers and
digests with the authoring compiler's golden vectors; and extend only the JSON
renderer. Keep table rendering, install-state inventory recovery, pack listing,
marketplace generation, and `catalogue-index.json` outside the change. Finish
with the package release surfaces required for a public output-format addition.

## Constraints

- RFC-0087 D6 defines the three discovery levels, exact allowlists, catalogue
  versus installed-state degradation, and the exclusion of concept bodies and
  cross-pack OKF indexing.
- RFC-0060 and ADR-0049 require live catalogue inventory; no persisted
  discovery cache or index may become authoritative.
- RFC-0076 owns `catalogue-index.json`; this experiment must keep its schema and
  bytes unchanged.
- `contracts/jsonschema/agentbundle-show.schema.json` is the complete success
  response contract. Errors remain stderr/exit-code behavior, not JSON bodies.
- The package keeps Python 3.11+ and zero base dependencies. Discovery uses no
  PyYAML, compiler import, pack-local script import, network, or LLM.
- A changed public JSON format requires the package version, PyPI README, and
  release notes to move together.

## Construction tests

**Integration tests:**

- Validate actual catalogue, empty-pack, authored-Skill, generated-pilot, and
  installed-state CLI responses against the complete JSON Schema.
- Share canonical digest/metadata vectors with the authoring compiler and prove
  discovery reports the same identities without executing or importing it.
- Run legacy table, error, inventory, list-packs, marketplace, and
  `catalogue-index.json` regression tests to prove excluded surfaces unchanged.
- Build the package without lint extras and run JSON discovery to prove the base
  dependency posture.

**Manual verification:** none beyond reviewing the documented JSON examples;
all behavior is machine-observable.

## Design (LLD)

### Design decisions

- The renderer constructs one explicit closed response record on both success
  paths; it does not merge arbitrary metadata dictionaries. Traces to AC1–AC4
  and AC13.
- Catalogue discovery is a read-only projection over the current pack tree.
  Generated manifests are integrity witnesses, not a discovery inventory:
  values come from live sources and are compared with manifest identities.
  Traces to AC7–AC12 and AC19–AC20.
- The installed-state path cannot establish rich metadata and therefore emits
  three explicit nulls. It never mines projected files for partial truth.
  Traces to AC15.
- A small package-local standard-library parser handles only the frontmatter
  subset needed for the allowlist. Unsupported YAML fails honestly rather than
  adding a base dependency or silently dropping fields. Traces to AC12 and AC19.

### Data & schema

- `ShowResponse` owns the ten top-level fields and has two schema-constrained
  variants selected by `source`.
- `PackMetadata` is the closed categories/keywords/licence record.
- `SkillMetadata` is keyed by canonical Skill directory name and carries the
  allowlisted activation and generated markers.
- `KnowledgeMetadata` is keyed by declared bundle ID and carries format,
  supported version, router name, licence, live concept count, and canonical
  source digest.
- Collections normalize strings to Unicode NFC for ordering and reject
  case-fold collisions, enforce the AC12a count limits, and reject non-portable
  control/device-name path segments. JSON uses the existing compact encoder and
  one LF.

### Interfaces & contracts

- The external interface remains
  `agentbundle show <pack> --format {table,json}`. No flag or exit-code set is
  added.
- Successful JSON implements
  `contracts/jsonschema/agentbundle-show.schema.json`; table output intentionally
  does not expose the new records.
- The authoring compiler's profile, marker, manifest, and digest formats are
  consumed contracts from `okf-authoring-projection`; discovery never calls its
  process interface.

### Component / module decomposition

- `commands/show.py` retains resolution, degradation, and rendering
  orchestration and passes three additional typed values into `_emit`.
- A focused package-local discovery module owns safe frontmatter subset parsing,
  normalization, pack/Skill/knowledge extraction, digest calculation, and
  manifest cross-checks. It has no write functions.
- `test_show_cmd.py` owns end-to-end compatibility; focused unit tests own
  extraction edge cases; contract tests own complete-response schema coverage.

### State & control flow

1. Resolve the catalogue and selected pack through the existing source chain.
2. Inventory Skills/agents through existing helpers.
3. Size-gate `pack.toml`, Skill directories/files/frontmatter, and the generated
   manifest before parsing; derive the closed pack record and discover Skill
   metadata from sorted live Skill directories.
4. If `[pack.metadata.okf]` is absent, return an empty knowledge array. If
   present, validate the supported profile and each confined bundle, derive
   live summary values, and compare markers/digests with the manifest.
5. Construct and emit the complete JSON object, or render the unchanged table.
6. If catalogue resolution fails but install state contains the pack, run the
   existing inventory union and emit rich metadata nulls.

### Behavior & rules

- Exact directory inventories remain authoritative for `skills` and `agents`;
  metadata never filters them to eval or projected subsets.
- Authored Skill fields do not inherit pack values. Generated fields must be a
  complete, consistent marker set or the command fails.
- Knowledge enumeration begins only from the pack's declared OKF bundles; an
  undeclared `okf/` directory is not surfaced.
- All objects and arrays are allowlisted and stable; missing optional scalar
  metadata is `null`, missing collections are empty arrays.

### Failure, edge cases & resilience

- An invalid managed declaration, missing bundle, unsafe path, malformed
  required frontmatter subset, unsupported version/profile, marker conflict,
  manifest drift, digest mismatch, or duplicate normalized identity produces
  exit 1, empty stdout, and a one-line relative diagnostic.
- A size, depth, or item-count limit is checked before the corresponding full
  parse/allocation and fails through the same empty-stdout channel.
- An ordinary pack without OKF remains a successful catalogue response.
- Catalogue-unavailable behavior continues through the existing state loader,
  including warned-and-skipped incompatible state scopes.
- Reads are bounded by the authoring profile's limits so inspection cannot turn
  an invalid oversized bundle into an unbounded CLI operation.

### Quality attributes (NFRs)

- Compatibility: every legacy field and non-JSON surface has regression
  coverage; new top-level fields are additive.
- Determinism: repeated reads of unchanged bytes emit identical response bytes
  and stable ordering.
- Honesty: rich metadata is either source-backed and internally consistent or
  null/error; there is no partial installed-state reconstruction.
- Security/privacy: output contains no body text, remote locator, authorship,
  raw extension, absolute path, secret, or instruction content.

### Dependencies & integration

- Reuse verified pack resolution, TOML loading, Skill/agent inventory, and
  compact JSON emission from the existing command path.
- Consume golden profile/digest vectors from the authoring spec's tests through
  neutral test fixtures, not imports from shipped pack code.
- Package version/release files move only in the final task after the public
  behavior and regression suite are green.

## Tasks

### T1: The complete show JSON contract accepts both success variants and rejects drift

**Depends on:** none

**Touches:** `contracts/jsonschema/agentbundle-show.schema.json`, `packages/agentbundle/tests/contracts/test_agentbundle_show_schema.py`, `packages/agentbundle/tests/fixtures/show_contract/**`

**Verification mode:** TDD.

**Tests:**

- Add catalogue and installed-state golden objects plus one invalid mutation for
  every required key, closed object, scalar/array type, source conditional,
  digest, normalized path, and nested allowlist in AC1–AC16.
- Validate the schema itself as JSON Schema 2020-12.

**Approach:**

- Keep the schema self-contained and model source-specific nullability with
  conditional branches over `source`.

**Done when:** The contract suite covers every response field and both success
variants with no implementation import.

### T2: Live pack, Skill, and knowledge extraction is deterministic and fail-closed

**Depends on:** T1, spec:okf-authoring-projection/T3

**Touches:** `packages/agentbundle/agentbundle/catalogue_tooling/okf_discovery.py`, `packages/agentbundle/tests/unit/test_okf_discovery.py`, `packages/agentbundle/tests/fixtures/okf_discovery/**`

**Verification mode:** TDD.

**Tests:**

- Stub and implement AC4–AC14 and AC19 across authored/generated neutral
  fixtures, no-OKF packs, live edits, boundary-equal/boundary-plus-one size,
  depth and list limits, malformed inputs, portable-path failures, collisions,
  router/procedure review-marker rules, marker/manifest disagreement, and shared
  compiler digest vectors. Actual pilot coverage remains in T4 after T6–T8
  produce the pilot artifacts.
- Monkeypatch network, process execution, write APIs, and optional YAML imports
  to fail if the extractor attempts them.

**Approach:**

- Introduce typed closed records and a bounded standard-library frontmatter
  subset parser. Derive values from live bytes, then use the manifest only to
  verify generated identity and source digest.

**Done when:** Pure extractor tests pass without PyYAML and return either a
complete normalized record or one safe relative diagnostic.

### T3: show emits the additive schema-valid JSON while preserving all legacy paths

**Depends on:** T2

**Touches:** `packages/agentbundle/agentbundle/commands/show.py`, `packages/agentbundle/tests/integration/test_show_cmd.py`, `packages/agentbundle/tests/unit/test_local_scope_t12_show.py`

**Verification mode:** TDD plus goal-based CLI integration checks.

**Tests:**

- Update exact-key tests for AC2–AC3 and add schema validation for catalogue,
  empty, non-OKF, neutral generated-OKF, and installed-state responses.
- Preserve byte/snapshot coverage for table output, unknown packs,
  unavailable-not-installed errors, legacy state warnings, and multi-scope
  inventory union under AC15–AC19.

**Approach:**

- Extend catalogue `_emit` inputs with three closed records and the degrade call
  with three nulls. Keep table rendering ignorant of them.
- Convert extractor failures into the existing command error channel with no
  JSON error body.

**Done when:** All show integration tests pass and actual success output validates
against the complete schema.

### T4: The release and excluded discovery surfaces are verified together

**Depends on:** T3, spec:okf-authoring-projection/T8

**Touches:** `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/pyproject.toml`, `packages/agentbundle/README-pypi.md`, `packages/agentbundle/CHANGELOG.md`, `packages/agentbundle/tests/**`, `docs/architecture/agentbundle.md`, `docs/architecture/pack-layout.md`

**Verification mode:** Goal-based package, regression, and documentation checks.

**Tests:**

- Run AC18 and AC21 regression coverage over list-packs, marketplace,
  `catalogue-index.json`, package build metadata, schema files, base-only
  installation, and user-facing examples.
- Run AC20 against the actual generated `security-checklists` pack and the
  exact cost-pilot bytes staged beneath a temporary discoverable catalogue
  path, validating both complete CLI responses against the schema.
- Run the full AgentBundle package suite and documentation link/lint gates.

**Approach:**

- Apply one compatible package version bump and update release documentation
  only after T3 is green. Document rich discovery as Experimental while keeping
  excluded surfaces explicit.

**Done when:** Package and documentation gates pass, version metadata agrees,
and no excluded discovery artifact changes.

## Rollout

- **Delivery:** Ship as an additive JSON response in the AgentBundle version
  produced by T4. Consumers must treat the new rich fields as Experimental
  until RFC-0087 reaches a terminal decision.
- **Infrastructure:** None; the command reads local catalogue or install-state
  files only.
- **External-system integration:** None. No registry, network service, or
  upstream OKF fetch participates in discovery.
- **Deployment sequencing:** The authoring contracts and generated-metadata
  vectors precede extraction; extraction precedes renderer changes; the two
  pilot outputs and adapter checks precede release closeout.
- **Rollback:** Under rejection/withdrawal, remove the three rich response
  fields, discovery helper and schema/tests/docs in the cleanup release while
  preserving the seven legacy fields and installed inventory behavior.

## Risks

- The existing lightweight frontmatter parser may accept a wider or narrower
  subset than the generated Skill contract; isolate and test the discovery
  subset instead of importing a lint-private helper blindly.
- Reimplementing the compiler digest algorithm in the package can drift. Shared
  golden vectors and an explicitly specified canonical algorithm are required;
  direct imports would invert the package/pack dependency.
- Strict failure on malformed managed OKF can surprise operators accustomed to
  `show` succeeding on partially malformed packs. The behavior is intentional:
  a partial knowledge inventory would be falsely authoritative.
- Adding exact-key schema closure makes future additive fields require a schema
  update. That is the desired contract discipline but carries release cost.
- Release docs can imply cross-pack search or installed knowledge recovery that
  does not exist; examples must show one pack and explicit installed-state
  nulls.

## Changelog

- 2026-08-15: Initial plan following RFC-0087 Open approval and confirmation
  that one JSON Schema governs the complete `agentbundle show` success response.
