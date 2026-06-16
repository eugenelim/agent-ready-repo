# RFC-0035: SSO-cookie auth for the atlassian pack (Data Center)

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-16
- **Date closed:** 2026-06-16
- **Related:** [RFC-0013](0013-credential-broker-contract.md) (defines the
  `sso-cookie` broker and **explicitly defers** this work in its § 9
  Out-of-scope), [ADR-0003](../adr/0003-credential-broker-contract.md),
  [RFC-0006](0006-skill-secrets-storage.md). Reverses one named deferral in
  RFC-0013 § 9; the four-broker contract itself is unchanged except for a
  narrow erratum to the "one broker per skill" rule (Decision 2).

## The ask

**Recommendation (BLUF):** Wire the atlassian pack's read skills to the
already-shipped `sso-cookie` broker so they authenticate against
**Atlassian Data Center** instances behind corporate SSO that block API
tokens — starting with `jira` (read paths) and `confluence-crawler`,
validated against a real DC instance, and shipped **Experimental** until that
transcript lands. Enterprise SSO connection parameters live in a new
in-skill **reference config file** that downstream deployments edit, not in
hand-edited runtime state.

**Why now (SCQA):**
- *Situation.* RFC-0013 built the `sso-cookie` broker
  (`~/.agentbundle/bin/sso-broker.py`, six verbs, fully implemented) and named
  "Atlassian Data Center products" as its canonical use case.
- *Complication.* The four atlassian skills ship `auth: creds` (token only).
  On an SSO-only DC instance that blocks personal access tokens, **none of
  them can authenticate** — and RFC-0013 § 9 deferred wiring them to
  `sso-cookie`, partly on the false premise that it is "a frontmatter change
  adopters make in their deployment." It is not: the clients build only
  `Basic`/`Bearer` headers and never call the broker (see Evidence).
- *Question.* Do we close that gap in-tree now, scoped to Data Center and
  read-first, with the enterprise config surfaced as an adopter-editable
  reference file?

**Decisions requested:**

1. **Scope to Data Center only.** · *recommended:* yes — cookie auth is
   **removed on Cloud** (since 2019-06-03); only DC/Server shares the web
   session with REST. · *why:* shipping a Cloud cookie path would be dead on
   arrival. · *decide-by:* at acceptance; **default if no objection: DC-only.**
2. **One-broker-per-skill erratum.** · *recommended:* allow a single skill to
   declare `auth: sso-cookie` **with a `creds` fallback** via a narrow erratum
   to RFC-0013 § 2's "every credentialed skill picks exactly one." · *why:* one
   `jira` skill must serve both token users and DC-SSO users. · *decide-by:* at
   acceptance; **default: erratum (Option A below).**
3. **Read-only first; writes deferred.** · *recommended:* ship search/get/
   export over cookies now; defer create/update/transition/comment/attachment
   until XSRF-token handling is designed. · *why:* DC mutating requests need an
   `atlassian.xsrf.token` header echo that RFC-0013 deferred (cookies only).
   · *decide-by:* at acceptance; **default: read-only.**
4. **Enterprise config pre-baked into a pack customization.** · *recommended:*
   ship `references/sso-config.toml` (placeholder-shaped) per SSO-capable skill;
   an enterprise **pre-bakes** its instance config into a customized pack — the
   **default sign-in method** (`auth_default = "sso-cookie"`), the **flavor**
   (`server` = Data Center), and the **instance URL** — so developers install
   it already pointed at the corporate instance over SSO, no per-developer
   edit. · *why:* gives the SSO profile a version-controlled, customization-time
   source distinct from machine-local runtime cookie state. · *decide-by:* at
   acceptance; **default: ship the reference file, SSO-default is enterprise
   opt-in (upstream default stays `creds`).**
5. **Skill rollout order.** · *recommended:* `jira` (read) → `confluence-crawler`;
   defer `confluence-publisher` (writes) and `jira-align` (Cloud-SaaS-likely).
   · *decide-by:* at acceptance; **default: jira-first.**

## Problem & goals

**Diagnosis.** An Atlassian **Data Center** instance fronted by corporate SSO
(SAML/OIDC via an IdP) can be configured to refuse personal access tokens.
The atlassian pack's four skills resolve credentials exclusively through the
`creds` broker and present a token in a `Basic` or `Bearer` `Authorization`
header (`packs/atlassian/.apm/skills/*/scripts/_client.py`). With tokens
blocked, every operation fails at the auth boundary, and the pack is unusable
on exactly the enterprise deployments it targets.

RFC-0013 anticipated this — it built the `sso-cookie` broker for "Atlassian
Data Center products (Jira / Confluence / Jira Align / Bitbucket DC)" — but
its § 9 deferred connecting the in-tree skills to it, for two reasons: (a)
"the SSO path is a frontmatter change adopters make in their deployment," and
(b) "the repo has no corporate-SSO test deployment to validate against."
Reason (a) is **false** (the clients have no cookie path and the
`auth: sso-cookie` lint would reject a frontmatter-only flip — see Evidence);
reason (b) is **now resolvable** because a real DC instance is available for
the validation transcript.

**Goals.**
- A user on an SSO-only **DC** instance can run read operations (`jira`
  search/get/export; `confluence-crawler`) authenticated by the captured SSO
  session, with no personal access token.
- A single skill serves both token users and DC-SSO users; the auth path is
  selected without forking the skill.
- Enterprise SSO parameters (login URL, success pattern, cookie domains,
  validation endpoint) are declared in a **version-controlled, adopter-editable
  reference file** in the skill, decoupled from machine-local cookie state.
- The RFC-0013 four-broker security contract (argv ban, never-logged,
  path-not-value output, corporate-proxy/trust-store passthrough) is preserved.

**Non-goals.**
- **Atlassian Cloud.** Cookie auth is removed there; Cloud-SSO-with-tokens-
  blocked is an OAuth 2.0 (3LO) problem — a different broker RFC-0013 deferred
  separately (`sso-pat-mint`/OAuth). Out of scope here.
- **Write/mutating operations in v1.** Deferred pending XSRF design (Decision 3).
- **jira-align.** Deferred on rollout-sequencing grounds — it is write-capable
  and on a distinct API/auth shape — **not** because it is Cloud-only (its
  client supports self-hosted installs). Revisit after the read-first jira /
  confluence-crawler path is validated.
- **A new broker.** This RFC consumes the existing `sso-cookie` broker
  unchanged; it does not redesign credential brokering.
- **DOM-scraping of CSRF/XSRF tokens.** RFC-0013 deferred it; this RFC inherits
  that boundary (and is why writes are a non-goal).

## Proposal

### 1. Read-path cookie auth in the atlassian clients (Decision 1, 3)

Each SSO-capable skill's `_client.py` gains a cookie-auth path, selected when
the skill resolves `auth: sso-cookie` (Decision 2). Today these clients import
`from credbroker import load_credentials` (the standalone resolver at
`packs/credential-brokers/.apm/user-libs/credbroker/`, which superseded
RFC-0013's `credentials_shim` distribution model) and build a `Basic`/`Bearer`
`Authorization` header. The new path:

1. Resolves the broker at `Path.home() / ".agentbundle" / "bin" /
   "sso-broker.py"` (the canonical resolution RFC-0013 § 4b pins), failing
   with the install-the-pack remediation message if absent.
2. Calls `sso-broker get-cookies <profile>` (subprocess, `env={**os.environ}`
   per RFC-0013 § 1). The broker prints a **path** to the on-disk cookie jar.
   Note the real data-at-rest model (verified against `sso-broker.py`
   `_do_get_cookies`): `get-cookies` *materialises the cookie values in
   cleartext* to a `0600` file under `~/.agentbundle/sso-cookies/<profile>.jar`
   and prints that path. The keychain is the storage-at-rest tier; the
   path-not-value handoff keeps values off **argv and stdout**, not off disk.
   The client must treat the jar path's *contents* as sensitive (never logged,
   never surfaced to the LLM) — an AC the spec carries.
3. Loads the jar in-process and attaches it to the `httpx.AsyncClient` as a
   cookie jar (DC session needs `JSESSIONID`, `crowd.token_key`, and
   `atlassian.xsrf.token` together), with **no `Authorization` header**. The
   cookie-path `httpx.AsyncClient` must be wired to honour `HTTPS_PROXY` /
   `NO_PROXY` and `REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE` / `SSL_CERT_DIR`
   explicitly — httpx does **not** read these from the environment by default
   (unlike urllib), so RFC-0013 § 1's corporate-network obligation is only met
   if the client opts in. Spec AC.
4. On a 401 from a read call, the **consuming client** (which observes the
   401 — the broker makes no request) re-invokes `sso-broker test`/`register`;
   the broker owns the re-auth browser flow. The client does not silently
   retry into a browser flow itself.

Only read verbs are enabled on the cookie path in v1, enforced **structurally
by a GET/HEAD method allowlist at the `_request` chokepoint** — not by
blocklisting named mutating methods. This is load-bearing: the jira client
exposes a `raw(method, path, …)` escape hatch that accepts any verb, so a
per-method blocklist would let `raw("POST", …)` walk to the wire on the cookie
session and 403 on the XSRF check (or worse, succeed). A chokepoint allowlist
covers `raw` and any future method by construction. Mutating calls on the
cookie path raise "writes over SSO-cookie auth are not supported yet
(RFC-0035 v1); use a personal access token, or wait for the XSRF follow-on."

### 2. One-broker-with-fallback erratum (Decision 2)

RFC-0013 § 2 states "every credentialed skill picks exactly one" broker. A
`jira` skill on a mixed estate (some users on tokens, some on SSO-only DC)
needs both. This RFC adds a **narrow erratum**: a skill MAY declare
`auth: sso-cookie` together with a `creds` fallback, resolved at runtime by a
single, explicit rule:

The single selector is the config's **`auth_default`** key (§ 3) — which sign-in
method the skill reaches for first; the other is the fallback:

- If the skill's SSO reference config (§ 3) is **absent or
  `auth_default = "creds"`** → use the existing `creds` (token) path, unchanged.
  This is the upstream default.
- If `auth_default = "sso-cookie"` **and** a registered profile exists → use
  the cookie path. `creds` is the fallback only when no SSO config selected it.
- If `auth_default = "sso-cookie"` **but the broker or profile is
  unavailable** → **fail closed** with the re-`register` remediation. The
  fail-closed branch must key on the full failure surface, not just one exit
  code: **only `get-cookies` exit 0 with a readable jar path proceeds** on the
  cookie path; any non-zero exit (the broker returns 2 for both
  "not registered" and "no jar"), a broker-absent resolution failure, or an
  uncaught exception (e.g. a keychain hard-fail inside the broker) all fail
  closed. The client must **not** silently fall through to `creds` here: the
  enterprise has declared SSO the default sign-in method, and a silent
  downgrade either fails confusingly at the server or succeeds with a
  stale/over-privileged token the user believed retired. Spec AC.

`auth_default` is the **one** switch (no separate `enabled` flag — that would
be a redundant second source of truth); today's token users have no SSO config
and resolve to `creds` byte-for-byte as before, and the only ambiguous case
(SSO-default but unavailable) is fail-closed rather than downgraded.

The erratum is recorded in RFC-0013 (§ Errata, Approver-signed) per the
governance-erratum convention — and drafted verbatim here so the Approver
signs the exact loosening, not a forward-reference:

> **RFC-0013 § Errata (proposed by RFC-0035).** § 2's rule "Every credentialed
> skill picks exactly one [broker]" is narrowed: a skill MAY declare
> `auth: sso-cookie` together with a `creds` fallback, resolved at runtime by a
> single explicit rule keyed on `auth_default` (absent or `creds` → `creds`;
> `sso-cookie` + registered → cookie; `sso-cookie` + unavailable → fail
> closed). No other broker
> combination is permitted; the one-broker rule stands for every other pairing.

### 3. `references/sso-config.toml` — the adopter-editable enterprise seam (Decision 4)

Each SSO-capable skill ships a new reference file alongside its existing
`references/creds-schema.toml`. It declares the DC SSO profile the broker's
`register`/`get-cookies` operate on:

Alongside the SSO connection fields, the file carries three **new** keys that
let an enterprise **pre-bake** the deployment defaults into its pack
customization — the **default sign-in method**, the **flavor**, and the
**instance URL** — so a developer who installs the customized pack is pointed
at the corporate Data Center instance over SSO out of the box, with no
per-developer config edit:

```toml
# references/sso-config.toml — atlassian jira.
# UPSTREAM ships this placeholder-shaped (auth_default = "creds", *.invalid
# hosts, no real data). An ENTERPRISE pre-bakes its real values into its pack
# customization (see § 3a); the developer then just runs
# `sso-broker register <profile>` once. Cookie VALUES never live here —
# only connection parameters.

[sso]
auth_default = "sso-cookie"      # the DEFAULT sign-in method (the one switch);
                                 #   "creds" = token default (the upstream value)
flavor = "server"                # "server" = Data Center / on-prem (vs "cloud");
                                 #   pinned here, not auto-detected from the URL
base_url = "https://jira.example-corp.invalid"   # enterprise: the real DC REST base URL
profile = "atlassian-dc"         # maps to sso_profile
login_url = "https://jira.example-corp.invalid"
success_url_pattern = "https://jira.example-corp.invalid/secure/.*"
cookie_domains = ["jira.example-corp.invalid", "sso.example-corp.invalid"]
validation_endpoint = "/rest/api/2/myself"
session_filename = "atlassian-dc.jar"
```

The three new baked keys (the SSO connection fields — `login_url`,
`success_url_pattern`, `cookie_domains`, `validation_endpoint`,
`session_filename` — are pre-baked too; these three are what these edits add):
- **`auth_default`** — the skill's default sign-in method. An enterprise on
  SSO-only DC sets it to `sso-cookie`, so SSO is what the skill reaches for
  first (this is the answer to "set the default sign-in method"); `creds`
  (token) is then the fallback per § 2. Upstream default is `creds`.
- **`flavor = "server"`** — pins Data Center / Server explicitly rather than
  inferring from the host, so a DC instance behind a vanity hostname is not
  mis-detected as Cloud (and Cloud is refused on the SSO path — cookie auth is
  Cloud-dead).
- **`base_url`** — the instance REST base URL, baked once so the developer
  supplies no `JIRA_BASE_URL`. On the SSO path this supersedes the `creds`
  schema's `BASE_URL` env var.

- **Upstream ships placeholders** (`*.invalid` hosts, `auth_default = "creds"`)
  carrying no real deployment data. This file lives under `references/`, not
  `seeds/`, so the `lint-seeds` placeholder rules do **not** cover it — so the
  discipline needs its own gate. **Spec AC:** a lint asserts the
  upstream-shipped `sso-config.toml` carries only `*.invalid` hosts and
  `auth_default = "creds"` (the SSO default is an enterprise opt-in, never the
  upstream default), and that no cookie value lands in the file. **This lint
  must be a structural TOML-key check, not a substring scan** — parse the TOML
  and assert the key set is a subset of the declared connection-param schema,
  rejecting any unknown key or any value matching a cookie-value shape. A naive
  `grep` for `token`/`session` false-positives on the legitimate
  `crowd.token_key` cookie *name*, `session_filename`, and
  `success_url_pattern` — the AC26(c) substring trap this repo has already been
  bitten by.
- **Enterprises pre-bake it into a pack customization** — they set
  `auth_default`, `flavor`, `base_url`, and the SSO connection fields once and
  ship the customized pack so developers install it already pointed at the
  corporate instance (§ 3a). This is the "modify the pack when deployed
  downstream for enterprise" seam the design calls for, and it slots into the
  existing adapt-to-project substitution class. `cookie_domains`, `login_url`,
  `base_url`, and `validation_endpoint` are **operator-trusted configuration**:
  the customization's reviewer owns
  validating those edited values, named explicitly because they drive a real
  browser navigation and outbound requests (see the input-validation ACs
  below).
- **Input-validation ACs (these fields feed a browser + outbound requests —
  an SSRF/over-capture surface).** The broker's only scheme guard today is
  `test`'s http(s) check (which the broker leaves http-permissive); there is
  no host allowlist or cookie-domain confinement. The shipped broker is
  consumed unchanged (§ Non-goals), so these are **new config-validation-layer
  ACs** above it, not broker behaviour today. The spec must require: (a)
  `login_url` and `success_url_pattern` are **https-only** (scheme allowlist,
  reject anything else — stricter than the broker's http-permissive guard);
  (b) `validation_endpoint` is a **root-relative path** (leading `/`, no
  scheme, no host, no protocol-relative `//`) resolved against the declared
  instance base, so the cookie-bearing `test` request cannot be steered
  off-host; (c) captured and sent cookies are **constrained to the explicitly
  declared `cookie_domains`** — never the broker's "derive domains from every
  observed cookie" fallback when the config declares them, so the jar is not an
  over-broad capture of the whole SSO redirect chain (analytics / IdP / third-
  party cookies); (d) `register` persists only cookies whose domain is in the
  declared set; (e) the consumer client's **request base host must itself be a
  member of `cookie_domains`** (fail-closed on mismatch), closing the loop
  between capture-confinement and send-confinement when a downstream edit drifts
  the skill base URL from the SSO config.
- **Relationship to the runtime profile.** RFC-0013's
  `~/.agentbundle/sso-profiles/<profile>.toml` is written by `register` from
  browser observation and "never hand-edited." `sso-config.toml` is the
  **declarative, version-controlled** counterpart. The *proposed* binding
  (pending Open Question 2) is that `register` seeds the runtime profile from
  it, so locked-down enterprise browsers and repeatable deployments don't
  depend on free-form observation. The client reads `sso-config.toml` only for
  `[sso].auth_default`, `flavor`, `base_url`, `profile`, and `cookie_domains`
  (the last for the AC(e) send-host membership check). **No cookie values are stored in this file or
  the runtime profile TOML** — the cookie jar lives in the OS keychain at rest
  and is materialised in cleartext to the `0600`
  `~/.agentbundle/sso-cookies/<profile>.jar` file (which **persists between
  calls** until `rm`/refresh — not a transient temp file; see § 1 step 2 and
  the pre-mortem); the connection config and the secret material are kept in
  separate artifacts.

#### 3a. How config works on a corporate deployment (end-to-end)

The model is **pre-baking**: the enterprise sets the instance config once at
pack-customization time and the customized pack is the unit developers install.
Configuration splits into **two planes** so the pre-baked config is shared and
secret-free, while every secret stays per-user and per-machine:

| Plane | Artifact | Who authors it | Where it lives | Shared or per-user | In version control? |
| --- | --- | --- | --- | --- | --- |
| **Connection config** (incl. `auth_default`, `flavor`, `base_url`) | `references/sso-config.toml`, **pre-baked into the enterprise pack customization** | A platform owner, once per instance | Inside the org's customized pack | **Shared** across the org (instance config, not a secret) | **Yes** — committed in the customization |
| **Secret material** | the cookie jar | Each developer, via `register` | OS keychain + `0600` floor file on *their own* machine | **Per-user, per-machine** | **Never** — not committed, not shared |

The lifecycle on a corporate Data Center deployment:

1. **Pre-bake the instance config once.** A platform owner sets the three
   baked keys plus the SSO connection fields in `references/sso-config.toml` —
   `auth_default = "sso-cookie"` (SSO is the default sign-in method),
   `flavor = "server"` (Data Center), `base_url` / `login_url` /
   `success_url_pattern` / `cookie_domains` / `validation_endpoint` /
   `session_filename`. The edit is reviewed (the
   input-validation ACs above are the reviewer's checklist) and versioned, not
   a per-developer chore. Staging + production are two `profile` values (two
   files or a profiles table), so one estate can carry several instances.
2. **Ship it as a customized pack.** The org distributes the customized pack
   the way it ships any pack — a private fork, a vendored copy, or the
   **adapt-to-project substitution** layer (this file is exactly a class-1
   substitution / `.upstream` companion target). Because the pre-baked config
   is shared and secret-free, it travels through normal pack distribution with
   no special handling; the developer installs it already pointed at the
   corporate instance over SSO.
3. **Survive upstream upgrades.** When a later catalogue release touches the
   shipped placeholder `sso-config.toml`, the org's edited values must not be
   clobbered. The adapt-to-project **`.upstream` companion merge** (class-2) is
   the intended mechanism: the upgrade lands the new upstream version alongside,
   and the org reconciles, rather than the upgrade silently reverting the
   instance config. The spec carries this as the documented upgrade path.
4. **Each developer registers once.** On first use the developer runs
   `sso-broker register <profile>` on their own machine: a headed browser opens
   the corporate `login_url`, they complete SSO (including any MFA/IdP step the
   org enforces), and the broker captures the session cookies for the declared
   `cookie_domains` into *their own* keychain. Nothing here is shared or
   committed; the shared config told the broker **where** to go, the developer's
   own session provides **who** they are.
5. **The skills just work.** With `auth_default = "sso-cookie"` and a
   registered profile, the client resolves the cookie path automatically
   (§ 1); with no config it falls back to `creds` (token), and a developer who
   hasn't registered yet on an SSO-default pack is failed closed with the
   `register` remediation (§ 2).
6. **Re-auth is per-user.** On TTL expiry or a 401, the developer re-runs
   `register` (or `refresh`); the shared config is untouched.

This keeps the corporate-network obligations of RFC-0013 § 1 intact end to end:
the headed browser and the consumer client both inherit `HTTPS_PROXY` /
`NO_PROXY` and the system trust store (§ 1 step 3 makes the httpx wiring an AC,
since httpx does not honour those env vars by default), so the flow works behind
a corporate proxy with an internal CA.

### 4. Validation & status (Decision against RFC-0013 § 9 reason (b))

The RFC ships **Experimental** until one real manual-QA transcript against a
Data Center instance lands (read flow: `register` → `get-cookies` →
authenticated `jira` search returns results; `test` returns 0). That transcript
fills the `sso-cookie × <os>` row already pending in `docs/backlog.md` (a
bullet under the `## credential-broker-contract` heading today; the spec must
add a resolvable `###` backlog anchor for its deferred-AC marker, with the
`(deferred: <anchor>)` marker on the AC checkbox line itself per the
deferred-marker convention). Mock-
level tests (broker invocation shape, cookie-jar attachment, no-`Authorization`-
header assertion, writes-refused error) gate in CI; the live transcript gates
the move from Experimental to Accepted.

## Options considered

**Axis: where the dual (token + SSO) auth decision lives**, since the contract
pins one broker per skill and we must serve both populations. These four
exhaust it — the choice is made in frontmatter (one or two skills), at runtime
(inside one skill), or not at all.

| Option | Shape | Trade-offs |
| --- | --- | --- |
| **A. One skill, `sso-cookie` + `creds` fallback (erratum)** ⭐ | Single `jira` skill; runtime rule picks cookie or token (§ 2). | Needs a narrow RFC-0013 erratum; keeps one skill, one doc surface, zero change for token users. Prior art: the kiro-alias-parity in-place contract erratum. |
| **B. Separate `jira` + `jira-sso` skills** | Duplicate skill, one per broker. | Contract-clean (each picks one broker) but doubles SKILL.md / client / docs / tests; drift risk between the twins. Prior art: none in-repo favours twinning credentialed skills. |
| **C. Do nothing** | Keep `auth: creds`; adopters fork the client downstream. | Zero upstream work; but the gap is real and recurring (RFC-0013 § Motivation documented a downstream consumer already carrying hand-rolled `browser_auth.py`). Cost of delay: every SSO-only DC adopter re-solves it, exactly the duplication RFC-0013 set out to kill. |
| **D. Always-cookie (drop token path)** | Replace `creds` with `sso-cookie`. | Simplest code, but breaks every existing token user and contradicts RFC-0013's DC-only scope (Cloud users have no cookie path at all). Rejected. |

Recommended: **A**. It is the only option that serves both populations with a
single maintained skill and no regression for today's users, at the cost of
one auditable erratum.

## Risks & what would make this wrong

**Pre-mortem.**
- *Writes look supported and 403 in the field.* Mitigation: mutating verbs
  hard-refuse on the cookie path with an explicit message; they never reach the
  wire.
- *Cookie-jar attachment leaks into logs.* Mitigation: the broker emits a path
  not values; the client loads the jar in-process and the never-logged
  invariant (RFC-0013 § 1) applies; a test asserts no cookie value is logged.
- *Enterprise edits the reference file but forgets `register`.* Mitigation:
  `get-cookies` exits non-zero with the `register` remediation; the client
  surfaces it verbatim.
- *Mid-session cookie rotation (IdP rotates `JSESSIONID`).* Mitigation: 401 →
  broker re-`register` per RFC-0013 § 4b; the client does not silently retry.
- *A typo'd or malicious `login_url`/`cookie_domains` in the downstream config
  redirects the headed browser through an attacker domain and captures its
  cookies.* Mitigation: https-only scheme guard + capture confined to declared
  `cookie_domains` (§ 3 ACs); downstream-fork reviewer owns the edited values.
- *SSO-default-but-unavailable silently downgrades to a stale token.*
  Mitigation: fail-closed rule (§ 2).
- *Cleartext cookie jar at rest is read by another local process.* The jar is
  `0600` under `~/.agentbundle/sso-cookies/`; this matches RFC-0013's existing
  file-floor model and is not worsened here, but it is a real at-rest exposure
  the RFC names honestly rather than claiming keychain-only confinement.

**Key assumptions (falsifiable).**
- *DC REST accepts the captured session cookies for read endpoints.* Falsifiable
  by the validation transcript; if a DC instance needs an XSRF header even on
  GETs, read-only scope shrinks further.
- *The three cookies (`JSESSIONID` + `crowd.token_key` + `atlassian.xsrf.token`)
  are within the broker's declared `cookie_domains`.* If the IdP sets the
  session cookie on a domain the broker doesn't capture, `register` must widen
  `cookie_domains` — an edit to `sso-config.toml`, not code.
- *Token users are unaffected.* Falsifiable: with `auth_default = "creds"` (the
  upstream default) or no SSO config, the resolved path is byte-identical to
  today's `creds`.

**Drawbacks.** Adds a second auth path per SSO-capable client (more surface to
test and maintain). Introduces a contract erratum (one-broker rule loosened).
Requires Playwright on the user's machine for `register` (RFC-0013's existing
dependency, surfaced on first use). The reference-config file is one more
adopter-edit point that can drift from the real instance.

## Evidence & prior art

**Spike / de-risk result.** The riskiest assumption was RFC-0013 § 9's claim
that enabling SSO is "a frontmatter change adopters make in their deployment."
**Falsified by code inspection:** all four `_client.py` files authenticate
solely by building `Basic`/`Bearer` `Authorization` headers from
`load_credentials` (the `creds` broker); none invoke `sso-broker` or load a
cookie jar. Further, RFC-0013 § 6 requires an `auth: sso-cookie` skill's
`scripts/` to subprocess-invoke `sso-broker.py` — so flipping only the
frontmatter would **fail the credentialed-skill lint and still not
authenticate**. Conclusion: this needs a client code change, which is what
justifies an RFC rather than a doc note.

**Repo precedent.**
- `docs/rfc/0013-credential-broker-contract.md` — § 2 defines `sso-cookie` and
  names Atlassian DC as the use case; § 4b pins broker path/verbs/profile
  schema; § 9 records the deferral this RFC reverses; § scope-boundary defers
  XSRF/DOM scraping (the basis for read-only-first).
- `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py` — broker
  fully implemented (register / get-cookies / test / refresh / list-profiles /
  rm), projected to `~/.agentbundle/bin/`.
- `docs/backlog.md` — the `sso-cookie × {macOS,Windows,Linux}` manual-QA rows
  are open; this RFC's transcript closes the relevant one.
- `packs/atlassian/.apm/skills/*/references/creds-schema.toml` — the existing
  per-skill reference-file precedent `sso-config.toml` parallels.

**External prior art.**
- [Atlassian — Cookie-based auth deprecation notice](https://developer.atlassian.com/cloud/jira/platform/deprecation-notice-basic-auth-and-cookie-based-auth/)
  — Jira **Cloud** cookie auth progressively disabled from 2019-06-03; use API
  tokens / OAuth. Confirms the DC-only scope (fetched, claim confirmed).
- [Atlassian community — cookie auth for Crowd + Jira + SSO](https://community.atlassian.com/forums/Crowd-questions/How-to-perform-cookie-based-authentication-in-crowd-Jira-SSO/qaq-p/990663)
  — DC cookie auth requires `crowd.token_key`, `JSESSIONID`, and
  `atlassian.xsrf.token` together on subsequent requests.
- [Atlassian support — XSRF token missing on Data Center](https://support.atlassian.com/jira/kb/xsrf-security-token-missing-or-session-expiring-in-jira-data-center/)
  — DC enforces an XSRF check on mutating requests, grounding the write
  deferral.

## Experiment / validation

- **Hypothesis.** A `register`-captured SSO session against a DC instance
  authenticates read REST calls (`/rest/api/2/myself`, JQL search) with no API
  token.
- **What we measure.** `sso-broker test <profile>` exit code; HTTP status and
  result count from an authenticated `jira` search; presence of the three
  session cookies in the jar; absence of any `Authorization` header on the wire.
- **Success / failure criteria.** Success: `test` → 0, search → 200 with
  results. Failure: read calls 401/403 even with a valid session (would force
  the XSRF-on-reads finding and shrink scope).

Results captured in `docs/specs/atlassian-sso-cookie/notes/` (linked spike note), not
pasted here; status stays **Experimental** until the transcript lands.

## Open questions

1. **Does DC read REST need an XSRF header even on GETs in some IdP configs?**
   · *recommended default:* assume not (read-only path ships without XSRF
   header); the validation transcript confirms. · *owner:* eugenelim · *decide-by:*
   validation.
2. **Does `register` seed the runtime profile from `sso-config.toml`, or does
   the client pass parameters to the broker per call?** · *recommended default:*
   `register` seeds from the file (keeps the broker's "profile is the unit of
   config" model intact). · *owner:* eugenelim + implementer · *decide-by:* spec.
3. **Is `confluence-crawler` in v1 or a fast-follow?** · *recommended default:*
   v1 alongside `jira` (both read-only; shared client shape). · *owner:* eugenelim
   · *decide-by:* spec.

## Follow-on artifacts

- ✅ **RFC-0013 § Errata entry** (Approver-signed, 2026-06-16) recording the
  one-broker-with-`creds`-fallback loosening (Decision 2) — landed in this PR.
- ADR: record the DC-only-and-read-only scoping decision if it proves
  load-bearing for future broker work.
- Spec: `docs/specs/atlassian-sso-cookie/` — client cookie path, reference-file
  schema, lint coverage, mock tests, and the live-DC manual-QA transcript.
- Possible `add-credentialed-skill` template update if `sso-config.toml`
  becomes a standard companion for `auth: sso-cookie` skills.

## Errata

This RFC is Accepted: the body above is preserved as the original decision
record. Corrections found while building it are appended here, Approver-signed.

- **2026-06-16 (Approver: eugenelim) — § 1 step 3's premise that `httpx` ignores
  proxy / CA environment variables by default is imprecise.** § 1 step 3 asserts
  the cookie-path client must opt in because "httpx does **not** read these from
  the environment by default (unlike urllib)." Probing the pinned client
  (`httpx` 0.28.1) shows `trust_env` defaults to **True**, so httpx already honors
  `HTTP(S)_PROXY` / `NO_PROXY` and `SSL_CERT_FILE` / `SSL_CERT_DIR`. The real gaps
  are narrower: httpx does **not** read `REQUESTS_CA_BUNDLE` (a requests-only
  variable), and the existing client passes `verify=<bool>`, which can override
  the trust-store context. The **requirement** stands unchanged — the cookie-path
  client must honor the corporate proxy and system trust store — but the spec's
  acceptance criterion (`atlassian-sso-cookie` AC8) is written against actual
  httpx behavior: keep `trust_env=True`, build an explicit SSL context honoring
  `SSL_CERT_FILE`/`SSL_CERT_DIR` and mapping `REQUESTS_CA_BUNDLE`, and avoid a bare
  `verify=True` that would clobber the trust store. Recorded in
  `docs/specs/atlassian-sso-cookie/spec.md` (Assumptions + AC8).

- **2026-06-16 (Approver: eugenelim) — § 1's cookie-resolution logic is placed in
  the `credbroker` library, not in each client.** § 1 illustrated the resolution
  steps (resolve broker → `get-cookies` → load jar) living in each `_client.py`.
  Because RFC-0023 retired in-pack shared-module projection and `credbroker` is
  the single consumer-resolution home every credentialed skill already imports,
  the spec places the resolver + the validation/confinement primitives in
  `credbroker` (platform-agnostic, reusable by any integration). The broker engine
  stays unchanged, preserving this RFC's non-goal. Recorded in
  [ADR-0026](../adr/0026-sso-consumer-resolution-in-credbroker.md) and a second
  [RFC-0013 § Errata](0013-credential-broker-contract.md#errata) entry.

- **2026-06-16 (Approver: eugenelim) — § 3's `register`-time capture-confinement
  is relocated to the consumer at load time.** § 3 AC(d) reads as though
  `register` persists only cookies in the declared `cookie_domains`. The shipped
  `sso-broker.py` (consumed unchanged) persists **every** observed cookie;
  `--cookie-domain` only writes the profile-TOML metadata, it never filters the
  jar. Capture-confinement therefore happens in the consumer: it filters the
  loaded jar to `cookie_domains` at load time, before attaching it
  (`atlassian-sso-cookie` AC4/AC5). The over-broad jar at rest is the broker's
  existing behavior, named honestly rather than claimed away.
