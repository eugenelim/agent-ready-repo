"""Unit tests for the dropped-primitives warning rail (T6 of
docs/specs/dropped-primitives-coverage).

Covers the helpers exposed in ``agentbundle.commands.install``:

  - ``_enumerate_dropped_primitives(pack_dir, adapter)``
  - ``_enumerate_compatible_primitives(pack_dir, adapter)``
  - ``_format_dropped_warning(pack_name, adapter, dropped, compatible)``
  - ``_DROPPED_WARNING_SEEN`` short-circuit (single-scope + dual-scope)

Integration with the install handler hook is covered in T8's
integration suite — this module isolates the formatter + helper contracts.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentbundle.commands.install import (
    _DROPPED_WARNING_SEEN,
    _clear_dropped_warning_seen,
    _enumerate_compatible_primitives,
    _enumerate_dropped_primitives,
    _format_dropped_warning,
    _maybe_emit_dropped_warning,
)


def _seed_pack(
    root: Path,
    *,
    skills: list[str] = (),
    agents: list[str] = (),
    hook_bodies: list[str] = (),
    hook_wirings: list[str] = (),
    commands: list[str] = (),
) -> Path:
    """Build a fixture pack at ``root`` shipping the named primitive files.

    Source paths follow the contract's ``primitive.<type>.source-path``
    layout (skills are directories with SKILL.md; agents/commands are
    .md files; hooks are .sh files; hook-wiring are .toml files).
    """
    pack = root
    pack.mkdir(parents=True, exist_ok=True)
    if skills:
        (pack / ".apm" / "skills").mkdir(parents=True, exist_ok=True)
        for name in skills:
            (pack / ".apm" / "skills" / name).mkdir(parents=True)
            (pack / ".apm" / "skills" / name / "SKILL.md").write_text(
                f"# {name}\n", encoding="utf-8"
            )
    if agents:
        (pack / ".apm" / "agents").mkdir(parents=True, exist_ok=True)
        for name in agents:
            (pack / ".apm" / "agents" / f"{name}.md").write_text(
                f"# {name}\n", encoding="utf-8"
            )
    if hook_bodies:
        (pack / ".apm" / "hooks").mkdir(parents=True, exist_ok=True)
        for name in hook_bodies:
            (pack / ".apm" / "hooks" / f"{name}.sh").write_text(
                f"# {name}\n", encoding="utf-8"
            )
    if hook_wirings:
        (pack / ".apm" / "hook-wiring").mkdir(parents=True, exist_ok=True)
        for name in hook_wirings:
            (pack / ".apm" / "hook-wiring" / f"{name}.toml").write_text(
                "[hooks]\n", encoding="utf-8"
            )
    if commands:
        (pack / ".apm" / "commands").mkdir(parents=True, exist_ok=True)
        for name in commands:
            (pack / ".apm" / "commands" / f"{name}.md").write_text(
                f"# {name}\n", encoding="utf-8"
            )
    return pack


class TestEnumerateDroppedPrimitives(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_codex_against_core_like_pack(self) -> None:
        """Post-v0.8 codex drops only `command`. Pack ships agents +
        commands + hook-wiring; only `command` count appears."""
        pack = _seed_pack(
            self.tmp_path / "pack",
            agents=["a", "b"],
            commands=["c1", "c2", "c3"],
            hook_wirings=["w1"],
        )
        result = _enumerate_dropped_primitives(pack, "codex")
        self.assertEqual(result, {"command": 3})

    def test_copilot_against_core_like_pack(self) -> None:
        """Copilot drops agent + command + hook-wiring; all three counts."""
        pack = _seed_pack(
            self.tmp_path / "pack",
            agents=["a", "b"],
            commands=["c1", "c2", "c3"],
            hook_wirings=["w1"],
        )
        result = _enumerate_dropped_primitives(pack, "copilot")
        self.assertEqual(result, {"agent": 2, "command": 3, "hook-wiring": 1})

    def test_kiro_against_core_like_pack(self) -> None:
        """Kiro drops only `command`."""
        pack = _seed_pack(
            self.tmp_path / "pack",
            agents=["a"],
            commands=["c1"],
        )
        result = _enumerate_dropped_primitives(pack, "kiro")
        self.assertEqual(result, {"command": 1})

    def test_claude_code_returns_empty(self) -> None:
        """Claude-code has no `dropped` modes."""
        pack = _seed_pack(
            self.tmp_path / "pack",
            agents=["a"], commands=["c1"], hook_wirings=["w1"],
        )
        result = _enumerate_dropped_primitives(pack, "claude-code")
        self.assertEqual(result, {})

    def test_skills_only_pack_returns_empty(self) -> None:
        """Pack shipping only skills against any adapter returns empty."""
        pack = _seed_pack(self.tmp_path / "pack", skills=["foo"])
        for adapter in ("codex", "copilot", "kiro", "claude-code"):
            with self.subTest(adapter=adapter):
                self.assertEqual(_enumerate_dropped_primitives(pack, adapter), {})

    def test_empty_directory_treated_as_no_primitives(self) -> None:
        """``.apm/commands/`` exists but is empty → command not counted."""
        pack = self.tmp_path / "pack"
        (pack / ".apm" / "commands").mkdir(parents=True)
        result = _enumerate_dropped_primitives(pack, "codex")
        self.assertEqual(result, {})

    def test_missing_directory_treated_as_no_primitives(self) -> None:
        """``.apm/commands/`` doesn't exist → command not counted."""
        pack = self.tmp_path / "pack"
        pack.mkdir()
        result = _enumerate_dropped_primitives(pack, "codex")
        self.assertEqual(result, {})

    def test_junk_files_filtered_out_of_count(self) -> None:
        """``.DS_Store`` and non-matching-suffix files don't inflate
        the count (concern 6 of iter-1 review). Per-type suffix:
        agents/commands = .md; hook-wiring = .toml; hook-body = any
        file; skills = subdirectories."""
        pack = self.tmp_path / "pack"
        (pack / ".apm" / "commands").mkdir(parents=True)
        # One real command (.md), plus junk files.
        (pack / ".apm" / "commands" / "real.md").write_text("# real\n", encoding="utf-8")
        (pack / ".apm" / "commands" / ".DS_Store").write_text("junk", encoding="utf-8")
        (pack / ".apm" / "commands" / "README.txt").write_text("not a command", encoding="utf-8")
        # Stray subdirectory — shouldn't count toward .md commands.
        (pack / ".apm" / "commands" / "subdir").mkdir()
        result = _enumerate_dropped_primitives(pack, "codex")
        self.assertEqual(result, {"command": 1})

    def test_hook_wiring_filter_by_toml_suffix(self) -> None:
        pack = self.tmp_path / "pack"
        (pack / ".apm" / "hook-wiring").mkdir(parents=True)
        (pack / ".apm" / "hook-wiring" / "real.toml").write_text("[hooks]\n", encoding="utf-8")
        (pack / ".apm" / "hook-wiring" / "stray.md").write_text("not a wiring", encoding="utf-8")
        result = _enumerate_dropped_primitives(pack, "copilot")
        self.assertEqual(result.get("hook-wiring"), 1)


class TestEnumerateCompatiblePrimitives(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_codex_post_bump_with_full_pack(self) -> None:
        """Post-v0.8, codex projects skill + agent + hook-body +
        hook-wiring (only command dropped). Pack ships all four → all four
        in the compatible list."""
        pack = _seed_pack(
            self.tmp_path / "pack",
            skills=["s1"],
            agents=["a1"],
            hook_bodies=["h1"],
            hook_wirings=["w1"],
            commands=["c1"],
        )
        result = _enumerate_compatible_primitives(pack, "codex")
        self.assertEqual(set(result), {"skill", "agent", "hook-body", "hook-wiring"})

    def test_copilot_with_full_pack(self) -> None:
        """Copilot projects skill + hook-body; the rest drop."""
        pack = _seed_pack(
            self.tmp_path / "pack",
            skills=["s1"], agents=["a1"], hook_bodies=["h1"],
            hook_wirings=["w1"], commands=["c1"],
        )
        result = _enumerate_compatible_primitives(pack, "copilot")
        self.assertEqual(set(result), {"skill", "hook-body"})

    def test_skills_only_against_copilot(self) -> None:
        """Pack ships only skills; compatible list is `[skill]`."""
        pack = _seed_pack(self.tmp_path / "pack", skills=["s1"])
        result = _enumerate_compatible_primitives(pack, "copilot")
        self.assertEqual(result, ["skill"])


class TestFormatDroppedWarning(unittest.TestCase):
    def test_one_type_singular(self) -> None:
        msg = _format_dropped_warning(
            "core",
            "codex",
            dropped_counts={"agent": 1},
            compatible_types=["skill"],
        )
        self.assertIn("ships 1 agent that codex projects as 'dropped'", msg)
        self.assertNotIn("agents", msg)

    def test_one_type_plural(self) -> None:
        msg = _format_dropped_warning(
            "core", "codex",
            dropped_counts={"command": 3},
            compatible_types=["skill"],
        )
        self.assertIn("ships 3 commands that codex projects as 'dropped'", msg)

    def test_two_type(self) -> None:
        msg = _format_dropped_warning(
            "core", "copilot",
            dropped_counts={"agent": 2, "command": 3},
            compatible_types=["skill"],
        )
        # Sorted by type name: agent (alphabetical) before command.
        self.assertIn("ships 2 agents and 3 commands", msg)

    def test_three_type_serial_comma(self) -> None:
        msg = _format_dropped_warning(
            "core", "copilot",
            dropped_counts={"agent": 2, "command": 3, "hook-wiring": 1},
            compatible_types=["skill", "hook-body"],
        )
        # Sorted alphabetically: agent, command, hook-wiring.
        self.assertIn("ships 2 agents, 3 commands, and 1 hook-wiring", msg)

    def test_zero_count_elision(self) -> None:
        """Counts with a zero entry render as if the zero weren't there."""
        msg = _format_dropped_warning(
            "core", "codex",
            dropped_counts={"agent": 0, "command": 3, "hook-wiring": 0},
            compatible_types=["skill"],
        )
        self.assertIn("ships 3 commands that codex", msg)
        # 'agent' (zero) is elided — only "commands" should appear in the count list.
        self.assertNotIn(" agent ", msg)
        self.assertNotIn(" agents ", msg)
        # hook-wiring (zero) elided.
        self.assertNotIn(" hook-wiring ", msg)

    def test_compatible_list_in_message(self) -> None:
        msg = _format_dropped_warning(
            "core", "codex",
            dropped_counts={"command": 1},
            compatible_types=["skill", "agent", "hook-body", "hook-wiring"],
        )
        # Plural form, sorted: agents, hook-bodies, hook-wirings, skills
        self.assertIn("The compatible primitives (", msg)
        self.assertIn(") will proceed.", msg)
        for plural in ("agents", "hook-bodies", "hook-wirings", "skills"):
            self.assertIn(plural, msg)

    def test_pinned_wording_exact_template_plural(self) -> None:
        """Spec AC10 pinned wording — exact string match for N>1 case."""
        msg = _format_dropped_warning(
            "core", "codex",
            dropped_counts={"command": 3},
            compatible_types=["skill", "agent", "hook-body", "hook-wiring"],
        )
        expected = (
            "warning: pack core ships 3 commands that codex projects as 'dropped'; "
            "these primitives will not be installed. "
            "The compatible primitives (agents, hook-bodies, hook-wirings, and skills) "
            "will proceed."
        )
        self.assertEqual(msg, expected)

    def test_pinned_wording_exact_template_singular(self) -> None:
        """Spec AC10 pinned wording — exact string match for N=1 case."""
        msg = _format_dropped_warning(
            "core", "codex",
            dropped_counts={"command": 1},
            compatible_types=["skill", "agent"],
        )
        expected = (
            "warning: pack core ships 1 command that codex projects as 'dropped'; "
            "these primitives will not be installed. "
            "The compatible primitives (agents and skills) will proceed."
        )
        self.assertEqual(msg, expected)

    def test_pinned_wording_exact_template_three_type(self) -> None:
        """Spec AC10 pinned wording — exact string match for serial-comma case."""
        msg = _format_dropped_warning(
            "core", "copilot",
            dropped_counts={"agent": 2, "command": 3, "hook-wiring": 1},
            compatible_types=["skill", "hook-body"],
        )
        expected = (
            "warning: pack core ships 2 agents, 3 commands, and 1 hook-wiring "
            "that copilot projects as 'dropped'; "
            "these primitives will not be installed. "
            "The compatible primitives (hook-bodies and skills) will proceed."
        )
        self.assertEqual(msg, expected)

    def test_all_zero_counts_refused(self) -> None:
        """Formatter refuses an all-zero count map — caller guards
        upstream; refusing here surfaces the bug rather than emitting
        a malformed 'ships  that ...' string."""
        with self.assertRaises(ValueError):
            _format_dropped_warning(
                "core", "codex",
                dropped_counts={"agent": 0, "command": 0},
                compatible_types=["skill"],
            )

    def test_empty_dropped_counts_refused(self) -> None:
        """Empty dict raises the same way as all-zero."""
        with self.assertRaises(ValueError):
            _format_dropped_warning(
                "core", "codex",
                dropped_counts={},
                compatible_types=["skill"],
            )


class TestShortCircuitSeenSet(unittest.TestCase):
    def setUp(self) -> None:
        _clear_dropped_warning_seen()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)

    def tearDown(self) -> None:
        _clear_dropped_warning_seen()
        self._tmp.cleanup()

    def test_single_scope_repeat_silenced(self) -> None:
        """Two calls for the same (root, pack, adapter, scope) — second
        is silent."""
        pack = _seed_pack(
            self.tmp_path / "pack",
            agents=["a"], commands=["c"],
        )
        from io import StringIO
        import sys

        captured = StringIO()
        old = sys.stderr
        sys.stderr = captured
        try:
            _maybe_emit_dropped_warning(
                root=self.tmp_path,
                pack_dir=pack,
                pack_name="pack",
                adapter="copilot",
                scope="repo",
            )
            first = captured.getvalue()
            captured.seek(0)
            captured.truncate()
            _maybe_emit_dropped_warning(
                root=self.tmp_path,
                pack_dir=pack,
                pack_name="pack",
                adapter="copilot",
                scope="repo",
            )
            second = captured.getvalue()
        finally:
            sys.stderr = old
        self.assertIn("warning:", first)
        self.assertEqual(second, "")

    def test_dual_scope_independent(self) -> None:
        """Each scope is independently silenceable: silencing repo
        (by repeating it) leaves user free to fire fresh.

        Sequence: fire repo (emits), repeat repo (silent), fire user
        (emits fresh — independent silencing), repeat user (silent).
        """
        pack = _seed_pack(
            self.tmp_path / "pack",
            agents=["a"], commands=["c"],
        )
        from io import StringIO
        import sys

        # First fire — repo.
        captured = StringIO()
        old = sys.stderr
        sys.stderr = captured
        try:
            _maybe_emit_dropped_warning(
                root=self.tmp_path, pack_dir=pack, pack_name="pack",
                adapter="copilot", scope="repo",
            )
            self.assertIn("warning:", captured.getvalue())

            # Repeat repo — silenced.
            captured.seek(0); captured.truncate()
            _maybe_emit_dropped_warning(
                root=self.tmp_path, pack_dir=pack, pack_name="pack",
                adapter="copilot", scope="repo",
            )
            self.assertEqual(captured.getvalue(), "")

            # First fire — user. INDEPENDENT of repo's silencing.
            captured.seek(0); captured.truncate()
            _maybe_emit_dropped_warning(
                root=self.tmp_path, pack_dir=pack, pack_name="pack",
                adapter="copilot", scope="user",
            )
            self.assertIn(
                "warning:", captured.getvalue(),
                "user-scope warning should fire fresh despite repo "
                "being silenced — that's the independence AC11 pins",
            )

            # Repeat user — silenced.
            captured.seek(0); captured.truncate()
            _maybe_emit_dropped_warning(
                root=self.tmp_path, pack_dir=pack, pack_name="pack",
                adapter="copilot", scope="user",
            )
            self.assertEqual(captured.getvalue(), "")

            # Seen-set contains both 4-tuples.
            keys = {(k[1], k[2], k[3]) for k in _DROPPED_WARNING_SEEN}
            self.assertIn(("pack", "copilot", "repo"), keys)
            self.assertIn(("pack", "copilot", "user"), keys)
        finally:
            sys.stderr = old

    def test_silent_for_claude_code(self) -> None:
        """Claude-code has no dropped modes; warning stays silent."""
        pack = _seed_pack(
            self.tmp_path / "pack",
            agents=["a"], commands=["c"], hook_wirings=["w"],
        )
        from io import StringIO
        import sys

        captured = StringIO()
        old = sys.stderr
        sys.stderr = captured
        try:
            _maybe_emit_dropped_warning(
                root=self.tmp_path,
                pack_dir=pack,
                pack_name="pack",
                adapter="claude-code",
                scope="repo",
            )
        finally:
            sys.stderr = old
        self.assertEqual(captured.getvalue(), "")

    def test_skills_only_pack_silent_against_any_adapter(self) -> None:
        pack = _seed_pack(self.tmp_path / "pack", skills=["s"])
        from io import StringIO
        import sys

        for adapter in ("codex", "copilot", "kiro", "claude-code"):
            with self.subTest(adapter=adapter):
                _clear_dropped_warning_seen()
                captured = StringIO()
                old = sys.stderr
                sys.stderr = captured
                try:
                    _maybe_emit_dropped_warning(
                        root=self.tmp_path,
                        pack_dir=pack,
                        pack_name="pack",
                        adapter=adapter,
                        scope="repo",
                    )
                finally:
                    sys.stderr = old
                self.assertEqual(captured.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
