# authn-session — authentication, session, tokens

> **Loaded when:** the change touches login, logout, password handling, MFA,
> session creation/expiry, or token issuance/verification (JWT, opaque, API
> keys).
> **Standards:** OWASP Top 10:2025 A07 (Authentication Failures) · ASVS 5.0 V6
> (Authentication) + V7 (Session Management) · OWASP API Security Top 10:2023
> (API2 Broken Authentication) · Proactive Controls 2024 C6 (Digital Identity).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the
> flow, you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, confirm the spec specifies session **lifecycle** as criteria,
not just "log the user in": rotation-on-privilege-change, idle and absolute
timeouts, and what invalidates a session. Authentication strength
(MFA paths, lockout/throttling) should be an AC where the asset warrants it
(ASVS 5.0 V6.2; Proactive Controls 2024 C6).

## Implementation checks

- `reason` **Session fixation / rotation.** The session identifier must rotate
  on login and on privilege elevation; reusing a pre-auth session id lets an
  attacker fixate it.
- `reason` **JWT verification.** Reject `alg: none`; pin the expected
  algorithm; verify the signature against the *expected* key, not the key the
  token names (`jku`/`kid` confusion). An unverified or `alg`-confused JWT is
  a Blocker.
- `reason` **Token entropy & storage.** Session tokens and reset tokens must be
  CSPRNG-derived and stored hashed; predictable or plaintext-stored tokens are
  forgeable.
- `reason` **Lockout / throttling.** Sensitive auth endpoints (login, OTP,
  reset) need rate-limiting or progressive backoff; their absence is a
  credential-stuffing invitation.
- `reason` **Logout & expiry actually invalidate.** A logout that only clears
  a client cookie while the server token stays valid is a false control.
- `hybrid` **Hardcoded / weak credentials in the diff.** A secret scanner
  flags committed credentials; you judge whether a "test" default is reachable
  in production config.

## Established-helper bypass

Authentication is almost never something to hand-roll. Resolve the repo's
sanctioned auth/session library or middleware and flag a change that
introduces its own password hashing, its own JWT parsing, or its own session
store instead of the blessed path — rolled-its-own auth is where `alg: none`
and unsalted hashes slip in.
