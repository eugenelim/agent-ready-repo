# Plan: catalogue test classification

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> note why in the changelog at the bottom.

## Approach

Add a behavior-level regression that sends each top-level test category through
the existing unclassified-info emitter, confirm it fails on the current
classifier, then add one stable `tests/**` exclusion. Synchronize the
AgentBundle patch version and changelog, run the narrow no-temp tests locally,
and reserve the writable-temp package and end-to-end gates for the final manual
verification block.

## Constraints

- RFC-0002 owns self-host classification and keeps unknown-path notices
  informational.
- RFC-0082 and ADR-0075 place catalogue conformance and roster tests outside the
  engine package boundary.
- Package changes require matching versions in `pyproject.toml` and
  `agentbundle/version.py`; the commit requires
  `Engine-Change-RFC: RFC-0002`.
- The patch number is the next version after the versions published on PyPI,
  checked immediately before metadata is edited. If that read-only network
  check is unavailable, version selection is surfaced rather than guessed.
- This run ends with the version-bump PR ready for publication. Tagging,
  publishing, setting the spec to Shipped, and workspace closeout happen only
  in a separate follow-on after the release is confirmed.
- The active shell cannot create temporary or generated-output directories.

## Construction tests

**Integration tests:** the real `agentbundle catalogue verify --root .` exits
zero without any `unclassified` notice for the tracked inventory.

**Manual verification:** the final writable-environment command block runs the
package suite, repository policy gate, and real verifier once.

## Design (LLD)

### Design decisions

- Extend `EXCLUDED_PATTERNS` with `tests/**`; do not add new classifier logic or
  enumerate the current filenames. Traces to AC1, AC2, and AC4.
- Patch the emitter's input seam in the regression test so red/green is
  deterministic and does not depend on temporary Git state. Traces to AC2 and
  AC3.

### Failure, edge cases & resilience

The anchored glob must not catch `tests.md`, and a control path outside known
boundaries must still surface. The marketplace message is outside this
classifier and remains untouched by boundary, not by a new test obligation.
Traces to AC3 and AC4.

## Tasks

### T1: Top-level catalogue tests are classified at their ownership boundary

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/build/self_host.py`, `packages/agentbundle/tests/build_pipeline/test_self_host_check.py`

**Tests:**
- TDD red: `InfoLineUnclassifiedTests` supplies representative conformance,
  fixture, and roster paths plus `misc/future-owner.txt`; only the control is
  emitted (AC1–AC3). `stub: true` — materialized as
  `test_top_level_catalogue_tests_are_not_reported_unclassified`.
- TDD boundary: `ExcludedGlobTests` proves `tests/**` matches nested test assets
  but not `tests.md` (AC4). `stub: true` — materialized as
  `test_top_level_test_boundary_is_anchored`.
- Existing integration regression
  `InfoLineUnclassifiedTests.test_unclassified_path_surfaces_as_info_without_failing`
  drives `run_self_host` and pins AC3's informational exit code.
- Stub-marker disposition: package tests ship in the sdist, so PLAN carries the
  durable `stub: true` audit record. The temporary internal AC markers were
  removed immediately after the syntax-valid stubs failed red, per
  `packages/AGENTS.local.md`.

**Approach:**
- Materialize and run the behavior regression before production code.
- Add the single anchored exclusion and rerun both focused tests.

**Done when:** both focused tests pass and the unknown control still emits.

### T2: AgentBundle pre-publication metadata identifies the correction

**Depends on:** T1

**Touches:** `packages/agentbundle/pyproject.toml`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/CHANGELOG.md`, `docs/specs/README.md`

**Tests:**
- Goal-based: `test_version.py` confirms package and runtime versions agree
  (AC5).
- Goal-based: `python -m pip index versions agentbundle` identifies the next
  unpublished patch before either version source changes (AC5).
- Goal-based: the spec index resolves and names the active regression contract.
- Goal-based: the package governance-marker pattern from
  `packages/AGENTS.local.md`, scoped only to added diff lines in the changed
  package test, returns no matches after stub cleanup; the repository-wide
  legacy corpus is unchanged.

**Approach:**
- Bump AgentBundle to the next available patch version in both sources.
- Add a concise Fixed entry and the active-spec index row.

**Done when:** version parity passes and release notes name the classifier fix;
publication and lifecycle closeout remain in the required follow-on.

### T3: Available gates and the real verifier establish release readiness

**Depends on:** T1, T2

**Tests:**
- Goal-based: run Ruff, version parity, and focused classifier tests locally
  without temporary-file use (AC6).
- Goal-based: rerun the package governance-marker pattern against only added
  diff lines in the changed package test before review.
- Goal-based/manual: run the package suite, `SKIP_SAST=1 make build-check`, and
  `agentbundle catalogue verify --root .` in the writable environment (AC6).

**Approach:**
- Run local read-only-compatible gates first.
- Provide one copy-paste-safe multiline shell block for the remaining writable
  gates and record their outcome when returned.

**Done when:** every available gate is green and the manual verification set is
minimal and complete.

## Rollout

The current run prepares the next AgentBundle patch release. After this PR
merges, maintainers tag and publish that version through the standard release
process; only a subsequent closeout change marks this spec Shipped and updates
`workspace.toml`. Rollback before publication is the code and metadata revert;
no data, configuration, dependency, or infrastructure migration exists.

## Risks

- A broad glob could hide unrelated future content; the anchored `tests/**`
  shape and `tests.md` negative control constrain it.
- A predicate-only test could stay green if the emitter stopped consulting the
  predicate; the behavior regression drives the emitter directly.
- Local filesystem restrictions prevent the complete gate set here; the final
  manual block keeps that residual explicit.

## Resolve-vs-surface disposition

- Resolve: classifier regression, focused no-temp tests, release metadata,
  spec/status lint, and code review.
- Preserve: marketplace user-scope exclusion output and every projection rule.
- Surface: only gates that intrinsically require writable temporary or generated
  directories, as one final user-run verification block.
- Approved skip: remote base-freshness; local `main` is the comparison baseline.

## Changelog

- 2026-08-11: initial full-mode plan for the top-level test ownership regression.
