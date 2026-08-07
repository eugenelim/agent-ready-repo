# exceptional-conditions — error paths, retries, fail-open

> **Loaded when:** the change adds error handling, retry/timeout logic,
> fallbacks, circuit breakers, or alters what happens when a dependency fails.
> **Standards:** **OWASP Top 10:2025 A10 (Mishandling of Exceptional
> Conditions — new in 2025)** (+ A09 Security Logging & Monitoring Failures) ·
> ASVS 5.0 V16 (Security Logging & Error Handling) · Proactive Controls 2024
> C10 (Handle all Errors and Exceptions).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the
> flow, you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, the control is **decide fail-open vs fail-closed explicitly**
— for each control the feature relies on (authz check, token verification,
rate limiter), the spec should state what happens when its dependency is
unavailable. A security control that defaults to "allow" on error is the
classic exceptional-condition bug (Proactive Controls 2024 C10; ASVS 5.0 V16).

## Implementation checks

- `reason` **Fail-open vs fail-closed.** When an authz/verification/rate-limit
  dependency errors or times out, does the code *deny* or *allow*? A security
  decision that falls through to allow on exception is a Blocker.
- `reason` **Error-path information leak (A09).** Exceptions returned to the
  caller must not carry stack traces, SQL, internal paths, or secrets;
  trace what the catch block actually emits.
- `reason` **Unbounded retry / amplification (DoS).** Retries without a cap or
  backoff, recursion without a depth bound, or an unbounded allocation driven
  by input is a denial-of-service vector.
- `reason` **Swallowed exceptions.** A bare `except: pass` over a security
  operation hides a failure that should deny or alert — flag the silent
  swallow, not just the missing log.
- `reason` **Critical-event logging gap (A09).** Auth failures, access-control
  denials, and integrity violations should be logged with enough context
  (correlation id, actor) to investigate — without logging the sensitive
  payload itself.
- `tool` **Empty-catch / swallowed-error lint.** Some linters flag empty catch
  blocks; confirm the rule is on, but the *security* judgment (deny vs allow)
  stays reviewer-owned.

## Established-helper bypass

Resolve the repo's sanctioned error-handling / result wrapper and structured
logger, and flag a change that invents its own fail-through behavior or logs
ad hoc (and possibly leaks) instead of using the blessed path — the shared
error wrapper is where fail-closed and redaction were already settled.
