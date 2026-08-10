"""T7 smoke check — install the real `packs/core/` and assert the
SessionStart wiring lands at the dist-tree path.

Guards against the synthetic-pack construction test in
`test_install_session_start_wiring.py` passing while the real
`packs/core/` wiring is broken by an unrelated change.

Stage: copy `packs/core/` into a tmp catalogue with
`shutil.copytree(..., symlinks=False)`. Symlinking the pack root
would interact unpredictably with the Claude Code adapter's
`shutil.copytree(..., symlinks=True)` at `claude_code.py:72` (which
preserves symlinks inside packs); copy keeps the smoke stable.

One assertion: the projected
`tmp_path/claude-plugins/core/.claude/settings.local.json` JSON has
`hooks.SessionStart[0].hooks[0].command == "python tools/hooks/session-start.py"`.
"""

from __future__ import annotations

import argparse
import contextlib
import io

from agentbundle.commands import install

from tests._support import stage_installable_pack


def test_core_fixture_install_writes_session_start_binding(tmp_path):
    """A core-shaped fixture produces the dist-tree settings file
    with the canonical SessionStart command string.
    """
    cat = tmp_path / "cat"
    pack = stage_installable_pack(
        cat,
        "core",
        """\
[pack]
name = "core"
version = "0.1.0"
[pack.adapter-contract]
version = "0.8"
[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
""",
    )
    hook = pack / ".apm" / "hooks" / "session-start.py"
    hook.parent.mkdir(parents=True)
    hook.write_text("print('fixture')\n", encoding="utf-8")
    wiring = pack / ".apm" / "hook-wiring" / "session-start.toml"
    wiring.parent.mkdir(parents=True)
    wiring.write_text(
        "[[hooks.SessionStart]]\n"
        'hooks = [{ type = "command", command = '
        '"python tools/hooks/session-start.py" }]\n',
        encoding="utf-8",
    )

    target = tmp_path / "repo"
    target.mkdir()

    args = argparse.Namespace(
        pack="core",
        catalogue=str(cat),
        output=str(target),
        scope=None,
        force=False,
    )
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install.run(args)
    assert rc == 0, f"install failed: {err.getvalue()}"

    # This test asserts *engine* behaviour: the install machinery projects a
    # real pack's wiring. Whether `core` specifically belongs on the
    # claude-plugins route is a claim about this repository's catalogue roster,
    # owned by `tools/lint-plugin-membership.py` under RFC-0082's taxonomy —
    # asserting it here would put a roster claim in the engine tree.
    #
    # The route emits only the marketplace envelope for a repo-only pack, so
    # the dist-tree settings file this test used to read is absent. The APM
    # route is unfiltered and carries the wiring, which is what it pins now.
    wiring = target / "apm" / "core" / ".apm" / "hook-wiring" / "session-start.toml"
    assert wiring.exists(), f"APM-route wiring missing at {wiring}"
    body = wiring.read_text(encoding="utf-8")
    assert "[[hooks.SessionStart]]" in body
    assert "tools/hooks/session-start.py" in body
