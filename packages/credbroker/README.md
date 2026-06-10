# credbroker

A standalone, pip-installable credential resolver for credentialed agent
skills. Resolves secrets **in-process** through three tiers —
environment variable → OS keyring → a `0600` dotfile floor — and never lets a
cleartext value cross a process boundary to the LLM.

> Status: **published on PyPI** — `credbroker 0.1.0` (2026-06-10, RFC-0023).
> Install from PyPI (`pip install credbroker`, or `credbroker[crypto]` for the
> encrypted vault), or from the repo path for local development
> (`pip install -e ./packages/credbroker`).

## Install

```bash
pip install credbroker                          # stdlib-only core, from PyPI
pip install 'credbroker[crypto]'                # + encrypted-at-rest vault

# Or work against a repo clone — an editable install for local development
# (no PyPI needed; same import, the repo copy wins on sys.path):
pip install -e ./packages/credbroker
pip install -e './packages/credbroker[crypto]'
```

The core has **no third-party dependency**. The `[crypto]` extra adds
`cryptography` + `argon2-cffi` for an encrypted-at-rest vault at the floor tier;
without it, resolution degrades to the keyring/plaintext-dotfile floor.

## Use

```python
from credbroker import load_credentials

# Keys are used verbatim; only the namespace is upper-cased to compose the
# env / dotfile name (here: JIRA_BASE_URL, JIRA_API_TOKEN). Use upper-case keys.
creds = load_credentials("jira", required_keys=["BASE_URL", "API_TOKEN"])
```

See [`docs/specs/credbroker/spec.md`](../../docs/specs/credbroker/spec.md) for
the full contract and [RFC-0023](../../docs/rfc/0023-credential-manager-broker.md)
for the rationale.
