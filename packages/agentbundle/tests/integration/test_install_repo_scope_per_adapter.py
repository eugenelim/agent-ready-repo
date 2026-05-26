"""End-to-end integration coverage for the RFC-0012 per-IDE projection
at repo scope (spec AC33).

Each test installs a real shipped pack (`core`) at repo scope, asserts
the per-adapter on-disk projection lands at the right directory, the
state file records the resolved adapter, and stdout matches the
pinned `installed: <pack> @ repo via <adapter>` shape.

Pre-existing unit coverage in `tests/unit/test_install_argparse_emit_install_routes.py`,
`tests/unit/test_install_messages_repo_scope.py`, and
`tests/unit/test_resolve_user_scope_target_adapter.py` (RFC-0012
repo-scope cases) covers the resolver branches, message-rail
formatting, and orphan-refusal mechanics. This module exercises the
adopter-facing greenfield path end-to-end.

Coverage scope (vs. spec AC33's full matrix):

  - Per-adapter greenfield writes projection + state + stdout
    (claude-code default, kiro, codex, copilot).
  - `--emit-install-routes` dist-tree shape.
  - Upgrade with state-hint at repo scope (AC10b parity).
  - Migration trigger (b) shape-mismatch end-to-end.
  - Migration trigger (a) adapter-disagreement end-to-end.

The orphan-recovery case (c) ships in
``tests/unit/test_install_inband_detection.py`` alongside the
per-pack (b)+(c) precedence witness and the once-per-session
short-circuit witness.
"""

from __future__ import annotations

import io
import sys
import tomllib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[4]
PACKS_DIR = REPO_ROOT / "packs"


def _run_install(argv: list[str]) -> tuple[int, str, str]:
    """Invoke install via the argparse layer; return (rc, stdout, stderr)."""
    from agentbundle.cli import _build_parser
    from agentbundle.commands import install

    parser = _build_parser()
    args = parser.parse_args(["install"] + argv)
    out_buf, err_buf = io.StringIO(), io.StringIO()
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        rc = install.run(args)
    return rc, out_buf.getvalue(), err_buf.getvalue()


def _load_state(adopter: Path) -> dict:
    state_path = adopter / ".agentbundle-state.toml"
    return tomllib.loads(state_path.read_text(encoding="utf-8"))


class RepoScopePerAdapterGreenfieldTests(unittest.TestCase):
    """Per-adapter greenfield install lands at the right directory."""

    def _install_and_assert(
        self,
        *,
        adapter_flag: str | None,
        expected_adapter: str,
        expected_dir: str,
    ) -> None:
        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            argv = [
                "--pack",
                "core",
                "--scope",
                "repo",
                "--output",
                str(adopter),
                str(REPO_ROOT),
            ]
            if adapter_flag is not None:
                argv = argv[:2] + ["--adapter", adapter_flag] + argv[2:]
            rc, stdout, stderr = _run_install(argv)
            self.assertEqual(
                rc, 0, f"install failed:\nstdout={stdout}\nstderr={stderr}"
            )

            # Stdout pins the resolved adapter.
            self.assertIn(
                f"installed: core @ repo via {expected_adapter}",
                stdout,
            )

            # On-disk projection lands at the expected directory.
            projection_dir = adopter / expected_dir
            self.assertTrue(
                projection_dir.exists(),
                f"expected projection at {projection_dir}; "
                f"adopter tree: {sorted(p.relative_to(adopter).as_posix() for p in adopter.rglob('*'))[:20]}",
            )

            # State file records the resolved adapter. The state TOML
            # uses `[pack.<name>]` (singular). Per `dump_state`, the
            # `adapter` field is omitted when it equals the default
            # ("claude-code") — the implicit-default contract that
            # pre-dates RFC-0012. So we accept both "field absent" and
            # `field == "claude-code"` for the default case.
            state = _load_state(adopter)
            pack_state = state.get("pack", {}).get("core", {})
            recorded_adapter = pack_state.get("adapter", "claude-code")
            self.assertEqual(
                recorded_adapter,
                expected_adapter,
                f"state.adapter mismatch: {pack_state!r}",
            )

    def test_claude_code_default_no_adapter_flag(self) -> None:
        """No `--adapter` → DEFAULT_ADAPTER (claude-code) → `.claude/`."""
        self._install_and_assert(
            adapter_flag=None,
            expected_adapter="claude-code",
            expected_dir=".claude",
        )

    def test_kiro_explicit_adapter(self) -> None:
        self._install_and_assert(
            adapter_flag="kiro",
            expected_adapter="kiro",
            expected_dir=".kiro",
        )

    def test_codex_explicit_adapter(self) -> None:
        self._install_and_assert(
            adapter_flag="codex",
            expected_adapter="codex",
            expected_dir=".agents/skills",
        )

    def test_copilot_explicit_adapter(self) -> None:
        """Copilot's projection target is `.github/instructions/`."""
        self._install_and_assert(
            adapter_flag="copilot",
            expected_adapter="copilot",
            expected_dir=".github/instructions",
        )


class RepoScopeEmitInstallRoutesTests(unittest.TestCase):
    """`--emit-install-routes` falls back to the dist-tree shape."""

    def test_emit_install_routes_writes_dist_tree(self) -> None:
        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            rc, stdout, stderr = _run_install(
                [
                    "--pack",
                    "core",
                    "--scope",
                    "repo",
                    "--emit-install-routes",
                    "--output",
                    str(adopter),
                    str(REPO_ROOT),
                ]
            )
            self.assertEqual(
                rc, 0, f"install failed:\nstdout={stdout}\nstderr={stderr}"
            )

            # Dist-tree shape present.
            self.assertTrue(
                (adopter / "claude-plugins" / "core").exists(),
                f"expected claude-plugins/core/ under {adopter}",
            )
            self.assertTrue(
                (adopter / "apm" / "core").exists(),
                f"expected apm/core/ under {adopter}",
            )

            # No per-IDE directory landed (the dist-tree producer
            # doesn't write to `.claude/`, `.kiro/`, etc.).
            self.assertFalse(
                (adopter / ".claude" / "skills").exists(),
                "unexpected per-IDE projection alongside dist-tree",
            )

            # Stdout carries the route-list summary AND the recap.
            self.assertIn("emitted install routes for core at", stdout)
            self.assertIn(" and ", stdout)  # the N=2 join rule
            self.assertIn("installed: core @ repo", stdout)


def _clear_inband_detection_seen() -> None:
    """Reset the once-per-session detection set between cases."""
    from agentbundle.commands import install as _install_mod

    _install_mod._clear_inband_detection_seen()


def _plant_state_row(
    adopter: Path,
    *,
    pack_name: str,
    adapter: str = "claude-code",
    installed_version: str = "0.1.0",
) -> None:
    """Write a minimal v0.3 state.toml with a single ``[pack.<name>]`` row.

    Mirrors the fixture helper in
    :mod:`tests.unit.test_install_inband_detection` — kept local rather
    than imported to keep this module self-contained for the integration
    suite.
    """
    import textwrap

    adapter_line = ""
    if adapter != "claude-code":
        adapter_line = f'adapter = "{adapter}"\n'
    state_path = adopter / ".agentbundle-state.toml"
    state_path.write_text(
        textwrap.dedent(
            f"""\
            schema-version = "0.3"

            [pack.{pack_name}]
            installed-version = "{installed_version}"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "repo"
            {adapter_line}"""
        ),
        encoding="utf-8",
    )


class RepoScopeUpgradeWithStateHintTests(unittest.TestCase):
    """AC33 upgrade-with-state-hint case — **defensive regression pin**.

    The spec asks for "AC10b parity at repo scope". AC10b proper (the
    state-hint short-circuit inside ``_resolve_target_adapter``) is
    not exercised at repo-scope upgrade today because
    ``upgrade.py:230+`` only invokes the resolver when
    ``effective_scope == "user"`` — repo scope falls through to
    ``render_pack`` (dist-tree shape). The cross-adapter refusal at
    ``upgrade.py:371-379`` is structurally unreachable at repo scope
    by the same gating.

    This test pins that structure: ``state.adapter`` stays ``"kiro"``
    after a repo-scope upgrade, and the ``pack adapter changed``
    refusal does not fire. A future refactor that extends the
    cross-adapter refusal block to repo scope without also threading
    the state-hint short-circuit would break this test — that's the
    regression the pin catches. Lifting repo-scope upgrade onto the
    per-IDE projection path is explicitly Ask-first in the spec; if
    that lift lands, this test wants tightening (assert the resolver
    *was* called with ``state_adapter=pack_state.adapter``)."""

    def setUp(self) -> None:
        _clear_inband_detection_seen()

    def test_upgrade_state_hint_keeps_kiro_no_cross_adapter_refusal(self) -> None:
        from agentbundle.cli import _build_parser
        from agentbundle.commands import install, upgrade

        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            parser = _build_parser()

            # Step 1: install --adapter kiro.
            args = parser.parse_args(
                [
                    "install",
                    "--pack", "core",
                    "--scope", "repo",
                    "--adapter", "kiro",
                    "--output", str(adopter),
                    str(REPO_ROOT),
                ]
            )
            rc = install.run(args)
            self.assertEqual(rc, 0)
            state = _load_state(adopter)
            self.assertEqual(
                state["pack"]["core"].get("adapter"), "kiro",
                f"install did not record adapter=kiro: {state!r}",
            )

            # Step 2: populate <repo>/.claude/ to simulate the
            # adopter having Claude Code state present alongside Kiro.
            # AC10b parity: the resolver's state-hint short-circuit
            # must prefer state.adapter (kiro) over any heuristic that
            # would route to claude-code on observing this directory.
            claude_dir = adopter / ".claude" / "skills" / "marker"
            claude_dir.mkdir(parents=True)
            (claude_dir / "SKILL.md").write_text(
                "---\nname: marker\ndescription: claude-state\n---\nBody.",
                encoding="utf-8",
            )

            # Step 3: upgrade.
            upgrade_args = parser.parse_args(
                [
                    "upgrade",
                    "--pack", "core",
                    "--to", "0.1.0",
                    str(REPO_ROOT),
                    "--root", str(adopter),
                    "--scope", "repo",
                ]
            )
            err_buf = io.StringIO()
            with redirect_stderr(err_buf):
                _rc = upgrade.run(upgrade_args)
            stderr = err_buf.getvalue()

            # The cross-adapter refusal text from upgrade.py:371-379
            # must not fire at repo scope. Pinning the exact substring
            # makes a future refactor that extends the refusal block
            # to repo scope (without state-hint) trip this assertion.
            self.assertNotIn("pack adapter changed", stderr)

            # State row's adapter stays kiro regardless of the upgrade's
            # outcome (the test pins state preservation, not upgrade
            # success — repo-scope upgrade still goes through the
            # dist-tree renderer today; per-IDE upgrade at repo scope
            # is a future RFC's surface).
            state_after = _load_state(adopter)
            recorded_after = (
                state_after.get("pack", {}).get("core", {}).get("adapter", "claude-code")
            )
            self.assertEqual(
                recorded_after, "kiro",
                f"state.adapter regressed post-upgrade: {state_after!r}",
            )


class RepoScopeMigrationTriggerBTests(unittest.TestCase):
    """AC33 + AC24(b): a pre-RFC-0012 state file plus on-disk dist-tree
    files refuses the install with the pinned (b) message."""

    def setUp(self) -> None:
        _clear_inband_detection_seen()

    def test_b_shape_mismatch_e2e_real_pack(self) -> None:
        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            _plant_state_row(adopter, pack_name="core")
            # Plant dist-tree files (legacy producer shape).
            (adopter / "claude-plugins" / "core").mkdir(parents=True)
            (adopter / "claude-plugins" / "core" / "plugin.json").write_text(
                "{}", encoding="utf-8"
            )
            (adopter / "apm" / "core").mkdir(parents=True)
            (adopter / "apm" / "core" / "pack.toml").write_text(
                "", encoding="utf-8"
            )

            rc, stdout, stderr = _run_install(
                [
                    "--pack", "core",
                    "--scope", "repo",
                    "--output", str(adopter),
                    str(REPO_ROOT),
                ]
            )
            self.assertNotEqual(rc, 0)
            self.assertIn("pre-RFC-0012 dist-tree files for pack core", stderr)
            # Platform-portable: separate segments avoid the Windows
            # path-separator (``\\``) breaking the joined substring.
            self.assertIn("claude-plugins", stderr)
            self.assertIn("apm", stderr)
            self.assertIn("rerun with --force", stderr)


class RepoScopeMigrationTriggerATests(unittest.TestCase):
    """AC33 + AC24(a): a pre-RFC-0012 state file whose recorded adapter
    disagrees with the resolver's pick (and no dist-tree files) refuses
    the install with the pinned (a) message."""

    def setUp(self) -> None:
        _clear_inband_detection_seen()

    def test_a_adapter_disagreement_e2e_real_pack(self) -> None:
        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            # State records claude-code; CLI passes --adapter kiro.
            _plant_state_row(adopter, pack_name="core", adapter="claude-code")
            # No dist-tree files → (b) does not fire; (a) does.

            rc, stdout, stderr = _run_install(
                [
                    "--pack", "core",
                    "--scope", "repo",
                    "--adapter", "kiro",
                    "--output", str(adopter),
                    str(REPO_ROOT),
                ]
            )
            self.assertNotEqual(rc, 0)
            self.assertIn(
                "state records adapter 'claude-code' for pack core", stderr
            )
            self.assertIn("resolver picked 'kiro'", stderr)


if __name__ == "__main__":
    unittest.main()
