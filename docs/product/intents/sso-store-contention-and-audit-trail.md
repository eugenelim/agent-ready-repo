# Make SSO contention recoverable and auditable

- **Slug:** `sso-store-contention-and-audit-trail`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [spec/sso-store-transition-serialization AC24](../../specs/sso-store-transition-serialization/spec.md); [spec/sso-store-transition-serialization AC10](../../specs/sso-store-transition-serialization/spec.md)

## Outcome

An unattended SSO re-authentication can retain its recapture record, recover correctly from short store contention, and have its macOS keychain timing bounded by a tested lock budget.

## Opportunity

Recapture logging currently goes to stderr, a recoverable contended-store exit is treated as an operator action, and the real-keychain end-to-end timing procedure remains owed.

## What this absorbs

### sso-contended-consumer-backoff

This section also absorbs the legacy `sso-recapture-audit-sink` record.

AC16 logs recapture through `log.info`, but `jira.py`'s `main` calls `logging.basicConfig` with no filename. The record therefore goes to stderr, which an agent may discard, leaving an unattended re-auth repudiable. The recorded fix is an append-only `0600` log under `~/.agentbundle/logs/`.

`sso-broker.py`'s new contended exit code `6` is documented as recoverable, but no consumer backs off on it. `jira.py`'s check path has a bare `except credbroker.SsoError` handler that routes it to `EXIT_USER_ACTION`, telling the operator to re-register over a condition that clears in under a second. The recorded fix is to catch `SsoStoreContendedError` in `jira.py`'s check path and retry once with backoff before falling through to the user-action exit.

Unblocks when: `spec/sso-store-transition-serialization` ships.

### sso-ac10-end-to-end-timing

Spawn-cost extrapolation predicts that the macOS keychain path exceeds AC10, but the end-to-end procedure can write login-keychain entries and prompt. The required settling evidence is operator consent on macOS and twenty projected-broker timings recorded in the existing manual-QA artifact.

Unblocks when: the twenty consented macOS projected-broker timings are recorded.

## Assumptions

- No additional assumptions.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

## Current truth

Verified 2026-11-05: `jira.py` handles `credbroker.SsoError` at two sites and maps it to `EXIT_USER_ACTION`; nothing in `packs/atlassian` references `SsoStoreContendedError`. The comment at `jira.py:680` still says the recapture notice goes to stderr and the durable sink is deferred. `sso-store-transition-serialization` is Shipped, so both fixes are unblocked.

## Readiness

- **Route:** new-spec, for the backoff and the audit sink together (one session). Neither depends on `sso-browser-state-protection`.
- **First slice:** catch `SsoStoreContendedError` in the check path, retry once with backoff, then fall through to the user-action exit; write the recapture record to an append-only 0600 file under `~/.agentbundle/logs/`.
- **Agent-only proof:** tests with a stub broker that raises the contended error once, then succeeds; a permissions assertion on the log file.
- **The AC10 timing item is reduced.** The 20 consented macOS timings stay a manual, non-blocking follow-up. The agent-only substitute is the fake-`security` budget test in slice 2 of `sso-browser-state-delivery`; if that lands, drop the manual item.

## Non-goals

- The 20 consented real-keychain timings; they stay a manual non-blocking follow-up and are replaced by a fake-`security` budget test.
- Browser-state lifetime, cooldown and launch locking, owned by `sso-browser-state-protection`.

## Riskiest assumption

**Riskiest assumption:** a single backoff retry clears real store contention. Tested agent-only with a stub broker that raises `SsoStoreContendedError` once and then succeeds, and another that raises it twice, which must fall through to the user-action exit.
