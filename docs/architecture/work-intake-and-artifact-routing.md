# Work intake and artifact routing

## 1. Purpose and boundary

`work-intake` is the shared local front door for starting, remembering,
inspecting, and refreshing repository work. It classifies content by delivery
role, writes a canonical artifact before its lifecycle entry when a durable
route is selected, and dispatches only after both are valid. An eligible
explicit direct-light request remains session-local.

Tracker adapters acquire and normalize; they do not classify artifacts or write
repository state. `workspace-status` reads and reconciles repository state and
owns the temporary reviewed migration transaction for accepted legacy entries.
Configured refresh processors compare tracker-origin artifacts and may apply
authorized local changes or separately confirmed coordination actions.

## 2. Entrypoints

- `work-intake` selects direct-light, intent, brief, spec, defect,
  Draft-with-gaps, remember, status, or refresh behavior.
- `workspace-status` reports canonical ready, active, blocked, shipped,
  authority, refresh, reconciliation, and retained legacy state.
- Jira, Jira Align, GitHub, and Linear intake adapters emit the same strict
  normalized contract and delegate the route.
- Profile refresh processors resolve by exact profile ID/version and return a
  closed comparison/effect result.
- `capture-work` is a temporary compatibility alias that emits a deprecation
  notice and forwards to `work-intake` without separate semantics.

## 3. Owned state and write authority

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Canonical requirements and decisions | `docs/product/`, `docs/specs/`, and other registered artifact paths | Owning artifact workflow | Processors, reviewers, reconciliation |
| Lifecycle index | `workspace.toml` | `work-intake`, selected workflows, and reviewed migration/repair effects | `workspace-status`, execution, review |
| Tracker-origin authority | One closed `source-authority.v1` block in the canonical artifact, mirrored by structured workspace source fields | Accepted intake/refresh workflow | Refresh and reconciliation |
| Refresh receipts | Authority block plus guarded artifact/workspace pair | Exact configured refresh processor | Status and later refresh |
| Migration ledger | `.workspace-migrations.json` | Authorized `workspace-status` migration transaction | Recovery, rollback, audit |
| Selection and confirmation | Human-authored repository-relative JSON supplied out of band | Human reviewer/approver | Migration planner/effect only |
| Direct-light decision record | Active session only | `work-loop` | Requester and current session |

`workspace.toml` indexes artifacts and lifecycle facts. It is not a
requirements store. Target entries contain exactly `path`, `kind`, `source`,
`summary`, and `needs`; comments, summaries, order, labels, and hints cannot
select a route, satisfy a dependency, or authorize dispatch.

## 4. Dependencies and allowed edges

Source adapters may acquire and normalize external input. Only `work-intake`
classifies that input. Artifact processors receive the selected route after the
artifact and workspace state exist; they do not reconstruct a contract from
index prose. Refresh processors receive an existing registered artifact, exact
profile identity, lifecycle, authority, and revision pair.

Repository-origin work is locally authoritative. Tracker-origin work has a
closed per-field `source`/`local` ownership map and compared/accepted revisions.
Lifecycle locks and explicit decisions govern local refresh. A remote tracker
coordination action is a separate effect with its own fresh exact confirmation;
neither tracker content nor intake authorization can approve it.

## 5. Primary flows

1. An adapter or local request produces validated normalized intake.
2. `work-intake` classifies the content. Direct-light stays session-local;
   durable routes materialize the artifact, then register its target entry.
3. `workspace-status` reconciles the artifact, membership, plan, provenance,
   authority, dependencies, and lifecycle. Only canonical ready or active specs
   may start or resume the work-loop.
4. Every workspace-dispatchable, queued, or resumable build item resolves to an
   existing durable `spec.md` and sibling `plan.md`; execution receives those
   files rather than tracker payloads or index comments. An explicit
   direct-light request is session-local, creates no workspace entry, and is
   ineligible for argless dispatch or fresh-session resumption.
5. Refresh resolves the exact configured processor, acquires and compares one
   source revision, presents field decisions, and applies guarded local changes
   only after authorization. Remote coordination remains separately confirmed.
6. A supported legacy membership stays visible and non-dispatchable until a
   human supplies a reviewed route selection. Planning is read-only; apply is
   ledger-first; rollback restores the exact legacy slice without deleting the
   canonical artifact.

Classification routes an explicit start to exactly one durability class:

```text
explicit start
    |
validate and classify
    |
    +-- direct light --> work-loop from current request
    |
    +-- durable single slice --> spec + plan --> workspace --> work-loop
    |
    +-- multi-slice outcome --> brief --> confirmed specs + plans
```

The end-to-end pipeline those classes execute in:

```text
source adapter ── normalized-intake.v1 ──> work-intake
                                                |
              +---------------------------------+------------------+
              |                                 |                  |
        direct-light                    artifact + index       status/refresh
        (session only)                         |                  |
                                               v                  v
                                        processor/work-loop   workspace-status
```

## 6. Failure and recovery behavior

Missing, malformed, duplicate, unsafe, or inconsistent state becomes a stable
non-dispatchable reconciliation finding with one safe next action. An
unavailable or version-mismatched refresh processor performs no mutation.
Unresolved authority or lifecycle conflicts stop before an artifact write.

Migration serializes through `.workspace-repair.lock`, rechecks the workspace,
ledger, selection, and artifact fingerprints inside the lock, and consumes
fresh authorization before effects. A durable `pending` or `rollback_pending`
operation is recovered from the ledger. A concurrent change or malformed
ledger fails closed; canonical artifacts and unknown/private TOML extensions
are never deleted or silently rewritten.

## 7. Observability, evidence, and the compatibility window

`workspace.toml`, canonical artifacts, and `workspace-status` provide the
observable routing and lifecycle record. Provenance records the source locator
and revision without copying credentials or a tracker payload.

All current writers and the workspace seed emit only target entries. The
accepted legacy reader and `capture-work` forwarding alias remain installed in
the initial delivery. Their later removal is a separate, non-dispatchable
follow-up gated by RFC-0083's release count, elapsed time, advance notice,
fixture/writer/guide/rollback evidence, and check-before-effect Approver
authorization.

Rollback returns writers to the preceding dual-reader release and uses the
ledger to restore legacy workspace representation. It preserves target
artifacts and migration evidence.

## 8. Mechanical invariants and evaluation

- JSON Schemas own normalized intake, target entries, authority/refresh, and
  migration selection/confirmation/ledger/result shapes.
- Reconciliation owns stable finding codes and never makes legacy entries
  dispatchable by inference.
- The integrated routing matrix runs acquisition, normalization, routing,
  authority/refresh, and read-only migration planning across Jira, Jira Align,
  GitHub, and Linear in two clean roots; canonical results and next actions must
  be byte-identical.
- Pack/plugin versions move together for non-cosmetic pack changes. Self-hosted
  projections and marketplace metadata are generated from pack sources.
- Marketing builds before docs, followed by emitted-link validation.

These skill scripts run in the finish-time checklist and can run as fail-closed
CI gates where a PR event and Python exist. They do not fail closed inside an
arbitrary adopter repository.

- `lint-spec-status.py` checks `docs/specs/*/spec.md` metadata against the
  status contract in `CONVENTIONS.md` §4.
- `lint-traceability.py` flags structural orphans across the product chain.
- `lint-brief-coverage.py` rolls each brief's Spec map from `Brief:` back-links
  and requires a non-empty map of shipped specs for delivery.

Maintainer procedures live in
[Maintaining work intake, refresh, and legacy migration](../guides/reference/work-intake-maintenance.md).

## 9. Relevant decisions

- [RFC-0083 — Work intake and artifact routing](../rfc/0083-work-intake-and-artifact-routing.md)
- [ADR-0009 — Product brief layer and plan-owned LLD](../adr/0009-product-brief-layer-and-plan-owned-lld.md)
- [ADR-0019 — Product intent ontology and brief projection](../adr/0019-product-intent-ontology-and-brief-projection.md)
- [ADR-0033 — Intent-level open recognized set decoupled from scale](../adr/0033-intent-level-open-recognized-set-decoupled-from-scale.md)
- [ADR-0077 — Feature projection and tracker authority](../adr/0077-feature-projection-and-tracker-authority.md)
- [ADR-0078 — Standalone intake and deterministic workspace index](../adr/0078-standalone-intake-and-deterministic-workspace-index.md)
- [ADR-0092 — Direct-light execution is session-local](../adr/0092-direct-light-execution-session-local-boundary.md)
  — the decision this page's §5 invariant records; it refines ADR-0078's
  start-route materialization rule for captured and indexed items while leaving
  its workspace-entry dispatchability rule unchanged.

## 10. Last verified against commit

`297739e4`

Verified against the Group 2–7 schema, runtime, evaluation, and documentation
surfaces.
