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
import shutil
from pathlib import Path

from agentbundle.commands import install

REPO_ROOT = Path(__file__).resolve().parents[4]
REAL_CORE = REPO_ROOT / "packs" / "core"


def test_real_core_install_writes_session_start_binding(tmp_path):
    """Real `packs/core/` install produces the dist-tree settings file
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

    # `core` declares allowed-scopes = ["repo"], so it does not reach the
    # user-scope claude-plugins route (docs/specs/claude-plugin-route-scope).
    # The route emits only the marketplace envelope; core's own subtree — and
    # therefore the dist-tree settings file this test used to read — is absent
    # by design. The APM route is unfiltered and still carries core's wiring,
    # which is what this test now pins.
    plugins_dir = target / "claude-plugins"
    assert not (plugins_dir / "core").exists(), (
        "core is repo-only and must not reach the claude-plugins route"
    )
    wiring = target / "apm" / "core" / ".apm" / "hook-wiring" / "session-start.toml"
    assert wiring.exists(), f"APM-route wiring missing at {wiring}"
    body = wiring.read_text(encoding="utf-8")
    assert "[[hooks.SessionStart]]" in body
    assert "tools/hooks/session-start.py" in body
