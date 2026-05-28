# Template: credentialed-skill `auth: creds`

For primitives whose credential is a static token resolved through the
three-tier model (env → OS keychain → 0600 dotfile floor) per RFC-0006.
The `credential-brokers` pack projects `credentials_shim.py` (plus the
per-platform Tier-2 backends `_keychain_macos.py` and
`_credman_windows.py`) into your skill's `scripts/` directory on the
next `make build-self` run. Copy everything below the horizontal rule
verbatim into your skill's `SKILL.md` body. Replace `<your-skill-name>`,
`<service>`, `<namespace>`, `<KEY>` placeholders; leave the rest
unchanged. The lint (`tools/lint-credentialed-skills.sh`) checks for
the verbatim phrases inside the `### Security rules (non-negotiable)`
section and verifies your `scripts/` imports the shim.

> **After saving your `SKILL.md`, run `make build-self`** before
> running any test that imports `credentials_shim`. The build pipeline
> projects `credentials_shim.py`, `_keychain_macos.py`, and
> `_credman_windows.py` into your skill's `scripts/` directory only
> after it sees `auth: creds` in your frontmatter; without that step
> the import fails with `ModuleNotFoundError`.

Frontmatter shape:

```yaml
---
name: <your-skill-name>
description: <what triggers it>
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds
  namespace: <namespace>
  keys: ["<KEY>"]
---
```

Schema at `<skill-dir>/references/creds-schema.toml`:

```toml
[namespace]
name = "<namespace>"

[[namespace.keys]]
name = "<KEY>"
label = "<service> API token"
secret = true
```

---

# Skill: <your-skill-name>

<one-line description of what the skill helps the user accomplish>

## How this skill works

This skill calls the `<service>` API via the credentialed primitive
at `scripts/cli.py`. The primitive resolves credentials via the
vendored `credentials_shim` (env → OS keychain → 0600 dotfile floor)
inside its own process. The LLM never sees the cleartext token as a
tool argument.

### Security rules (non-negotiable)

- Secrets live only in `~/.agentbundle/credentials.env`
  (mode 0600 on POSIX; DACL-restricted on Windows), the OS keyring,
  or process environment variables.
  **Never** read that file, print it, or echo the token.
- **Never** put the token on the command line. The primitive
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and exits — do not work around it.
- If `check` exits with the "missing credentials" code, tell the
  user to run the `credential-setup` skill themselves. It's
  interactive — do not run it for them.

## Usage

The primitive's Python entry point imports the projected sibling.
Two boilerplate blocks are non-negotiable in any credentialed CLI:

```python
import sys
from pathlib import Path

# Bootstrap when invoked as ``python scripts/cli.py`` — Python sets
# ``__package__`` to None for file-path invocation, which breaks the
# ``from .credentials_shim import …`` line below. Gated on
# ``__spec__ is None`` so the block only fires for true file-path
# invocation; an importlib-based test harness is responsible for
# its own package context.
if __package__ in (None, "") and __spec__ is None:
    _here = Path(__file__).resolve().parent
    sys.path.insert(0, str(_here.parent))
    __package__ = _here.name

from .credentials_shim import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)

creds = load_credentials("<namespace>", required_keys=["<KEY>"])
token = creds.<KEY>  # never printed, never echoed
```

Invoke the primitive via `subprocess.run([sys.executable,
"scripts/cli.py", "<verb>", ...])`. The primitive resolves
credentials inside its own process and constructs the API call
without surfacing the token to the LLM. The `__package__` bootstrap
makes the documented file-path invocation work under both project-
scope and user-scope install layouts (a flat `scripts/` dir with no
`__init__.py`).
