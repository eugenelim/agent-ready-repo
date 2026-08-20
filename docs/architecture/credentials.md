# Credentials and trust boundaries

## 1. Purpose and boundary

Credentialed primitives obtain credentials at runtime without placing secret bytes
on argv, in process-visible shell history, or in agent transcripts. The
subsystem protects against accidental exposure and cross-user access at rest.

It does not protect against a hostile process running as the same OS principal.
That process can read local stores, alter adopter configuration, or invoke the
engine. A human login page is different: an agent-influenced destination could
harvest credentials the agent did not already have. Headed capture therefore
remains operator-only.

## 2. Entrypoints

- Credentialed primitives declare one broker in `SKILL.md`: `creds`, `env`,
  `cli`, or `sso-cookie`.
- `credbroker.load_credentials` resolves `creds` in-process.
- `credbroker.load_sso_cookies`, `refresh_sso_session`, and
  `register_sso_session` are the consumer SSO API.
- `sso-broker.py` provides `get-cookies`, `test`, `rm`,
  `list-profiles`, `register`, and `refresh`.
- `credential-setup` reads `references/creds-schema.toml`, prompts with
  `getpass` or `input`, writes the highest available tier, and reports it on
  stderr.
- [Credentialed-skill authoring guidance](../../guides/credential-brokers/how-to/add-a-credentialed-skill.md)
  covers broker and primitive declarations, not operator setup.

## 3. Owned state and write authority

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Tokens | OS credential store or `~/.agentbundle/credentials.env` | `credbroker` write API | Credentialed primitive subprocesses |
| SSO profile and jar | `~/.agentbundle/sso-profiles/` and SSO store | `sso-broker.py` | `credbroker` and the engine |
| Materialised cookie jar | `~/.agentbundle/sso-cookies/<profile>.jar` | `sso-broker.py get-cookies` | Credentialed primitive |
| Profile lock | `~/.agentbundle/sso-locks/<profile>.lock` | `sso-broker.py` | Store-touching SSO verbs |

Consumers receive a jar path, never cookie bytes. SSO lockfiles contain no
credential material and are never deleted.

## 4. Dependencies and allowed edges

Skills orchestrate credentialed primitives but never read credentials. A
`credentialed-cli` refuses value-shaped credential flags such as `--token`,
`--api-key`, `--bearer`, `--pat`, and `--password`. An MCP server may
accept header-naming flags but never value-shaped flags.

No `get` verb or tool returns cleartext to the model. A primitive calls
`load_credentials` inside its own subprocess and uses the value only in an
outbound HTTP header. Direct credential reads require the explicit
`# credentialed-primitive: reads-creds-directly` marker.

`credbroker` imports no SSO engine code. It subprocesses `sso-broker.py`;
the engine never imports `credbroker`. Consumers call the library and do not
construct broker argv or subprocesses themselves.

The `creds` broker uses first-hit-wins per required key. `env` consumes an
already-present environment value. `cli` delegates to the vendor CLI.
A fallback declaration requires both brokers' security phrases.

## 5. Primary flows

1. `creds` resolves each required key through Tier 1, Tier 2, then Tier 3.
2. `sso-cookie` loads a stored session, materialises a jar path, and passes
   that path to the consumer.
3. An expired typed SSO session may trigger one headless refresh and one
   re-probe. First capture and re-registration are operator actions.
4. A credentialed primitive uses the resolved value inside its own process for
   the outbound request.

## 6. Failure and recovery behavior

### Three storage tiers

| Tier | Storage | Refusal or boundary |
| --- | --- | --- |
| 1 | `<NAMESPACE>_<KEY>` environment variable | Used as supplied for CI or wrappers. |
| 2 | macOS Keychain or Windows Credential Manager | Linux has no Tier 2. Documented hard failures raise `Tier2HardFailError` and do not fall through. macOS writes by child stdin, never argv. |
| 3 | `~/.agentbundle/credentials.env` | Opt-in fallback. POSIX requires file `0600` and parent `0700`; Windows verifies the DACL. Permission failures raise `PermissiveAclError`. |

The Tier-3 parser rejects `export ` prefixes, variable expansion, and
multiline values. Optional `credbroker[crypto]` uses an encrypted vault;
the stdlib floor remains plaintext. `credential-setup` refuses Tier-3 fallback
without `--allow-insecure-fallback`.

SSO exit code `2` means no usable session, `4` means an unregistered
profile, and `6` means a contended store. Only those are recoverable:
`2` and `4` require re-authentication, while `6` retries the same call.
Engine failure (`3`) and required human interaction (`5`) are terminal.

Automatic refresh takes only a profile, never a destination. It is headless and
returns `5` rather than displaying a login page. Consumers recover only from
the typed session-unavailable signal, refresh once, and re-probe once. A generic
authentication error, timeout, confinement failure, or missing engine is not an
expired-session signal.

Every SSO mutation uses a per-profile lock. `list-profiles` is advisory and
unlocked. `get-cookies`, `test`, `rm`, `register`, and `refresh` share that
lock. `get-cookies` rewrites the materialised jar after each retrieval to avoid
serving a stale keychain-backed session. The lockfile is retained to prevent
split locking. Locking is only guaranteed on a local filesystem; unsupported
network-home locking can degrade serialization or report permanent contention.

Profile names match `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$` with
`re.fullmatch`, reject Windows reserved device names, and pass resolved-path
containment. Cookie values, names, and jar paths never cross argv.

First capture may derive an HTTPS destination from protected-resource metadata,
OIDC discovery, or a registered vendor probe. Failure to derive refuses; it
never falls back to configured input. Derivation compares only origin and does
not close same-principal configuration poisoning. Some same-host topologies
short-circuit derivation and provide no attestation.

Every derivation request uses HTTPS, follows no redirects, has a 5-second
connect and read limit within a 15-second total budget, caps bodies at 64 KiB,
verifies certificates, accepts no insecure flag, and sends no authorization,
cookie, or proxy-authentication header.

### The substring trap

A primitive's defensive path check must not literally name
`.agentbundle/credentials.env`; the credential-read rule treats that as a
direct read unless the primitive carries its direct-read opt-out marker.

```python
# Correct
parts = Path(suspect).parts
if "credentials.env" in parts and ".agentbundle" in parts:
    refuse(...)

# Tripped by the check
if str(suspect) == ".agentbundle/credentials.env":
    refuse(...)
```

## 7. Observability and evidence

`sso-broker.py` returns per-verb exit codes. SSO refusals and lock contention
are observable without returning cookie bytes. Credential resolution exposes
success or typed failure to the invoking primitive, not to the agent context.

A consumer primitive's `check` verb verifies its declared credential ladder
and exits zero only when every required key resolves. An `sso-cookie` check
validates the captured session and may use the bounded auto-recovery flow.

## 8. Mechanical invariants

- `agentbundle catalogue lint` (`CAT-L031`) checks declared credential
  brokers, broker security phrases, argv bans, dotfile-read refusals, and
  broker-specific primitive resolution patterns.
- `tools/lint-sso-config.py` requires shipped `sso-config.toml` files to be
  placeholder-shaped: no real instance configuration, captured cookie value,
  or non-`creds` default may ship upstream.

## 9. Relevant ADRs

- [ADR-0003 — Credential broker contract](../adr/0003-credential-broker-contract.md)
- [ADR-0026 — SSO consumer resolution in credbroker](../adr/0026-sso-consumer-resolution-in-credbroker.md)
- [ADR-0080 — Generic headed SSO capture remains operator-only](../adr/0080-generic-headed-sso-capture-remains-operator-only.md)

## 10. Last verified against commit

`c8cf4b37`
