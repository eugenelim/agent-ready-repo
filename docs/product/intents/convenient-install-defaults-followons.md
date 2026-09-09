# Convenient install default-source integrity

- **Status:** Accepted


## Outcome

The layer-4 git+https default catalogue route resolves mutable main to an immutable commit SHA and verifies that the fetched archive bytes correspond to the recorded source identity before installing executable agent content.

## Boundary

- Preserve RFC-0046 and ADR-0036 source precedence, editable-install discovery, and the no-repository-source and no-current-directory rules.
- Limit this outcome to the existing default catalogue route; direct skill sources retain their RFC-0098 and ADR-0100 contract.
- Reuse established bounded, credential-free GitHub acquisition controls instead of introducing a second transport or verification stack.

## Owner

- AgentBundle maintainers.

## Unresolved questions

- Do RFC-0046 and the frozen specification finish line provide sufficient Engine-Change-RFC authority, or must an approver accept a narrow integrity-pinning follow-on RFC?
- Which existing source-identity primitive should bind the commit SHA to the acquired catalogue archive without a force-push race?

## Projection

- Resolve the RFC-authority question, then shape a security-reviewed full-mode delivery spec with mutable-ref, archive-mismatch, redirect, and rollback tests.

## Opportunity

The packaged layer-4 default currently acquires executable catalogue content from a mutable unauthenticated repository tip without a post-acquisition identity check.

## Assumptions

- The exact finish line in the frozen specification remains authoritative: resolve main to a full commit SHA and verify the fetched archive digest.


## Source

- Mode: repo-origin
- Locator: docs/specs/convenient-install-defaults/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin
