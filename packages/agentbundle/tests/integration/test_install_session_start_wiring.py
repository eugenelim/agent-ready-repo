"""T1 of wire-session-start-hook spec — construction test.

Stages a synthetic minimal pack inside a tmp catalogue and asserts that
`install.run(...)` with `--emit-install-routes` compiles the wiring TOML into
Claude Code's nested SessionStart schema. At **repo scope**, that opt-in
produces a dist-tree Claude-plugin layout, so the compiled hook lands
in `<target>/claude-plugins/<pack>/.claude-plugin/plugin.json`
(the flat `<target>/.claude/...` shape is only produced at user scope,
which this spec doesn't cover).

Synthetic — not the real `packs/core/` — so the assertion compresses
the invariant "any v0.2 pack that ships this wiring TOML, installed at
repo scope, produces this settings shape." The real-core smoke check
lives in `test_install_core_smoke.py`.

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
version = "0.18"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo", "user"]
user-scope-hooks = true
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
    (pack / "pack.toml").write_text(PACK_TOML, encoding="utf-8", newline="\n")
    # The claude-plugins route requires a source manifest as well as
    # user-admitting scopes (docs/specs/claude-plugin-route-scope § The derived
    # set, condition 2). Without it this pack produces no dist-tree output and
    # the wiring assertion below has nothing to read.
    claude_plugin = pack / ".claude-plugin"
    claude_plugin.mkdir(parents=True)
    (claude_plugin / "plugin.json").write_text(
        '{\n  "name": "test-core",\n  "version": "0.1.0",\n'
        '  "description": "wiring-shape fixture"\n}\n',
        encoding="utf-8",
        newline="\n",
    )
    apm = pack / ".apm"
    (apm / "hooks").mkdir(parents=True)
    # Empty stub: hook-body projection is direct-file; content doesn't
    # matter for the wiring-shape assertion.
    (apm / "hooks" / "session-start.py").write_text("", encoding="utf-8", newline="\n")
    (apm / "hook-wiring").mkdir()
    (apm / "hook-wiring" / "session-start.toml").write_text(
        WIRING_TOML, encoding="utf-8", newline="\n"
    )


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

    rc, _stdout, stderr = _install({
        "pack": "test-core",
        "catalogue": str(cat),
        "output": str(target),
        "scope": None,
        "force": False,
        "emit_install_routes": True,
    })
    assert rc == 0, f"install failed: {stderr}"

    plugin_root = target / "claude-plugins" / "test-core"
    plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
    assert plugin_json.exists(), f"plugin.json not written under {plugin_root}"
    data = json.loads(plugin_json.read_text(encoding="utf-8"))

    # SessionStart has the unconditional install marker first, then authored wiring.
    assert "hooks" in data and "SessionStart" in data["hooks"], (
        f"hooks.SessionStart missing from settings: {data}"
    )
    entries = data["hooks"]["SessionStart"]
    assert len(entries) == 2, f"expected marker + authored SessionStart, got {entries!r}"

    outer = entries[1]
    # Pins the matcher-absence semantic (fires on all session types:
    # startup / resume / clear). Guards against a future TOML edit
    # accidentally narrowing scope by adding `matcher = "startup"`.
    assert outer.get("matcher", "") == "", (
        f"outer entry must omit matcher (or have empty matcher); got {outer!r}"
    )

    # Inner `hooks` array shape: one element with type=command and the
    # literal command string Claude Code expects.
    inner = outer.get("hooks", [])
    assert len(inner) == 1, f"expected 1 inner hook, got {inner!r}"
    assert inner[0]["type"] == "command", f"inner hook type must be 'command'; got {inner[0]!r}"
    assert inner[0]["command"] == (
        'python "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.py"'
    ), (
        f"inner hook command mismatch; got {inner[0]!r}"
    )
    assert (plugin_root / "hooks" / "session-start.py").is_file()
    assert not (plugin_root / ".claude").exists()
