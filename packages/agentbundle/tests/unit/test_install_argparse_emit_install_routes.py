"""Unit tests for the `--emit-install-routes` flag and the handler-level
mutex with `--adapter` at `--scope repo` (RFC-0012 / repo-scope-per-
adapter-projection AC14-AC17, AC32).

Covers:

  - `--emit-install-routes` parses at both scopes (argparse-level
    admission; handler enforces the binding to `--scope repo`).
  - The old user-scope-only `--adapter` binding is gone — passing
    `--adapter X --scope repo` no longer surfaces the legacy
    `install: --adapter is bound to --scope user` line.
  - `--emit-install-routes` at `--scope user` is refused with the
    pinned `install: --emit-install-routes is bound to --scope repo`.
  - `--adapter X --emit-install-routes` at `--scope repo` is refused
    with the pinned mutex message.
  - The mutex consults the *resolved* scope (`requested_scope`), not
    `args.scope`, so a pack whose `[scope] default-scope = "user"`
    surfaces the binding even when `--scope` is omitted.
  - The implementation does NOT use `argparse.add_mutually_exclusive_group`
    (the exclusion is scope-conditional).
"""

from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class EmitInstallRoutesArgparseTests(unittest.TestCase):
    """argparse-level admission — both scopes accept the flag."""

    def test_flag_admitted_at_repo_scope(self) -> None:
        from agentbundle.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(
            [
                "install",
                "--pack",
                "demo",
                "--scope",
                "repo",
                "--emit-install-routes",
                ".",
            ]
        )
        self.assertTrue(args.emit_install_routes)

    def test_flag_admitted_at_user_scope_at_argparse_layer(self) -> None:
        """argparse-level: the flag parses; the handler enforces the
        binding refusal."""
        from agentbundle.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(
            [
                "install",
                "--pack",
                "demo",
                "--scope",
                "user",
                "--emit-install-routes",
                ".",
            ]
        )
        self.assertTrue(args.emit_install_routes)

    def test_no_mutually_exclusive_group_for_flags(self) -> None:
        """The exclusion is scope-conditional, so argparse-level
        `add_mutually_exclusive_group` is the wrong tool — assert the
        install subparser does NOT register a mutex group covering
        --adapter / --emit-install-routes."""
        from agentbundle.cli import _build_parser

        parser = _build_parser()
        install_sp = parser._subparsers._group_actions[0].choices["install"]
        for group in install_sp._mutually_exclusive_groups:
            actions = [a.option_strings for a in group._group_actions]
            for opts in actions:
                self.assertNotIn("--adapter", opts)
                self.assertNotIn("--emit-install-routes", opts)


def _make_minimal_pack(root: Path, name: str = "demo", default_scope: str = "repo") -> Path:
    """Create a minimal pack.toml fixture sufficient to drive install
    through to the handler-level mutex check."""
    pack_dir = root / name
    pack_dir.mkdir(parents=True)
    pack_toml = textwrap.dedent(
        f"""\
        [pack]
        name = "{name}"
        version = "0.1.0"
        spec-version = "0.6"

        [pack.adapter-contract]
        version = "0.7"

        [pack.install]
        default-scope = "{default_scope}"
        allowed-scopes = ["repo", "user"]
        allowed-adapters = ["claude-code", "kiro"]
        """
    )
    (pack_dir / "pack.toml").write_text(pack_toml, encoding="utf-8")
    return pack_dir


class HandlerLevelMutexTests(unittest.TestCase):
    """Handler-level refusals — assert exact stderr text + non-zero exit."""

    def _run_install(self, argv: list[str], capsys=None):
        """Invoke install.run via the argparse layer; capture stderr."""
        import io
        import sys
        from contextlib import redirect_stderr

        from agentbundle.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["install"] + argv)
        buf = io.StringIO()
        with redirect_stderr(buf):
            from agentbundle.commands import install

            rc = install.run(args)
        return rc, buf.getvalue()

    def test_emit_install_routes_at_user_scope_refused(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            packs_dir = root / "packs"
            packs_dir.mkdir()
            _make_minimal_pack(packs_dir, "demo", default_scope="user")
            output_root = root / "adopter"
            output_root.mkdir()
            rc, stderr = self._run_install(
                [
                    "--pack",
                    "demo",
                    "--scope",
                    "user",
                    "--emit-install-routes",
                    "--output",
                    str(output_root),
                    str(packs_dir),
                ]
            )
            self.assertNotEqual(rc, 0)
            self.assertIn(
                "install: --emit-install-routes is bound to --scope repo",
                stderr,
            )

    def test_adapter_with_emit_install_routes_at_repo_refused(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            packs_dir = root / "packs"
            packs_dir.mkdir()
            _make_minimal_pack(packs_dir, "demo", default_scope="repo")
            output_root = root / "adopter"
            output_root.mkdir()
            rc, stderr = self._run_install(
                [
                    "--pack",
                    "demo",
                    "--scope",
                    "repo",
                    "--adapter",
                    "kiro",
                    "--emit-install-routes",
                    "--output",
                    str(output_root),
                    str(packs_dir),
                ]
            )
            self.assertNotEqual(rc, 0)
            self.assertIn(
                "install: --adapter and --emit-install-routes are "
                "mutually exclusive at --scope repo",
                stderr,
            )

    def test_emit_install_routes_via_pack_default_scope_user(self) -> None:
        """The mutex consults requested_scope, not args.scope. A pack
        whose `default-scope = "user"` with no CLI --scope flag still
        surfaces the binding refusal when --emit-install-routes is
        passed."""
        with TemporaryDirectory() as raw:
            root = Path(raw)
            packs_dir = root / "packs"
            packs_dir.mkdir()
            _make_minimal_pack(packs_dir, "demo", default_scope="user")
            output_root = root / "adopter"
            output_root.mkdir()
            rc, stderr = self._run_install(
                [
                    "--pack",
                    "demo",
                    # No --scope; pack default-scope is user.
                    "--emit-install-routes",
                    "--output",
                    str(output_root),
                    str(packs_dir),
                ]
            )
            self.assertNotEqual(rc, 0)
            self.assertIn(
                "install: --emit-install-routes is bound to --scope repo",
                stderr,
            )


class AdapterBindingRemovedTests(unittest.TestCase):
    """RFC-0012 AC15 — the user-scope-only --adapter binding is gone."""

    def test_adapter_at_repo_scope_no_longer_refused_at_binding_layer(self) -> None:
        """Verify `--adapter X --scope repo` doesn't surface the
        legacy pinned `install: --adapter is bound to --scope user`
        text. (The install may still fail later — e.g. nonexistent
        pack — but not at the bound-to-user-scope check.)"""
        import io
        from contextlib import redirect_stderr

        from agentbundle.cli import _build_parser
        from agentbundle.commands import install

        with TemporaryDirectory() as raw:
            root = Path(raw)
            packs_dir = root / "packs"
            packs_dir.mkdir()
            _make_minimal_pack(packs_dir, "demo", default_scope="repo")
            output_root = root / "adopter"
            output_root.mkdir()

            parser = _build_parser()
            args = parser.parse_args(
                [
                    "install",
                    "--pack",
                    "demo",
                    "--scope",
                    "repo",
                    "--adapter",
                    "kiro",
                    "--output",
                    str(output_root),
                    str(packs_dir),
                ]
            )
            buf = io.StringIO()
            with redirect_stderr(buf):
                install.run(args)
            stderr = buf.getvalue()
            self.assertNotIn(
                "--adapter is bound to --scope user",
                stderr,
            )


if __name__ == "__main__":
    unittest.main()
