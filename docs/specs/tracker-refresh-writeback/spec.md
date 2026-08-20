# Spec: Tracker refresh and write-back

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0083, ADR-0077, ADR-0078
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/jsonschema/normalized-intake.schema.json`, `contracts/jsonschema/workspace-entry.schema.json`, `contracts/jsonschema/source-authority.schema.json`, `contracts/jsonschema/refresh-authorization-policy.schema.json`, `contracts/jsonschema/refresh-result.schema.json`
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- **Light-mode lean fill.** For low-risk work running the `work-loop`
skill's light mode, only Objective + Acceptance Criteria + a short task list
(in `plan.md`) are required. **Boundaries**, **Testing Strategy**, and
**Assumptions** are optional — keep them only if they earn their place. Any
risk trigger (see the `work-loop` skill) escalates to full mode, where every
section is filled. -->

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
changelog. This applies to the spec body only — `plan.md` keeps its own
changelog of how the approach evolved. -->

## Objective

An adopter can ask `work-intake` to refresh existing tracker-origin work from
Jira, Jira Align, Linear, or GitHub and receive a reviewed field-level delta
whose allowed actions follow the artifact lifecycle. The local approver decides
every requirement change, Implementing work stays locked, remote write-back
payloads are limited to trace and coordination actions, and a completed
comparison leaves the canonical artifact and its `workspace.toml` revision
mirror consistent without exposing credentials or source payloads.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Resolve an existing canonical artifact and its structured workspace entry
  before acquisition; refresh never materializes, reclassifies, or dispatches
  work.
- Validate acquired data against the Group 2 normalized-intake JSON Schema,
  treat all source text as untrusted data, and preserve only fields required by
  the destination artifact.
- Treat the canonical artifact's source-authority record as authoritative and
  `workspace.toml` as a mirror of only the mode, source locator, and compared
  revision.
- Parse exactly one fenced `toml source-authority` block from a tracker-origin
  artifact and validate its closed record before using ownership, acceptance,
  decision, conflict, receipt, or revision data. Surrounding prose and tracker
  content are never authority.
- Present requirement deltas field by field and require the local approver's
  decision before changing a requirement, accepted revision, receipt,
  dependency pin, or tracker projection.
- Apply the canonical-artifact update, source decision or conflict record, and
  workspace revision mirror as one guarded local operation after a completed
  comparison.
- Use each Group 5 tracker profile's declared acquisition and write-back
  capabilities; unsupported operations fail closed with a named next action.
- Resolve the local approver from the canonical artifact's acceptance record
  and repository authorization policy, or from the repository's configured
  Draft-refresh approver role when no acceptance record exists; check that
  identity and role before any effect and record the authorized identity, role,
  decision time, and source.
- Validate the repository's global `[authorization.refresh]` table against the
  refresh-authorization-policy contract. The table declares permitted roles
  only; artifact ownership, decisions, conflicts, receipts, and identities
  remain in the canonical artifact. The current human session supplies the
  approver identity and claimed role through an explicit confirmation.
- Validate every credential-bearing, user-configured destination used by
  repository-owned HTTP before credential loading or network I/O: enforce the
  profile's permitted scheme and host allowlist, resolve and pin an allowed
  address, and refuse redirects.
- Keep GitHub `gh` invocations on the fixed-host approved-CLI boundary: obtain
  the host only from trusted repository or administrator configuration, bind
  credentials to that host, and treat tracker content only as argv-safe data.
- Preserve Jira's zero-wire refusal for non-GET/HEAD operations over SSO-cookie
  authentication.
- Update adopter documentation, pack metadata, eval coverage, and the
  user-visible changelog in the same phase as each shipped tracker capability.

### Ask first

- Every `accept-source` or `revise-both` decision on a locally owned field.
- Every remote tracker mutation, including a status transition, comment, trace
  link, pull-request link, or closure action, as a separate confirmation
  by the authorized local approver.
- A change from repo-origin to tracker-origin or any change to the artifact's
  field-ownership map.
- Any tracker field mapping or write-back action absent from the active
  profile's versioned capability declaration.
- Any destination whose visibility is broader than the source when safe
  redaction cannot be established.

### Never do

- Blindly overwrite local requirements, apply a source delta while a spec is
  Implementing or its brief is Executing, or rewrite a Shipped child.
- Import tracker-authored requirement changes into a repo-origin artifact;
  those changes remain separate Draft intake unless origin changes through an
  explicit human decision.
- Poll, subscribe to webhooks, add an always-on synchronization service, or
  fetch remote state while deciding dispatch.
- Copy credentials, complete tracker payloads, unnecessary personal or
  sensitive fields, or the artifact's complete field-ownership map into
  `workspace.toml`, stdout, stderr, logs, or agent-visible skill output.
- Bypass an adapter's authentication, transport, confirmation, or write-method
  guard through a raw-call escape hatch.
- Send credentials or a request to loopback, private, link-local, multicast,
  unspecified, cloud-metadata, profile-unlisted, or DNS-rebound destinations;
  follow an unvalidated redirect; or resolve once and connect to a different
  address without revalidation.
- Let tracker content select or alter a GitHub host, URL, executable, command
  option, credential scope, or repository target.
- Introduce a second refresh lifecycle or tracker-specific authority vocabulary
  beside the Group 2 contracts.
- Reuse a remote confirmation, or apply it to any artifact, revision, profile,
  destination, action, target, or payload other than the exact mutation whose
  digest it approved.

## Testing Strategy

- **Authority and transition rules — TDD.** A table-driven construction suite
  covers origin mode, artifact kind, lifecycle, field ownership, decision,
  comparison outcome, and profile capability because these inputs have a
  compact deterministic result.
- **Guarded local updates — TDD integration tests.** Failure injection proves
  that staging and replacement failures preserve artifact content,
  decision/conflict record, receipts, dependency pins, and workspace revision
  mirror; a rollback failure returns the named inconsistent terminal result.
- **Tracker acquisition and write payloads — TDD contract tests.** Fake
  transports and command runners assert exact method, path, payload,
  confirmation, and refusal behavior without live tracker writes.
- **Status and `work-intake` delegation — TDD integration tests.** Tests
  exercise Group 4's public refresh front door, the Group 6 configured
  processor interface, and Group 3's status result so a
  missing processor, conflict, or unsupported capability remains visible and
  non-mutating.
- **Pack projection, activation, and documentation — goal-based checks.**
  Catalogue lint/verify, self-host drift, pack evals, guide validation, link
  checks, and site builds verify the published surface.
- **Approver experience — manual QA.**
  `docs/specs/tracker-refresh-writeback/notes/refresh-capability-walkthrough.md`
  records one no-write dry run per tracker, including scope, fixture inputs,
  observed outputs and routes, run/session boundary, reviewer, and date; no
  manual QA step writes to a production tracker.

## Acceptance Criteria

- [x] **AC1 — Existing-artifact boundary.** The guarded local mutation resolves
  the artifact and workspace paths to canonical real paths beneath the
  repository root and rejects a missing, malformed, lexically traversing,
  symlink-escaping, out-of-repository, or provenance-mismatched pair before
  any local effect. It creates no artifact or workspace entry and revalidates
  both confined targets and their exact fingerprints immediately before
  guarded replacement.
- [x] **AC2 — Contract validation.** Every acquired record accepted by refresh
  validates against `contracts/jsonschema/normalized-intake.schema.json`, and
  every workspace mirror written by refresh validates against
  `contracts/jsonschema/workspace-entry.schema.json`.
- [ ] **AC3 — Repo-origin isolation.** (deferred: tracker-refresh-projection-repair-confirmation) A repo-origin requirement delta changes
  no local requirement or source authority; the result reports projection
  drift or offers separate Draft intake, while coordination-only projection
  repair still requires confirmation.
- [x] **AC4 — Draft refresh.** For a Draft tracker-origin intent, brief, or
  spec, a reviewed delta updates only approved source-owned fields, preserves
  local-owned fields, and advances the compared revision in the artifact and
  workspace mirror only after an identity authorized by the repository's
  configured Draft-refresh approver source and role approves the delta. The
  check occurs before any effect, the review record includes identity, role,
  timestamp, and authorization source, and missing, ambiguous, stale, or
  unauthorized approval produces zero local effects.
- [x] **AC5 — Accepted conflict gate.** For an Accepted intent, Ready brief, or
  Approved spec, every changed locally owned requirement receives exactly one
  recorded `keep-local`, `accept-source`, or `revise-both` decision from an
  identity whose role is authorized by the artifact acceptance record and
  repository policy; the check occurs before any effect, missing/ambiguous or
  unauthorized identity fails closed, and the record includes identity, role,
  timestamp, and authorization source. Accepted fields remain locally owned
  afterward. The guarded commit rejects a changed accepted field unless its
  existing and proposed ownership are both `local`, and rejects any ownership
  map change unless a separate explicit origin/ownership-change path authorized
  it.
- [x] **AC6 — Compared-revision semantics.** A completed comparison advances
  `source_revision` and its workspace mirror even when the approver keeps local
  requirements or leaves a conflict unresolved; acquisition or comparison
  failure advances neither.
- [x] **AC7 — Rejection preservation.** `keep-local`, rejection, and
  unresolved-conflict outcomes change no accepted revision, accepted
  requirement value, coordination receipt, or dependency pin.
- [x] **AC8 — Guarded local write.** A staging or replacement failure rolls the
  canonical artifact, source decision/conflict record, workspace mirror,
  receipts, and dependency pins back to their pre-refresh values. A failure of
  the rollback itself returns `local_write_inconsistent`, a distinct terminal
  result that names a possibly torn pair rather than reporting a clean rollback.
- [ ] **AC9 — Executing lock.** (deferred: tracker-refresh-enforced-capability-state) An Implementing spec or Executing brief refuses
  requirement refresh before any local mutation and names the lifecycle state
  that must change before retry. Remote write-back remains constrained by
  declared capability and per-mutation confirmation, but does not receive a
  verified lifecycle.
- [ ] **AC10 — Deferred brief scope.** (deferred: tracker-refresh-materialized-child-scope) A Ready brief returning from execution
  may refresh only not-yet-materialized scope after conflict resolution;
  Shipped children remain byte-stable and queued Approved children use their
  own Approved-state gate.
- [ ] **AC11 — Shipped allowlist.** (deferred: tracker-refresh-enforced-capability-state) Remote write-back accepts only
  confirmed trace links, display status, comments, pull-request links, and
  closure; no other coordination field or requirement/body field enters the
  remote payload. Shipped-only scoping is not enforced on the remote path
  because that path does not receive a verified lifecycle.
- [x] **AC12 — Remote partial failure.** Remote write-back is a separately
  confirmed operation: every individual mutation receives its own
  check-before-effect confirmation from the authorized local approver and
  records identity and timestamp. A durable pending receipt precedes every
  adapter effect. A missing, stale, ambiguous, or unauthorized confirmation
  rejects before the request. A failed remote call leaves local authority
  intact, reports a retry-safe failed/pending outcome, and is not silently
  retried. The processor boundary does not itself establish correspondence to a
  preceding local authority decision.
- [x] **AC13 — Profile parity.** The same lifecycle fixture matrix passes for
  registration-dependent acquisition, mapping, and common local authority
  outcome across the supported Jira, Jira Align, Linear, and GitHub
  tracker-origin profiles; profile differences are limited to declared
  acquisition, revision, field mapping, and write-back capabilities. This
  matrix does not exercise per-profile durable-write transactions.
- [x] **AC14 — Jira SSO confinement.** Jira SSO-cookie non-GET/HEAD attempts
  fail before the transport records a request; token-authenticated writes
  continue through the existing Jira confirmation and method guards.
- [x] **AC15 — Untrusted source handling.** Instruction-shaped source text
  appears only as candidate field data and cannot select a processor, alter a
  decision, expand a write payload, or invoke a tool.
- [x] **AC16 — Output confidentiality.** Credentials, raw source payloads, and
  unnecessary personal or sensitive fields are absent from the front-door
  result and remediation, the materialized artifact, and tracker command
  construction.
- [x] **AC17 — Status visibility.** `workspace-status` renders origin mode,
  compared revision, accepted revision when present, unresolved conflict state,
  active profile, and advisory refresh/write-back availability without becoming
  a second authority store. Availability reports `False` or `unknown` where
  resolved capability state is unavailable.
- [x] **AC18 — Front-door delegation.** `work-intake` resolves and invokes the
  configured processor for each supported profile; a missing, incompatible, or
  unavailable processor changes nothing and returns one named remediation.
- [x] **AC19 — Published surface.** Changed packs carry required version,
  plugin-manifest, changelog, projection, activation-eval, behavioral-eval,
  README, and tracker-guide updates, and all catalogue and guide gates pass.
- [x] **AC20 — No live-write test dependency.** The complete automated suite
  passes with fake transports and command runners and requires no tracker
  credentials or external mutation.
- [x] **AC21 — Credentialed destination confinement.** Before any request or
  credential-bearing repository-owned HTTP client is created, the adapter
  accepts only a profile-declared scheme and profile-scoped hostname, requires
  HTTPS whenever credentials are attached, rejects userinfo and undeclared
  ports, and rejects loopback, private, link-local, multicast, unspecified, and
  known cloud-metadata addresses for both literal and DNS-resolved destination
  hosts. AC23 governs a configured proxy hop: private corporate-network ranges
  remain permitted there while unspecified, link-local, and explicit metadata
  addresses are refused.
- [x] **AC22 — Redirect and rebinding resistance.** Redirects are disabled and
  no permitted-redirect path is offered. Resolution is pinned or rechecked at
  connect time so a DNS answer cannot change from an allowed address to a
  forbidden address between validation and use, and every refusal occurs
  before the fake transport records a request. These connect and DNS controls
  apply where repository code owns user-configured HTTP. GitHub
  instead uses the approved `gh` CLI with a host read only from trusted
  repository or administrator configuration: credentials remain bound to that
  host, tracker content cannot alter it, and a mismatch or untrusted hostname
  or URL rejects before invocation. Locally owned tests prove argv and stdin
  isolation without asserting control over `gh`'s internal transport.
- [x] **AC23 — Least-privilege skill metadata.** Every new or changed refresh
  or write-back skill action declares only the `allowed-tools` and
  `metadata.boundaries` it uses, including `network_fetch`,
  `filesystem_read_untrusted`, and `filesystem_write` only where applicable.
  Credential-bearing actions also retain every applicable `credentialed`,
  `primitive-class`, `auth`/`auth-fallback`, namespace, and key metadata field
  without inventing locally managed keys for an approved CLI. Per-processor
  source tests and supported-adapter projection tests prove these declarations
  survive unchanged and are never broadened. `github-refresh` declares
  `metadata.credentialed: true`, `metadata.primitive-class: credentialed-cli`,
  and `metadata.auth: cli`, with no locally managed `namespace` or `keys`.
  Linear honors `HTTPS_PROXY`/`NO_PROXY`, `REQUESTS_CA_BUNDLE`,
  `SSL_CERT_FILE`, and `SSL_CERT_DIR` without weakening AC21-AC22 destination,
  redirect, or DNS-rebinding controls; an unsafe or unusable proxy/trust
  configuration fails closed with redacted output.
  A configured proxy is an explicit corporate-network hop, not a destination
  exemption: its resolved address is pinned and rejects unspecified,
  link-local, and cloud-metadata ranges before connection.
- [x] **AC24 — Closed authority and policy encoding.** A tracker-origin
  artifact contains exactly one fenced `toml source-authority` block whose
  parsed object validates against `source-authority.schema.json`; the block is
  the only source for mode, locator, compared revision, accepted revision,
  field ownership, acceptance, decisions, conflicts, local receipts, and remote
  action receipts. The global `[authorization.refresh]` table validates against
  `refresh-authorization-policy.schema.json` and declares permitted Draft and
  accepted approver roles without storing identities or artifact authority.
  Missing, duplicate, malformed, unknown, or contradictory fields fail before
  acquisition or effects, and surrounding prose or tracker text cannot become
  authority. Every coordinator result validates against
  `refresh-result.schema.json`.
- [x] **AC25 — Exact single-use remote confirmation.** Every remote mutation
  consumes one fresh confirmation bound to approver identity and role, artifact
  path, compared source revision, tracker profile and destination, action type,
  target locator, and a canonical payload digest. The confirmation identifier
  and binding are recorded in the artifact's remote-action receipt before the
  adapter call; reuse, mismatch, stale, ambiguous, or unauthorized confirmation
  fails before transport or `gh` invocation. A failed call updates only that
  receipt to a retry-safe failed state and a retry requires a new confirmation.
  The Jira client checks the pending receipt structurally for its action and
  target at the guarded-write boundary; concrete receipt-class identity is not
  asserted across pack runtimes.

## Assumptions

- Technical: Group 6 consumes the approved Group 2 normalized-intake and
  workspace-entry JSON Schemas rather than defining parallel encodings
  (source: user confirmation 2026-08-09).
- Technical: Group 3 supplies reconciliation/status support for authority
  mismatches, Group 4 supplies the public refresh front door and fail-closed
  unavailable result, and Group 6 supplies the configured refresh-processor
  interface and registry (source: user confirmations 2026-08-09 and
  2026-08-17).
- Technical: Group 5's supported profile registry covers Jira, Jira Align,
  Linear, and GitHub and distinguishes tracker profile capability from
  authentication capability (source: user confirmation 2026-08-09).
- Technical: Group 6 owns the missing configured refresh-processor registry,
  guarded artifact/workspace writer, and the three refresh-specific schemas;
  these extend the shipped Group 2–5 seams without changing their normalized
  intake, workspace-entry, lifecycle, or profile vocabularies (source: user
  confirmation 2026-08-17).
- Product: the current human session is the trusted source of the explicit
  approver identity and role presented to refresh; repository policy authorizes
  the role and the canonical artifact records the identity and evidence (source:
  user confirmation 2026-08-17).
- Technical: Jira SSO-cookie authentication remains read-only unless a
  separate security-reviewed XSRF change is approved (source:
  `packs/atlassian/.apm/skills/jira/scripts/_client.py`).
- Product: the fourth adopter intent is operational for every supported
  tracker-origin profile even when a profile truthfully reports a particular
  remote write capability as unavailable (source: user confirmation
  2026-08-09).
- Process: ADR-0077 and ADR-0078 are Accepted approval prerequisites, and implementation
  follows Groups 2–5 (source: user confirmation 2026-08-09).
- Process: every non-cosmetic pack change carries its required version,
  projection, changelog, and eval updates (source: `packs/AGENTS.md` and
  `packs/AGENTS.local.md`).
