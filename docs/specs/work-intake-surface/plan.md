# Plan: Work intake surface

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change as implementation teaches us. Substantial changes are
> recorded in the changelog.

## Approach

Land the router after the Group 2 schemas and Group 3 enforcement surface. Add `work-intake` and minimal intent materialization first; narrow `author-brief`, `receive-brief`, and `new-spec` into processors; align status and execution; replace `capture-work` with an alias; then close with shared routing evaluations and public documentation. Tests compare artifact, membership, processor, authority mode, and mutations at each boundary so classification cannot drift into processors.

## Constraints

- RFC-0083 defines routing, lifecycle, authority, compatibility, and documentation behavior.
- ADR-0077 and ADR-0078 are accepted approval prerequisites.
- `contracts/jsonschema/normalized-intake.schema.json` and `contracts/jsonschema/workspace-entry.schema.json` are consumed Group 2 contracts, not redefined here.
- Group 3 owns parser, reconciliation, status classification, and dispatch enforcement.
- `.apm/` is authoritative; `.agents/`, `.codex/`, and `.claude/` projections are generated.
- Shipped pack content carries no internal governance citations.
- A new core primitive requires a minor pack version bump and matching plugin version.
- No dependency is added.

## Construction tests

**Integration tests:**

- A normalized routing corpus covers start, remember, unavailable refresh, direct spec, multi-spec brief, minimal intent, defect, and ambiguity against both Group 2 schemas. Status has a separate read-only delegation fixture because it bypasses normalized intake.
- A core-only fixture proves no optional shaping skill is required.
- Alias-equivalence fixtures compare normalized requests, artifacts, and registrations.
- Ready-with-zero-spec and missing-spec/plan fixtures prove non-dispatchability.
- Hostile-source fixtures cover embedded instructions, secrets, personal data, and confidentiality mismatch across every visible output channel.

**Manual verification:**

- Follow the four published adopter-intent examples from a clean core-only install and record observed artifact, membership, processor, mutation result, and stop point in `docs/specs/work-intake-surface/manual-qa.md`; use a fresh temporary adopter workspace for each example.
- Inspect generated navigation and the built site for the canonical front door and compatibility-only alias.

## Design (LLD)

### Interfaces & contracts

`work-intake` consumes `contracts/jsonschema/normalized-intake.schema.json` and produces registrations conforming to `contracts/jsonschema/workspace-entry.schema.json`. It dispatches processors by name: `author-brief`, `receive-brief`, `new-spec`, `bug-fix`, `workspace-status`, and a configured refresh processor. The router owns classification; processors own artifact-specific behavior. Status is passed through unchanged.

Traces to: AC2–AC14 · both JSON Schemas.

### Failure, edge cases & resilience

Invalid normalized records, unsafe paths, missing processors, ambiguity, missing artifacts, unavailable refresh, unsafe redaction, and confidentiality mismatch fail closed before dispatch or mutation. Compatibility invocation passes through the same validation. Guarded Group 2/3 operations prevent partial materialize/register state.

Traces to: AC4–AC16 · both JSON Schemas.

### Dependencies & integration

The surface consumes Group 2 validation and Group 3 reconciliation/dispatch. Existing skills integrate by normalized input and named handoff, not path coupling or copied classification. Existing projection, eval, guide, and site mechanisms publish the surface.

Traces to: AC1–AC19 · both JSON Schemas.

## Tasks

### T1: Core-only `work-intake` routes normalized requests and materializes minimal intents

**Depends on:** spec:normalized-intake-workspace-contracts/T4, spec:workspace-routing-invariants/T4

**Touches:** `packs/core/.apm/skills/work-intake/**`, `packs/core/tests/skills/work-intake/**`

**Verification mode:** TDD for routing; goal-based integration checks for choreography.

**Tests:**

**Stub:** `packs/core/tests/skills/work-intake/test_work_intake.py` contains compilable failing `test_routes_canonical_inputs`, `test_rejects_unsafe_core_parent`, and `test_declares_minimal_boundaries` cases against the shipped Group 2 validator before production edits.

- Red fixtures cover all four adopter intents and canonical routes. Covers AC1–AC7.
- Boundary fixtures cover ambiguity, out-of-repository layout, embedded instructions, sensitive fields, and confidentiality mismatch. Covers AC5, AC7, AC15–AC16.
- Failure-injection fixtures cover artifact-write and registration-write
  failures, rollback, explicit non-dispatchable reconciliation, a safe
  repair-required terminal status when reconciliation persistence also fails,
  path traversal and symlink escape/loop refusal before callbacks, safe dispatch
  failure reporting, raw-exception suppression, and no processor dispatch from
  partial state.
  Covers AC20.
- A core-only fixture proves no optional pack resolution. Covers AC1, AC4.
- Boundary metadata tests require only `filesystem_write`, `filesystem_read_untrusted`, and applicable `network_fetch` actions. Covers AC19.

**Approach:**

- Add the `work-intake` skill, activation/behavior evals, fixtures, and minimal-intent asset.
- Consume the Group 2 schemas and encode the accepted classification tests.
- Define materialize-before-register sequencing, named dispatch, status pass-through, and unavailable-refresh behavior.

**Done when:** routing and boundary tests pass and all records validate against the Group 2 schemas.

### T2: Brief and spec processors preserve narrow artifact responsibilities

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/author-brief/**`, `packs/core/.apm/skills/receive-brief/**`, `packs/core/.apm/skills/new-spec/**`, `packs/core/tests/skills/receive-brief/**`

**Verification mode:** TDD for Ready/slice invariants; goal-based handoff evals.

**Tests:**

**Stub:** `packs/core/tests/skills/receive-brief/test_work_intake_processors.py` contains compilable failing `test_ready_brief_without_specs`, `test_only_confirmed_slices_materialize`, and `test_processor_boundary_metadata` cases against the shipped Group 2 contracts before production edits.

- Draft brief returns to intake without specs. Covers AC8.
- Ready brief with no spec-map rows creates no spec, plan, or work entry. Covers AC9.
- Only confirmed slices reach `new-spec`; direct and derived provenance differs correctly. Covers AC6, AC9–AC10.
- Changed processor actions declare minimal filesystem/network boundaries. Covers AC19.

**Approach:**

- Make `author-brief` an internal Draft materializer.
- Replace decomposition-dependent readiness with the accepted Ready gate.
- Keep deferred scope in the brief and pass normalized provenance to `new-spec`.

**Done when:** Ready-with-zero-spec and provenance tests pass.

### T3: Status and execution use Group 3 without duplicate routing

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/workspace-status/SKILL.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/tests/skills/workspace-status/**`, `packs/core/tests/skills/work-loop/**`

**Verification mode:** TDD for dispatch guards; goal-based status integration.

**Tests:**

**Stub:** `packs/core/tests/skills/workspace-status/test_work_intake_passthrough.py` and `packs/core/tests/skills/work-loop/test_work_intake_dispatch.py` contain compilable failing `test_status_passthrough`, `test_missing_contract_fails_closed`, and `test_consumer_boundary_metadata` cases against the shipped Group 3 surface before production edits.

- Intake status equals direct `workspace-status` structured output. Covers AC12.
- Missing spec/plan, Draft status, findings, and comment changes remain non-dispatchable. Covers AC11.
- A valid Approved spec/plan enters the claim path without reconstruction. Covers AC11.
- Changed read actions declare `filesystem_read_untrusted`; write/network permissions are absent unless the action uses them. Covers AC19.

**Approach:**

- Remove skill-level classification duplicated from Group 3.
- Resolve only structured spec paths and existing plans.
- Keep rendering, repair planning, and findings in `workspace-status`.

**Done when:** status pass-through matches and all invalid execution fixtures fail closed.

### T4: `capture-work` is a deprecating alias with no independent semantics

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/capture-work/**`, `packs/core/tests/skills/capture-work/**`

**Verification mode:** Goal-based integration checks.

**Tests:**

**Stub:** no stub (goal-based integration check).

- Both names yield identical normalized requests, artifacts, and entries. Covers AC14.
- The alias emits deprecation and never writes legacy state. Covers AC14.
- Static checks find no second classifier or direct writer. Covers AC14.
- The alias declares no broader boundary or allowed-tool set than `work-intake`. Covers AC19.

**Approach:**

- Replace the body with a thin name-based `work-intake` handoff.
- Preserve activation during compatibility and remove comment-backed writer instructions.

**Done when:** alias-equivalence and static checks pass.

### T5: Shared routing evaluations prove the complete core surface

**Depends on:** T2, T3, T4

**Touches:** `packs/core/.apm/skills/work-intake/evals/**`, `packs/core/.apm/skills/author-brief/evals/**`, `packs/core/.apm/skills/receive-brief/evals/**`, `packs/core/.apm/skills/new-spec/evals/**`, `packs/core/.apm/skills/workspace-status/evals/**`, `packs/core/.apm/skills/capture-work/evals/**`, `packs/core/tests/pack/**`, `packs/core/pack.toml`

**Verification mode:** Goal-based evaluation matrix.

**Tests:**

**Stub:** no stub (goal-based evaluation matrix).

- Assert artifact, membership, processor, and authority mode for every route. Covers AC1–AC16.
- Run Tier-A coverage for all affected skills.
- Replay identical state twice and compare results.
- Project every changed skill to each supported adapter and assert its minimal `metadata.boundaries` and allowed tools survive unchanged. Covers AC19.

**Approach:**

- Reuse Group 2/3 fixtures, add `work-intake` to `[pack.evals]`, and source guide examples from the same cases.

**Done when:** the full matrix passes twice deterministically.

### T6: Core release and public documentation expose the new front door

**Depends on:** T5

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/core/README.md`, `packs/core/DESIGN.md`, `packs/core/JOURNEY.md`, `packs/core/docs/index.md`, `packs/core/seeds/docs/product/**`, `guides/core/**`, `guides/README.md`, `docs/product/journeys/**`, `docs/architecture/overview.md`, `docs/product/changelog.md`

**Verification mode:** Goal-based catalogue/docs checks; manual cold-adopter walkthrough.

**Tests:**

**Stub:** no stub (goal-based catalogue/documentation checks with manual QA).

- Validate guide metadata, index, navigation, site build, and links. Covers AC17–AC18.
- Assert public guidance names the front door and marks the alias compatibility-only.
- Run a static construction check over every changed shipped pack surface for internal RFC/ADR/spec/AC and repository-only governance citations.
- Run catalogue lint/verify and self-host drift checks after version bumps.

**Approach:**

- Add the shared how-to, artifact explanation, and routing/lifecycle reference.
- Update affected pack, brief, spec, execution, status, architecture, and journey references.
- Bump core minor, match plugin version, regenerate projections, and add changelog.

**Done when:** all catalogue/docs gates pass and the four cold-adopter flows match expected state.

## Rollout

- **Delivery:** Ship after Group 2’s dual reader and Group 3’s fail-closed enforcement. Introduce `work-intake` and the alias together; new writes use only target state.
- **Rollback:** Revert the core writer release while retaining the prior dual reader. Keep all canonical artifacts.
- **Infrastructure:** None.
- **External integration:** Refresh stays unavailable until Group 6.
- **Sequence:** Group 1 decisions → Groups 2/3 → T1–T6. Group 7 owns removal after the compatibility gates.

## Risks

- Processors may retain competing routing rules.
- Ambiguity may accidentally appear ready.
- Ready-brief changes may create placeholders or conflict with coverage lint.
- The alias may preserve legacy semantics.
- Security prose may lack coverage across all output channels.
- Guides may rename the entry point while retaining old behavior.
- Implementing before Groups 2/3 stabilize may create schema drift.

## Changelog

- 2026-08-09: Initial full-mode plan from accepted RFC-0083 and confirmed assumptions.
- 2026-08-14: Closed pre-execution review gaps for realpath confinement, transactional registration, least-privilege declarations, materialized TDD stubs, status delegation, governance-citation checks, and manual-QA evidence.
- 2026-08-15: Added the fail-closed repair-required outcome for nested
  reconciliation-record failures and aligned AC20 with executable failure
  injection.
- 2026-08-15: Made route selection, confidentiality checks, confined target
  resolution, hostile-input output suppression, and dispatch failures
  executable review surfaces rather than prose-only contracts.
- 2026-08-15: Cold-adopter QA exposed a noncanonical minimal-intent preamble and
  an under-specified actor-plus-capability routing rule. Added parser round-trip
  coverage and pinned the published start example to the direct-spec route.
- 2026-08-15: Corrective cold-adopter QA exposed normalized `source.locator`
  leaking into the workspace-entry contract and an unconditional link to
  maintainer-only guidance. Added an explicit source mapping and fresh-install
  relative-link coverage before closing T6.
