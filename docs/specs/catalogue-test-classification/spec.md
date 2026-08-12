# Spec: catalogue test classification

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0002; RFC-0082; ADR-0075
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Repository maintainers run `agentbundle catalogue verify --root .` against the
catalogue source tree without receiving `unclassified` notices for its
repository-owned top-level test suite. Unknown paths outside established
ownership boundaries remain visible and informational.

## Boundaries

### Always do

- Classify the top-level `tests/**` tree at its stable ownership boundary.
- Preserve dynamic Projected membership and informational unknown-path behavior.
- Keep AgentBundle release metadata synchronized with the engine change.

### Ask first

- Reclassifying any existing Projected, Manual, Source, or Excluded path.
- Changing an unclassified notice into a verification failure.
- Broadening the fix beyond the top-level test tree and its release metadata.

### Never do

- Blanket-exclude `.agentbundle/**` or another generated projection boundary.
- Maintain a per-file or per-test-category allowlist for this ownership class.
- Change marketplace scope filtering, pack declarations, or projection rules.

## Testing Strategy

- **TDD, behavior:** drive the unclassified-info emitter with representative
  conformance, fixture, and roster paths plus an unknown control. The test pins
  the observable stderr contract without requiring a temporary worktree.
- **Goal-based, package:** run the focused classifier tests and the AgentBundle
  version-parity test.
- **Goal-based, end to end:** run the real catalogue verifier and require exit
  zero with no `unclassified` notice for the repository inventory.

## Acceptance Criteria

- [x] **AC1.** Every Git-visible path under top-level `tests/**` is classified
  Excluded from self-host projection.
- [x] **AC2.** Representative paths from `tests/conformance/`,
  `tests/fixtures/`, and `tests/roster/` emit no `unclassified` notice.
- [x] **AC3.** A Git-visible path outside all Projected and Excluded boundaries
  still emits one informational notice without changing a clean exit code.
- [x] **AC4.** The ownership rule is one anchored `tests/**` boundary; similarly
  named root files such as `tests.md` remain outside it.
- [x] **AC5.** AgentBundle reports the next patch version from both package
  metadata sources and its changelog records the classifier correction.
- [x] **AC6.** Focused classifier tests, AgentBundle package tests, repository
  policy gates, and the real catalogue verifier pass in a writable environment.

## Assumptions

- Technical: `tests/conformance/` and `tests/roster/` are repository-owned and
  never shipped as engine content (source: `packages/AGENTS.md`).
- Technical: `tests/fixtures/install_snapshot/**` belongs to the roster-shaped
  `tests/roster/test_install_snapshot.py` contract under ADR-0075's
  assertion-based ownership rule (source: `tests/roster/test_install_snapshot.py`
  module contract and ADR-0075 Decision).
- Technical: self-host classification is Projected membership plus
  `EXCLUDED_PATTERNS` (source: `docs/specs/catalogue-verify-classification/spec.md`).
- Product: all present and future paths under top-level `tests/**` are Excluded
  while unknown paths elsewhere remain visible (source: user confirmation
  2026-08-11).
- Process: local `main` is the approved comparison baseline and remote freshness
  is skipped because Git metadata cannot be updated (source: user confirmation
  2026-08-11).
- Process: AgentBundle engine changes require synchronized versions and an
  `Engine-Change-RFC:` commit footer (source: `packages/AGENTS.md` and
  `packages/AGENTS.local.md`).
- Technical: this integration-shaped correction exposes no new contract file
  (source: user confirmation 2026-08-11).
