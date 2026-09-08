# Make SSO contention recoverable and auditable

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/sso-store-transition-serialization AC24](../../specs/sso-store-transition-serialization/spec.md)
- **Authority:** [spec/sso-store-transition-serialization AC10](../../specs/sso-store-transition-serialization/spec.md)

## Outcome

An unattended SSO re-authentication can retain its recapture record, recover correctly from short store contention, and have its macOS keychain timing evidenced.

## Opportunity

Recapture logging currently goes to stderr, a recoverable contended-store exit is treated as an operator action, and the real-keychain end-to-end timing procedure remains owed.

## What this absorbs

### sso-contended-consumer-backoff

AC16 logs recapture through `log.info`, but `jira.py:780-783` configures logging with no filename. The record therefore goes to stderr, which an agent may discard, leaving an unattended re-auth repudiable. The recorded fix is an append-only `0600` log under `~/.agentbundle/logs/`.

`sso-broker.py`'s new contended exit code `6` is documented as recoverable, but no consumer backs off on it. `jira.py:709` has a bare `except credbroker.SsoError` that routes it to `EXIT_USER_ACTION`, telling the operator to re-register over a condition that clears in under a second. The recorded fix is to catch `SsoStoreContendedError` in `jira.py`'s check path and retry once with backoff before falling through to the user-action exit.

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
