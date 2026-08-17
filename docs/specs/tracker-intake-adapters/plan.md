# Plan: Tracker intake adapters

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change as implementation teaches us. Substantial changes are
> recorded in the changelog.

## Approach

Pin one versioned semantic fixture matrix against the Group 2 schemas and completed Group 4 surface. Then update Jira, Jira Align, Linear, and GitHub as one dependency-independent wave. The installed Phase-1 supervisor runs that wave sequentially in task-ID order because parallel write fan-out is disabled. Each adapter keeps its acquisition mechanism but replaces direct brief creation and classification with normalized emission and a name-based `work-intake` handoff. A convergence task runs every common fixture through every profile, followed by pack release and tracker documentation. Convergence compares artifact, membership, processor, and authority rather than adapter prose. Manual guide QA records its durable evidence in `docs/specs/tracker-intake-adapters/notes/adapter-guide-walkthrough.md`; PLAN names but does not create that file.

## Constraints

- RFC-0083 defines content-based classification, profile hints, authority, trust boundaries, and the fixture matrix.
- The two not-yet-numbered Group 1 ADRs named in the spec are approval prerequisites.
- `contracts/jsonschema/normalized-intake.schema.json` and `contracts/jsonschema/workspace-entry.schema.json` are consumed Group 2 contracts.
- Group 4 `work-intake` owns classification, creation, registration, and processor selection.
- Group 6 owns refresh conflicts, execution locks, and write-back.
- Jira, Jira Align, and Linear retain sibling-skill acquisition; GitHub retains `gh`.
- Credential-bearing adapter-controlled HTTP profiles permit only `https`; trusted acquisition metadata, not tracker-authored text, supplies locator and revision.
- Adapter JSON input and output use strict RFC 8259 parsing and emission.
- Intake stays read-only, `.apm/` stays authoritative, and no dependency is added.

## Construction tests

**Integration tests:**

- Run one semantic corpus through all profiles and compare artifact, membership, processor, and authority.
- Validate normalized records and resulting registrations against both Group 2 schemas.
- Run malformed, missing-revision, unknown-profile, hostile-instruction, sensitive-data, and confidentiality fixtures through every adapter.
- Assert missing `work-intake` yields a named diagnostic and no local write.
- Assert no intake fixture invokes a tracker write.

**Manual verification:**

- Match every tracker guide example to a checked-in fixture.
- Build the site and follow direct-spec, multi-spec, collection, and defect examples.
- During EXECUTE, write `docs/specs/tracker-intake-adapters/notes/adapter-guide-walkthrough.md` with the checked scope, fixture inputs, rendered routes/results, session or run boundary, reviewer, and review date; do not create it during PLAN.

## Design (LLD)

### Interfaces & contracts

Each adapter translates tracker payloads into `contracts/jsonschema/normalized-intake.schema.json`, including profile ID/version, source locator/revision, object hint, action, required fields, constraints, and proposed authority. It invokes `work-intake` by name. Resulting registration conforms to `contracts/jsonschema/workspace-entry.schema.json`; adapters never author it.

Traces to: AC1–AC10, AC16, AC20–AC23 · both JSON Schemas.

### Failure, edge cases & resilience

Authentication failure stops acquisition. Malformed payload, absent provenance, unknown profile, unsafe redaction, confidentiality mismatch, and missing router fail closed without local writes. For adapter-controlled HTTP destinations, policy validates scheme, profile-scoped host allowlist, resolved addresses, redirect handling, and connect-time DNS identity before credentials are attached. GitHub is a separate fixed-host approved-`gh` boundary: adapter code accepts host selection only from trusted repository or administrator configuration, binds credentials to it, and rejects mismatched or payload-derived `--hostname`/URL arguments before invocation; redirect and DNS guarantees remain owned by `gh`. Profile budgets bound pages, items, bytes, timeouts, retries, and backoff; exhaustion returns deterministic marked truncation or view-only refusal. Ambiguous collections become separate units, view-only output, or a smallest-choice prompt. Embedded instructions remain inert; intake performs no external write.

Traces to: AC7–AC16, AC20–AC23 · normalized-intake schema.

### Dependencies & integration

Jira/Jira Align/Linear integrate through credentialed sibling skills; GitHub uses permitted `gh` reads. All converge on Group 4 `work-intake`. Group 6 later plugs refresh processors into the same public route without changing Group 5 ownership.

Traces to: AC1–AC23 · both JSON Schemas.

## Tasks

### T1: A shared profile and routing fixture matrix fixes the adapter contract

**Depends on:** spec:normalized-intake-workspace-contracts/T4, spec:work-intake-surface/T6

**Touches:** `packs/atlassian/.apm/skills/jira-brief-intake/evals/**`, `packs/atlassian/.apm/skills/jira-align-brief-intake/evals/**`, `packs/linear/.apm/skills/linear-brief-intake/evals/**`, `packs/github/.apm/skills/github-brief-intake/evals/**`, `tests/roster/test_tracker_intake_adapters.py`, `packs/atlassian/tests/skills/jira-brief-intake/test_jira_brief_intake.py`, `packs/atlassian/tests/skills/jira-align-brief-intake/test_jira_align_brief_intake.py`, `packs/linear/tests/skills/linear-brief-intake/test_linear_brief_intake.py`, `packs/github/tests/skills/github-brief-intake/test_github_brief_intake.py`

**Verification mode:** TDD for expected routes; goal-based JSON Schema validation.

**Tests:**

**Stub:** compilable red pytest stubs materialized during PLAN in `tests/roster/test_tracker_intake_adapters.py`: `test_common_routes_validate`, `test_ssrf_matrix_fails_before_credentials`, and `test_profile_budgets_are_deterministic`. T1 replaces the stubs with the shared harness and fixture assertions before adapter production edits.

- Common fixtures cover direct spec, multi-spec brief, cross-repo briefs, incoherent collection, and defect. Covers AC3–AC10.
- Boundary fixtures cover malformed input, missing revision, unknown profile, hostile instructions and shell metacharacters, sensitive data, confidentiality mismatch, adapter-controlled HTTP SSRF, discrete sibling-skill/GitHub argv, credential ordering, and profile budgets. Covers AC13–AC15, AC20–AC22.
- Expected normalized records validate before adapter work begins. Covers AC1–AC2.
- Projection fixtures define the minimal boundary/tool expectations later asserted for every changed skill. Covers AC23.

**Approach:**

- Define one semantic input/expected-route record reused by every profile.
- Keep tracker-specific raw payloads beside the common expected normalized form.
- Record artifact, membership, processor, authority, and no-mutation failure state.

**Done when:** the corpus is schema-valid and every profile has a raw fixture for every common case.

### T2: Jira intake emits normalized records and delegates every route

**Depends on:** T1

**Touches:** `packs/atlassian/.apm/skills/jira-brief-intake/**`, `packs/atlassian/.apm/skills/jira/**`, `packs/atlassian/tests/skills/jira-brief-intake/**`, `packs/atlassian/tests/skills/jira/**`

**Verification mode:** TDD for mapping; goal-based router integration.

**Tests:**

**Stub:** compilable red pytest stubs materialized during PLAN in `packs/atlassian/tests/skills/jira-brief-intake/test_jira_brief_intake.py`: `test_jira_normalizes_routes`, `test_jira_ssrf_precedes_credentials`, `test_jira_resource_budget`, and `test_jira_boundary_metadata`.

- Map Epic, Story/Task, board, sprint, JQL, and defect fixtures. Covers AC1–AC10.
- Assert `jira` is the only acquisition skill and no write verb occurs. Covers AC11–AC12.
- Assert hostile/sensitive and missing-router cases fail safely; tracker-derived CLI values use discrete argv or schema-validated data files with no shell. Covers AC13–AC16.
- Assert allowed schemes/hosts, blocked address classes, redirect/DNS behavior, and no credential-bearing request before validation. Covers AC20–AC21.
- Assert Jira maximum pages/items/bytes and timeout/retry/backoff yield deterministic marked truncation or view-only refusal. Covers AC22.
- Assert minimal boundary/tool declarations project unchanged. Covers AC23.

**Approach:**

- Replace object-to-brief identity with a versioned Jira profile.
- Retain flavor-aware reads through `jira`.
- Enforce the versioned Jira destination and resource-budget policy at the acquisition boundary.
- Remove direct artifact/workspace writes and delegate normalized input.
- Update manifest, examples, activation, and behavior evals.

**Done when:** Jira fixtures match common routes and static checks find no local writer or tracker write.

### T3: Jira Align intake emits normalized records and delegates every route

**Depends on:** T1

**Touches:** `packs/atlassian/.apm/skills/jira-align-brief-intake/**`, `packs/atlassian/.apm/skills/jira-align/**`, `packs/atlassian/tests/skills/jira-align-brief-intake/**`, `packs/atlassian/tests/skills/jira-align/**`

**Verification mode:** TDD for profile mapping; goal-based router integration.

**Tests:**

**Stub:** compilable red pytest stubs materialized during PLAN in `packs/atlassian/tests/skills/jira-align-brief-intake/test_jira_align_brief_intake.py`: `test_jira_align_normalizes_routes`, `test_jira_align_ssrf_precedes_credentials`, `test_jira_align_resource_budget`, and `test_jira_align_boundary_metadata`.

- Map Feature, child story/task/defect, cross-repo, and incoherent fixtures. Covers AC1–AC10.
- Require a profile version for organization mappings. Covers AC2, AC10, AC15.
- Assert `jira-align`-only reads, no writes, and safe hostile/missing-router behavior; tracker-derived CLI values use discrete argv or schema-validated data files with no shell. Covers AC11–AC16.
- Assert allowed schemes/hosts, blocked address classes, redirect/DNS behavior, and no credential-bearing request before validation. Covers AC20–AC21.
- Assert Jira Align maximum pages/items/bytes and timeout/retry/backoff yield deterministic marked truncation or view-only refusal. Covers AC22.
- Assert minimal boundary/tool declarations project unchanged. Covers AC23.

**Approach:**

- Convert field mapping from identity to versioned hints.
- Retain `jira-align` acquisition.
- Enforce the versioned Jira Align destination and resource-budget policy at the acquisition boundary.
- Remove direct brief/queue creation and local fallback routing.
- Update manifest and evals.

**Done when:** Jira Align fixtures validate and match equivalent common routes without local/external writes.

### T4: Linear intake emits normalized records and delegates every route

**Depends on:** T1

**Touches:** `packs/linear/.apm/skills/linear-brief-intake/**`, `packs/linear/.apm/skills/linear/**`, `packs/linear/tests/skills/linear-brief-intake/**`, `packs/linear/tests/skills/linear/**`

**Verification mode:** TDD for profile mapping; goal-based router integration.

**Tests:**

**Stub:** compilable red pytest stubs materialized during PLAN in `packs/linear/tests/skills/linear-brief-intake/test_linear_brief_intake.py`: `test_linear_normalizes_routes`, `test_linear_ssrf_precedes_credentials`, `test_linear_resource_budget`, and `test_linear_boundary_metadata`.

- Map Issue, sub-issue, Project, collection, cross-repo, and regression fixtures. Covers AC1–AC10.
- Prove type and item count do not decide brief identity. Covers AC7, AC10.
- Assert `linear`-only reads, no writes, and safe hostile/missing-router behavior; tracker-derived CLI values use discrete argv or schema-validated data files with no shell. Covers AC11–AC16.
- Assert allowed schemes/hosts, blocked address classes, redirect/DNS behavior, and no credential-bearing request before validation. Covers AC20–AC21.
- Assert Linear maximum pages/items/bytes and timeout/retry/backoff yield deterministic marked truncation or view-only refusal. Covers AC22.
- Assert minimal boundary/tool declarations project unchanged. Covers AC23.

**Approach:**

- Replace direct brief/queue writes with versioned profile output.
- Preserve field provenance and comparable revision for Group 6.
- Enforce the versioned Linear destination and resource-budget policy at the acquisition boundary.
- Keep sync behavior outside this task except a non-behavioral processor reference.
- Add Tier-A/behavior evals; T7 owns the pack-level `[pack.evals]` release declaration.

**Done when:** Linear fixtures match common routes without direct materialization or tracker writes.

### T5: GitHub intake emits normalized records and delegates every route

**Depends on:** T1

**Touches:** `packs/github/.apm/skills/github-brief-intake/**`, `packs/github/tests/skills/github-brief-intake/**`

**Verification mode:** TDD for profile mapping; goal-based router integration.

**Tests:**

**Stub:** compilable red pytest stubs materialized during PLAN in `packs/github/tests/skills/github-brief-intake/test_github_brief_intake.py`: `test_github_normalizes_routes`, `test_github_rejects_untrusted_hostname_before_gh`, `test_github_resource_budget`, and `test_github_boundary_metadata`.

- Map Issue, Milestone, incoherent milestone, cross-repo, and regression fixtures. Covers AC1–AC10.
- Assert approved `gh` reads are the only operations and anonymous/private ambiguity fails safely. Covers AC11–AC12.
- Assert hostile/sensitive and missing-router cases fail safely; every tracker-derived `gh` value remains a discrete argument with no shell. Covers AC13–AC16.
- With a fake `gh` argv sink, assert host selection comes only from trusted repository/administrator configuration, credentials stay bound to that host, payload/source-locator host values never reach argv, and mismatched or untrusted `--hostname`/URL input is rejected before `gh` is called. Do not assert that adapter code controls `gh` redirects or DNS. Covers AC20–AC21.
- Assert GitHub maximum pages/items/bytes and timeout/retry/backoff yield deterministic marked truncation or view-only refusal. Covers AC22.
- Assert minimal boundary/tool declarations project unchanged. Covers AC23.

**Approach:**

- Replace Milestone-to-brief identity with a versioned GitHub profile.
- Preserve existing auth posture and read-only acquisition.
- Document GitHub as a fixed-host approved-CLI trust boundary; construct `gh` argv only from the trusted configured host and normalized repository identifiers, never source text or source locators.
- Keep transport-level redirect and DNS guarantees assigned to approved `gh`, while enforcing all locally controllable host/credential/argv checks before invocation.
- Enforce the versioned GitHub resource-budget policy around `gh` output and pagination.
- Remove direct creation, local fallback routing, and intake write-back.
- Add Tier-A/behavior evals; T7 owns the pack-level `[pack.evals]` release declaration.

**Done when:** GitHub fixtures match common routes, fake argv proves trusted configured-host and credential binding with pre-invocation rejection of payload-derived or mismatched host/URL input, and the adapter invokes no write or direct artifact writer.

### T6: All profiles converge on identical semantic routing

**Depends on:** T2, T3, T4, T5

**Touches:** `packs/atlassian/.apm/skills/jira-brief-intake/evals/**`, `packs/atlassian/.apm/skills/jira-align-brief-intake/evals/**`, `packs/linear/.apm/skills/linear-brief-intake/evals/**`, `packs/github/.apm/skills/github-brief-intake/evals/**`, `tests/roster/test_tracker_intake_adapters.py`

**Verification mode:** Goal-based cross-profile integration matrix.

**Tests:**

**Stub:** no stub (goal-based cross-profile integration matrix).

- Compare artifact, membership, processor, and authority across profiles. Covers AC3–AC10.
- Run security/error, credential-ordering, and resource-budget cases across profiles; run full HTTP SSRF cases only where the adapter controls the destination, and GitHub fixed-host fake-argv cases at the approved-CLI boundary. Covers AC12–AC16, AC20–AC22.
- Replay identical inputs and assert deterministic results.
- Project every changed skill to each supported adapter and assert minimal boundary/tool declarations survive unchanged. Covers AC23.

**Approach:**

- Run against the real Group 4 router, not local classifiers.
- Fail profile-specific route differences unless substantive content differs.
- Record acquisition differences separately from route expectations.
- Report GitHub redirect/DNS assurance as owned by approved `gh`; assert only trusted configuration, credential binding, argv construction, and pre-invocation rejection locally.

**Done when:** all semantic cases converge, permitted routing divergence is content-based, adapter-controlled HTTP profiles pass the full SSRF matrix, and GitHub passes the fixed-host fake-argv matrix without claiming local redirect/DNS enforcement.

### T7: Tracker packs and public guidance ship converged behavior

**Depends on:** T6

**Touches:** `packs/atlassian/pack.toml`, `packs/atlassian/.claude-plugin/plugin.json`, `packs/atlassian/README.md`, `packs/linear/pack.toml`, `packs/linear/.claude-plugin/plugin.json`, `packs/linear/README.md`, `packs/github/pack.toml`, `packs/github/.claude-plugin/plugin.json`, `packs/github/README.md`, `.claude-plugin/marketplace.json`, `guides/_shared/how-to/choose-a-tracker-integration.md`, `guides/_shared/reference/tracker-vocabulary.md`, `guides/atlassian/**`, `guides/linear/**`, `guides/github/**`, `docs/product/journeys/pm-intakes-from-tracker.md`, `docs/architecture/overview.md`, `docs/product/changelog.md`, `docs/specs/tracker-intake-adapters/notes/adapter-guide-walkthrough.md`

**Verification mode:** Goal-based catalogue/docs checks; manual guide walkthrough.

**Tests:**

**Stub:** no stub (goal-based catalogue/documentation checks with manual QA).

- Assert current Tier-A and `[pack.evals]` declarations. Covers AC18.
- Validate guides, indexes, navigation, site build, and links. Covers AC17, AC19.
- Assert examples under `guides/_shared/**`, `guides/atlassian/**`, `guides/linear/**`, and `guides/github/**` resolve to checked-in fixtures. Covers AC17.
- Assert guides teach neither object-to-brief identity nor adapter classification/writes.
- Record manual QA in `docs/specs/tracker-intake-adapters/notes/adapter-guide-walkthrough.md`, including scope, fixture inputs, rendered routes/results, session or run boundary, reviewer, and date.
- Run catalogue lint/verify and self-host projection.

**Approach:**

- Document profile hints, content classification, shared routing, and Group 6 boundary.
- Update shared vocabulary, selection guidance, and the PM journey.
- Apply matching patch version bumps, regenerate projections, and add changelog.

**Done when:** catalogue/docs gates pass, every guide matches the convergence matrix, and `docs/specs/tracker-intake-adapters/notes/adapter-guide-walkthrough.md` contains the required scope, fixture inputs, rendered routes/results, session/run boundary, reviewer, and date.

## Rollout

- **Delivery:** Publish after Group 2 schemas and Group 4 router. All adapters write only normalized target state in the same catalogue release.
- **Rollback:** Revert adapter pack releases while retaining the shared dual reader; keep canonical artifacts.
- **Infrastructure:** None.
- **External integration:** Existing credentials/read APIs remain; no polling or webhook service.
- **Sequence:** Shared T1 → dependency-independent T2–T5 wave executed sequentially by the installed Phase-1 supervisor → convergence T6 → release/docs T7. Group 6 follows.
- **Compatibility:** Legacy state remains readable, but updated adapters never write it.

## Risks

- Tracker prose may preserve container-equals-brief semantics.
- Fixtures may hide meaningful content differences.
- Jira Align mappings may be unversioned.
- Linear provenance may omit a comparable revision.
- GitHub write-back may survive intake.
- Live credentials may be mistaken for required tests.
- Separate releases may expose incompatible adapter/router versions.
- Guides may preserve tracker ontology after behavior changes.

## Changelog

- 2026-08-09: Initial full-mode plan from accepted RFC-0083 and confirmed assumptions.
- 2026-08-16: Reconciled the approved plan with the shipped Phase-1 supervisor, named the shared roster harness, corrected task ownership, and materialized PLAN-time red stubs; added HTTPS-only, trusted-provenance, and strict-JSON security controls from pre-execution review.
