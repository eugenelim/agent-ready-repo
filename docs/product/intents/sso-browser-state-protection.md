# SSO browser state is bounded and minimally retained

- **Slug:** `sso-browser-state-protection`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** capability
- **Owner:** eugenelim

## Outcome

Persistent SSO browser state is time-bounded, minimally stored, protected from concurrent browser launches, and not repeatedly recaptured, while macOS keychain operations remain within an explicitly derived lock budget.

## Boundary

- Credential-broker browser-state capture, storage, expiry, refresh cooldown, per-profile browser-launch serialization, and macOS keychain call budgeting.
- Pack dependency schemas, catalogue defaults, lint wording, optional client hooks, live credential transcripts, and consumer retry behavior remain outside this intent.

## Owner

- eugenelim, with credential-broker maintainers.

## Unresolved questions

- Choose the maximum browser-session lifetime and automatic-recapture cooldown from measured operator and IdP behavior.
- Choose batching, per-call timeout, or both for macOS keychain operations, including behavior while an operator is responding to a keychain prompt.
- Fix the browser-launch lock wait and stale-recovery policy separately from the short store-transition lock.

## Projection

- One delivery brief, [sso-browser-state-delivery](../briefs/sso-browser-state-delivery.md), whose slices group into three specifications: capture modes and stderr bounding; browser-state security and recapture controls; and macOS keychain latency and lock-budget controls.

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

## Answers to the unresolved questions

Decided 2026-11-05 by the owner as configurable, documented defaults, so measuring operator and IdP behavior is a manual follow-up and not a precondition:

- Maximum browser-session lifetime: 12 hours, enforced at read time.
- Automatic-recapture cooldown: 15 minutes, kept in broker-written state.
- Browser-launch lock wait: 120 seconds, with stale recovery, separate from the short store-transition lock.
- macOS keychain: both batching and a per-call timeout of 5 seconds. The lock budget is derived as calls multiplied by the timeout, plus margin. The owner's keychain prompt response time is covered by the timeout, not by holding the store lock.

## Current truth

Verified 2026-11-05: the broker has no maximum age, cooldown or launch lock; `_capture` still takes `persist: bool` and `headless: bool`; engine stderr is still inherited. This intent now also owns the former `credential-broker-bounded-modes-and-errors` (mode enum and stderr bounding), which ships first.

## Readiness

- **Route:** brief. See [sso-browser-state-delivery](../briefs/sso-browser-state-delivery.md).
- **First slice:** mode enum plus refresh stderr bounding, and confirmation of which accepted RFC the `Engine-Change-RFC:` trailer names.
- **Agent-only proof:** unit tests with a fake `security` binary, a fake child that writes a path to stderr, and a two-process fake launch lock.
- **Manual dependency:** real keychain timing runs and a live IdP check of the defaults; both are named non-blocking follow-ups in the brief.

## Riskiest assumption

**Riskiest assumption:** the broker can enforce session age, cooldown and the launch lock through broker-written state without a background process. Tested agent-only with fakes for the keychain, the clock and a singleton lock.

## Outcome note

Capture modes (`operator-register`, `ephemeral-register`, `automatic-refresh`) and refresh stderr bounding, absorbed from `credential-broker-bounded-modes-and-errors`, are part of this outcome: browser state is only protected if capture exposes explicit modes and bounded errors. They ship as the first slice of the delivery brief.
