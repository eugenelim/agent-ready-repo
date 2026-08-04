"""Tests for _WorkspaceStatusTool — pack-presence filter, slug safety, FSM merging."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "agentbundle" / "workspace_mcp.py"


def _load_module():
    """Load workspace_mcp as a module without executing main()."""
    spec = importlib.util.spec_from_file_location("agentbundle.workspace_mcp", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("agentbundle.workspace_mcp", mod)
    spec.loader.exec_module(mod)
    return mod


class TestWorkspaceStatusSlugSafety:
    """AC10: unsafe slugs are rejected; safe slugs pass; entry.slug (not entry.path) is used."""

    def test_unsafe_slug_dot_rejected(self) -> None:
        mod = _load_module()
        assert not mod._is_safe_slug(".")

    def test_unsafe_slug_dotdot_rejected(self) -> None:
        mod = _load_module()
        assert not mod._is_safe_slug("..")

    def test_unsafe_slug_leading_dash_rejected(self) -> None:
        mod = _load_module()
        assert not mod._is_safe_slug("-bad")

    def test_safe_slug_passes(self) -> None:
        mod = _load_module()
        assert mod._is_safe_slug("my-feature.v2")

    def test_spec_prefixed_path_rejected(self) -> None:
        """Regression: entry.path = "spec/name" must not be used in the slug guard.

        WorkEntry.path contains "spec/<slug>"; passing it to _is_safe_slug rejects
        the "/" and silently drops every work-queue item (AC8/AC10).
        The fix uses entry.slug ("name", no prefix) instead of entry.path.
        """
        mod = _load_module()
        # entry.path format is rejected by _SAFE_SLUG_RE (contains "/")
        assert not mod._is_safe_slug("spec/my-feature")
        # entry.slug format is accepted
        assert mod._is_safe_slug("my-feature")

    def test_ini_slug_with_slash_rejected(self) -> None:
        mod = _load_module()
        assert not mod._is_safe_slug("ini/bad")

    def test_empty_slug_rejected(self) -> None:
        mod = _load_module()
        assert not mod._is_safe_slug("")


class TestPackPresenceFilter:
    """Pack-presence check uses 6 probe roots (3 adapters × repo + user scope), OR logic (AC9)."""

    def test_skill_found_in_repo_claude_root(self, tmp_path: Path) -> None:
        pytest.skip("STUB: AC9 — create SKILL.md under .claude/skills/{skill}/; dispatch_skill advertised as available")

    def test_skill_not_in_any_root_marks_unavailable(self, tmp_path: Path) -> None:
        pytest.skip("STUB: AC9 — no SKILL.md anywhere → available=False + required_pack present")

    def test_skill_found_in_user_scope(self, tmp_path: Path) -> None:
        pytest.skip("STUB: AC9 — skill exists in ~/.agents/skills/{skill}/SKILL.md")


class TestFSMStateMerge:
    """FSM fields from _EventBridge are present in workspace_status() result (AC8)."""

    def test_fsm_fields_present_in_result(self) -> None:
        pytest.skip("STUB: AC8 — result must contain current_state, gate_pending, gate, gate_question, review_findings")

    def test_gate_pending_true_when_bridge_says_gate(self) -> None:
        pytest.skip('STUB: AC7/AC8 — bridge.get_fsm_state() gate_pending=True → result["gate_pending"] True')
