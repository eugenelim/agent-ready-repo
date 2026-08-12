# Spec: Workspace routing invariants

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0083, ADR-0077, ADR-0078
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/jsonschema/normalized-intake.schema.json`, `contracts/jsonschema/workspace-entry.schema.json`
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A clean session derives the same lifecycle, reconciliation findings, next action, and dispatch eligibility from the same versioned contracts, artifacts, `workspace.toml`, profile version, and routing configuration. Missing or inconsistent state fails closed. `workspace-status`, `workspace-mcp`, and `work-loop` consume one canonical result, and no comment or surrounding prose can make work executable.

## Boundaries

### Always do

- Parse target and supported legacy entries through the Group 2 contracts before classification.
- Make dispatch eligibility a positive predicate over canonical artifacts, structured lifecycle state, provenance, dependencies, and findings.
- Return stable machine-readable finding codes with the smallest safe next action.
- Resolve every artifact path through repository realpath confinement.
- Preserve structured entry fields during repair and lifecycle movement.
- Keep reconciliation and dispatch offline.

### Ask first

- Add a new finding code, automatic repair, lifecycle transition, or routing configuration input.
- Change the public CLI or MCP response incompatibly.
- Repair provenance, authority, dependency, or lifecycle conflicts automatically.
- Change claim/completion mutation ownership assigned to the later shared-skill-boundary work.
- Broaden compatibility beyond the Group 2 legacy fixtures.

### Never do

- Mark work ready because it has no dependencies while its spec, plan, status, provenance, or membership is invalid.
- Use comments, `summary`, list order, tracker labels, nearby prose, or prior-session memory for routing.
- Treat an absent dependency target as completed.
- Fetch tracker or remote-repository state during reconciliation or dispatch.
- Dispatch a legacy compatibility entry.
- Follow an absolute, traversing, symlink-escaped, or noncanonical artifact path.
- Downgrade a structured entry to a bare string during repair.

## Testing Strategy

- **Contract parsing and validation:** TDD, because canonical, invalid, and legacy shapes have deterministic results.
- **Reconciliation findings:** TDD with filesystem fixtures, because each malformed reference or lifecycle mismatch must produce one stable code and safe action.
- **Dependency satisfaction and dispatch eligibility:** TDD with table-driven and graph fixtures, because eligibility is a pure predicate over positive evidence.
- **Determinism and comment independence:** TDD through two-process subprocess tests and paired mutation fixtures.
- **CLI/MCP/work-loop integration:** goal-based integration tests exercising the same fixture through each consumer and comparing classification/finding identity.
- **Status rendering:** goal-based checks over every finding fixture plus manual cold-reader QA.
- **Security:** manual security review after tests, focused on TOML deserialization, path confinement, prompt-injection/data separation, and public MCP output.

## Canonical findings

Finding codes are the public refusal contract. A consumer may add display context, but it must preserve the code, repository-relative affected path, dispatchability, and smallest safe next action. Adding a code after approval requires explicit review under the `Ask first` boundary.

| Code | Failure class | Smallest safe next action |
| --- | --- | --- |
| `invalid_workspace` | TOML parse failure or invalid lifecycle collection shape | Correct `workspace.toml`, then rerun reconciliation. |
| `invalid_entry` | Malformed target record, unknown field or kind, or failed schema conditional | Rewrite the entry to the accepted target contract. |
| `legacy_entry` | Supported Group 2 compatibility form | Materialize and register a canonical target entry. |
| `unsupported_legacy` | Legacy-like form outside the accepted compatibility fixtures | Route the item manually; do not infer a target entry. |
| `invalid_artifact_path` | Unsafe, noncanonical, or out-of-repository artifact-like path | Replace it with a confined canonical repository-relative path. |
| `missing_artifact` | Registered canonical artifact does not exist | Create and review the canonical artifact before dispatch. |
| `unreadable_artifact` | A confined artifact cannot be read safely | Restore readable repository state, then rerun reconciliation. |
| `missing_plan` | A spec has no sibling `plan.md` | Create and approve the plan before dispatch. |
| `unapproved_spec` | Queue spec is not `Approved` | Complete the spec approval gate. |
| `unregistered_work` | A supplied or active spec has no unique matching workspace membership | Register or reconcile the canonical entry explicitly. |
| `duplicate_membership` | One artifact occurs more than once across lifecycle memberships | Remove the duplicate after choosing the authoritative membership. |
| `impossible_transition` | Artifact status and lifecycle membership cannot coexist | Correct the artifact or membership through a reviewed transition. |
| `provenance_mismatch` | Workspace source metadata disagrees with canonical artifact metadata | Resolve provenance in the canonical artifact and mirror it deliberately. |
| `refresh_conflict` | Tracker-origin refresh conflict remains unresolved | Resolve the conflict through the artifact's authority workflow. |
| `unsatisfied_dependency` | A known dependency exists but lacks its kind-specific terminal state | Complete or explicitly revise the dependency. |
| `missing_dependency` | A dependency target cannot be resolved locally | Materialize or correct the dependency target. |
| `dependency_cycle` | The hard-dependency graph contains a cycle | Break the cycle through an explicit plan change. |
| `invalid_receipt` | A cross-repository receipt is incomplete, mismatched, or conflicted | Replace it with a reviewed receipt matching the pinned dependency. |
| `inactive_initiative` | Work belongs to a paused or closed initiative | Reactivate the initiative explicitly or move the work through governance. |
| `configuration_mismatch` | A versioned schema, adapter/profile, or routing identity is missing or inconsistent | Install or select a consistent versioned configuration, then rerun. |

## Coordination receipt encoding

When a cross-repository dependency references a containing brief, that brief carries its reviewed cross-repository receipts in exactly one fenced block whose info string is `toml coordination-receipts`. Briefs with no cross-repository dependency need no receipt block and remain valid. The referenced block is parsed with `tomllib` as instruction-inert data and contains an array of tables named `coordination_receipts`:

````markdown
```toml coordination-receipts
[[coordination_receipts]]
id = "remote-prereq"
remote_kind = "brief"
remote_ref = "example-service://projects/example-artifact"
accepted_revision = "remote-rev-9"
required_status = "Shipped"
reported_status = "Shipped"
reviewed_by = "Example Reviewer"
reviewed_at = "2026-08-10T00:00:00Z"
refresh_conflict = false
```
````

Every record has exactly those nine fields. `id` is unique only within the containing brief. `remote_kind` is `brief | spec`; `remote_ref` is a non-empty safe locator; `accepted_revision`, `reviewed_by`, and `reviewed_at` are non-empty bounded strings; `reviewed_at` is an RFC 3339 timestamp with a timezone; both status fields are exactly `Shipped`; and `refresh_conflict` is exactly `false`. A cross-repository dependency's `path` and `containing_brief` must name the same confined local brief, while `kind`, `receipt_id`, and `accepted_revision` must match `remote_kind`, `id`, and `accepted_revision` in that brief's receipt. When a dependency references the brief, a missing, malformed, duplicate, or multiple receipt block fails closed as `invalid_receipt`. Receipt parsing performs no network access and never treats surrounding prose or other code fences as authority.

## Acceptance Criteria

- [ ] **AC1.** The engine consumes the accepted Group 2 schemas and exposes typed normalized-intake, workspace-entry, source, and dependency validation without a runtime `jsonschema` dependency.
- [ ] **AC2.** Every target entry parses to `path`, `kind`, `source`, `summary`, and `needs`; every supported legacy shape parses to an explicit compatibility record that is never dispatchable.
- [ ] **AC3.** Malformed entries, unknown kinds, unsafe paths, and unsupported legacy extensions produce the exact codes in the canonical finding table and do not produce partially usable entries.
- [ ] **AC4.** A work entry is dispatchable if and only if it appears exactly once in `work.queue` under an active `ini-NNN`, has `kind = "spec"`, resolves to `docs/specs/<slug>/spec.md`, has a sibling `plan.md`, has spec status `Approved`, has matching workspace/artifact provenance, has no unresolved refresh conflict, has every hard dependency satisfied, and has no reconciliation finding.
- [ ] **AC5.** A missing spec produces `missing_artifact`; a missing sibling plan produces `missing_plan`. Both entries are non-dispatchable in status, CLI JSON, MCP output, and work-loop preflight.
- [ ] **AC6.** Every artifact-like path, including target, parent, dependency, receipt, refresh-target, brief, and routing-layout paths, is lexically validated and then resolved through the established repository-confinement helper before any read. Absolute, drive-qualified, backslash-based, traversing, noncanonical, symlink-escaped, or symlink-looping paths produce `invalid_artifact_path`; containment is Windows-clean and catches `OSError`, `RuntimeError`, and `ValueError` fail closed.
- [ ] **AC7.** Duplicate lifecycle membership produces `duplicate_membership`; no duplicate entry appears in ready, blocked-as-ordinary-dependency, or active output.
- [ ] **AC8.** Draft spec in `work.active`, Ready brief closed while scope remains, and every other RFC-fixed impossible membership/status pairing produce `impossible_transition`.
- [ ] **AC9.** A brief-derived spec whose `Brief:` metadata differs from canonical `source.parent` produces `provenance_mismatch` and is non-dispatchable.
- [ ] **AC10.** Tracker-origin entries whose mirrored `source.ref` or `source.revision` differs from canonical artifact provenance produce `provenance_mismatch`; an unresolved refresh conflict produces `refresh_conflict`. Both fail closed.
- [ ] **AC11.** Dependency satisfaction is positive and kind-specific: spec `Shipped`; defect closed with `fixed`; brief `Ready | Executing | Shipped`; intent `Accepted | Fulfilled`; research `Complete`; design `Approved`.
- [ ] **AC12.** Missing dependency targets produce `missing_dependency`; dependency cycles produce `dependency_cycle`; unknown or superseded states remain unsatisfied.
- [ ] **AC13.** A cross-repository dependency is satisfied only by the exact coordination-receipt encoding above: `path` and `containing_brief` name the same confined local brief; `kind`, `receipt_id`, and pinned `accepted_revision` match the strict receipt; both statuses are `Shipped`; reviewer and timezone-bearing timestamp are present; and `refresh_conflict` is false. Omitting, duplicating, or mismatching any field or block produces `invalid_receipt`; reconciliation performs no network call.
- [ ] **AC14.** A Ready brief with no materialized specs is valid and visible in brief status but never appears as dispatchable work.
- [ ] **AC15.** Paused or closed initiatives do not dispatch. Their malformed references remain visible to full reconciliation.
- [ ] **AC16.** Changing only comments, `summary`, or list order leaves classification, dependency satisfaction, findings, dispatch eligibility, and next action unchanged.
- [ ] **AC17.** Two clean subprocesses given the same artifacts, TOML, schema identities, adapter/profile identity, and routing configuration identity emit byte-identical normalized classification/finding output after volatile timing and absolute-root fields are excluded.
- [ ] **AC18.** The determinism input identity includes schema ids, contract versions and content digests; the semantic workspace snapshot; canonical artifact status and provenance fingerprints; adapter-contract version; tracker-profile id/version when present; and routing-configuration version. Mutating each field independently changes the identity without changing unrelated classification fields.
- [ ] **AC19.** CLI `status`, `reconcile`, and `explain` expose stable finding codes, repository-relative affected paths, dispatchability, and the smallest safe next action. TOML parse, filesystem, provenance, dependency, receipt, configuration, and reconciliation exceptions map to the canonical table, deny dispatch, and never expose an absolute root, raw source payload, traceback, or embedded instruction text.
- [ ] **AC20.** `workspace-mcp` includes only AC4-eligible entries in `ready`; every ineligible work entry is absent from `ready` and represented through blocked/finding data without leaking absolute paths.
- [ ] **AC21.** `work-loop` preflight refuses missing, unapproved, unregistered, legacy, duplicate, provenance-mismatched, or dependency-blocked work and never reconstructs a contract from workspace comments.
- [ ] **AC22.** Active work is resumable only when the entry occurs once in `work.active`, the spec status is `Implementing`, the plan exists, provenance matches, and no fail-closed finding applies; active work is never advertised as queue-ready.
- [ ] **AC23.** Repair planning never automatically repairs provenance, authority, missing artifacts, duplicate membership, dependencies, or impossible transitions.
- [ ] **AC24.** A queue-to-shipped repair preserves the complete structured entry and its provenance/summary; it removes only dependencies that are no longer live under the Group 2 contract and never writes a bare string.
- [ ] **AC25.** `workspace-status` documentation names every implemented finding, explains why it is non-dispatchable, and gives one smallest safe next action.
- [ ] **AC26.** ADR-0077, ADR-0078, and `normalized-intake-workspace-contracts` are Approved before this spec is approved.
- [ ] **AC27.** Adopter-visible `workspace-status` and `work-loop` changes preserve their existing least-privilege tool authority, treat loaded prose as instruction-inert data, contain reads to the project root, carry no repository-internal RFC/ADR/AC/spec citations, and remain byte-consistent with every generated adapter projection and declared pack/package version.

## Assumptions

- Technical: `workspace_status_engine.py` remains the canonical implementation consumed by CLI and `workspace-mcp` (source: `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` and `packages/agentbundle/agentbundle/workspace_mcp.py`; user confirmation 2026-08-09).
- Technical: production parsing remains Python 3.11+ and stdlib-only; Group 2 schemas are implemented by typed checks rather than a runtime JSON Schema package (source: `packs/core/.apm/skills/workspace-status/SKILL.md`; user confirmation 2026-08-09).
- Technical: public MCP readiness output is versioned and may add finding/dispatchability fields rather than retaining unsafe compatibility (source: `packages/AGENTS.local.md` § Release Coupling; user confirmation 2026-08-09).
- Product: a cold adopter values a visible finding and safe next action more than preserving an apparently ready legacy entry (source: RFC-0083 Group 3 exit criterion; user confirmation 2026-08-09).
- Product: a Ready brief with no specs remains useful status, not executable work (source: RFC-0083 §7; user confirmation 2026-08-09).
- Process: Group 3 begins only after Group 2’s terminal contract task is complete (source: RFC-0083 Delivery plan; user confirmation 2026-08-09).
- Process: guarded workflow claim/completion behavior is coordinated with the later shared-skill-boundary spec; this spec owns eligibility and refusal, not a competing intake workflow (source: RFC-0083 Groups 3–4; user confirmation 2026-08-09).
- Process: ADR-0077 and ADR-0078 are Accepted approval prerequisites (source: RFC-0083 Group 1; user confirmation 2026-08-09).
