# Plan: credentialed-cli-hygiene

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `packs/atlassian/.apm/skills/confluence-crawler/scripts/crawl_space.py` — AC2.
- `packs/atlassian/.apm/skills/jira-align/scripts/jira_align.py` — AC3.
- `packages/credbroker/tests/unit/test_sso_resolver.py` — AC5.
- `tools/lint-sso-config.py` + `tools/test-lint-sso-config.py` — AC6–AC8.
- Tests for AC4 under each pack's test tree.
- `workspace.toml` — AC10.

**What demonstrates done**
- TDD: warning tests red before the `print` is added; lint grammar cases red
  before the check exists.
- Goal-based: `tools/lint-sso-config.py` and `tools/test-lint-sso-config.py`
  both exit 0; `make ci`.

**What I am NOT changing**
- `jira.py` and `publish_page.py` — already compliant; touching them would be
  churn.
- `_client.py`'s `resp.json()` sites — a separate spec.
- The grammar itself. The lint mirrors the engine; it does not redefine it.

## Security reasoning (inline — `security-reviewer` is a named skip)

`security-reviewer` cannot be dispatched under this session's no-subagent
instruction. The boundary-matching modules are reasoned through here instead, so
the skip is not a silent one.

- **`secrets-and-crypto` / transport.** AC1–AC3 are a *disclosure* change, not a
  control change: no code path gains or loses TLS verification. The risk of
  getting it wrong is the inverse of the usual one — a warning printed on the
  SSO-cookie path where the flag is inert would tell an operator verification is
  off when it is on. That is why AC2 mandates two distinct messages rather than
  one, matching `jira.py`.
- **`path-and-file` / CWE-22, CWE-73.** AC6 is the real security content. The
  `[sso].profile` value composes a filesystem path under
  `~/.agentbundle/browser-state/<profile>`; a traversal value is a confinement
  escape. The engine already refuses at runtime (`validate_sso_profile`), so this
  is defence in depth moved earlier — a build-time refusal so a bad value never
  ships in an adopter-facing reference config.
- **Windows reserved device names.** Carried deliberately: `CON.toml` resolves to
  the console device regardless of directory, so the reserved-name refusal is
  part of the grammar and not an optional extra.
- **Duplication risk.** Restating the grammar in a stdlib-only lint creates a
  second copy of a security-relevant constant. AC7's drift guard is the control;
  without it this change would trade a runtime gap for a slower-moving one.

## Declined patterns

- **Tempted:** import `validate_sso_profile` into the lint instead of restating
  the pattern. **Declined:** the lint is pure-stdlib by design and must run on a
  checkout with nothing installed. AC7's equality assertion buys the safety
  without the dependency.
- **Tempted:** fold in the `_client.py` `_json` helper while in the atlassian
  pack. **Declined:** ~16 call sites in a credentialed client is its own change
  with its own tests, and bundling would hide both.
- **Tempted:** "fix" `confluence-publisher` and `figma` because the backlog entry
  named them. **Declined:** measured first — the publisher already warns and
  figma has no such flag. Editing them would be churn against a stale claim.
- **Tempted:** one shared warning string for both branches in `crawl_space.py`.
  **Declined:** the two cases say opposite things about whether verification is
  on. Sharing the string is the bug.

## Tasks

### T1 — AC2/AC3/AC4: `--insecure` warnings
- **Mode:** TDD. Warning tests first.
- **Tests:** per-CLI stderr assertions.

### T2 — AC5: dynamic credbroker version
- **Mode:** TDD.
- **Tests:** the rewritten `test_version_matches_pyproject`.

### T3 — AC6/AC7/AC8: profile grammar in the lint
- **Mode:** TDD. Self-test cases (reject + accept + drift guard) before the check.
- **Tests:** `tools/test-lint-sso-config.py`.

### T4 — AC9/AC10: gates + backlog disposition
- **Mode:** goal-based.

## Anchor-test sweep

- `tools/test-lint-sso-config.py`'s `_DUPLICATED` tuple pins file paths (per
  `docs/specs/pack-test-boundary-remaining-packs/plan.md:335`). This change adds
  cases, and does not move any pinned file — no update needed, but confirm.
- `test_version_matches_pyproject` is itself the anchor T2 rewrites.

## Verification log

- **AC1** Measured, not assumed: `jira.py` and `publish_page.py` already warn;
  `figma` has no `--insecure` flag. Only `crawl_space.py` and `jira_align.py` were silent.
- **AC2/AC3/AC4** 6 crawler tests + 4 jira-align tests green. The crawler tests drive
  `main_async` with a patched `_select_auth_path`; the jira-align tests drive the real CLI
  as a subprocess. Two crawler tests assert the messages are NOT interchangeable — the
  cookie path must not claim verification was disabled.
- **Placement corrected mid-task:** jira-align's warning was first added at client
  construction (after `load_credentials()`), where a run with no credential returns first
  and discloses nothing. Moved into `main()` after logging config, matching
  `publish_page.py`. `test_warning_precedes_credential_resolution` pins it.
- **Flag ordering learned from the failure:** `--insecure` is a top-level flag, so
  `jira_align.py --insecure check`; `check --insecure` is an argparse error.
- **AC5** `test_version_matches_pyproject` reads pyproject via tomllib; 8 tests green.
- **AC6/AC8** 17 self-test cases pass (10 new, covering traversal, absolute path,
  trailing newline, leading punctuation, over-length, two reserved-device forms,
  non-string, and two accept cases).
- **Boundary fixtures corrected:** the naive 64-char fixture (`"a"*64`) failed for the
  WRONG reason — a dotless 64-char alphanumeric matches the opaque-token detector, whose
  charset excludes `.`. Both boundary cases now carry a dot so they exercise the length
  grammar and nothing else.
- **AC7** drift guard proven non-tautological: with credbroker importable it returns []
  today, and returns 1 finding when the engine's pattern is mutated in memory.
- **AC9** `tools/lint-sso-config.py` -> 2 files scanned, 0 findings, exit 0;
  `tools/test-lint-sso-config.py` -> exit 0.
- **AC10** three entries removed from `[backlog].open` (137 -> 134).
- **REVIEW** `adversarial-reviewer` and `security-reviewer` = named skips (session
  instruction prohibits subagent dispatch). Security reasoning applied inline and recorded
  in this plan's § Security reasoning.
