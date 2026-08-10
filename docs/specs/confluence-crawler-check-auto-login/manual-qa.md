# Manual QA: Confluence crawler check auto-login

## Stubbed CLI journey

**Status:** Passed — 2026-08-10

The user ran the focused suite in a writable environment with the repository's
local CredBroker package available: 42 tests passed. Its boundary-level CLI
journey used a throwaway `sso-config.toml`, the real selector and SSO client
factory, stubbed cookie resolution and HTTP transport, and no real browser or
network. The complete Confluence crawler suite also passed after two legacy
non-identity response fixtures were updated to return a usable stub identity.

The bounded journey is:

1. Select SSO-cookie authentication from a throwaway configuration.
2. Make the first direct `whoami()` probe raise the typed unavailable-session
   signal and record that its client closes.
3. Record one `refresh_sso_session("confluence")` call with no keyword
   arguments and capture the four-part stderr disclosure.
4. Make the second fresh `whoami()` probe return `{"username": "Example User"}`
   and record that its client closes.
5. Stop after the second probe.

Real credentials, browser profiles, browser launch, network access, setup, and
crawl output are outside this QA session and must remain untouched.
