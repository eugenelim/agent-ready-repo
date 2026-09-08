# SSO browser state is bounded and minimally retained

- **Status:** Draft
- **Level:** capability

## Outcome

Persistent SSO browser state is time-bounded, minimally stored, protected from concurrent browser launches, and not repeatedly recaptured, while macOS keychain operations remain within an explicitly derived lock budget.

## Boundary

- Credential-broker browser-state capture, storage, expiry, refresh cooldown, per-profile browser-launch serialization, and macOS keychain call budgeting.
- Pack dependency schemas, catalogue defaults, lint wording, optional client hooks, live credential transcripts, and consumer retry behavior remain outside this intent.

## Owner

- Credential-broker maintainers; no individual owner is recorded.

## Unresolved questions

- Choose the maximum browser-session lifetime and automatic-recapture cooldown from measured operator and IdP behavior.
- Choose batching, per-call timeout, or both for macOS keychain operations, including behavior while an operator is responding to a keychain prompt.
- Fix the browser-launch lock wait and stale-recovery policy separately from the short store-transition lock.

## Projection

- One delivery brief with two separately gated specifications: browser-state security and recapture controls; and macOS keychain latency and lock-budget controls.

## Opportunity

This intent absorbs browser-state-lifetime, sso-broker-at-rest-minimisation, sso-broker-register-concurrency, sso-keychain-call-timeouts, and sso-recapture-cooldown. Current profiles can retain replayable sessions indefinitely, store unfiltered cookies under umask-default directories, collide on Chromium singleton locks, exceed store-lock budgets during keychain calls, and launch automatic refresh repeatedly across processes.

## Assumptions

- Browser-launch serialization remains separate from the short store-transition lock so a long Chromium launch cannot starve get-cookies.
- Capture-time destination filtering supplements rather than replaces consumer-side cookie-send confinement.
- Protected credential-broker changes require an accepted Engine-Change-RFC authority at landing time.


## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin
