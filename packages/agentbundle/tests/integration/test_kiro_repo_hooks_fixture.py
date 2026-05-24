"""T6: integration coverage for ``merge-into-agent-json`` against the
``kiro-repo-hooks`` fixture.

End-to-end: read the fixture's `.apm/hook-wiring/on-spawn.toml` with
`tomllib`, seed a `.kiro/agents/reviewer.json` (per RFC-0005's
pipeline-ordering invariant — the agent file must exist before
wiring runs; T7 will enforce this; here we simulate the pipeline by
pre-seeding), run the merger, assert the shape.

Per spec § Boundaries — *Never do* — no live writes to
`~/.kiro/agents/` outside tmp_path. The repo-scope variant works
against `tmp_path/.kiro/agents/<agent>.json`.

Spec AC coverage: AC15, AC19 against the fixture.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES = REPO_ROOT / "packages" / "agentbundle" / "tests" / "fixtures" / "packs"
KIRO_REPO_HOOKS = FIXTURES / "kiro-repo-hooks"


def _load_wiring_tomls(pack_path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    wiring_dir = pack_path / ".apm" / "hook-wiring"
    if wiring_dir.exists():
        for entry in sorted(wiring_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".toml":
                out[entry.stem] = tomllib.loads(entry.read_text(encoding="utf-8"))
    return out


class KiroRepoHooksFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        # Pre-seed the agent JSON the pipeline (T7) will produce. T6
        # consumes a pre-existing agent file.
        self.agent_json = self.tmp / ".kiro" / "agents" / "reviewer.json"
        self.agent_json.parent.mkdir(parents=True, exist_ok=True)
        self.agent_json.write_text(
            json.dumps(
                {"name": "reviewer", "description": "Reviews pending work."},
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )

    def test_fixture_round_trip_install_uninstall(self) -> None:
        from agentbundle.build.projections.merge_into_agent_json import (
            project,
            unproject,
        )

        wiring = _load_wiring_tomls(KIRO_REPO_HOOKS)
        self.assertIn("on-spawn", wiring, "fixture missing on-spawn.toml")

        owned = project(self.agent_json, "kiro-repo-hooks", wiring)
        self.assertEqual(owned, [("agentSpawn", "kiro-repo-hooks:on-spawn")])

        data = json.loads(self.agent_json.read_text(encoding="utf-8"))
        # Body keys preserved.
        self.assertEqual(data["name"], "reviewer")
        # Wiring merged.
        self.assertEqual(data["hooks"]["agentSpawn"][0]["id"], "kiro-repo-hooks:on-spawn")

        unproject(self.agent_json, owned)
        data = json.loads(self.agent_json.read_text(encoding="utf-8"))
        # Agent file remains; the wiring entries are gone.
        self.assertTrue(self.agent_json.exists())
        self.assertNotIn("agentSpawn", data.get("hooks", {}))
        self.assertEqual(data["name"], "reviewer")

    def test_fixture_reinstall_idempotent(self) -> None:
        from agentbundle.build.projections.merge_into_agent_json import project

        wiring = _load_wiring_tomls(KIRO_REPO_HOOKS)
        project(self.agent_json, "kiro-repo-hooks", wiring)
        first = self.agent_json.read_bytes()
        project(self.agent_json, "kiro-repo-hooks", wiring)
        self.assertEqual(self.agent_json.read_bytes(), first)


if __name__ == "__main__":
    unittest.main()
