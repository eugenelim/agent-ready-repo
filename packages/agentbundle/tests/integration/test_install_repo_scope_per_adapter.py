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
        """Copilot's skill projection target is `.github/skills/` (v0.11
        copilot-skills-and-web: first-class Agent Skills, was
        `.github/instructions/`)."""
        self._install_and_assert(
            adapter_flag="copilot",
            expected_adapter="copilot",
            expected_dir=".github/skills",
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
    """AC33 upgrade-with-state-hint case — **AC10b parity at repo scope**.

    Now that repo-scope upgrade routes through
    ``_render_for_repo_scope`` (mirroring install), AC10b is real at
    this scope: ``upgrade.run`` invokes ``_resolve_target_adapter``
    with ``state_adapter=pack_state.adapter`` so a Kiro-installed
    pack stays on Kiro even when the resolver's legacy heuristic
    would otherwise pick Claude Code on observing a populated
    ``<repo>/.claude/`` directory.

    Pin: install ``--adapter kiro``, plant a Claude Code marker
    under ``.claude/skills/``, run an upgrade with no flags. Assert
    (a) ``state.adapter`` stays ``"kiro"``, (b) the cross-adapter
    ``pack adapter changed`` refusal does not fire, (c) the
    post-upgrade projection lands at ``.kiro/`` — the load-bearing
    evidence the resolver was called with the state-hint and routed
    to Kiro (a regression to ``render_pack`` or to the unhinted
    resolver would re-emit dist-tree or ``.claude/`` shape)."""

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
            self.assertTrue(
                (adopter / ".kiro").exists(),
                f"install did not land .kiro/ projection under {adopter}",
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
                rc_upgrade = upgrade.run(upgrade_args)
            stderr = err_buf.getvalue()

            self.assertEqual(
                rc_upgrade, 0,
                f"upgrade must succeed at repo scope with state-hint; "
                f"stderr={stderr!r}",
            )

            # The cross-adapter refusal text from upgrade.py's
            # cross-adapter block must not fire at repo scope. Pinning
            # the exact substring makes a future refactor that extends
            # the refusal block to repo scope (without state-hint)
            # trip this assertion.
            self.assertNotIn("pack adapter changed", stderr)

            # State row's adapter stays kiro across the upgrade.
            state_after = _load_state(adopter)
            recorded_after = (
                state_after.get("pack", {}).get("core", {}).get("adapter", "claude-code")
            )
            self.assertEqual(
                recorded_after, "kiro",
                f"state.adapter regressed post-upgrade: {state_after!r}",
            )

            # Load-bearing evidence the resolver was called with
            # `state_adapter="kiro"` and that the per-IDE projection
            # landed (not the dist-tree producer's output): post-upgrade,
            # `.kiro/` is still on disk and no `apm/`, `claude-plugins/`,
            # or `marketplace.json` leaked into the adopter root.
            self.assertTrue(
                (adopter / ".kiro").exists(),
                f"upgrade dropped .kiro/ projection — resolver was not "
                f"called with state_adapter=kiro, or the per-IDE branch "
                f"was bypassed; tree: "
                f"{sorted(p.relative_to(adopter).as_posix() for p in adopter.rglob('*'))[:20]}",
            )
            self.assertFalse(
                (adopter / "apm").exists(),
                f"upgrade leaked apm/ subtree under {adopter}",
            )
            self.assertFalse(
                (adopter / "claude-plugins").exists(),
                f"upgrade leaked claude-plugins/ subtree under {adopter}",
            )
            self.assertFalse(
                (adopter / "marketplace.json").exists(),
                f"upgrade leaked marketplace.json under {adopter}",
            )


class RepoScopeSameVersionUpgradeStateFilesTests(unittest.TestCase):
    """Regression: same-version `upgrade` at repo scope must not
    silently re-shape `state.files` into the dist-tree projection nor
    drop `apm/<pack>/` and `claude-plugins/<pack>/` subtrees into the
    adopter's repo.

    The bug: pre-fix, `upgrade.run` at repo scope called
    `render.render_pack(pack_dir)` (the dist-tree producer used by
    `make build`), which emits `apm/<pack>/...` +
    `claude-plugins/<pack>/...` + `marketplace.json` keys. RFC-0012's
    install lift uses `_render_for_repo_scope` (per-IDE shape such as
    `.claude/skills/<name>/SKILL.md`). Same-version upgrade therefore
    (i) wrote the dist-tree subtree on top of the per-IDE install and
    (ii) accreted those paths into `state.files` while the
    install-time per-IDE entries lingered — net ~3× growth.

    Pin: install via the RFC-0012 default path, snapshot
    `state.files`, run `upgrade --to <same-version>`, then assert the
    keyset is byte-identical (same paths, no dist-tree leak) and no
    `apm/` or `claude-plugins/` directories appear under the adopter
    root."""

    def setUp(self) -> None:
        _clear_inband_detection_seen()

    def test_same_version_upgrade_does_not_corrupt_state_or_leak_dist_tree(self) -> None:
        from agentbundle.cli import _build_parser
        from agentbundle.commands import install, upgrade

        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            parser = _build_parser()

            # Step 1: install at repo scope (RFC-0012 default — no
            # `--emit-install-routes`, no `--adapter`).
            install_args = parser.parse_args(
                [
                    "install",
                    "--pack", "core",
                    "--scope", "repo",
                    "--output", str(adopter),
                    str(REPO_ROOT),
                ]
            )
            rc = install.run(install_args)
            self.assertEqual(rc, 0, "install of core must succeed")

            state_before = _load_state(adopter)
            files_before = set(
                state_before["pack"]["core"].get("files", {}).keys()
            )
            self.assertTrue(
                files_before,
                "install must record at least one entry in state.files",
            )
            # Per-IDE projection — no dist-tree-shaped paths recorded.
            for relpath in files_before:
                self.assertFalse(
                    relpath.startswith("apm/")
                    or relpath.startswith("claude-plugins/")
                    or relpath == "marketplace.json",
                    f"install recorded unexpected dist-tree path {relpath!r}; "
                    f"all paths: {sorted(files_before)}",
                )

            # Step 2: upgrade to the same version. The pack's `version`
            # in `packs/core/pack.toml` is the source of truth; pin via
            # the state row so the test stays valid through bumps.
            installed_version = state_before["pack"]["core"]["installed-version"]
            upgrade_args = parser.parse_args(
                [
                    "upgrade",
                    "--pack", "core",
                    "--to", installed_version,
                    str(REPO_ROOT),
                    "--root", str(adopter),
                    "--scope", "repo",
                ]
            )
            rc = upgrade.run(upgrade_args)
            self.assertEqual(
                rc, 0, "same-version upgrade at repo scope must succeed"
            )

            # Step 3: `state.files` keyset must match the install
            # snapshot — same paths, no dist-tree leak.
            state_after = _load_state(adopter)
            files_after = set(
                state_after["pack"]["core"].get("files", {}).keys()
            )
            new_keys = files_after - files_before
            self.assertFalse(
                new_keys,
                f"upgrade added new entries to state.files: "
                f"{sorted(new_keys)}",
            )
            stale_keys = files_before - files_after
            self.assertFalse(
                stale_keys,
                f"upgrade dropped install-time entries from state.files: "
                f"{sorted(stale_keys)}",
            )

            # Step 4: the adopter tree must not have grown a
            # `claude-plugins/` or `apm/` subtree under the repo root.
            self.assertFalse(
                (adopter / "claude-plugins").exists(),
                f"upgrade leaked claude-plugins/ subtree under {adopter}; "
                f"tree: {sorted(p.relative_to(adopter).as_posix() for p in adopter.rglob('*'))[:20]}",
            )
            self.assertFalse(
                (adopter / "apm").exists(),
                f"upgrade leaked apm/ subtree under {adopter}",
            )
            self.assertFalse(
                (adopter / "marketplace.json").exists(),
                f"upgrade leaked marketplace.json under {adopter}",
            )


class RepoScopeDiffAfterInstallTests(unittest.TestCase):
    """Regression: `diff` against a freshly-installed pack at repo scope
    must report no drift.

    The bug: pre-fix, `diff.run` unconditionally rendered the dist-tree
    shape via `render.render_pack`, but RFC-0012's install lift landed
    files at `<repo>/.claude/...` (or `.kiro/...`, etc.). The two
    shapes never overlap, so diff returned exit 1 with every per-IDE
    file flagged as missing — and any in-place adopter edit slipped
    past detection because diff was looking at the wrong tree."""

    def setUp(self) -> None:
        _clear_inband_detection_seen()

    def test_diff_after_install_reports_no_drift(self) -> None:
        from agentbundle.cli import _build_parser
        from agentbundle.commands import diff, install

        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            parser = _build_parser()

            install_args = parser.parse_args(
                [
                    "install",
                    "--pack", "core",
                    "--scope", "repo",
                    "--output", str(adopter),
                    str(REPO_ROOT),
                ]
            )
            rc = install.run(install_args)
            self.assertEqual(rc, 0, "install must succeed")

            diff_args = parser.parse_args(
                [
                    "diff",
                    str(REPO_ROOT / "packs" / "core"),
                    "--root", str(adopter),
                ]
            )
            out_buf, err_buf = io.StringIO(), io.StringIO()
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                rc = diff.run(diff_args)

            self.assertEqual(
                rc, 0,
                f"diff must report exit 0 when nothing has drifted post-install; "
                f"stdout={out_buf.getvalue()!r} stderr={err_buf.getvalue()!r}",
            )
            self.assertEqual(
                out_buf.getvalue().strip(), "",
                f"diff must produce no stdout when in sync; got: {out_buf.getvalue()!r}",
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
