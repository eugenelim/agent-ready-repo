# Plan: cognitive-load-reduction

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:**
  `packs/core/seeds/AGENTS.md` (root-pointer pattern),
  `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py`
  (confined reads),
  `packages/agentbundle/agentbundle/catalogue_tooling/lint.py` (seed routing),
  `tools/add-rendering-directives.py` (managed blocks), and
  `guides/_shared/reference/output-rendering.md` (authoring contract).

## Approach

Use one behavior in five places: the root pointer, `AGENT_RULES.md`, the
always-on cognitive-load topic, `docs/AGENTS.md`, and a managed block inside
every skill. The lookup files govern seeded repositories; the skill block
keeps user-profile and out-of-repo use independent.

Keep the router tool-neutral. Verify Claude through `CLAUDE.md → AGENTS.md`,
Codex through root `AGENTS.md`, and Gemini through the existing managed context
filename bridge. Do not add an adapter rule format.

Generate repeated skill content from one constant. Keep shape-specific skill
directives outside the managed markers. Score only eligible prose, and pair
numeric thresholds with semantic and quiet-work fixtures.

## Constraints

- `.apm/` skill sources and core seed sources remain canonical; projections
  are generated.
- Skills remain standalone at user and repository scope.
- File reads that cross a trust boundary use the repository's confined-read
  helper or an equivalent pure-stdlib descriptor-bound operation.
- Readability scoring stays deterministic and dependency-free.
- Pack versions, eval metadata, changelogs, and generated manifests stay in
  sync with changed canonical content.
- The future catalogue `rules` primitive remains out of scope.

## Assumption trio

- **Touches:** the existing cognitive-load sources, tools, tests, pack eval
  metadata, generated projections, and this spec pair.
- **Done:** focused behavior tests, readability and quiet-work checks, lint,
  typecheck, managed-output checks, a fresh catalogue build, and all warranted
  reviewers are clean.
- **Not changing:** adapter contracts, install scope, dependencies, native rule
  formats, or `docs/CONVENTIONS.md`.

**Declined:** a second safe-read implementation, live-model eval machinery,
and adapter-specific rule files. Existing helpers and deterministic contracts
cover the accepted outcome.

## Tasks

### T1: Bound every new prose and lookup read

**Depends on:** none

**Verification mode:** TDD.

**Touches:** `tools/check-output-readability.py`,
`packages/agentbundle/agentbundle/catalogue_tooling/lint.py`, confined-read
tests, and readability tests.

**Tests:**

- Readability inputs reject symlinks, hard links, reparse-like files,
  non-regular files, dot-segment escapes, identity swaps, and files above the
  byte limit before reading their body. Verifies AC11 and AC14.
- Router and topic lint reads use the blessed helper with an explicit bound and
  retain the existing short diagnostics. Race and unsafe-target regressions
  exercise the live linter path. Verifies AC9, AC10, and AC14.

**Approach:** reuse `read_confined_regular_file`; do not precheck with one path
and read with another. Keep the standalone tool importable from a source
checkout without adding a dependency.

**Done when:** focused tests prove bounded reads and no raw lookup `read_text`
path remains.

### T2: Keep pack eval metadata coherent

**Depends on:** none

**Verification mode:** goal-based check.

**Touches:** changed pack manifests and eval metadata, including
`packs/user-guide-diataxis/pack.toml`.

**Tests:** pack lint and an inventory check find no changed pack whose declared
eval disposition conflicts with shipped eval files. Verifies AC13 and AC16.

**Approach:** update stale declarations only; do not create another eval route
when the existing harness already covers the pack.

**Done when:** pack metadata matches the committed eval surface.

### T3: Re-verify the end-to-end cognitive-load contract

**Depends on:** T1, T2

**Verification mode:** goal-based checks plus manual artifact review.

**Touches:** canonical skills, guide, seeds, pack evals, versions, changelog,
and generated projections only when regeneration reports drift.

**Tests:**

- The injector is current and idempotent across every canonical skill.
- Seed, router, host-path, authority, and safe-read contracts pass.
- Every publishable pack found by the inventory check has a fixture that meets
  AC11's readability thresholds. Gate output reports the pack count. Routine
  transcripts contain no optional chatter and retain AC7's allowed updates.
- The guide and actual instruction corpus remain readable without losing the
  semantic controls.
- OKF outputs, scaffold data, projections, versions, eval metadata,
  marketplace, changelog, `/now/` highlight data, and a fresh catalogue build
  are coherent.

**Approach:** run narrow tests first, then lint, typecheck, build, and drift
checks. Treat enterprise `os.rmdir` cleanup denials as supported-profile work
only after the affected assertions have been confirmed once.

**Done when:** available gates pass; the public guide names the working
principle; release highlights reach `/now/`; and the rendered rule, docs
lookup, and representative skills remain clear and complete.

### T4: Close review and release evidence

**Depends on:** T3

**Verification mode:** reviewer and finish-gate evidence.

**Touches:** review artifacts plus spec and plan status.

**Tests:** adversarial, security, and quality reports are independently
adjudicated clean; the experience-reviewer is a named skip if unavailable;
spec-status and diff checks pass.

**Approach:** fix only sustained findings, return through gates after each
review unit, then mark the spec `Shipped` and plan `Done`.

**Done when:** the work-loop reaches the human merge gate with no unresolved
accepted finding.

## Rollout and recovery

- Deliver one coordinated pack release wave; no flag or runtime migration.
- Re-run the injector and generators from canonical sources to recover drift.
- Published versions remain immutable; source guidance and tools can be
  reverted in a later release.

## Risks

- **Router growth:** the row ceiling and leaf-only rule keep bodies out of the
  router.
- **Substance loss:** semantic fixtures and exact-content guards sit beside
  readability scores.
- **Batch damage:** markers, preflight, idempotence, and generated-output checks
  protect custom skill content.
- **Host variance:** evidence labels distinguish static, semantic, and observed
  behavior.
