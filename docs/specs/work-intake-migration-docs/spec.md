# Spec: Work-intake migration, compatibility, and documentation

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0083, ADR-0077, ADR-0078
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/jsonschema/work-intake-migration-manifest.schema.json`, `contracts/jsonschema/work-intake-migration-selection.schema.json`, `contracts/jsonschema/work-intake-migration-confirmation.schema.json`, `contracts/jsonschema/work-intake-migration-result.schema.json`
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer can reconcile every supported legacy `workspace.toml` entry into
a human-selected canonical artifact route or a clear non-dispatchable finding,
produce a read-only migration plan from a reviewed selection file, record each
authorized operation in the repository-root `.workspace-migrations.json`
ledger before conversion, and restore the legacy representation without
authoring or deleting canonical artifacts. Adopters discover
`work-intake`, its artifact and authority model, and the compatibility window
consistently across guides, pack pages, journeys, navigation, and routing
evaluations. The `capture-work` alias remains a forwarding compatibility
surface until the canonical AC14 removal gate and the approved root-workspace
backlog entry are satisfied; removal remains outside the initial delivery.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off before
proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Treat the released workspace seeds and entry shapes present when RFC-0083 was
  accepted as the complete supported legacy fixture set.
- Validate target entries against the Group 2 workspace-entry JSON Schema and
  migration records against
  `contracts/jsonschema/work-intake-migration-manifest.schema.json`; validate
  reviewed selections and effect confirmations against their sibling migration
  JSON Schemas named in the `Contract:` header.
- Present the legacy value, durable source, current lifecycle membership,
  proposed route, and smallest safe next action before any conversion.
- Require a human to choose the canonical artifact route and approve creation
  of any missing artifact.
- Keep `repair-plan --migration-selection <path>` read-only. When the selected
  canonical artifact does not exist, return the owning processor as the next
  action and refuse to create a ledger entry or mutate `workspace.toml`.
- Resolve migration approval from the repository's configured migration role
  and resolve alias-removal approval from RFC-0083's Approver metadata; check
  authorization before each effect. Migration receipts record an opaque,
  one-effect authorization subject, a digest of the matched policy role,
  timestamp, and source; compatibility records retain the RFC's public
  Approver metadata.
- Load migration roles only from the closed `[authorization.migration]` table
  in `workspace.toml`, with `contract_version =
  "work-intake-migration-authorization.v1"` and one non-empty unique
  `approver_roles` list. Values are public, non-sensitive capability labels
  from the closed set `migration-approver`, `repository-maintainer`, and
  `security-approver`; person, team, account, and organization identifiers are
  invalid policy values. The table stores roles only; current-session subject,
  role, timestamp, and authorization source are effect-specific evidence.
- Require apply and rollback to consume a closed current-session confirmation
  file authored and supplied by the human through an out-of-band current-session
  channel. Its opaque `confirmation-<32 lowercase hex>` unique ID, action,
  operation ID/digest, opaque
  `subject-<32 lowercase hex>` authorization subject, role, RFC 3339 timestamp,
  and `current-human-session` authorization source bind it to exactly one
  effect. A confirmation ID and subject are independently generated from an
  OS-backed cryptographically secure random source and are one-effect-only;
  reuse of either rejects. Migration tooling never generates them, and every
  documented human generation path must use an OS-backed CSPRNG. Names, emails,
  usernames, account
  identifiers, and organization-specific identifiers reject in either opaque
  field before persistence. The live role is checked against the closed policy
  table but only its lowercase SHA-256 digest is copied into the ledger.
  Confirmations expire after five minutes and cannot be reused.
  Migration tooling and skills never create or modify selection or confirmation
  files; artifact processors retain their own authorization contracts.
- Treat the human-authored confirmation boundary as protection against
  autonomous agent effects, not authentication against a malicious local
  repository writer, who already has equivalent direct mutation capability.
- Scan the exact legacy slice before ledger creation. Refuse with a stable,
  non-echoing manual-remediation finding when credential-shaped content is
  detected or the reviewed selection has not attested that comment content is
  safe and necessary for exact rollback.
- Persist a reversible old-to-new operation in the repository-root
  `.workspace-migrations.json` ledger before changing `workspace.toml`, then
  use guarded, comment-preserving mutation.
- Keep legacy entries visible but non-dispatchable until their canonical
  artifact and required plan exist and validate.
- Preserve canonical artifacts and Git history during rollback.
- Keep migration, rollback, and removal idempotent, path-confined, crash-safe,
  and observable.
- Match the runtime-neutral confinement semantics of
  `agentbundle.catalogue_tooling.file_safety` for repository-relative identity,
  link/reparse/hard-link refusal, safe reads and fingerprints, confined write
  parents, and fail-closed resolution errors without importing package internals
  from portable pack source.
- Author adopter documentation in `guides/`, maintainer documentation in
  `docs/guides/` or current-state docs, and regenerate website output from
  source.
- Keep phase-specific documentation with Groups 2-6; use this group for
  migration guidance and the final cross-surface consistency pass.

### Ask first

- The canonical route for every ambiguous or comment-rich legacy entry.
- Creation or substantive modification of an intent, brief, spec/plan,
  research/design artifact, or defect context during migration.
- Handling a private or undocumented TOML extension beyond leaving it
  unchanged with a manual-routing finding.
- Any destructive cleanup, removal of a compatibility reader, or change to the
  published compatibility clock.
- Removal of `capture-work`, after presenting dated release evidence,
  the complete AC14 evidence set, and the approved root-workspace backlog item.

### Never do

- Infer a behavioral contract from comments or automatically promote prose
  into an Approved spec, Ready brief, Accepted intent, or resolved defect.
- Use comment text, `summary`, list order, tracker type, or previous-session
  memory to select a route or satisfy a dependency.
- Create, prefill, rewrite, or suggest route or authorization values for a
  migration selection or confirmation file on the human's behalf; tooling may
  emit only the observed candidates and exact operation/action/digest values
  the human must independently choose or bind in an out-of-band input.
- Delete a canonical artifact, Git history, or newly created migration artifact
  when rolling back the workspace representation.
- Author an intent, brief, spec/plan, research/design artifact, or defect
  context from `workspace-status` migration code; the route plan names the
  owning processor and waits for that processor's reviewed artifact.
- Auto-convert unknown/private extensions, silently discard comments, or
  overwrite a workspace whose fingerprint changed after review.
- Weaken, bypass, or reinterpret AC14 or the approved root-workspace backlog
  entry when evaluating alias removal.
- Claim alias removal is part of the initial migration delivery.
- Hand-edit `docs-site/src/content/docs/guides/`, generated pack/journey pages
  under `web/src/content/`, or `.claude-plugin/marketplace.json`.
- Turn this final audit into a terminal documentation wave that excuses missing
  phase guides from Groups 2-6.
- Store credentials, source payloads, unnecessary personal data, or sensitive
  comments in the migration ledger.

## Testing Strategy

- **Legacy parsing and migration planning — TDD.** Fixture tests cover every
  accepted legacy shape, malformed variants, unknown extensions, duplicate
  membership, missing artifacts/plans, and human-choice gates.
- **Ledger, conversion, and rollback — TDD integration tests.** Tests validate
  the JSON Schema, closed selection/confirmation inputs, exact old
  representation, comment preservation, path confinement, fresh single-use
  authorization, atomic ledger-first writes, pending recovery, idempotence,
  and zero artifact authoring/deletion by migration code.
- **Routing convergence — TDD/goal-based integration tests.** A versioned
  matrix invokes the real Group 2-6 seams across supported profiles and asserts
  the evaluation-only normalized record, including result code,
  dispatchability, and next action, across two independent clean roots.
- **Documentation correctness — goal-based checks.** Repository searches,
  guide/schema validation, index coverage, source-to-site generation, route
  checks, internal-link checks, and production builds detect stale semantics.
- **Compatibility clock and removal — manual QA with mechanical evidence.**
  `docs/specs/work-intake-migration-docs/notes/initial-compatibility-review.md`
  records the initial evidence state against AC14 and the approved
  root-workspace backlog entry, including scope, fixture/build inputs, observed
  results, run/session boundary, reviewer, and date.
- **Rendered discovery — manual QA.**
  `docs/specs/work-intake-migration-docs/notes/adopter-route-walkthrough.md`
  records a cold-reader pass through start, defer, status, refresh, and
  migration, including scope, fixture/build inputs, observed routes,
  run/session boundary, reviewer, and date.

## Acceptance Criteria

- [x] **AC1 — Supported fixture corpus.** Versioned fixtures cover bare
  `spec/<slug>` strings in work arrays; bare shaping slugs;
  `{slug, type, needs}` shaping objects; brief-path strings in brief queues;
  and comment-rich `[backlog].open` entries written by released workflows at
  RFC acceptance. Completeness is pinned only by the acceptance ref and source
  paths in
  [`notes/legacy-source-inventory.md`](notes/legacy-source-inventory.md).
- [x] **AC2 — Legacy recognition.** Each supported fixture parses without
  becoming dispatchable by legacy inference and reports its exact source
  representation and lifecycle membership.
- [x] **AC3 — Human-selected route.** Every convertible legacy entry consumes a
  schema-closed `work-intake-migration-selection.v1` reviewed selection file
  validating against
  `contracts/jsonschema/work-intake-migration-selection.schema.json`
  and containing one complete Group 2 Schema-valid target entry. It produces a
  deterministic read-only plan naming the target kind, repository-relative
  artifact path, target membership, source provenance, owning processor, and
  smallest next action.
  Planning creates no artifact, ledger entry, or workspace mutation. A missing
  canonical artifact returns its owning processor and remains non-dispatchable.
  Every later effect requires fresh current-session confirmation carrying an
  opaque authorization subject and a role appearing in
  `[authorization.migration].approver_roles`; missing,
  ambiguous, stale, or unauthorized evidence rejects before that effect.
  `repair-apply` receives the same selection file used by planning plus a
  confirmation file; rollback needs only its recorded operation and a new
  confirmation file. Migration tooling and skill instructions never create,
  modify, or prefill either human-authored file.
- [x] **AC4 — Missing-contract refusal.** A missing spec or sibling plan
  remains non-dispatchable, and no comment or nearby prose is transformed into
  the missing contract.
- [x] **AC5 — Unknown-extension boundary.** Private or undocumented TOML
  extensions remain byte-stable and receive a manual-routing finding; they do
  not expand the supported compatibility window.
- [x] **AC6 — Manifest ledger contract.** Before conversion, the repository-root
  `.workspace-migrations.json` ledger validates against
  `contracts/jsonschema/work-intake-migration-manifest.schema.json` and records
  `work-intake-migration-ledger.v1` as an ordered operation set. Each operation
  is bound to the ledger's canonical repository identity and records the
  workspace path/fingerprint, exact legacy representation and membership,
  approved target
  entry, artifact receipt with path/fingerprint/`existed_before_apply = true`
  and owning processor, stable operation identity, apply/rollback state, and
  an ordered set of effect-attempt receipts containing opaque confirmation ID,
  action, operation digest, opaque authorization subject, authorization-role
  digest, timestamp,
  authorization source,
  and consumed-before-effect state needed for durable replay refusal. Each retry
  or recovery effect consumes a distinct fresh confirmation before mutation.
  After JSON Schema validation, a mandatory semantic validator rejects duplicate
  operation IDs, duplicate confirmation IDs or authorization subjects anywhere
  in the ledger, receipt
  operation ID/digest mismatches, apply receipts after rollback begins, and any
  state not justified by an ordered apply-then-rollback receipt sequence.
- [x] **AC7 — Path and privacy confinement.** Ledger and migration paths
  use runtime-neutral confinement behavior equivalent to
  `agentbundle.catalogue_tooling.file_safety`: repository-relative identity;
  strict root resolution; refusal of absolute, backslash, `..`, symlink,
  reparse-point, and hard-link escape; pre/post-open regular-file checks for
  reads and fingerprints; confined parent checks for writes; and fail-closed
  handling of `OSError`, `RuntimeError`, and resolution errors before mutation.
  Portable pack source does not import `agentbundle` package internals.
  Ledger/stdout/stderr/log output contains no credentials, raw tracker
  payloads, or unnecessary personal or sensitive data. Before the exact legacy
  slice becomes durable, credential-pattern detection and a human privacy
  attestation bound to its slice digest must pass; refusal never echoes the
  matched content and leaves the legacy entry unchanged for manual sanitation.
  The detector scans raw UTF-8 without normalization and fails closed, with no
  override, on any non-empty password/secret/token/private-key assignment,
  Basic/Bearer authorization header, credential-bearing URI query, PEM/OpenSSH
  private-key marker, or GitHub/Slack/AWS token prefix defined only in
  [`notes/credential-detector-contract.md`](notes/credential-detector-contract.md).
- [x] **AC8 — Guarded conversion.** `repair-apply` accepts one planned operation
  ID together with the reviewed selection file, revalidates the selection,
  artifact receipt, migration policy, fresh confirmation, ledger, and workspace
  fingerprint, persists the approved ledger operation first, preserves
  unrelated entries and comments, writes only a Group 2 schema-valid target
  entry, and creates no duplicate lifecycle membership.
- [x] **AC9 — Crash safety and idempotence.** Failure injection before and
  after ledger staging/replacement and workspace staging/replacement leaves
  either the reviewed legacy workspace with any separately approved canonical
  artifact intact, or the complete target workspace. Rerunning plan/apply
  produces no duplicate artifacts, entries, or ledger operations; a persisted
  pending operation is recoverable deterministically with a newly bound
  confirmation and never by replaying a consumed confirmation ID or
  authorization subject.
- [x] **AC10 — Reversible rollback.** Rollback restores the exact recorded
  legacy representation and membership for one operation ID when its applied
  fingerprint and fresh authorization guard match, updates only that ledger
  operation's rollback state, leaves canonical artifacts and Git history
  intact, and refuses to overwrite independently changed state.
- [x] **AC11 — Target writers.** Every supported current workflow and workspace
  seed writes only the target structured contract; `capture-work` forwards to
  `work-intake`, writes no separate semantics, and emits the documented
  deprecation notice during the window.
- [x] **AC12 — Reader-first rollback.** The release immediately before
  write-new remains a dual reader capable of reading target entries and
  restoring ledger-backed legacy entries without enabling new legacy writes.
- [x] **AC13 — Compatibility evidence.** A durable checklist records evidence
  for every AC14 predicate and records the RFC Approver identity, role,
  timestamp, metadata source, and decision without redefining those predicates.
- [ ] **AC14 — Removal gate.** (deferred: capture-work-alias-removal)
  `capture-work` and the legacy reader remain
  present through the initial delivery and are removed only after two
  consecutive minor releases counted from the first write-new release, at
  least 90 days, one-minor advance notice, passing fixture/writer/guide/rollback
  gates, and a check-before-effect authorization against RFC-0083's Approver
  metadata. Missing, ambiguous, stale, or unauthorized approval rejects before
  removal. This is an explicitly deferred follow-up, not an executable task in
  the initial plan.
- [x] **AC15 — Shared adopter documentation.** Public sources contain a
  task-first how-to for starting, deferring, checking, and refreshing through
  `work-intake`; an explanation of artifact responsibilities; a
  routing/lifecycle/authority/reconciliation reference; and compatibility
  guidance for `capture-work` users.
- [x] **AC16 — Tracker and journey documentation.** Current Jira, Jira Align,
  Linear, GitHub, brief, spec, execution, and workspace-status pages use
  content/coherence/shippability routing and declared origin authority rather
  than object-name ontology.
- [x] **AC17 — Stale-semantic audit.** A repository-wide current-doc audit
  finds no instruction to reconstruct a spec from workspace comments, no
  unconditional feature-to-brief rule, no claim that trackers are universally
  one-way, and no non-alias invocation of `capture-work`.
- [x] **AC18 — Maintainer documentation.** Current-state documentation covers
  canonical artifact responsibility, non-semantic comments, authority modes,
  dispatch invariants, migration/rollback, adapter contracts, reconciliation
  findings, and routing-evaluation maintenance.
- [x] **AC19 — Routing evaluation matrix.** Versioned fixtures drive the real
  Group 2-6 seams and project their outputs into an evaluation-only normalized
  record containing case ID, profile ID/version, artifact kind/path, lifecycle
  membership, processor, authority mode, dispatchability, result code, and next
  action. The record covers direct spec, multi-spec brief, cross-repo
  projection, incoherent collection/view, defect, remember, status, migration,
  and each Group 6 refresh lifecycle across all supported profiles; it is not a
  new runtime or published contract.
  The migration row invokes the actual T2 read-only planner and asserts its
  applicability/result/next action; apply and rollback durability remain T3
  integration coverage rather than profile-routing cases.
- [x] **AC20 — Deterministic result.** Two clean runs with identical artifacts,
  TOML, schemas, profile/version, routing configuration, and evaluation input
  produce byte-equivalent normalized results and the same next action.
- [x] **AC21 — Published navigation.** Guide frontmatter, indices, aliases,
  sidebar placement, pack links, and landing-page discovery expose the new
  route; previous routes either remain valid or redirect as documented.
- [x] **AC22 — Documentation gates.** Guide validation, index coverage, site
  dry run, marketing-site build, docs-site production build,
  internal-link/route checks, and routing evaluations pass from canonical
  sources without hand-edited generated output.
- [x] **AC23 — Phase ownership.** The final audit reports any missing Group 2-6
  phase guide as a blocking finding rather than silently absorbing it as
  acceptable terminal documentation debt.
- [x] **AC24 — Release metadata.** Every changed pack carries the required
  version/plugin/changelog/eval updates, projections are regenerated from
  `.apm/` sources, and the deferred alias-removal backlog item records that its
  future removal release requires a major core-pack increment.
- [x] **AC25 — Authorization is check-before-effect.** Migration planning may
  be read-only, but artifact creation, ledger approval, conversion, rollback,
  and compatibility-policy changes each resolve their owning repository or RFC
  authorization contract and reject explicitly before effects when
  authorization is missing, ambiguous, stale, or insufficient. Artifact
  creation stays under the owning processor's contract; migration apply and
  rollback use `[authorization.migration]` and a fresh, single-use confirmation
  authored through the out-of-band current-human session. Durable migration
  receipts store only the one-effect opaque confirmation ID and authorization
  subject, digest of the matched policy role, timestamp, and source; the raw
  role is never copied into the ledger. Because permitted role labels are
  already public and non-sensitive, that digest is an integrity binding rather
  than a privacy mechanism. Public RFC compatibility evidence retains its own
  Approver metadata. This gate prevents autonomous agent
  effects; it does not
  claim to authenticate against a malicious principal who already controls
  repository files.
- [x] **AC26 — Skill permission and boundary preservation.** Every changed
  skill declares only the `allowed-tools` and `metadata.boundaries` required by
  its actions, explains each high-impact capability at the point of use,
  contains no credential- or identity-seeking instruction, and preserves those
  declarations without broadening across every supported projection.
  Migration instructions explicitly prohibit creating or editing reviewed
  selection and confirmation inputs.
- [x] **AC27 — Explicit migration surfaces.** `workspace-status` adds no public
  migration skill. `repair-plan --migration-selection <path>` is read-only;
  `repair-apply --migration-selection <path> --operation-id <id>
  --confirmation-file <path>` is the sole migration apply writer; and
  `repair-rollback --operation-id <id> --confirmation-file <path>` is the sole
  rollback writer. The existing Type 2 cleanup contract is unchanged. All three
  return stable machine-readable results and redacted refusal codes; absent
  migration inputs retain the pre-migration CLI contract.
  Migration planning rejects `--plan-file`; migration apply rejects
  `--plan-file` and `--yes`; partial or mixed migration argument sets fail
  closed. Conversely, the existing Type 2 path accepts none of
  `--migration-selection`, `--operation-id`, or `--confirmation-file` and
  retains its current `--plan-file`/`--yes` semantics.
  Each effect's `--confirmation-file` is a closed
  `work-intake-migration-confirmation.v1` document validating against
  `contracts/jsonschema/work-intake-migration-confirmation.schema.json` and
  bound to that action and operation ID/digest. Migration results retain the
  existing `schema_version = 1`/`mode` envelope and add a `migration` object
  validating against
  `contracts/jsonschema/work-intake-migration-result.schema.json`, with exact
  `contract_version`, `result_code`, `applicable`, `mutated`, `operation_id`,
  `operation_digest`, `next_action`, and `ledger_state` names and per-result
  required fields. Exit 0 means a
  completed read/apply/rollback or idempotent no-op, including a non-applicable
  missing-artifact plan; exit 1 returns `workspace_absent` with
  `next_action = "create-workspace"` and no operation fields; exit 2 means
  invalid, unsafe, stale, unauthorized, or failed execution.
  The migration `result_code` vocabulary is closed to `planned`,
  `artifact_missing`, `manual_routing_required`, `applied`, `already_applied`,
  `rolled_back`, `already_rolled_back`, `workspace_absent`,
  `invalid_selection`, `unsafe_path`,
  `legacy_finding_missing`, `selection_mismatch`, `target_invalid`,
  `privacy_review_required`, `sensitive_legacy_content`, `artifact_changed`,
  `migration_policy_invalid`, `confirmation_invalid`, `confirmation_stale`,
  `confirmation_reused`, `confirmation_binding_mismatch`,
  `unauthorized_approver`, `ledger_invalid`, `ledger_changed`,
  `operation_missing`, `operation_state_conflict`, `workspace_changed`,
  `lock_busy`, `write_failed`, `recovery_conflict`, and
  `dependency_unavailable`; stdout contains only the JSON envelope and stderr
  may contain a bounded generic diagnostic that never includes input content.
- [x] **AC28 — Contract inventory accuracy.** `contracts/README.md` labels the
  migration ledger/selection/confirmation/result Schemas and the Group 2
  Schemas as public authored contracts, links each owning spec, and separately
  identifies which contracts are copied into AgentBundle CLI data. Contract
  tests enforce the stated distinction and do not infer CLI bundling merely
  from repository publication.

## Deferred follow-up

Alias and legacy-reader removal is not part of this plan's initial executable
task graph. The initial delivery records a non-dispatchable
`capture-work-alias-removal` item in `workspace.toml [backlog].open`. AC14 and
that approved root-workspace entry are the canonical removal-gate sources. A
later human-approved spec or task owns implementation after both are satisfied;
this spec does not invent that future artifact's identifier.

## Assumptions

- Technical: Group 2 owns the normalized-intake and workspace-entry JSON
  Schemas; Group 7 adds only the ledger, reviewed-selection,
  effect-confirmation, and CLI migration-result JSON Schemas needed for
  reversible conversion (source: user confirmation 2026-08-09 plus reshaped
  interface contract 2026-08-21).
- Technical: Group 3's reconciliation and repair-plan/apply seams are the
  implementation substrate for migration rather than a second workspace parser
  (source: user confirmation 2026-08-09).
- Technical: the supported legacy fixture set is limited to released workspace
  seeds and entry shapes present when RFC-0083 was accepted (source: user
  confirmation 2026-08-09).
- Technical: the canonical acceptance ref and source-path inventory live only
  in `notes/legacy-source-inventory.md` (local Git/RFC inspection 2026-08-21).
- Technical: durable migration state is one repository-root
  `.workspace-migrations.json` ledger; `repair-plan` consumes a reviewed
  selection file, `repair-apply` addresses a planned operation ID, and
  `repair-rollback` addresses an applied operation ID (source: user confirmation
  2026-08-21).
- Technical: migration authorization is the closed
  `[authorization.migration]` role-only table; ledger/apply/rollback effects
  require fresh current-session evidence, while any artifact or policy effect
  remains governed by its owning processor (source: user confirmation
  2026-08-21).
- Technical: apply and rollback confirmations follow the existing refresh
  safety shape: closed JSON, exact operation/action binding, unique confirmation
  ID, `current-human-session` source, RFC 3339 timestamp no more than five
  minutes old, and durable single-use enforcement. `repair-apply` also receives
  the reviewed selection file so a read-only plan need not create hidden state
  (source: user confirmation of the current-session authorization decision,
  specified by this draft on 2026-08-21).
- Security: selection and confirmation files are human-authored through an
  out-of-band current-session channel; migration code/skills never create or
  edit them. This control prevents autonomous agent effects and does not defend
  against a malicious local writer with direct repository mutation capability
  (secure-design review resolution 2026-08-21).
- Security: exact rollback data is admitted only after no-echo credential
  detection and human privacy attestation bound to the source-slice digest;
  otherwise migration refuses pending manual sanitation (secure-design review
  resolution 2026-08-21).
- Technical: migration tooling never authors substantive canonical artifacts;
  a missing artifact routes to its owning processor and apply waits for a
  reviewed artifact receipt (source: user confirmation 2026-08-21).
- Technical: the routing matrix's normalized record is evaluation-only, and
  repository JSON Schemas remain public authored contracts without an implied
  AgentBundle CLI bundle requirement (source: user confirmation 2026-08-21).
- Technical: an interrupted migration may leave the reviewed legacy workspace
  beside a separately approved canonical artifact; rollback preserves that
  artifact and restores only workspace representation (source: user
  confirmation 2026-08-21).
- Product: a cold adopter discovers the complete route through public guides
  and website navigation without knowing internal skill names (source: user
  confirmation 2026-08-09).
- Process: Group 7 follows Groups 2-6 and performs a final consistency pass
  without replacing their phase-owned documentation (source: user confirmation
  2026-08-09).
- Process: alias removal is a later externally gated task and cannot finish in
  the initial migration delivery (source: user confirmation 2026-08-09).
- Process: AC14 and the approved root-workspace backlog entry are the canonical
  compatibility/removal predicates (source: RFC-0083).
