# Credentials and trust boundaries

Credentialed primitives obtain secrets at runtime through `credbroker` and the
`sso-broker.py` engine, so secret bytes never reach argv, shell history, or an
agent transcript. The design stops accidental exposure and cross-user access at
rest. It does not stop a hostile process running as the same OS user, and a
human login page is never driven by an agent: first capture is an operator
action.[^c1]

## 1. Four brokers, one rule: the model never sees the value

A credentialed primitive declares exactly one broker in `SKILL.md`: `creds`,
`env`, `cli`, or `sso-cookie`. A fallback declaration needs both brokers'
security phrases.

| Broker | Resolves by | Consumer receives |
| --- | --- | --- |
| `creds` | First hit per required key across three storage tiers (§ 3) | A value, used only inside the primitive's own subprocess |
| `env` | An environment value already present | That value |
| `cli` | The vendor CLI's own login | Nothing; the CLI authenticates |
| `sso-cookie` | A stored browser session | A cookie-jar file path, never cookie bytes |

Three rules follow from that:

- Skills orchestrate credentialed primitives and never read credentials.
- No `get` verb or tool returns cleartext to the model. A primitive calls
  `credbroker.load_credentials` inside its own process and uses the value only
  in an outbound HTTP header.
- A `credentialed-cli` refuses value-shaped flags (`--token`, `--api-key`,
  `--bearer`, `--pat`, `--password`). An MCP server may accept header-naming
  flags, never value-shaped ones.

`credential-setup` prompts with `getpass` or `input` from
`references/creds-schema.toml`, writes the highest available tier, and reports
the tier on stderr.[^c2]

## 2. Dependency edges run one way

`credbroker` subprocesses `sso-broker.py` and imports no engine code; the
engine never imports `credbroker`. Consumers call the library and never build
broker argv themselves. The public consumer API is `load_credentials`,
`load_sso_cookies`, `refresh_sso_session`, and `register_sso_session`.

`agentbundle` depends on `credbroker`, never the reverse.
`agentbundle.catalogue_fetch.open_fetch_session` calls
`credbroker.resolve_http_access(url, env=env)` for `catalogue+https://` and
`archive+https://` sources. The resolved credential lives only inside the
`FetchSession`; error messages and state files carry none of it.[^c3]

Direct credential reads need the explicit marker
`# credentialed-primitive: reads-creds-directly`.

The `credbroker` implementation exists in two trees:
`packages/credbroker/credbroker/` (the published library) and
`packs/credential-brokers/.apm/user-libs/credbroker/` (the projected copy).
`agentbundle.build.user_libs.check_drift` is the read-only gate that reports a
difference between them, and the build rewrites the copy from the library.[^c4]

## 3. Secrets live in three tiers, and failure never falls through silently

| Tier | Storage | Boundary |
| --- | --- | --- |
| 1 | `<NAMESPACE>_<KEY>` environment variable | Used as supplied, for CI or wrappers. |
| 2 | macOS Keychain or Windows Credential Manager | Linux has no Tier 2. A documented hard failure raises `Tier2HardFailError` and does not fall through. macOS writes through child stdin, never argv. |
| 3 | `~/.agentbundle/credentials.env` | Opt-in. POSIX requires file `0600` and parent `0700`; Windows verifies the DACL. A permission failure raises `PermissiveAclError`. |

The Tier 3 parser rejects an `export ` prefix, variable expansion, and
multiline values. The optional `credbroker[crypto]` extra encrypts the file
into a vault; without it the file is plaintext.

On Linux, which has no Tier 2,
`credential-setup` writes Tier 3 directly. On macOS and Windows it refuses the
Tier 3 fallback unless given `--allow-insecure-fallback`.[^c5]

### State and write authority

| State | Location | Writer | Readers |
| --- | --- | --- | --- |
| Tokens | OS credential store or `~/.agentbundle/credentials.env` | `credbroker` write API | Credentialed primitive subprocesses |
| SSO profile and jar | `~/.agentbundle/sso-profiles/` and the SSO store | `sso-broker.py` | `credbroker` and the engine |
| Materialised cookie jar | `~/.agentbundle/sso-cookies/<profile>.jar` | `sso-broker.py get-cookies` | Credentialed primitive |
| Profile lock | `~/.agentbundle/sso-locks/<profile>.lock` | `sso-broker.py` | Store-touching SSO verbs |

Lockfiles hold no credential material and are never deleted, which prevents
split locking.

## 4. SSO sessions recover once, headlessly, and never by showing a login page

`sso-broker.py` has seven verbs: `register`, `get-cookies`, `test`, `refresh`,
`list-profiles`, `rm`, and `show-tier2-backend` (a probe that prints the active
Tier 2 backend). Capture is `register` (headed, 300-second sign-in poll) or
`refresh` (headless, 20-second silent window).[^c6]

Exit codes carry the recovery decision:

| Code | Meaning | Recovery |
| --- | --- | --- |
| `0` | Ok | None |
| `2` | No usable session | Re-authenticate |
| `4` | Profile not registered | Register |
| `6` | Another process holds the profile's store lock | Retry the same call |
| `3` | Engine failure | Terminal |
| `5` | Headless refresh needs a human | Terminal for automation; ask the operator to re-register |

An expired session triggers one headless refresh and one re-probe, and only on
the typed session-unavailable signal. Refresh takes a profile and never a
destination. A generic authentication error, timeout, confinement failure, or
missing engine is not an expired-session signal.[^c7]

Every mutating verb (`get-cookies`, `test`, `rm`, `register`, `refresh`) takes
the per-profile lock; `list-profiles` is advisory and unlocked. `get-cookies`
rewrites the materialised jar after each retrieval so a stale keychain-backed
session is never served. Locking is guaranteed only on a local filesystem; on
an unsupported network home, serialization can degrade or report permanent
contention.

Profile names match `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$` via `re.fullmatch`,
reject Windows reserved device names, and pass resolved-path containment. `rm`
is gated on containment alone, so a profile registered under a now-invalid name
stays deletable. Cookie values, names, and jar paths never cross argv.

### First-capture destination derivation

First capture may derive an HTTPS destination from protected-resource metadata,
OIDC discovery, or a registered vendor probe. A failed derivation refuses; it
never falls back to configured input. Every derivation request uses HTTPS,
follows no redirects, has 5-second connect and read limits inside a 15-second
total budget, caps bodies at 64 KiB, verifies certificates, accepts no insecure
flag, and sends no authorization, cookie, or proxy-authentication header.

Derivation compares origin only. It does not close same-principal
configuration poisoning, and some same-host topologies short-circuit it and
give no attestation.

`validate_https_url` checks only the scheme of
`login_url`, `success_url_pattern`, and `base_url`; it does not confine the
`success_url_pattern` host to the cookie domains. Cookie-send confinement is
enforced separately on the consumer side.[^c8]

## 5. Observability: the caller gets a typed result; cookie bytes never cross, engine stderr does

Per-verb exit codes make SSO refusals and lock contention observable without
returning cookie bytes. A primitive's `check` verb exits zero only when every
required key resolves; for `sso-cookie` it validates the captured session and
may use the bounded auto-recovery flow in § 4.

The `credbroker` library inherits the engine's stderr during interactive
`register` and `refresh`, and `load_sso_cookies` also inherits it, so engine
diagnostics reach the caller's stream unfiltered. When an agent runs the
primitive, that stderr lands in the agent's transcript; capturing and
translating it is **STATUS: PLANNED** (§ 7). Recapture notices go to the invoking process's stderr, not to a durable audit
log.[^c9]

## 6. Mechanical invariants

- `agentbundle catalogue lint` rule `CAT-L031` checks declared brokers, broker
  security phrases, argv bans, dotfile-read refusals, and broker-specific
  resolution patterns.
- `tools/lint-sso-config.py` requires shipped `sso-config.toml` files to stay
  placeholder-shaped: no real instance configuration, captured cookie value, or
  non-`creds` default ships upstream.

### The substring trap

A primitive's defensive path check must not literally name
`.agentbundle/credentials.env`; the credential-read rule treats that as a
direct read unless the primitive carries the opt-out marker.

```python
# Correct
parts = Path(suspect).parts
if "credentials.env" in parts and ".agentbundle" in parts:
    refuse(...)

# Tripped by the check
if str(suspect) == ".agentbundle/credentials.env":
    refuse(...)
```

## 7. Open design work

- **STATUS: PLANNED** — Replace the `persist` and `headless` Boolean pair in
  `sso-broker.py` `_capture` with named modes `operator-register`,
  `ephemeral-register`, and `automatic-refresh`, and capture and translate
  refresh stderr before the caller sees a failure:
  [`credential-broker-bounded-modes-and-errors`](../product/intents/credential-broker-bounded-modes-and-errors.md).
- **STATUS: PLANNED** — Bound browser-session lifetime, minimise stored
  cookies, serialize browser launches per profile, and budget macOS keychain
  calls:
  [`sso-browser-state-protection`](../product/intents/sso-browser-state-protection.md).
- **STATUS: PLANNED** — Retry once on exit `6` in the Jira check path and write
  recapture records to a durable log:
  [`sso-store-contention-and-audit-trail`](../product/intents/sso-store-contention-and-audit-trail.md).
- No operator setup guide exists. `guides/credential-brokers/` holds
  authoring guidance only, including
  [add a credentialed skill](../../guides/credential-brokers/how-to/add-a-credentialed-skill.md):
  [`credential-operator-guide`](../product/intents/credential-operator-guide.md).

## 8. Decisions

- [ADR-0003 — Credential broker contract](../adr/0003-credential-broker-contract.md)
- [ADR-0026 — SSO consumer resolution in credbroker](../adr/0026-sso-consumer-resolution-in-credbroker.md)
- [ADR-0080 — Generic headed SSO capture remains operator-only](../adr/0080-generic-headed-sso-capture-remains-operator-only.md)

[^c1]: Boundary statements: `docs/adr/0003-credential-broker-contract.md`, `docs/adr/0080-generic-headed-sso-capture-remains-operator-only.md`.

[^c2]: `packs/credential-brokers/.apm/skills/credential-setup/` (`SKILL.md`, `scripts/setup.py`); authoring guide `guides/credential-brokers/how-to/add-a-credentialed-skill.md`.

[^c3]: `packages/credbroker/credbroker/_http_access.py` (`resolve_http_access`); `packages/agentbundle/agentbundle/catalogue_fetch/__init__.py` (`open_fetch_session`).

[^c4]: `packages/agentbundle/agentbundle/build/user_libs.py` (`check_drift`, `collect_sources`); `packages/agentbundle/tests/build_pipeline/test_user_libs_projection.py`. `packages/credbroker/credbroker/` and `packs/credential-brokers/.apm/user-libs/credbroker/` hold the same module set (`_core`, `_sso`, `_http_access`, `_vault`, `_keychain_macos`, `_credman_windows`).

[^c5]: `packages/credbroker/credbroker/_core.py` (Tier 3 parser, `PermissiveAclError`), `_keychain_macos.py` (stdin write), `packages/credbroker/pyproject.toml` (`crypto` extra), `credential-setup` `setup.py` (`--allow-insecure-fallback`).

[^c6]: `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py`: `_build_parser`, `_REGISTER_SIGNIN_POLL_S`, `_REFRESH_SILENT_WINDOW_S`, module docstring exit-code table, `_GRAMMAR_GUARDED_VERBS`.

[^c7]: `packages/credbroker/credbroker/_sso.py`: `refresh_sso_session`, `SsoStoreContendedError`, `SsoSessionUnavailableError`.

[^c8]: `packages/credbroker/credbroker/_sso.py`: `_DERIVE_TOTAL_BUDGET_S`, `_DERIVE_BODY_CAP_BYTES`, `_derivation_opener`, `validate_https_url`; cookie-send confinement: `docs/specs/atlassian-sso-cookie/spec.md` (AC4, AC5, AC6, AC20).

[^c9]: `packages/credbroker/credbroker/_sso.py` (engine runner: `capture=False` inherits every stream, `capture=True` inherits stderr); `packs/atlassian/.apm/skills/jira/scripts/jira.py` (`main` configures `logging.basicConfig` without a filename).
