"""Tests for _LIFECYCLE_MANIFEST and DEFAULT_SESSION_INSTRUCTION (AC20, AC24)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "agentbundle" / "workspace_mcp.py"


def _load_wsmcp():
    spec = importlib.util.spec_from_file_location("workspace_mcp", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestLifecycleManifest:
    """_LIFECYCLE_MANIFEST has exactly 7 keys with required fields (AC24)."""

    def test_manifest_has_seven_keys(self) -> None:
        mod = _load_wsmcp()
        assert len(mod._LIFECYCLE_MANIFEST) == 7

    def test_manifest_contains_all_seven_types(self) -> None:
        mod = _load_wsmcp()
        expected = {"work", "research", "shape", "design", "strategy", "signal", "brief"}
        assert set(mod._LIFECYCLE_MANIFEST.keys()) == expected

    def test_manifest_entries_have_required_fields(self) -> None:
        mod = _load_wsmcp()
        required = {"dispatch_skill", "output_pattern", "has_gates", "required_pack"}
        for name, entry in mod._LIFECYCLE_MANIFEST.items():
            missing = required - set(entry.keys())
            assert not missing, f"manifest[{name!r}] missing keys: {missing}"

    def test_work_type_has_gates(self) -> None:
        mod = _load_wsmcp()
        assert mod._LIFECYCLE_MANIFEST["work"]["has_gates"] is True

    def test_signal_type_no_dispatch_skill(self) -> None:
        mod = _load_wsmcp()
        assert mod._LIFECYCLE_MANIFEST["signal"]["dispatch_skill"] is None

    def test_brief_type_has_receive_brief_skill(self) -> None:
        mod = _load_wsmcp()
        assert mod._LIFECYCLE_MANIFEST["brief"]["dispatch_skill"] == "receive-brief"

    def test_output_pattern_for_research(self) -> None:
        mod = _load_wsmcp()
        patterns = mod._LIFECYCLE_MANIFEST["research"]["output_pattern"]
        assert patterns is not None
        assert any("{slug}" in p for p in patterns)


class TestDefaultSessionInstruction:
    """DEFAULT_SESSION_INSTRUCTION contains the 6 required rules (AC20)."""

    def test_session_instruction_is_non_empty_string(self) -> None:
        mod = _load_wsmcp()
        assert isinstance(mod.DEFAULT_SESSION_INSTRUCTION, str)
        assert len(mod.DEFAULT_SESSION_INSTRUCTION) > 100

    def test_session_instruction_mentions_workspace_status(self) -> None:
        mod = _load_wsmcp()
        assert "workspace_status" in mod.DEFAULT_SESSION_INSTRUCTION

    def test_session_instruction_mentions_git_tools(self) -> None:
        mod = _load_wsmcp()
        assert "git_" in mod.DEFAULT_SESSION_INSTRUCTION

    def test_session_instruction_mentions_elicit(self) -> None:
        mod = _load_wsmcp()
        assert "elicit" in mod.DEFAULT_SESSION_INSTRUCTION

    def test_session_instruction_has_six_numbered_rules(self) -> None:
        mod = _load_wsmcp()
        # Rules are numbered 1-6
        for n in range(1, 7):
            assert f"{n}." in mod.DEFAULT_SESSION_INSTRUCTION, f"rule {n} missing"
