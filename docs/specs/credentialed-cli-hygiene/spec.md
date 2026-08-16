# Spec: credentialed-cli-hygiene

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none new. This spec brings three surfaces into line with rules
  that already exist — `docs/CONVENTIONS.md`'s `--insecure` disclosure rule and
  `credbroker._sso.validate_sso_profile`'s profile grammar.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. One risk trigger fires: security boundary — two of the three
items concern TLS-verification disclosure and a path-traversal-relevant profile
grammar on credentialed CLIs. `security-reviewer` cannot be dispatched under this
session's no-subagent instruction, so its absence is a NAMED SKIP and the
boundary-matching security-checklists reasoning is applied inline and recorded in
the plan. The G-plan human gates are satisfied by the operator's standing
authorization for this run. -->

## Objective

Three rules in this repository are stated but not enforced everywhere they
apply. A rule that holds on three of four surfaces is worse than one that holds
nowhere: readers generalise from the compliant cases.

Success: each rule holds on every surface it names, and each is pinned by a test
or a lint that fails when the rule is broken again.

## Acceptance Criteria

- [x] **AC1 — `--insecure` warns on every CLI that honours it.**
  `docs/CONVENTIONS.md` § *Five anti-patterns rejected by name* requires
  `--insecure` to "emit a stderr warning". Measured state, which differs from
  the backlog entry that recorded this:

  | CLI | Before | Action |
  |---|---|---|
  | `jira.py` | warns on both paths | none — already compliant |
  | `confluence-publisher/publish_page.py` | warns | none — already compliant |
  | `confluence-crawler/crawl_space.py` | **silent** | add both branches |
  | `jira-align/jira_align.py` | **silent** | add the honoured branch |
  | `figma` | no `--insecure` flag exists | not applicable |

  The entry named `confluence-publisher` and `figma` as silent. Neither is: the
  publisher warns already, and figma has no such flag. Both are recorded here so
  the correction is not lost.

- [x] **AC2 — `crawl_space.py` warns on both auth paths.** It has an SSO-cookie
  branch, so it takes `jira.py`'s two-case shape: on the token path the flag is
  honoured and the warning says verification is off; on the SSO-cookie path the
  flag is inert (the client builds its own SSL context) and the warning says it
  is being ignored. `jira.py:1091` records why the ignored-case notice cannot be
  scoped to one subcommand — *every* subcommand on that path ignores the flag —
  so `crawl_space.py`'s early-returning `--check` path gets it too.

- [x] **AC3 — `jira_align.py` warns where the flag is honoured.** It has no SSO
  path, so it needs only the one branch.

- [x] **AC4 — the warnings are pinned by tests.** A test per CLI asserts the
  warning reaches stderr when `--insecure` is passed, and that it is absent
  otherwise. Without this the rule regresses the moment someone reorders `main`.

- [x] **AC5 — `credbroker.__version__` is checked against `pyproject.toml`, not
  a literal.** `test_version_matches_pyproject`
  (`tests/unit/test_sso_resolver.py:136`) asserts `== "0.6.0"`, so the test's
  name is a lie: it pins a literal that a version bump must remember to update
  in two places. It reads the version from `pyproject.toml` with `tomllib`.

- [x] **AC6 — `lint-sso-config.py` enforces the profile grammar.** It validates
  the `[sso]` key set but not the value of `[sso].profile`, so a pre-baked
  traversal value (`../../etc`) ships upstream and fails only at runtime. The
  lint applies the same grammar the engine enforces — `_SSO_PROFILE_PATTERN`
  (`^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`) plus the Windows reserved-device-name
  refusal — as a build-time check.

  The grammar is **restated, not imported**: `tools/lint-sso-config.py` is
  pure-stdlib by design and runs against a repo checkout with no dependency on
  `packages/credbroker` being installed. AC7 is what keeps the copy honest.

- [x] **AC7 — the restated grammar cannot drift from the engine's.** A self-test
  case asserts the lint's pattern string is byte-identical to
  `credbroker._sso._SSO_PROFILE_PATTERN` and its reserved-name set equal to
  `_RESERVED_DEVICE_NAMES`, skipping if `credbroker` is not importable. A copy
  with no drift guard is how the two silently diverge.

- [x] **AC8 — the new lint check has self-test coverage both ways.**
  `tools/test-lint-sso-config.py` gains a case for a rejected profile (traversal,
  over-length, leading punctuation, and a reserved device name) and confirms a
  valid profile still passes.

- [x] **AC9 — the shipped configs still pass.** `python3 tools/lint-sso-config.py`
  exits 0 against the repo's own `sso-config.toml` files, and
  `python3 tools/test-lint-sso-config.py` exits 0.

- [x] **AC10 — the backlog entries are dispositioned.**
  `insecure-warning-sibling-clis`, `credbroker-version-test-dynamic` and
  `lint-sso-config-profile-charset` are removed from `[backlog].open`.

## Boundaries

### Always do

- Mirror the existing compliant wording (`jira.py`, `publish_page.py`) rather
  than inventing a third phrasing for the same warning.

### Never do

- Never make `tools/lint-sso-config.py` import `credbroker`. It must run on a
  bare checkout. AC7 is the drift control instead.
- Never weaken the grammar to make a shipped config pass. If a shipped config
  fails AC9, the config is wrong.
- Never touch the `resp.json()` read paths in `_client.py`. That is
  `nonjson-2xx-guard-all-read-paths` — a ~16-site change to a credentialed
  client, deliberately taken as its own spec rather than buried here.

## Testing Strategy

- **TDD** for AC4 (warning tests), AC5 (dynamic version), AC6–AC8 (lint grammar
  + drift guard + self-test cases). Each has a clear red state.
- **Goal-based** for AC9: both scripts exit 0.

## Assumptions

- The `--insecure` flag on `crawl_space.py`'s SSO-cookie path is genuinely inert,
  matching `jira.py`'s documented behaviour: `from_sso_cookies` builds its own
  SSL context and the flag is never forwarded. Verified by reading the
  constructor call — it takes no `verify_tls` argument.
