# credbroker

[![PyPI](https://img.shields.io/pypi/v/credbroker)](https://pypi.org/project/credbroker/)
[![Python](https://img.shields.io/pypi/pyversions/credbroker)](https://pypi.org/project/credbroker/)
[![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue)](https://github.com/eugenelim/agent-ready-repo#license)

**Resolve secrets for agent skills without leaking them to the model.**

`credbroker` is a standalone, pip-installable credential resolver. It reads a secret in-process, walks three tiers, and never lets a cleartext value cross a process boundary to the LLM. The core is stdlib-only, with no third-party dependency.

## Install

```bash
pip install credbroker              # stdlib-only core
pip install 'credbroker[crypto]'    # + encrypted-at-rest vault
```

## Use

`credbroker` is a plain Python library. It works in any program, agent, or skill — no framework and no agent-ready-repo install required.

Resolve a namespace's credentials in one call:

```python
from credbroker import load_credentials

# Keys are used verbatim. The namespace is upper-cased to compose the
# env / dotfile name: here, JIRA_BASE_URL and JIRA_API_TOKEN.
creds = load_credentials("jira", required_keys=["BASE_URL", "API_TOKEN"])

connect(creds.BASE_URL, token=creds.API_TOKEN)   # attribute access returns the value
```

A typical agent skill resolves its namespace once, up front, and fails loud if a secret is missing — so the agent surfaces a setup prompt instead of firing a half-filled request:

```python
from credbroker import load_credentials, CredentialsMissingError

def jira_session():
    try:
        creds = load_credentials("jira", required_keys=["BASE_URL", "API_TOKEN"])
    except CredentialsMissingError as exc:
        raise SystemExit(str(exc))   # clear setup guidance, no broken call
    return Session(creds.BASE_URL, token=creds.API_TOKEN)
```

The returned object is immutable, and its `repr` lists key names only. A stray `print(creds)` can't echo token bytes.

## How it resolves

`credbroker` walks three tiers and returns the first hit:

1. **Environment variable** — `JIRA_API_TOKEN`. Good for CI and ephemeral shells.
2. **OS keyring** — the platform's native secret store. macOS uses the Keychain. Windows uses Credential Manager. The backend is chosen at import time from `sys.platform`.
3. **Dotfile floor** — a `0600` dotfile, or an encrypted-at-rest vault with the `[crypto]` extra (Argon2id, then AES-256-GCM).

Linux and other platforms have no keyring tier. Resolution skips straight from the environment variable to the dotfile floor. Without `[crypto]`, that floor is the plaintext `0600` dotfile.

## Learn more

For local development, install from a repo clone: `pip install -e ./packages/credbroker`.

See the [full contract](https://github.com/eugenelim/agent-ready-repo/blob/main/docs/specs/credbroker/spec.md) and [RFC-0023](https://github.com/eugenelim/agent-ready-repo/blob/main/docs/rfc/0023-credential-manager-broker.md) for the rationale.
