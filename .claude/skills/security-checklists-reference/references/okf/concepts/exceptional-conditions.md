---
title: "exceptional-conditions"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# exceptional-conditions

Use when the change adds error handling, retry or timeout logic, fallbacks,
circuit breakers, or dependency-failure behavior.

## Spec-stage

Require fail-open versus fail-closed behavior for every control the feature
relies on, including logging and user-visible outcomes.

## Implementation checks

- `reason` Security controls should fail closed unless explicitly justified.
- `reason` Retry loops need caps, jitter, and bounded side effects.
- `reason` Fallbacks must not bypass authentication, authorization, or checks.
- `reason` Errors should not leak secrets or sensitive internals.
- `reason` Security-relevant failures need audit-quality logging.

## Established-helper bypass

Resolve the sanctioned error, retry, and logging helpers and flag ad-hoc
fallbacks that bypass central security behavior.
