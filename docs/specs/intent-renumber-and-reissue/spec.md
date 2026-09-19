# Spec: Intent renumber, reissue, and the tombstone

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** docs/product/briefs/intent-identity-and-registration.md
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Constrained by:** ADR-0108

## Objective

Make an ordinal safe to change. A renumber is not free: `workspace.toml` holds the registry `path` entries and a stale one raises `missing_artifact`, which `tests/roster/test_workspace_status_projection.py` treats as fail-closed. The owner accepted the renumber cost, so the constraint is on completeness of the sweep rather than its frequency.

A post-admission altitude change reissues at the new prefix and leaves a tombstone, which keeps `max + 1` correct without a shared retired list, per ADR-0108 D3's non-reuse rule.

## Testing Strategy

- Renumber one real intent end to end; assert zero stale path-shaped citations and unchanged pointer values.
- Assert a tombstone is counted by the allocator and does not trip the corpus lint.
- Assert behaviour for a tombstone whose target is missing, and for two tombstones pointing at each other.

## Acceptance Criteria

- [ ] A renumber leaves zero stale path-shaped citations — registry `path` entries and Markdown link targets — and changes no canonical pointer value, because identity binds to each artifact's `Slug:` field.
- [ ] A renumber edits `workspace.toml` in lockstep with the rename, and the sweep is complete rather than best-effort.
- [ ] A retirement or altitude change leaves a tombstone the allocator counts, so an ordinal is never reused.
- [ ] **Decision owed by this spec:** how a tombstone coexists with the shape contract — how it is identified, how it is excluded from intent-shape validation, whether resolution follows it to the reissued artifact, and what happens when its target is missing or two tombstones point at each other.
