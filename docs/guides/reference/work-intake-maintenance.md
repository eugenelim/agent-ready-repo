# Maintaining work intake, refresh, and legacy migration

This reference is for catalogue maintainers changing an intake adapter, the
shared router, workspace reconciliation, refresh, or the temporary compatibility
reader. The public behavior is one pipeline; each component owns a narrow part.

## Responsibility map

| Component | Owns | Must not own |
| --- | --- | --- |
| Source adapter | Bounded acquisition, provenance, profile-version hints, strict normalization | Artifact classification, repository writes, authorization |
| `work-intake` | Content-based route, artifact-before-registration sequencing, processor selection | Tracker vocabulary, source credentials, legacy conversion |
| Canonical artifact | Requirements, decisions, acceptance state, tracker-origin authority block | Workspace membership |
| `workspace.toml` | Artifact path/kind, lifecycle membership, source mirror, display summary, hard dependencies | Requirements or comment-backed routing |
| Processor | The artifact-specific workflow selected by the route | Reclassifying the source from tracker object names |
| Refresh processor | Exact-profile acquire/map/compare and declared local or remote coordination capability | Reusing intake authorization or bypassing lifecycle locks |
| `workspace-status` | Read-only status, reconciliation, migration planning, authorized ledger/apply/rollback | Authoring artifacts or human route/authorization inputs |

Target workspace entries conform to
`contracts/jsonschema/workspace-entry.schema.json` and contain exactly `path`,
`kind`, `source`, `summary`, and `needs`. Comments, summaries, order, tracker
labels, and profile hints are non-semantic. Only a uniquely registered Approved
spec with an existing sibling plan can enter `canonical.ready`; only a valid
registered active spec can enter `canonical.active`.

## Adapter contract

An adapter validates its destination and resource budget, acquires only bounded
fields, treats all source content as untrusted data, and emits
`normalized-intake.v1`. The shared router alone decides intent, brief, spec,
defect, direct-light, Draft-with-gaps, status, remember, or refresh behavior.
Equivalent normalized content must produce the same route for Jira, Jira Align,
GitHub, and Linear.

Intake adapters are read-only at the tracker boundary. A configured refresh
processor is a separate capability. It resolves by exact profile ID and version;
missing or mismatched registration returns a no-effect result. Any supported
remote coordination action needs a fresh confirmation for its exact action,
target, profile, and payload digest.

## Authority and refresh

Workspace source mode is closed to `repo-origin` or `tracker-origin`.
Tracker-origin artifacts carry exactly one closed `source-authority.v1` block.
Its field ownership map assigns each field to `source` or `local`, while
compared/accepted revisions, decisions, conflicts, and receipts make changes
auditable. Repository-origin work remains locally authoritative.

Lifecycle locks are enforced by the refresh processor, not inferred by an
adapter. Draft, Accepted, Ready, Approved, Implementing, Executing, and Shipped
must each remain represented in the versioned evaluation matrix. Local field
decisions and remote coordination are separate effects and separate evidence.

## Reconciliation findings

Finding codes are public behavior. Add or change one only with its stable safe
next action, CLI projection, tests, guide reference, and evaluation result.
Reconciliation fails closed for malformed or duplicate entries, missing
artifacts/plans, invalid transitions or provenance, unresolved refresh state,
dependency failures, inactive initiatives, and configuration mismatches.
Accepted legacy shapes return `legacy_entry` and remain non-dispatchable;
unknown or private shapes return a manual-routing finding without mutation.

## Migration transaction

Migration planning consumes one reviewed, human-authored
`work-intake-migration-selection.v1` file and is read-only. The tool reports
observed candidates; it never chooses a route or creates, edits, prefills, or
suggests substantive selection values. Apply and rollback each consume a fresh,
single-use, human-authored `work-intake-migration-confirmation.v1` file whose
role is allowed by repository `[authorization.migration]` policy.

The repository-root `.workspace-migrations.json` ledger is written before the
workspace effect. Operations move through `pending`, `applied`,
`rollback_pending`, and `rolled_back`; confirmation receipts are consumed before
their effect. All migration effects share `.workspace-repair.lock`, recheck
fingerprints inside the lock, preserve exact legacy TOML slices, and leave
canonical artifacts untouched. Recovery resolves a durable pending state; it
does not guess after a fingerprint conflict.

## Compatibility release discipline

New writers and seeds emit only target entries. `capture-work` remains a
deprecation-emitting forwarding alias, and the accepted legacy reader remains
installed, until every removal predicate in RFC-0083 is proven and its Approver
authorizes a separately planned removal. The initial delivery records the
evidence state but does not satisfy or weaken that later gate.

Rollback during the window disables target writers, returns to the preceding
dual-reader release, and uses the current ledger-backed rollback operation to
restore the exact legacy workspace representation. It never deletes a canonical
artifact or migration evidence.

## Evaluation and release checklist

When any component changes:

1. Update the shared routing matrix and the affected profile matrix.
2. Preserve acquisition → normalization → routing → authority/refresh coverage
   and all seven lifecycle states for every supported profile.
3. Run the integrated evaluator in two independent clean roots and require
   byte-identical normalized results and next actions.
4. Run workspace-status migration planning/effect/CLI tests, including rollback
   and failure seams.
5. Update the owning pack and plugin versions together, add user-facing release
   notes, then regenerate self-hosted projections and marketplace metadata.
6. Build marketing before docs, audit emitted links, and inspect generated
   canonical and compatibility routes rather than editing generated output.

The schemas under `contracts/jsonschema/`, the scripts under the owning
`.apm/skills/` directories, and their construction tests are mechanically
authoritative. This page explains how those contracts fit together; it does not
replace them.
