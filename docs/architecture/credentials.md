# Credentials

The secret-handling subsystem inside `packages/agentbundle/`. Defines how a
credentialed primitive — a `jira`, `figma`, or `confluence-publisher` CLI —
acquires a token at runtime without ever putting it on argv, in env-var
echoes, or in agent transcripts. Authoritative spec:
[`docs/specs/skill-secrets/spec.md`](../specs/skill-secrets/spec.md);
*why*: [RFC-0006](../rfc/0006-skill-secrets-storage.md).

## Two-layer architecture

The repo distinguishes two things that often get conflated:

- **Skills** never read credentials. They drive UX, planning, and shell-out
  patterns, but they don't talk to authenticated APIs themselves.
- **Credentialed primitives** read credentials. Every primitive declares
  its class via `SKILL.md` frontmatter:

  ```yaml
  metadata:
    credentialed: true
    primitive-class: credentialed-cli   # or: mcp-server
  ```

  - `credentialed-cli` — a Python module invoked via `python -m <pkg>` that
    calls `load_credentials` internally. **Refuses** any value-shaped
    credential flag (`--token`, `--api-key`, `--bearer`, `--pat`,
    `--password`).
  - `mcp-server` — an MCP server holding the secret. May accept
    *header-naming* flags (`--bearer-header`, `--auth-header`) but never
    value-shaped flags.

`conventions-check` enforces both rules: the argv-ban lint catches
value-shaped flags in primitive `cli.py` files, and the
missing-"Don't"-block lint catches credentialed-CLI skills that don't carry
the verbatim refuse-block from the credentialed-skill template.

## The loader

The public surface is one function in
[`agentbundle/credentials.py`](../../packages/agentbundle/agentbundle/credentials.py)
(a shim re-export of `agentbundle/creds/loader.py`):

```python
from agentbundle.credentials import load_credentials

creds = load_credentials(
    namespace="JIRA",
    required_keys=["API_TOKEN", "BASE_URL", "EMAIL"],
)
creds.API_TOKEN  # str
```

Returns an immutable dataclass; attribute access on a key not in
`required_keys` raises `AttributeError`. Single responsibility:
*resolve* — schema validation is the `agentbundle creds` verb's job, not
the loader's. The loader walks **first-hit-wins per key** (a key resolved
at Tier 1 is not re-checked at lower tiers; mixing tiers across keys
within one namespace is permitted).

## The three tiers

| Tier | Storage | Use case |
| --- | --- | --- |
| **Tier 1** | `<NAMESPACE>_<KEY>` env var (`JIRA_API_TOKEN`, `JIRA_BASE_URL`, …) | CI runners, wrapper scripts that inject secrets per-command. |
| **Tier 2** | OS keyring (macOS Keychain, Windows Credential Manager) | Interactive developer machine. The default. |
| **Tier 3** | `~/.agentbundle/credentials.env`, mode `0600` + parent `0700` | Locked-down environments where Tier 2 isn't available; opt-in fallback. |

Linux libsecret is deferred to a v2 RFC; the loader falls through to
Tier 3 on Linux today.

### Tier 2 backends — stdlib only

- **macOS** ([`creds/_keychain_macos.py`](../../packages/agentbundle/agentbundle/creds/_keychain_macos.py)) —
  `subprocess.run(["/usr/bin/security", ...])`. The write path passes the
  token via **child stdin**, never argv. Service = `"agentbundle"`,
  account = `"<namespace>:<key>"`.
- **Windows** ([`creds/_credman_windows.py`](../../packages/agentbundle/agentbundle/creds/_credman_windows.py)) —
  `ctypes` against `advapi32.{CredReadW, CredWriteW, CredDeleteW, CredFree}`.
  In-process, no subprocess. `CRED_TYPE_GENERIC`,
  `CRED_PERSIST_LOCAL_MACHINE`, target-name
  `agentbundle:<namespace>:<key>`.

The backend label is selected at module-load time per `sys.platform`.
A documented set of Win32 hard-fail codes (see
[`_credman_windows.py`](../../packages/agentbundle/agentbundle/creds/_credman_windows.py)
for the current list) raises `Tier2HardFailError` and does **not** fall
through to Tier 3. Silent degradation is the security smell, not the
dotfile.

### Tier 3 — the dotfile

A stdlib `.env` parser (`parse_env_file` in
[`creds/loader.py`](../../packages/agentbundle/agentbundle/creds/loader.py))
handles `KEY=value`, quoted values, and `#` comments. It rejects `export ` prefix, variable expansion, and
multi-line values — `.env` is not bash. POSIX: enforces mode `0600` on the
file and `0700` on `~/.agentbundle/`. Windows: DACL-verified via `icacls`.
`PermissiveAclError` on either failure.

## The `creds` CLI verb

Four subcommands, deliberately **no `get`**:

| Subcommand | Effect |
| --- | --- |
| `creds setup <namespace>` | Interactive `getpass` prompt; writes to highest-available tier; announces the chosen tier on stderr; exits non-zero if it had to fall back to Tier 3 without `--allow-insecure-fallback`. |
| `creds check <namespace>` | Reports presence and resolved tier per key; never prints the secret. |
| `creds where <namespace>` | Resolves to a path (Tier 3) or a keyring service/account (Tier 2) — for diagnostics. |
| `creds rm <namespace>` | Removes the namespace from the active tier. |

`get` is the design hinge: the LLM is never given a tool that returns
cleartext. Anything that needs the token reads it via `load_credentials`
inside the primitive's own subprocess and writes it to an outbound HTTP
header.

## Per-primitive schema declaration

Every credentialed primitive ships
`references/creds-schema.toml` declaring its namespace and required keys:

```toml
namespace = "JIRA"

[keys.API_TOKEN]
secret = true
description = "Atlassian API token"

[keys.BASE_URL]
secret = false
description = "https://<your-org>.atlassian.net"
```

The schema is what `creds setup` reads to know which prompts to issue.
Secret vs non-secret distinguishes which keys go to keyring storage
(secret) vs which go to the dotfile / env var unconditionally
(non-secret siblings like `BASE_URL`). The canonical reference is
[`packs/core/.apm/skills/example-credentialed-skill/references/creds-schema.toml`](../../packs/core/.apm/skills/example-credentialed-skill/references/creds-schema.toml).

## The AC26(c) substring trap

Refuse-guards inside a primitive's `cli.py` that **literally name** the
substring `.agentbundle/credentials.env` will trip the same
`conventions-check` lint that catches credential *reads*. The lint is
substring-shaped, not AST-shaped, and that's a feature: it catches both
real reads and "well-meaning" string interpolations that point at the
dotfile.

Compose path checks via basename + `Path.parts`, never the literal full
string:

```python
# Correct
parts = Path(suspect).parts
if "credentials.env" in parts and ".agentbundle" in parts:
    refuse(...)

# Tripped by the lint
if str(suspect) == ".agentbundle/credentials.env":
    refuse(...)
```

This rule applies to `creds/loader.py` itself and to any primitive script
that mentions the dotfile defensively. The trap is named for the
acceptance criterion in
[`docs/specs/skill-secrets/spec.md`](../specs/skill-secrets/spec.md#acceptance-criteria)
that introduced it.

## Where to read next

- [`docs/specs/skill-secrets/spec.md`](../specs/skill-secrets/spec.md) —
  the authoritative spec.
- [`docs/rfc/0006-skill-secrets-storage.md`](../rfc/0006-skill-secrets-storage.md) —
  the design rationale.
- [`docs/guides/explanation/credentialed-skills.md`](../guides/explanation/credentialed-skills.md) —
  the adopter-facing companion.
- [`docs/guides/how-to/add-a-credentialed-skill.md`](../guides/how-to/add-a-credentialed-skill.md) —
  how to author a new credentialed primitive (via the
  `add-credentialed-skill` skill in `core`).
