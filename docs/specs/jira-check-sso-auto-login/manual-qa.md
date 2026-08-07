# Manual QA — jira-check-sso-auto-login

The Testing Strategy's *whole change* row is a Visual / manual QA rung: exercise
the real built artifact and **record observed stdout, stderr and exit code**.
This is that record. Run 2026-08-06 on macOS 15 (darwin 25.5.0), Python 3.13.13,
against the shipped `references/sso-config.toml` (`auth_default = "creds"`).

## 1. Token path unchanged, no browser

```console
$ cd packs/atlassian/.apm/skills/jira
$ python scripts/jira.py check
```

**stdout:** *(empty)*

**stderr:**

```
error: namespace 'jira': missing required credential(s): BASE_URL, API_TOKEN
  BASE_URL:
    Tier 1: env 'JIRA_BASE_URL' not set
    Tier 2: macOS Keychain — entry not present
    Tier 3: dotfile ~/.agentbundle/credentials.env absent
  API_TOKEN:
    Tier 1: env 'JIRA_API_TOKEN' not set
    Tier 2: macOS Keychain — entry not present
    Tier 3: dotfile ~/.agentbundle/credentials.env absent
```

**exit:** `2` — byte-identical to the pre-change output. No browser, no
recapture, no engine spawn.

## 2. `--insecure` warns on the token path (AC18)

```console
$ python scripts/jira.py --insecure check
```

**stdout:** *(empty)*

**stderr:** the same credential report, preceded by the new line:

```
warning: --insecure disables TLS certificate verification for this invocation.
```

**exit:** `2`.

`--insecure` is a **global** flag and must precede the subcommand.
`jira.py check --insecure` exits `2` from argparse with `unrecognized
arguments: --insecure` — the plan's canonical command block said the latter and
was corrected.

## 3. SSO-cookie path, end to end through the real engine

Not in the Testing Strategy's row, but run because the fake-broker rung cannot
prove the wiring. A temporary `sso-config.toml` with `auth_default =
"sso-cookie"`, the **real** projected engine copied to a throwaway
`HOME/.agentbundle/bin/`, and no registered profile:

```console
$ HOME=/tmp/sso-e2e python scripts/jira.py check
```

**stderr:**

```
sso-broker get-cookies: profile 'jira' not registered; run 'sso-broker register jira ...'
INFO jira.cli: SSO session unavailable for profile jira: SSO session unavailable for profile jira; run 'sso-broker register jira'
notice: the SSO session for profile jira has expired. Re-establishing it headlessly — no browser will be shown, and the sign-in destination comes from the engine's stored profile, not from sso-config.toml.
INFO jira.cli: recapture attempt for profile jira
sso-broker refresh: profile 'jira' not registered; run 'register' first
error: no SSO session has ever been captured for profile jira on this machine — ask the user to run: python scripts/jira.py check --register
```

**exit:** `2`.

That is the whole chain through real artifacts: the real config loader, real
`credbroker`, a real subprocess spawn of the real engine, engine exit `4` →
`SsoProfileNotRegisteredError` → the user-addressed remediation. Exactly one
recapture attempt; no retry; no browser.

```console
$ HOME=/tmp/sso-e2e python scripts/jira.py whoami
```

**stderr:** `error: SSO session unavailable for profile jira; run 'sso-broker
register jira'` — and **no** recapture attempt, which is AC19/AC31's point.

```console
$ HOME=/tmp/sso-e2e python scripts/jira.py check --register
```

**stderr:**

```
error: could not confirm where jira.corp.example.com sends users to sign in, so the configured destination https://sso.corp.example.com cannot be attested. If it is correct, register with: python scripts/setup_sso.py
```

**exit:** `2`. Derivation ran and refused **before** any browser could open.

## What this session did not exercise

- **No live Data Center instance and no identity provider.** Nothing here
  proves what Chromium emits during a real redirect chain, nor Seraph's actual
  status codes. The fake-broker rung proves argv, exit-code routing,
  destination pinning, and the timeout and retry bounds.
- **No successful recapture.** Every path above ends in a refusal, because a
  success needs a captured session. The success path is covered by the unit
  suites against a fake engine.
- **No Windows run.** The `taskkill` tree-kill arm and the reserved-device-name
  behaviour are reasoned from Win32 semantics; they are verified only when
  AC26's parity run is green.
- **No Playwright.** `launch_persistent_context(headless=True)` and the
  `add_cookies` seeding (AC35) are unprobed, as AC35 itself records.
