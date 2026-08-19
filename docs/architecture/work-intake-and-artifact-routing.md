# Work intake and artifact routing

## 1. Purpose and boundary

`work-intake` turns local or tracker-supplied work into a canonical repository
artifact and lifecycle entry. It classifies content by its delivery role rather
than by a tracker label.

It does not replace a tracker or provide tracker refresh. Refresh remains
adapter-owned and does not write repository state until a compatible adapter
implements its contract.

## 2. Entrypoints

- `work-intake` accepts standalone work and routes it to an intent, brief,
  spec, defect, or non-dispatchable capture.
- `workspace-status` reads artifact and lifecycle state to report next work,
  blocking references, and reconciliation findings.
- Tracker adapters acquire and normalize source data before routing it through
  `work-intake`.

## 3. Owned state and write authority

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Canonical work artifacts | `docs/product/` and `docs/specs/` | The workflow that creates the artifact | Workflows, contributors, reviewers |
| Lifecycle index | `workspace.toml` | `work-intake` and its selected workflow | `workspace-status`, execution, review |
| Tracker provenance | Canonical artifact and its index entry | The accepting intake workflow | Refresh and reconciliation workflows |

`workspace.toml` indexes artifacts and lifecycle facts. It is not a
requirements store.

## 4. Dependencies and allowed edges

Tracker adapters may acquire and normalize external input. Only the local intake
route classifies it and writes canonical artifacts. Processors consume an
existing artifact and workspace entry; they do not reconstruct a contract from
index comments.

The repository artifact is authoritative for repo-origin work. Imported
tracker fields remain source-owned until local acceptance. This ownership rule is
documented; this page does not claim a command enforces it.

## 5. Primary flows

1. `work-intake` acquires supplied material, normalizes it, classifies its
   delivery role, writes the canonical artifact, and registers lifecycle state.
2. `workspace-status` resolves indexed artifacts and reports ready, blocked,
   active, and reconciliation states.
3. A dispatchable spec has an existing `spec.md` and `plan.md`; execution
   receives those files rather than tracker payloads or index comments.

## 6. Failure and recovery behavior

A missing artifact, malformed lifecycle entry, or inconsistent reference is a
reconciliation finding. `workspace-status` reports it instead of guessing.

Unavailable tracker refresh leaves repository state unchanged. A capture without
a dispatchable artifact remains visible but cannot enter execution.

## 7. Observability and evidence

`workspace.toml`, canonical artifacts, and `workspace-status` provide the
observable routing and lifecycle record. Provenance records the source locator
and revision without copying credentials or a tracker payload.

## 8. Mechanical invariants

These skill scripts run in the finish-time checklist and can run as fail-closed
CI gates where a PR event and Python exist. They do not fail closed inside an
arbitrary adopter repository.

- `lint-spec-status.py` checks `docs/specs/*/spec.md` metadata against the
  status contract in `CONVENTIONS.md` §4.
- `lint-traceability.py` flags structural orphans across the product chain.
- `lint-brief-coverage.py` rolls each brief's Spec map from `Brief:` back-links
  and requires a non-empty map of shipped specs for delivery.

## 9. Relevant ADRs

- [ADR-0009 — Product brief layer and plan-owned LLD](../adr/0009-product-brief-layer-and-plan-owned-lld.md)
- [ADR-0019 — Product intent ontology and brief projection](../adr/0019-product-intent-ontology-and-brief-projection.md)
- [ADR-0033 — Intent-level open recognized set decoupled from scale](../adr/0033-intent-level-open-recognized-set-decoupled-from-scale.md)
- [ADR-0077 — Feature projection and tracker authority](../adr/0077-feature-projection-and-tracker-authority.md)
- [ADR-0078 — Standalone intake and deterministic workspace index](../adr/0078-standalone-intake-and-deterministic-workspace-index.md)

## 10. Last verified against commit

`c8cf4b37`
