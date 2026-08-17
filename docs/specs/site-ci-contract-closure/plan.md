# Plan: Site CI contract closure

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

## Approach

First pin required-workflow inclusion with a construction test. Then add focused
contrast-checker tests and wire one explicit required CI step that runs the
seven modules plus the contrast check. Keep the local command identical to the
CI selection so future changes cannot create a second test contract.

## Constraints

- Follow RFC-0082 test ownership.
- Use existing Python and standard-library tooling.
- Keep the build-check workflow required and fail closed.

## Construction tests

**Integration tests:** run the workflow-shape test, all seven registered
modules, and the contrast checker tests as one focused local gate.

**Manual verification:** inspect the required-job and path-filter diff to ensure
the step is neither advisory nor conditionally skipped for relevant paths.

## Design (LLD)

### Design decisions

One explicit workflow step owns the exact module list. A construction test
parses that step and its path filters; it does not infer coverage from comments
or Make targets. Traces to: AC1, AC2, AC5, AC6.

### Failure, edge cases & resilience

The contract rejects missing modules, renamed modules, invalid color strings,
ratios below the threshold, and commands hidden behind non-required conditions.
Traces to: AC2-AC5.

### Dependencies & integration

The workflow reuses the repository's installed pytest and Python environment.
The contrast checker remains a direct Python command. Traces to: AC3-AC7.

## Tasks

### T1: Required-workflow construction test proves exact inclusion

**Depends on:** none

**Touches:** tools/test_build_gate_chain.py, .github/workflows/build-check.yml

**Tests:**
- TDD: seed each of the seven module names absent in turn and require failure
  (AC1-AC2).
- TDD: seed an advisory or wrong-job invocation and require failure (AC2).
- TDD: remove a relevant path trigger and require failure (AC5).

**Approach:**
- Extend the existing workflow construction-test surface rather than creating a
  second workflow parser.
- Assert semantic command membership and required-job placement.

**Done when:** the test is red on the current workflow and distinguishes every
  named omission.

### T2: Contrast checker has a deterministic unit contract

**Depends on:** none

**Touches:** tools/check-docs-contrast.py, tools/test_check_docs_contrast.py

**Tests:**
- TDD: known passing, exact-boundary, and failing ratios (AC3).
- TDD: invalid hexadecimal input refuses clearly (AC3).
- TDD: a failing registered pair returns non-zero (AC3-AC4).

**Approach:**
- Exercise public calculation and CLI seams without snapshots or source-shape
  assertions.
- Keep fixtures local and dependency-free.

**Done when:** the checker behavior is proved independently of CI wiring.

### T3: Required CI runs the seven modules and contrast gate

**Depends on:** T1, T2

**Touches:** .github/workflows/build-check.yml

**Tests:**
- Goal-based: run the T1 workflow construction test (AC1-AC2, AC5-AC6).
- Goal-based: execute the exact CI command locally (AC1, AC4, AC6).
- Goal-based: verify dependency manifests are unchanged (AC7).

**Approach:**
- Add one plainly named required step using the exact registered module list.
- Add the checker and affected paths to the workflow filters.

**Done when:** the focused local command is green and the workflow construction
contract recognizes the required gate.

## Rollout

The required job changes immediately for relevant pull requests. Reverting the
workflow step and its construction test restores the previous behavior; no data
or deployment migration exists.

## Risks

- A broad Make target may look equivalent while required CI still omits tests.
- Path filters can prevent an otherwise-correct step from running.
- A checker test that asserts implementation constants instead of emitted exit
  behavior would provide false confidence.

## Changelog

- 2026-08-17: initial plan derived from the approved tech-site completion brief.
