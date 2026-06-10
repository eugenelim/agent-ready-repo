# Credentials

> **Updated for [RFC-0023](../rfc/0023-credential-manager-broker.md) (2026-06-09).**
> For `auth: creds`, the resolver is the standalone, pip-installable
> [`credbroker`](../rfc/0023-credential-manager-broker.md) library imported
> in-process. It replaced the build-projected `credentials_shim`, which now
> survives only as the `adapter-root-bins` companion shim for `sso-broker`.
> This page describes the current (credbroker) model; the three-tier storage
> contract below is unchanged from the shim.

The secret-handling subsystem for credentialed primitives in this
catalogue. Defines how a credentialed primitive — a `jira`, `figma`,
or `confluence-publisher` CLI — acquires a token at runtime without
ever putting it on argv, in env-var echoes, or in agent transcripts.
Authoritative specs:
[`docs/specs/credential-broker-contract/spec.md`](../specs/credential-broker-contract/spec.md)
(current contract; four brokers); the predecessor
[`docs/specs/skill-secrets/spec.md`](../specs/skill-secrets/spec.md)
(historical, three-tier model). *Why*:
[RFC-0013](../rfc/0013-credential-broker-contract.md) +
[RFC-0006](../rfc/0006-skill-secrets-storage.md).

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

The `auth:` field selects which broker the primitive uses. `creds` is
the three-tier model documented below; `env` / `cli` / `sso-cookie`
cover environment-variable, vendor-CLI delegation, and headed-browser
SSO flows respectively. See the spec for the per-broker contracts.

`tools/lint-credentialed-skills.sh` enforces every rule: argv-ban,
Don't-block presence, dotfile-read refusal, and per-broker AST walks
(e.g. `auth: creds` requires a `credbroker` resolver import —
`from credbroker import …`; the legacy `from .credentials_shim import …`
is still recognized).

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
[how-to](../guides/how-to/add-a-credentialed-skill.md#how-credbroker-reaches-syspath--the-layered-model)):

- **Vendored floor (zero-pip, user scope).** A user-scope install of the
  `credential-brokers` pack delivers a byte-faithful, stdlib-base copy of
  the package source to `~/.agentbundle/lib/credbroker/`, which every
  credentialed skill appends to `sys.path` at **lowest** precedence — so a
  no-repo install resolves Tier-1/2/3 with no pip. The floor is drift-gated
  byte-for-byte against `packages/credbroker/credbroker/` — **one shared
  copy**, not the N-per-skill projection the shim used.
- **pip (corporate / PyPI).** A `pip install credbroker` (internal index,
  local wheel, or PyPI) lands in site-packages, which precedes the floor on
  `sys.path` — so it wins and unlocks the encrypted `[crypto]` vault.

The `credentials_shim` source is **kept** at
[`packs/credential-brokers/.apm/shared-libs/credentials_shim.py`](../../packs/credential-brokers/.apm/shared-libs/credentials_shim.py),
but only as the companion shim that rides the `adapter-root-bins` →
`~/.agentbundle/bin/` projection for `sso-broker.py`; no consumer skill
imports it for `creds` resolution any more.

## The three tiers

| Tier | Storage | Use case |
| --- | --- | --- |
| **Tier 1** | `<NAMESPACE>_<KEY>` env var (`JIRA_API_TOKEN`, `JIRA_BASE_URL`, …) | CI runners, wrapper scripts that inject secrets per-command. |
| **Tier 2** | OS keyring (macOS Keychain, Windows Credential Manager) | Interactive developer machine. The default. |
| **Tier 3** | `~/.agentbundle/credentials.env`, mode `0600` + parent `0700` | Locked-down environments where Tier 2 isn't available; opt-in fallback. |

Linux libsecret is deferred to a v2 RFC; the loader falls through to
Tier 3 on Linux today.

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

## Setting up credentials

The `credential-setup` skill (shipped by the `credential-brokers` pack
and projected to `.claude/skills/credential-setup/`) replaces the
prior `agentbundle creds setup <namespace>` CLI. The skill:

- Reads the consumer's `references/creds-schema.toml` to know which
  keys to prompt for.
- Walks each key via `getpass` (token-shaped) or `input` (non-secret
  sibling like `BASE_URL`).
- Writes to the highest-available tier (Keychain → Credential Manager
  → dotfile), announces the chosen tier on stderr, and refuses to
  fall back to Tier 3 without `--allow-insecure-fallback`.

There is no `get` verb. The LLM is never given a tool that returns
cleartext. Anything that needs the token reads it via
`load_credentials` inside the primitive's own subprocess and writes
it to an outbound HTTP header.

To verify resolution, invoke the consumer skill's own `check` verb —
e.g. `python3 scripts/cli.py check` walks the same Tier 1 → 2 → 3
ladder and exits 0 when every declared key resolves.

## Per-primitive schema declaration

Every credentialed primitive ships
`references/creds-schema.toml` declaring its namespace and required
keys:

```toml
namespace = "JIRA"

[keys.API_TOKEN]
secret = true
description = "Atlassian API token"

[keys.BASE_URL]
secret = false
description = "https://<your-org>.atlassian.net"
```

The schema is what the `credential-setup` skill reads to know which
prompts to issue. Secret vs non-secret distinguishes which keys go
to keyring storage (secret) vs which go to the dotfile / env var
unconditionally (non-secret siblings like `BASE_URL`). A canonical
reference is
[`packs/atlassian/.apm/skills/jira/references/creds-schema.toml`](../../packs/atlassian/.apm/skills/jira/references/creds-schema.toml)
(`API_TOKEN` secret; `BASE_URL` / `EMAIL` non-secret).

## The substring trap

Refuse-guards inside a primitive's `cli.py` that **literally name**
the substring `.agentbundle/credentials.env` will trip the same
`conventions-check` lint that catches credential *reads*. The lint is
substring-shaped for backwards compatibility (a follow-up rewrites it
as an AST walk per the `credential-broker-contract` ROADMAP entry).

Compose path checks via basename + `Path.parts`, never the literal
full string:

```python
# Correct
parts = Path(suspect).parts
if "credentials.env" in parts and ".agentbundle" in parts:
    refuse(...)

# Tripped by the lint
if str(suspect) == ".agentbundle/credentials.env":
    refuse(...)
```

This rule applies to any primitive script (`cli.py`) that mentions the
dotfile defensively.

## Where to read next

- [`docs/specs/credential-broker-contract/spec.md`](../specs/credential-broker-contract/spec.md) —
  the four-broker contract.
- [`docs/rfc/0023-credential-manager-broker.md`](../rfc/0023-credential-manager-broker.md) —
  the `credbroker` library that replaced the projected shim for `auth: creds`
  (and its layered-delivery amendment); [`docs/specs/credbroker/spec.md`](../specs/credbroker/spec.md)
  + [`docs/specs/credbroker-user-scope/spec.md`](../specs/credbroker-user-scope/spec.md)
  are the implementing specs.
- [`docs/rfc/0013-credential-broker-contract.md`](../rfc/0013-credential-broker-contract.md) —
  the four-broker design rationale (the predecessor shim model).
- [`docs/specs/skill-secrets/spec.md`](../specs/skill-secrets/spec.md) —
  the predecessor spec (kept for historical context).
- [`docs/guides/explanation/credentialed-skills.md`](../guides/explanation/credentialed-skills.md) —
  the adopter-facing companion.
- [`docs/guides/how-to/add-a-credentialed-skill.md`](../guides/how-to/add-a-credentialed-skill.md) —
  the step-by-step procedure for authoring a new credentialed primitive.
