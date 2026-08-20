# AGENTS.md — `packages/credbroker/`

Applies to `packages/credbroker/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Package boundary

`credbroker` is a stdlib-first credential resolver. It resolves env, OS-keyring,
then dotfile/vault credentials in-process and never passes cleartext to an LLM.

## Package-specific traps

- Platform keyring calls require platform guards; unsupported systems continue to
  the next resolver tier.
- The optional `[crypto]` extra must be skipped gracefully when unavailable.
- Vault tests must redirect their home and vault paths to test fixtures.
- In credbroker tests, use `tmp_path` — or `tmp_path_factory.mktemp()` for autouse
  fixtures — never `tempfile.mkdtemp()`, literal `/tmp`, or direct `HOME` reads.
- Use `monkeypatch` to direct resolver environments; guard symlink setup with
  `OSError` skips where the platform cannot provide it.

## Essential commands

```bash
python3 -m pytest packages/credbroker/tests/ -q
```

## Deeper pointers

Resolver implementation and test fixtures own backend-specific behavior.
