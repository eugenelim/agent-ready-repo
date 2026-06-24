"""AC10: install --scope user against the research pack writes the
state-file row, lands the seven projected skill directories under
~/.claude/skills/ and the two projected subagent files under
~/.claude/agents/, and uninstall reverses both effects.

Mirrors test_install_converters_user_scope.py — the converters precedent
is the agreed shape (in-process install.run, $HOME redirected via
patch.dict, fixture catalogue populated from packs/research/).
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
RESEARCH_PACK_SRC = REPO_ROOT / "packs" / "research"
SKILL_NAMES = (
    "identify-perspectives",
    "build-outline",
    "source-map",
    "research",
    "devils-advocate",
    "compare-hypotheses",
    "decision-archaeology",
)
AGENT_NAMES = ("evidence-retriever", "source-extractor")


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


class ResearchUserScopeInstallTests(unittest.TestCase):
    """End-to-end install/uninstall round-trip for the research pack
    at user scope. Mirrors the converters precedent: $HOME is
    redirected to a tmp path so the test never touches the developer's
    real home tree."""

    def setUp(self) -> None:
        # addCleanup runs in LIFO: HOME patch unwinds before rmtree
        # blows away the tree HOME points at — register rmtree first
        # (runs last), env.stop second (runs first).
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        # Both HOME and USERPROFILE — Path.home() consults USERPROFILE
        # first on Windows and ignores HOME, so patching only HOME is a
        # no-op on the windows-latest runner.
        self._env = patch.dict(
            os.environ,
            {"HOME": str(self.home), "USERPROFILE": str(self.home)},
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        # Temporary catalogue layout: <cat>/packs/research/ — populated
        # from the repo-local pack via copytree.
        self.cat = self.tmp / "catalogue"
        (self.cat / "packs").mkdir(parents=True)
        shutil.copytree(RESEARCH_PACK_SRC, self.cat / "packs" / "research")

    def test_install_then_uninstall_round_trip(self) -> None:
        install_args = argparse.Namespace(
            pack="research",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
            force=False,
            force_merge=False,
        )
        rc, stdout, stderr = _run_install(install_args)
        self.assertEqual(rc, 0, f"install failed: stdout={stdout!r} stderr={stderr!r}")

        # HOME-resolution guard fires before state-file assertions.
        agentbundle_dir = self.home / ".agentbundle"
        self.assertTrue(
            agentbundle_dir.exists(),
            f"~/.agentbundle/ absent under tmp $HOME {self.home}; "
            f"check $HOME propagation",
        )

        # Deferred import — agentbundle.config resolves $HOME at first
        # import and the patch.dict above has to be live before that.
        from agentbundle.config import STATE_SCHEMA_VERSION, load_state

        state_path = agentbundle_dir / "state.toml"
        # Raw TOML read — load_state() defaults a missing schema-version
        # key to STATE_SCHEMA_VERSION, so comparing parsed-field-to-
        # constant is a tautology. The raw lookup makes the assertion
        # test the install contract, not the loader's default.
        try:
            import tomllib  # 3.11+
        except ModuleNotFoundError:  # pragma: no cover
            import tomli as tomllib  # type: ignore[no-redef]
        raw_state = tomllib.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(raw_state.get("schema-version"), STATE_SCHEMA_VERSION)

        state = load_state(state_path)
        self.assertIn("research", state.packs)
        pack_state = state.packs["research"]
        self.assertEqual(pack_state.scope, "user")
        # Floor at len(SKILL_NAMES) — one file-tracking entry per
        # shipped skill at minimum, matching the converters precedent
        # (spec AC10 floor at 7; agent files may or may not appear in
        # this list depending on the install implementation).
        self.assertGreaterEqual(
            len(pack_state.files),
            len(SKILL_NAMES),
            f"expected at least {len(SKILL_NAMES)} entries in "
            f"state.packs['research'].files, got {len(pack_state.files)}",
        )

        for name in SKILL_NAMES:
            skill_dir = self.home / ".claude" / "skills" / name
            self.assertTrue(
                skill_dir.is_dir(),
                f"expected projected skill directory at {skill_dir}",
            )
            self.assertTrue(
                (skill_dir / "SKILL.md").is_file(),
                f"expected SKILL.md inside {skill_dir}",
            )

        for name in AGENT_NAMES:
            agent_file = self.home / ".claude" / "agents" / f"{name}.md"
            self.assertTrue(
                agent_file.is_file(),
                f"expected projected agent file at {agent_file}",
            )

        uninstall_args = argparse.Namespace(
            pack="research",
            root=str(self.repo),
            scope="user",
            yes=True,
        )
        rc, stdout, stderr = _run_uninstall(uninstall_args)
        self.assertEqual(rc, 0, f"uninstall failed: stdout={stdout!r} stderr={stderr!r}")

        for name in SKILL_NAMES:
            skill_dir = self.home / ".claude" / "skills" / name
            self.assertFalse(
                skill_dir.exists(),
                f"projected skill directory at {skill_dir} survived uninstall",
            )

        for name in AGENT_NAMES:
            agent_file = self.home / ".claude" / "agents" / f"{name}.md"
            self.assertFalse(
                agent_file.exists(),
                f"projected agent file at {agent_file} survived uninstall",
            )

        # AC10's looser form: state file is gone OR state file remains
        # with the research row removed.
        research_gone = (
            not state_path.exists()
            or "research" not in load_state(state_path).packs
        )
        self.assertTrue(
            research_gone,
            "research entry survived uninstall in state.toml",
        )
