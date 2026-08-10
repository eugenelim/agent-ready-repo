# Spec: Catalogue small cleanups

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none
- **Shape:** mixed

> **Mode:** light (no risk trigger fired)

## Objective

The catalogue parity register accurately describes the non-blocking
plugin-offer assertion in `pages.yml`. Its resolved backlog record and the
stale fixture-indentation and engine-build Ruff records leave the open queue;
the Ruff-canonical fixture source and landed Ruff configuration remain
unchanged.

## Boundaries

### Always do

- Remove a backlog record only after its corresponding change is present and
  verified.

### Ask first

- Bring an additional workflow into the CI-parity linter's in-scope roster.
- Expand this cleanup into package or scaffold release work.

### Never do

- Change agentbundle engine behavior, public schemas, or published scaffold
  content.
- Include any catalogue wave, test-carve-out, security-hardening, Atlassian,
  SSO, JSON-schema, primitive-retirement, or separately owned verifier work.

## Testing Strategy

- Parity disposition: a goal-based assertion reads the actual `WORKFLOW_SCOPE`
  value and checks that it names the built-output assertion, its non-blocking
  posture, and the blocking self-test.
- Queue state: goal-based full workspace reconciliation after the resolved and
  stale comment-and-entry blocks are removed, plus a parsed slug-set comparison
  against local `main` proving no other open backlog entry changed.

## Acceptance Criteria

- [x] **AC1:** `WORKFLOW_SCOPE["pages.yml"]` accurately states that the
      built-output plugin-offer assertion is intentionally non-blocking and that
      its self-test remains in the blocking local gate chain.
- [x] **AC2:** `workspace.toml [backlog].open` no longer contains
      `plugin-pages-yml-parity-disposition` or
      `plugin-fixture-continuation-indent` or
      `ruff-excludes-the-engine-build-package`; all other backlog entries,
      including `catalogue-gate-b-no-local-target` and
      `profiles-agents-normative-pointer`, remain unchanged.
- [x] **AC3:** `docs/specs/README.md` lists this light spec and its final status.
- [x] **AC4:** Focused checks, Ruff, catalogue verification, workspace
      reconciliation, and repository policy/build checks pass.

## Assumptions

- Technical: the current `pages.yml` scope reason omits its non-blocking
  assertion (source: repository read 2026-08-10).
- Process: tests under `tools/` are repository-only and new tool scripts are
  pure-stdlib Python (source: `AGENTS.md` and `packages/AGENTS.md`).
- Technical: local `main` already anchors Ruff's output exclusion at `/build`
  and explicitly keeps the shipped engine build package in scope (source:
  `pyproject.toml` at `9808fab8dd` and user confirmation 2026-08-10).
- Product: only the parity disposition remains compatible with this branch;
  `catalogue-gate-b-no-local-target` remains open because a safe workflow
  replayer requires its own parser safety contract, and
  `plugin-fixture-continuation-indent` is removed as stale metadata because Ruff
  0.15.17 canonicalizes the current equal indentation and rewrites the proposed
  deeper continuation indentation, while
  `profiles-agents-normative-pointer` remains open because scaffold edits are
  release-coupled (source: user confirmation 2026-08-10,
  `AGENTS.local.md`, pre-execution adversarial review 2026-08-10, and
  `ruff format -` probe 2026-08-10).
