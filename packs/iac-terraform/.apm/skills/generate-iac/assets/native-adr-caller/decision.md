# Keep the example workspace local

* Status: accepted
* Date: 2026-01-01

## Context and Problem Statement

Demonstrate a saved-plan exchange for example-account without cloud access.

## Decision Drivers

* Keep the backend local and the workspace named example-workspace.
* Require validation, policy, security and review evidence for the saved plan.

## Considered Options

* Local example workspace
* Remote cloud workspace

## Decision Outcome

Chosen option: local example workspace, because this exercise needs no cloud resources.

### Consequences

All plan and check artifacts are synthetic. No deployment is authorized.
