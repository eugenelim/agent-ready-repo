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

Deferred to follow-up: cross-adapter upgrade with state-hint, the
three migration triggers (b/a/c), and the (b)+(c) precedence test.
The orphan-recovery case (c) ships in the unit tests already.
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


if __name__ == "__main__":
    unittest.main()
