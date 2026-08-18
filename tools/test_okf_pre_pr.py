"""Tests for the repo-only OKF compiler pre-PR gate."""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent / "catalogue"))
import pre_pr_catalogue as pre_pr  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_pack(root: Path, name: str, *, okf_path: str = "okf/demo") -> Path:
    pack = root / "packs" / name
    bundle = pack / okf_path
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "index.md").write_text(
        '---\nokf_version: "0.2"\n---\n'
        "<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->\n"
        "# Demo\n",
        encoding="utf-8",
    )
    concepts = bundle / "concepts"
    concepts.mkdir(exist_ok=True)
    (concepts / "example.md").write_text(
        "---\n"
        'title: "Example"\n'
        'type: "Reference"\n'
        'status: "Active"\n'
        "---\n"
        "# Example\n",
        encoding="utf-8",
    )
    (pack / "pack.toml").write_text(
        "\n".join(
            [
                "[pack]",
                f'name = "{name.lstrip("_")}"',
                "",
                "[pack.metadata.okf]",
                'profile = "agentbundle-okf/v1"',
                "",
                "[[pack.metadata.okf.bundles]]",
                'id = "demo"',
                f'path = "{okf_path}"',
                '"router-skill" = "demo-router"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return pack


class OkfPrePrGateTests(unittest.TestCase):
    def test_discovery_includes_underscore_pilots_and_excludes_plain_packs(self) -> None:
        with self.subTest("discovery"):
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                _write_pack(root, "_okf-pilot")
                _write_pack(root, "managed")
                plain = root / "packs" / "plain"
                plain.mkdir(parents=True)
                (plain / "pack.toml").write_text(
                    '[pack]\nname = "plain"\n', encoding="utf-8"
                )

                discovered = [path.name for path in pre_pr._okf_pack_dirs(root)]

        self.assertEqual(discovered, ["_okf-pilot", "managed"])

    def test_run_okf_checks_invokes_compiler_for_each_managed_pack(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "_pilot")
            _write_pack(root, "core")
            seen: list[tuple[str, list[str]]] = []

            def fake_run(label: str, argv: list[str], env: dict | None = None) -> None:
                del env
                seen.append((label, argv))

            with mock.patch.object(pre_pr, "_run", fake_run):
                pre_pr._run_okf_checks(root, sys.executable)

        self.assertEqual([label for label, _ in seen], [
            "okf compiler check _pilot",
            "okf compiler check core",
        ])
        for _, argv in seen:
            self.assertIn("--check", argv)
            self.assertIn("--pack", argv)

    def test_clean_drift_and_unsafe_inputs_use_shipped_compiler_check(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "managed")
            compiler = pre_pr._okf_compiler_script(REPO_ROOT)
            write = subprocess.run(
                [
                    sys.executable,
                    str(compiler),
                    "--root",
                    str(root),
                    "--pack",
                    "managed",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(write.returncode, 0, write.stderr)

            with mock.patch.object(pre_pr, "_okf_compiler_script", return_value=compiler):
                pre_pr._run_okf_checks(root, sys.executable)

            router = (
                root
                / "packs"
                / "managed"
                / ".apm"
                / "skills"
                / "demo-router"
                / "SKILL.md"
            )
            router.write_text(
                router.read_text(encoding="utf-8") + "\nmanual drift\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(pre_pr, "_okf_compiler_script", return_value=compiler),
                self.assertRaises(SystemExit),
            ):
                pre_pr._run_okf_checks(root, sys.executable)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "unsafe", okf_path="okf/../escape")
            stderr = io.StringIO()
            with (
                mock.patch.object(pre_pr, "_okf_compiler_script", return_value=compiler),
                contextlib.redirect_stderr(stderr),
                self.assertRaises(SystemExit),
            ):
                pre_pr._run_okf_checks(root, sys.executable)
            self.assertIn("okf compiler check unsafe", stderr.getvalue())

    def test_plain_catalogue_has_no_okf_check_and_gate_imports_no_pyyaml(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plain = root / "packs" / "plain"
            plain.mkdir(parents=True)
            (plain / "pack.toml").write_text('[pack]\nname = "plain"\n', encoding="utf-8")

            with mock.patch.object(pre_pr, "_run") as run:
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    pre_pr._run_okf_checks(root, sys.executable)

        run.assert_not_called()
        self.assertIn("no managed packs", stdout.getvalue())
        source = (REPO_ROOT / "tools" / "catalogue" / "pre_pr_catalogue.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("import yaml", source)

    def test_dependency_audit_and_scanners_cover_okf_compiler_paths(self) -> None:
        requirements = (REPO_ROOT / "tools" / "requirements.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("pyyaml>=6.0", requirements.lower())

        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("SAST_DIRS := tools packs packages tests", makefile)
        self.assertIn("tools/run-bandit-gate.py $(SAST_DIRS)", makefile)
        self.assertIn("$(SEMGREP_EXCLUDE) $(SAST_DIRS)", makefile)
        self.assertIn("tools/audit-requirements.py tools/requirements.txt", makefile)
        self.assertIn("$$(find packs -name requirements.txt | sort)", makefile)
        self.assertIn("--optional-group lint", makefile)
        self.assertIn("packages/agentbundle/pyproject.toml", makefile)


if __name__ == "__main__":
    unittest.main()
