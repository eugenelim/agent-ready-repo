"""T2: credential-brokers pack manifest + skeleton install tests.

Verifies AC4 (manifest shape), AC5 (directory invariant), and the
RFC-0004 Rail A refusal (seeds/ at user scope). The install
integration is in-process per the
test_install_converters_user_scope.py idiom; $HOME redirected so the
test never touches the developer's real tree.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import re
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
PACK_SRC = REPO_ROOT / "packs" / "credential-brokers"


def _run_install(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands import install

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = install.run(args)
    return rc, stdout.getvalue(), stderr.getvalue()


class PackManifestShapeTests(unittest.TestCase):
    """AC4: pack.toml carries the verbatim field shape from RFC-0013 § 4."""

    def setUp(self) -> None:
        self.pack_toml = tomllib.loads(
            (PACK_SRC / "pack.toml").read_text(encoding="utf-8")
        )

    def test_pack_name_and_version(self) -> None:
        pack = self.pack_toml["pack"]
        self.assertEqual(pack["name"], "credential-brokers")
        self.assertEqual(pack["version"], "0.1.0")

    def test_description_names_the_three_artefacts(self) -> None:
        # The verbatim description from RFC-0013 § 4 names the three
        # artefacts the pack ships (credentials_shim, sso-broker,
        # credential-setup). Pin substrings rather than the whole
        # string so prose touchups don't false-trigger.
        desc = self.pack_toml["pack"]["description"]
        self.assertIn("credentials_shim", desc)
        self.assertIn("sso-broker", desc)
        self.assertIn("credential-setup", desc)
        self.assertIn("LLM-cooperative", desc)

    def test_adapter_contract_version_is_07(self) -> None:
        self.assertEqual(
            self.pack_toml["pack"]["adapter-contract"]["version"], "0.7"
        )

    def test_install_block_shape(self) -> None:
        install_block = self.pack_toml["pack"]["install"]
        self.assertEqual(install_block["default-scope"], "user")
        self.assertEqual(install_block["allowed-scopes"], ["user", "repo"])
        self.assertEqual(
            install_block["allowed-adapters"],
            ["claude-code", "kiro", "codex"],
        )


class PackDirectoryInvariantTests(unittest.TestCase):
    """AC5: .apm/ tree contains exactly the three declared primitive
    directories (shared-libs/, adapter-root-bins/, skills/credential-setup/),
    plus pack.toml at the pack root. No seeds/, no hooks/, no
    hook-wiring/, no second .apm/skills/<other>/. No <adapt:NAME>
    markers anywhere under .apm/.
    """

    def test_pack_root_carries_pack_toml(self) -> None:
        self.assertTrue((PACK_SRC / "pack.toml").is_file())

    def test_apm_contains_only_declared_subdirs(self) -> None:
        apm = PACK_SRC / ".apm"
        self.assertTrue(apm.is_dir())
        subdirs = {p.name for p in apm.iterdir() if p.is_dir()}
        self.assertEqual(
            subdirs,
            {"shared-libs", "adapter-root-bins", "skills"},
            f".apm/ subdirs deviate from the declared set: {subdirs}",
        )

    def test_skills_contains_only_credential_setup(self) -> None:
        skills = PACK_SRC / ".apm" / "skills"
        self.assertTrue(skills.is_dir())
        subdirs = {p.name for p in skills.iterdir() if p.is_dir()}
        self.assertEqual(
            subdirs,
            {"credential-setup"},
            f".apm/skills/ deviates from declared set: {subdirs}",
        )

    def test_no_forbidden_dirs(self) -> None:
        # Refusal rails A/B + RFC-0007 user-scope discipline: no seeds/,
        # no hooks/, no hook-wiring/.
        for forbidden in ("seeds", ".apm/hooks", ".apm/hook-wiring"):
            self.assertFalse(
                (PACK_SRC / forbidden).exists(),
                f"forbidden directory present: {forbidden}",
            )

    def test_no_adapt_markers_under_apm(self) -> None:
        # RFC-0007 user-scope refusal rail C: <adapt:NAME> markers
        # are repo-scope only. Walk .apm/ recursively.
        marker = re.compile(r"<adapt:[A-Z_]+>")
        apm = PACK_SRC / ".apm"
        for path in apm.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            self.assertIsNone(
                marker.search(text),
                f"<adapt:...> marker present in {path.relative_to(REPO_ROOT)}",
            )


class _BaseInstall(unittest.TestCase):
    """$HOME-redirected install scaffold shared by the install tests."""

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
        self.cat = self.tmp / "catalogue"
        (self.cat / "packs").mkdir(parents=True)
        # Copy the pack source verbatim so the test exercises the actual
        # shipped manifest, not a fixture.
        shutil.copytree(PACK_SRC, self.cat / "packs" / "credential-brokers")


class PackInstallTests(_BaseInstall):
    """AC4 install path: --scope user against a fixture $HOME succeeds."""

    def test_install_at_user_scope_succeeds(self) -> None:
        args = argparse.Namespace(
            pack="credential-brokers",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
            force=False,
            force_merge=False,
        )
        rc, stdout, stderr = _run_install(args)
        self.assertEqual(
            rc, 0,
            f"install --scope user failed: stdout={stdout!r} stderr={stderr!r}",
        )
        # ~/.agentbundle/ must exist after a user-scope install — the
        # state.toml lands there.
        self.assertTrue(
            (self.home / ".agentbundle").exists(),
            f"~/.agentbundle/ absent under tmp HOME {self.home}",
        )


class SeedsRefusalRailTests(_BaseInstall):
    """RFC-0004 Rail A: a non-empty seeds/ at the pack root refuses
    user-scope install. The refusal text is enforced by
    `scope_rails.check_seeds` and surfaced as `install: <pack>: <msg>`.
    """

    def setUp(self) -> None:
        super().setUp()
        # Inject a seeds/ directory with one file post-copy.
        seeds = self.cat / "packs" / "credential-brokers" / "seeds"
        seeds.mkdir()
        (seeds / "README.md").write_text("# injected fixture\n", encoding="utf-8")

    def test_install_refuses_with_pinned_message(self) -> None:
        args = argparse.Namespace(
            pack="credential-brokers",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
            force=False,
            force_merge=False,
        )
        rc, _stdout, stderr = _run_install(args)
        self.assertNotEqual(rc, 0, "install should refuse with seeds/ injected")
        self.assertIn("seeds/", stderr)
        self.assertIn("user", stderr)
        self.assertIn("allowed-scopes", stderr)


if __name__ == "__main__":
    unittest.main()
