# Spec: Work-intake migration, compatibility, and documentation

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0083, ADR-0077, ADR-0078
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/jsonschema/workspace-entry.schema.json`, `contracts/jsonschema/normalized-intake.schema.json`, `contracts/jsonschema/work-intake-migration-manifest.schema.json`
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer can reconcile every supported legacy `workspace.toml` entry into
a human-selected canonical artifact route or a clear non-dispatchable finding,
record a reversible migration before conversion, and restore the legacy
representation without deleting canonical artifacts. Adopters discover
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
  `contracts/jsonschema/work-intake-migration-manifest.schema.json`.
- Present the legacy value, durable source, current lifecycle membership,
  proposed route, and smallest safe next action before any conversion.
- Require a human to choose the canonical artifact route and approve creation
  of any missing artifact.
- Resolve migration approval from the repository's configured migration role
  and resolve alias-removal approval from RFC-0083's Approver metadata; check
  authorization before each effect and record identity, role, timestamp, and
  authorization source.
- Persist a reversible old-to-new mapping before changing `workspace.toml`,
  then use guarded, comment-preserving mutation.
- Keep legacy entries visible but non-dispatchable until their canonical
  artifact and required plan exist and validate.
- Preserve canonical artifacts and Git history during rollback.
- Keep migration, rollback, and removal idempotent, path-confined, crash-safe,
  and observable.
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
- Delete a canonical artifact, Git history, or newly created migration artifact
  when rolling back the workspace representation.
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
  comments in the migration manifest.

## Testing Strategy

- **Legacy parsing and migration planning — TDD.** Fixture tests cover every
  accepted legacy shape, malformed variants, unknown extensions, duplicate
  membership, missing artifacts/plans, and human-choice gates.
- **Manifest, conversion, and rollback — TDD integration tests.** Tests
  validate the JSON Schema, exact old representation, comment preservation,
  path confinement, stale fingerprints, atomic writes, idempotence, and
  artifact non-deletion.
- **Routing convergence — TDD/goal-based integration tests.** A versioned
  matrix runs canonical intake and Group 6 refresh cases across supported
  profiles and asserts artifact, lifecycle membership, processor, authority
  mode, and next action.
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

- [ ] **AC1 — Supported fixture corpus.** Versioned fixtures cover bare
  `spec/<slug>` strings in work arrays; bare shaping slugs;
  `{slug, type, needs}` shaping objects; brief-path strings in brief queues;
  and comment-rich `[backlog].open` entries written by released workflows at
  RFC acceptance.
- [ ] **AC2 — Legacy recognition.** Each supported fixture parses without
  becoming dispatchable by legacy inference and reports its exact source
  representation and lifecycle membership.
- [ ] **AC3 — Human-selected route.** Every convertible legacy entry produces
  a reviewable plan naming one target kind, repository-relative artifact path,
  target membership, source provenance, and smallest next action; no conversion
  applies before an identity authorized by the repository's migration policy
  confirms that route. Missing, ambiguous, stale, or unauthorized identity
  rejects before artifact, manifest, or workspace mutation, and the manifest
  records approver identity, role, timestamp, and authorization source.
- [ ] **AC4 — Missing-contract refusal.** A missing spec or sibling plan
  remains non-dispatchable, and no comment or nearby prose is transformed into
  the missing contract.
- [ ] **AC5 — Unknown-extension boundary.** Private or undocumented TOML
  extensions remain byte-stable and receive a manual-routing finding; they do
  not expand the supported compatibility window.
- [ ] **AC6 — Manifest contract.** Before conversion, a manifest validates
  against `contracts/jsonschema/work-intake-migration-manifest.schema.json` and
  records the workspace path/fingerprint, exact legacy representation and
  membership, approved target entry, created-artifact paths with pre-existence
  flags, operation identity, and rollback state.
- [ ] **AC7 — Path and privacy confinement.** Manifest and migration paths
  resolve inside the repository without symlink escape, and
  manifest/stdout/stderr/log output contains no credentials, raw tracker
  payloads, or unnecessary personal or sensitive data.
- [ ] **AC8 — Guarded conversion.** A conversion refuses a changed workspace
  fingerprint, preserves unrelated entries and comments, writes only a Group 2
  schema-valid target entry, and creates no duplicate lifecycle membership.
- [ ] **AC9 — Crash safety and idempotence.** Failure injection before and
  after each durable write leaves either the reviewed legacy state or the
  complete target state; rerunning plan/apply produces no duplicate artifacts,
  entries, or manifest operations.
- [ ] **AC10 — Reversible rollback.** Rollback restores the exact recorded
  legacy representation and membership when its guard matches, leaves
  canonical artifacts and Git history intact, and refuses to overwrite
  independently changed state.
- [ ] **AC11 — Target writers.** Every supported current workflow and workspace
  seed writes only the target structured contract; `capture-work` forwards to
  `work-intake`, writes no separate semantics, and emits the documented
  deprecation notice during the window.
- [ ] **AC12 — Reader-first rollback.** The release immediately before
  write-new remains a dual reader capable of reading target entries and
  restoring manifest-backed legacy entries without enabling new legacy writes.
- [ ] **AC13 — Compatibility evidence.** A durable checklist records evidence
  for every AC14 predicate and records the RFC Approver identity, role,
  timestamp, metadata source, and decision without redefining those predicates.
- [ ] **AC14 — Removal gate.** `capture-work` and the legacy reader remain
  present through the initial delivery and are removed only after two
  consecutive minor releases counted from the first write-new release, at
  least 90 days, one-minor advance notice, passing fixture/writer/guide/rollback
  gates, and a check-before-effect authorization against RFC-0083's Approver
  metadata. Missing, ambiguous, stale, or unauthorized approval rejects before
  removal. This is an explicitly deferred follow-up, not an executable task in
  the initial plan. (deferred: capture-work-alias-removal)
- [ ] **AC15 — Shared adopter documentation.** Public sources contain a
  task-first how-to for starting, deferring, checking, and refreshing through
  `work-intake`; an explanation of artifact responsibilities; a
  routing/lifecycle/authority/reconciliation reference; and compatibility
  guidance for `capture-work` users.
- [ ] **AC16 — Tracker and journey documentation.** Current Jira, Jira Align,
  Linear, GitHub, brief, spec, execution, and workspace-status pages use
  content/coherence/shippability routing and declared origin authority rather
  than object-name ontology.
- [ ] **AC17 — Stale-semantic audit.** A repository-wide current-doc audit
  finds no instruction to reconstruct a spec from workspace comments, no
  unconditional feature-to-brief rule, no claim that trackers are universally
  one-way, and no non-alias invocation of `capture-work`.
- [ ] **AC18 — Maintainer documentation.** Current-state documentation covers
  canonical artifact responsibility, non-semantic comments, authority modes,
  dispatch invariants, migration/rollback, adapter contracts, reconciliation
  findings, and routing-evaluation maintenance.
- [ ] **AC19 — Routing evaluation matrix.** Versioned fixtures assert chosen
  artifact, lifecycle membership, processor, authority mode, and next action
  for direct spec, multi-spec brief, cross-repo projection, incoherent
  collection/view, defect, remember, status, and each Group 6 refresh lifecycle
  across all supported profiles.
- [ ] **AC20 — Deterministic result.** Two clean runs with identical artifacts,
  TOML, schemas, profile/version, routing configuration, and evaluation input
  produce byte-equivalent normalized results and the same next action.
- [ ] **AC21 — Published navigation.** Guide frontmatter, indices, aliases,
  sidebar placement, pack links, and landing-page discovery expose the new
  route; previous routes either remain valid or redirect as documented.
- [ ] **AC22 — Documentation gates.** Guide validation, index coverage, site
  dry run, marketing-site build, docs-site production build,
  internal-link/route checks, and routing evaluations pass from canonical
  sources without hand-edited generated output.
- [ ] **AC23 — Phase ownership.** The final audit reports any missing Group 2-6
  phase guide as a blocking finding rather than silently absorbing it as
  acceptable terminal documentation debt.
- [ ] **AC24 — Release metadata.** Every changed pack carries the required
  version/plugin/changelog/eval updates, projections are regenerated from
  `.apm/` sources, and the deferred alias-removal backlog item records that its
  future removal release requires a major core-pack increment.
- [ ] **AC25 — Authorization is check-before-effect.** Migration planning may
  be read-only, but artifact creation, manifest approval, conversion, rollback,
  and compatibility-policy changes each resolve the required role from the
  repository policy, record authorized identity and timestamp, and reject
  explicitly before effects when authorization is missing, ambiguous, stale,
  or insufficient.

## Deferred follow-up

Alias and legacy-reader removal is not part of this plan's initial executable
task graph. The initial delivery records a non-dispatchable
`capture-work-alias-removal` item in `workspace.toml [backlog].open`. AC14 and
that approved root-workspace entry are the canonical removal-gate sources. A
later human-approved spec or task owns implementation after both are satisfied;
this spec does not invent that future artifact's identifier.

## Assumptions

- Technical: Group 2 owns the normalized-intake and workspace-entry JSON
  Schemas; Group 7 adds only the migration-manifest JSON Schema needed for
  reversible conversion (source: user confirmation 2026-08-09).
- Technical: Group 3's reconciliation and repair-plan/apply seams are the
  implementation substrate for migration rather than a second workspace parser
  (source: user confirmation 2026-08-09).
- Technical: the supported legacy fixture set is limited to released workspace
  seeds and entry shapes present when RFC-0083 was accepted (source: user
  confirmation 2026-08-09).
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
