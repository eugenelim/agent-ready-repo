"""T12: user-scope refusal rails — seeds / hooks / marker.

Verifies AC #16 (RFC-0004) for the distribution-adapters spec. The rails
fire only when a pack declares `"user" ∈ allowed-scopes` — repo-only
packs are not inspected, so SKILL.md files that *document* the marker
syntax (e.g. `adapt-to-project`) are not refused because their packs
declare `allowed-scopes = ["repo"]`.

Each test builds its fixture in a `tempfile.TemporaryDirectory()` to
keep the build/ fixtures tree small and to make the marker-byte tests
explicit about what's on disk.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path


PACK_TOML_USER_OK = """
[pack]
name = "demo-user"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "user"
allowed-scopes = ["user"]
"""

PACK_TOML_REPO_ONLY = """
[pack]
name = "demo-repo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""


def _write_pack(root: Path, name: str, toml_text: str) -> Path:
    pack = root / name
    pack.mkdir()
    (pack / "pack.toml").write_text(toml_text)
    return pack


class RailASeedsTests(unittest.TestCase):
    """A non-empty seeds/ with allowed-scopes=['user'] is refused."""

    def test_rail_a_refuses_seeds_with_user_scope(self) -> None:
        from agentbundle.build.scope_rails import check_seeds

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            (pack / "seeds").mkdir()
            (pack / "seeds" / "AGENTS.md").write_text("hi")

            result = check_seeds(pack, ["user"])
            self.assertIsNotNone(result)
            self.assertIn("seeds/AGENTS.md", result)

    def test_rail_a_accepts_seeds_with_repo_only(self) -> None:
        from agentbundle.build.scope_rails import check_seeds

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_REPO_ONLY)
            (pack / "seeds").mkdir()
            (pack / "seeds" / "AGENTS.md").write_text("hi")

            self.assertIsNone(check_seeds(pack, ["repo"]))

    def test_rail_a_accepts_empty_seeds(self) -> None:
        from agentbundle.build.scope_rails import check_seeds

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            (pack / "seeds").mkdir()
            self.assertIsNone(check_seeds(pack, ["user"]))


class RailBHooksTests(unittest.TestCase):
    """A non-empty .apm/hooks/ or .apm/hook-wiring/ with user scope is refused."""

    def test_rail_b_refuses_hook_body_with_user_scope(self) -> None:
        from agentbundle.build.scope_rails import check_hooks

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            (pack / ".apm" / "hooks").mkdir(parents=True)
            (pack / ".apm" / "hooks" / "pre-pr.sh").write_text("#!/bin/sh\n")

            result = check_hooks(pack, ["user"])
            self.assertIsNotNone(result)
            self.assertIn(".apm/hooks/pre-pr.sh", result)

    def test_rail_b_refuses_hook_wiring_with_user_scope(self) -> None:
        from agentbundle.build.scope_rails import check_hooks

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            (pack / ".apm" / "hook-wiring").mkdir(parents=True)
            (pack / ".apm" / "hook-wiring" / "pre-pr.toml").write_text("[hooks]\n")

            result = check_hooks(pack, ["user"])
            self.assertIsNotNone(result)
            self.assertIn(".apm/hook-wiring/pre-pr.toml", result)

    def test_rail_b_accepts_hooks_with_repo_only(self) -> None:
        from agentbundle.build.scope_rails import check_hooks

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_REPO_ONLY)
            (pack / ".apm" / "hooks").mkdir(parents=True)
            (pack / ".apm" / "hooks" / "pre-pr.sh").write_text("#!/bin/sh\n")
            self.assertIsNone(check_hooks(pack, ["repo"]))

    def test_rail_b_accepts_no_hooks(self) -> None:
        from agentbundle.build.scope_rails import check_hooks

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            self.assertIsNone(check_hooks(pack, ["user"]))

    def test_rail_b_lifts_when_user_scope_hooks_true(self) -> None:
        """RFC-0005 § Rail B — user-scope lift: a pack that opts in via
        ``user-scope-hooks = true`` is accepted even with hooks at user
        scope. The flag is the consent gesture."""
        from agentbundle.build.scope_rails import check_hooks

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            (pack / ".apm" / "hooks").mkdir(parents=True)
            (pack / ".apm" / "hooks" / "pre-pr.sh").write_text("#!/bin/sh\nexit 0\n")
            self.assertIsNone(
                check_hooks(pack, ["user"], user_scope_hooks=True),
                "Rail B did not lift on user_scope_hooks=True",
            )

    def test_rail_b_refuses_without_user_scope_hooks_default(self) -> None:
        """The default (user_scope_hooks=False) preserves the v0.2 refusal
        behaviour — a pack with hooks at user scope is refused."""
        from agentbundle.build.scope_rails import check_hooks

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            (pack / ".apm" / "hooks").mkdir(parents=True)
            (pack / ".apm" / "hooks" / "pre-pr.sh").write_text("#!/bin/sh\nexit 0\n")
            # Default (no flag passed) — must refuse.
            self.assertIsNotNone(check_hooks(pack, ["user"]))
            # Explicit False — same refusal.
            self.assertIsNotNone(check_hooks(pack, ["user"], user_scope_hooks=False))


class RailCMarkersTests(unittest.TestCase):
    """`<adapt:NAME>` markers under .apm/skills/, /agents/, /commands/ refused."""

    def test_rail_c_refuses_upper_snake_marker_in_skill_with_user_scope(self) -> None:
        """Legacy UPPER_SNAKE form `<adapt:NAME>` is refused."""
        from agentbundle.build.scope_rails import check_markers

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            skills_dir = pack / ".apm" / "skills" / "my-skill"
            skills_dir.mkdir(parents=True)
            (skills_dir / "SKILL.md").write_text(
                "# My skill\n\nDoes <adapt:PROJECT_NAME> things.\n"
            )

            result = check_markers(pack, ["user"])
            self.assertIsNotNone(result)
            self.assertIn(".apm/skills/my-skill/SKILL.md", result)

    def test_rail_c_refuses_lowercase_hyphen_marker_in_skill_with_user_scope(self) -> None:
        """Canonical lowercase-hyphen form `<adapt:project-name>` is refused.

        Closes the AC21 carve-out: until the code-side widening, a
        user-scope pack carrying the canonical marker form passed
        `validate` in code even though the spec contract refused it.
        """
        from agentbundle.build.scope_rails import check_markers

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            skills_dir = pack / ".apm" / "skills" / "my-skill"
            skills_dir.mkdir(parents=True)
            (skills_dir / "SKILL.md").write_text(
                "# My skill\n\nDoes <adapt:project-name> things.\n"
            )

            result = check_markers(pack, ["user"])
            self.assertIsNotNone(result)
            self.assertIn(".apm/skills/my-skill/SKILL.md", result)

    def test_rail_c_refuses_lowercase_marker_in_agent_with_user_scope(self) -> None:
        """Canonical form is refused under `.apm/agents/` too (rail directory coverage)."""
        from agentbundle.build.scope_rails import check_markers

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            agents_dir = pack / ".apm" / "agents"
            agents_dir.mkdir(parents=True)
            (agents_dir / "reviewer.md").write_text("Owner: <adapt:owner>\n")

            result = check_markers(pack, ["user"])
            self.assertIsNotNone(result)
            self.assertIn(".apm/agents/reviewer.md", result)

    def test_rail_c_accepts_non_marker_strings(self) -> None:
        """Strings that resemble markers but don't match either grammar pass.

        Wrong-cased prefix `<ADAPT:NAME>` and mixed-case names like
        `<adapt:MixedCase>` are not valid markers under either casing
        and must not trigger the rail.
        """
        from agentbundle.build.scope_rails import check_markers

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            skills_dir = pack / ".apm" / "skills" / "non-markers"
            skills_dir.mkdir(parents=True)
            # Wrong-cased prefix — must not match either grammar.
            (skills_dir / "A.md").write_text("plays with <ADAPT:NAME>")
            # Mixed-case name — matches neither UPPER_SNAKE nor lowercase-hyphen.
            (skills_dir / "B.md").write_text("plays with <adapt:MixedCase>")
            # Empty name — matches neither grammar.
            (skills_dir / "C.md").write_text("plays with <adapt:>")
            self.assertIsNone(check_markers(pack, ["user"]))

    def test_rail_c_does_not_inspect_repo_only_pack(self) -> None:
        """Repo-only packs are not inspected — the rail's scope clause stops it."""
        from agentbundle.build.scope_rails import check_markers

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_REPO_ONLY)
            skills_dir = pack / ".apm" / "skills" / "doc-marker"
            skills_dir.mkdir(parents=True)
            (skills_dir / "SKILL.md").write_text("documents <adapt:NAME>")
            self.assertIsNone(check_markers(pack, ["repo"]))

    def test_rail_c_skips_binary_files(self) -> None:
        """Non-UTF-8 files are skipped silently."""
        from agentbundle.build.scope_rails import check_markers

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            skills_dir = pack / ".apm" / "skills" / "with-binary"
            skills_dir.mkdir(parents=True)
            # Raw bytes that are not valid UTF-8 — should be skipped.
            (skills_dir / "icon.bin").write_bytes(b"\xff\xfe\x00<adapt:NAME>")
            # A clean text file in the same directory.
            (skills_dir / "SKILL.md").write_text("# clean\n")
            self.assertIsNone(check_markers(pack, ["user"]))

    def test_rail_c_refuses_symlink_under_skills(self) -> None:
        """RFC-0004 Rail C must refuse symlinks under primitive dirs.

        A `*.md → /dev/zero` symlink would bypass the size cap because
        `stat()` follows the symlink and reports the target's
        size (zero for /dev/zero). The lstat-based detection refuses
        symlinks outright so the cap holds.
        """
        from agentbundle.build.scope_rails import check_markers
        import os as _os

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            skills_dir = pack / ".apm" / "skills" / "symlink-skill"
            skills_dir.mkdir(parents=True)
            # Create a symlink — target need not exist; the rail
            # refuses on the symlink type alone.
            _os.symlink("/dev/null", skills_dir / "SKILL.md")
            result = check_markers(pack, ["user"])
            self.assertIsNotNone(result)
            self.assertIn("symlink", result)

    def test_rail_c_refuses_oversize_file(self) -> None:
        """Files larger than the size cap are refused before being read."""
        from agentbundle.build.scope_rails import check_markers, _MARKER_RAIL_FILE_CAP_BYTES

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            skills_dir = pack / ".apm" / "skills" / "oversize"
            skills_dir.mkdir(parents=True)
            # Sparse file slightly larger than the cap — no marker payload needed.
            big = skills_dir / "SKILL.md"
            with open(big, "wb") as fh:
                fh.seek(_MARKER_RAIL_FILE_CAP_BYTES + 1)
                fh.write(b"\0")
            result = check_markers(pack, ["user"])
            self.assertIsNotNone(result)
            self.assertIn("size cap", result)

    def test_rail_c_deterministic_first_offender(self) -> None:
        """sorted(os.walk(...)) order — `a/` comes before `b/`."""
        from agentbundle.build.scope_rails import check_markers

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            for sub in ("z-late", "a-early"):
                d = pack / ".apm" / "skills" / sub
                d.mkdir(parents=True)
                (d / "SKILL.md").write_text("hi <adapt:NAME>")
            result = check_markers(pack, ["user"])
            self.assertIsNotNone(result)
            self.assertIn("a-early/SKILL.md", result)


class CliValidateSpecNamedStderrTests(unittest.TestCase):
    """`validate` emits the spec-named text on the cross-field invariant."""

    def test_default_scope_not_in_allowed_scopes_emits_spec_text(self) -> None:
        import argparse
        import io
        import contextlib

        from agentbundle.commands import validate as validate_cmd

        with tempfile.TemporaryDirectory() as td:
            pack = Path(td) / "p"
            pack.mkdir()
            (pack / "pack.toml").write_text(
                """
[pack]
name = "demo-invariant"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "user"
allowed-scopes = ["repo"]
""",
                encoding="utf-8",
            )
            args = argparse.Namespace(pack_path=str(pack), strict=False)
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                rc = validate_cmd.run(args)
            self.assertEqual(rc, 1)
            err = buf.getvalue()
            # Spec contract text (RFC-0004 last AC for agent-spec-cli).
            self.assertIn("default-scope", err)
            self.assertIn("'user'", err)
            self.assertIn("allowed-scopes", err)
            self.assertIn("demo-invariant", err)


class CliValidateWiringTests(unittest.TestCase):
    """The CLI's `validate` subcommand surfaces rail refusals to stderr."""

    def test_validate_refuses_user_scope_pack_with_hooks(self) -> None:
        import argparse
        import io
        import contextlib

        from agentbundle.commands import validate as validate_cmd

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            (pack / ".apm" / "hooks").mkdir(parents=True)
            (pack / ".apm" / "hooks" / "pre-pr.sh").write_text("#!/bin/sh\n")

            args = argparse.Namespace(pack_path=str(pack), strict=False)
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                rc = validate_cmd.run(args)
            self.assertEqual(rc, 1)
            self.assertIn("demo-user", buf.getvalue())
            self.assertIn(".apm/hooks/pre-pr.sh", buf.getvalue())

    def test_validate_accepts_user_scope_pack_with_no_offenders(self) -> None:
        import argparse

        from agentbundle.commands import validate as validate_cmd

        with tempfile.TemporaryDirectory() as td:
            pack = _write_pack(Path(td), "p", PACK_TOML_USER_OK)
            args = argparse.Namespace(pack_path=str(pack), strict=False)
            self.assertEqual(validate_cmd.run(args), 0)


if __name__ == "__main__":
    unittest.main()
