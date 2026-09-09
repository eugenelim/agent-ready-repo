# SSO-cookie lint wording matches the check carve-out

- **Status:** Draft
- **Level:** feature

## Outcome

Catalogue lint wording accurately forbids automatic SSO setup while preserving the shipped non-mutating check carve-out.

## Boundary

- The pinned SSO-cookie guidance phrase and the contract tests that enforce it.
- Credential behavior, automatic-refresh policy, capture commands, and unrelated lint rules remain outside this intent.

## Owner

- AgentBundle catalogue-lint maintainers; no individual owner is recorded.

## Unresolved questions

- None recorded. The shipped check carve-out remains authoritative.

## Projection

- One direct-light implementation after acceptance that amends the phrase and its exact contract tests without changing runtime behavior.

## Opportunity

This intent absorbs sso-cookie-lint-phrase-amendment. The currently pinned phrase says not to run any setup helper, while the shipped check carve-out permits the non-mutating check path, so the literal guidance contradicts the enforced behavior.

## Assumptions

- This is a wording and test-contract correction, not authorization for a new credential operation.
- A protected AgentBundle change requires accepted Engine-Change-RFC authority at landing time.


## Source

- Mode: repo-origin
- Locator: docs/specs/jira-check-sso-auto-login/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin
