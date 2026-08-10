"""T2: credential-brokers pack manifest + skeleton install tests.

Verifies the manifest shape, the directory invariant, and the
Rail A refusal (seeds/ at user scope). The install
integration is in-process per the
test_install_converters_user_scope.py idiom; $HOME redirected so the
test never touches the developer's real tree.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests._support import stage_installable_pack


def _stage_broker_pack(catalogue: Path) -> Path:
    """Create the smallest pack exercising the two broker delivery rails."""
    pack = stage_installable_pack(
        catalogue,
        "credential-brokers",
        """\
[pack]
name = "credential-brokers"
version = "0.1.0"
[pack.adapter-contract]
version = "0.7"
[pack.install]
default-scope = "user"
allowed-scopes = ["user", "repo"]
allowed-adapters = ["claude-code", "kiro-ide", "codex", "copilot", "cursor", "gemini"]
""",
    )
    library = pack / ".apm" / "user-libs" / "credbroker"
    library.mkdir(parents=True)
    (library / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    bins = pack / ".apm" / "adapter-root-bins"
    bins.mkdir(parents=True)
    (bins / "sso-broker.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    shared = pack / ".apm" / "shared-libs"
    shared.mkdir(parents=True)
    (shared / "credentials_shim.py").write_text("VALUE = 1\n", encoding="utf-8")
    return pack


def _run_install(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands import install

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = install.run(args)
    return rc, stdout.getvalue(), stderr.getvalue()


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
        _stage_broker_pack(self.cat)


class SeedsRefusalRailTests(_BaseInstall):
    """Rail A: a non-empty seeds/ at the pack root refuses
    user-scope install. The refusal text is enforced by
    `scope_rails.check_seeds` and surfaced as `install: <pack>: <msg>`.
    """

    def setUp(self) -> None:
        super().setUp()
        # Inject a seeds/ directory with one file post-copy.
        seeds = self.cat / "packs" / "credential-brokers" / "seeds"
        seeds.mkdir()
        (seeds / "README.md").write_text("# injected fixture\n", encoding="utf-8", newline="\n")

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


class UserScopeFloorDeliveryTests(_BaseInstall):
    """credbroker-user-scope T4: a ``$HOME``-redirected user-scope install
    delivers the vendored ``credbroker`` floor (``lib/``) **and** the
    ``sso-broker`` rail (``bin/`` + the companion shim), and a real
    consumer entry script resolves ``import credbroker`` from the floor.
    """

    def _install(self) -> tuple[str, str]:
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
            rc, 0, f"install --scope user failed: stdout={stdout!r} stderr={stderr!r}"
        )
        return stdout, stderr

    def test_lib_no_exec_bit_and_bin_is_0755(self) -> None:
        # File-mode contract: lib/ default-mode (no exec bit), bin/ 0o755.
        if os.name != "posix":
            self.skipTest("POSIX mode bits; Windows inherits the parent DACL")
        self._install()
        init = self.home / ".agentbundle" / "lib" / "credbroker" / "__init__.py"
        self.assertFalse(
            init.stat().st_mode & 0o111,
            "lib/ floor must carry no exec bit (importable Python, not a script)",
        )
        sso = self.home / ".agentbundle" / "bin" / "sso-broker.py"
        self.assertEqual(
            sso.stat().st_mode & 0o777, 0o755, "bin/*.py must be 0o755 on POSIX"
        )

    def test_delivery_stays_under_agentbundle_jail(self) -> None:
        # Jail + no-leak: the floor/bin artifacts land ONLY under
        # ~/.agentbundle/ — never leaked into the adapter projection dir or
        # anywhere else under $HOME. write_jailed enforces the prefix; this
        # asserts the delivery composed paths under it.
        self._install()
        artifact_root = self.home / ".agentbundle"
        for needle in ("credbroker", "sso-broker", "credentials_shim"):
            for hit in self.home.rglob(f"*{needle}*"):
                self.assertTrue(
                    artifact_root in hit.parents or hit == artifact_root,
                    f"delivery leaked outside the .agentbundle/ jail: {hit}",
                )

    def test_refuses_group_world_writable_floor(self) -> None:
        # Security: a pre-existing world/group-writable floor is a local
        # code-execution vector (the floor is appended to sys.path); refuse.
        if os.name != "posix":
            self.skipTest("POSIX mode bits; the DACL model differs on Windows")
        floor = self.home / ".agentbundle" / "lib"
        floor.mkdir(parents=True)
        floor.chmod(0o777)
        args = argparse.Namespace(
            pack="credential-brokers",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
            force=False,
            force_merge=False,
        )
        rc, _stdout, stderr = _run_install(args)
        self.assertNotEqual(rc, 0, "install must refuse a group/world-writable floor")
        self.assertIn("group/world-writable", stderr)

    def test_symlinked_pack_content_is_not_delivered(self) -> None:
        # Security: pack_dir comes from an untrusted catalogue. A symlinked
        # source under adapter-root-bins/ (executable bin) or user-libs/
        # (importable floor) pointing out of tree must not have its target's
        # bytes read into ~/.agentbundle/.
        if os.name != "posix":
            self.skipTest("symlink creation needs privilege on Windows")
        secret = self.tmp / "secret.txt"
        secret.write_bytes(b"SECRET-OUT-OF-TREE\n")
        cat_pack = self.cat / "packs" / "credential-brokers"
        (cat_pack / ".apm" / "adapter-root-bins" / "evil.py").symlink_to(secret)
        (cat_pack / ".apm" / "user-libs" / "credbroker" / "evil_lib.py").symlink_to(secret)
        self._install()
        evil_bin = self.home / ".agentbundle" / "bin" / "evil.py"
        evil_lib = self.home / ".agentbundle" / "lib" / "credbroker" / "evil_lib.py"
        self.assertFalse(evil_bin.exists(), "symlinked bin source was delivered")
        self.assertFalse(evil_lib.exists(), "symlinked lib source was delivered")


if __name__ == "__main__":
    unittest.main()
