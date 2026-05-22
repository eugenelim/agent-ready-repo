"""End-to-end pipeline test (T8).

Drives `make build` (via `python -m agentbundle.build build`) against
the four reference fixture packs at
`packages/agentbundle/agentbundle/build/tests/fixtures/packs/` on a
clean checkout and asserts the dist/ shape AC #7 + AC #13 require.
Production-pack migration into a top-level `packs/` directory is out
of scope per the spec's amended AC #7 (RFC-0001 F-dist follow-on
owns it).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
FIXTURES_PACKS = (
    Path(__file__).resolve().parent / "fixtures" / "packs"
)
REFERENCE_PACKS = ("core", "governance-extras", "user-guide-diataxis", "monorepo-extras")


def _run_build(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentbundle.build", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


class EndToEndBuildTests(unittest.TestCase):
    def test_default_build_produces_expected_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_build(
                [
                    "build",
                    "--packs-dir",
                    str(FIXTURES_PACKS),
                    "--output-dir",
                    tmp,
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            tmp_path = Path(tmp)
            marketplace = tmp_path / "claude-plugins" / "marketplace.json"
            self.assertTrue(marketplace.exists())
            entries = json.loads(marketplace.read_text(encoding="utf-8"))
            self.assertEqual(len(entries["plugins"]), len(REFERENCE_PACKS))
            for pack in REFERENCE_PACKS:
                self.assertTrue((tmp_path / "claude-plugins" / pack).exists())
                self.assertTrue((tmp_path / "apm" / pack).exists())

    def test_plain_build_does_not_invoke_self_host_recipes(self) -> None:
        """AC: plain `make build` produces only dist/apm, dist/claude-plugins,
        and dist/claude-plugins/marketplace.json — never the three self-host
        recipes' artefacts (overlay output in the working tree, composite
        AGENTS.md, composite marketplace)."""
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_build(
                [
                    "build",
                    "--packs-dir",
                    str(FIXTURES_PACKS),
                    "--output-dir",
                    tmp,
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            tmp_path = Path(tmp)
            self.assertFalse((tmp_path / "AGENTS.md").exists())
            # The composite marketplace lives at .claude-plugin/marketplace.json
            # (distinct from the aggregating marketplace.json at
            # claude-plugins/marketplace.json).
            self.assertFalse((tmp_path / ".claude-plugin" / "marketplace.json").exists())


class CheckCommandTests(unittest.TestCase):
    def test_make_build_check_on_a_clean_pre_projected_tree_exits_zero(self) -> None:
        """Render once into a temp working tree, then `check` it. The check
        should exit 0 because the tree matches the rendered output."""
        with tempfile.TemporaryDirectory() as tmp:
            working = Path(tmp) / "tree"
            working.mkdir()
            # Use git init to make it dirty-tree-detection-ready.
            import os
            env = os.environ.copy()
            env["GIT_AUTHOR_NAME"] = "test"
            env["GIT_AUTHOR_EMAIL"] = "test@example.com"
            env["GIT_COMMITTER_NAME"] = "test"
            env["GIT_COMMITTER_EMAIL"] = "test@example.com"
            subprocess.run(["git", "init", "-q", str(working)], check=True, env=env)

            from agentbundle.build.adapters import ADAPTERS
            from agentbundle.build.contract import load as load_contract
            from agentbundle.build.main import discover_packs

            contract = load_contract(
                REPO_ROOT / "docs" / "specs" / "adapter-contract" / "contract.toml"
            )
            for pack in discover_packs(FIXTURES_PACKS):
                for adapter_name, project in ADAPTERS.items():
                    if adapter_name not in contract["adapter"]:
                        continue
                    project(pack.path, contract, working)
            subprocess.run(["git", "-C", str(working), "add", "-A"], check=True, env=env)
            subprocess.run(
                ["git", "-C", str(working), "commit", "-q", "-m", "seed"],
                check=True,
                env=env,
            )

            result = _run_build(
                [
                    "check",
                    "--packs-dir",
                    str(FIXTURES_PACKS),
                    "--output-dir",
                    str(working),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)


class ScaffoldCommandTests(unittest.TestCase):
    def test_scaffold_copies_seeds_into_output(self) -> None:
        # core pack has no seeds/ directory in the fixture, so we make one.
        seeds_dir = FIXTURES_PACKS / "core" / "seeds"
        created_seeds = not seeds_dir.exists()
        if created_seeds:
            seeds_dir.mkdir()
            (seeds_dir / "AGENTS.md").write_text("# seeded\n", encoding="utf-8")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                result = _run_build(
                    [
                        "scaffold",
                        "--packs-dir",
                        str(FIXTURES_PACKS),
                        "--pack",
                        "core",
                        "--output",
                        tmp,
                    ]
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                self.assertTrue((Path(tmp) / "AGENTS.md").exists())
        finally:
            if created_seeds:
                (seeds_dir / "AGENTS.md").unlink()
                seeds_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
