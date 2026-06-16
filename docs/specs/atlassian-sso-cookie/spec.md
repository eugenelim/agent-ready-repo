# Spec: atlassian-sso-cookie

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0035, RFC-0013, RFC-0023, ADR-0026
- **Brief:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A developer on an Atlassian **Data Center** instance fronted by corporate SSO
— where personal access tokens are blocked — runs `jira` read operations
(JQL search, get issue/project/user, server info) and `confluence-crawler`
authenticated by a captured SSO web session, with no API token. The two skills
resolve the SSO session through a new platform-agnostic consumer resolver in the
`credbroker` library, which subprocess-invokes the unchanged `sso-broker.py`
engine and returns a cookie jar; the skills attach those cookies to their HTTP
client with no `Authorization` header. A single `jira` skill still serves
today's token users unchanged — the auth path is chosen at runtime from a
version-controlled, adopter-editable `references/sso-config.toml`, not by forking
the skill. An enterprise pre-bakes its instance config (default sign-in method,
flavor, base URL, SSO connection parameters) into a pack customization, so a
developer installs the pack already pointed at the corporate instance and only
runs `sso-broker register` once. Token users — and any install with no SSO
config — get byte-identical `creds` behavior. Write operations over the cookie
path are refused with an explicit message (deferred pending XSRF design); Cloud
is out of scope (cookie auth is removed there).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Resolve the SSO session **only** through the new `credbroker` consumer
  resolver, which invokes the unchanged `sso-broker.py` via `subprocess.run`;
  treat the jar-path's *contents* as secret (never logged, never echoed, never
  surfaced to the LLM).
- Confine cookies to the declared `cookie_domains` **in the consumer at load
  time** — the unchanged broker captures an over-broad jar (every cookie observed
  across the SSO/IdP/analytics redirect chain), so the consumer filters the loaded
  jar to `cookie_domains` before attaching it, and requires the request base host
  to be a member of that set (fail-closed on mismatch).
- Wire the cookie-path HTTP client to honor the corporate proxy and system trust
  store — `HTTPS_PROXY` / `NO_PROXY` and the CA bundle — and send **no**
  `Authorization` header on the cookie path.
- Keep today's `creds` (token) path byte-identical when no SSO config is present
  or `auth_default = "creds"`.

### Ask first

- Adding any **new** Python dependency to `credbroker` (its base import graph is
  stdlib-only) or to either atlassian skill.
- Widening scope beyond `jira` read paths + `confluence-crawler` (e.g. enabling
  writes, `confluence-publisher`, or `jira-align`).
- Changing the `sso-config.toml` key schema once the structural lint pins it.

### Never do

- **Never modify `sso-broker.py` or the RFC-0013 four-broker contract** beyond
  the already-landed one-broker-with-fallback erratum. The broker engine is
  consumed unchanged.
- **Never add a new pip-installable user-lib** — the SSO consumer resolver lands
  in the existing `credbroker` library, not a new distributable.
- **Never enable a mutating HTTP verb on the cookie path.** Reads are enforced by
  a GET/HEAD allowlist at the `_request` chokepoint (covering the `raw()` escape
  hatch), not a per-method blocklist.
- **Never silently downgrade to `creds`** when `auth_default = "sso-cookie"` but
  the broker/profile is unavailable — fail closed with the re-`register`
  remediation.
- **Never let a real cookie value, real host, or non-`creds` `auth_default` ship
  in the upstream `references/sso-config.toml`** — upstream is placeholder-shaped
  (`*.invalid` hosts, `auth_default = "creds"`).

## Testing Strategy

- **`credbroker` SSO resolver (broker resolution, exit-code → outcome mapping,
  jar load, fail-closed branches): TDD.** Pure logic with a compressible
  invariant; the broker subprocess is faked to return canned exit codes + jar
  paths. Unit level.
- **`sso-config.toml` validation primitives (https-only scheme guard over
  `login_url`/`success_url_pattern`/`base_url`, root-relative endpoint,
  cookie-domain confinement, send-host membership) and the load-time jar filter:
  TDD.** Table-driven over valid/invalid inputs; this is the SSRF/over-capture
  control surface, so each rejection path — and the over-broad-jar → filtered-jar
  reduction — is a test. Unit level.
- **Cookie-path HTTP wiring (no `Authorization` header; cookie jar attached;
  GET/HEAD allowlist refuses writes incl. `raw("POST", …)`; proxy/trust-store
  env honored): TDD via a mock transport.** Assert on the *outbound request*
  (headers, cookies, refusal) through httpx's `MockTransport`, not on internal
  client attributes. Unit/integration level.
- **`auth_default` selector + `creds` fallback (absent/`creds` → token path
  byte-identical; `sso-cookie` + registered → cookie path; `sso-cookie` +
  unavailable → fail closed): TDD.** Unit level.
- **Structural `sso-config.toml` lint + amended `lint_credentialed_skills.py`
  (dual-auth phrase sets; credbroker-SSO-import accepted): goal-based check.**
  Run each lint against the repo and against crafted fixtures; the exit code is
  the contract. A test that just restates the lint is not added.
- **Live Data Center read transcript (`register` → `get-cookies` →
  authenticated `jira` search returns results; `sso-broker test` → 0): manual
  QA, exercised end-to-end against a real DC instance.** This is the gate from
  Experimental to Accepted and is **deferred** (no DC instance in CI).

## Acceptance Criteria

Numbered for plan traceability; each maps to one or more `plan.md` tasks.

- [ ] **AC1.** `credbroker` exposes a public SSO consumer resolver (e.g.
  `load_sso_cookies(profile)`) that resolves `sso-broker.py` at
  `Path.home()/.agentbundle/bin/sso-broker.py`, runs `get-cookies <profile>` via
  `subprocess.run`, and returns the on-disk jar path; a broker-absent resolution
  raises with the install-the-pack remediation. `credbroker` base import graph
  stays stdlib-only and its version is bumped (0.1.1 → 0.2.0).
- [ ] **AC2.** The resolver proceeds on the cookie path **only** when
  `get-cookies` exits `0` with a readable jar path; any non-zero exit (the broker
  returns `2` for both "not registered" and "no jar"), a broker-absent failure, or
  an uncaught broker exception fails closed with the verbatim remediation
  `"SSO session unavailable for profile <profile>; run 'sso-broker register
  <profile>'"` — it never falls through to `creds` when `auth_default =
  "sso-cookie"`.
- [ ] **AC3.** `credbroker` exposes reusable validation primitives that reject: a
  non-`https` `login_url`, `success_url_pattern`, **or `base_url`**; a
  `validation_endpoint` that is not a root-relative path (must lead with `/`, no
  scheme, host, or protocol-relative `//`); and any cookie whose domain is outside
  the declared `cookie_domains`.
- [ ] **AC4.** Because the unchanged broker captures an over-broad jar (every
  cookie observed across the SSO redirect chain — `--cookie-domain` only writes
  profile metadata, and `get-cookies` re-materialises the *full* jar to the `0600`
  floor on every call), the **consumer** filters the loaded jar to the declared
  `cookie_domains` at load time, before attaching it. The match is a
  **normalized label-boundary suffix match** — both sides dot-stripped (the broker
  stores domains via `lstrip(".")` while cookie `domain` fields keep a leading
  dot); a cookie domain `d` is admitted iff `d == allowed` or `d` is a
  dot-delimited subdomain of `allowed` (so `evil-corp.example.com` is rejected
  against `corp.example.com`, and `jira.corp.example.com` is admitted). The filter
  is applied on **every** resolution and its result is never written back to the
  broker path (the on-disk jar stays over-broad; see AC10).
- [ ] **AC5.** On the cookie path the cookie set that actually leaves the process
  is a subset of the declared `cookie_domains`, asserted on the **outbound request**
  via a mock transport (not merely on a base-host check). The test matrix includes
  the `evil-corp.example.com` vs `corp.example.com` near-miss.
- [ ] **AC6.** The consumer client's request base host is a member of
  `cookie_domains`; a mismatch fails closed before any cookie-bearing request
  leaves the process.
- [ ] **AC7.** On the cookie path, the HTTP client sends **no** `Authorization`
  header and attaches the (filtered) cookie jar; verified on the outbound request
  via a mock transport.
- [ ] **AC8.** The cookie-path HTTP client honors `HTTPS_PROXY`/`NO_PROXY` and the
  system/corporate trust store (CA bundle), wired against actual httpx behavior
  (`trust_env=True`; an explicit SSL context that honors `SSL_CERT_FILE`/
  `SSL_CERT_DIR` and maps `REQUESTS_CA_BUNDLE`; the trust store is not clobbered
  by a bare `verify=True`).
- [ ] **AC9.** Only GET/HEAD reach the wire on the cookie path, enforced by an
  allowlist at the `_request` chokepoint in both clients. In `jira` (which exposes
  a `raw(method, …)` escape hatch) a mutating call — including `raw("POST", …)` —
  raises "writes over SSO-cookie auth are not supported yet (RFC-0035 v1); use a
  personal access token, or wait for the XSRF follow-on"; `confluence-crawler`
  (no `raw()`) refuses a non-GET/HEAD `method` at the same chokepoint. In both,
  the mock transport records **zero** requests for a refused verb.
- [ ] **AC10.** The consumer reads the jar in-process from the broker-supplied
  path only — it never re-writes, copies, or logs the jar or its contents,
  including never persisting the AC4-filtered jar back to the broker path (the
  `0600` at-rest floor is the broker's responsibility, verified by the broker's
  own tests).
- [ ] **AC11.** On a `401` from a read call, the client surfaces the verbatim
  re-`register` remediation `"401 Unauthorized — SSO session expired; run
  'sso-broker register <profile>' to re-authenticate"`, does **not** silently
  retry into a browser flow, and stops using the known-stale jar (no further
  cookie-bearing request with that session).
- [ ] **AC12.** `jira` and `confluence-crawler` ship `references/sso-config.toml`,
  placeholder-shaped upstream: `auth_default = "creds"`, `*.invalid` hosts, no
  cookie values.
- [ ] **AC13.** The selector resolves the cookie path iff `auth_default =
  "sso-cookie"` and a profile is registered; with the config absent or
  `auth_default = "creds"` the outbound request headers and the resolved
  `Credentials` are identical to today's `creds` path (a token user with no SSO
  config sees no behavior change).
- [ ] **AC14.** The setup helper reads the validated `sso-config.toml` and drives
  `sso-broker register <profile>` from it (RFC-0035 Open Q2), passing no cookie
  value on argv, and validates `login_url`/`base_url` scheme + `validation_endpoint`
  (AC3 primitives) **before** invoking `register`, so no unvalidated value is ever
  seeded into the profile the unchanged broker's `test`/`get-cookies` read.
- [ ] **AC15.** A new structural lint parses the upstream
  `references/sso-config.toml` and fails if any `[sso]` key is outside the declared
  connection-param schema, if any value matches a cookie-value shape, if
  `auth_default != "creds"`, or if any host is not `*.invalid`. The check is
  TOML-key structural, **not** a substring scan (no false-positive on
  `crowd.token_key`, `session_filename`, `success_url_pattern`).
- [ ] **AC16.** `jira` and `confluence-crawler` declare `auth: sso-cookie` with a
  `metadata.auth-fallback: creds` marker, and their Security sections carry
  **both** brokers' required phrase sets. `lint_credentialed_skills.py` is amended
  so that (a) a skill carrying the `auth-fallback: creds` marker must satisfy both
  the `sso-cookie` and `creds` phrase sets, and (b) a `credbroker` SSO-resolver
  import satisfies the broker-invocation requirement (mirroring RFC-0023's
  `has_credbroker_import` for `creds`) in place of an in-`scripts/`
  `sso-broker.py` path expression.
- [ ] **AC17.** Mock-level tests cover broker invocation shape, cookie-jar
  attachment, the no-`Authorization` assertion, the writes-refused error, the
  fail-closed branches, and cookie-domain confinement (capture-filter + send
  subset).
- [ ] **AC18.** The upstream-upgrade path for a pre-baked `sso-config.toml` is
  documented as the adapt-to-project `.upstream` companion merge (class-2), so an
  org's edited instance config is not clobbered by a later catalogue release.
- [ ] **AC19.** (deferred: atlassian-sso-cookie-live-dc-read-transcript) A live
  Data Center read transcript (`register` → `get-cookies` → authenticated `jira`
  search returns results; `sso-broker test` → 0) is captured at
  `notes/live-dc-read.md`. This is the gate that flips the feature Experimental →
  Accepted; it reopens when a real corporate-SSO DC instance is available (the
  plan's `## Construction tests` → Manual verification owns the gesture).

## Assumptions

- Technical: All four atlassian `_client.py` authenticate only by building
  Basic/Bearer headers from `credbroker.load_credentials`; none invoke the broker
  or load a cookie jar (source: `packs/atlassian/.apm/skills/jira/scripts/_client.py`,
  `…/confluence-crawler/scripts/_client.py`).
- Technical: `sso-broker.py get-cookies <profile>` exits `0` and prints a `0600`
  jar path on success, `2` when the profile is unregistered or no jar exists, and
  reads no config file — the broker stays unchanged (source:
  `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py` `_do_get_cookies`).
- Technical: `credbroker` (v0.1.1) is a token resolver only (`load_credentials`
  + write helpers); it has no SSO/cookie surface today, and it is the single
  consumer-resolution home actually in use — all six shipped credentialed skills
  are `auth: creds` (source: `packs/credential-brokers/.apm/user-libs/credbroker/__init__.py`;
  skill frontmatter survey).
- Technical: RFC-0023 retired the build-time projection of pack-local shared
  modules into skill `scripts/`; the only surviving cross-skill code-sharing
  mechanism is the pip-installable `credbroker` library (source:
  `packages/agentbundle/agentbundle/build/shared_libs.py:5-18`).
- Technical: `httpx` 0.28.1 defaults `trust_env=True` (honors proxy +
  `SSL_CERT_FILE`/`SSL_CERT_DIR` env) and exposes `verify`/`proxy` params; it does
  **not** read `REQUESTS_CA_BUNDLE`. The RFC §1-step-3 premise that httpx ignores
  proxy/CA env by default is imprecise; the AC is written against actual behavior
  (source: probe `python -c "import httpx; …"` → trust_env default True).
- Technical: `lint_credentialed_skills.py` for `auth: sso-cookie` today requires
  the sso-cookie phrase set + an in-`scripts/` `sso-broker.py` path expression +
  `subprocess.run`, and does not require a credbroker import; moving resolution
  into `credbroker` requires amending it (source:
  `tools/lint_credentialed_skills.py:72-77,930-981`; RFC-0023 `has_credbroker_import`
  precedent at `:425-444`).
- Process: this is full-mode work-loop (security boundary: auth, secrets,
  network I/O); the SSO consumer-resolution decision is recorded in an ADR and a
  second RFC-0013 § Errata entry, authored once the design is finalized (source:
  user confirmation 2026-06-16).
- Product/Scope: v1 covers `jira` read paths + `confluence-crawler`; the
  setup helper reads `sso-config.toml` and drives `sso-broker register` (the
  broker is seeded from the file); writes, `confluence-publisher`, and `jira-align`
  are deferred (source: user confirmation 2026-06-16; RFC-0035 Decisions 1/3/5 +
  Open Questions 2/3).
