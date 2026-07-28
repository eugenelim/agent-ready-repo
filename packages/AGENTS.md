# AGENTS.md — `packages/`

Guidance for developing Python packages in this directory. The primary package is `agentbundle`
(`packages/agentbundle/`). This file covers package-specific rules; catalogue and skill authoring
guidance lives in [`packs/AGENTS.md`](../packs/AGENTS.md).

## Version bump rule

Non-cosmetic package changes require bumping `version.py` and `pyproject.toml`. CLI-surface changes also require a PyPI release — see [`packages/AGENTS.local.md`](AGENTS.local.md#release-coupling) for what always requires one.

## Install-test coverage rule

Tests that exercise an on-disk projection layout, the per-pack orphan scanner, or the install
handler's adapter-resolution path **must parametrize over every shipped adapter** — not just the
default. Each adapter projects to a different directory layout and the per-pack scanner's
primitive-name heuristic interacts differently with each shape.

Opt-out: tests scoped to adapter-independent logic (scope-resolution, dependency gates,
state-accumulation) may skip parametrization; the test's docstring must say so.

**Reference shape:** `packages/agentbundle/tests/integration/test_multi_pack_install.py`.
`packages/agentbundle/agentbundle/_data/adapter.toml` is the source of truth for which adapters ship;
the test module derives `_SHIPPED_ADAPTERS` from it via `scope.shipped_adapters_from_contract()` —
adding a new `[adapter.<name>]` table expands every parametrized test in the same PR.

## Windows / cross-OS compatibility

All new code in `packages/` must be Windows-clean.

- **Encoding:** `Path.read_text()` / `Path.write_text()` / `open()` for text must always pass
  `encoding="utf-8"`. Exception: `read_bytes()` / `write_bytes()` are inherently correct.
- **Symlinks:** wrap `os.symlink()` in `try/except OSError: pytest.skip("symlinks not available")`.
- **POSIX-only assertions:** wrap inode checks (`st_ino`), nanosecond mtimes (`st_mtime_ns`), and
  permission-bit assertions in `if sys.platform != "win32":`. Gate `os.chmod()` with `if os.name == "posix":`.
- **Paths:** use `pathlib.Path` or `os.path.join`. No string concatenation with `/`, no
  `os.environ["HOME"]`, no hardcoded `/tmp`.
- **Subprocess:** list form only, never `shell=True`. Do not invoke `which`, `grep`, `find`, `sed`,
  `awk`, `make`, `sh`, or `bash` via subprocess in portable code.
- **User-scope root isolation in tests:** set `AGENTBUNDLE_USER_ROOT` alongside `HOME` so
  `resolve_user_root()` uses the temp path on all platforms (Windows `expanduser()` ignores
  monkeypatched env vars). See `tests/integration/test_adapt_dual_scope.py` for the pattern.

## Test conventions

- Use `tmp_path` (pytest fixture), not `tempfile.mkdtemp()`.
- Use `pytest.MonkeyPatch` (`monkeypatch` fixture) for environment patching; do not use
  `unittest.mock.patch.dict` in new tests (use it only when extending existing unittest-style tests).
- Autouse fixtures: use `tmp_path_factory.mktemp()`, not `tmp_path`, to avoid polluting test
  isolation with shared state across fixture scopes.
- The test roots are `tests/unit/` (pure logic, no disk) and `tests/integration/` (full-stack,
  disk writes, subprocess). New tests go in the appropriate root.
