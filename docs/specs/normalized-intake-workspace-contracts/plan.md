# Plan: Normalized intake and workspace contracts

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> note why in the changelog at the bottom.

## Approach

Define the two JSON Schemas first, with separate fixture sets so normalized-source concerns do not leak into workspace lifecycle rules. Then add contextual TOML fixtures for memberships, legacy reads, authority, and compaction. A single contract-test module validates the schemas, parses TOML through the standard library, and checks the contextual invariants the entry schema cannot express alone. Documentation and the core seed land last, generated projections follow their `.apm` sources, and no production reader changes until `workspace-routing-invariants`.

## Constraints

- RFC-0083 fixes artifact responsibilities, lifecycle memberships, dependency meanings, authority modes, compatibility shapes, and migration duration.
- The two Group 1 ADRs are approval prerequisites. One refines feature projection and tracker authority; the other establishes standalone intake, the shared minimal intent contract, relocatable core intent output, and deterministic workspace indexing. Their identifiers remain unstated until assigned.
- `contracts/jsonschema/normalized-intake.schema.json` and `contracts/jsonschema/workspace-entry.schema.json` are the sole machine-readable contracts.
- Runtime core readers remain Python 3.11+ and stdlib-only. `jsonschema` is test-time only.
- New pack tests belong under `packs/core/tests/`; `.apm/` contains shipped sources, not tests.
- Changes under `packs/core/` require a pack version/plugin version bump, self-host projection, and changelog entry.
- Shipped pack content does not cite this repository’s RFC, ADR, spec, or AC identifiers.

## Construction tests

**Integration tests:**

- Parse every TOML fixture with `tomllib`, normalize each target entry to JSON, and validate it against `workspace-entry.schema.json`.
- Assert every JSON Schema example and every workspace guide/seed example uses the same field names and enum values.
- Run the compaction fixture matrix against the reference graph oracle and prove live dependencies and open parents are retained.
- Validate both schemas with `jsonschema.validators.validator_for(...).check_schema(...)`.

**Manual verification:**

- Security review confirms source content is treated as data, sensitive payloads have no persistence field, and path checks fail closed.
- Review the rendered workspace reference as a cold adopter and confirm the canonical form, legacy form, and non-dispatchability distinction are explicit.

## Design (LLD)

### Design decisions

- The contracts use two schemas because normalized intake is a transient source-boundary envelope, while a workspace entry is durable repository coordination state. Combining them would expose source payload fields to the workspace index. Traces to: AC1–AC8.
- JSON Schema validates object shape; contextual lifecycle, duplicate-membership, compatibility, and compaction rules use TOML fixtures plus a reference oracle. Traces to: AC15–AC23.
- Legacy forms stay outside the target entry schema. The compatibility reader recognizes them explicitly rather than weakening the target schema. Traces to: AC20–AC21.

### Data & schema

`normalized-intake.schema.json` defines:

- `contract_version`
- `action: start | remember | refresh`
- normalized `content`
- source locator, revision, profile id/version, and object-type hint
- supplied constraints
- proposed authority mode
- refresh-only target artifact path

`workspace-entry.schema.json` defines:

- canonical artifact `path`
- `kind`
- bounded `source`
- display-only `summary`
- typed hard dependencies in `needs`

Membership, lifecycle, source-decision, minimal-intent, defect, legacy, and compaction fixtures remain separate because they describe relationships among entries and artifacts. Traces to: AC1–AC23 · `contracts/jsonschema/normalized-intake.schema.json` · `contracts/jsonschema/workspace-entry.schema.json`.

### Interfaces & contracts

The two schemas are the published interfaces. Each carries an `x-spec` backlink. Consumers validate parsed representations and must enforce repository confinement after schema validation. No runtime code imports the test-only `jsonschema` package. Traces to: AC1, AC7, AC10, AC24.

### Component / module decomposition

- `contracts/jsonschema/*.schema.json`: normative object contracts.
- `packs/core/tests/pack/fixtures/work-intake-contracts/`: valid, invalid, lifecycle, legacy, and compaction evidence.
- `packs/core/tests/pack/test_work_intake_contracts.py`: schema and contextual contract tests.
- `guides/core/reference/workspace-toml-schema.md`: adopter-facing exact TOML encoding and semantics.
- `packs/core/seeds/workspace.toml`: target empty-workspace example.
- `packs/core/.apm/skills/workspace-status/SKILL.md`: initialization text aligned to the contract.

Traces to: AC1–AC24.

### State & control flow

A source becomes a normalized transient record, classification chooses a canonical artifact, and registration writes a target workspace entry. Legacy inputs take a separate compatibility branch and remain non-dispatchable until human routing produces canonical state. Compaction evaluates references before removing only the index entry. Traces to: AC2–AC5, AC15–AC23.

### Behavior & rules

- Hints never select an artifact by themselves.
- Summary and comments never affect semantics.
- Tracker-origin requires durable provenance.
- Dependencies are positive, typed, and hard.
- Cross-repository status is represented by reviewed local receipts.
- Compatibility never implies promotion.

Traces to: AC5, AC11–AC23.

### Failure, edge cases & resilience

Invalid schemas fail tests. Invalid target entries fail validation. Legacy entries are recognized only by the enumerated compatibility shapes. Unknown extensions remain manual-routing findings and do not expand the compatibility contract. Paths require runtime realpath confinement even after lexical schema checks. Traces to: AC8–AC10, AC20–AC22.

### Quality attributes (NFRs)

- Deterministic: the same parsed record produces the same validation result.
- Portable: runtime consumers need only Python 3.11 stdlib facilities.
- Auditable: schema versions, backlinks, fixtures, and authority provenance are explicit.
- Confidential: no unbounded payload or credential field exists.

Traces to: AC1–AC7, AC10, AC23–AC24.

### Dependencies & integration

Group 3 consumes both schemas and the fixture corpus. Groups 4–7 consume the normalized envelope, workspace encoding, authority records, and legacy cases without redefining them. The contracts add no network, storage, or runtime-library dependency. Traces to: AC1–AC24.

## Tasks

### T1: Normalized-intake schema accepts every supported acquisition action and rejects unsafe persistence shapes

**Depends on:** none

**Touches:** `contracts/jsonschema/normalized-intake.schema.json`, `packs/core/tests/pack/fixtures/work-intake-contracts/normalized-intake/*.json`, `packs/core/tests/pack/test_normalized_intake_contract.py`

**Verification mode:** TDD

**Tests:**

**Stub:** draft (uncompiled) — `normalized-intake.schema.json`, imported by the pytest cases below, is created by this task and is unavailable at PLAN. The first EXECUTE action materializes these cases as compilable failing tests before any schema or other production-contract edit.

- Valid fixtures cover repo-origin and tracker-origin `start`, `remember`, and `refresh`. Traces to: AC1–AC5, AC19.
- Invalid fixtures reject status-as-normalized-intake, refresh without an artifact target, target on start/remember, missing tracker revision, unknown action/authority, raw payload, credentials, and unknown fields. Traces to: AC3–AC6.
- Schema validation confirms the `x-spec` backlink and stable contract version. Traces to: AC1.

**Approach:**

- Author `contracts/jsonschema/normalized-intake.schema.json`.
- Use conditional schema branches for action-specific fields and authority-specific provenance.
- Keep substantive content normalized and bounded; omit raw source payload and instruction fields.
- Add focused valid and invalid JSON fixtures.

**Done when:** all normalized-intake fixtures produce their declared valid/invalid result and the schema passes its meta-schema check.

### T2: Workspace-entry schema and contextual fixtures encode lifecycle, authority, legacy, and compaction rules

**Depends on:** none

**Touches:** `contracts/jsonschema/workspace-entry.schema.json`, `packs/core/tests/pack/fixtures/work-intake-contracts/workspace/**`, `packs/core/tests/pack/test_workspace_entry_contract.py`

**Verification mode:** TDD

**Tests:**

**Stub:** draft (uncompiled) — `workspace-entry.schema.json` and its contextual fixture contract, imported by the pytest cases below, are created by this task and are unavailable at PLAN. The first EXECUTE action materializes these cases as compilable failing tests before any schema, fixture-oracle, or other production-contract edit.

- Valid target entries cover every `kind`, both authority modes, parent provenance, local dependencies, and cross-repository receipt pins. Traces to: AC7–AC14, AC19.
- Invalid target entries reject missing semantic fields, unknown fields/kinds, unsafe paths, tracker-origin without revision, field ownership in workspace source, scalar needs, and incomplete receipt pins. Traces to: AC8–AC14.
- TOML fixtures cover every lifecycle membership, Ready-without-spec, minimal intent, defect outcomes, and every accepted legacy representation. Traces to: AC15–AC21.
- Compaction fixtures retain entries with live dependency/open-parent references or incomplete closure evidence and allow only safe index removal. Traces to: AC22.
- Comment, summary, and ordering variants preserve the same semantic graph. Traces to: AC23.

**Approach:**

- Author `contracts/jsonschema/workspace-entry.schema.json`.
- Choose one canonical TOML encoding: inline entry tables containing all five fields; `needs` is an array of typed inline tables.
- Add parsed-TOML fixture manifests with expected membership, compatibility classification, and compaction result.
- Keep legacy shapes out of the target schema and enumerate them in compatibility fixtures.

**Done when:** all target, lifecycle, legacy, and compaction fixtures carry an explicit expected result and no target fixture depends on comments.

### T3: One contract harness verifies both schemas and every contextual fixture

**Depends on:** T1, T2

**Touches:** `packs/core/tests/pack/test_work_intake_contracts.py`

**Verification mode:** TDD

**Tests:**

**Stub:** draft (uncompiled) — the two schemas and fixture contracts imported by `test_work_intake_contracts.py` are created by upstream RFC-0083 tasks T1 and T2 and are unavailable at PLAN. The first EXECUTE action materializes the cases below as compilable failing tests before any cross-contract harness or oracle implementation edit.

- Both schemas pass the selected JSON Schema meta-validator.
- Every JSON fixture validates or fails with the expected schema path.
- Every TOML entry normalizes to the same five-field JSON form before validation.
- The contextual oracle rejects duplicate membership, impossible membership/status pairs, unsafe legacy promotion, and unsafe compaction.
- The minimal intent, defect, authority-decision, and Ready-without-spec fixtures satisfy their contract assertions.

**Approach:**

- Add a pytest module under the core pack’s pack-test boundary.
- Use `jsonschema` only in tests and `tomllib` for TOML parsing.
- Keep expected outcomes in fixture metadata so new consumers reuse the cases.
- Make failure output identify the fixture and contract rule.

**Done when:** `python3 -m pytest packs/core/tests/pack/test_work_intake_contracts.py -q` passes and demonstrates every AC1–AC23 fixture family.

### T4: Published workspace references, seed, and pack projections match the contracts

**Depends on:** T3

**Touches:** `guides/core/reference/workspace-toml-schema.md`, `packs/core/seeds/workspace.toml`, `packs/core/.apm/skills/workspace-status/SKILL.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`

**Verification mode:** goal-based check

**Tests:**

**Stub:** no stub (goal-based check)

- Extracted guide and seed examples parse and validate against the T1/T2 schemas. Traces to: AC24.
- The guide states comments and summaries are non-semantic, documents every lifecycle membership, and identifies legacy entries as non-dispatchable. Traces to: AC13, AC15–AC23.
- Pack and plugin versions match; generated projections are drift-clean.
- Catalogue lint, verify, guide validation, and build checks pass.

**Approach:**

- Rewrite the workspace reference around the target contract and compatibility appendix.
- Replace the seed’s legacy comments and example syntax with the canonical five-field form.
- Update the workspace-status initialization template at its `.apm` source.
- Bump core pack metadata, project once after all source edits, and add the changelog entry.

**Done when:** documentation examples validate, pack/projected sources are synchronized, and the repository’s contract, guide, catalogue, and build gates pass.

## Rollout

- **Delivery:** contract-first. This change publishes schemas, fixtures, references, and target seeds without enabling target-state dispatch or a write-new router.
- **Infrastructure:** none.
- **External-system integration:** none; tracker adapters consume the normalized schema only in later groups.
- **Deployment sequencing:** T1/T2 establish the contracts, T3 proves them, and T4 publishes them. Group 3 lands after T4 and implements readers. Existing writers remain unchanged until the reader-first compatibility release is available.
- **Rollback:** revert the contract publication before any write-new release. No canonical artifacts are deleted and no workspace is automatically migrated.

## Risks

- The entry schema may accidentally encode lifecycle context that belongs in the workspace parser, making the schema brittle.
- A permissive source object could turn `workspace.toml` into a second authority store.
- A compatibility fixture could be mistaken for a target writer example.
- Root contracts and adopter-facing pack references could drift if examples are not validated by the same harness.
- The two Group 1 ADRs may sharpen wording; approval must wait until their accepted text matches these contracts.

## Changelog

- 2026-08-09: Initial plan derived from accepted RFC-0083 and confirmed assumptions.
