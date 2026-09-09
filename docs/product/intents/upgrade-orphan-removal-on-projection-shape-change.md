# Upgrade orphan removal on projection-shape change

- **Status:** Accepted


## Outcome

AgentBundle upgrade removes previously owned files that are absent from the newly computed projection, so adapter projection-shape changes do not leave stale artifacts.

## Boundary

- Limit deletion to files recorded as owned by the prior install state and absent from the new whole-pack projection.
- Preserve foreign and shared files, enforce the existing install-root confinement boundary, and keep uninstall plus reinstall as the workaround until this ships.
- Do not change recorded adapter identity or Kiro alias semantics.

## Owner

- AgentBundle maintainers.

## Unresolved questions

- Does RFC-0022 provide sufficient Engine-Change-RFC authority for generalized upgrade orphan removal, or must an approver accept a narrow follow-on RFC?
- What ordered deletion, projection, and rollback contract prevents either stale files or partial-upgrade data loss?

## Projection

- Shape a dedicated full-mode delivery spec after the RFC-authority question is resolved; require deletion-confinement tests and security review.

## Opportunity

A legacy Kiro JSON install upgraded through the alias path writes the new Markdown projection but leaves the previously owned JSON artifact behind.

## Assumptions

- The expected-failure Kiro upgrade case remains the regression anchor until the replacement spec deliberately converts it to a passing test.


## Source

- Mode: repo-origin
- Locator: docs/specs/kiro-install-alias-parity/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin
