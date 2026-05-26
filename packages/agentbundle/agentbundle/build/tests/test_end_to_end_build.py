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
            self.assertEqual(
                {entry["name"] for entry in entries["plugins"]},
                set(REFERENCE_PACKS),
            )
            for pack in REFERENCE_PACKS:
                self.assertTrue((tmp_path / "claude-plugins" / pack).exists())
                self.assertTrue((tmp_path / "apm" / pack).exists())

            # AC #7 + integrated-journey coverage: assert each of the five
            # primitives lands at its declared output under the `core` pack
            # — the only fixture that exercises every primitive type.
            core_plugin = tmp_path / "claude-plugins" / "core"
            self.assertTrue((core_plugin / ".claude" / "skills" / "example").exists())
            self.assertTrue((core_plugin / ".claude" / "agents" / "bar.md").exists())
            self.assertTrue((core_plugin / "tools" / "hooks" / "baz.sh").exists())
            self.assertTrue((core_plugin / "tools" / "hooks" / "baz.py").exists())
            self.assertTrue(
                (core_plugin / ".claude" / "settings.local.json").exists()
            )
            self.assertTrue((core_plugin / ".claude" / "commands" / "qux.md").exists())

    def test_plain_build_does_not_invoke_self_host_recipes(self) -> None:
        """AC: plain `make build` produces only dist/apm, dist/claude-plugins,
        and dist/claude-plugins/marketplace.json — never the three self-host
        recipes' artefacts (overlay output in the working tree, composite
        AGENTS.md, composite marketplace). Verifies AC #14: working tree is
        unchanged after the run (git status --porcelain returns byte-
        identical output before and after)."""
        before = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout
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
            self.assertFalse((tmp_path / ".claude-plugin" / "marketplace.json").exists())
        after = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        self.assertEqual(before, after, "plain `make build` modified the working tree")


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

            # Seed `.adapt-discovery.toml` so `make build-check`'s
            # fail-fast (spec AC14) doesn't reject the call. Canonical
            # v0.1 shape per adapt-to-project AC9.
            (working / ".adapt-discovery.toml").write_text(
                'discovery-schema-version = "0.1"\n', encoding="utf-8"
            )

            from agentbundle.build.adapters import ADAPTERS
            from agentbundle.build.contract import load as load_contract
            from agentbundle.build.main import discover_packs
            from agentbundle.build.self_host import run_self_host

            contract = load_contract(
                REPO_ROOT / "docs" / "contracts" / "adapter.toml"
            )
            # Pre-seed using the self-host runner so the working
            # tree exactly matches what `make build-check` will render
            # (including new seed/marketplace/symlink outputs).
            run_self_host(
                working_tree=working,
                packs_dir=FIXTURES_PACKS,
                dry_run=False,
                force=True,
                contract=contract,
            )
            subprocess.run(["git", "-C", str(working), "add", "-A"], check=True, env=env)
            subprocess.run(
                ["git", "-C", str(working), "commit", "-q", "-m", "seed"],
                check=True,
                env=env,
            )

            # `make build-check` depends on `make build` (Makefile:63) so the
            # writer-template / APM drift gates introduced in commits
            # 25590fe + 89c0db3 always see a populated dist/ tree. Mirror
            # that dependency here: run `build` into <working>/dist/ before
            # invoking `check --output-dir <working>` so `<working>/dist/
            # claude-plugins/` and `<working>/dist/apm/` exist.
            build_result = _run_build(
                [
                    "build",
                    "--packs-dir",
                    str(FIXTURES_PACKS),
                    "--output-dir",
                    str(working / "dist"),
                ]
            )
            self.assertEqual(
                build_result.returncode, 0, msg=build_result.stderr
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
        """Scaffold copies a pack's seeds/ to the named output directory.

        Uses a tempfile-based packs dir so the source fixture tree stays
        untouched even if the test is interrupted mid-run.
        """
        import shutil

        with tempfile.TemporaryDirectory() as workspace:
            workspace_path = Path(workspace)
            packs_clone = workspace_path / "packs"
            shutil.copytree(FIXTURES_PACKS, packs_clone)
            (packs_clone / "core" / "seeds").mkdir()
            (packs_clone / "core" / "seeds" / "AGENTS.md").write_text(
                "# seeded\n", encoding="utf-8"
            )
            output_dir = workspace_path / "out"

            result = _run_build(
                [
                    "scaffold",
                    "--packs-dir",
                    str(packs_clone),
                    "--pack",
                    "core",
                    "--output",
                    str(output_dir),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((output_dir / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
