"""T6: integration coverage for ``merge-into-agent-json`` against the
``kiro-user-hooks`` fixture (user scope).

Same shape as the repo-scope test, except ``$HOME`` is redirected to
a ``tmp_path`` and the agent JSON lands under
``$HOME/.kiro/agents/<agent>.json`` per RFC-0005 § `[adapter.kiro.scope]`.

AC coverage: AC18 (dispatchability shape — `sh -c "$command"` resolves
the projected hook body), plus the same AC15/AC19 shapes the repo
test pins.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES = REPO_ROOT / "packages" / "agentbundle" / "tests" / "fixtures" / "packs"
KIRO_USER_HOOKS = FIXTURES / "kiro-user-hooks"


def _load_wiring_tomls(pack_path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    wiring_dir = pack_path / ".apm" / "hook-wiring"
    if wiring_dir.exists():
        for entry in sorted(wiring_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".toml":
                out[entry.stem] = tomllib.loads(entry.read_text(encoding="utf-8"))
    return out


class KiroUserHooksFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self._env_patch = patch.dict(os.environ, {"HOME": str(self.home)})
        self._env_patch.start()
        self.addCleanup(self._env_patch.stop)

        # Pre-seed the user-scope agent JSON (T7's pipeline-ordering
        # invariant: agent projects before wiring). Place under the
        # redirected $HOME so the test does not touch the developer's
        # real ~/.kiro/.
        self.agent_json = self.home / ".kiro" / "agents" / "reviewer.json"
        self.agent_json.parent.mkdir(parents=True, exist_ok=True)
        self.agent_json.write_text(
            json.dumps(
                {"name": "reviewer", "description": "Reviews pending work."},
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )

    def test_user_scope_round_trip(self) -> None:
        from agentbundle.build.projections.merge_into_agent_json import (
            project,
            unproject,
        )

        wiring = _load_wiring_tomls(KIRO_USER_HOOKS)
        owned = project(self.agent_json, "kiro-user-hooks", wiring)
        self.assertEqual(owned, [("agentSpawn", "kiro-user-hooks:on-spawn")])

        data = json.loads(self.agent_json.read_text(encoding="utf-8"))
        self.assertEqual(data["hooks"]["agentSpawn"][0]["id"], "kiro-user-hooks:on-spawn")

        unproject(self.agent_json, owned)
        data = json.loads(self.agent_json.read_text(encoding="utf-8"))
        self.assertNotIn("agentSpawn", data.get("hooks", {}))

    def test_no_writes_outside_redirected_home(self) -> None:
        """AC29 shape: every write lands inside the tmp-scoped $HOME."""
        from agentbundle.build.projections.merge_into_agent_json import project

        wiring = _load_wiring_tomls(KIRO_USER_HOOKS)
        project(self.agent_json, "kiro-user-hooks", wiring)
        # The only artifact under the redirected $HOME is the agent JSON.
        artifacts = sorted(
            p.relative_to(self.home).as_posix()
            for p in self.home.rglob("*")
            if p.is_file()
        )
        self.assertEqual(artifacts, [".kiro/agents/reviewer.json"])

    def test_dispatchable_command_after_merge(self) -> None:
        """AC18: the projected hook entry's `command` field must
        dispatch via `sh -c "$command"` from any working directory.
        T8b's resolver substitutes `$HOOK_BODY_PATH` with the resolved
        absolute path; we simulate that here by substituting the
        placeholder in the wiring before merge, then merging, then
        reading the merged `command` back and dispatching it. This
        closes the loop that AC18 demands: the byte path running
        through is `wiring TOML → merge → merged JSON → sh -c → exit 0`.
        """
        from agentbundle.build.projections.merge_into_agent_json import project

        # Create a concrete hook body the substituted command will dispatch.
        hook_body = self.tmp / "stub.sh"
        hook_body.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        hook_body.chmod(0o755)

        # Simulate T8b's resolver: substitute the placeholder in the
        # wiring before passing to project().
        wiring = _load_wiring_tomls(KIRO_USER_HOOKS)
        for body in wiring.values():
            for event_entries in body.get("hooks", {}).values():
                for entry in event_entries:
                    if entry.get("command") == "$HOOK_BODY_PATH":
                        entry["command"] = str(hook_body)

        project(self.agent_json, "kiro-user-hooks", wiring)

        # Read the merged command back from the on-disk agent JSON and
        # dispatch it. Run from an arbitrary cwd (the tmp root, not the
        # hook body's directory) to satisfy AC18's "from any working
        # directory" clause.
        data = json.loads(self.agent_json.read_text(encoding="utf-8"))
        command = data["hooks"]["agentSpawn"][0]["command"]
        self.assertEqual(command, str(hook_body))
        result = subprocess.run(
            ["sh", "-c", command],
            cwd=str(self.tmp),
            capture_output=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"merged command did not dispatch: stderr={result.stderr.decode()}",
        )


if __name__ == "__main__":
    unittest.main()
