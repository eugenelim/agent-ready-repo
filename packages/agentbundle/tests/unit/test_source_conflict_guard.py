"""Tests for spec/source-conflict-install-guard (RFC-0072 D3).

Unit tests call _check_source_conflict directly (pure function, no I/O).
Integration tests drive install.run() with a minimal args namespace.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from agentbundle.commands.install import _check_source_conflict
from agentbundle.config import PackState, State


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_with_row(
    pack_name: str,
    adapter: str,
    source: str | None,
) -> State:
    state = State()
    state.packs[(pack_name, adapter)] = PackState(
        installed_version="1.0.0",
        source=source,
    )
    return state


def _run_install(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands import install

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = install.run(args)
    return rc, stdout.getvalue(), stderr.getvalue()


def _stage_pack(
    catalogue_root: Path,
    pack_name: str,
    *,
    allowed_adapters: list[str] | None = None,
) -> None:
    """Create a minimal repo-scope pack in catalogue_root/packs/<pack_name>/."""
    pack_dir = catalogue_root / "packs" / pack_name
    pack_dir.mkdir(parents=True, exist_ok=True)
    aa_line = ""
    if allowed_adapters is not None:
        aa_line = f"allowed-adapters = {allowed_adapters!r}\n"
    (pack_dir / "pack.toml").write_text(
        textwrap.dedent(
            f"""\
            [pack]
            name = "{pack_name}"
            version = "0.1.0"
            spec-version = "0.6"

            [pack.adapter-contract]
            version = "0.7"

            [pack.install]
            default-scope = "repo"
            allowed-scopes = ["repo"]
            {aa_line}"""
        ),
        encoding="utf-8",
    )
    skill_dir = pack_dir / ".apm" / "skills" / f"{pack_name}-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {pack_name}-skill\ndescription: {pack_name}\n---\nBody.",
        encoding="utf-8",
    )


_ABSENT = object()  # sentinel for "omit _source_uri attribute entirely"


def _make_install_args(
    pack: str,
    catalogue: str,
    output: str,
    *,
    scope: str | None = None,
    force: bool = False,
    yes: bool = False,
    adapter: str | None = None,
    source_uri: object = _ABSENT,
) -> argparse.Namespace:
    """Build an args namespace for install.run().

    Sets emit_install_routes=False to select the per-IDE projection path
    (matching the default argparse value). Without this attribute, the
    fallback logic in run() uses emit_install_routes=(scope != "user"),
    which causes the --adapter + --emit-install-routes mutex to fire.
    """
    ns = argparse.Namespace(
        pack=pack,
        catalogue=catalogue,
        output=output,
        scope=scope,
        force=force,
        yes=yes,
        adapter=adapter,
        emit_install_routes=False,
    )
    # _source_uri: pass None explicitly to simulate "attribute present but None"
    # vs omit entirely (_ABSENT) to simulate absent attribute.
    if source_uri is not _ABSENT:
        ns._source_uri = source_uri
    return ns


# ---------------------------------------------------------------------------
# Unit tests — _check_source_conflict directly
# ---------------------------------------------------------------------------

class SourceConflictGuardUnitTests(unittest.TestCase):
    """Direct unit tests of _check_source_conflict. No I/O."""

    def test_source_conflict_state_none_returns_none(self):
        """state=None → guard is a no-op (unresolvable user scope)."""
        result = _check_source_conflict("mypack", "repo", None, "/tmp/cat")
        self.assertIsNone(result)

    def test_source_conflict_no_existing_rows_allowed(self):
        """Empty rows for pack → None (first install at scope)."""
        state = State()  # no rows
        result = _check_source_conflict("mypack", "repo", state, "/tmp/cat")
        self.assertIsNone(result)

    def test_source_conflict_same_canonical_source_allowed(self, tmp_path=None):
        """Same concrete source → allowed (AC3)."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            cat = Path(d) / "catalogue"
            cat.mkdir()
            state = _state_with_row("mypack", "claude-code", str(cat))
            result = _check_source_conflict("mypack", "repo", state, str(cat))
            self.assertIsNone(result)

    def test_source_conflict_differing_representations_allowed(self):
        """Path with .. resolves to same canonical as direct path → allowed (AC3, AC7).

        This test fails if canonicalize_source is NOT engaged — a bare string
        compare would refuse because the strings differ.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            cat = Path(d) / "catalogue"
            cat.mkdir()
            subdir = Path(d) / "subdir"
            subdir.mkdir()
            # source with .. that resolves to the same path
            dotdot_path = str(subdir / ".." / "catalogue")
            resolved_path = str(cat.resolve())
            state = _state_with_row("mypack", "claude-code", dotdot_path)
            result = _check_source_conflict("mypack", "repo", state, resolved_path)
            self.assertIsNone(result)

    def test_source_conflict_different_concrete_sources_refused(self):
        """Different concrete paths → refused (AC2)."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            cat_a = Path(d) / "catA"
            cat_a.mkdir()
            cat_b = Path(d) / "catB"
            cat_b.mkdir()
            state = _state_with_row("mypack", "claude-code", str(cat_a))
            result = _check_source_conflict("mypack", "repo", state, str(cat_b))
            self.assertIsNotNone(result)

    def test_source_conflict_incoming_none_existing_concrete_refused(self):
        """Incoming canonicalizes to None, existing is concrete → refused (AC8)."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            cat = Path(d) / "catalogue"
            cat.mkdir()
            state = _state_with_row("mypack", "claude-code", str(cat))
            # "agent-ready-repo" canonicalizes to None
            result = _check_source_conflict("mypack", "repo", state, "agent-ready-repo")
            self.assertIsNotNone(result)

    def test_source_conflict_existing_none_incoming_concrete_refused(self):
        """Existing source=None, incoming is concrete → refused (AC8)."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            cat = Path(d) / "catalogue"
            cat.mkdir()
            state = _state_with_row("mypack", "claude-code", None)
            result = _check_source_conflict("mypack", "repo", state, str(cat))
            self.assertIsNotNone(result)

    def test_source_conflict_both_none_refused(self):
        """Both canonicalize to None → refused (AC8 'cannot prove equal')."""
        state = _state_with_row("mypack", "claude-code", "agent-ready-repo")
        result = _check_source_conflict("mypack", "repo", state, "agent-ready-repo")
        self.assertIsNotNone(result)

    def test_source_conflict_legacy_literal_refused(self):
        """source='agent-ready-repo' (legacy sentinel) with concrete incoming → refused (AC7, AC8)."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            cat = Path(d) / "catalogue"
            cat.mkdir()
            state = _state_with_row("mypack", "claude-code", "agent-ready-repo")
            result = _check_source_conflict("mypack", "repo", state, str(cat))
            self.assertIsNotNone(result)

    def test_source_conflict_multiple_adapters_all_same_source_allowed(self):
        """Multiple adapters, all same non-None canonical → allowed (AC3)."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            cat = Path(d) / "catalogue"
            cat.mkdir()
            state = State()
            state.packs[("mypack", "claude-code")] = PackState(
                installed_version="1.0.0", source=str(cat)
            )
            state.packs[("mypack", "kiro")] = PackState(
                installed_version="1.0.0", source=str(cat)
            )
            result = _check_source_conflict("mypack", "repo", state, str(cat))
            self.assertIsNone(result)

    def test_source_conflict_cross_scope_not_blocked(self):
        """Guard only inspects the passed state (AC6).

        Pass user_state (empty for the pack) even though repo_state has
        a conflicting row — the guard must return None because it only
        looks at the given state argument.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            cat_a = Path(d) / "catA"
            cat_a.mkdir()
            cat_b = Path(d) / "catB"
            cat_b.mkdir()
            # repo_state has a conflicting row (different source)
            repo_state = _state_with_row("mypack", "claude-code", str(cat_a))
            # user_state is empty for this pack
            user_state = State()
            # Guard called with user_state (requested_scope="user" scenario)
            result = _check_source_conflict("mypack", "user", user_state, str(cat_b))
            self.assertIsNone(result)

    # Error message content tests (AC5)

    def _conflict_result(self, pack_name="mypkg", scope="repo"):
        """Helper: trigger a conflict and return the error string."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            cat_a = Path(d) / "catA"
            cat_a.mkdir()
            cat_b = Path(d) / "catB"
            cat_b.mkdir()
            state = _state_with_row(pack_name, "claude-code", str(cat_a))
            result = _check_source_conflict(pack_name, scope, state, str(cat_b))
            self.assertIsNotNone(result)
            return result, str(cat_a.resolve()), str(cat_b.resolve())

    def test_source_conflict_error_message_contains_pack_name(self):
        """Error message includes the pack name (AC5a)."""
        result, _, _ = self._conflict_result(pack_name="specialpack")
        self.assertIn("specialpack", result)

    def test_source_conflict_error_message_contains_scope(self):
        """Error message includes the target scope (AC5b)."""
        result, _, _ = self._conflict_result(scope="repo")
        self.assertIn("repo", result)

    def test_source_conflict_error_message_contains_incoming_source(self):
        """Error message includes the canonical incoming source string (AC5c)."""
        result, existing, incoming = self._conflict_result()
        self.assertIn(incoming, result)

    def test_source_conflict_error_message_contains_existing_adapter_and_source(self):
        """Error message includes existing adapter name and canonical source (AC5d)."""
        result, existing, _ = self._conflict_result()
        self.assertIn("claude-code", result)
        self.assertIn(existing, result)

    def test_source_conflict_error_message_contains_upgrade_recovery(self):
        """Error message mentions upgrade as a recovery path (AC5e)."""
        result, _, _ = self._conflict_result()
        self.assertIn("upgrade", result)

    def test_source_conflict_error_message_contains_uninstall_recovery(self):
        """Error message mentions uninstall all existing adapters as recovery (AC5e)."""
        result, _, _ = self._conflict_result()
        self.assertIn("uninstall all existing adapters", result)

    def test_source_conflict_error_message_force_no_bypass_note(self):
        """Error message explicitly states --force does not bypass (AC4, AC5)."""
        result, _, _ = self._conflict_result()
        self.assertIn("--force does not", result)


# ---------------------------------------------------------------------------
# Integration tests — full install.run() path
# ---------------------------------------------------------------------------

class SourceConflictInstallIntegrationTests(unittest.TestCase):
    """Integration tests driving install.run() for source conflict scenarios."""

    def setUp(self) -> None:
        self.tmp = Path(__import__("tempfile").mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, ignore_errors=True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self.cat_a = self.tmp / "catA"
        self.cat_b = self.tmp / "catB"
        # stage the same pack in both catalogues
        _stage_pack(self.cat_a, "demo", allowed_adapters=["claude-code", "kiro"])
        _stage_pack(self.cat_b, "demo", allowed_adapters=["claude-code", "kiro"])
        # clear inband detection seen set between tests
        from agentbundle.commands import install
        install._clear_inband_detection_seen()

    def tearDown(self) -> None:
        from agentbundle.commands import install
        install._clear_inband_detection_seen()

    def _install(self, *, catalogue: Path, adapter: str | None = None,
                 force: bool = False, yes: bool = False,
                 scope: str | None = None, pack: str = "demo") -> tuple[int, str, str]:
        args = _make_install_args(
            pack,
            str(catalogue),
            str(self.repo),
            scope=scope,
            force=force,
            yes=yes,
            adapter=adapter,
        )
        return _run_install(args)

    def _state_has_adapter(self, adapter: str) -> bool:
        """Return True if the repo state has a row for (demo, adapter)."""
        from agentbundle.config import load_state
        state_path = self.repo / ".agentbundle-state.toml"
        if not state_path.exists():
            return False
        state = load_state(state_path)
        return state.row("demo", adapter) is not None

    def test_source_conflict_multi_adapter_same_source_allowed(self):
        """Multi-adapter install from same catalogue is allowed (AC3)."""
        rc1, _, err1 = self._install(catalogue=self.cat_a, adapter="claude-code")
        self.assertEqual(rc1, 0, f"first install failed: {err1!r}")

        rc2, _, err2 = self._install(catalogue=self.cat_a, adapter="kiro")
        self.assertEqual(rc2, 0, f"second-adapter install refused: {err2!r}")

        # Both adapter rows present in state.
        self.assertTrue(self._state_has_adapter("claude-code"))
        self.assertTrue(self._state_has_adapter("kiro"))

    def test_source_conflict_refusal_before_any_file_written(self):
        """Refusal happens before any write — kiro row absent from state (AC1, AC2)."""
        rc1, _, _ = self._install(catalogue=self.cat_a, adapter="claude-code")
        self.assertEqual(rc1, 0)

        rc2, _, err2 = self._install(catalogue=self.cat_b, adapter="kiro")
        self.assertNotEqual(rc2, 0)
        self.assertIn("source conflict", err2)

        # kiro adapter row must be absent from state.
        self.assertFalse(self._state_has_adapter("kiro"))
        # kiro projection directory must not exist.
        self.assertFalse((self.repo / ".kiro").exists())

    def test_source_conflict_force_flag_does_not_bypass(self):
        """--force does NOT bypass source mismatch (AC4, AC1)."""
        rc1, _, _ = self._install(catalogue=self.cat_a, adapter="claude-code")
        self.assertEqual(rc1, 0)

        rc2, _, err2 = self._install(
            catalogue=self.cat_b, adapter="kiro", force=True
        )
        self.assertNotEqual(rc2, 0, "--force must not bypass source conflict")
        self.assertIn("source conflict", err2)

        # kiro row absent, no kiro projection files.
        self.assertFalse(self._state_has_adapter("kiro"))
        self.assertFalse((self.repo / ".kiro").exists())

    def test_source_conflict_same_adapter_different_source_refused(self):
        """Same adapter, different source → refused by guard (not Step 4a) (AC2)."""
        rc1, _, _ = self._install(catalogue=self.cat_a, adapter="claude-code")
        self.assertEqual(rc1, 0)

        rc2, _, err2 = self._install(catalogue=self.cat_b, adapter="claude-code")
        self.assertNotEqual(rc2, 0)
        # Error must say "source conflict", NOT "use 'upgrade' to change version"
        self.assertIn("source conflict", err2)
        self.assertNotIn("use 'upgrade' to change version", err2)

    def test_source_conflict_legacy_row_blocks_second_adapter(self):
        """Legacy source='agent-ready-repo' row blocks new-adapter install (AC7, AC8)."""
        from agentbundle.config import dump_state
        # Seed legacy state manually.
        state = _state_with_row("demo", "claude-code", "agent-ready-repo")
        state_path = self.repo / ".agentbundle-state.toml"
        state_path.write_text(dump_state(state), encoding="utf-8")

        rc, _, err = self._install(catalogue=self.cat_a, adapter="kiro")
        self.assertNotEqual(rc, 0)
        self.assertIn("uninstall all existing adapters", err)

    def test_source_conflict_guard_before_step3c_orphan_cleanup(self):
        """Guard fires before Step-3c --force cleanup; dist-tree files survive (AC1).

        Steps:
        1. Install demo for claude-code from cat_a → source recorded.
        2. Clear inband detection cache.
        3. Plant dist-tree files (would be removed by Step-3c (b) under --force).
        4. Attempt reinstall for claude-code from cat_b (different source)
           with --force --yes.
        5. Guard fires first → exit 1 → dist-tree files untouched.
        """
        rc1, _, _ = self._install(catalogue=self.cat_a, adapter="claude-code")
        self.assertEqual(rc1, 0)

        from agentbundle.commands import install as _install_mod
        _install_mod._clear_inband_detection_seen()

        # Plant dist-tree files.
        dist_tree_file = self.repo / "claude-plugins" / "demo" / "plugin.json"
        dist_tree_file.parent.mkdir(parents=True)
        dist_tree_file.write_text("{}", encoding="utf-8")

        rc2, _, err2 = self._install(
            catalogue=self.cat_b, adapter="claude-code", force=True, yes=True
        )
        self.assertNotEqual(rc2, 0, "guard must fire before --force cleanup")
        self.assertIn("source conflict", err2)

        # Dist-tree file must still exist (cleanup didn't run).
        self.assertTrue(
            dist_tree_file.exists(),
            "dist-tree file was removed before source conflict guard fired",
        )

    def test_source_conflict_cross_scope_force_dual_scope_succeeds(self):
        """Cross-scope different-source install is not blocked (AC6).

        repo scope from cat_a → user scope from cat_b should succeed:
        the guard checks user_state (empty for this pack) → allows.
        Repo row's source is unchanged after user-scope install.
        """
        import os
        fake_home = self.tmp / "home"
        fake_home.mkdir()

        env_patch = patch.dict(os.environ, {
            "HOME": str(fake_home),
            "USERPROFILE": str(fake_home),
        })
        with env_patch:
            # Repo-scope install from cat_a.
            rc1, _, err1 = self._install(catalogue=self.cat_a, scope="repo",
                                          adapter="claude-code")
            self.assertEqual(rc1, 0, f"repo install failed: {err1!r}")

            # User-scope install from cat_b (different source). Needs both
            # scopes for the pack → use a pack that allows user scope.
            # Our _stage_pack is repo-only; use a user-allowed pack TOML.
            cat_c = self.tmp / "catC"
            _stage_pack_both_scopes(cat_c, "demo-user")
            cat_d = self.tmp / "catD"
            _stage_pack_both_scopes(cat_d, "demo-user")

            rc2, _, err2 = _run_install(_make_install_args(
                "demo-user",
                str(cat_c),
                str(self.repo),
                scope="repo",
                adapter="claude-code",
            ))
            self.assertEqual(rc2, 0, f"demo-user repo install failed: {err2!r}")

            rc3, _, err3 = _run_install(_make_install_args(
                "demo-user",
                str(cat_d),
                str(self.repo),
                scope="user",
                force=True,
            ))
            self.assertEqual(rc3, 0, f"user-scope cross-source install refused: {err3!r}")

            # Repo row's source is unchanged: canonicalize(cat_c).
            from agentbundle.config import load_state, canonicalize_source
            repo_state = load_state(self.repo / ".agentbundle-state.toml")
            repo_row = repo_state.row("demo-user", "claude-code")
            self.assertIsNotNone(repo_row)
            self.assertEqual(
                repo_row.source,
                canonicalize_source(str(cat_c)),
                "repo row source was mutated during user-scope install",
            )

    def test_source_conflict_profile_source_uri_integration(self):
        """_source_uri attribute is used when present for source comparison (AC11).

        Setup:
        - demo for claude-code installed from cat_a (source recorded = canonicalize(cat_a)).
        - Second install with args.catalogue=cat_b AND args._source_uri=str(cat_a):
          guard uses _source_uri (= cat_a canonical = match) → allowed.
        - Third install with args.catalogue=cat_b AND args._source_uri=None:
          guard falls back to catalogue_uri = cat_b (≠ cat_a) → refused.
        """
        rc1, _, _ = self._install(catalogue=self.cat_a, adapter="claude-code")
        self.assertEqual(rc1, 0)

        # Second adapter install with _source_uri matching existing source.
        args_with_uri = _make_install_args(
            "demo",
            str(self.cat_b),
            str(self.repo),
            adapter="kiro",
            source_uri=str(self.cat_a),  # logical URI = same as first install
        )
        rc2, _, err2 = _run_install(args_with_uri)
        # Source conflict guard allows (same canonical); install may succeed or
        # fail for other reasons (e.g. kiro adapter resolution), but NOT
        # because of source conflict.
        self.assertNotIn("source conflict", err2,
                         "_source_uri should have prevented source conflict")

        # Third install: _source_uri=None → fallback to catalogue_uri=cat_b → conflict.
        args_none_uri = _make_install_args(
            "demo",
            str(self.cat_b),
            str(self.repo),
            adapter="kiro",
            source_uri=None,  # explicit None → or-fallback to catalogue_uri
        )
        rc3, _, err3 = _run_install(args_none_uri)
        self.assertNotEqual(rc3, 0)
        self.assertIn("source conflict", err3,
                      "fallback to catalogue_uri should trigger source conflict")


def _stage_pack_both_scopes(catalogue_root: Path, pack_name: str) -> None:
    """Stage a pack that supports both repo and user scope."""
    pack_dir = catalogue_root / "packs" / pack_name
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "pack.toml").write_text(
        textwrap.dedent(
            f"""\
            [pack]
            name = "{pack_name}"
            version = "0.1.0"
            spec-version = "0.6"

            [pack.adapter-contract]
            version = "0.7"

            [pack.install]
            default-scope = "repo"
            allowed-scopes = ["repo", "user"]
            allowed-adapters = ["claude-code"]
            """
        ),
        encoding="utf-8",
    )
    (pack_dir / ".apm").mkdir(exist_ok=True)


if __name__ == "__main__":
    unittest.main()
