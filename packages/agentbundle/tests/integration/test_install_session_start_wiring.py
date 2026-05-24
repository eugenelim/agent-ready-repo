"""T1 of wire-session-start-hook spec — construction test for AC1/AC9.

Stages a synthetic minimal pack inside a tmp catalogue and asserts that
`install.run(...)` projects the wiring TOML into Claude Code's
nested SessionStart schema. At **repo scope**, `agentbundle install`
produces a dist-tree Claude-plugin layout, so the settings file lands
at `<target>/claude-plugins/<pack>/.claude/settings.local.json`
(the flat `<target>/.claude/...` shape is only produced at user scope,
which this spec doesn't cover).

Synthetic — not the real `packs/core/` — so the assertion compresses
the invariant "any v0.2 pack that ships this wiring TOML, installed at
repo scope, produces this settings shape." The real-core smoke check
lives in `test_install_core_smoke.py` (AC10).

Shape pinned: the nested form documented at
https://code.claude.com/docs/en/hooks. The outer entry has no
`matcher` field (or empty), and carries an inner `hooks` array whose
elements declare `type = "command"` and the literal command string.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
from pathlib import Path

from agentbundle.commands import install


PACK_TOML = """
[pack]
name = "test-core"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""

WIRING_TOML = """
[[hooks.SessionStart]]
hooks = [
  { type = "command", command = "python tools/hooks/session-start.py" },
]
"""


def _stage_synthetic_pack(catalogue_root: Path) -> None:
    """Build a minimal pack that ships the session-start wiring at repo scope.

    Mirrors `test_install_dual_scope._stage_pack` in spirit but inlined so the
    test reads as a self-contained construction check.
    """
    pack = catalogue_root / "packs" / "test-core"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(PACK_TOML, encoding="utf-8")
    apm = pack / ".apm"
    (apm / "hooks").mkdir(parents=True)
    # Empty stub: hook-body projection is direct-file; content doesn't
    # matter for the wiring-shape assertion.
    (apm / "hooks" / "session-start.py").write_text("", encoding="utf-8")
    (apm / "hook-wiring").mkdir()
    (apm / "hook-wiring" / "session-start.toml").write_text(WIRING_TOML, encoding="utf-8")


def _install(args_dict) -> tuple[int, str, str]:
    args = argparse.Namespace(**args_dict)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install.run(args)
    return rc, out.getvalue(), err.getvalue()


def test_install_writes_nested_session_start_binding(tmp_path):
    cat = tmp_path / "cat"
    _stage_synthetic_pack(cat)
    target = tmp_path / "repo"
    target.mkdir()

    rc, _stdout, stderr = _install(
        dict(
            pack="test-core",
            catalogue=str(cat),
            output=str(target),
            scope=None,
            force=False,
        )
    )
    assert rc == 0, f"install failed: {stderr}"

    # Repo-scope install produces the dist-tree Claude-plugin layout:
    # `<target>/claude-plugins/<pack-name>/.claude/settings.local.json`.
    settings = target / "claude-plugins" / "test-core" / ".claude" / "settings.local.json"
    assert settings.exists(), (
        f"settings.local.json not written under {target / 'claude-plugins' / 'test-core'}"
    )
    data = json.loads(settings.read_text(encoding="utf-8"))

    # SessionStart array has exactly one outer entry.
    assert "hooks" in data and "SessionStart" in data["hooks"], (
        f"hooks.SessionStart missing from settings: {data}"
    )
    entries = data["hooks"]["SessionStart"]
    assert len(entries) == 1, f"expected 1 SessionStart entry, got {entries!r}"

    outer = entries[0]
    # AC1 pins the matcher-absence semantic (fires on all session types:
    # startup / resume / clear). Guards against a future TOML edit
    # accidentally narrowing scope by adding `matcher = "startup"`.
    assert outer.get("matcher", "") == "", (
        f"outer entry must omit matcher (or have empty matcher); got {outer!r}"
    )

    # Inner `hooks` array shape: one element with type=command and the
    # literal command string Claude Code expects.
    inner = outer.get("hooks", [])
    assert len(inner) == 1, f"expected 1 inner hook, got {inner!r}"
    assert inner[0]["type"] == "command", (
        f"inner hook type must be 'command'; got {inner[0]!r}"
    )
    assert inner[0]["command"] == "python tools/hooks/session-start.py", (
        f"inner hook command mismatch; got {inner[0]!r}"
    )
