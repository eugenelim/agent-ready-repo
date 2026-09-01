# Shaping-review efficacy evidence extract

- **Recorded:** 2026-08-31
- **Owner:** Core shaping-reviewer maintainers
- **Authority:** Non-authoritative evidence extract; not a reviewer report or
  adjudication artifact

This maintained extract records the stable results of three fresh isolated
reviews without persisting model-authored review instructions. The exact raw
and adjudication pairs remain in the work-loop's ignored review storage through
the human handoff and are not committed. Each row is independently checkable
against the unchanged seeded fixture digest. Detection is based on defect
identity and disposition, not a total number of observations.

| Mode | Fixture | Reviewed SHA-256 | Expected defect key | Adjudicated identification | Review date | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| `intent` | `docs/specs/rfc0099-migration-validation-record/fixtures/intent-fast-status.md` | `f7d35ac168bf0cdd5932f82f3ad2afc32e56da840bb134491fe3f06d9edd97df` | `SHAPE-UNNECESSARY-INTENT` | `sustained`: unnecessary intent and wrapper skill duplicate `workspace-status` | 2026-08-31 | Core shaping-reviewer maintainers |
| `intent` | `docs/specs/rfc0099-migration-validation-record/fixtures/intent-fast-status.md` | `f7d35ac168bf0cdd5932f82f3ad2afc32e56da840bb134491fe3f06d9edd97df` | `SHAPE-UNSAFE-SIMPLIFICATION` | `sustained`: confinement and reconciliation controls are deferred | 2026-08-31 | Core shaping-reviewer maintainers |
| `delivery-brief` | `docs/specs/rfc0099-migration-validation-record/fixtures/delivery-brief-flag-rename.md` | `c196a0208c4da2d3ae63bf66ab5fe5bde5d5bd6d39f57c9816b3f94344846bd1` | `SHAPE-WRAPPER-BRIEF` | `sustained`: a one-team, one-slice change is wrapped in a delivery brief | 2026-08-31 | Core shaping-reviewer maintainers |
| `delivery-brief` | `docs/specs/rfc0099-migration-validation-record/fixtures/delivery-brief-flag-rename.md` | `c196a0208c4da2d3ae63bf66ab5fe5bde5d5bd6d39f57c9816b3f94344846bd1` | `SHAPE-SPECULATIVE-SLICES` | `sustained`: unsupported future capabilities are admitted as delivery slices | 2026-08-31 | Core shaping-reviewer maintainers |
| `spec` | `docs/specs/rfc0099-migration-validation-record/fixtures/spec-improve-intake.md` | `23c44e9d6298c44611e22b0446f76e5eeae2ae3424210ab439cb233ca8c9af85` | `SHAPE-VAGUE-SPEC-OBJECTIVE` | `sustained`: objective and acceptance criteria are subjective | 2026-08-31 | Core shaping-reviewer maintainers |
| `spec` | `docs/specs/rfc0099-migration-validation-record/fixtures/spec-improve-intake.md` | `23c44e9d6298c44611e22b0446f76e5eeae2ae3424210ab439cb233ca8c9af85` | `SHAPE-MISSING-BOUNDARIES` | `sustained`: scope and mutable-surface boundaries are delegated | 2026-08-31 | Core shaping-reviewer maintainers |
