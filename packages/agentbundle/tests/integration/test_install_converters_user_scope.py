"""AC6a: install --scope user against the converters pack writes the
state-file row, lands the three projected skill directories under
~/.claude/skills/, and uninstall reverses both effects.

The reference idiom is test_install_user_hooks.py:_UserScopeInstallBase
(in-process install.run, $HOME redirected via patch.dict). Install
takes --pack + positional catalogue + --output + --scope; uninstall
takes --pack + --root + --scope (different field name — root, not
output).
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

REPO_ROOT = Path(__file__).resolve().parents[4]
CONVERTERS_PACK_SRC = REPO_ROOT / "packs" / "converters"
SKILL_NAMES = ("file-to-markdown", "markdown-to-html", "msg-to-markdown")


def _run_install(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands import install

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = install.run(args)
    return rc, stdout.getvalue(), stderr.getvalue()


def _run_uninstall(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands import uninstall

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = uninstall.run(args)
    return rc, stdout.getvalue(), stderr.getvalue()


class ConvertersUserScopeInstallTests(unittest.TestCase):
    """End-to-end install/uninstall round-trip for the converters pack
    at user scope. Mirrors _UserScopeInstallBase from
    test_install_user_hooks.py: $HOME is redirected to a tmp path so
    the test never touches the developer's real home tree."""

    def setUp(self) -> None:
        # addCleanup runs in LIFO order: the HOME patch must unwind
        # *before* shutil.rmtree blows away the tree HOME points at,
        # so register rmtree first (it runs last) and env.stop second
        # (it runs first).
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        # Set both HOME (POSIX) and USERPROFILE (Windows) — `Path.home()`
        # consults USERPROFILE first on Windows and ignores HOME there,
        # so patching only HOME is a no-op on the windows-latest runner.
        # Mirrors the widened patch in _UserScopeInstallBase.
        self._env = patch.dict(
            os.environ,
            {"HOME": str(self.home), "USERPROFILE": str(self.home)},
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        # Temporary catalogue layout: <cat>/packs/converters/ — populated
        # from the repo-local pack via copytree.
        self.cat = self.tmp / "catalogue"
        (self.cat / "packs").mkdir(parents=True)
        shutil.copytree(CONVERTERS_PACK_SRC, self.cat / "packs" / "converters")

    def test_install_then_uninstall_round_trip(self) -> None:
        install_args = argparse.Namespace(
            pack="converters",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
            force=False,
            force_merge=False,
        )
        rc, stdout, stderr = _run_install(install_args)
        self.assertEqual(rc, 0, f"install failed: stdout={stdout!r} stderr={stderr!r}")

        # HOME-resolution guard: if $HOME didn't propagate into the CLI's
        # Path.home() (e.g. cached at import time), the state directory
        # lands at the developer's real home and the next assertion fires
        # with a clear message instead of a confusing AttributeError.
        agentbundle_dir = self.home / ".agentbundle"
        self.assertTrue(
            agentbundle_dir.exists(),
            f"~/.agentbundle/ absent under tmp $HOME {self.home}; "
            f"check $HOME propagation",
        )

        # Deferred import: agentbundle.config resolves $HOME at first
        # import and the patch.dict above has to be live before that.
        from agentbundle.config import STATE_SCHEMA_VERSION, load_state

        state_path = agentbundle_dir / "state.toml"
        # Read the raw TOML to assert the install path actually wrote the
        # schema-version key. load_state() defaults a missing key to
        # STATE_SCHEMA_VERSION (config.py:185), so comparing the parsed
        # field to the constant is a tautology that would pass even if
        # install never wrote the field. The raw lookup makes the
        # assertion test the install contract, not the loader's default.
        try:
            import tomllib  # 3.11+
        except ModuleNotFoundError:  # pragma: no cover
            import tomli as tomllib  # type: ignore[no-redef]
        raw_state = tomllib.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(raw_state.get("schema-version"), STATE_SCHEMA_VERSION)

        state = load_state(state_path)
        self.assertIn("converters", state.packs)
        pack_state = state.packs["converters"]
        self.assertEqual(pack_state.scope, "user")
        # The install→state→uninstall data flow runs through this dict;
        # uninstall reads it to know what to remove. Floor at three (one
        # entry per shipped skill at minimum) — an exact total would be
        # brittle but a positive count alone would miss a regression that
        # only records one skill's files.
        self.assertGreaterEqual(
            len(pack_state.files),
            len(SKILL_NAMES),
            f"expected at least {len(SKILL_NAMES)} entries in "
            f"state.packs['converters'].files, got {len(pack_state.files)}",
        )

        for name in SKILL_NAMES:
            skill_dir = self.home / ".claude" / "skills" / name
            self.assertTrue(
                skill_dir.is_dir(),
                f"expected projected skill directory at {skill_dir}",
            )
            # Presence of SKILL.md is the closest thing to a "skill is
            # actually usable" assertion: the dir alone could be empty.
            self.assertTrue(
                (skill_dir / "SKILL.md").is_file(),
                f"expected SKILL.md inside {skill_dir}",
            )

        uninstall_args = argparse.Namespace(
            pack="converters",
            root=str(self.repo),
            scope="user",
        )
        rc, stdout, stderr = _run_uninstall(uninstall_args)
        self.assertEqual(rc, 0, f"uninstall failed: stdout={stdout!r} stderr={stderr!r}")

        for name in SKILL_NAMES:
            skill_dir = self.home / ".claude" / "skills" / name
            self.assertFalse(
                skill_dir.exists(),
                f"projected skill directory at {skill_dir} survived uninstall",
            )

        # Spec AC6a's looser form covers two valid implementations: state
        # file is gone, OR state file remains with the converters row
        # removed. Expressed as a single boolean rather than a conditional
        # that silently no-ops when the file is gone.
        converters_gone = (
            not state_path.exists()
            or "converters" not in load_state(state_path).packs
        )
        self.assertTrue(
            converters_gone,
            "converters entry survived uninstall in state.toml",
        )
