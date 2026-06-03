# Plan: credentialed-cli-exit-code-contract

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Establish the canonical taxonomy + a top-level catch-all handler in the
reference consumer (`jira`) first, then apply the identical pattern to the
other four. The shape per skill: (1) define/normalize the `EXIT_*` constants to
`0 OK · 1 USER_ERROR · 2 AUTH · 3 SERVER · 4 INTERNAL`; (2) wrap the CLI entry so the
existing typed-exception handlers map to canonical codes **and** a final
`except Exception` maps anything else — including `Tier2HardFailError` and the
shim's `ModuleNotFoundError` — to `4 INTERNAL` with a clean one-line stderr (type +
safe message, never the token, never a traceback); (3) add the message-first
"When a request fails" body to the `SKILL.md`. The riskiest parts are
`confluence-publisher` (its `EXIT_USER_ACTION=2` / `EXIT_ERROR=1` need
per-call-site remapping — a USER_ACTION that meant "creds problem" becomes 2
AUTH, a conflict/other becomes the right canonical code) and `confluence-crawler`
(today bare integer literals, no named constants — introduce the table without
changing any *observable* behavior except the reconciled codes). The guide
update lands last so its documented codes match the implemented reference.

The change is code + docs only; no new module, no dependency, the shim
untouched (Boundaries § Never do).

## Constraints

- **RFC-0006 / RFC-0013 / ADR-0003** — credentialed-skill architecture. The
  frozen "skills don't hold credentials; do not run setup for them" rule is
  preserved; no credential value on stdout/argv/error paths.
- **credential-broker-contract spec AC6/AC8** — `credentials_shim.py` is
  byte-equivalence-gated; this plan does not touch it.
- The canonical taxonomy is documented in the guide + this spec only; CONVENTIONS
  (RFC-gated) is deferred to the A+B RFC.

## Construction tests

**Integration tests:** a cross-skill consistency check asserting all five define
identical `EXIT_OK/USER_ERROR/AUTH/SERVER/INTERNAL` values (goal-based; lives wherever
T1 establishes the skill test harness).
**Manual verification:** none — every behavior here is mechanically checkable.

## Design (LLD)

### Design decisions
- **Top-level catch-all over per-exception patching.** A final `except Exception
  → EXIT_INTERNAL` at the entry point fixes the uncaught-traceback class of bug once,
  rather than chasing each new exception type (authsome `cli/main.py:491` pattern,
  adapted). Traces to: AC2, AC3.
- **Dedicated `4 INTERNAL` rather than overloading `1`.** Keeps `1` purely
  USER_ERROR; authsome folds infra-unavailable into its generic `1`, we don't.
  Traces to: AC1, AC3.
- **Per-skill identical constants, not a shared module.** Structural
  centralization is deferred to the A+B RFC (Boundaries § Never do). Traces to:
  AC1.

### Interfaces & contracts
- The exit-code table in `spec.md` § Objective **is** the contract surface
  (consumed by agents/scripts that drive these CLIs). No `contracts/` artifact;
  documented in the authoring guide. Traces to: AC1, AC6.

### Failure, edge cases & resilience
- `Tier2HardFailError` (keychain hard-fail) and `ModuleNotFoundError`
  (unprojected shim) are the two failures currently escaping uncaught → both map
  to `4 INTERNAL` via the catch-all, with the stderr message naming the cause and
  the remediation (`make build-self` / install route). No retries added.
- **Catch-all boundary invariant:** the top-level handler is `except Exception`,
  **never** `except BaseException`. `SystemExit` (figma raises `SystemExit(str)`
  for input validation → exit 1) and `KeyboardInterrupt` (crawler → 130) derive
  from `BaseException` and must stay outside it. On the *unexpected* branch the
  handler prints `type(exc).__name__` + a fixed safe line — it does **not**
  interpolate `str(exc)` (which could carry a token-shaped value). Traces to:
  AC2, AC4.

## Tasks

### T1: `jira` — canonical taxonomy + top-level catch-all (reference)

**Depends on:** none

**Tests:**
- Unit: `CredentialsMissingError`→2, a simulated 401 and 403→2, a 5xx/transport
  error→3, `Tier2HardFailError`→4, an arbitrary unexpected `Exception`→4 (AC3).
- Unit: catch-all is `except Exception` — a raised `SystemExit("msg")` exits 1
  (not swallowed to 4); the unexpected branch raised with a token-shaped message
  prints type + safe line, never the message (AC2, AC4).
- Subprocess: invoke `python scripts/jira.py check` (documented invocation) with
  the shim import forced to fail (`ModuleNotFoundError`) and assert exit 4 +
  one-line stderr, **no traceback** (AC2). Per test-real-invocation convention.
- Establishes where these skills' tests live / the harness (note it for T2–T5).

**Approach:**
- Normalize `EXIT_*` in `jira.py` to the canonical set (already `0/1/2/3`; add
  `EXIT_INTERNAL = 4`).
- Wrap the `main`/`_run` dispatch so existing `AuthError`/`JiraError` handlers
  keep mapping to 2/3, and a trailing `except Exception` maps to `EXIT_INTERNAL`;
  on the unexpected branch print `type(exc).__name__` + a fixed safe line (no
  `str(exc)`, no token, no traceback). Do **not** use `except BaseException`.
- Add the message-first "When a request fails" body + canonical-code references
  to `jira/SKILL.md` (mirroring guide Step 8).

**Done when:** the unit + subprocess tests above are green; `jira.py check`
returns 4 (not a traceback) on a forced shim/keychain failure.

### T2: `jira-align` — apply the T1 pattern

**Depends on:** T1
**Touches:** packs/atlassian/.apm/skills/jira-align/**

**Tests:** same matrix as T1 against `jira_align.py` (AC1–AC3).
**Approach:** apply T1's constant set + catch-all + SKILL.md body; `jira-align`
already uses `0/1/2/3`.
**Done when:** T2 test matrix green.

### T3: `figma` — apply the T1 pattern

**Depends on:** T1
**Touches:** packs/figma/.apm/skills/figma/**

**Tests:** same matrix against `figma.py` (AC1–AC3).
**Approach:** apply the pattern; `figma` already uses `0/1/2/3`. Preserve the
existing untrusted-text security note.
**Done when:** T3 test matrix green.

### T4: `confluence-publisher` — remap divergent codes + apply pattern

**Depends on:** T1
**Touches:** packs/atlassian/.apm/skills/confluence-publisher/**

**Tests:** T1 matrix **plus** an assertion that each former `EXIT_USER_ACTION=2`
/ `EXIT_ERROR=1` call site now returns the canonical code for its actual cause
(AC1).
**Approach:** read every `EXIT_USER_ACTION` / `EXIT_ERROR` use; map
credential/auth causes→2, server→3, usage→1, infra/unexpected→4; add catch-all;
add SKILL.md body. Note the observable exit-code change in the PR (accepted break,
spec § Assumptions).
**Done when:** T4 test matrix green; no `EXIT_USER_ACTION`/bare `EXIT_ERROR`
remains.

### T5: `confluence-crawler` — introduce named constants + apply pattern

**Depends on:** T1
**Touches:** packs/atlassian/.apm/skills/confluence-crawler/**

**Tests:** T1 matrix against `crawl_space.py`, plus per-call-site assertions for
the two splits this skill needs: the usage-error sites (`crawl_space.py:287,294`
— `--space`/`--root` missing) return `1`; the `AuthError` sites (`:256,274`)
return `2`; the partial-completion site (`:351`, `return 0 if failed == 0 else 1`)
returns `3` when pages failed; `KeyboardInterrupt` (`:359`) still returns `130`
and is **not** caught by the `except Exception` catch-all (AC1, AC2).
**Approach:** `crawl_space.py` today uses bare literals and conflates two meanings
on `2` (usage *and* auth). Introduce the `EXIT_*` table; **enumerate every
`return 2`** and split usage→`1 USER_ERROR` vs auth→`2 AUTH`; remap the
partial-completion `else 1`→`3 SERVER` (boundary ruling); keep `130` (128+SIGINT)
outside the `0–4` table and outside the catch-all (it rides `KeyboardInterrupt`,
a `BaseException`); add catch-all + SKILL.md body. Flag the `2→1` and `1→3`
observable breaks in the PR.
**Done when:** T5 test matrix green; no bare integer `return` in the entry path
except the documented `130`; both observable breaks noted in the PR.

### T6: authoring guide — document the canonical table

**Depends on:** T1
**Touches:** docs/guides/how-to/add-a-credentialed-skill.md

**Tests:** goal-based — grep (anchored on section content, not step ordinals)
asserts the broker-import example now maps `Tier2HardFailError → 4` (correcting
today's `→ 3` at `add-a-credentialed-skill.md:118-120`), shows the
`except Exception` catch-all + `EXIT_INTERNAL`, and that the canonical `0–4`
table is present near "When a request fails"; fences balanced; Step 7 lint-pinned
blocks byte-unchanged (AC6).
**Approach:** update the broker-import example handler to show the catch-all +
`EXIT_INTERNAL` and the corrected `Tier2HardFailError → 4`; add the canonical
`0–4` table near "When a request fails"; keep the body message-first.
**Done when:** grep checks pass; `lint-credentialed-skills` + `lint-agent-artifacts`
green.

## Rollout

Pure code + docs change to user-scope pack skills; no infra, no flag, no
migration. Reversible by revert. Observable breaks (accepted, 0.1.0 packs, noted
in the PR): `confluence-publisher` `EXIT_USER_ACTION`/`EXIT_ERROR` remap;
`confluence-crawler` usage `2→1` and partial-completion `1→3`.

## Risks

- **`confluence-publisher` semantic remap.** `EXIT_USER_ACTION=2` may encode a
  meaning other than "auth" at some call sites; mis-mapping changes behavior.
  Mitigation: T4 reads every call site before remapping; per-site test.
- **Test-harness location unknown for pack skills.** T1 establishes it; if these
  skills have no existing test home, T1 must create a minimal one (kept local to
  the skill, no new top-level dir — Boundaries § Never do).

## Changelog

- 2026-06-03: initial plan. Taxonomy + top-level-catch-all settled from authsome
  research (`errors.py` + `utils.py:197`) and maintainer leans per user
  delegation; structural centralization deferred to the A+B RFC.
