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
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
PACK_SRC = REPO_ROOT / "packs" / "credential-brokers"
# credbroker-user-scope T4: a real API CLI (eager importer is setup.py, below)
# whose floor resolution closes the lazy-import gap T1 could only prove
# structurally. The atlassian pack ships it; skip if the checkout lacks it.
JIRA_SCRIPTS = REPO_ROOT / "packs" / "atlassian" / ".apm" / "skills" / "jira" / "scripts"
SETUP_SCRIPTS = PACK_SRC / ".apm" / "skills" / "credential-setup" / "scripts"


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
        # Bumped 0.1.0 → 0.1.1 (metadata enrichment) → 0.1.2 (per-pack
        # guide-home `documentation` link) → 0.1.3 (missing-credbroker guard +
        # credentials_shim→credbroker description fix) → 0.2.0 (credbroker SSO
        # consumer family, RFC-0035: load_sso_cookies + confinement primitives)
        # → 0.2.1 (first-value adoption contract, RFC-0064 Amendment #4);
        # adapter-contract unchanged.
        self.assertEqual(pack["version"], "0.2.1")

    def test_description_names_the_three_artefacts(self) -> None:
        # The description names the artefacts the pack ships. Since RFC-0023 the
        # `auth: creds` resolver is the `credbroker` library (the build-projected
        # `credentials_shim` it replaced is no longer the consumer-facing
        # resolver), so the description names credbroker, sso-broker, and
        # credential-setup. Pin substrings rather than the whole string so prose
        # touchups don't false-trigger.
        desc = self.pack_toml["pack"]["description"]
        self.assertIn("credbroker", desc)
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
        # RFC-0013 § 4 shipped the three-harness set; § Errata (2026-06-12)
        # widened it to add `copilot` + `cursor` and `gemini` — all three since
        # declared `.agentbundle/` in `allowed-prefixes.user`, the § 4d
        # precondition, so the adapter-agnostic broker delivery rail reaches them.
        self.assertEqual(
            install_block["allowed-adapters"],
            ["claude-code", "kiro-ide", "codex", "copilot", "cursor", "gemini"],
        )


class PackDirectoryInvariantTests(unittest.TestCase):
    """AC5: .apm/ tree contains exactly the declared primitive directories
    (shared-libs/, adapter-root-bins/, user-libs/, skills/credential-setup/),
    plus pack.toml at the pack root. No seeds/, no hooks/, no
    hook-wiring/, no second .apm/skills/<other>/. No <adapt:NAME>
    markers anywhere under .apm/.

    ``user-libs/`` was added by credbroker-user-scope T3 — the vendored
    `credbroker` floor source projected from `packages/credbroker/credbroker/`.
    """

    def test_pack_root_carries_pack_toml(self) -> None:
        self.assertTrue((PACK_SRC / "pack.toml").is_file())

    def test_apm_contains_only_declared_subdirs(self) -> None:
        apm = PACK_SRC / ".apm"
        self.assertTrue(apm.is_dir())
        subdirs = {p.name for p in apm.iterdir() if p.is_dir()}
        self.assertEqual(
            subdirs,
            {"shared-libs", "adapter-root-bins", "user-libs", "skills"},
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


class UserScopeFloorDeliveryTests(_BaseInstall):
    """credbroker-user-scope T4: a ``$HOME``-redirected user-scope install
    delivers the vendored ``credbroker`` floor (``lib/``) **and** the
    ``sso-broker`` rail (``bin/`` + the AC22b companion shim), and a real
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

    def _clean_env(self, **extra: str) -> dict[str, str]:
        """Subprocess env with ``HOME``/``USERPROFILE`` pointed at the install
        and the isolation knobs cleared: drop ``PYTHONPATH``/``PYTHONHOME`` (so
        the only library source is site-packages — itself hidden by ``-S`` when
        a real ``credbroker`` is installed — plus any caller-supplied
        ``PYTHONPATH``) and any ambient ``JIRA_*``/``FIGMA_*`` credential vars
        so credentials genuinely miss.

        Inherits the *rest* of ``os.environ`` rather than allow-listing a
        handful — on Windows, asyncio's Winsock init (``import _overlapped``)
        needs ``SystemRoot``/``SystemDrive``/``WINDIR`` etc., and a minimal env
        raises ``OSError: [WinError 10106]`` before the CLI can run."""
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"}
            and not k.startswith(("JIRA_", "FIGMA_"))
        }
        env["HOME"] = str(self.home)
        env["USERPROFILE"] = str(self.home)
        env.update(extra)
        return env

    def test_floor_lib_bin_and_companion_land(self) -> None:
        # AC: floor-delivery + sso-broker half.
        self._install()
        lib = self.home / ".agentbundle" / "lib" / "credbroker"
        for name in ("__init__.py", "_core.py", "_vault.py"):
            self.assertTrue(
                (lib / name).is_file(),
                f"~/.agentbundle/lib/credbroker/{name} absent after install",
            )
        binp = self.home / ".agentbundle" / "bin"
        # sso-broker.py + the AC22b companion shim + both _sso_* backends.
        for name in (
            "sso-broker.py",
            "credentials_shim.py",
            "_sso_keychain_macos.py",
            "_sso_credman_windows.py",
        ):
            self.assertTrue(
                (binp / name).is_file(),
                f"~/.agentbundle/bin/{name} absent after install",
            )

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
        os.chmod(floor, 0o777)
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

    def test_setup_py_resolves_credbroker_from_floor(self) -> None:
        # End-to-end (eager importer): setup.py does `from credbroker import …`
        # at module top. Under `-S` (no site-packages) the floor is the ONLY
        # credbroker, so `--help` (exit 0, after the import) proves the floor
        # resolved. Real subprocess invocation — no runpy/importlib synthesis.
        self._install()
        entry = SETUP_SCRIPTS / "setup.py"
        if not entry.is_file():
            self.skipTest(f"{entry} not present in this checkout")
        proc = subprocess.run(
            [sys.executable, "-S", "scripts/setup.py", "--help"],
            cwd=str(SETUP_SCRIPTS.parent),
            capture_output=True,
            text=True,
            env=self._clean_env(),
            timeout=60,
        )
        self.assertEqual(
            proc.returncode,
            0,
            "setup.py --help failed under -S — `from credbroker import` did not "
            f"resolve from the floor; stderr:\n{proc.stderr}",
        )

    def test_api_cli_resolves_credbroker_from_floor(self) -> None:
        # End-to-end (the LOAD-BEARING CLI case, plan T4 coverage note): the
        # five API CLIs import credbroker lazily inside an httpx-gated verb, so
        # T1 could only prove their precedence structurally. Here a real
        # `jira.py check` — with a stub httpx so its `_client` import succeeds —
        # reaches load_credentials, which imports credbroker from the floor and
        # runs Tier-1→2→3 resolution. No creds anywhere → CredentialsMissingError
        # → AuthError → EXIT_USER_ACTION (2). Reaching exit 2 *and* emitting the
        # Tier ladder *requires* the floor import (a vacuous exit-2 from a
        # missing dependency would carry neither).
        self._install()
        entry = JIRA_SCRIPTS / "jira.py"
        if not entry.is_file():
            self.skipTest(f"{entry} not present in this checkout")
        stub = self.tmp / "httpxstub"
        stub.mkdir()
        (stub / "httpx.py").write_text("# stub: import-only\n", encoding="utf-8")

        # Make the floor the *only* credbroker. `-S` (no site-packages) does
        # that — but only apply it when a credbroker is actually installed in
        # this interpreter's site-packages: on Windows `-S` also breaks
        # asyncio's `_overlapped` C-extension load (jira.py imports asyncio at
        # module top), so the CLI can't run under `-S` there. CI never hits the
        # bad combination — Linux build-check pip-installs credbroker (needs
        # `-S`; asyncio is fine under `-S` on POSIX); Windows build-check does
        # not (the floor is already the only credbroker, so no `-S` needed).
        credbroker_in_site = importlib.util.find_spec("credbroker") is not None
        if credbroker_in_site and os.name == "nt":
            self.skipTest(
                "credbroker installed on Windows: cannot hide it without -S, "
                "which breaks asyncio import on Windows"
            )
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
        self.assertNotIn(
            "No module named 'credbroker'",
            proc.stderr,
            "the floor failed to resolve `import credbroker` for the API CLI",
        )
        self.assertEqual(
            proc.returncode,
            2,
            "jira.py check must exit EXIT_USER_ACTION(2) via credbroker's "
            f"CredentialsMissingError resolved from the floor; stderr:\n{proc.stderr}",
        )
        # Positive proof it reached credbroker's env→keyring→dotfile ladder
        # (platform-agnostic: the Tier labels are emitted on every OS; the
        # Tier-2 backend *name* is not, so we don't pin it).
        for tier in ("Tier 1", "Tier 2", "Tier 3"):
            self.assertIn(
                tier,
                proc.stderr,
                f"{tier} resolution not reached — credbroker did not run from "
                f"the floor; stderr:\n{proc.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
