"""T7 / AC10 smoke check — install the real `packs/core/` and assert the
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
import json
import shutil
from pathlib import Path

from agentbundle.commands import install


REPO_ROOT = Path(__file__).resolve().parents[4]
REAL_CORE = REPO_ROOT / "packs" / "core"


def test_real_core_install_writes_session_start_binding(tmp_path):
    """AC10: real `packs/core/` install produces the dist-tree settings file
    with the canonical SessionStart command string.
    """
    assert REAL_CORE.exists(), f"real packs/core/ missing at {REAL_CORE}"

    # Copy (not symlink) the real pack into a tmp catalogue.
    cat = tmp_path / "cat"
    (cat / "packs").mkdir(parents=True)
    shutil.copytree(REAL_CORE, cat / "packs" / "core", symlinks=False)

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

    settings = target / "claude-plugins" / "core" / ".claude" / "settings.local.json"
    assert settings.exists(), (
        f"dist-tree settings file missing at {settings}"
    )
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert (
        data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        == "python tools/hooks/session-start.py"
    ), f"unexpected SessionStart command in {data!r}"
