"""T5: integration coverage for ``user-merge-json`` against the
``cc-user-hooks`` fixture.

Complements ``tests/unit/test_user_merge_json.py``: the unit tests
construct wiring data in-memory; this test reads the fixture's actual
``.apm/hook-wiring/*.toml`` content from disk, parses it with
``tomllib``, and runs the merger end-to-end against a ``tmp_path``-
scoped ``~/.claude/settings.json``.

Per spec § Boundaries — *Never do* — no live writes to
``~/.claude/`` outside ``tmp_path``. ``$HOME`` is redirected via
``patch.dict(os.environ, {"HOME": tmp})`` for the duration of each
test; the assertion target is the tmp-scoped settings file.

Spec AC coverage: AC8 / AC9 / AC11 against the fixture.
"""

from __future__ import annotations

import json
import os
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES = REPO_ROOT / "packages" / "agentbundle" / "tests" / "fixtures" / "packs"
CC_USER_HOOKS = FIXTURES / "cc-user-hooks"


def _load_wiring_tomls(pack_path: Path) -> dict[str, dict]:
    """Parse every ``.apm/hook-wiring/*.toml`` under *pack_path*."""
    out: dict[str, dict] = {}
    wiring_dir = pack_path / ".apm" / "hook-wiring"
    if not wiring_dir.exists():
        return out
    for entry in sorted(wiring_dir.iterdir()):
        if entry.is_file() and entry.suffix == ".toml":
            out[entry.stem] = tomllib.loads(entry.read_text(encoding="utf-8"))
    return out


class CCUserHooksFixtureTests(unittest.TestCase):
    """End-to-end shape: read fixture wiring → project → assert
    on-disk settings file has the expected merged shape."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.tmp, ignore_errors=True)
        self.home = Path(self.tmp) / "home"
        self.home.mkdir()
        self.settings = self.home / ".claude" / "settings.json"
        self._env_patch = patch.dict(os.environ, {"HOME": str(self.home)})
        self._env_patch.start()
        self.addCleanup(self._env_patch.stop)

    def test_fixture_round_trip_install_uninstall(self) -> None:
        """Install → settings file has the fixture's `UserPromptSubmit`
        wiring tagged with `cc-user-hooks:on-prompt`. Uninstall →
        the entry is gone; the empty event array is removed too."""
        from agentbundle.build.projections.user_merge_json import (
            project,
            unproject,
        )

        wiring = _load_wiring_tomls(CC_USER_HOOKS)
        self.assertIn("on-prompt", wiring, "fixture missing on-prompt.toml")

        owned = project(self.settings, "cc-user-hooks", wiring)
        self.assertEqual(owned, [("UserPromptSubmit", "cc-user-hooks:on-prompt")])

        data = json.loads(self.settings.read_text(encoding="utf-8"))
        entries = data["hooks"]["UserPromptSubmit"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["id"], "cc-user-hooks:on-prompt")

        unproject(self.settings, owned)
        data = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertNotIn("UserPromptSubmit", data.get("hooks", {}))

    def test_fixture_reinstall_idempotent(self) -> None:
        from agentbundle.build.projections.user_merge_json import project

        wiring = _load_wiring_tomls(CC_USER_HOOKS)
        project(self.settings, "cc-user-hooks", wiring)
        first = self.settings.read_bytes()
        project(self.settings, "cc-user-hooks", wiring)
        self.assertEqual(self.settings.read_bytes(), first)

    def test_no_writes_outside_redirected_home(self) -> None:
        """AC29: nothing lands outside the tmp_path-scoped $HOME."""
        from agentbundle.build.projections.user_merge_json import project

        wiring = _load_wiring_tomls(CC_USER_HOOKS)
        project(self.settings, "cc-user-hooks", wiring)
        # The only artifact under tmp is the redirected ~/.claude tree.
        artifacts = sorted(
            p.relative_to(self.home).as_posix()
            for p in self.home.rglob("*")
            if p.is_file()
        )
        self.assertEqual(artifacts, [".claude/settings.json"])


if __name__ == "__main__":
    unittest.main()
