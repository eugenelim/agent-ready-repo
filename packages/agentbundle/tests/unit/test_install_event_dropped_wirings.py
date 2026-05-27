"""Unit tests for T3 + T4 of docs/specs/incompatible-hook-event-drop.

Covers:
  T3 — ``enumerate_event_dropped_wirings`` in
       ``agentbundle.commands._drop_warning``
  T4 — ``format_drop_message`` in the same module (+ backward-compat
       alias ``_format_dropped_warning`` in install.py stays green)

T3 + T4 tests colocated here because both helpers live in
``_drop_warning.py``.
"""

from __future__ import annotations

import tempfile
import tomllib
import unittest
from pathlib import Path

from agentbundle.commands._drop_warning import (
    enumerate_event_dropped_wirings,
    format_drop_message,
)


# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------

def _load_contract() -> dict:
    """Load the bundled adapter.toml contract."""
    import tomllib as _tomllib
    from agentbundle.build.main import _read_bundled

    return _tomllib.loads(_read_bundled("adapter.toml"))


def _packs_dir() -> Path:
    """Absolute path to the repo's packs/ directory."""
    from agentbundle.build.main import REPO_ROOT

    return REPO_ROOT / "packs"


def _seed_wiring(root: Path, name: str, content: str) -> Path:
    """Write a hook-wiring TOML at ``<root>/.apm/hook-wiring/<name>.toml``."""
    hw_dir = root / ".apm" / "hook-wiring"
    hw_dir.mkdir(parents=True, exist_ok=True)
    p = hw_dir / f"{name}.toml"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# T3: enumerate_event_dropped_wirings
# ---------------------------------------------------------------------------


class TestEnumerateEventDroppedWirings(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)
        self.contract = _load_contract()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_enumerate_event_drops_core_against_kiro(self) -> None:
        """core against kiro: session-start.toml uses SessionStart (not in
        kiro's agent-event-vocabulary) AND lacks attach-to-agent, so two
        entries fire.

        Deviation from plan test #1: the plan's prescribed assertion
        expected only the vocab entry, but packs/core/.apm/hook-wiring/
        session-start.toml has no attach-to-agent field (the comment in
        that file says "No attach-to-agent: that's a Kiro-only field").
        The T3 Approach code fires both step 2a (vocab) and step 2b
        (attach-to-agent) independently; the correct result is two entries.
        """
        result = enumerate_event_dropped_wirings(
            _packs_dir() / "core",
            "kiro",
            self.contract,
        )
        self.assertEqual(
            result,
            [
                ("hook-wiring/session-start.toml", "event not in adapter vocabulary"),
                ("hook-wiring/session-start.toml", "kiro requires 'attach-to-agent'"),
            ],
        )

    def test_enumerate_event_drops_emits_two_entries_when_both_reasons_fire(
        self,
    ) -> None:
        """Fixture wiring with both bad event AND missing attach-to-agent
        against kiro: exactly two entries (not concatenated)."""
        pack = self.tmp_path / "pack"
        # Use an out-of-vocab event name + no attach-to-agent field.
        _seed_wiring(
            pack,
            "bad",
            "[[hooks.SessionStart]]\nhooks = []\n",
        )
        result = enumerate_event_dropped_wirings(pack, "kiro", self.contract)
        self.assertEqual(len(result), 2)
        self.assertIn(
            ("hook-wiring/bad.toml", "event not in adapter vocabulary"), result
        )
        self.assertIn(
            ("hook-wiring/bad.toml", "kiro requires 'attach-to-agent'"), result
        )

    def test_enumerate_event_drops_silent_for_claude_code(self) -> None:
        """claude-code declares no agent-event-vocabulary; returns []."""
        # Verify against the contract rather than hardcoding.
        contract = self.contract
        projections = (
            contract.get("adapter", {})
            .get("claude-code", {})
            .get("projections", {})
            .get("hook-wiring", {})
        )
        self.assertNotIn(
            "agent-event-vocabulary",
            projections,
            "test precondition: claude-code must not declare agent-event-vocabulary",
        )

        result = enumerate_event_dropped_wirings(
            _packs_dir() / "core",
            "claude-code",
            self.contract,
        )
        self.assertEqual(result, [])

    def test_enumerate_event_drops_silent_when_type_dropped(self) -> None:
        """copilot has hook-wiring dropped at the type level; returns []."""
        result = enumerate_event_dropped_wirings(
            _packs_dir() / "core",
            "copilot",
            self.contract,
        )
        self.assertEqual(result, [])

    def test_enumerate_event_drops_handles_wiring_with_no_events_table(
        self,
    ) -> None:
        """Well-formed TOML with empty hooks section returns [].

        Include attach-to-agent so the kiro step-2b check doesn't fire —
        the test pins the vocab-check-on-empty-hooks-section behavior,
        not the attach-to-agent check.
        """
        pack = self.tmp_path / "pack"
        # attach-to-agent at top level; [hooks] is a separate empty section.
        _seed_wiring(
            pack,
            "empty-hooks",
            'attach-to-agent = "some-agent"\n[hooks]\n',
        )
        result = enumerate_event_dropped_wirings(pack, "kiro", self.contract)
        # no events under hooks → nothing to drop from vocab check
        self.assertEqual(result, [])

    def test_enumerate_event_drops_emits_entry_on_parse_failure(
        self,
    ) -> None:
        """Malformed TOML returns (relpath, "hook-wiring TOML failed to parse").
        Pins AC6c's asymmetry: install enumerates parse-fail as a drop entry."""
        pack = self.tmp_path / "pack"
        _seed_wiring(pack, "bad", "this is not valid TOML !!!")
        result = enumerate_event_dropped_wirings(pack, "kiro", self.contract)
        self.assertEqual(
            result,
            [("hook-wiring/bad.toml", "hook-wiring TOML failed to parse")],
        )

    def test_enumerate_event_drops_emits_entry_on_empty_attach_to_agent(
        self,
    ) -> None:
        """Kiro+pack with attach-to-agent = "" produces a drop entry —
        install-side is more permissive than validate-side (which refuses
        on empty string per AC4b).

        Documented asymmetry: validate refuses on `attach = ""` (kept
        refusal, exit 1); install enumerates it as a drop entry so the
        file is named in the warning rather than projecting a corrupt
        target. Adopters who run install-without-validate see the file
        listed instead of a silent bad projection at .kiro/agents/.json.
        """
        pack = self.tmp_path / "pack"
        _seed_wiring(pack, "empty-attach", 'attach-to-agent = ""\n')
        result = enumerate_event_dropped_wirings(pack, "kiro", self.contract)
        self.assertEqual(
            result,
            [("hook-wiring/empty-attach.toml", "kiro requires 'attach-to-agent'")],
        )

    def test_enumerate_event_drops_attach_to_agent_only_when_adapter_is_kiro(
        self,
    ) -> None:
        """Non-kiro adapter with vocab declared: no attach-to-agent entry.
        Contract fixture is an inline Python dict literal (no on-disk file)."""
        # Inline fixture contract: a hypothetical adapter "hypo" that declares
        # an agent-event-vocabulary but is NOT kiro.
        inline_contract = {
            "adapter": {
                "hypo": {
                    "projection": [
                        {"primitive": "hook-wiring", "mode": "merge-json"},
                    ],
                    "projections": {
                        "hook-wiring": {
                            "agent-event-vocabulary": ["EventA"],
                        }
                    },
                }
            }
        }
        pack = self.tmp_path / "pack"
        # Wiring uses EventA (in vocab) so no vocab drop; no attach-to-agent.
        _seed_wiring(pack, "w", "[[hooks.EventA]]\nhooks = []\n")
        result = enumerate_event_dropped_wirings(pack, "hypo", inline_contract)
        # No kiro → no attach-to-agent check; EventA is in vocab → no vocab drop.
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# T4: format_drop_message
# ---------------------------------------------------------------------------


class TestFormatDropMessage(unittest.TestCase):
    def test_format_warning_pre_amendment_wording_pinned(self) -> None:
        """AC8 load-bearing pin. Exact byte-string for the pre-amendment
        (primitive-type-only) shape with pack=core, adapter=codex,
        1 command dropped, compatible=[skill, agent, hook-body, hook-wiring].
        Quote verbatim; do NOT compute via the formatter."""
        result = format_drop_message(
            pack_name="core",
            adapter="codex",
            dropped_counts={"command": 1},
            compatible_types=["skill", "agent", "hook-body", "hook-wiring"],
            event_drops=[],
        )
        expected = (
            "warning: pack core ships 1 command that codex projects as 'dropped'; "
            "these primitives will not be installed. "
            "The compatible primitives (agents, hook-bodies, hook-wirings, and skills) "
            "will proceed."
        )
        self.assertEqual(result, expected)

    def test_format_warning_event_only(self) -> None:
        """dropped_counts={} + non-empty event_drops: no 'Additionally,' prefix;
        event clause is the lead clause."""
        result = format_drop_message(
            pack_name="core",
            adapter="kiro",
            dropped_counts={},
            compatible_types=["skill", "agent", "hook-body", "hook-wiring"],
            event_drops=[
                ("hook-wiring/session-start.toml", "event not in adapter vocabulary")
            ],
        )
        self.assertIn("warning:", result)
        self.assertNotIn("Additionally,", result)
        self.assertIn(
            "the following hook-wiring file(s) will be skipped "
            "(event not in adapter vocabulary): hook-wiring/session-start.toml.",
            result,
        )
        self.assertIn("The compatible primitives", result)

    def test_format_warning_primitive_and_event(self) -> None:
        """Both non-empty: 'Additionally, ' (capital A, comma-space) prefix
        on the event clause."""
        result = format_drop_message(
            pack_name="core",
            adapter="kiro",
            dropped_counts={"command": 1},
            compatible_types=["skill", "agent", "hook-body", "hook-wiring"],
            event_drops=[
                ("hook-wiring/session-start.toml", "event not in adapter vocabulary")
            ],
        )
        self.assertIn("pack core ships 1 command that kiro projects as 'dropped'", result)
        self.assertIn(
            "Additionally, the following hook-wiring file(s) will be skipped",
            result,
        )
        self.assertIn("The compatible primitives", result)

    def test_format_warning_reason_summary_dedupe(self) -> None:
        """Both reason categories: vocabulary first, joined with ' + '.
        Pins AC7's order rule."""
        result = format_drop_message(
            pack_name="core",
            adapter="kiro",
            dropped_counts={},
            compatible_types=["skill"],
            event_drops=[
                ("hook-wiring/f.toml", "event not in adapter vocabulary"),
                ("hook-wiring/f.toml", "kiro requires 'attach-to-agent'"),
            ],
        )
        self.assertIn(
            "(event not in adapter vocabulary + kiro requires 'attach-to-agent')",
            result,
        )

    def test_format_warning_file_list_dedupe_and_sort(self) -> None:
        """Multiple entries for the same file → file appears once.
        Multiple files are sorted and joined with serial-comma-plus-and."""
        result = format_drop_message(
            pack_name="core",
            adapter="kiro",
            dropped_counts={},
            compatible_types=["skill"],
            event_drops=[
                ("hook-wiring/b.toml", "event not in adapter vocabulary"),
                ("hook-wiring/a.toml", "event not in adapter vocabulary"),
                ("hook-wiring/b.toml", "kiro requires 'attach-to-agent'"),
            ],
        )
        # b.toml appears once despite two entries; lexicographic order: a, b.
        self.assertIn(
            "hook-wiring/a.toml, and hook-wiring/b.toml",
            result,
        )
        # Confirm only one occurrence of b.toml in the file-list portion.
        # (assertIn above guarantees order + no dup)

    def test_format_validate_info_one_file_one_reason(self) -> None:
        """AC2 byte-pin: one file, one reason."""
        result = format_drop_message(
            pack_name="core",
            adapter="kiro",
            dropped_counts={},
            compatible_types=[],
            event_drops=[
                ("hook-wiring/session-start.toml", "event not in adapter vocabulary")
            ],
            mode="validate_info",
        )
        expected = (
            "info: pack core: the following hook-wiring file(s) will not project "
            "to kiro (event not in adapter vocabulary): "
            "hook-wiring/session-start.toml."
        )
        self.assertEqual(result, expected)

    def test_format_validate_info_one_file_two_reasons(self) -> None:
        """AC2 byte-pin: one file, two reasons (vocabulary + attach-to-agent)."""
        result = format_drop_message(
            pack_name="core",
            adapter="kiro",
            dropped_counts={},
            compatible_types=[],
            event_drops=[
                ("hook-wiring/session-start.toml", "event not in adapter vocabulary"),
                (
                    "hook-wiring/session-start.toml",
                    "kiro requires 'attach-to-agent'",
                ),
            ],
            mode="validate_info",
        )
        expected = (
            "info: pack core: the following hook-wiring file(s) will not project "
            "to kiro (event not in adapter vocabulary + kiro requires 'attach-to-agent'): "
            "hook-wiring/session-start.toml."
        )
        self.assertEqual(result, expected)

    def test_format_validate_info_two_files(self) -> None:
        """AC2 byte-pin: two files, lexicographically sorted with
        serial-comma-plus-and."""
        result = format_drop_message(
            pack_name="core",
            adapter="kiro",
            dropped_counts={},
            compatible_types=[],
            event_drops=[
                ("hook-wiring/second.toml", "event not in adapter vocabulary"),
                ("hook-wiring/first.toml", "event not in adapter vocabulary"),
            ],
            mode="validate_info",
        )
        expected = (
            "info: pack core: the following hook-wiring file(s) will not project "
            "to kiro (event not in adapter vocabulary): "
            "hook-wiring/first.toml, and hook-wiring/second.toml."
        )
        self.assertEqual(result, expected)

    def test_format_validate_info_adapter_name_substituted(self) -> None:
        """adapter='copilot': literal adapter name in output, rest invariant.
        A hardcoded 'kiro' in the formatter source would fail this."""
        result = format_drop_message(
            pack_name="core",
            adapter="copilot",
            dropped_counts={},
            compatible_types=[],
            event_drops=[
                ("hook-wiring/session-start.toml", "event not in adapter vocabulary")
            ],
            mode="validate_info",
        )
        self.assertIn("will not project to copilot", result)
        self.assertNotIn("kiro", result)
        self.assertIn("info: pack core:", result)

    def test_format_validate_info_refuses_when_dropped_counts_nonempty(
        self,
    ) -> None:
        """validate_info mode + non-empty dropped_counts raises ValueError.
        Pins the formatter's defensive-by-construction contract."""
        with self.assertRaises(ValueError):
            format_drop_message(
                pack_name="core",
                adapter="kiro",
                dropped_counts={"command": 1},
                compatible_types=[],
                event_drops=[
                    (
                        "hook-wiring/session-start.toml",
                        "event not in adapter vocabulary",
                    )
                ],
                mode="validate_info",
            )

    def test_format_install_warning_refuses_when_both_empty(self) -> None:
        """install_warning mode with both dropped_counts and event_drops empty
        raises ValueError."""
        with self.assertRaises(ValueError):
            format_drop_message(
                pack_name="core",
                adapter="kiro",
                dropped_counts={},
                compatible_types=["skill"],
                event_drops=[],
            )

    def test_format_validate_info_refuses_when_event_drops_empty(self) -> None:
        """validate_info mode with empty event_drops raises ValueError."""
        with self.assertRaises(ValueError):
            format_drop_message(
                pack_name="core",
                adapter="kiro",
                dropped_counts={},
                compatible_types=[],
                event_drops=[],
                mode="validate_info",
            )


if __name__ == "__main__":
    unittest.main()
