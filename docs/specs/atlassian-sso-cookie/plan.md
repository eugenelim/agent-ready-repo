# Plan: atlassian-sso-cookie

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change has three layers, built bottom-up so each rests on a tested floor.

**Layer 1 — `credbroker` gains an SSO consumer family (platform-agnostic).**
The library that already resolves the `creds` (token) family for every
credentialed skill gains a second family: a public `load_sso_cookies(profile)`
resolver that locates `~/.agentbundle/bin/sso-broker.py`, runs `get-cookies
<profile>` via `subprocess.run`, and returns the on-disk jar path — proceeding
**only** on exit 0 with a readable path, failing closed otherwise. Alongside it
land reusable validation primitives (https-only scheme guard, root-relative
endpoint check, cookie-domain confinement, send-host membership) that the
`sso-broker.py` *engine* does not perform and that this RFC adds *above* it. The
engine is untouched; Playwright stays in the engine; `credbroker`'s base import
graph stays stdlib-only. This is the riskiest layer to get right (it is the
security control surface) and the most reusable, so it is built and tested
first, in isolation from any consumer.

**Layer 2 — the atlassian consumer seam.** Each SSO-capable skill ships
`references/sso-config.toml` (placeholder-shaped upstream) and a small config
loader that reads `[sso]`, applies the Layer-1 validation primitives, and drives
the `auth_default` selector. A new structural lint pins the upstream file's
shape. A setup helper reads the config and drives `sso-broker register`, seeding
the runtime profile from the file (RFC-0035 Open Q2 default).

**Layer 3 — the two clients.** `jira/_client.py` and
`confluence-crawler/_client.py` each gain a cookie-auth path selected by the
`auth_default` resolution: build an httpx client with the cookie jar attached, no
`Authorization` header, proxy/trust-store env honored, and a GET/HEAD allowlist
at the `_request` chokepoint that refuses every mutating verb (including the
`raw()` escape hatch) before the wire. The frontmatter flips to `auth:
sso-cookie`, the Security sections carry both brokers' phrase sets, and
`lint_credentialed_skills.py` is amended to (a) require both phrase sets for a
dual-auth skill and (b) accept a `credbroker` SSO-resolver import in place of an
in-`scripts/` broker path expression — mirroring RFC-0023's `creds` migration.

The riskiest part is the security boundary: cookie capture/send confinement and
the fail-closed selector. Those are Layer 1, TDD, tested before any client wiring
exists. The token path stays byte-identical throughout — the regression bar is
"a token user with no SSO config sees no change."

## Constraints

- **RFC-0035** — DC-only, read-first, one-broker-with-`creds`-fallback,
  pre-baked `sso-config.toml`. All five Decisions adopted at their defaults.
- **RFC-0013** — the four-broker contract (argv ban, never-logged,
  path-not-value handoff, corporate-proxy/trust-store passthrough). Preserved;
  the broker engine is consumed unchanged. The one-broker-with-fallback erratum
  is already landed (RFC-0013 § Errata).
- **RFC-0023** — `credbroker` is the pip-installable consumer-resolution library;
  shared modules are no longer projected into skill `scripts/`. The SSO resolver
  extends this library rather than introducing a new one.
- **ADR-0026** (this PR's companion) — records that SSO consumer-resolution
  belongs in the `credbroker` resolver library, platform-agnostic; a second
  RFC-0013 § Errata records the consumer-surface addition. Authored once this
  design is adversarial-clean.
- **CONVENTIONS § 4** — spec metadata contract: the deferred live-DC AC carries
  `(deferred: atlassian-sso-cookie-live-dc-read-transcript)` resolving to the
  `docs/backlog.md` heading of that slug.

## Construction tests

Most construction tests live per-task below. Cross-cutting:

**Integration tests:**
- A mock-transport (`httpx.MockTransport`) end-to-end through each client's
  cookie path asserting: cookie jar attached, no `Authorization` header,
  GET/HEAD succeed, `raw("POST", …)` refused before the wire.
- Token-path regression: with no SSO config / `auth_default = "creds"`, the
  resolved `Credentials` + outbound headers are identical to the pre-change path.

**Manual verification:**
- Live DC read transcript (deferred — gates Experimental → Accepted; **closes spec
  AC19**): `sso-broker register <profile>` (headed Chromium SSO) → `get-cookies` →
  `jira` JQL search returns results → `sso-broker test` exits 0. Captured at
  `notes/live-dc-read.md`.

## Design (LLD)

Stack: Python 3.12, stdlib + `httpx` 0.28.1 (existing client dep). No new
dependency. `credbroker` is the pip-installable library at
`packs/credential-brokers/.apm/user-libs/credbroker/`; the atlassian clients are
the two skills under `packs/atlassian/.apm/skills/`.

### Design decisions

- **SSO consumer resolution lives in `credbroker`, not in the clients or a new
  user-lib.** `credbroker` is already the single consumer-resolution home (the
  `creds` family); RFC-0023 removed in-pack shared-module projection, so a
  shared client-side helper has no other single-source home. A new user-lib is
  rejected (user constraint + cost); per-client duplication is rejected (the
  validation primitives are a security surface that must not drift). Traces to:
  AC1, AC3. Rejected alternatives carried in this section per ADR-0026.
- **The validation primitives live in `credbroker`, the `sso-config.toml`
  *schema* lives in the consumer.** The generic guards (scheme, root-relative,
  domain confinement) are reusable by any platform integration; the file shape
  is atlassian-specific. Traces to: AC3, AC4.
- **Reads enforced by a chokepoint allowlist, not a method blocklist.** The
  `_request` method is the single point every call (including `raw()`) funnels
  through; a GET/HEAD allowlist there covers future verbs by construction.
  Traces to: AC9.

### Interfaces & contracts

- `credbroker.load_sso_cookies(profile: str) -> Path` — new public surface
  (re-exported from `__init__.__all__`); raises a `credbroker` exception type on
  fail-closed. Version 0.1.1 → 0.2.0. Traces to: AC1, AC2.
- `credbroker` validation primitives + jar filter (names finalized in T2) — pure
  functions: https-only scheme guard over `login_url`/`success_url_pattern`/
  `base_url`, root-relative `validation_endpoint`, cookie-domain membership, and
  `filter_jar_to_domains(jar, cookie_domains)` (the load-time confinement the
  unchanged over-broad-capture broker can't do). Traces to: AC3, AC4, AC5.
- `references/sso-config.toml` `[sso]` schema — the connection-param key set is
  the contract the structural lint pins (AC15).
- No `contracts/` artifact: this feature exposes no REST/event/RPC surface
  (Contract: none).

### Failure, edge cases & resilience

- `get-cookies` exit 2 (not registered / no jar), broker-absent, uncaught broker
  exception → fail closed with verbatim re-`register` remediation; never fall
  through to `creds` when `auth_default = "sso-cookie"`. Traces to: AC2.
- Over-broad captured jar → consumer filters to `cookie_domains` at load before
  attach; sent cookie set ⊆ declared domains. Traces to: AC4, AC5.
- `401` mid-session (cookie rotation) → surface re-`register` remediation
  verbatim; no silent browser-flow retry; stop using the stale jar. Traces to:
  AC11.
- Send-host ∉ `cookie_domains` (downstream edit drifts the base URL) → fail
  closed before any request. Traces to: AC6.
- Corrupt / hand-edited `sso-config.toml` (non-https URL incl. `base_url`,
  off-host endpoint) → rejected by the validation primitives at load and by the
  T7 setup helper before `register`. Traces to: AC3, AC14.

### Dependencies & integration

- Consumes the unchanged `sso-broker.py` engine via `subprocess.run` (env
  `{**os.environ}` passthrough per RFC-0013 § 1).
- `httpx` cookie-path wiring: `trust_env=True` (proxy + `SSL_CERT_FILE`/`_DIR`),
  explicit SSL context mapping `REQUESTS_CA_BUNDLE`, no bare `verify=True` that
  would clobber the trust store. Traces to: AC8. Cross-link: `## Rollout`.

## Tasks

### T1: `credbroker` SSO resolver — broker resolution + exit-code mapping + fail-closed

**Depends on:** none

**Touches:** `packs/credential-brokers/.apm/user-libs/credbroker/*.py`,
`packages/agentbundle/tests/unit/*`

**Tests:**
- `get-cookies` exit 0 + readable path → returns the path (AC1).
- exit 2, broker-absent, uncaught broker exception → raises the fail-closed
  exception with the verbatim remediation; never returns a path (AC2).
- broker resolves at `Path.home()/.agentbundle/bin/sso-broker.py`; absent → raise
  with install-the-pack remediation (AC1).
- `subprocess.run` is the only process-spawn used; no cookie value crosses argv
  or is logged (AC10).

**Approach:**
- Add `_sso.py` (or extend `_core`) with `load_sso_cookies(profile)`; re-export
  from `__init__.__all__`; bump `__version__` to `0.2.0`.
- Fake the broker in tests with a stub script returning canned exit/stdout.

**Done when:** new credbroker SSO-resolver unit tests green; `credbroker`
imports with no third-party dependency; version asserted 0.2.0.

### T2: `credbroker` SSO validation primitives + load-time jar filter

**Depends on:** none

**Touches:** `packs/credential-brokers/.apm/user-libs/credbroker/*.py`,
`packages/agentbundle/tests/unit/*`

**Tests:**
- non-`https` `login_url`/`success_url_pattern`/`base_url` rejected; `https`
  accepted (AC3).
- `validation_endpoint` not root-relative (scheme, host, `//`, no leading `/`)
  rejected; `/rest/api/2/myself` accepted (AC3).
- cookie whose domain ∉ declared `cookie_domains` rejected; inside accepted (AC3).
- `filter_jar_to_domains`: an over-broad jar (IdP/analytics cookies + the session
  three) reduces to only the cookies whose domain ∈ `cookie_domains`, using a
  normalized label-boundary suffix match — include the `evil-corp.example.com` vs
  `corp.example.com` near-miss (rejected) and `jira.corp.example.com` (admitted)
  (AC4).
- send-host membership: base host ∈ `cookie_domains` passes, mismatch raises
  (AC6).

**Approach:**
- Pure functions raising a `credbroker` validation exception; `filter_jar_to_domains`
  returns the reduced jar. AC4 (cookie-domain filter) and AC6 (send-host
  membership) consume the **same** `cookie_domains` normalization primitive, so the
  label-boundary rule is single-sourced. Table-driven tests.

**Done when:** validation-primitive + jar-filter unit tests green across the
valid/invalid table.

### T3: `sso-config.toml` reference files + config loader + `auth_default` selector

**Depends on:** T2

**Touches:** `packs/atlassian/.apm/skills/jira/references/sso-config.toml`,
`…/confluence-crawler/references/sso-config.toml`, the per-skill config loader.

**Tests:**
- loader parses `[sso]`, applies T2 primitives, returns a validated config (AC3).
- selector: config absent or `auth_default = "creds"` → `creds` path; outbound
  headers + resolved `Credentials` identical to pre-change (AC13); `auth_default =
  "sso-cookie"` + registered → cookie path; `sso-cookie` + unavailable → fail
  closed (AC2).

**Approach:**
- Ship placeholder-shaped files (`auth_default = "creds"`, `*.invalid` hosts) per
  RFC-0035 § 3.
- Loader is small and per-skill (the schema is consumer-specific); selector keys
  solely on `auth_default` (no separate `enabled` flag).

**Done when:** loader/selector unit tests green; reference files present and
placeholder-shaped (AC12).

### T4: structural `sso-config.toml` lint

**Depends on:** T3

**Touches:** `tools/lint-sso-config.py` (new), `tools/hooks/pre-pr.py`,
CI wiring, `tools/test-lint-sso-config.py` (new).

**Tests:**
- upstream files pass; a fixture with an unknown `[sso]` key, a cookie-value-
  shaped value, `auth_default != "creds"`, or a non-`*.invalid` host each fail
  (AC15).
- no false-positive on `crowd.token_key`, `session_filename`,
  `success_url_pattern` (structural TOML-key check, not substring).

**Approach:**
- `.py` (Windows portability); parse TOML, assert key-set ⊆ schema, value shapes,
  placeholder invariants. Wire into `pre-pr.py` and the build-check/CI surface
  that runs the lint family.

**Done when:** lint green on repo, red on each crafted fixture; wired into the
gate.

### T5: `jira/_client.py` cookie-auth path + selector wiring

**Depends on:** T1, T2, T3

**Touches:** `packs/atlassian/.apm/skills/jira/scripts/_client.py`,
`…/jira/scripts/test_*.py`.

**Tests (mock transport):**
- cookie jar attached (filtered to `cookie_domains`), no `Authorization` header on
  the outbound request; sent cookie set ⊆ declared domains (AC4, AC5, AC7).
- GET/HEAD reach the wire; `raw("POST", …)`/PUT/DELETE raise the verbatim
  writes-refused message and the transport records **zero** requests (AC9).
- base host ∉ `cookie_domains` → fail closed before any request (AC6).
- `401` → verbatim re-`register` remediation, no browser retry, stale jar not
  reused (AC11).
- jar read in-process from the broker path only; never re-written/copied/logged
  (AC10).
- proxy/trust-store wiring present (`trust_env`, SSL context, `REQUESTS_CA_BUNDLE`
  mapping; no bare `verify=True`) (AC8).
- token-path regression: no SSO config → headers/`Credentials` identical to
  today (AC13).

**Approach:**
- Add a cookie-path branch in `load_credentials`/client construction selected by
  the T3 selector; resolve cookies via `credbroker.load_sso_cookies`, filter via
  `credbroker.filter_jar_to_domains`; build the httpx client with the filtered jar
  and no auth header; add the GET/HEAD allowlist at `_request` (covers `raw()`).

**Done when:** jira cookie-path tests green; token-path regression green. The
jira-side mock-level coverage (broker invocation shape, jar attachment,
no-`Authorization`, writes-refused, fail-closed, domain confinement) lands here
toward the AC17 rollup (T6 mirrors it for confluence-crawler).

### T6: `confluence-crawler/_client.py` cookie-auth path

**Depends on:** T5

**Touches:** `packs/atlassian/.apm/skills/confluence-crawler/scripts/_client.py`,
its tests.

**Tests:** the AC4/AC5/AC6/AC7/AC8/AC10/AC11/AC13 set, mirrored for
confluence-crawler. **AC9 differs:** confluence-crawler has no `raw()`, so assert
the `_request` chokepoint refuses a non-GET/HEAD `method` argument before the wire
(transport records zero requests) — not a `raw("POST")` test.

**Approach:** apply the settled T5 shape to confluence-crawler's client; the
allowlist guards its `_request` `method` parameter.

**Done when:** confluence-crawler cookie-path tests green; token-path regression
green; the confluence-crawler half of the AC17 mock-coverage rollup lands
(completing AC17 with T5).

### T7: setup helper — seed the runtime profile from `sso-config.toml`

**Depends on:** T3

**Touches:** the per-skill setup path that drives `sso-broker register`.

**Tests:** goal-based — helper reads the validated config and invokes
`sso-broker register <profile> --login-url … --cookie-domain …` with values from
the file (no cookie value on argv); it runs the AC3 scheme/endpoint validation
**before** invoking `register`, so a malformed `login_url`/`base_url`/
`validation_endpoint` is rejected and never seeded into the broker profile the
unchanged `test`/`get-cookies` read (AC14). Broker engine unchanged.

**Approach:** thin wrapper translating validated `[sso]` connection fields into
`register` flags (RFC-0035 Open Q2 default: register seeds from the file).

**Done when:** helper drives `register` from the file in a faked-broker test;
malformed-config fixture is rejected before `register`.

### T8: frontmatter flip + dual-auth Security phrases + `lint_credentialed_skills.py` amendment

**Depends on:** T5, T6

**Touches:** `jira/SKILL.md`, `confluence-crawler/SKILL.md`,
`tools/lint_credentialed_skills.py`, `tools/test-lint-credentialed-skills.py`,
`packs/core/seeds/docs/CONVENTIONS.md` (+ projected `docs/CONVENTIONS.md`).

**Bundled fix (same-concern ride-along):** correct the two stale
`tools/lint-credentialed-skills.sh` references in CONVENTIONS § Frontmatter schema
(lines ~1044, ~1107) to the canonical `tools/lint_credentialed_skills.py` (the
`.sh` is a thin back-compat shim that delegates to it). `docs/CONVENTIONS.md` is
self-host-projected (`self_host.py` allow-list), so edit the **seed**
`packs/core/seeds/docs/CONVENTIONS.md` and run `make build-self` to regenerate the
projection — do not hand-edit the projected file. This task already touches the
same lint, so the reference fix lands with it rather than as a loose flag.

**Tests:**
- amended lint: a skill carrying the `metadata.auth-fallback: creds` marker must
  satisfy **both** the `sso-cookie` and `creds` phrase sets — missing either
  fails, carrying both passes (AC16).
- amended lint: a `credbroker` SSO-resolver import satisfies the broker-invocation
  requirement for `auth: sso-cookie` (no in-`scripts/` broker path expression
  required), mirroring `has_credbroker_import` for `creds` (AC16).
- both skills pass the amended lint after the flip.

**Approach:**
- Flip `metadata.auth` to `sso-cookie` and add `metadata.auth-fallback: creds`;
  add both phrase sets to the Security sections; amend the lint to (a) read the
  `auth-fallback` marker and union the required phrase sets, and (b) add a
  `has_credbroker_sso_import` check accepted in the `auth == "sso-cookie"` branch
  in place of the `sso-broker.py` path expression. Keep `REQUIRED_PHRASES_BY_BROKER`
  single-sourced.

**Done when:** `lint_credentialed_skills.py` + its self-test green; both skills
declare `auth: sso-cookie` + the fallback marker and pass.

### T9: docs — upstream-upgrade path + status + changelog

**Depends on:** T3

**Touches:** `docs/guides/` (adapt-to-project `.upstream` companion merge for the
pre-baked config), `docs/product/changelog.md`, the spec status.

**Tests:** goal-based — guide describes the class-2 `.upstream` companion merge
upgrade path (AC18); changelog `[Unreleased]` entry added (user-visible skill
behavior change).

**Approach:** document the pre-bake → ship → upgrade lifecycle (RFC-0035 § 3a);
note in the changelog. Flip the spec to `Implementing`/`Shipped` in the
implementing PR per the set-final-status-in-the-implementing-PR convention.

**Done when:** the upgrade-path guide and changelog entry land; gate green.

## Rollout

- **Delivery:** additive and reversible. Upstream default is `auth_default =
  "creds"`; with no SSO config every skill behaves exactly as today, so the
  change is dark for token users until an enterprise opts in by pre-baking
  `auth_default = "sso-cookie"`. No data migration; rollback is reverting the
  PR(s).
- **Infrastructure:** none new in-repo. Per-developer: the `sso-broker` engine's
  existing Playwright dependency (surfaced on first `register`); the `0600`
  cookie jar under `~/.agentbundle/sso-cookies/`.
- **External-system integration:** a real Data Center instance behind corporate
  SSO is required for the live transcript (deferred AC); the corporate proxy +
  internal CA must be honored end to end (the httpx wiring AC).
- **Deployment sequencing:** Layer 1 (`credbroker` resolver + primitives) ships
  before any client wiring depends on it; the structural lint ships with the
  reference files it pins; the frontmatter flip ships after the clients carry the
  credbroker SSO import the amended lint expects. Feature stays **Experimental**
  (RFC status) until the live-DC transcript lands; the spec ships with that one
  AC deferred.

## Risks

- **DC read REST might require an XSRF header even on GETs** (RFC-0035 Open Q1).
  If the transcript shows 401/403 on reads, read-only scope shrinks and the XSRF
  follow-on is pulled forward. Falsifiable only against a live instance.
- **`lint_credentialed_skills.py` amendment is delicate** — it must accept the
  credbroker SSO import without weakening the in-`scripts/` enforcement for any
  skill that still resolves the broker locally. Mitigate by mirroring the
  existing `has_credbroker_import` shape and adding both pass/fail fixtures.
- **Substring-trap on the new lint** (`feedback_credentialed_lint_substring_trap`)
  — the structural `sso-config.toml` lint must be TOML-key structural, never a
  `grep` for `token`/`session`.
- **Version-bump test traps** — bumping `credbroker` to 0.2.0 may trip
  version-assertion tests in CI-ungated roots; run the full `packages/agentbundle`
  suite by hand on the bump.

## Changelog

- 2026-06-16: initial plan. SSO consumer-resolution placed in `credbroker`
  (platform-agnostic) rather than a new user-lib or per-client duplication, after
  establishing that RFC-0023 retired in-pack shared-module projection and that
  `credbroker` is the single consumer-resolution home in use. Governance recorded
  in ADR-0026 + a second RFC-0013 § Errata (authored once the design is
  adversarial-clean).
