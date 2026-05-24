"""T8a: state-file schema v0.3 — additive bump + header-only migration.

Covers acceptance criteria AC20, AC21, AC22 from spec.md and the plan
T8a Tests subsection.

Read-time defaults (RFC-0005 § State-file impact):
  - Absent ``adapter`` on a row → ``"claude-code"``.
  - Absent ``target-file`` on a claude-code row → ``"~/.claude/settings.json"``.
  - Absent ``target-file`` on a kiro row → required; reader refuses.

Write-time refuse-and-explain:
  - Write paths against a v0.2 state file raise the v0.2 stale-schema
    refusal with the standard "run 'agentbundle init-state --migrate' first"
    text shape.

``init-state --migrate`` semantics:
  - v0.2 → v0.3 is **header-only**: rewrite only the schema-version line,
    no per-row backfill. Round-trip preserves every other byte (except
    final-newline normalisation).
  - v0.1 → v0.3 is the legacy full re-serialize path; lands at v0.3
    directly with the v0.1 → v0.2 scope-column backfill applied.
"""

from __future__ import annotations

import textwrap
import unittest
from pathlib import Path


class StateSchemaVersionTests(unittest.TestCase):
    def test_state_schema_version_is_0_3(self) -> None:
        from agentbundle import config

        self.assertEqual(config.STATE_SCHEMA_VERSION, "0.3")


class V03ReadTimeDefaultsTests(unittest.TestCase):
    """A v0.3 reader resolves absent optional fields to their declared defaults."""

    def test_absent_adapter_defaults_to_claude_code(self) -> None:
        """AC21: a v0.3 row with no ``adapter`` reads as ``claude-code``."""
        from agentbundle import config

        toml_text = textwrap.dedent("""
            schema-version = "0.3"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "user"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        path = _write_tmp(self, toml_text)
        state = config.load_state(path, for_write=False)
        self.assertEqual(state.schema_version, "0.3")
        self.assertEqual(state.packs["demo"].adapter, "claude-code")

    def test_absent_target_file_for_claude_code_defaults_to_settings(self) -> None:
        """AC21: claude-code rows with no ``target-file`` resolve to
        ``~/.claude/settings.json`` — the adapter's user-scope default."""
        from agentbundle import config

        toml_text = textwrap.dedent("""
            schema-version = "0.3"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "user"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        path = _write_tmp(self, toml_text)
        state = config.load_state(path, for_write=False)
        self.assertEqual(state.packs["demo"].target_file, "~/.claude/settings.json")

    def test_kiro_row_without_target_file_reads_as_none(self) -> None:
        """AC21: kiro rows have NO ``target-file`` default. The read path
        stays operationally tolerant — returns None — so ``init-state
        --migrate`` can still operate on a malformed v0.3. Consumers
        that need the field (T8b/T8c install / upgrade walkers)
        surface their own errors when they go to use it."""
        from agentbundle import config

        toml_text = textwrap.dedent("""
            schema-version = "0.3"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "user"
            adapter = "kiro"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        path = _write_tmp(self, toml_text)
        state = config.load_state(path, for_write=False)
        self.assertEqual(state.packs["demo"].adapter, "kiro")
        self.assertIsNone(state.packs["demo"].target_file)

    def test_kiro_row_with_target_file_accepted(self) -> None:
        from agentbundle import config

        toml_text = textwrap.dedent("""
            schema-version = "0.3"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "repo"
            adapter = "kiro"
            target-file = ".kiro/agents/reviewer.json"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        path = _write_tmp(self, toml_text)
        state = config.load_state(path, for_write=False)
        self.assertEqual(state.packs["demo"].adapter, "kiro")
        self.assertEqual(state.packs["demo"].target_file, ".kiro/agents/reviewer.json")

    def test_explicit_claude_code_target_file_overrides_default(self) -> None:
        """An explicit ``target-file`` always wins over the read-time default."""
        from agentbundle import config

        toml_text = textwrap.dedent("""
            schema-version = "0.3"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "repo"
            adapter = "claude-code"
            target-file = ".claude/settings.local.json"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        path = _write_tmp(self, toml_text)
        state = config.load_state(path, for_write=False)
        self.assertEqual(state.packs["demo"].target_file, ".claude/settings.local.json")


class HookWiringOwnedTests(unittest.TestCase):
    """AC20: rows grow an optional ``hook-wiring-owned`` array-of-tables."""

    def test_hook_wiring_owned_round_trip(self) -> None:
        from agentbundle import config

        toml_text = textwrap.dedent("""
            schema-version = "0.3"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "user"
            primitives = []

            [pack.demo.files]

            [[pack.demo.hook-wiring-owned]]
            event = "UserPromptSubmit"
            id = "demo:on-prompt"

            [[pack.demo.hook-wiring-owned]]
            event = "SessionStart"
            id = "demo:on-session"
        """).strip() + "\n"

        path = _write_tmp(self, toml_text)
        state = config.load_state(path, for_write=False)
        owned = state.packs["demo"].hook_wiring_owned
        self.assertEqual(len(owned), 2)
        self.assertEqual(owned[0]["event"], "UserPromptSubmit")
        self.assertEqual(owned[0]["id"], "demo:on-prompt")
        self.assertEqual(owned[1]["event"], "SessionStart")

    def test_absent_hook_wiring_owned_is_empty_list(self) -> None:
        from agentbundle import config

        toml_text = textwrap.dedent("""
            schema-version = "0.3"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "repo"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        path = _write_tmp(self, toml_text)
        state = config.load_state(path, for_write=False)
        self.assertEqual(state.packs["demo"].hook_wiring_owned, [])


class V02WriteRefusedTests(unittest.TestCase):
    """AC22: a v0.2 state file refuses write-capable load with the exact
    refuse-and-explain text the v0.1 → v0.2 migration established."""

    def test_v02_load_for_write_raises_legacy(self) -> None:
        from agentbundle import config

        toml_text = textwrap.dedent("""
            schema-version = "0.2"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "repo"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        path = _write_tmp(self, toml_text)
        with self.assertRaises(config.ConfigError) as ctx:
            config.load_state(path, for_write=True)
        self.assertIn("0.2", str(ctx.exception))
        self.assertIn("init-state --migrate", str(ctx.exception))

    def test_v02_load_for_read_still_works(self) -> None:
        """Read paths still parse v0.2 (legacy compatibility) — only writes refuse."""
        from agentbundle import config

        toml_text = textwrap.dedent("""
            schema-version = "0.2"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "repo"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        path = _write_tmp(self, toml_text)
        state = config.load_state(path, for_write=False)
        self.assertEqual(state.schema_version, "0.2")
        self.assertIn("demo", state.packs)


class V02MigrateHeaderOnlyTests(unittest.TestCase):
    """AC21: ``init-state --migrate`` on a v0.2 file rewrites only the
    schema-version line. Body bytes are preserved (no per-row backfill)."""

    def test_migrate_v02_to_v03_rewrites_only_version_line(self) -> None:
        import argparse

        from agentbundle.commands import init_state as cmd

        v02_text = textwrap.dedent("""
            schema-version = "0.2"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "repo"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        repo_root, state_path = _write_state_in_repo(self, v02_text)
        args = argparse.Namespace(
            migrate=True,
            scope="repo",
            root=str(repo_root),
        )
        rc = cmd.run(args)
        self.assertEqual(rc, 0)

        # Byte-level invariant: exactly the version line changes.
        new_text = state_path.read_text(encoding="utf-8")
        expected = v02_text.replace(
            'schema-version = "0.2"', 'schema-version = "0.3"', 1
        )
        self.assertEqual(
            new_text,
            expected,
            "migrate rewrote bytes outside the schema-version line",
        )

    def test_migrate_v03_to_v03_is_byte_identity(self) -> None:
        """Idempotence at the byte level — running ``--migrate`` against an
        already-v0.3 file must not strip explicit-default rows. Concern
        raised by adversarial review: the prior full-re-serialize path
        silently drops ``target-file = "~/.claude/settings.json"`` when
        it matches the read-time default."""
        import argparse

        from agentbundle.commands import init_state as cmd

        v03_text = textwrap.dedent("""
            schema-version = "0.3"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "repo"
            target-file = "~/.claude/settings.json"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        repo_root, state_path = _write_state_in_repo(self, v03_text)
        args = argparse.Namespace(
            migrate=True,
            scope="repo",
            root=str(repo_root),
        )
        rc = cmd.run(args)
        self.assertEqual(rc, 0)

        new_text = state_path.read_text(encoding="utf-8")
        self.assertEqual(
            new_text,
            v03_text,
            "already-v0.3 migrate must be byte-identity (target-file stripped?)",
        )

    def test_migrate_already_v03_is_idempotent(self) -> None:
        import argparse

        from agentbundle.commands import init_state as cmd

        v03_text = textwrap.dedent("""
            schema-version = "0.3"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "repo"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        repo_root, state_path = _write_state_in_repo(self, v03_text)
        args = argparse.Namespace(
            migrate=True,
            scope="repo",
            root=str(repo_root),
        )
        rc = cmd.run(args)
        self.assertEqual(rc, 0)
        self.assertIn('schema-version = "0.3"', state_path.read_text(encoding="utf-8"))


class V01MigrateLegacyPathTests(unittest.TestCase):
    """v0.1 → v0.3 still works (single-step full re-serialize)."""

    def test_migrate_v01_lands_at_v03_with_scope_column(self) -> None:
        import argparse

        from agentbundle.commands import init_state as cmd

        v01_text = textwrap.dedent("""
            schema-version = "0.1"

            [pack.demo]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            primitives = []

            [pack.demo.files]
        """).strip() + "\n"

        repo_root, state_path = _write_state_in_repo(self, v01_text)
        args = argparse.Namespace(
            migrate=True,
            scope="repo",
            root=str(repo_root),
        )
        rc = cmd.run(args)
        self.assertEqual(rc, 0)
        new_text = state_path.read_text(encoding="utf-8")
        self.assertIn('schema-version = "0.3"', new_text)
        self.assertIn('scope = "repo"', new_text)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _write_tmp(test: unittest.TestCase, text: str) -> Path:
    """Write *text* to a unique tempfile and register cleanup."""
    import tempfile

    fd_dir = tempfile.mkdtemp()
    test.addCleanup(__import__("shutil").rmtree, fd_dir, ignore_errors=True)
    path = Path(fd_dir) / ".agent-ready-state.toml"
    path.write_text(text, encoding="utf-8")
    return path


def _write_state_in_repo(test: unittest.TestCase, text: str) -> tuple[Path, Path]:
    """Create a synthetic repo root with a state file at the expected path."""
    import tempfile

    repo = Path(tempfile.mkdtemp())
    test.addCleanup(__import__("shutil").rmtree, str(repo), ignore_errors=True)
    state_path = repo / ".agent-ready-state.toml"
    state_path.write_text(text, encoding="utf-8")
    return repo, state_path


if __name__ == "__main__":
    unittest.main()
