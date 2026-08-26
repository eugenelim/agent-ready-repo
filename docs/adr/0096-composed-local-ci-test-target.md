# ADR-0096: Composed local CI uses an explicit post-build-check test target

- **Status:** Accepted
- **Date:** 2026-08-25
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** none. Per CONVENTIONS § Cite upward, an ADR does not cite specs;
  the affected frozen and current specs carry the pointer.

## Context

A shipped local-CI contract pins standalone `test` as a direct `ci`
prerequisite. Five files are also build-check self-tests, and their semantic
equivalence can be mechanically established, so that graph executes them twice.

The composed route must keep build-check ownership and self-test-before-lint
ordering, keep standalone test complete, remain safe under parallel Make, and
offer no ambient selector that can reduce a standalone gate.

## Decision

**We will make an explicit `test-after-build-check` target the test prerequisite
of composed local CI while keeping standalone `test` unchanged.**

The composed target depends on successful `build-check`, acquires the existing
test lease once, and runs the existing test recipe with only the mechanically
owned shared files excluded. Local parity dispositions point to this reachable
composed target; build-check remains the owner of the excluded files.

## Decision drivers

- Preserve standalone gate independence and build-check failure attribution.
- Make composed ownership and parallel ordering visible in the Make graph.
- Prevent environment or command-line state from selecting reduced standalone
  coverage.
- Avoid a general runner, persistent state, or duplicated long test recipe.

## Consequences

**Positive:**

- One composed invocation executes the shared semantic contract once.
- A dependency edge, rather than hidden provenance, owns parallel ordering.
- Standalone and make-free gates retain their existing entrypoints.

**Negative:**

- The shipped direct-prerequisite clause and plan receive status-only partial
  supersession pointers.
- Local CI parity dispositions name the composed target even though standalone
  `test` remains the public complete test gate.
- Construction tests must keep two route plans and five exclusions aligned.

**Revisit if:** supported Make gains a simpler explicit ordering primitive that
retains standalone `test` as the direct composed prerequisite, or the shared
set grows beyond a narrow exact-file composition.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** actual-Make construction tests prove exact graph, recursive
  delegation, parallel ordering, standalone completeness, and once-only union.
- **Owner:** repository maintainers

## Alternatives considered

**Target-specific composition profile.** Rejected because GNU Make 3.81 can
protect selector provenance but cannot also express the required parallel
ownership edge without changing standalone test or adding broader coordination.

**Skip the build-check self-tests.** Rejected because it separates each linter
from its proving self-test and changes failure ordering and attribution.

**Move the test recipe into a shared runner.** Rejected because five exact files
do not justify a general orchestration layer or moving unrelated process
boundaries into Python.
