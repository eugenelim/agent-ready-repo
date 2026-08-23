# Plan: Work-intake migration, compatibility, and documentation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Freeze the RFC-acceptance legacy corpus first and define the lossless
`.workspace-migrations.json` ledger. Extend Group 3's reconciliation/repair
seams in two explicit layers: a read-only planner consumes a reviewed selection
file and names the owning artifact processor; apply/rollback then address one
operation ID, resolve fresh authorization, persist the ledger before workspace
mutation, and never author or delete canonical artifacts. Build an
evaluation-only cross-profile normalized record from the real Groups 2-6 seams,
then run a source-first documentation and navigation audit. The initial delivery
ends with the dual reader, target writers, migration and rollback tooling,
published guidance, routing evaluations, and a dated compatibility record.
Alias/legacy-reader removal is a distinct later task gated canonically by AC14
and the approved root-workspace backlog entry; neither can be satisfied by task
ordering alone.

## Constraints

- RFC-0083 fixes the supported legacy shapes, human-routing boundary,
  reader-first/write-new sequence, compatibility duration, rollback ownership,
  documentation surfaces, and removal gates.
- Approval requires the two accepted Group 1 ADRs named in `spec.md`.
- Group 2 owns `contracts/jsonschema/normalized-intake.schema.json` and
  `contracts/jsonschema/workspace-entry.schema.json`; this plan consumes them.
- Group 3 owns workspace parsing, reconciliation findings, fail-closed
  dispatch, and repair-plan/apply mechanics.
- Group 4 owns `work-intake` and the `capture-work` forwarding alias.
- Group 5 owns canonical cross-profile acquisition/routing fixtures; Group 6
  owns refresh-state fixtures.
- `contracts/jsonschema/work-intake-migration-manifest.schema.json` records
  the repository-root ledger and reversible operation facts only;
  `work-intake-migration-{selection,confirmation}.schema.json` govern the two
  human-authored inputs, and `work-intake-migration-result.schema.json` governs
  the CLI migration result object. None becomes another requirements store.
- RFC-acceptance compatibility is pinned only by
  `notes/legacy-source-inventory.md`; current working-tree shapes cannot expand
  T1 implicitly.
- `[authorization.migration]` is a closed role-only workspace table with
  `contract_version = "work-intake-migration-authorization.v1"` and
  `approver_roles`. Identity and approval evidence never persist in policy.
- Repository JSON Schemas are public authored contracts. Listing one in
  `contracts/README.md` does not by itself require an AgentBundle CLI data copy;
  the README must distinguish authored contract authority from explicitly
  bundled CLI data.
- `packs/core/seeds/docs/CONVENTIONS.md` is the source for projected
  `docs/CONVENTIONS.md`.
- `guides/` is the public source. `docs-site/src/content/docs/guides/`,
  generated `web/src/content/{packs,journeys}`,
  `.claude-plugin/marketplace.json`, and adapter projections are generated.
- No new dependency or top-level directory is introduced.
- Portable pack source does not import `agentbundle` package internals. Where
  migration confinement cannot reuse a runtime-resident helper, tests pin
  runtime-neutral behavior equivalent to
  `agentbundle.catalogue_tooling.file_safety` instead of accepting a shallow
  `realpath` prefix check.
- Alias removal is a major core-pack change and cannot land in the initial
  delivery.

## Construction tests

**Integration tests:**

- Run every accepted legacy fixture through parse → finding → reviewed
  selection → read-only plan → artifact-receipt check → authorized ledger-first
  apply → target reconciliation → authorized rollback → legacy reconciliation.
- Inject failures at ledger staging/replacement, workspace staging/replacement,
  and rollback. Assert only the reviewed legacy workspace (with any separately
  approved canonical artifact intact) or complete target workspace survives.
- Run the shared routing corpus across the supported Jira, Jira Align, Linear,
  and GitHub profiles and compare byte-normalized results across two clean
  workspaces.
- Generate the docs site from source, build web before docs-site, and verify
  canonical and alias routes.

**Manual verification:**

- Review one conversion proposal for each legacy shape and one
  unknown-extension refusal.
- Have the reviewer independently author one selection and separate apply and
  rollback confirmations from the emitted candidate/binding facts; confirm no
  migration command or skill creates or edits those inputs.
- Inspect a rollback transcript and confirm newly created canonical artifacts
  remain.
- Record the cold-reader pass in
  `docs/specs/work-intake-migration-docs/notes/adopter-route-walkthrough.md`,
  including scope, fixture/build inputs, observed routes/results, run/session
  boundary, reviewer, and date.
- Record the initial AC14/backlog evidence state in
  `docs/specs/work-intake-migration-docs/notes/initial-compatibility-review.md`
  with the same evidence fields. Deferred removal review remains unavailable
  and non-dispatchable from this plan.

## Design (LLD)

### Design decisions

Migration extends the existing reconciliation/repair surface rather than
adding a second workspace parser or public migration skill. The repository-root
`.workspace-migrations.json` file is a durable, schema-validated ordered
operation ledger because rollback must survive session loss. It records
representation changes, artifact receipts, and effect authorization evidence,
not requirements.
Documentation remains source-first, and the routing-evaluation corpus is
versioned beside the public `work-intake` behavior it measures.

The compatibility bridge and alias removal are separate release events. The
initial delivery deliberately retains both readers and the forwarding alias.
The later removal follow-up remains outside this executable task graph until
AC14 and the approved root-workspace backlog entry are satisfied.

Traces to: AC1-AC14, AC19-AC28 · implements
`contracts/jsonschema/work-intake-migration-manifest.schema.json`.

### Data & schema

The migration ledger contains a schema version, Group 3 canonical repository
identity, and ordered unique operations.
Each operation contains a stable operation ID; repository-relative workspace
path; pre-apply workspace fingerprint; exact legacy TOML slice and membership;
approved target entry and membership; owning processor; artifact receipt with
repository-relative path, confined fingerprint, and
`existed_before_apply = true`; operation/apply/rollback state; applied
fingerprint; and an ordered list of effect-attempt confirmation receipts
containing opaque ID, action, operation digest, opaque one-effect authorization
subject, digest of the matched policy role, time, authorization source, and
consumed-before-effect state. It
excludes source payloads and requirements.
The only durable operation progression is `pending → applied →
rollback_pending → rolled_back`; recovery may complete the next state but may
not skip or reverse one. The ledger is append-only by operation ID except for
those state/receipt transitions, and serialization preserves operation and
confirmation-receipt order. Recovery consumes a new fresh confirmation; a
receipt persisted before an interrupted effect is never reusable.
Its `contract_version` is `work-intake-migration-ledger.v1`.
Because JSON Schema cannot express uniqueness by a nested property or compare a
receipt with its containing operation, T2's
`validate_migration_ledger_invariants` runs after Schema validation and before
every read/effect. It implements the ledger's `x-semantic-invariants`: globally
unique operation IDs plus globally unique confirmation IDs and authorization
subjects, exact receipt operation binding, apply-before-rollback receipt order,
and state/receipt consistency.

The reviewed selection is a closed JSON input, not durable migration state. Its
`contract_version` is `work-intake-migration-selection.v1`; it contains only
the stable legacy finding ID, workspace
fingerprint, exact source collection/index/slice digest, selected target
Group 2 entry/membership, owning processor, provenance reference, and a human
`legacy_content_approved_for_ledger` attestation bound by the slice digest.
Unknown or missing fields refuse. The planner derives a stable operation ID and
operation digest from that content plus the confined artifact receipt.

Apply and rollback each consume a closed confirmation JSON file with
`contract_version = "work-intake-migration-confirmation.v1"`, opaque unique
`confirmation-<32 lowercase hex>` ID, action, operation ID/digest,
`authorization_subject = "subject-<32 lowercase hex>"`, approver role, RFC 3339
`confirmed_at`, and
`authorization_source = "current-human-session"`. The evidence must match the
current effect, be no more than five minutes old, and have an unused ID and
subject. Both opaque values are generated outside migration tooling from an
OS-backed CSPRNG; every documented helper uses `secrets.token_hex(16)` or an
equivalent OS-backed primitive, never `random`. The raw matched role is
transient; its lowercase SHA-256 digest is persisted in the accepted receipt so
replay refuses without retaining the role text.
Both selection and confirmation are human-authored out-of-band inputs.
`workspace-status`, its skill instructions, and other migration code may show
observed candidates plus the operation/action/digest binding, but may not
create, edit, prefill, or choose route/subject/role/timestamp values in either
file. The confirmation ID and subject are independently CSPRNG-generated,
one-effect-only, and globally unique across receipts; the parser rejects names,
emails, usernames, account IDs, and organization-specific identifiers in both
fields by accepting only their closed opaque patterns. This is an autonomy boundary: a
malicious local writer remains outside
the threat model because that principal can already edit the protected files
directly.

All fingerprints and digests use lowercase SHA-256 over bytes. Canonical
operation material uses UTF-8 JSON with sorted keys and compact separators.
The persisted authorization-role digest is lowercase SHA-256 over the exact
UTF-8 bytes of the policy-matched role slug. Policy slugs come only from the
closed public, non-sensitive capability vocabulary `migration-approver`,
`repository-maintainer`, and `security-approver`; the digest is an integrity
binding, not a claim that a sensitive low-entropy role can be anonymized.
`operation_id` is the full selection-material digest prefixed with
`migration-`; `operation_digest` covers that selection plus the current
artifact receipt. Existing Group 3 workspace/plan fingerprint conventions are
reused rather than introducing a second encoding.

The exact legacy slice preserves comments and punctuation that parsed TOML
cannot round-trip. Apply validates the target entry against the Group 2
workspace-entry Schema. Rollback validates the applied fingerprint and restores
only the recorded slice; canonical artifacts are never rollback targets.

Traces to: AC1-AC10 · implements the four migration Schemas and consumes the
existing Group 2 JSON Schemas.

### Interfaces & contracts

`workspace-status` reconciliation emits typed legacy findings. `repair-plan
--migration-selection <path>` validates a schema-closed selection file and
emits a read-only proposed operation; without that option it retains the
existing Type 2 cleanup contract. A missing artifact returns the owning
processor as `next_action` and cannot become applicable. `repair-apply
--migration-selection <path> --operation-id <id> --confirmation-file <path>`
revalidates the selection, artifact receipt, policy, current-session
confirmation, ledger, and workspace fingerprint, writes the ledger first, then
performs the guarded conversion.
`repair-rollback --operation-id <id> --confirmation-file <path>` is the sole
rollback writer and refuses stale or already-diverged state.
Exit/output shapes stay deterministic, redacted, and machine-readable.
Migration plan/apply arguments are mutually exclusive with the existing Type 2
`--plan-file`/`--yes` mode; partial or mixed argument sets refuse before reads
or writes. With no migration arguments, Type 2 behavior is byte-compatible.
Migration branches retain the existing `schema_version = 1` and `mode`
envelope and add a `migration` object validating against
`work-intake-migration-result.schema.json` with
`contract_version = "work-intake-migration-result.v1"`, exact snake_case field
names, and the per-result requirements in that Schema. Exit bands remain 0 for
a completed result/idempotent no-op,
1 only for the Schema-valid `workspace_absent` result, and 2 for invalid,
unsafe, stale, unauthorized, or failed execution. Stdout is JSON only; stderr
is bounded and never echoes input.

`capture-work` remains a public alias into `work-intake` during the window and
emits a deprecation notice. It owns no routing behavior. The initial delivery
records a non-dispatchable backlog anchor for a later human-approved removal
artifact instead of scheduling removal here.

Migration authorization resolves from the closed role-only
`[authorization.migration]` repository policy; alias-removal
authorization resolves from RFC-0083's Approver metadata. Both are
check-before-effect. Migration persists only opaque confirmation ID and
authorization subject, the matched-role digest, timestamp, and source;
compatibility evidence records the RFC's public Approver fields. Missing,
ambiguous, stale, or insufficient authorization rejects before mutation.

Traces to: AC2-AC14, AC25, AC27-AC28 · implements the four migration Schemas
and consumes the workspace-entry Schema.

### State & control flow

A legacy entry moves through:

`detected → non-dispatchable finding → reviewed selection → read-only plan →
artifact processor/receipt → authorized ledger pending → conversion applied →
target reconciled`.

Failure before complete apply leaves the legacy workspace and any separately
approved canonical artifact intact. A completed apply may move through
`applied → rollback_pending → rolled_back`; canonical artifacts remain.
Unknown extensions stop at a manual finding.

Apply and rollback serialize through Group 3's shared `.workspace-repair.lock`.
Apply re-reads and fingerprints the ledger, workspace, selection, and artifact
inside that lock. Rollback has no selection input: it re-reads the ledger and
workspace, validates the recorded applied fingerprint plus fresh confirmation,
and treats the canonical artifact as an untouched independent object. A
mismatched concurrent writer receives a stable refusal instead of a
last-writer-wins update.

Compatibility progresses independently:

`initial compatibility evidence → approved non-dispatchable backlog anchor →
AC14 predicates satisfied → later human-approved planning → removal`.

Traces to: AC2-AC14, AC20.

### Behavior & rules

Only the human-selected artifact kind controls conversion. Comments and
summary are display evidence, never classifiers. Missing artifacts remain
findings whose next action names the owning processor; migration code never
authors them. Unknown extensions remain unchanged. New writers always emit
target entries. Removal remains fail-closed until both canonical sources—AC14
and the approved root-workspace backlog entry—are satisfied.

Traces to: AC2-AC5, AC11-AC14, AC17, AC23-AC25.

### Failure, edge cases & resilience

Runtime-neutral file-safety semantics prevent workspace, ledger, selection, or
artifact-receipt paths from leaving the repository or crossing unsafe link-like
files. Fingerprints prevent an approved plan from overwriting later edits.
Operation IDs and ledger state make apply/rollback idempotent. A durable pending
operation is recovered deterministically; unknown entries and malformed ledgers
fail closed. Generated docs are rebuilt, never repaired in place.

Before ledger staging, a bounded credential-pattern scan runs only over the
exact legacy slice. A match or missing slice-digest-bound human privacy
attestation returns a stable manual-sanitation refusal, never the matched text.
The slice stays solely in its legacy source until the gate passes.
The exact raw-byte handling, regex classes, no-override policy, and no-echo
result are owned by
`notes/credential-detector-contract.md`; implementation and fixtures reference
that note rather than copying its vocabulary into this revisable plan.

A clock or release gate that cannot be proven is false. An incomplete audit,
authorization failure, or missing Approver decision retains the alias. Rollback
during the window returns writers to the previous dual-reader release and
never removes target artifacts.

Traces to: AC4-AC14, AC21-AC25.

### Quality attributes (NFRs)

Determinism is checked by byte-equivalent evaluation-only normalized results
across two clean runs. Safety is checked by failure injection,
stale-fingerprint refusal, path-confinement tests, and zero artifact authoring
or deletion by migration code. Documentation completeness is checked by
explicit source, route, link, build, and semantic-search gates. Privacy is
checked across the ledger, stdout, stderr, and logs.

Traces to: AC7-AC10, AC17, AC20-AC24.

### Dependencies & integration

The implementation consumes the complete Group 2-6 chain. Migration relies on
Group 2 encodings, Group 3 findings/repair, Group 4 writers/alias, Group 5
profile convergence, and Group 6 authority/refresh fixtures. Public docs are
built by `tools/build-site.py`; site order remains web then docs-site. Pack
metadata and projections follow the catalogue version/self-host rules.

Rollout sequencing and the externally gated removal are defined in
`## Rollout`.

Traces to: AC1-AC28 · implements the four migration Schemas and consumes the
two upstream Group 2 Schemas.

## Tasks

### T1: Legacy fixtures and the four migration Schemas validate

**Depends on:** spec:normalized-intake-workspace-contracts/T4, spec:workspace-routing-invariants/T4, spec:work-intake-surface/T6, spec:tracker-intake-adapters/T7, spec:tracker-refresh-writeback/T6

**Implements:** the versioned legacy/ledger contract foundation in AC1, AC5-AC7, AC28.

**Review shape:** DEEP foundation layer, kept below 2,000 reviewable behavior/test lines.

**Touches:** contracts/jsonschema/work-intake-migration-manifest.schema.json, contracts/jsonschema/work-intake-migration-selection.schema.json, contracts/jsonschema/work-intake-migration-confirmation.schema.json, contracts/jsonschema/work-intake-migration-result.schema.json, contracts/README.md, docs/specs/work-intake-migration-docs/notes/legacy-source-inventory.md, docs/specs/work-intake-migration-docs/notes/credential-detector-contract.md, packs/core/tests/skills/workspace-status/fixtures/work-intake-migration/**, tools/test_workspace_status.py, tools/test_workspace_status_cli.py

**Verification mode:** TDD

**Tests:**

**PLAN stub gate:** after separate spec approval and before production edits,
materialize compilable red tests in `tools/test_workspace_status.py` and
`tools/test_workspace_status_cli.py` plus fixture-validation tests under
`packs/core/tests/skills/workspace-status/`, each marked `STUB: AC...`; record
`stub: true` in the work-loop task state. Draft authoring intentionally commits
no red stubs, per `new-spec` step 4. The four migration Schemas are authored
spec contracts; T1 validates/finalizes them and adds no conversion logic.

`stub: true` — AC1, AC5-AC7, and AC28 contract stubs are materialized in the
declared workspace-status fixture/test surfaces and compile under pytest.

- Add one exact fixture for each RFC-supported legacy shape and
  malformed/missing-artifact variants. Verifies AC1-AC4.
- Add unknown/private-extension fixtures and assert byte-stable manual
  findings. Verifies AC5.
- Add valid/invalid ledger fixtures for ordered unique operations, every
  required field, path form, fingerprint, artifact receipt with the required
  existed-before-apply fact, ordered consumed confirmation receipts, and
  operation state. Verifies AC6-AC7, AC25.
- Add schema-valid but semantically invalid fixtures for duplicate operation
  IDs, cross-operation duplicate confirmation IDs or authorization subjects,
  mismatched receipt bindings,
  rollback state without a rollback receipt, apply-after-rollback order, and
  skipped/reversed state. Verifies AC6, AC9, AC25.
- Assert the ledger Schema publishes the exact four `x-semantic-invariants`
  rules/codes consumed by T2 rather than leaving cross-record validation in
  plan prose. Verifies AC6, AC28.
- Add valid/invalid selection, confirmation, and migration-result fixtures for
  their closed field sets, exact versions/bindings, per-result requirements,
  privacy attestation, freshness, and unknown fields. Confirmation fixtures
  accept only opaque `confirmation-<32 lowercase hex>` and
  `subject-<32 lowercase hex>` forms and reject names, emails, usernames,
  account IDs, and organization identifiers in those fields. Ledger fixtures
  contain only the role digest, never raw role text; result fixtures include
  the exact `workspace_absent` exit-1 outcome. Verifies AC3, AC7, AC25, AC27.
- Add a contract inventory/back-pointer check that distinguishes public authored
  Schemas from explicit AgentBundle CLI data copies. Verifies AC28.

**Approach:**

- Copy the released acceptance-time representations into a versioned fixture
  corpus without normalizing punctuation or comments.
- Derive the exact legacy fixture set only from the pinned ref and
  `notes/legacy-source-inventory.md`; make the test fail if any inventoried
  source path is absent at that ref or an accepted representation is unpinned.
- Validate and, only where construction tests expose a contract defect, refine
  the authored JSON Schemas for the repository-root ledger, reviewed selection,
  effect confirmation, and migration result. T2 owns their runtime-neutral
  validators and types.
- Verify the authored migration contracts and existing Group 2 contracts remain
  inventoried in `contracts/README.md` with owning specs and truthful bundling
  labels.
- Use repository-relative paths and fixed digest/operation-state vocabularies.

**Done when:** all accepted shapes are pinned, unknown extensions are
characterized, and all four migration-contract validation suites pass without
implementation conversion logic.

### T2: Migration planning is deterministic, read-only, and human-selected

**Depends on:** T1

**Implements:** the Objective's reviewable non-dispatchable finding and read-only planning outcomes in AC2-AC4, AC7-AC8, AC20, AC27.

**Review shape:** DEEP planning layer, kept below 2,000 reviewable behavior/test lines.

**Touches:** packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py, packs/core/.apm/skills/workspace-status/scripts/workspace_status.py, packs/core/.apm/skills/workspace-status/SKILL.md, packs/core/tests/skills/workspace-status/**, tools/test_workspace_status.py, tools/test_workspace_status_cli.py, packages/agentbundle/agentbundle/_data/workspace_status_engine.py, tests/roster/test_workspace_status_projection.py

**Verification mode:** TDD

**Tests:**

**PLAN stub gate:** after separate spec approval and before production edits,
materialize compilable red tests in
`packs/core/tests/skills/workspace-status/test_workspace_status_engine_autonomous.py`,
`tools/test_workspace_status.py`, `tools/test_workspace_status_cli.py`, and the
projection test, each marked `STUB: AC...`; record `stub: true` in work-loop
task state. T2 implements runtime-neutral contract validators, selection parser,
and migration-plan types; there is no T1 Python module.

`stub: true` — AC2-AC4, AC7-AC8, AC20, and AC27 planner/projection stubs are
materialized in the declared engine, CLI, autonomous, and projection tests.

- Assert each legacy shape produces a typed non-dispatchable finding with exact
  source, membership, candidate routes, and smallest safe next action. Verifies
  AC2-AC5.
- Assert the legacy engine projects the exact source TOML slice, including
  collection delimiters, punctuation, whitespace, and adjacent comments,
  rather than reconstructing it from parsed values. Verifies AC2, AC10.
- Assert no plan exists until a closed selection JSON supplies the exact legacy
  finding ID, workspace fingerprint, source collection/index/slice digest,
  complete Group 2 target entry/membership, processor, provenance reference,
  and positive privacy attestation bound to the slice digest; reject
  unknown/missing fields and route/finding mismatches. Verifies AC3-AC4, AC7.
- Assert plans validate target entries against the Group 2 Schema and reject
  out-of-repository paths, symlink escape, duplicates, stale provenance, or
  impossible membership. Verifies AC7-AC8.
- Assert planning uses repository-relative identity, strictly resolves its
  root, refuses absolute/backslash/`..`, symlink, reparse-point, and hard-link
  escape, and fails closed on `OSError`, `RuntimeError`, or resolution errors
  without importing `agentbundle` package internals. Verifies AC7.
- Assert planning is purely read-only: no migration-policy requirement, ledger
  write, workspace write, or artifact creation. A missing artifact returns the
  owning processor as `next_action`; an existing artifact yields a confined
  fingerprint receipt and an applicable stable operation ID/digest. Verifies
  AC3-AC4, AC7-AC8, AC25, AC27.
- Assert planner/CLI/skill code can emit observed candidates and exact binding
  facts but has no path that creates, edits, prefills, or chooses values in a
  selection or confirmation file. Verifies AC3, AC25-AC27.
- Run planning twice and assert byte-equivalent normalized output. Verifies
  AC20.
- Assert the existing v1 CLI envelope plus closed migration object, planner
  result-code subset, exit bands, JSON-only stdout, and bounded non-echoing
  stderr exactly match AC27. Verifies AC27.
- Assert the `.apm` engine and packaged AgentBundle projection remain
  byte-identical after the source change. Verifies AC24.
- Assert `validate_migration_ledger_invariants` accepts valid T1 ledgers and
  returns the exact semantic-invariant code for every schema-valid invalid
  fixture before any caller may select an operation. Verifies AC6-AC7, AC25.

**Approach:**

- Extend Group 3's finding and repair-plan types with legacy migration
  operations.
- Implement the runtime-neutral migration contract parsers plus
  `validate_migration_ledger_invariants`; JSON Schema shape validation always
  precedes semantic-invariant validation.
- Keep route selection outside heuristics; comments may appear as quoted
  review context only.
- Build a proposed ledger operation from the exact fixture slice, reviewed
  target, and confined artifact receipt, but emit it only as normalized output.
- Reuse existing CLI JSON/result conventions and exit bands.

**Done when:** every supported legacy fixture produces the same safe read-only
plan or finding on repeated runs, missing artifacts identify their processor,
and no plan infers a route or creates durable state.

### T3: Apply and rollback survive interruption without deleting artifacts

**Depends on:** T2

**Implements:** the Objective's authorized ledger-first conversion and exact rollback outcomes in AC6-AC10, AC25-AC27.

**Review shape:** DEEP mutation layer, kept below 2,000 reviewable behavior/test lines; split apply and rollback into separate tasks if construction exceeds that bound.

**Touches:** packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py, packs/core/.apm/skills/workspace-status/scripts/workspace_status.py, packs/core/.apm/skills/workspace-status/SKILL.md, packs/core/tests/skills/workspace-status/**, tools/test_workspace_status.py, tools/test_workspace_status_cli.py, packages/agentbundle/agentbundle/_data/workspace_status_engine.py, tests/roster/test_workspace_status_projection.py

**Verification mode:** TDD

**Tests:**

**PLAN stub gate:** after separate spec approval and before production edits,
materialize compilable red apply/rollback and failure-injection tests under
`packs/core/tests/skills/workspace-status/`, `tools/test_workspace_status.py`,
`tools/test_workspace_status_cli.py`, and the projection test, each marked
`STUB: AC...`; record `stub: true` in work-loop task state.

`stub: true` — AC3, AC6-AC10, AC25, and AC27 effect/recovery stubs are
materialized in the declared pack, engine, CLI, and projection tests.

- Inject failure before/after ledger stage, ledger replace, workspace stage,
  and workspace replace. Assert migration code never invokes an artifact writer.
  Verifies AC8-AC9, AC25.
- Re-run apply against no-ledger pre-state, durable-pending ledger state,
  complete target state, stale state, and partially recovered state; assert no
  duplicate entry or operation and deterministic pending recovery using a new
  confirmation ID. Verifies AC9, AC25.
- Roll back every accepted legacy shape and assert exact legacy
  slice/membership restoration, comment preservation, and canonical artifact
  retention. Verifies AC10.
- Assert stale fingerprints, out-of-repo/symlink paths, and malformed ledgers
  refuse without mutation; changed artifacts block apply but do not block a
  guarded rollback that never reads or mutates them. Verifies AC7-AC10.
- Assert ledger/workspace reads and fingerprints perform pre/post-open
  regular-file checks, write targets validate confined parents, link-like or
  multiply linked files refuse, and path-resolution failures have zero
  effects. Verifies AC7-AC10.
- Assert apply and rollback each re-resolve the repository migration role,
  validate a closed confirmation bound to the exact operation ID/digest and
  action, record only the opaque one-effect confirmation ID and subject, role
  digest, timestamp, and source, never copy the raw role into the ledger, and
  reject names, emails, usernames, account/org identifiers in opaque fields,
  missing, ambiguous, future, older-than-five-minutes, reused, mismatched, or
  insufficient authorization before any effect. Verifies AC3, AC10, AC25.
- Assert migration code never generates opaque evidence and imports no
  non-cryptographic RNG; every documented human generation command uses an
  OS-backed CSPRNG such as `secrets.token_hex(16)`. Verifies AC25.
- Assert `repair-apply` requires selection, operation ID, and confirmation file;
  `repair-rollback` requires operation ID and a distinct confirmation file; and
  partial/mixed migration plus Type 2 arguments refuse while existing Type 2
  behavior is byte-compatible without migration arguments. Verifies AC27.
- Exercise every apply/rollback refusal and success code in AC27 and assert its
  exact envelope, exit band, mutation flag, and redacted stderr behavior.
  Verifies AC7, AC27.
- Assert each accepted confirmation appends its opaque ID and subject, action,
  operation digest, matched-role digest, and consumed-before-effect receipt to
  the ledger before the guarded effect; crash recovery requires a new receipt
  and cross-action, same-ID, or same-subject replay refuses. Verifies AC6, AC9,
  AC25.
- Assert `validate_migration_ledger_invariants` runs after Schema validation and
  before every ledger read/effect, rejecting every `x-semantic-invariants`
  fixture with the stable code and zero mutation. Verifies AC6-AC9, AC25.
- Assert stdout, stderr, and logs contain no prohibited data. Verifies AC7.
- Assert credential-shaped content or a missing/mismatched human privacy
  attestation refuses before ledger staging, never echoes matched text, and
  leaves the legacy source byte-stable for manual sanitation. Cover every
  closed regex class, casing, line-ending preservation, near misses, and the
  no-override false-positive policy. Verifies AC7.

**Approach:**

- Parse `[authorization.migration]` as the closed role-only v1 contract and
  accept only the three public capability labels named by the spec; reject any
  subject/identity/evidence field or person/team/account/organization label in
  policy.
- Treat selection and confirmation paths as human-supplied read-only inputs;
  migration code opens neither for write and the skill pauses for the human to
  author each file out of band.
- Persist and fsync/replace the repository-root ledger's pending operation
  before workspace conversion; after conversion, persist the applied state and
  fingerprint. Recover a matching pending operation by inspecting guarded
  workspace state, never by recreating an artifact.
- Reuse comment-preserving guarded mutation from Group 3.
- Record the externally produced artifact receipt and its pre-existence fact;
  rollback never deletes either pre-existing or newly created artifacts.
- Make operation state transitions monotonic and compare fingerprints before
  every write.

**Done when:** the full ledger-first apply/rollback matrix and every
failure-injection case pass, pending operations recover deterministically,
confirmations are fresh/single-use/exactly bound, and migration code neither
authors nor deletes artifacts.

### T4: The cross-profile routing evaluation matrix converges

**Depends on:** T2

**Implements:** the Objective's cross-profile routing-evaluation outcome in AC19-AC20, AC24.

**Review shape:** WIDE fixture/evaluation layer; canonical JSON byte comparison and paired pack/plugin version assertions are its reproducibility proof.

**Touches:** packs/core/.apm/skills/work-intake/evals/evals.json, packs/core/.apm/skills/work-intake/evals/eval_queries.json, packs/core/.apm/skills/work-intake/evals/files/routing/**, packs/atlassian/.apm/skills/**/evals/**, packs/github/.apm/skills/**/evals/**, packs/linear/.apm/skills/**/evals/**, packs/{core,atlassian,github,linear}/pack.toml, packs/{core,atlassian,github,linear}/.claude-plugin/plugin.json, packs/core/tests/pack/test_work_intake_surface.py, tests/roster/test_tracker_intake_adapters.py, tests/roster/test_tracker_refresh_lifecycle_matrix.py, tests/roster/test_work_intake_refresh_coordinator.py, tests/roster/test_{jira,jira_align,linear,github}_refresh_processor.py, tools/test-run-pack-evals.py

**Verification mode:** TDD and goal-based check

**Tests:**

**PLAN stub gate:** after separate spec approval and before production edits,
materialize compilable red matrix tests in the exact core/roster files named by
`Touches`, each marked `STUB: AC19` or `STUB: AC20`, and record `stub: true` in
work-loop task state. Group 4-6 router/profile/refresh implementations already
exist; T4 composes them with T2's read-only migration planner and adds no
runtime normalized-result contract.

`stub: true` — AC19-AC20 matrix stubs are materialized across the
declared core and roster test surfaces; the remaining eval files are populated
during T4's WIDE fixture pass.

- Add direct-spec, multi-spec brief, cross-repo, incoherent collection/view,
  defect, remember, and status fixtures. Verifies AC19.
- Add Draft, Accepted, Ready, Approved, Implementing, Executing, and Shipped
  refresh fixtures from Group 6. Verifies AC19.
- Add a migration fixture that invokes T2's actual read-only planner and
  normalizes its `result_code`, applicability, and next action; do not model
  apply/rollback as tracker-profile routing. Verifies AC19.
- Assert the evaluation-only record's case/profile/version, artifact kind/path,
  lifecycle membership, processor, authority mode, dispatchability, result
  code, and next action across Jira, Jira Align, Linear, and GitHub. Verifies
  AC19-AC20.
- Acquire/normalize profile input, invoke the actual Group 2-6 engines in two
  independently created clean roots, and compare canonical JSON bytes rather
  than serializing one expected object twice. Verifies AC19-AC20.
- Add near-miss activation cases separating intake, status/triage, refresh,
  defect, and migration intents.

**Approach:**

- Keep canonical expected routing in the core `work-intake` eval corpus.
- Let profile fixtures supply only versioned source mappings and capabilities.
- Use the actual Group 2 schemas and Group 3-6 engines rather than duplicating
  expected logic in the runner.
- Implement normalization in evaluation/test support only; production `Route`,
  refresh result, and adapter contracts remain independently owned.
- Bump each changed pack and matching Claude plugin manifest together as
  required by scoped pack instructions.

**Done when:** the complete matrix passes across every supported profile and
two clean runs produce identical results and next actions.

### T5: Adopter documentation teaches one current route

**Depends on:** T2, T4

**Implements:** the Objective's adopter discovery and consistent route outcomes in AC15-AC17, AC21-AC23.

**Review shape:** WIDE source-first documentation retrofit; semantic-search inventory, route walkthrough, and generated-site gates are its reproducibility proof.

**Touches:** guides/_shared/how-to/use-work-intake.md, guides/_shared/explanation/work-artifact-responsibilities.md, guides/_shared/reference/work-intake-routing-and-lifecycle.md, guides/_shared/how-to/choose-a-tracker-integration.md, guides/_shared/reference/tracker-vocabulary.md, guides/core/how-to/capture-work.md, guides/core/how-to/migrate-capture-work.md, guides/core/reference/workspace-toml-schema.md, guides/core/explanation/why-a-brief-layer.md, guides/core/how-to/intake-an-external-brief.md, guides/core/how-to/receive-a-product-brief-and-decompose-it-into-specs.md, guides/core/how-to/orient-at-session-start.md, guides/{atlassian,github,linear}/**, guides/README.md, packs/{core,atlassian,github,linear,product-engineering}/{README.md,JOURNEY.md}, guide-nav-baseline.toml, docs/specs/work-intake-migration-docs/notes/adopter-route-walkthrough.md

**Verification mode:** Goal-based check with manual rendered review

**Tests:**

**Stub:** no stub (goal-based check with manual rendered review).

- Search current adopter sources for comment-backed spec reconstruction,
  unconditional feature-to-brief projection, universal one-way tracker claims,
  and non-alias `capture-work` invocation. Verifies AC15-AC17.
- Validate required frontmatter, duplicate slugs, index coverage, existing
  links, aliases, and non-orphaned pages. Verifies AC15-AC17, AC21.
- Trace one cold-reader route from landing/index to start, defer, status,
  refresh, and migration. Verifies AC15-AC16, AC21.
- Record that pass in
  `docs/specs/work-intake-migration-docs/notes/adopter-route-walkthrough.md`
  with scope, fixture/build inputs, observed routes/results, run/session
  boundary, reviewer, and date. Verifies AC15-AC16, AC21-AC22.
- Compare every capability claim with the owning skill/profile source.
  Verifies AC16-AC17.

**Approach:**

- Use `author-product-docs` in retrofit mode.
- Update or create the minimum complete how-to, explanation, reference, and
  migration pages required by RFC-0083.
- Preserve `guides/core/how-to/capture-work.md` as compatibility guidance or
  an alias route during the window.
- Update tracker pages, pack landing pages, and journeys from their canonical
  sources; change the navigation baseline only for deliberate route changes.

**Done when:** current adopter sources contain one consistent work-intake
model, all pages are reachable, no stale semantic search hit remains
unexplained, and the dated adopter-route walkthrough contains every required
evidence field.

### T6: Maintainer docs, site output, and initial compatibility release gates pass

**Depends on:** T3, T5

**Implements:** the Objective's maintainer guidance, target-writer, compatibility-window, release-metadata, and deferred-removal outcomes in AC11-AC14, AC18, AC21-AC26.

**Review shape:** DEEP release-integration layer, kept below 2,000 reviewable behavior/test lines; split documentation generation from compatibility evidence if construction exceeds that bound.

**Touches:** workspace.toml, packs/core/seeds/docs/CONVENTIONS.md, docs/CONVENTIONS.md, docs/architecture/work-intake-and-artifact-routing.md, docs/architecture/overview.md, docs/guides/**, docs/product/journeys/{pm-intakes-from-tracker,engineer-runs-work-loop,agent-executes-spec}.md, docs/adr/0019-product-intent-ontology-and-brief-projection.md, packs/core/.apm/skills/capture-work/SKILL.md, packs/core/seeds/workspace.toml, packs/{core,atlassian,github,linear}/pack.toml, packs/{core,atlassian,github,linear}/.claude-plugin/plugin.json, docs/product/changelog.md, site.toml, tools/build-site.py, tools/test_build_site_*.py, docs/specs/work-intake-migration-docs/notes/initial-compatibility-review.md, .claude-plugin/marketplace.json

**Verification mode:** Goal-based check with manual compatibility review

**Tests:**

**Stub:** no stub (goal-based check with manual compatibility review).

- Verify conventions, architecture, internal
  adapter/migration/reconciliation/eval guidance, journeys, and ADR metadata
  match the accepted model. Verifies AC18, AC23.
- Audit every supported writer and seed and assert target-only output; assert
  `capture-work` forwards and emits the deprecation notice. Verifies AC11.
- Run ledger-backed rollback against the designated dual-reader release
  fixtures. Verifies AC12.
- Run guide validation, guide-index coverage, site dry run, catalogue gates,
  and the full web-before-docs-site production build. Verifies AC21-AC24.
- Inspect built canonical and alias routes and confirm generated output has no
  hand-authored diff. Verifies AC21-AC22.
- Create
  `docs/specs/work-intake-migration-docs/notes/initial-compatibility-review.md`
  with scope, fixture/build inputs, observed results, run/session boundary,
  reviewer, date, and the initial evidence state against AC14 and the approved
  root-workspace backlog entry. Verifies AC13-AC14.
- Resolve compatibility-policy authority from RFC-0083's Approver metadata and
  assert the record contains identity, role, timestamp, metadata source, and the
  current `deferred` decision. Missing, ambiguous, stale, or insufficient RFC
  authority fails before a compatibility-policy or removal-gate claim. It does
  not reuse `[authorization.migration]` or satisfy the later removal decision.
  Verifies AC13-AC14, AC25.
- Assert root `workspace.toml` contains one non-dispatchable
  `capture-work-alias-removal` item under `[backlog].open`, conforms to the
  canonical AC14/AC24 contract, and does not invent or dispatch a future spec
  identifier. Verifies AC14, AC24.
- Assert every changed skill keeps the minimum required `allowed-tools` and
  `metadata.boundaries`, explains high-impact capabilities, contains no
  credential- or identity-seeking instruction, and projects those declarations
  without broadening across every supported adapter. Verifies AC26.
- Assert workspace-status guidance labels selection/confirmation files as
  human-authored out-of-band inputs and never instructs an agent to synthesize,
  prefill, or edit their route or authorization fields. Verifies AC25-AC26.

**Approach:**

- Edit `packs/core/seeds/docs/CONVENTIONS.md`, then regenerate its projection.
- Update current-state architecture and maintainer guidance after behavior and
  public docs are stable.
- Preserve T4's eval-triggered pack/plugin version pairs; apply any additional
  paired metadata/version/changelog changes required by T5-T6 source edits,
  then self-host after all source edits.
- Publish the initial delivery with the dual reader and alias intact.
- Record rollback and release evidence without marking the alias-removal gate
  complete.
- Preserve and validate the approved root `workspace.toml` backlog anchor
  `capture-work-alias-removal`; AC14 and that entry remain canonical and the
  item stays non-dispatchable until a separately approved follow-up is planned.

**Done when:** the initial migration delivery passes all code, catalogue,
eval, guide, link, and site gates; rollback is demonstrated; the compatibility
record and both QA notes are dated and complete; and `capture-work` plus the
legacy reader remain installed.

## Rollout

- **Initial delivery:** T1-T6 only. Ship the reader-first-compatible migration
  path, target writers, reversible ledger/apply/rollback, routing matrix,
  complete documentation, and dated compatibility record. Keep the alias and
  legacy reader.
- **Compatibility window:** maintain the evidence required by AC14 and the
  approved root-workspace backlog entry; neither source is weakened here.
- **Later removal:** outside this executable plan. T6 leaves a non-dispatchable
  root-workspace backlog anchor; a later human-approved spec/task may be
  created only after AC14 and the approved backlog entry are satisfied.
- **Infrastructure:** none. Migration is local, explicit, and
  repository-confined.
- **External-system integration:** no tracker read or write is required to
  migrate or reconcile a workspace. Routing evals use fixtures.
- **Rollback:** disable target writers and return to the prior dual-reader
  release; use the ledger to restore legacy entries without deleting
  canonical artifacts.
- **Irreversibility:** the published removal release is a major
  public-interface change, but repository artifacts and migration ledgers
  remain durable.

## Risks

- The legacy fixture corpus may normalize away comments or punctuation needed
  for exact rollback. T1 stores exact TOML slices.
- Migration repair code may drift from Group 3 parsing. Extending the existing
  finding/repair seams keeps one parser.
- A long compatibility period can leave the checklist stale. The deferred
  follow-up must re-run every audit rather than trusting old evidence.
- Group 7 can become a dumping ground for documentation omitted by earlier
  groups. AC23 makes missing phase docs blocking findings.
- Renamed guide routes can silently break because Starlight lacks a native
  link-failure gate. Explicit route/link checks and alias inspection cover the
  gap.
- Pack README-only changes still require version metadata; alias removal
  requires a major core bump.
- A read-only plan could become unreproducible if apply cannot recover its
  inputs. Requiring the same reviewed selection file at apply time and binding
  its digest into the operation/confirmation avoids hidden planner state.

## Changelog

- 2026-08-21: Returned the feature to shaping after the implementation-readiness
  audit. Specified the repository-root ledger, closed migration policy,
  reviewed selection and current-session confirmation inputs, processor-owned
  artifact handoff, ledger-first recovery/rollback semantics, evaluation-only
  normalized routing record, four authored migration Schemas, a pinned legacy
  source inventory, closed result/refusal and credential-detector contracts,
  opaque single-use confirmation evidence with role-digest-only persistence,
  contract inventory distinction, projection and pack-version ownership, and
  exact CLI surfaces.
- 2026-08-09: Initial plan drafted from accepted RFC-0083 with confirmed
  assumptions; the initial migration delivery ends at T6 and records later
  alias removal as a non-dispatchable backlog follow-up.
