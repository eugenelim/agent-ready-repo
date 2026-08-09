# Spec: Normalized intake and workspace contracts

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0083, ADR-0077, ADR-0078
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/jsonschema/normalized-intake.schema.json`, `contracts/jsonschema/workspace-entry.schema.json`
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Adopters and workflow authors have one versioned contract for passing acquired work into shared intake and one versioned contract for indexing canonical artifacts in `workspace.toml`. The contracts preserve source provenance, authority, lifecycle membership, and hard dependencies without copying requirements into the workspace index. They accept the legacy shapes supported at RFC-0083 acceptance as explicit, non-dispatchable compatibility input and give every later parser, adapter, status surface, and dispatcher the same fixtures and field meanings.

## Boundaries

### Always do

- Keep normalized intake transient and persist requirements only in the selected canonical artifact.
- Represent every target workspace entry with `path`, `kind`, `source`, `summary`, and `needs`.
- Treat comments, summaries, list order, tracker vocabulary, and profile hints as non-authoritative.
- Version both contracts and maintain valid, invalid, legacy, lifecycle, and compaction fixtures.
- Keep repository paths relative, canonical, and resolvable inside the repository.

### Ask first

- Add or rename an artifact kind, lifecycle membership, authority mode, dependency kind, or normalized-intake action.
- Change a required field or accept a new legacy representation.
- Change the compatibility duration or the conditions for removing a legacy reader.
- Place requirements, field ownership, or source-decision history anywhere other than the canonical artifact.
- Change either Group 1 architectural prerequisite after it is accepted.

### Never do

- Treat a comment, `summary`, tracker type, profile hint, list position, or previous-session memory as a routing input.
- Store complete source payloads, acceptance criteria, credentials, secrets, personal data, or the field-level authority map in `workspace.toml`.
- Convert legacy prose into an Approved spec or otherwise make a legacy entry dispatchable by inference.
- Add a runtime schema-validation dependency to the core read path.
- Permit absolute paths, `..` traversal, or an out-of-repository artifact reference.
- Define a second contract that competes with either JSON Schema.

## Testing Strategy

- **Normalized-intake structure and conditional rules:** TDD against `contracts/jsonschema/normalized-intake.schema.json`, because accepted and rejected payload shapes are finite, table-driven invariants.
- **Workspace entry structure, authority, dependency, and path rules:** TDD against `contracts/jsonschema/workspace-entry.schema.json`, because each field and conditional requirement has a precise valid/invalid boundary.
- **Lifecycle, compatibility, and compaction semantics:** TDD through parsed TOML fixtures and a contract oracle, because those rules depend on entry context rather than one JSON object alone.
- **Reference and seed parity:** goal-based checks that parse every published example and compare its normalized fields with the contract fixtures.
- **Projection and publication:** goal-based catalogue lint, verify, self-host, and guide validation.
- **Security boundaries:** manual security review of path, provenance, confidentiality, prompt-injection, and sensitive-data constraints after the construction tests pass.

## Acceptance Criteria

- [ ] **AC1.** `contracts/jsonschema/normalized-intake.schema.json` is a valid JSON Schema with a stable contract version and an `x-spec` backlink to this spec.
- [ ] **AC2.** A normalized intake record carries `contract_version`, `action`, normalized substantive content, a durable source locator and revision, supplied constraints, and a proposed authority mode.
- [ ] **AC3.** The normalized action vocabulary is `start | remember | refresh`; status bypasses source acquisition and normalized intake and delegates directly to `workspace-status`.
- [ ] **AC4.** `refresh` requires the repository-relative path of an existing canonical artifact. `start` and `remember` reject that refresh-only target field.
- [ ] **AC5.** Tracker profile id/version and tracker object type are optional classification hints under source provenance and cannot determine artifact kind or processor.
- [ ] **AC6.** Normalized content contains only fields needed for classification and materialization—outcomes, constraints, evidence, behaviors, assumptions, and named gaps—and rejects an unbounded raw source-payload field.
- [ ] **AC7.** `contracts/jsonschema/workspace-entry.schema.json` is a valid JSON Schema with a stable contract version and an `x-spec` backlink to this spec.
- [ ] **AC8.** Every target workspace entry requires exactly the semantic fields `path`, `kind`, `source`, `summary`, and `needs`; unknown fields fail schema validation.
- [ ] **AC9.** `kind` is exactly `intent | research | design | brief | spec | defect`.
- [ ] **AC10.** `path` is a repository-relative canonical artifact path. The contract rejects empty paths, absolute paths, backslash-based paths, and paths containing a `..` segment; runtime realpath confinement remains a consumer obligation.
- [ ] **AC11.** `source.mode` is exactly `repo-origin | tracker-origin`. Tracker-origin source records require a durable source reference and revision; repo-origin records may omit an external revision.
- [ ] **AC12.** Workspace source provenance may carry a parent artifact, tracker profile id/version, or coordination reference, but it cannot carry `owned_fields`, source-decision rows, requirements, or credentials.
- [ ] **AC13.** `summary` is non-empty display text and is explicitly excluded from routing, reconciliation, dependency satisfaction, and lifecycle decisions.
- [ ] **AC14.** `needs` is an array of typed hard-dependency records. A local dependency names `kind` and canonical `path`; a cross-repository dependency additionally names the containing local brief, receipt id, and pinned accepted revision.
- [ ] **AC15.** The workspace reference defines every RFC-0083 membership, including `[backlog].open`, `[backlog].closed`, shaping backlog/active, brief draft/ready/executing/shipped, and work queue/active/shipped.
- [ ] **AC16.** A Ready brief with zero child specs is valid, visible, and non-dispatchable.
- [ ] **AC17.** The minimal shared intent contract is documented with `Status`, `Level`, `Outcome`, `Opportunity`, `Assumptions`, and `Source`; its default path is `docs/product/intents/<slug>.md`, subject to an in-repository `[core]` layout override.
- [ ] **AC18.** Defect fixtures require expected behavior, observed behavior, reproduction evidence or an error signature, provenance, and a durable citation establishing intended behavior. Closed defects record exactly `fixed | declined | superseded`.
- [ ] **AC19.** Fixtures cover both authority modes and the artifact-owned source-decision values `keep-local`, `accept-source`, and `revise-both`; the workspace mirror contains no field-ownership map.
- [ ] **AC20.** Compatibility fixtures cover bare `spec/<slug>` work strings, bare shaping slugs, `{slug, type, needs}` shaping objects, brief-path strings, and comment-rich backlog entries.
- [ ] **AC21.** Every compatibility fixture is tagged legacy by the reader contract; a missing artifact or plan remains non-dispatchable, and no fixture reconstructs requirements from comments.
- [ ] **AC22.** Compaction fixtures refuse removal of a Shipped entry while any live `needs` edge or open parent references it, or while required closure evidence is absent. Allowed compaction never deletes the canonical artifact.
- [ ] **AC23.** Editing only comments, `summary`, or array order leaves the expected artifact classification and semantic dependency graph unchanged.
- [ ] **AC24.** `guides/core/reference/workspace-toml-schema.md`, `packs/core/seeds/workspace.toml`, and every contract example validate against the accepted schemas and use the same exact field names and TOML encoding.
- [ ] **AC25.** ADR-0077 and ADR-0078 are Accepted and back-linked before this spec is approved.

## Assumptions

- Technical: the shipped workspace read path remains Python 3.11+ and stdlib-only; development tests may use the repository’s existing `jsonschema` dependency (source: `packs/core/.apm/skills/workspace-status/SKILL.md` and `tools/requirements.txt`; user confirmation 2026-08-09).
- Technical: the JSON Schemas define normalized JSON representations, while TOML fixtures are parsed with `tomllib` before validation (source: `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`; user confirmation 2026-08-09).
- Technical: `workspace-mcp` continues to consume the canonical workspace engine rather than growing an independent classifier (source: `packages/agentbundle/agentbundle/workspace_mcp.py:_WorkspaceStatusTool.call`; user confirmation 2026-08-09).
- Product: a Ready brief with no specs is useful planning state and remains non-executable (source: RFC-0083 §7; user confirmation 2026-08-09).
- Product: legacy entries remain readable during migration but never become executable without canonical artifacts and human routing (source: RFC-0083 §10; user confirmation 2026-08-09).
- Process: this is full-mode work because it changes public contracts, crosses deserialization and filesystem boundaries, and is a prerequisite for dependent implementation groups (source: `AGENTS.md` § How we work; user confirmation 2026-08-09).
- Process: ADR-0077 and ADR-0078 are Accepted approval prerequisites (source: RFC-0083 Group 1; user confirmation 2026-08-09).
