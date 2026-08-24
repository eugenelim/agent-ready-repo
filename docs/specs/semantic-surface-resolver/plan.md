# Plan: Shared semantic-surface resolver

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `ARCHITECTURE.md` and `docs/architecture/work-intake-and-artifact-routing.md` own the intake boundary; `contracts/jsonschema/workspace-entry.schema.json` plus `tests/roster/test_workspace_entry_contract.py` are the published-contract precedent; `packs/core/.apm/skills/work-intake/scripts/intake_router.py` and `intake_transaction.py` plus their tests are the two analogous pure-routing and confinement implementations. Named deviation: the current workspace engine assumes every target has a repository path, so Wave 1 admits locator-only records but deliberately projects them as non-dispatchable until a later RFC-0096 wave owns execution semantics.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as implementation teaches us. Substantial
> changes are recorded in the changelog.

## Approach

Land one reader-first contract and resolver in four dependency-ordered tasks. First publish the resolution result schema and additive workspace path-or-locator extension with valid/invalid fixtures. Then implement a stdlib-only deterministic resolver beside `work-intake`, reusing the existing core confinement semantics and keeping discovery/adapters outside the helper. Next teach the typed workspace reader to preserve the optional surface metadata while refusing locator-only dispatch without reading a local artifact. Finally wire portable skill guidance, evaluation cases, release metadata, generated self-host projections, and the RFC-0096 Wave 1 completion matrix. No task adds lifecycle mutations or later-wave consumers.

The riskiest part is distinguishing “external and intentionally not a path” from “unsafe local path” without either localizing the external locator or weakening repository confinement. Contract fixtures and real filesystem tests establish that boundary before any consumer integration.

## Constraints

- RFC-0096 fixes the role model, six-rung resolution behavior, reporting fields, optional locator extension, authority separation, bounded discovery, external-locator treatment, and Wave 1 boundary.
- RFC-0083, ADR-0077, and ADR-0078 keep workspace state an index and preserve source authority/provenance.
- RFC-0093 and RFC-0094 keep completion/lifecycle and direct-light behavior unchanged.
- `contracts/jsonschema/*.schema.json` are published interfaces with bidirectional `x-spec` traceability.
- `workspace_status_engine.py` remains the canonical workspace reader; consumers do not gain a second parser.
- Core runtime code is Python 3.11+ stdlib-only and writes UTF-8 when it writes; this resolver is read-only.
- `.apm/` is authoring source. Self-hosted `.agents/`, `.codex/`, and `.claude/` content is generated, not edited directly.
- A core pack content change updates matching `pack.toml` and `plugin.json` versions and the affected evaluation harness.
- The active `okf-authoring-projection` work also expects to touch core version metadata; implementation must sequence or reconcile that manifest edit against the then-current value rather than overwrite it.
- No new dependency, top-level directory, mandatory config, registry, network adapter, closeout command, or lifecycle transition is admitted.

## Assumption trio

- **Files expected to change:** the two JSON Schemas; new resolution fixtures and roster contract tests; `work-intake` resolver source/tests/SKILL/evals; `workspace_status_engine.py` and focused parser/projection tests; workspace reference/current architecture/changelog; core version metadata and generated self-host projections; this spec, plan, README index, and `workspace.toml` lifecycle entry.
- **Tests that demonstrate done:** schema valid/invalid matrices; resolver precedence/confinement/authority tests; workspace path compatibility and locator-only refusal tests; work-intake eval/projection tests; full Wave 1 fixture matrix; core pack lint/verify and self-host drift checks.
- **Not changing:** artifact lifecycle/status transitions, `work-loop` completion behavior, source refresh, tracker acquisition/write-back, shaping handoff, architecture/ADR routing, close-work, cooling/retirement, migration, or any RFC-0096 Wave 2–7 surface.

## Declined additions

- **Temptation: add a global `[surfaces]` registry.** Declined because RFC-0096 makes configuration optional and repository policy/convention authoritative.
- **Temptation: create a shared package or new runtime dependency.** Declined because the core pack must remain portable and stdlib-only.
- **Temptation: make locator-only entries executable immediately.** Declined because that changes lifecycle/dispatch behavior owned by later waves.
- **Temptation: probe external locators for availability or writability.** Declined because Wave 1 is offline, authority-preserving, and evidence-based.
- **Temptation: fold closeout destinations into the resolver.** Declined because close-work and durable-output routing begin in later waves.

## Construction tests

**Integration tests:**

- Run every committed resolution fixture through JSON Schema validation and the Python resolver, normalize the result, and compare exact status, role, locator identity, provenance strength, confinement, availability/writability, authority, revision/fingerprint, confirmations, next action, and mutation trace.
- Parse legacy path-only, path-plus-surface, and locator-only workspace fixtures through both the schema oracle and `workspace_status_engine.py`; path-only semantics remain identical and locator-only stays non-dispatchable with `configuration_mismatch`.
- Project the changed core skill to supported adapters and run the same fixture subset against source and generated self-host copies.

**Manual verification:**

- Invoke the resolver module’s documented Python API in a temporary adopter repository for one explicit local, one custom convention, and one external case; record returned values and confirm the external case performs no local path/network operation.
- Run `work-intake` activation/evaluation cases and inspect that the shared resolver is selected only for semantic destination resolution, not lifecycle closeout.

## Design (LLD)

### Design decisions

- One closed `SurfaceCandidate` input and one closed `SurfaceResolution` output prevent each workflow from inventing precedence or authority semantics. Traces to: AC1–AC5, AC8–AC9, AC12.
- Candidate acquisition is outside the resolver. Repository guidance, optional adapters, and bounded analogue discovery normalize evidence first; the pure selection function never scans or fetches. Traces to: AC3–AC5.
- Canonical candidate identity is role + locator kind + canonical locator value. Equivalent aliases coalesce; non-equivalent peers remain ambiguous. Traces to: AC3, AC9, AC13.
- Local and external locators are disjoint tagged variants. Only the repository-path variant reaches confinement. Traces to: AC6–AC7.
- Locator-only workspace records are contract-valid but execution-ineligible in Wave 1. The current finding vocabulary communicates that missing integration without adding a lifecycle state. Traces to: AC10–AC11.

### Data & schema

`semantic-surface-resolution.v1` defines:

- resolution status: `resolved | confirmation-required | destination-required | refused`
- the thirteen semantic roles in AC2
- logical locator and tagged physical locator (`repository-path | external`)
- bounded provenance evidence with source and strength
- `available | unavailable | unknown` and `writable | read-only | unknown`
- `repository-confined | external | unknown` confinement
- independent source/write/delete authority facts
- optional revision/fingerprint, confirmations, stable code, and next action

Resolved results require the selected locators and complete facts. Non-resolved results prohibit selected locator/revision fields, retain only decision provenance, and make capability/confinement/authority facts explicitly `unknown` rather than omitting them or implying a destination.

`workspace-entry.v1` keeps every existing field and adds `surface_role` and a closed non-path `locator`. Existing `path` remains valid; at least one of `path` or `locator` is required; locator-only entries require `surface_role`. Traces to: AC1–AC2, AC8, AC10 · both JSON Schemas.

### Interfaces & contracts

- `surface_resolver.resolve_surface(repository_root, role, candidates) -> SurfaceResolution` is the only selection API.
- Candidate constructors distinguish explicit, policy/configuration, repository convention, and external evidence without giving caller prose executable meaning.
- `surface_resolver.render_safe_result(result)`, if needed by the skill surface, emits only schema fields and stable codes; exception text and raw candidate prose are absent.
- `workspace_status_engine.parse_workspace_entry` preserves optional surface metadata; canonical dispatch evaluation rejects an entry without a local `path` through `configuration_mismatch`.

Traces to: AC3–AC12 · `contracts/jsonschema/semantic-surface-resolution.schema.json` and `workspace-entry.schema.json`.

### Failure, edge cases & resilience

Closed dataclasses/schema reject unknown fields, oversized inputs, malformed roles, and invalid evidence. Mandatory-policy conflict stops selection. Path resolution catches `OSError`, `RuntimeError`, and `ValueError`; performs native realpath containment; and never exposes absolute paths or exceptions. External locators reject URL userinfo and query/fragment material without parsing them as filesystem paths. All failure outcomes are deterministic and read-only.

Traces to: AC4, AC6–AC9, AC11–AC13.

### Quality attributes (NFRs)

- **Security:** 100% of repository-path fixtures pass canonicalize-then-confine checks or a stable refusal; no external fixture reaches filesystem/network seams.
- **Determinism:** repeated clean-process runs over the completion matrix produce byte-identical normalized JSON.
- **Portability:** runtime uses Python 3.11 stdlib and repository-relative POSIX contract values; Windows drive/backslash cases fail closed.
- **Compatibility:** every pre-Wave-1 valid workspace fixture retains the same parse and dispatch classification.
- **Observability:** every non-resolved result has a stable code and safe next action; every resolved result carries all AC8 facts.

Traces to: AC6–AC14.

### Dependencies & integration

The resolver lives beside the existing `work-intake` router and transaction helpers, but neither helper calls it for lifecycle writes in Wave 1. `workspace_status_engine.py` consumes only the additive workspace fields. Contract tests use the repository’s development `jsonschema` dependency; runtime does not. Self-host projection carries changed skill source through the normal catalogue pipeline.

Traces to: AC5, AC10–AC14.

## Tasks

### T1: Resolution and workspace contracts accept every valid locator shape and reject every unsafe or ambiguous shape

**Depends on:** none

**Touches:** `contracts/jsonschema/semantic-surface-resolution.schema.json`, `contracts/jsonschema/workspace-entry.schema.json`, `packs/core/tests/pack/fixtures/semantic-surface-resolution/**`, `packs/core/tests/pack/fixtures/work-intake-contracts/workspace/target/**`, `tests/roster/test_semantic_surface_resolution_contract.py`, `tests/roster/test_workspace_entry_contract.py`

**Verification mode:** TDD

**Tests:**

**Stub:** materialize compilable red contract tests before production edits.

- Valid resolved fixtures cover local and external tagged locators and the complete AC8 result. Covers AC1–AC2, AC7–AC8.
- Non-resolved fixtures cover ambiguity, absence, refusal, confirmations, stable codes, next actions, prohibited selected-locator fields, decision provenance, and explicit unknown capability/confinement/authority facts. Covers AC9.
- Schema limits reject unknown fields, unknown roles/status/strengths, over-four result provenance records, credentials, queries/fragments, controls, and malformed local paths; `confirmation-required` requires at least one required confirmation. Covers AC1–AC7, AC9, AC12.
- Workspace fixtures cover path-only compatibility, path-plus-surface metadata, locator-only extension, missing both, locator without role, and unknown locator fields. Covers AC10.
- `x-spec` backlinks and spec `Contract:` links agree.

**Approach:**

- Author the resolution schema directly because no JSON Schema authoring skill is installed.
- Add `surface_role`/`locator` to the workspace schema with path-or-locator and locator-requires-role conditionals.
- Keep fixtures small, closed, generic, and free of internal RFC citations in shipped pack content.

**Done when:** both schemas validate, all valid fixtures pass, all invalid fixtures fail for the intended boundary, and all legacy workspace fixtures retain their prior oracle result.

### T2: The stdlib resolver deterministically applies precedence, authority reporting, and confinement

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-intake/scripts/surface_resolver.py`, `packs/core/tests/skills/work-intake/test_surface_resolver.py`, `packs/core/tests/pack/fixtures/semantic-surface-resolution/**`

**Verification mode:** TDD

**Tests:**

**Stub:** materialize failing tests for explicit precedence, policy refusal, equivalent collapse, ambiguity, absence, evidence bounds, local confinement, external zero-I/O, and independent authority before the implementation.

- Table cases cover every precedence rung and lower-rank suppression. Covers AC3.
- More than 32 candidates or more than four evidence records on any candidate is refused; one analogue stays inference; confirmed bounded convention resolves; contradictory mandatory policy refuses. Covers AC4–AC5, AC9.
- Real filesystem cases cover existing/missing in-root targets, absolute/traversal/backslash/drive input, symlink escape, and loop. Covers AC6.
- Patched `Path.resolve` and network/credential sentinels prove external locators never reach those seams. Covers AC7.
- Source/write/delete authority vary independently, and unknown remains unknown. Covers AC8, AC12.
- Invalid logical/physical locator, provenance, authority-evidence, confirmation-evidence, and workspace-source references cover credential, query/fragment, whitespace, and control-character shapes before any safe renderer consumes them. Covers AC7, AC12.
- Two clean subprocess runs produce byte-identical normalized results with empty mutation traces. Covers AC11–AC13.

**Approach:**

- Add frozen dataclasses/enums for candidates, evidence, authority facts, locators, confirmations, and results.
- Validate closed values before ranking.
- Canonicalize only local candidates and collapse equivalent identities before selecting.
- Return stable redacted refusal codes rather than exception data.

**Done when:** the resolver and fixture matrix are green and no test observes a write, network, shell, credential, or lifecycle callback.

### T3: Workspace readers preserve optional surface metadata without enabling locator-only dispatch

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, `packs/core/tests/skills/workspace-status/**`, `tools/test_workspace_status.py`, `tools/test_workspace_status_cli.py`, `packages/agentbundle/tests/test_workspace_mcp_tools.py`, `tests/roster/test_workspace_status_projection.py`

**Verification mode:** TDD and goal-based integration

**Tests:**

**Stub:** materialize a red parser/classification test for path-plus-surface preservation and locator-only `configuration_mismatch` before engine edits.

- Existing path-only corpus produces byte-identical canonical parse/dispatch output. Covers AC10–AC11.
- Path-plus-surface records preserve role/locator in typed and safe JSON projections without changing lifecycle classification. Covers AC10, AC12.
- Locator-only records perform no spec/path read, appear in blocked/findings, and never enter ready/active dispatch. Covers AC10–AC11.
- CLI/MCP/source-projection output contains no raw exceptions, absolute paths, credentials, or untrusted prose. Covers AC12.
- Status remains bounded and no Type 1/global scan is added.

**Approach:**

- Extend `WorkspaceEntry` with optional `path`, `surface_role`, and `locator` fields.
- Parse new fields against the closed contract; key membership safely when `path` is absent.
- Emit `configuration_mismatch` before artifact resolution for locator-only entries and reuse the existing next action.
- Preserve all lifecycle matrices and repair behavior.

**Done when:** legacy status tests stay green, locator-only fixtures are visible and fail closed, and no existing queue item changes classification.

### T4: The portable work-intake surface and release evidence expose Wave 1 without later-wave behavior

**Depends on:** T2, T3

**Touches:** `packs/core/.apm/skills/work-intake/SKILL.md`, `packs/core/.apm/skills/work-intake/evals/**`, `packs/core/tests/skills/work-intake/**`, `packs/core/tests/pack/**`, `guides/core/reference/workspace-toml-schema.md`, `docs/architecture/work-intake-and-artifact-routing.md`, `docs/product/changelog.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, generated self-host projections

**Verification mode:** Goal-based integration and manual API QA

**Tests:**

**Stub:** no stub (goal-based integration after T2/T3 TDD surfaces are green).

- Work-intake guidance states the precedence, bounded evidence, optional adapter, external-locator, authority, and confinement contract without internal governance citations. Covers AC3–AC12.
- Activation/eval cases exercise explicit, custom convention/configuration, external, ambiguity, and absence; later-wave closeout/cooling prompts remain near misses. Covers AC3–AC5, AC9, AC11.
- The committed completion matrix validates through schema, resolver, parser where applicable, and projected source comparison. Covers AC13.
- Core pack/plugin versions match; self-host generation is reproducible with zero diff on rerun; catalogue lint/verify and relevant core tests pass. Covers AC14.
- Manual API QA records explicit local, custom convention, and external results.

**Approach:**

- Add the resolver procedure to the existing work-intake surface without changing route/lifecycle tables.
- Document only the additive workspace fields and current fail-closed locator-only behavior.
- Update current architecture and changelog after implementation matches them.
- Bump the then-current core patch version once and regenerate projections through the canonical build.

**Done when:** Wave 1’s locator/evidence matrix is complete, all gates pass twice where determinism is claimed, and no diff names or implements RFC-0096 Waves 2–7.

## Rollout

- **Delivery:** additive reader-first release. Existing path-only repositories continue unchanged; new resolution callers may use the helper and schema immediately.
- **Infrastructure:** none.
- **External-system integration:** none; external locators are reported only.
- **Deployment sequencing:** T1 contract → T2 resolver and T3 reader (dependency peers after T1, executed sequentially by Phase 1 work-loop) → T4 portable release/evidence.
- **Rollback:** revert the additive schema/parser/resolver release. No migration or state mutation is required because Wave 1 writes no locator entries automatically.
- **Irreversible changes:** none.

## Risks

- Making `path` optional could accidentally turn a locator-only entry into a ready item through a legacy absence-based branch.
- A “safe external locator” validator could either admit credential-bearing URLs or reject legitimate opaque tracker schemes too aggressively.
- Filesystem availability/writability checks may become authority claims if the result contract does not keep those dimensions separate.
- One example may be promoted to a convention despite RFC-0096’s evidence rule.
- Projection tests may validate source while omitting the new resolver from an installed skill.
- Concurrent core version work may overwrite rather than increment the then-current manifest value.

## Resolve-vs-surface disposition record

| Discovery | Intent fit | Decision | Disposition |
| --- | --- | --- | --- |
| Existing core transaction helper already owns repository realpath confinement. | Matches | Include | Reuse its semantics; do not create a weaker path join. |
| Current workspace engine requires `path` for every target. | Matches | Include | Add optional locator parsing but keep locator-only non-dispatchable in Wave 1. |
| Active OKF work also plans a core version bump. | Matches process risk | Include as sequencing constraint | Read the then-current version immediately before the single Wave 1 bump; never overwrite another change. |
| Closeout, cooling, migration, and downstream workflow integration. | Does not match Wave 1 | Exclude | No implementation or durable follow-on is created by this spec. |

## Changelog

- 2026-08-23: Initial Wave 1 plan from accepted RFC-0096 and the confirmed JSON Schema + stdlib work-intake resolver shape.
