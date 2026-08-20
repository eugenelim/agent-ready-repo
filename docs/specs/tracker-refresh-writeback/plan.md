# Plan: Tracker refresh and write-back

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Implement one shared authority coordinator and the missing configured refresh
processor registry behind Group 4's `work-intake` refresh interface, then
compose it with the four Group 5 tracker profiles. Add one guarded local writer
for the canonical artifact/workspace pair because the shipped Group 3 repair
writer is private and queue-specific rather than a reusable mutation API.
The coordinator owns lifecycle decisions, guarded local updates, revision
semantics, conflict records, and status facts; adapters own acquisition,
revision extraction, field mapping, and capability-scoped remote commands.
Linear's existing brief sync becomes a compatibility entry into that shared
path. Jira and Jira Align reuse their existing clients where their guarded
commands suffice, and GitHub continues through the fixed-host approved `gh`
boundary. Automated verification uses schema fixtures and fake transports; no
test mutates a live tracker.

## Constraints

- RFC-0083 fixes origin modes, field ownership, allowed decisions, lifecycle
  locks, revision semantics, and Shipped write-back limits.
- Approval requires the two accepted Group 1 ADRs named in `spec.md`; no
  implementation begins while either remains unresolved.
- `contracts/jsonschema/normalized-intake.schema.json` and
  `contracts/jsonschema/workspace-entry.schema.json` are consumed contracts
  owned by `normalized-intake-workspace-contracts`.
- `workspace-routing-invariants` owns parsing, reconciliation, status
  classification, guarded workspace transitions, and repair readiness.
- `work-intake-surface` owns the public front door and fail-closed
  refresh-unavailable result. T1 owns the sole configured refresh-processor
  interface and registry behind that front door.
- `tracker-intake-adapters` owns the supported profile registry, normalized
  acquisition, and classification boundary.
- Existing adapter authentication and transport controls remain authoritative.
  In particular, Jira SSO-cookie writes remain refused.
- No new dependency is added. Shipped `.apm/` content contains no
  repository-governance citations.
- Each tracker capability and its adopter guide ship in the same phase.

## Construction tests

**Integration tests:**

- A cross-profile matrix loads the same normalized source changes into Jira,
  Jira Align, Linear, and GitHub processors and asserts the same local authority
  outcome for Draft, Accepted, Ready, Approved, Implementing, Executing, and
  Shipped states.
- Failure injection across artifact staging, workspace staging, guarded
  replace, and remote command failure proves local all-or-nothing behavior and
  explicit remote partial-failure reporting.
- `work-intake` refresh through `workspace-status` verifies processor
  selection, authority visibility, and fail-closed behavior from the public
  entry point.

**Manual verification:**

- Record `docs/specs/tracker-refresh-writeback/notes/refresh-capability-walkthrough.md`
  with one no-write dry run per tracker. It names scope, fixture inputs,
  observed outputs and routes, the run/session boundary, reviewer, and date.
- Review the generated guide routes and pack landing pages from the built site.
- Do not authenticate against or write to a production tracker for
  verification.

## Design (LLD)

### Interfaces & contracts

The shared coordinator accepts a Group 2 normalized-intake record, the resolved
canonical artifact, its validated workspace entry, the active profile
identifier/version, and an approver decision set. It returns a schema-valid
refresh result containing comparison status, local mutation status, conflict
state, and any separately confirmed remote action result. It delegates guarded
workspace parsing and reconciliation to Group 3, then uses a refresh-owned
guarded writer that locks, revalidates exact artifact/workspace fingerprints,
stages both replacements, and rolls back both on every pre-commit failure.

Tracker-origin artifacts carry exactly one fenced `toml source-authority`
block. Parsed source authority, repository `[authorization.refresh]` policy,
and coordinator results validate against the three Group 6 schemas before use.
The policy table contains role allowlists only; identities and artifact-specific
authority remain in the artifact.

The coordinator resolves approver identity and role from the canonical
acceptance record plus repository authorization policy. When a Draft artifact
has no acceptance record, it resolves the repository's configured
Draft-refresh approver source and role. Authorization and a fresh per-mutation
confirmation are checked before effects; decision records carry identity,
role, timestamp, and authorization source.

Each tracker processor implements the T1 configured-processor interface:
acquire the named source revision, map source fields to canonical artifact
fields, declare capabilities, and execute only approved remote actions. The
processor never selects artifact kind or lifecycle.

Each remote confirmation is a one-time value bound to the authorized identity
and role, artifact, compared revision, profile, destination, action, target,
and canonical payload digest. Its receipt is durably staged before one adapter
call; a retry creates a new confirmation rather than replaying the old one.

Traces to: AC1-AC13, AC17-AC18, AC23-AC25 · implements
`contracts/jsonschema/normalized-intake.schema.json` and
`contracts/jsonschema/workspace-entry.schema.json`; defines the three
refresh-specific schemas named by `spec.md`.

### Failure, edge cases & resilience

Acquisition and comparison failures are pre-commit failures. Local mutation is
one guarded operation over the artifact and workspace mirror. Remote write-back
is deliberately outside that local transaction: the local authority decision
is durable first, then the confirmed adapter command runs once and returns a
retry-safe outcome. A stale artifact/workspace fingerprint, profile-version
mismatch, unsupported capability, ambiguous field map, unresolved redaction,
or execution lock refuses without mutation.

Credential-bearing destinations used by repository-owned HTTP pass a shared
pre-request guard. The guard enforces profile-declared schemes, hostnames, and
ports; requires HTTPS for credentialed calls; rejects userinfo and forbidden
literal/resolved address ranges including cloud metadata; disables redirects
unless the profile permits and revalidates them; and pins or connect-time
rechecks DNS resolution to resist rebinding and validation/use races.

GitHub remains a distinct approved-CLI boundary. Repository code accepts its
host only from trusted repository or administrator configuration, verifies
credential-to-host binding, and rejects mismatched or tracker-supplied hosts or
URLs before constructing argv. Tests own argv/stdin isolation and do not claim
to govern `gh`'s internal connect, redirect, or DNS behavior.

The Jira SSO-cookie client remains a zero-wire refusal for non-GET/HEAD methods.
Rate limits, authentication failures, missing CLI tools, and external outages
surface adapter-specific remediation without changing compared revision unless
a comparison actually completed.

Traces to: AC1, AC4, AC6-AC16, AC18, AC21-AC23 · consumes the Group 2 schemas.

### Dependencies & integration

The dependency chain is Group 2 contracts and release readiness → Group 3
reconciliation and repair readiness → Group 4 public intake seam → Group 5
profile acquisition → this coordinator-owned guarded writer, configured refresh
registry, and processors.
Core owns shared authority behavior. Tracker packs own only their
adapter-specific edges. `workspace-status` consumes coordinator results for
display; it does not recalculate authority.

Rollout follows the reader/router-first sequence in `## Rollout`; no processor
is advertised operational until its fixtures, docs, and capability declaration
land together.

Traces to: AC2, AC13, AC17-AC20, AC23 · consumes both Group 2 JSON Schemas.

## Tasks

### T1: Shared refresh lifecycle and guarded-update tests pass

**Depends on:** spec:normalized-intake-workspace-contracts/T4, spec:workspace-routing-invariants/T4, spec:work-intake-surface/T6, spec:tracker-intake-adapters/T7

**Touches:** contracts/jsonschema/{source-authority,refresh-authorization-policy,refresh-result}.schema.json, packs/core/.apm/skills/work-intake/SKILL.md, packs/core/.apm/skills/work-intake/scripts/*.py, packs/core/.apm/skills/work-intake/evals/files/routing/matrix.json, packs/core/tests/skills/work-intake/**, packs/core/tests/pack/test_work_intake_surface.py, tests/roster/test_work_intake_contracts.py

**Verification mode:** TDD

**Tests:**

**Stub:** `true` — the red contract surface is compilable without importing the
not-yet-created `refresh.py`; EXECUTE replaces the local protocol fakes with the
real module before making these assertions green.

```python
# STUB: AC4 — Draft refresh requires an authorized reviewed delta
def test_draft_refresh_requires_authorized_review(refresh_contract):
    result = refresh_contract.compare(lifecycle="Draft", authorized=False)
    assert result.local_mutation == "refused"
    assert result.effects == []


# STUB: AC24 — only closed structured authority is accepted
def test_authority_block_is_closed(refresh_contract):
    result = refresh_contract.load_authority(block_count=2, unknown_field=True)
    assert result.code == "invalid_source_authority"
    assert result.effects == []


# STUB: AC25 — confirmation is exact and single-use
def test_remote_confirmation_is_bound_and_single_use(refresh_contract):
    first = refresh_contract.confirm(payload_digest="a" * 64)
    assert first.status == "pending"
    replay = refresh_contract.confirm(payload_digest="a" * 64, confirmation=first.confirmation)
    assert replay.code == "confirmation_reused"
    assert replay.transport_calls == 0
```

- Add a table-driven test for repo-origin and tracker-origin across Draft,
  Accepted, Ready, Approved, Implementing, Executing, and Shipped, including
  every allowed decision and unsupported transition. Verifies AC3-AC11.
- For Draft artifacts without an acceptance record, test the configured
  Draft-refresh approver source and role, identity/role/timestamp/source
  recording, check-before-effect ordering, and zero local effects for missing,
  ambiguous, stale, or unauthorized approval. Verifies AC4.
- Add comparison-result tests proving completed comparison advances the
  compared revision while acquisition/comparison failure does not. Add
  separate `keep-local`, rejection, and unresolved-conflict fixtures asserting
  accepted revision/value, coordination receipts, and dependency pins remain
  unchanged while only AC6's compared revision advances. Verifies AC6-AC7.
- Add guarded-write failure injection at every local stage and assert
  byte-identical pre-state after failure. Verifies AC8.
- Add stale-fingerprint, profile-version mismatch, missing processor, and
  unsupported-capability cases. Verifies AC1, AC13, AC18.
- Add lexical traversal and symlink-escape fixtures for both artifact and
  workspace targets; assert resolved-path confinement before reads or
  acquisition and exact confined-target fingerprint revalidation immediately
  before guarded replace. Verifies AC1, AC8.
- Add authorized, missing, ambiguous, stale, and unauthorized approver cases;
  assert identity/role/timestamp/source recording and zero effects on rejection.
  For Accepted/Ready/Approved artifacts, assert value-changing decisions retain
  `local` ownership and that unauthorized ownership-map changes fail closed;
  assert both unauthorized callers and an otherwise-authorized refresh
  approver cannot use this coordinator as the separate Ask-first
  origin/ownership-change path. Add a distinct confirmation check for each
  queued remote mutation. Verifies AC5, AC12.
- Add destination-guard cases for profile-permitted schemes, profile-scoped
  host/port allowlists, userinfo, literal and DNS-resolved
  loopback/private/link-local/multicast/unspecified and cloud-metadata
  addresses, redirects disabled by default, permitted-hop revalidation, DNS
  rebinding, and validation/use races; every refusal records zero requests.
  Verifies AC21-AC22.
- Add instruction-shaped source strings and sensitive-field fixtures that
  cannot affect routing or visible output. Verifies AC15-AC16.
- Assert the shared action declares only its required `allowed-tools` and
  `metadata.boundaries`; absent filesystem or network use remains absent after
  projection. Verifies AC23.
- Add schema and parser fixtures for exactly one closed source-authority block,
  repository role policy, and refresh result; reject missing, duplicate,
  malformed, unknown, contradictory, and prose-derived authority before
  acquisition or effects. Verifies AC24.
- Add confirmation-binding fixtures covering identity, role, artifact, source
  revision, profile, destination, action, target, canonical payload digest,
  staleness, and one-time consumption. Assert a failed remote action records a
  retry-safe receipt and a retry requires a new confirmation. Verifies AC25.

**Approach:**

- Add one pure authority-decision layer under the Group 4 `work-intake`
  scripts, consuming Group 2 schema-validated records.
- Add the configured refresh-processor registry at the existing Group 4 front
  door and preserve `refresh-unavailable` for absent/incompatible processors.
- Reuse Group 3 parsing, confinement, and reconciliation results, but own one
  refresh-specific guarded artifact/workspace writer because Group 3 exposes no
  generic mutation API.
- Represent remote write-back as a separately confirmed post-local operation
  with explicit pending/failed/succeeded result.
- Keep profile-specific field mapping and commands outside core.

**Done when:** the shared suite is green for every lifecycle row, all
failure-injection cases leave local state unchanged, and `work-intake` exposes
one processor contract without tracker-specific branches.

### T2: Authority and refresh availability are visible through status

**Depends on:** T1

**Touches:** packs/core/.apm/skills/workspace-status/SKILL.md, packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py, packs/core/.apm/skills/workspace-status/scripts/workspace_status.py, packs/core/.apm/skills/workspace-status/evals/**, packs/core/tests/skills/workspace-status/**, packages/agentbundle/agentbundle/_data/workspace_status_engine.py, packages/agentbundle/agentbundle/workspace_mcp.py, packages/agentbundle/tests/**, tests/roster/test_workspace_status_projection.py, tools/test_workspace_status.py, tools/test_workspace_status_cli.py

**Verification mode:** TDD

**Tests:**

**Stub:** `true` — the red contract surface uses a local result fake until T1
provides the coordinator result type.

```python
# STUB: AC17 — status renders structured refresh authority facts
def test_status_projects_refresh_authority(status_renderer, refresh_facts):
    rendered = status_renderer(refresh_facts(origin="tracker-origin", conflict=True))
    assert rendered["origin_mode"] == "tracker-origin"
    assert rendered["refresh"]["conflict"] is True
    assert "owned_fields" not in rendered
```

- Add status fixtures for repo-origin, Draft tracker-origin, accepted revision,
  unresolved conflict, execution lock, missing processor, and unsupported write
  capability. Verifies AC17-AC18.
- Assert status consumes structured authority/reconciliation facts and does not
  infer from comments or source text. Verifies AC15, AC17.
- Assert output redaction across JSON, stdout, stderr, and eval-captured skill
  output. Verifies AC16.

**Approach:**

- Extend Group 3's result model and renderers with the smallest
  refresh/authority fields needed for next action.
- Route all readiness and conflict judgments through existing reconciliation
  results.
- Keep field ownership and complete decision history in the artifact, not
  status output or workspace TOML.

**Done when:** CLI, engine, eval, and adopter-facing status fixtures show the
same authority and availability result without duplicating the authority map.

### T3: Linear refresh and allowed write-back pass contract fixtures

**Depends on:** T1

**Touches:** packs/linear/.apm/skills/linear-brief-sync/**, packs/linear/.apm/skills/linear/SKILL.md, packs/linear/.apm/skills/linear/scripts/linear.py, packs/linear/tests/**

**Verification mode:** TDD

**Tests:**

**Stub:** `true` — the red contract surface uses fake coordinator and GraphQL
transport protocols until the Linear processor exists.

```python
# STUB: AC11 — Linear emits only an allowlisted shipped mutation
def test_linear_shipped_write_is_allowlisted(linear_processor, confirmation):
    result = linear_processor.write(action="comment", confirmation=confirmation)
    assert result.action == "comment"
    assert set(result.payload) <= {"issue_id", "body"}


# STUB: AC12 — each Linear mutation consumes a fresh confirmation
def test_linear_rejects_confirmation_reuse(linear_processor, confirmation):
    linear_processor.write(action="comment", confirmation=confirmation)
    replay = linear_processor.write(action="close", confirmation=confirmation)
    assert replay.code == "confirmation_reused"
    assert replay.transport_calls == 0
```

- Characterize the existing Outcome/User-stories brief delta, then run the
  same source through the shared lifecycle matrix. Verifies AC4-AC10, AC13.
- Add fake GraphQL mutation tests for only profile-supported trace links,
  status, comments, pull-request links, and closure; assert every other
  coordination field and every requirement/body field cannot enter a mutation.
  Verifies AC11-AC12.
- Assert each Linear comment, trace link, pull-request link, status, or closure
  mutation requires
  a fresh confirmation by the authorized local approver; reused, missing,
  stale, ambiguous, or unauthorized confirmation records zero requests, and a
  success record includes identity and timestamp. Verifies AC5, AC12.
- Assert rejected, locked, unavailable, authentication-failed, and rate-limited
  paths perform no mutation. Verifies AC7, AC9, AC12.
- Assert the Linear destination passes scheme/host/address/redirect/DNS
  confinement before the fake GraphQL transport records a request. Assert the
  pinned transport also honors `HTTPS_PROXY`/`NO_PROXY` and
  `REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE`/`SSL_CERT_DIR`, pins the selected proxy
  socket, redacts proxy and credential details, and fails closed when proxy or
  trust handling cannot preserve the same confinement. Verifies AC21-AC23.
- Assert `linear-brief-sync` delegates to the configured processor and
  preserves its public compatibility trigger. Verifies AC18.
- Assert Linear refresh/write-back actions declare minimal `allowed-tools` and
  `metadata.boundaries` plus accurate credentialed/auth/namespace/key metadata.
  Verifies AC23.

**Approach:**

- Turn `linear-brief-sync` into a compatibility-facing wrapper over the shared
  refresh processor rather than preserving its private authority rules.
- Extend `linear.py` only for remote actions required by the declared profile;
  retain the credential broker and existing error contract.
- Add revision extraction and field mapping to the Group 5 Linear profile.

**Done when:** Linear passes the common lifecycle suite, its fake transport
sees only declared mutations, and the old sync invocation reaches the same
result as `work-intake` refresh.

### T4: Jira and Jira Align refresh preserve transport and auth guards

**Depends on:** T1

**Touches:** packs/atlassian/.apm/skills/*refresh*/**, packs/atlassian/.apm/skills/jira/scripts/jira.py, packs/atlassian/.apm/skills/jira/scripts/_client.py, packs/atlassian/.apm/skills/jira-align/scripts/jira_align.py, packs/atlassian/.apm/skills/jira-align/scripts/_client.py, packs/atlassian/tests/skills/**

**Verification mode:** TDD

**Tests:**

**Stub:** `true` — the red contract surface uses fake coordinator and transport
protocols until the Jira and Jira Align processors exist.

```python
# STUB: AC14 — Jira SSO-cookie writes remain zero-wire refusals
def test_jira_sso_write_is_zero_wire(jira_processor, sso_confirmation):
    result = jira_processor.write(action="comment", confirmation=sso_confirmation)
    assert result.code == "sso_cookie_write_refused"
    assert result.transport_calls == 0


# STUB: AC11 — Jira Align unsupported actions create no payload
def test_jira_align_undeclared_action_is_refused(jira_align_processor, confirmation):
    result = jira_align_processor.write(action="requirement_body", confirmation=confirmation)
    assert result.code == "unsupported_capability"
    assert result.transport_calls == 0
```

- Run Jira and Jira Align normalized fixtures through the common lifecycle
  matrix. Verifies AC3-AC13.
- Assert exact token-authenticated trace-link, pull-request-link, status,
  comment, and closure payloads for profile-supported Shipped actions; every
  other field produces no payload. Verifies AC11.
- Assert each such Jira or Jira Align mutation receives a distinct
  authorized-local-approver confirmation; confirmation reuse or an unauthorized
  identity records zero requests, and success records identity and timestamp.
  Verifies AC5, AC12.
- Assert every Jira SSO-cookie non-GET/HEAD attempt raises before the fake
  transport records a request, including raw-call paths. Verifies AC14.
- Assert auth, redaction, unsupported custom-field mapping, and remote
  partial-failure results are fail-closed and retry-safe. Verifies AC12, AC16,
  AC18.
- Assert both clients validate configured schemes, profile hosts, resolved
  address ranges, redirect hops, and rebound DNS before credential loading or
  fake transport use. Verifies AC21-AC22.
- Assert Jira and Jira Align refresh/write-back actions declare minimal
  `allowed-tools` and `metadata.boundaries` and preserve each client's accurate
  credentialed/auth/fallback/namespace/key metadata. Verifies AC23.

**Approach:**

- Add configured refresh processor skills that compose with the existing
  `jira` and `jira-align` clients.
- Reuse existing narrow commands only for the AC11 allowlist when they meet the
  profile contract; do not broaden raw-call authority.
- Declare SSO-cookie remote writes unavailable while retaining read acquisition
  and local reviewed refresh.

**Done when:** both Atlassian profiles pass the common matrix, token write
fixtures match exact payloads, and all SSO-cookie write tests record zero
requests.

### T5: GitHub refresh and coordination write-back pass command fixtures

**Depends on:** T1

**Touches:** packs/github/.apm/skills/*refresh*/**, packs/github/.apm/skills/github-brief-intake/SKILL.md, packs/github/tests/**

**Verification mode:** TDD

**Tests:**

**Stub:** `true` — the red contract surface uses fake coordinator and command
runner protocols until the GitHub processor exists.

```python
# STUB: AC22 — GitHub target and host come only from trusted configuration
def test_github_rejects_tracker_selected_host(github_processor, confirmation):
    result = github_processor.write(
        action="comment", tracker_host="attacker.invalid", confirmation=confirmation
    )
    assert result.code == "untrusted_github_host"
    assert result.command_calls == 0


# STUB: AC15 — instruction-shaped content stays one data value
def test_github_content_cannot_add_argv(github_processor, confirmation):
    result = github_processor.write(
        action="comment", body="--hostname attacker.invalid", confirmation=confirmation
    )
    assert result.argv.count("--hostname") == 1
    assert result.stdin == "--hostname attacker.invalid"
```

- Run milestone/issue normalized records through the common lifecycle matrix.
  Verifies AC3-AC13.
- Assert confirmed Shipped comments, trace links, pull-request links, status,
  and closure construct the exact allowed `gh` commands, while every other
  coordination field and requirement/body edit constructs none. Verifies
  AC11-AC12.
- Assert every generated comment, trace link, pull-request link, status, or
  closure command consumes a distinct authorized-local-approver confirmation;
  reused or unauthorized confirmation runs no command, and success records
  identity and timestamp. Verifies AC5, AC12.
- Assert issue-body or requirement edits, inferred repository targets, missing
  authentication, and failed commands produce no secondary mutation. Verifies
  AC1, AC11, AC12, AC18.
- Assert instruction-shaped issue content remains quoted data and cannot add
  command arguments. Verifies AC15-AC16.
- Assert GitHub host selection accepts only trusted repository or administrator
  configuration, keeps credentials host-bound, and rejects tracker-supplied,
  mismatched, or untrusted hostnames/URLs before fake `gh` invocation. Assert
  argv-list and stdin isolation without mocking or claiming `gh`'s internal
  redirect/DNS controls. Verifies AC15, AC22.
- Assert the GitHub refresh action declares only the `gh`/filesystem tools and
  boundaries it uses and carries exactly `credentialed: true`,
  `primitive-class: credentialed-cli`, and `auth: cli`, with no `namespace`,
  `keys`, or non-contract auth identifier. Verifies AC23.

**Approach:**

- Add a GitHub configured refresh processor using `gh`; do not add a parallel
  HTTP client.
- Move reusable optional write-back rules out of `github-brief-intake` into the
  processor while preserving intake behavior.
- Pin repository, issue/milestone identifier, and source revision from
  normalized provenance before command construction.
- Resolve the GitHub host only from trusted repository or administrator
  configuration and keep tracker-derived values confined to argv-list or stdin
  data positions.

**Done when:** GitHub passes the lifecycle matrix and every fake `gh`
invocation is confirmed, target-pinned, allowlisted, and shell-safe.

### T6: Published tracker refresh surface passes catalogue, eval, and site gates

**Depends on:** T2, T3, T4, T5

**Touches:** packs/core/{README.md,JOURNEY.md,pack.toml,.claude-plugin/plugin.json}, packs/linear/{README.md,pack.toml,.claude-plugin/plugin.json}, packs/github/{README.md,pack.toml,.claude-plugin/plugin.json}, packs/atlassian/{README.md,JOURNEY.md,pack.toml,.claude-plugin/plugin.json}, guides/_shared/how-to/use-work-intake.md, guides/_shared/how-to/choose-a-tracker-integration.md, guides/_shared/reference/tracker-vocabulary.md, guides/core/reference/work-intake-routing-and-lifecycle.md, guides/core/how-to/orient-at-session-start.md, guides/linear/how-to/linear-brief-intake-and-sync.md, guides/github/how-to/intake-a-github-milestone-as-a-brief.md, guides/atlassian/**, docs/product/changelog.md, docs/specs/tracker-refresh-writeback/notes/refresh-capability-walkthrough.md, .claude-plugin/marketplace.json

**Verification mode:** Goal-based check with manual rendered review

**Tests:**

**Stub:** no stub (goal-based check with manual rendered review).

- Add or update activation and behavior evals for each user-triggered refresh
  surface, including near misses for tracker status/triage and ordinary intake.
  Verifies AC18-AC20.
- Run catalogue lint/verify and self-host projection; assert pack/plugin
  versions match and generated marketplace content is clean. Verifies AC19.
- For every changed processor, compare source and each supported adapter
  projection and assert minimal `allowed-tools`, `metadata.boundaries`, and
  credentialed-auth metadata survive byte-equivalently without broadening.
  Assert the GitHub source and projection retain the exact credentialed-CLI
  values from T5 and reject `auth: gh`, `primitive-class: approved-cli`,
  `namespace`, or `keys`. Verifies AC23.
- Run guide validation, guide-index coverage, site generation, marketing
  build, and docs-site build in canonical order. Verifies AC19.
- Search current guides and pack pages for claims that Linear is the sole
  refresh exception or Jira/Jira Align are always one-way. Verifies AC13, AC19.
- Create
  `docs/specs/tracker-refresh-writeback/notes/refresh-capability-walkthrough.md`
  from one rendered no-write refresh flow per tracker, recording scope,
  fixture inputs, observed outputs/routes, run/session boundary, reviewer, and
  date. Verifies AC11, AC13, AC17, AC20.

**Approach:**

- Update the shared `work-intake` how-to/reference first, then tracker-specific
  pages and pack landing surfaces.
- State tracker capability and authentication limitations explicitly,
  including Jira SSO-cookie read-only behavior.
- Apply required minor bumps for new primitives or patch bumps for body-only
  changes without riding unrelated unreleased versions.
- Run self-host only after every source and metadata edit.

**Done when:** all catalogue, least-privilege projection, eval, guide, and site
gates pass; a cold reader can find and follow refresh for each supported
tracker from the public entry point; and the dated capability walkthrough
contains complete evidence for all four profiles.

## Rollout

- **Delivery:** ship after Groups 2-5. The shared coordinator and status
  support land before tracker processors. Each processor remains unavailable
  through `work-intake` until its tests, capability declaration, and guide land.
- **Infrastructure:** none; refresh remains user-triggered and uses existing
  tracker clients, CLIs, and credential brokers.
- **External-system integration:** no live tracker migration is required.
  Profile and schema versions must match the installed Group 2/5 contracts.
- **Deployment sequencing:** T1 → T2 and T3/T4/T5 → T6. Group 7 begins only
  after T6 supplies the final refresh-state matrix.
- **Rollback:** disable the affected processor in the profile registry and
  return to Group 4's fail-closed “refresh unavailable” result. Local artifacts
  remain authoritative; no rollback deletes source decisions.
- **Irreversibility:** a confirmed remote tracker mutation may not be
  reversible. Every such action is separately confirmed and narrow.

## Risks

- A tracker-specific field model may tempt the implementation to fork
  authority behavior. The shared lifecycle suite is the convergence gate.
- A remote mutation can succeed after the local decision is durable and then
  fail to report success. Retry-safe result handling and explicit confirmation
  limit duplicate writes.
- Jira authentication capability can be confused with tracker profile support.
  The capability matrix keeps SSO-cookie writes unavailable without declaring
  Jira refresh unsupported.
- Group 2-5 interfaces may change before implementation. Reconcile exact
  schemas and public symbols before plan approval.
- Documentation can imply stronger write support than an adapter provides.
  Each profile's tested capability declaration is the source for guide claims.

## Changelog

- 2026-08-09: Initial plan drafted from accepted RFC-0083 with confirmed
  assumptions; local authority and remote write-back are deliberately separate
  operations.
- 2026-08-17: Pre-EXECUTE review found that Groups 3–5 shipped no generic
  guarded artifact/workspace writer, configured refresh registry, or closed
  refresh authority/confirmation contract. T1 now owns those missing seams;
  T2 includes required package/MCP projection work, and T6 updates the existing
  lifecycle reference instead of creating a duplicate authority page.
- 2026-08-18: Final review exposed four under-specified construction checks.
  T1 now pins rejection-preserving dependencies/receipts and accepted-field
  ownership, T3 preserves corporate proxy/trust behavior under DNS pinning,
  and T5/T6 pin GitHub to the repository's closed credentialed-CLI metadata.
