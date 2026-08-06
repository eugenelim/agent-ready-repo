# Credentials

> **Refreshed 2026-08-05.** The `creds` resolver is the standalone,
> pip-installable [`credbroker`](../rfc/0023-credential-manager-broker.md)
> library imported in-process ([RFC-0023](../rfc/0023-credential-manager-broker.md)),
> which replaced the build-projected `credentials_shim`. The `sso-cookie`
> broker ([RFC-0035](../rfc/0035-sso-cookie-auth-for-atlassian-pack.md)) now has
> its own section. The convention lint moved from a shell script into
> `agentbundle catalogue lint` (**CAT-L031**).

The secret-handling subsystem for credentialed primitives in this
catalogue. Defines how a credentialed primitive — a `jira`, `figma`,
or `confluence-publisher` CLI — acquires a credential at runtime without
ever putting it on argv, in env-var echoes, or in agent transcripts.
Authoritative specs:
[`docs/specs/credential-broker-contract/spec.md`](../specs/credential-broker-contract/spec.md)
(current contract); the predecessor
[`docs/specs/skill-secrets/spec.md`](../specs/skill-secrets/spec.md)
(historical, three-tier model). *Why*:
[RFC-0013](../rfc/0013-credential-broker-contract.md) +
[RFC-0006](../rfc/0006-skill-secrets-storage.md).

## Threat model — what this subsystem does and does not defend against

The tier model predates coding agents. It was built for a world where the
adversary is *another user*, an accidental `echo`, a process list, a shell
history file, or a `git add .`. Against those it works, and every control here
earns its place.

It was **not** built for an adversary running as the *same OS principal*, and it
cannot be retrofitted to. If an agent executes as you, then by construction it
can read `~/.agentbundle/credentials.env`, call the keychain with your
credentials, edit `~/.agentbundle/sso-profiles/*.toml`, and invoke
`~/.agentbundle/bin/sso-broker.py` directly. No tier, no `0600`, and no
in-process guard changes that — they are all inside the boundary the adversary
already occupies.

**Defends against**

- A secret reaching argv, a process list, a shell history, or a transcript.
- A secret entering the agent's *context* — consumers receive a path or a
  resolved value inside their own subprocess, never bytes the model sees.
- A secret at rest being read by another user, or committed to git.
- Silent degradation: resolution fails closed rather than falling through.

**Does not defend against**

- A same-principal process reading the store directly.
- A same-principal process editing an adopter config that names a destination.
- A same-principal process invoking the engine itself.

That distinction matters because the dominant real failure mode is an agent that
*misbehaves* — leaks a value into a log, echoes it into a transcript, pastes it
into an issue — not one that is *adversarial*. This subsystem substantially
closes the first and does not close the second. Documenting a stronger boundary
than exists is how a design ends up resting on a control it never had.

### The accepted profile, and the one carve-out

This catalogue **accepts** the same-principal limit rather than pretending to
close it. The accepted profile is:

> **The subsystem defends against an agent that errs, not an agent that is
> hostile.** A hostile same-principal process already has everything on the box.

That acceptance is not new and not specific to SSO — it has always been true of
the token path. An adversarial agent can read the Tier-3 dotfile, call the
keychain, or invoke the engine directly. Any control we add *inside* that
boundary is theatre, so we do not add it, and we do not claim it.

**The consequence for feature design is liberating, with one exception.** Once
the profile is accepted, a new capability is only worth arguing about if it gives
a hostile agent something it *did not already have*. Most do not: a convenience
verb that reads a store the agent could read anyway, or spawns an engine the
agent could spawn anyway, adds no reachable capability. Those ship.

The exception is **any flow that puts a human in front of a login page whose
destination the agent could influence.** That is categorically different: it does
not read what is already on the box, it *harvests a credential the agent cannot
otherwise obtain* — the operator's IdP password and MFA, which unlock far more
than the tool being configured. The blast radius leaves the machine.

So the boundary is not a verb and not a subsystem. It is:

| | Human types credentials? | Verdict |
|---|---|---|
| Automated re-auth against a warm browser session | no | ships — no marginal capability |
| Any flow that renders a login page to a human | **yes** | the one place a real control is worth its cost |

Where a control is warranted, it must satisfy the anchor test below — integrity
protection for the destination fields specifically, not for the whole config.

**What actually closes the same-principal case**, from a survey of comparable
projects (see the references below), is always a trust anchor the agent's process
cannot forge or reach:

| Anchor | Example |
|---|---|
| Another machine / network boundary | credential-injecting egress proxies — the secret is never on the agent's host |
| Another privilege level | `sudo`-gated wrappers; a root-owned config the agent cannot write |
| OS-mediated human presence | biometric / WebAuthn approval prompts |
| Platform attestation | SPIFFE/SPIRE — identity asserted by the kernel or orchestrator, not the caller |
| Cryptographic binding at issuance | authorization bound into a token by a human, un-widenable at call time |

Everything that fails does so the same way: it tries to enforce the boundary
*inside* the process the adversary controls — validation, allowlists, config
guards, prose rules, in-band confirmation. Any future control added here should
be checked against that test first.

## Two-layer architecture

The repo distinguishes two things that often get conflated:

- **Skills** never read credentials. They drive UX, planning, and
  shell-out patterns, but they don't talk to authenticated APIs
  themselves.
- **Credentialed primitives** read credentials. Every primitive
  declares its broker via `SKILL.md` frontmatter:

  ```yaml
  metadata:
    credentialed: true
    primitive-class: credentialed-cli   # or: mcp-server
    auth: creds                         # or: env / cli / sso-cookie
    namespace: <namespace>
    keys: ["<KEY>"]
  ```

  - `credentialed-cli` — a Python module invoked via subprocess that
    reads credentials inside its own process. **Refuses** any
    value-shaped credential flag (`--token`, `--api-key`, `--bearer`,
    `--pat`, `--password`).
  - `mcp-server` — an MCP server holding the secret. May accept
    *header-naming* flags (`--bearer-header`, `--auth-header`) but
    never value-shaped flags.

The `auth:` field selects which broker the primitive uses:

| Broker | Credential | Section |
| --- | --- | --- |
| `creds` | a token resolved through three storage tiers | [The `creds` broker](#the-creds-broker) |
| `sso-cookie` | a captured web session (cookie jar) | [The `sso-cookie` broker](#the-sso-cookie-broker) |
| `env` | a value the environment already holds | see the contract spec |
| `cli` | delegated to a vendor CLI's own login | see the contract spec |

A primitive may declare a fallback. `jira` carries `auth: sso-cookie`
with `auth-fallback: creds`, so the lint requires **both** brokers'
Don't-block phrase sets in its Security section.

### What the lint enforces

`agentbundle catalogue lint` — **CAT-L031**, implemented as
`_check_credentialed_skills` in
[`agentbundle/catalogue_tooling/lint.py`](../../packages/agentbundle/agentbundle/catalogue_tooling/lint.py)
and run by `make build-check`. It checks the argv ban, the presence of
each declared broker's Don't-block phrases under the
`### Security rules (non-negotiable)` heading (matched
whitespace-normalised, so the phrases may wrap), refusal to read the
dotfile, and per-broker AST walks over the primitive's scripts — e.g.
`auth: creds` requires a `credbroker` resolver import, and `auth:
sso-cookie` requires resolution via `load_sso_cookies`. A primitive that
genuinely must read credentials directly opts out with the
`# credentialed-primitive: reads-creds-directly` marker.

## The three tiers

| Tier | Storage | Use case |
| --- | --- | --- |
| **Tier 1** | `<NAMESPACE>_<KEY>` env var (`JIRA_API_TOKEN`, `JIRA_BASE_URL`, …) | CI runners, wrapper scripts that inject secrets per-command. |
| **Tier 2** | OS keyring (macOS Keychain, Windows Credential Manager) | Interactive developer machine. The default. |
| **Tier 3** | `~/.agentbundle/credentials.env`, mode `0600` + parent `0700` | Locked-down environments where Tier 2 isn't available; opt-in fallback. |

`credbroker`'s Tier-2 dispatch is `sys.platform`-gated to `darwin` and
`win32` only, so **Linux has no Tier 2** and falls through to Tier 3.
libsecret support is deferred to a follow-up RFC.

### Tier 2 backends — stdlib only

- **macOS** (`credbroker`'s `_keychain_macos.py`) —
  `subprocess.run(["/usr/bin/security", ...])`. The write path passes
  the token via **child stdin**, never argv. Service =
  `"agentbundle"`, account = `"<namespace>:<key>"`.
- **Windows** (`credbroker`'s `_credman_windows.py`) —
  `ctypes` against `advapi32.{CredReadW, CredWriteW, CredDeleteW,
  CredFree}`. In-process, no subprocess. `CRED_TYPE_GENERIC`,
  `CRED_PERSIST_LOCAL_MACHINE`, target-name
  `agentbundle:<namespace>:<key>`.

The backend label is selected at module-load time per `sys.platform`.
A documented set of Win32 hard-fail codes raises `Tier2HardFailError`
and does **not** fall through to Tier 3. Silent degradation is the
security smell, not the dotfile.

### Tier 3 — the dotfile

A stdlib `.env` parser (`parse_env_file` in `credbroker`'s `_core`)
handles `KEY=value`, quoted values, and `#` comments. It rejects
`export ` prefix, variable expansion, and multi-line values — `.env`
is not bash. POSIX: enforces mode `0600` on the file and `0700` on
`~/.agentbundle/`. Windows: DACL-verified via `icacls`.
`PermissiveAclError` on either failure.

Where `credbroker[crypto]` is installed (a pip layer, never the stdlib
floor), Tier 3 upgrades from the plaintext dotfile to an AEAD-encrypted
**vault** (Argon2id → KEK → AES-256-GCM, `credbroker`'s `_vault`); the
vendored floor stays stdlib-only and plaintext. See
[RFC-0023](../rfc/0023-credential-manager-broker.md).

## The `creds` broker

The `creds` broker resolves credentials through the three-tier model
below. Since [RFC-0023](../rfc/0023-credential-manager-broker.md) the
implementation is the standalone, pip-installable **`credbroker`**
library ([`packages/credbroker/`](../../packages/credbroker/)), imported
**in-process** — it replaced the build-projected `credentials_shim` that
earlier dropped a byte-identical copy (plus the Tier-2 backends
`_keychain_macos.py` / `_credman_windows.py`, now `credbroker`'s own
modules) into every consumer's `scripts/`. Consumers import the absolute
package form:

```python
from credbroker import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)

creds = load_credentials(
    namespace="jira",
    required_keys=["API_TOKEN", "BASE_URL", "EMAIL"],
)
creds.API_TOKEN  # str
```

Returns an immutable dataclass; attribute access on a key not in
`required_keys` raises `AttributeError`. Single responsibility:
*resolve* — schema validation is the `credential-setup` skill's
job, not the loader's. The loader walks **first-hit-wins per key**
(a key resolved at Tier 1 is not re-checked at lower tiers; mixing
tiers across keys within one namespace is permitted).

### How `credbroker` reaches the interpreter — the layered delivery

`import credbroker` resolves through a `sys.path` precedence stack fed by
two delivery layers (full author-facing detail in the
[how-to](../../guides/credential-brokers/how-to/add-a-credentialed-skill.md#how-credbroker-reaches-syspath--the-layered-model)):

- **Vendored floor (zero-pip, user scope).** A user-scope install of the
  `credential-brokers` pack delivers a byte-faithful, stdlib-base copy of
  the package source to `~/.agentbundle/lib/credbroker/`, which every
  credentialed skill appends to `sys.path` at **lowest** precedence — so a
  no-repo install resolves Tier-1/2/3 with no pip. The floor is drift-gated
  byte-for-byte against `packages/credbroker/credbroker/` — **one shared
  copy**, not the N-per-skill projection the shim used. The projection is
  performed by `agentbundle`'s build pipeline
  ([`build/user_libs.py`](../../packages/agentbundle/agentbundle/build/user_libs.py)),
  which copies *files*; it holds no knowledge of `credbroker`'s API.
- **pip (corporate / PyPI).** A `pip install credbroker` (internal index,
  local wheel, or PyPI) lands in site-packages, which precedes the floor on
  `sys.path` — so it wins and unlocks the encrypted `[crypto]` vault.

The `credentials_shim` source is **kept** at
[`packs/credential-brokers/.apm/shared-libs/credentials_shim.py`](../../packs/credential-brokers/.apm/shared-libs/credentials_shim.py),
but only as the companion shim that rides the `adapter-root-bins` →
`~/.agentbundle/bin/` projection for `sso-broker.py`; no consumer skill
imports it for `creds` resolution any more.

## The `sso-cookie` broker

> **Added by [RFC-0035](../rfc/0035-sso-cookie-auth-for-atlassian-pack.md);
> consumer resolution placed in `credbroker` by
> [ADR-0026](../adr/0026-sso-consumer-resolution-in-credbroker.md);
> recapture added by
> [`docs/specs/jira-check-sso-auto-login/spec.md`](../specs/jira-check-sso-auto-login/spec.md).**

For a Data Center instance behind corporate SSO there is no token to
resolve — the credential is a **captured web session**. The `sso-cookie`
broker covers that case. It is the only broker whose acquisition step
needs a human and a browser, which is what shapes everything below.

### Engine and library — the dependency direction

Two components, and the direction between them is load-bearing:

- **`sso-broker.py`** — the *engine*. Ships via `adapter-root-bins` to
  `~/.agentbundle/bin/`. Stdlib-only for `get-cookies` / `test` / `rm` /
  `list-profiles`; `register` and `refresh` additionally require **playwright**
  and exit non-zero when it is absent. `register` drives a **headed** Chromium
  for interactive capture; `refresh` drives a **headless** one with a bounded
  silent-completion window and returns a distinct exit code rather than showing a
  login page, so an automated consumer can never put one in front of an operator.
  Both store the jar (see below), and `get-cookies` answers with a **path, never
  bytes**.
- **`credbroker`** — the *library* consumers import. It **subprocesses**
  the engine.

So `credbroker` → `sso-broker.py`, never the reverse. The engine cannot
import `credbroker`; anything both need — notably the profile grammar
below — is duplicated deliberately and pinned equal by test.

### Consumer API

Consumers never resolve the broker path, build its argv, or call
`subprocess` themselves:

> **Status:** `load_sso_cookies` ships today. `validate_sso_profile`,
> `refresh_sso_session`, `register_sso_session` and `derive_sso_destination` are **planned** — specified by
> [`jira-check-sso-auto-login`](../specs/jira-check-sso-auto-login/spec.md) and
> landing with `credbroker` 0.5.0. This page is updated in that PR, not ahead of it.

```python
import credbroker

credbroker.validate_sso_profile(profile)        # grammar guard
jar_path = credbroker.load_sso_cookies(profile) # path, never bytes
credbroker.refresh_sso_session(profile)         # re-capture an expired session
credbroker.register_sso_session(profile, login_url=..., ...)  # first-time capture
credbroker.derive_sso_destination(base_url, strategies=())     # ask the resource (first capture only)
```

`refresh_sso_session` takes **only a profile** — deliberately. That
signature is how **destination pinning** is enforced: it is structurally
incapable of forwarding a sign-in destination, so an automated recovery
path cannot choose where the browser goes. The engine reads the
destination from `~/.agentbundle/sso-profiles/<profile>.toml`, which only
a completed, operator-authorised `register` writes.
`register_sso_session` is the sole function that accepts a destination.
**The guarantee is a property of this API, not of the system:** the engine binary
is directly invokable by any process running as the operator, so a caller with
shell access can hand it a destination regardless. Consumers are expected to
reach `register_sso_session` only from an operator-typed action, which is a
convention enforced by each consumer's own skill rules — not by this library.

Keeping the spawn inside `credbroker` also keeps the cross-platform
parts — timeout, process-tree kill (POSIX process groups vs Windows),
and environment composition — in one type-checked, CI-exercised place
rather than copied into each consumer skill.

### Where the jar actually lives

Two storage surfaces, and conflating them hides real bugs:

- **Primary store.** On Tier-2-capable platforms (macOS, Windows)
  `_store_cookie_jar` writes the jar into the **OS keychain**, chunked across
  continuation credentials when it exceeds the per-credential blob limit. Where
  Tier 2 is deferred by policy (Linux), it writes a `0600` file under
  `~/.agentbundle/sso-cookies/`.
- **Materialisation surface.** Consumers never receive bytes, so `get-cookies`
  writes the jar it just loaded to `~/.agentbundle/sso-cookies/<profile>.jar`
  and prints that path. On Linux the two surfaces are the same file; on
  macOS/Windows they are not — which is why the materialisation must be
  unconditional. A `get-cookies` that skips the rewrite when the file already
  exists serves a stale jar after every keychain-backed re-capture.

### Confinement controls

The engine's captured jar is deliberately over-broad, so the library
adds the controls above it — `validate_https_url`,
`validate_root_relative_endpoint`, `domain_in_cookie_domains`,
`filter_jar_to_domains`, `require_host_in_cookie_domains` — single-sourced
in `credbroker` so they cannot drift between consumers. On top of those:

- **Profile grammar.** `profile` is interpolated into filesystem paths
  and a keychain target name, so it is confined to
  `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$` via `re.fullmatch` (**not**
  `re.match`, whose `$` admits a trailing newline), excluding
  case-insensitive Windows reserved device names (`CON`, `NUL`, …) —
  on Windows `CON.toml` resolves to the console device regardless of
  directory. The engine enforces the same grammar independently, plus
  resolved-path containment (canonicalize-then-verify-parent).
- **No secret on argv.** No cookie value, cookie name, or jar path ever
  crosses a command line, in either direction.

### Destination derivation — defence in depth, on first capture only

The **automatic** recapture path takes no destination at all (see the Consumer
API above), so it needs no derivation. Derivation exists for the one path that
*does* accept one — an operator-typed first capture — where
`credbroker.derive_sso_destination(base_url, *, strategies=())` asks the
**resource server** where to authenticate, in a vendor-agnostic strategy chain,
returning the first scheme+host it resolves:

| Tier | Mechanism | Applies to |
|---|---|---|
| 1 | **RFC 9728** Protected Resource Metadata — `401` → `WWW-Authenticate: … resource_metadata` → `/.well-known/oauth-protected-resource` → authorization server metadata | modern OAuth resources (MCP adopted it) |
| 2 | **OIDC Discovery / RFC 8414** — `/.well-known/openid-configuration` → `authorization_endpoint` | most OIDC-protected on-prem tools |
| 3 | **Vendor probe** — a registered per-consumer strategy; Atlassian/Seraph is `GET {base_url}/login.jsp`, redirects unfollowed, read `Location` | Jira / Confluence / Bitbucket DC |
| 4 | none | SAML-only SPs — their metadata names the SP, never the IdP |

Tier 3 exists because SAML has no discovery equivalent; tier 4 is a real
outcome, not a failure to handle. A consumer that cannot derive **refuses** and
does not fall back to the configured value.

**What derivation does not do.** It does **not** close config poisoning: the
derivation target (`base_url`) lives in the same adopter- and agent-writable file
as the value being attested, so one write moves both and the comparison passes.
AWS's equivalent works only because its host suffix is hardcoded to
`*.amazonaws.com`; there is no comparable invariant here. Where the configured
sign-in host equals the base host — SP-initiated SAML, the majority Jira DC
topology — derivation is bypassed by construction and attests nothing. Consent
for first capture therefore rests on the operation being **operator-typed**, not
on attestation. And attestation itself is **partial, not universal**: where the
configured sign-in host equals the base host — SP-initiated SAML, the majority
topology — derivation short-circuits and verifies nothing, so the re-register
path attempts attestation but only achieves it on IdP-host topologies. A vendor's
own setup helper performs none at all. Only scheme+host is compared; every tier's URL carries
per-request `state` / `SAMLRequest` / `nonce`.

**Bounds — this is an outbound fetch on the credential path.** Every hop is
`https` only (including URLs read from a `resource_metadata` header or an
`authorization_servers` list); redirects are not followed (hop cap 0); 5 s
connect + 5 s read under a ≤15 s total budget; a 64 KiB body cap before parsing;
strict certificate verification that never honours an `--insecure`-style flag and
never reuses a consumer's own TLS context; and no `Authorization`, `Cookie`, or
proxy-auth header on any derivation request.

### Auto-recovery contract

A consumer's `check` verb may self-heal an **expired** session: on a typed
session-unavailable signal it calls `refresh_sso_session` once and re-probes.
That call is **headless** — it succeeds only when the browser profile can
complete the IdP flow unaided, and otherwise fails fast rather than presenting a
login page. It must key on that typed signal, never on a generic auth
error — a `403`, a failed confinement check, or a missing engine are
terminal, and re-authenticating cannot fix them. First-time capture stays
an explicit human action.

### What this costs the operator

Two very different experiences, and the split is the point — the path that runs
unattended is the one that is structurally safe.

| | Who acts | What they see | How often |
|---|---|---|---|
| **First capture** | operator, explicitly | a real sign-in page in a fresh browser context, and the destination host on stderr before it opens | **once per machine, per profile** |
| **Silent refresh** | nobody | nothing — `refresh` is headless | whenever the app session expires and the IdP session is still valid |
| **Re-registration prompt** | operator, unplanned | an exit-2 message, **not** a login page — headless `refresh` fails fast and names the consumer's *re-register* command, which is the path that attempts destination attestation | when the **IdP** session has also expired — typically first use of the day |

The middle row is the common case and is safe by construction:
`refresh_sso_session(profile)` accepts no destination, so an automated caller
cannot choose where the browser goes. The first row accepts a destination and is
therefore deliberately **not** automated — see the trust limits above.

The third row is why `refresh` is headless. An unattended refresh that could open
a headed browser would leave an agent-influenced login page in front of whoever
happens to be at the machine — the one exposure whose blast radius leaves the box.
A headless refresh instead fails fast and tells the caller a human is needed;
interactive capture is reachable only from an operator-typed command.

## Setting up credentials

The `credential-setup` skill — source at
[`packs/credential-brokers/.apm/skills/credential-setup/`](../../packs/credential-brokers/.apm/skills/credential-setup/),
installed into whichever adapter path the adopter's install targets —
replaces the prior `agentbundle creds setup <namespace>` CLI. The skill:

- Reads the consumer's `references/creds-schema.toml` to know which
  keys to prompt for.
- Walks each key via `getpass` (secret) or `input` (non-secret
  sibling like `BASE_URL`).
- Writes to the highest-available tier (Keychain → Credential Manager
  → dotfile), announces the chosen tier on stderr, and refuses to
  fall back to Tier 3 without `--allow-insecure-fallback`.

There is no `get` verb. The LLM is never given a tool that returns
cleartext. Anything that needs the credential reads it via
`load_credentials` inside the primitive's own subprocess and writes
it to an outbound HTTP header.

To verify resolution, invoke the consumer primitive's own `check` verb —
e.g. `python scripts/jira.py check` walks the same Tier 1 → 2 → 3
ladder and exits 0 when every declared key resolves. On a primitive whose
`auth:` is `sso-cookie`, `check` instead validates the captured session
and may self-heal it per the auto-recovery contract above.

## Per-primitive schema declaration

Every credentialed primitive ships `references/creds-schema.toml`
declaring its namespace and keys — a `[namespace]` table plus one
`[[namespace.keys]]` entry per key:

```toml
[namespace]
name = "jira"

[[namespace.keys]]
name = "BASE_URL"
label = "Jira base URL (Cloud: https://<site>.atlassian.net; Server: https://jira.corp.example.com)"
secret = false

[[namespace.keys]]
name = "API_TOKEN"
label = "Cloud API token or Server Personal Access Token"
secret = true
```

The env-var shape is `<NAMESPACE>_<KEY>` — `JIRA_BASE_URL`,
`JIRA_API_TOKEN`. `label` is the prompt text the `credential-setup` skill
issues. `secret` distinguishes which keys go to keyring storage from
non-secret siblings like `BASE_URL`. The canonical reference is
[`packs/atlassian/.apm/skills/jira/references/creds-schema.toml`](../../packs/atlassian/.apm/skills/jira/references/creds-schema.toml).

## The substring trap

Refuse-guards inside a primitive's script that **literally name** the
substring `.agentbundle/credentials.env` trip the same
[`conventions-check`](../../.claude/commands/conventions-check.md) rule
that catches credential *reads*, unless the script carries the
`# credentialed-primitive: reads-creds-directly` opt-out marker.

Compose path checks via basename + `Path.parts`, never the literal
full string:

```python
# Correct
parts = Path(suspect).parts
if "credentials.env" in parts and ".agentbundle" in parts:
    refuse(...)

# Tripped by the check
if str(suspect) == ".agentbundle/credentials.env":
    refuse(...)
```

This applies to any primitive script that mentions the dotfile
defensively.

## Prior art and threat references
The controls above are shaped by these; each is cited where the reasoning depends
on it rather than as a reading list.

- **Confused deputy / designation with authority** — the 1988 confused-deputy paper;
  [*Capability Myths Demolished*](https://papers.agoric.com/assets/pdf/papers/capability-myths-demolished.pdf).
  Why the automatic path takes **no** destination parameter instead of validating
  one.
- **Config file as a trust boundary** —
  [CVE-2024-52006 / GHSA-qm7j-c969-7j4q](https://github.com/git/git/security/advisories/GHSA-qm7j-c969-7j4q)
  (Git credential helper): *"configuration-file-supplied URLs receive the same
  credential access as explicitly user-provided URLs, despite having different
  trustworthiness profiles."*
- **Host pinning vs config-supplied tenant** — AWS CLI
  [IAM Identity Center](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html):
  `sso_start_url` is config-supplied, but the browser endpoint is derived from
  `sso_region` and is always `*.amazonaws.com`.
- **Resource-served destination discovery** —
  [RFC 9728](https://www.rfc-editor.org/rfc/rfc9728.pdf) (Protected Resource
  Metadata) and OIDC Discovery / RFC 8414, tiers 1–2 above. The
  [MCP authorization spec](https://modelcontextprotocol.io/specification/draft/basic/authorization/security-considerations)
  adopts RFC 9728 and notes the residual limit: issuer validation *"provides no
  protection if the expected issuer was obtained from an unvalidated source."*
- **The approval channel must be one the agent cannot write** — OWASP Top 10 for
  Agentic Applications 2026, **ASI09** (Human-Agent Trust Exploitation) and
  **ASI02**; OWASP Agentic Skills **AST03**. Why an in-prompt or agent-owned-TTY
  confirmation is not a control.
- **Trust-on-first-use does not close first-contact poisoning** —   *Why TOFU Doesn't Work* (TOFU critique).
- **Well-formed arguments defeat schema gating** —
  [*Capability Gates Are Not Authorization*](https://arxiv.org/html/2606.28679v1)
  (arXiv 2606.28679).
- **Privilege separation is what actually protects an agent-editable config** —
  *Locking down `gh`* (practitioner writeup):
  the same failure shape for `gh auth setup-git`, mitigated with `sudo`-gated
  wrappers rather than validation.
- **Derive the destination from live browser state** — 1Password's extension
  model injects only when the browser is already on the matching origin, with a
  biometric approval prompt that is genuinely out of an agent's reach.

## Where to read next

- [`docs/specs/credential-broker-contract/spec.md`](../specs/credential-broker-contract/spec.md) —
  the broker contract.
- [`docs/rfc/0023-credential-manager-broker.md`](../rfc/0023-credential-manager-broker.md) —
  the `credbroker` library that replaced the projected shim for `auth: creds`
  (and its layered-delivery amendment); [`docs/specs/credbroker/spec.md`](../specs/credbroker/spec.md)
  + [`docs/specs/credbroker-user-scope/spec.md`](../specs/credbroker-user-scope/spec.md)
  are the implementing specs.
- [`docs/rfc/0035-sso-cookie-auth-for-atlassian-pack.md`](../rfc/0035-sso-cookie-auth-for-atlassian-pack.md) —
  the `sso-cookie` broker; [`docs/adr/0026-sso-consumer-resolution-in-credbroker.md`](../adr/0026-sso-consumer-resolution-in-credbroker.md)
  places consumer resolution in `credbroker`, and
  [`docs/specs/jira-check-sso-auto-login/spec.md`](../specs/jira-check-sso-auto-login/spec.md)
  extends it from resolution-only to resolution-plus-recapture.
- [`docs/rfc/0013-credential-broker-contract.md`](../rfc/0013-credential-broker-contract.md) —
  the broker design rationale (the predecessor shim model).
- [`docs/specs/skill-secrets/spec.md`](../specs/skill-secrets/spec.md) —
  the predecessor spec (kept for historical context).
- [`guides/credential-brokers/explanation/credentialed-skills.md`](../../guides/credential-brokers/explanation/credentialed-skills.md) —
  the adopter-facing companion.
- [`guides/credential-brokers/how-to/add-a-credentialed-skill.md`](../../guides/credential-brokers/how-to/add-a-credentialed-skill.md) —
  the step-by-step procedure for authoring a new credentialed primitive.
