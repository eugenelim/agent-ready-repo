"""Repository cross-pack credential floor integration."""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_SRC = REPO_ROOT / "packs" / "credential-brokers"
JIRA_SCRIPTS = (
    REPO_ROOT / "packs" / "atlassian" / ".apm" / "skills" / "jira" / "scripts"
)


def _run_install(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands import install

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = install.run(args)
    return rc, stdout.getvalue(), stderr.getvalue()


class CredentialBrokerAtlassianIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self._env = patch.dict(
            os.environ,
            {"HOME": str(self.home), "USERPROFILE": str(self.home)},
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        self.catalogue = self.tmp / "catalogue"
        (self.catalogue / "packs").mkdir(parents=True)
        shutil.copytree(PACK_SRC, self.catalogue / "packs" / "credential-brokers")

    def _install(self) -> None:
        args = argparse.Namespace(
            pack="credential-brokers",
            catalogue=str(self.catalogue),
            output=str(self.repo),
            scope="user",
            force=False,
            force_merge=False,
        )
        rc, stdout, stderr = _run_install(args)
        self.assertEqual(rc, 0, f"stdout={stdout!r} stderr={stderr!r}")

    def _clean_env(self, **extra: str) -> dict[str, str]:
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"}
            and not key.startswith(("JIRA_", "FIGMA_"))
        }
        env["HOME"] = str(self.home)
        env["USERPROFILE"] = str(self.home)
        env.update(extra)
        return env

    def test_api_cli_resolves_credbroker_from_floor(self) -> None:
        self._install()
        entry = JIRA_SCRIPTS / "jira.py"
        if not entry.is_file():
            self.skipTest(f"{entry} not present in this checkout")
        stub = self.tmp / "httpxstub"
        stub.mkdir()
        (stub / "httpx.py").write_text(
            "# stub: import-only\n", encoding="utf-8", newline="\n"
        )
        credbroker_in_site = importlib.util.find_spec("credbroker") is not None
        if credbroker_in_site and os.name == "nt":
            self.skipTest("cannot isolate site-packages without breaking asyncio")
        argv = [sys.executable]
        if credbroker_in_site:
            argv.append("-S")
        argv += ["scripts/jira.py", "check"]
        proc = subprocess.run(
            argv,
            cwd=str(JIRA_SCRIPTS.parent),
            capture_output=True,
            text=True,
            env=self._clean_env(PYTHONPATH=str(stub)),
            timeout=60,
        )
        self.assertNotIn("No module named 'credbroker'", proc.stderr)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        for tier in ("Tier 1", "Tier 2", "Tier 3"):
            self.assertIn(tier, proc.stderr)
