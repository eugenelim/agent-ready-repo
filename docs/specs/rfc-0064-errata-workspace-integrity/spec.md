# Spec: rfc-0064-errata-workspace-integrity

Mode: light (no risk trigger fired)

- **Status:** Shipped
- **Owner:** eugenelim

## Objective

Add an amendment entry to RFC-0064 documenting the workspace-status integrity
trust boundary: the session-fragmentation condition under which `workspace-status`
can give an incomplete picture, the two skill fixes that close the gap, and the
manual workaround. Restructure the `## Amendments` section to the two-layer
format (`### Current state` / `### History / audit trail`) now that two
independent amendments exist — required by RFC-0055 once a second entry lands.

## Acceptance Criteria

- [x] A second amendment entry appears in `docs/rfc/0064-ini-001-ai-native-ecosystem.md` stating:
  1. The session-fragmentation condition (RFC accepted in session A; spec generation in session B silently drops the queue-write prompt)
  2. The two skill fixes: `new-rfc-followon-queue-write` (shipped) and `workspace-status-queue-reconciliation` (queued, unblocked)
  3. The manual workaround (check `docs/specs/*/spec.md` for Status: Approved|Implementing absent from queue; add via `queue-add` or hand-editing)
- [x] `## Amendments` section is restructured to two-layer format (`### Current state` summary table + `### History / audit trail` with both dated entries)
- [x] `workspace.toml` moves `spec/rfc-0064-errata-workspace-integrity` from `queue` to `shipped`
- [x] `docs/product/roadmap.md` updated with a one-line shipped entry under `## Now`

## Tasks

1. [x] Write lean spec (this file)
2. [x] Restructure `## Amendments` and add second entry to RFC-0064
3. [x] Move spec to shipped in `workspace.toml`; add `roadmap.md` entry
