# ADR-0026: SSO-cookie consumer resolution lives in the `credbroker` library, platform-agnostic

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-16
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0035](../rfc/0035-sso-cookie-auth-for-atlassian-pack.md) (SSO-cookie auth for the atlassian pack — the proposal this resolution serves); [RFC-0013](../rfc/0013-credential-broker-contract.md) (the four-broker contract + § Errata recording this consumer-surface addition); [RFC-0023](../rfc/0023-credential-manager-broker.md) (made `credbroker` the pip-installable consumer-resolution library and retired in-pack shared-module projection); [ADR-0003](0003-credential-broker-contract.md) (broker contract); spec: [`docs/specs/atlassian-sso-cookie/`](../specs/atlassian-sso-cookie/spec.md).

## Context

RFC-0035 wires the atlassian `jira` (read paths) and `confluence-crawler` skills
to the already-shipped `sso-cookie` broker so they authenticate against Atlassian
Data Center instances behind corporate SSO. The broker engine
(`sso-broker.py`) — capture via headed Chromium, keychain/file-floor storage, the
`get-cookies` path-not-value handoff — is fully implemented and consumed
**unchanged** (RFC-0035 non-goal).

The missing piece is the **consumer side**: the logic that locates the broker,
runs `get-cookies <profile>`, reads the jar path, confines the jar to the declared
cookie domains, and hands a cookie-attached HTTP client to the skill. Today no
such consumer resolver exists anywhere — every would-be consumer (atlassian now,
any future integration later) would hand-roll it.

Forces constraining where this logic lives:

- **`credbroker` is already the single consumer-resolution home in use.** All six
  shipped credentialed skills are `auth: creds` and resolve tokens through
  `credbroker.load_credentials` — the in-process resolver library RFC-0023 made
  canonical. The library resolves the `creds` family but has no SSO surface.
- **RFC-0023 retired in-pack shared-module projection.** The build no longer
  byte-copies `shared-libs/*.py` into skill `scripts/`; the only surviving
  cross-skill code-sharing mechanism is the pip-installable `credbroker` library.
  A shared client-side helper therefore has no other single-source home.
- **The cookie-resolution + validation logic is a security control surface.** It
  performs the https-only scheme guard, root-relative endpoint check, and
  cookie-domain capture/send confinement the unchanged broker does not. Duplicating
  it across two clients risks the two copies drifting — a security-relevant drift.
- **RFC-0035's non-goal forbids redesigning the broker.** Whatever home is chosen
  must leave `sso-broker.py` and the four-broker contract untouched.
- **The capability is inherently reusable.** SSO-only Data Center is not an
  atlassian-specific problem; figma and future integrations will hit it. The
  owner wants the capability available platform-wide, not atlassian-local.

## Decision

> SSO-cookie **consumer resolution** is a second credential family in the
> `credbroker` resolver library — a platform-agnostic `load_sso_cookies(profile)`
> resolver plus reusable validation/confinement primitives that subprocess-invoke
> the **unchanged** `sso-broker.py` engine. It is **not** placed in the individual
> clients, and **not** a new user-lib.

Specifically:

- **In `credbroker`, parallel to `creds`.** `credbroker` gains
  `load_sso_cookies(profile)` (re-exported from `__all__`) alongside
  `load_credentials`, plus pure validation primitives (https-only scheme guard
  over `login_url`/`success_url_pattern`/`base_url`, root-relative
  `validation_endpoint`, cookie-domain membership) and a load-time
  `filter_jar_to_domains` confinement helper. The base import graph stays
  stdlib-only (Playwright stays in the broker engine). Version 0.1.1 → 0.2.0.
- **The broker engine is unchanged.** `credbroker` invokes `sso-broker.py
  get-cookies` via `subprocess.run` and treats the jar path's contents as secret.
  No change to the engine, its storage tiers, the argv ban, or the never-logged /
  path-not-value guarantees.
- **Capture-confinement is a consumer responsibility, done at load time.** The
  unchanged broker captures an over-broad jar (every observed cookie);
  `credbroker` filters the loaded jar to the declared `cookie_domains` before it
  is attached, so the cookies that leave the process are a subset of the declared
  domains.
- **The consumer owns its config schema.** The `references/sso-config.toml` shape
  and the `auth_default` selector are atlassian-specific and stay in the skills;
  `credbroker` owns only the generic resolver + primitives.
- **No new user-lib; no new top-level structure.** The capability rides the
  existing pip-installable library and its existing delivery rail.

## Consequences

**Positive.**

- One maintained, tested copy of the security control surface — no per-client
  drift of the confinement/validation logic.
- The capability is reusable by any future integration with no further structural
  work; the resolver library now covers the client side of both credential
  families that need a resolver (`creds` and `sso-cookie`; `env` reads itself,
  `cli` delegates to an external tool).
- RFC-0035's "broker unchanged" non-goal is preserved.
- `lint_credentialed_skills.py` extends naturally: a `credbroker` SSO-resolver
  import satisfies the broker-invocation requirement for an `auth: sso-cookie`
  skill, mirroring RFC-0023's `has_credbroker_import` acceptance for `creds`.

**Negative / costs.**

- Extends a contract-governed library's public surface — recorded as a second
  RFC-0013 § Errata so the contract breadcrumb is explicit. A minor version bump
  (0.1.1 → 0.2.0) may trip version-assertion tests in CI-ungated roots; the build
  PR runs the full `packages/agentbundle` suite by hand on the bump.
- `credbroker` now carries SSO-specific code, slightly widening its
  responsibility beyond pure token resolution. Mitigated by keeping the engine
  (capture/storage) out of it — `credbroker` only *resolves and confines*, it does
  not capture.

## Alternatives considered

- **A — Resolution logic in each client (RFC-0035 § 1's illustrative placement).**
  Rejected: duplicates the security control surface across two `_client.py` files
  with drift risk, and RFC-0023 removed the shared-module projection that would
  let one source feed both.
- **B — A new pip-installable user-lib in the atlassian pack (e.g. `atlassian_sso`).**
  Rejected: a sizable new structural + packaging + install-wiring surface RFC-0035
  never scoped, and the owner's explicit constraint was "no more user-libs."
- **C — Per-client duplication guarded by a byte-identical drift test.** Rejected:
  honors single-source intent only by enforcement, not by construction, and still
  spreads a security surface across two files; the resolver library is the natural
  home.
- **D — Add the resolver to the broker engine (`sso-broker.py`).** Rejected:
  conflates the capture/storage engine with consumer resolution and would breach
  RFC-0035's "broker unchanged" non-goal.
