# `credbroker` SSO API

The consumer surface for `auth: sso-cookie` skills. A consumer never resolves the
broker path, builds its argv, or calls `subprocess` — it calls these.

Import from the top-level package:

```python
import credbroker
```

The library subprocess-invokes the `sso-broker.py` **engine**; the engine never
imports the library. Anything both need — the profile grammar below — is
duplicated deliberately and pinned equal by test.

## Functions

### `validate_sso_profile(profile) -> None`

Fail closed unless `profile` is safe to interpolate into a filesystem path and a
keychain entry name: `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$` under `re.fullmatch`,
excluding Windows reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`,
`LPT1`–`LPT9`) with or without an extension.

`re.fullmatch`, not `re.match`: the pattern's `$` matches before a trailing
newline, so `match` would admit `"jira\n"`.

Raises `SsoConfigError`, including for a non-`str` — never `TypeError`, which
would escape a consumer's credential exit band.

### `load_sso_cookies(profile) -> Path`

Resolve a captured session to an on-disk cookie-jar **path**. Never bytes: no
cookie value crosses argv, and no cookie value is logged.

Bounded at 30 s and run with an explicitly composed environment. Raises
`SsoSessionUnavailableError` only when the engine reports no usable session;
every other failure raises `SsoBrokerUnavailableError`.

### `refresh_sso_session(profile) -> None`

Re-establish an expired session **without a human**.

Takes only a profile. That signature *is* the control: the function is
structurally incapable of forwarding a sign-in destination, so no automated
caller can choose where the browser goes. The engine reads the destination from
the stored profile, which only a completed, operator-authorised registration
writes.

The engine's `refresh` is **headless**. It waits a bounded window for a warm
session's redirect chain to land unaided, and otherwise fails fast rather than
putting a login page in front of whoever is at the machine.

### `register_sso_session(profile, *, login_url, success_url_pattern, cookie_domains, validation_endpoint, session_filename=None, ttl_hint_minutes=None) -> None`

First capture, at the supplied destination. The **only** function that accepts
one — reach it from an operator-typed action, never automatically.

Captures in a throwaway browser context and seeds the standing profile from it.
Only connection parameters cross argv; no cookie value, cookie name, jar path or
`Cookie:`-header shape appears in what it composes.

### `derive_sso_destination(base_url, *, strategies=()) -> str | None`

Ask the resource server where it sends users to sign in. Returns the first
**origin** a chain resolves — RFC 9728 protected resource metadata, then OIDC
discovery / RFC 8414, then any *named* vendor probe the caller opted into
(`"atlassian-seraph"` today) — or `None`.

The origin is `scheme://host:port` with the port **always explicit** and an
IPv6 host bracketed: `https://idp.example:443`, not `https://idp.example`.
Normalise your own configured destination the same way before comparing — a
server is free to spell the default port either way, and comparing raw strings
refuses a destination that is in fact correct.

`None` is a real outcome, not an unhandled failure: SAML-only SPs expose no
discovery at all. A consumer that cannot derive must **refuse**, never fall back
to the configured value.

Bounded, because it is an outbound fetch on the credential path whose targets
are partly attacker-influenceable: https-only at every hop, redirects not
followed, a 5 s socket timeout under a 15 s total budget, a 64 KiB body cap
before parsing, strict TLS that no `--insecure`-style flag reaches, and no
`Authorization` / `Cookie` / proxy-auth header on any request.

**And an address bound.** Any hop whose origin is not `base_url`'s is refused
when its host resolves to loopback, link-local (where cloud instance metadata
lives), unique-local, RFC 1918, reserved, multicast or unspecified — otherwise a
compromised resource server could point the first probe's `resource_metadata`
at an internal service and have the operator's machine fetch it. The exemption
is keyed to the *origin*, not to the first request, because RFC 9728 puts the
metadata document on the resource server itself; an internally-hosted instance
must still be able to complete tier 1. A resolver failure is refused, not
allowed — a configured proxy resolves names local DNS cannot. It does not close
DNS rebinding, which would need a pinned-address connection.

**Defence in depth, not a control.** The derivation target lives in the same
adopter- and agent-writable config file as the value being attested, so one
write moves both.

## Exceptions

All derive from `SsoError`.

| Exception | Raised for | May a consumer recover? |
|---|---|---|
| `SsoSessionUnavailableError` | no usable session (engine exit 2) | **yes** |
| `SsoProfileNotRegisteredError` | `refresh` found no profile (exit 4); subclasses the row above | **yes** |
| `SsoInteractionRequiredError` | headless `refresh` needs a human (exit 5) | no |
| `SsoRecaptureFailedError` | `refresh` / `register` engine failure (exit 3 or unknown) | no |
| `SsoBrokerUnavailableError` | timeout, spawn failure, materialisation write failure | no |
| `SsoBrokerNotInstalledError` | the engine is absent | no |
| `SsoConfigError` | a config value or profile violates the confinement contract | no |

**Only the two recoverable rows may trigger a recapture.** A timeout is not an
expired session: mapping it to the recoverable type would open a browser
whenever a keychain was slow. `SsoProfileNotRegisteredError` subclasses
`SsoSessionUnavailableError` so handlers written before it existed keep working.

## Confinement primitives

Pure functions, shared so the control cannot drift between consumers:
`validate_https_url`, `validate_root_relative_endpoint`,
`domain_in_cookie_domains`, `filter_jar_to_domains`,
`require_host_in_cookie_domains`.

## Version floor

The recapture verbs land in `credbroker` **0.5.0**. Pin `credbroker>=0.5.0` in
your skill's `requirements.txt`: the pip layer precedes the vendored user-scope
floor on `sys.path`, so an older pinned install silently shadows the newer
vendored one. Feature-detect (`hasattr(credbroker, "refresh_sso_session")`) in
the branch that needs it, not in a shared bootstrap.

---

Architecture and threat model: [`docs/architecture/credentials.md`](../../../docs/architecture/credentials.md#the-sso-cookie-broker).
Authoring a new `auth: sso-cookie` skill: [add a credentialed skill](../how-to/add-a-credentialed-skill.md).
