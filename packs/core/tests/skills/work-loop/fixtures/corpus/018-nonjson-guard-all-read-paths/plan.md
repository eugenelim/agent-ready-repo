# Plan: nonjson-guard-all-read-paths

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `packs/atlassian/.apm/skills/{jira,confluence-crawler}/scripts/_client.py`
- a new test under `packs/atlassian/tests/skills/jira/`
- `pack.toml`, `.claude-plugin/plugin.json`, `workspace.toml`

**What demonstrates done**
- Per-skill suites; the mutation check on the scanner; `make ci`.

**What I am NOT changing**
- `confluence-publisher` / `jira-align` — no SSO path, so no expiry to diagnose.
- Retry, redirect, or status-code handling.
- The wording of the existing diagnosis, so operator-facing text is unchanged.

## Security reasoning (inline — `security-reviewer` is a named skip)

- **Authn-session.** The failure was diagnostic, not a control gap: the request
  already failed. But a wrong diagnosis has a real cost — "invalid JSON" sends an
  operator to debug a parser while their session is simply expired, and the
  recovery they need (re-register) is never suggested.
- **Why the token path must NOT get the diagnosis.** Symmetry would be wrong
  here. Reporting "session expired" where no session exists is a confident wrong
  answer, and worse than the generic error it replaced. AC2 pins that.
- **No new attacker surface.** `_json` reads the same body the caller already
  read and raises a typed error; nothing is logged, echoed, or retried.
- **What this does not do.** It does not make a 2xx *trustworthy* — only whoami
  can check identity. Other reads still accept a parseable body at face value,
  which is correct: they have no identity to check against.

## Declined patterns

- **Tempted:** apply the diagnosis on both auth paths for symmetry. **Declined:**
  see above; it is the one change here that could make things worse.
- **Tempted:** leave `whoami`'s original try/except in place after adding the
  shared decoder. **Declined:** it became unreachable — dead code that reads like
  a live guard is how the next person concludes the guard is per-method.
- **Tempted:** stop at jira, as the entry says. **Declined:** measured the
  siblings first. The crawler has the same SSO path and the same gap; fixing one
  of two leaves the defect standing behind a compliant example — the same trap
  PR #956 documented for the `--insecure` warning.

## Anchor-test sweep

- jira suite (186) and crawler suite (150) both exercise these clients heavily.
- `test-lint-sso-config.py` pins `_sso_config.py` / `setup_sso.py` byte-identical
  across jira and crawler; `_client.py` is NOT in that duplicated set (the two
  clients differ), so no parity assertion applies.
- Running `pytest packs/atlassian/tests/` wholesale hits 13 pre-existing
  collection errors from duplicate test basenames across skill dirs — identical
  on `origin/main`, and not how CI runs the pack (each skill suite runs with its
  own `working-directory`).

## Verification log

- **AC1** jira 15 sites and crawler 5 sites routed; each client left with exactly
  one direct `resp.json()`, inside `_json`.
- **AC4** mutation: adding a read method that calls `resp.json()` directly fails
  `test_no_read_path_calls_resp_json_directly`; removing it passes.
- **Two self-inflicted bugs, both caught by these tests before pushing.** The
  blanket string replace rewrote `_json`'s OWN body into `self._json(resp)` —
  infinite recursion — once in each client. The second time was a substring
  match: an 8-space `return resp.json()` pattern matched inside a 12-space line.
  Prefer a line-anchored rewrite over `str.replace` on indented code.
- **Suites** jira 186 passed; crawler 150 passed; `make lint-ruff` exit 0.
- **REVIEW** `adversarial-reviewer` and `security-reviewer` = named skips.
