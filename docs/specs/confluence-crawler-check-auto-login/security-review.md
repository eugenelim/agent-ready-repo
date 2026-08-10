# Security review: Confluence crawler check auto-login

## Scope

Authentication/session recovery, cookie-jar handling, outbound-request
confinement, exceptional conditions, and the Confluence skill's agent-facing
instructions.

## Pre-implementation secure-design review

**Status:** Clean — ready to commit (2026-08-10)

The review applied the authentication/session, secrets, outbound-SSRF,
exceptional-conditions, and agentic-skills modules plus STRIDE and LINDDUN. One
concern required field-level validation of materialized cookie records before
domain filtering or cookie attachment. AC3 and T1 now require list/mapping
shape, string `name`/`domain`/`value`, absent/null/string `path`, fixed
profile-only diagnostics, and ordering tests that poison downstream sinks.

Tool-owned SAST, SCA, secret scanning, executable tests, and manual QA were not
run during this source-only design review.

## Post-implementation diff review

**Status:** Clean — ready to commit (2026-08-10)

The implementation review covered the final client discriminator, cookie-jar
validation order, exact check-only routing, profile-only refresh call,
bounded diagnostics, post-refresh probe, branch-neutral crawl base URL, and
the focused stubbed test boundary. No security finding remained after the
final fix pass.

After this review, the user ran the executable tests, self-host projection,
repository policy chain, Bandit, Semgrep, and dependency audits in a writable
environment. All passed; the pre-existing spec-reference warnings remained
warn-only.
