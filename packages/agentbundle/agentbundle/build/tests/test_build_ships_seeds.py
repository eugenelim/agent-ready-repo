"""T5 (issue #190 Finding 1, dist half): the per-pack APM and Claude-plugin
build recipes ship the pack's seeds/ inside the artifact.

RFC-0001 §595 (APM) + §281-284 (both routes) require a pack's governance seeds
to travel inside the published artifact so the content is available on every
install route. The build never copied seeds/; this test drives the real build
pipeline against a seed-bearing temp pack and asserts seeds land in both
per-pack outputs. (`dist/` is gitignored, so this is verified by test, not by a
committed snapshot.)
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]


def _make_seed_pack(packs_dir: Path) -> None:
    pack = packs_dir / "seedpack"
    skill = pack / ".apm" / "skills" / "demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: demo\ndescription: A demo skill for the seed-ship build test.\n---\n\nBody.\n",
        encoding="utf-8",
    )
    (pack / "pack.toml").write_text(
        '[pack]\nname = "seedpack"\nversion = "0.1.0"\ndescription = "seed-ship test pack."\n',
        encoding="utf-8",
    )
    (pack / ".claude-plugin").mkdir()
    (pack / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "seedpack", "version": "0.1.0", "description": "seed-ship test pack."}) + "\n",
        encoding="utf-8",
    )
    docs = pack / "seeds" / "docs"
    docs.mkdir(parents=True)
    (pack / "seeds" / "AGENTS.md").write_text("# seedpack agents\n", encoding="utf-8")
    (docs / "CHARTER.md").write_text("# seedpack charter\n", encoding="utf-8")


class BuildShipsSeedsTests(unittest.TestCase):
    def test_seeds_shipped_in_both_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _make_seed_pack(packs_dir)
            out = tmp_path / "dist"

            result = subprocess.run(
                [
                    sys.executable, "-m", "agentbundle.build", "build",
                    "--packs-dir", str(packs_dir),
                    "--output-dir", str(out),
                ],
                capture_output=True, text=True, cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            # Claude-plugin artifact carries seeds/.
            plugin = out / "claude-plugins" / "seedpack" / "seeds"
            self.assertTrue((plugin / "AGENTS.md").exists(), msg=result.stderr)
            self.assertTrue((plugin / "docs" / "CHARTER.md").exists())

            # APM artifact carries seeds/.
            apm = out / "apm" / "seedpack" / "seeds"
            self.assertTrue((apm / "AGENTS.md").exists())
            self.assertTrue((apm / "docs" / "CHARTER.md").exists())


if __name__ == "__main__":
    unittest.main()
