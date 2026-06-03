# Spec: credentialed-cli-exit-code-contract

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0006, RFC-0013, ADR-0003
- **Brief:** none
- **Contract:** none <!-- the "contract" here is an exit-code taxonomy documented in the guide, not an OpenAPI/AsyncAPI artifact -->
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The five credentialed CLIs (`jira`, `jira-align`, `confluence-publisher`,
`confluence-crawler`, `figma`) disagree on what their exit codes mean, and
**none** of them catch `Tier2HardFailError` — so a keychain hard-fail, or a
shim that was never projected (`ModuleNotFoundError: credentials_shim`),
crashes with an uncaught Python traceback at exit 1 instead of a defined,
message-bearing code. An agent (or a script) driving these skills cannot
reliably triage a failure: the same exit 1 means "bad arguments" in one skill,
"partial crawl failure" in another, and "the credential subsystem is broken" by
accident in all of them.

This spec gives all five a **single canonical exit-code taxonomy** and a
**top-level handler** that maps every exception — known *or* unexpected — to a
defined code with a clean stderr message (never a traceback, never a
credential value). It aligns the authoring guide so new credentialed skills
inherit the same contract. Success: an operator reads the exit code to bucket
the failure and the stderr message to act on it, identically across all five.

Canonical taxonomy:

The taxonomy is **banded** — `0` success, `1` the coarse functional bucket, and
a reserved **`2–9` credential/auth band** with room to add new credential codes
without renumbering. Only `2` is used today; `3–9` are reserved.

| Code | Name | Meaning | Agent remediation |
|---|---|---|---|
| 0 | `OK` | success | proceed |
| 1 | `ERROR` | **functional / operational error** — bad arguments / usage, upstream 5xx, transport/unreachable, a run that completed with per-item upstream failures (partial crawl), `Tier2HardFailError` (keychain hard-fail), an unprojected shim (`ModuleNotFoundError`), or any otherwise-unhandled exception | read the message; surface it; don't loop (for a shim/keychain message, install / `make build-self`) |
| 2 | `AUTH` | **credential/auth — the user must act**: credential missing, invalid, expired, or rejected (401/403) | run the broker's setup action (user-invoked) — `credential-setup` / re-auth / re-scope |
| 3–9 | *(reserved)* | credential/auth band — future codes (e.g. a later 401-vs-403 split) take `3` onward without colliding with the functional bucket | — |

**Why banded this way.** Every *functional* failure gets the same agent
response ("surface it, don't loop"), so one coarse `1` + a precise message
suffices (the dominant CLI convention; `sysexits` and authsome both lean on the
message for within-bucket detail). *Credential/auth* failures are where the
agent must branch on the remediation (setup vs. re-auth vs. re-scope) and where
new distinctions are most likely, so they get the reserved `2–9` band. `check`
returns `2` on missing credentials, preserving the `author-a-skill.md`
sibling-detection contract (`flow-metrics → jira:check`, `2` = needs setup).

**Two boundary rulings the taxonomy depends on:**

- **Partial/degraded completion → `1`.** `confluence-crawler` today returns `1`
  when a crawl completes but some pages failed — a functional outcome, so it
  stays in the `1` bucket (consistent with `mermaid-renderer`'s `EXIT_PARTIAL=1`
  and authsome's batch-import, which returns its generic code with per-item
  detail in the report). The per-page detail stays in the structured output.
- **The catch-all is `except Exception`, never `BaseException`.** `SystemExit`
  (figma raises `SystemExit(str)` for input validation → `1`) and
  `KeyboardInterrupt` (crawler's `130`) derive from `BaseException` and are
  **deliberately not** caught by the `→ 1` handler. `130` (128+SIGINT) stays
  outside the table by POSIX convention.

## Boundaries

### Always do

- Map **every** exception at the CLI entry point to a canonical code via a
  top-level handler; an exception escaping as an uncaught traceback is a bug.
- Keep credential values out of stdout, argv, and **every** error message —
  print the exception type and a safe message, never the token.
- Make the `EXIT_*` constants identical across all five skills, matching the
  canonical table above byte-for-byte.

### Ask first

- Adding any exit code beyond `0–4` (e.g. a per-skill domain code) — confirm
  before widening the table.
- Re-meaning an existing code beyond the reconcile this spec defines.
- Touching `credentials_shim.py` (byte-equivalence-gated by
  credential-broker-contract AC6/AC8) — default is **don't**.

### Never do

- Never introduce a new shared/projected module or a new top-level dependency
  for this step. Structural centralization of the taxonomy into one shared
  module is deferred to the A+B RFC; step 1 uses per-skill identical constants.
- Never modify the macOS keychain backend `errSec` constants
  (`EXIT_NOT_FOUND=44` / `EXIT_DUPLICATE_ITEM=45` /
  `EXIT_INTERACTION_NOT_ALLOWED=25308`) in **any** `_keychain_macos.py` copy —
  those are the backend's interpretation of `/usr/bin/security` statuses, not CLI
  exit codes.
- Never widen the catch-all to `except BaseException` and never echo `str(exc)`
  verbatim on the unexpected-exception path (it may carry a token-shaped value) —
  print the exception *type* + a fixed safe line.
- Never run credential entry for the user, or pipe a value into
  `credential-setup` (frozen RFC-0006 rule; the "do not run it for them" prose
  stays verbatim).

## Testing Strategy

- **Exit-code mapping per exception type — TDD.** Per-skill unit tests assert
  each known exception maps to its canonical code (`CredentialsMissingError`→2,
  401/403→2, 5xx/transport→1, `Tier2HardFailError`→1) and that an
  *unexpected* exception maps to 1. Compressible invariant.
- **Top-level catch-all, no traceback escapes — TDD via subprocess.** Invoke
  the documented `python scripts/<cli>.py` entry with a forced
  `Tier2HardFailError` / `ModuleNotFoundError` and assert exit 1 + a clean
  one-line stderr (no traceback). Subprocess against the file-path invocation
  per the test-real-invocation convention, not a synthesised import. Also assert
  the catch-all is `except Exception` — a raised `SystemExit("msg")` exits 1
  (via interpreter, not swallowed by the handler) and a `KeyboardInterrupt`
  yields 130.
- **Unexpected-exception non-leak — TDD.** Raise an exception whose `str()`
  carries a token-shaped string; assert stderr prints the exception *type* + a
  fixed safe line and never the message.
- **Canonical-table consistency — goal-based.** A check asserts all five define
  identical `EXIT_OK/ERROR/AUTH` values (and reserve the `2–9` band).
- **Guide + message-first body — goal-based.** Grep asserts the "When a request
  fails" body and the canonical codes are present in all five `SKILL.md` and the
  guide.
- **No credential leakage on failure paths — goal-based.** The existing
  `lint-credentialed-skills` stays green; added handler assertions confirm no
  token reaches stderr.

## Acceptance Criteria

- [ ] All five CLIs define the banded taxonomy as named constants —
  `0 OK · 1 ERROR (functional) · 2 AUTH`, with `3–9` reserved for the
  credential/auth band. `confluence-publisher` is already `0/1/2` (confirm
  meanings). `jira`/`jira-align`/`figma` fold their `SERVER_ERROR=3` into `1`
  (and `USER_ERROR=1` stays `1`). `confluence-crawler` gains named constants
  (today bare literals): usage-error `return 2` sites → `1`, `AuthError` → `2`,
  partial-completion `return 1` stays `1`.
- [ ] Each CLI wraps its entry in a top-level **`except Exception`** handler
  mapping known exceptions to their canonical code and any otherwise-unhandled
  exception to `1`, emitting a clean one-line stderr (no traceback).
  `SystemExit` and `KeyboardInterrupt` are not caught (figma's `SystemExit(str)`
  validation → `1`; crawler's `KeyboardInterrupt` → `130`).
- [ ] `CredentialsMissingError`→2, simulated 401 and 403→2; 5xx/transport→1,
  `Tier2HardFailError`→1, shim `ModuleNotFoundError`→1, and an arbitrary
  unexpected `Exception`→1 — each verified by a per-skill unit test. `check`
  returns `2` on missing credentials (preserves the `jira:check` contract).
- [ ] On the **unexpected-exception** path the handler prints the exception
  *type* + a fixed safe line and does **not** interpolate `str(exc)`; a unit
  test raises an exception whose message contains a token-shaped string and
  asserts it never reaches stderr. `lint-credentialed-skills` stays green; no
  credential value reaches stdout/argv/stderr on any failure path.
- [ ] `credentials_shim.py` is unmodified (its byte-equivalence gate stays
  green).
- [ ] The authoring guide documents the banded table and corrects its current
  `Tier2HardFailError → 3` and `CredentialsMissingError → 2` example to the
  banded scheme (`Tier2HardFailError → 1`, `CredentialsMissingError → 2`) —
  asserted on the section *anchor* and *content* (the `EXIT_*` values + the
  `except Exception` catch-all), not on step ordinals. A message-first "When a
  request fails" body is present in all five `SKILL.md`.
- [ ] The frozen "do not run it for them" rule is preserved verbatim in all
  five skills and the guide.

## Assumptions

- Technical: the five consumers and their divergent taxonomies — jira/jira-align/figma `{0,1=USER_ERROR,2=AUTH_ERROR,3=SERVER_ERROR}`, confluence-publisher `{0,1=ERROR,2=USER_ACTION}`, confluence-crawler bare literals `0/1/2/130` — and that none catch `Tier2HardFailError` (source: grep of `packs/*/.apm/skills/*/scripts`, this session).
- Technical: `44/45/25308` are macOS keychain backend `errSec` constants, not CLI exit codes — out of scope (source: `packs/credential-brokers/.apm/shared-libs/_keychain_macos.py:51-53`).
- Technical: the shim raises `CredentialsMissingError` and `Tier2HardFailError` as public types (source: `credentials_shim.py:57,90`).
- Technical: the five are user-scope packs, not projected into `.claude/skills` — edits land directly in `packs/`, no `build-self` step (source: `ls .claude/skills`).
- Reference: authsome centralizes a typed exception hierarchy plus a single `format_error_code` mapper, and maps **every** exception (including unexpected) to a code at the CLI top — adopted *behaviorally* (the top-level catch-all) (source: `.context/authsome/src/authsome/errors.py`, `utils.py:197-218`, `cli/main.py:491`).
- Reference: authsome maps store/encryption-unavailable to its generic code rather than a dedicated one; we **follow** that — keychain/infra and unexpected errors fold into the coarse `1`, with the message carrying the cause; the reserved `2–9` band gives credential/auth codes room to grow instead (source: `.context/authsome/src/authsome/utils.py:201-218`).
- Process: no existing canonical *consumer-CLI* exit contract — CONVENTIONS § Credentialed skills is silent on it; this spec creates it and records it in the guide + spec, not CONVENTIONS (RFC-gated), for step 1 (source: grep `docs/CONVENTIONS.md`).
- Process: the taxonomy calls were delegated to the maintainer with two stated preferences — minimize churn and reserve a numeric *range* for auth codes (source: user confirmation 2026-06-03). Resolution: banded `0 / 1 ERROR / 2–9 AUTH` (only `2` used now). Adopts authsome's *philosophy* (typed mapper, map-every-exception-at-top, coarse code + message) but not its *numbers* — those are deferred to the A+B pip-manager, where the connection/provider/daemon code set applies and cross-tool drift actually matters; forcing authsome's numbers now would break `author-a-skill.md`'s `check → 2` contract (authsome maps cred-missing → 5).
- Accepted observable breaks (0.1.0 packs): `jira`/`jira-align`/`figma` `SERVER_ERROR=3 → 1`; `confluence-crawler` usage-error `2 → 1` (partial-completion stays `1`); `confluence-publisher` is already `0/1/2` (no code change, confirm meanings). Each is enumerated per call site before remapping (plan T4/T5) (source: maintainer decision, this session).
- Deliberate non-catch: `SystemExit` (figma input-validation `SystemExit(str)`→1) and `KeyboardInterrupt` (crawler→130) are outside the `except Exception` catch-all by design (source: `figma.py` SystemExit raises + `crawl_space.py:359` review finding, this session).
