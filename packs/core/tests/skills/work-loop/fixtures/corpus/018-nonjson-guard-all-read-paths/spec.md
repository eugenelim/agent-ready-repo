# Spec: nonjson-guard-all-read-paths

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none new. An existing diagnosis is generalised from one read
  method to all of them, in two clients.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Risk trigger: security boundary — credentialed HTTP clients and
session-expiry handling. `security-reviewer` is a NAMED SKIP under this session's
no-subagent instruction; reasoning is inline in the plan. Delivers the deferral
recorded as `nonjson-2xx-guard-all-read-paths` (spec/jira-check-sso-auto-login
AC11), which PR #956 deliberately left out as too large to bundle. -->

## Objective

On the SSO-cookie path a `2xx` is not evidence of a live session: a reverse
proxy commonly answers an expired one with `200` plus the IdP login page.
`whoami` diagnosed that; every other read decoded the body directly, so the same
login page surfaced as "invalid JSON" — a parser error where the true cause is
"your session expired".

## Acceptance Criteria

- [x] **AC1 — one decoder, used by every read.** `_json(resp)` carries the
  diagnosis; all 15 jira read sites and all 5 crawler sites route through it.
  Verified: each client has exactly one direct `resp.json()`, inside `_json`.

- [x] **AC2 — the token path keeps the true error.** A non-JSON `2xx` without a
  cookie session is a server or proxy fault, not an expiry; claiming otherwise
  would send the operator to re-register a session that was never involved. The
  original exception propagates there.

- [x] **AC3 — `whoami` keeps only what is genuinely its own.** The parseable-but
  -identity-less case stays: only that endpoint promises an identity, so only
  there can its absence be diagnosed. The non-JSON half moved to the shared
  decoder rather than being duplicated.

- [x] **AC4 — the fix cannot decay one method at a time.** A source scan fails if
  any read calls `resp.json()` outside `_json`, and a second test asserts the
  decoder and its diagnosis text exist exactly once. Mutation-verified: adding an
  unguarded read method fails the scan.

- [x] **AC5 — the sibling client with the same gap is fixed too.**
  `confluence-crawler` has an SSO-cookie path and the identical shape — one
  guarded read, three unguarded. The entry named only jira; fixing one of two SSO
  clients would leave the same defect behind a compliant example.
  `confluence-publisher` and `jira-align` have no SSO path, so they are not
  applicable.

- [x] **AC6 — released.** atlassian pack 0.8.3 → 0.8.4, `plugin.json` in parity,
  projections regenerated.

- [x] **AC7 — the backlog entry is removed.**

## Boundaries

### Never do

- Never apply the expired-session diagnosis on the token path. AC2 is the rail.
- Never re-inline the diagnosis text at a call site; AC4's second test fails.

## Testing Strategy

- **TDD + mutation** for AC1–AC4. Per-skill suites: jira 186, crawler 150.
