# packages/credbroker — agent context

`credbroker` is a standalone, stdlib-only credential resolver. It reads secrets
in-process, walks three tiers (env variable → OS keyring → dotfile/vault), and
never lets cleartext cross a process boundary to the LLM.

## Package structure

| Path | Purpose |
|------|---------|
| `credbroker/_core.py` | Three-tier resolution logic |
| `credbroker/_keychain_macos.py` | macOS Keychain backend |
| `credbroker/_credman_windows.py` | Windows Credential Manager backend |
| `credbroker/_vault.py` | Encrypted-at-rest vault (requires `[crypto]` extra) |
| `credbroker/_sso.py` | SSO web-session cookie resolver |
| `tests/unit/` | Pure logic, no disk |
| `tests/integration/` | Full-stack, disk writes, subprocess |

## Windows / cross-OS compatibility

All new code must be Windows-clean:

- **Encoding:** `Path.read_text()` / `Path.write_text()` / `open()` must pass `encoding="utf-8"`.
- **Paths:** use `pathlib.Path`. No hardcoded `/tmp` or `os.environ["HOME"]`.
- **Subprocess:** list form only, never `shell=True`.
- **Platform guards:** wrap keychain and credential-manager calls in `if sys.platform == ...` guards —
  Linux has no keyring tier and skips straight to the dotfile floor.
- **Symlinks:** wrap `os.symlink()` in `try/except OSError: pytest.skip(...)`.

## Test conventions

- Use `tmp_path` (pytest fixture), not `tempfile.mkdtemp()`.
- Use `pytest.MonkeyPatch` for environment patching.
- The `[crypto]` extra is optional; tests that require it should skip gracefully when
  `cryptography` is absent.
- Vault tests must not write to the real user home; always redirect via `tmp_path`.
