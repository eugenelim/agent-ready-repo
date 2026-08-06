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
    """Unsafe slugs are rejected; safe slugs pass; entry.slug (not entry.path) is used."""

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
        """Regression guard: work-queue slug check at lines ~434/452 must use entry.slug.

        WorkEntry.path = "spec/<slug>" (contains "/", rejected by _SAFE_SLUG_RE).
        WorkEntry.slug = "<slug>" (no slash, passes).
        Using entry.path silently drops ALL work-queue items; using entry.slug passes them.
        This test guards the call sites directly by inspecting the source code section
        so that reverting entry.slug → entry.path at those lines would fail this test.
        """
        src = _MODULE_PATH.read_text(encoding="utf-8")
        # Isolate the work-queue loop section (ready + blocked, before shaping items)
        work_start = src.index("Work queue items (ready / blocked)")
        shaping_start = src.index("Shaping items", work_start)
        work_section = src[work_start:shaping_start]
        # Call sites must use entry.slug, not entry.path
        assert "_is_safe_slug(entry.slug)" in work_section, (
            "work-queue slug guard must use entry.slug (not entry.path)"
        )
        assert "_is_safe_slug(entry.path)" not in work_section, (
            "work-queue slug guard must NOT use entry.path — WorkEntry.path contains 'spec/' prefix"
        )
        # Verify the slug field in output also uses entry.slug
        assert '"slug": entry.slug' in work_section, (
            "work-queue output 'slug' field must come from entry.slug"
        )

    def test_ini_slug_with_slash_rejected(self) -> None:
        mod = _load_module()
        assert not mod._is_safe_slug("ini/bad")

    def test_empty_slug_rejected(self) -> None:
        mod = _load_module()
        assert not mod._is_safe_slug("")


class TestPackPresenceFilter:
    """Pack-presence check uses 6 probe roots (3 adapters × repo + user scope), OR logic."""

    def test_skill_found_in_repo_claude_root(self, tmp_path: Path) -> None:
        pytest.skip("STUB: create SKILL.md under .claude/skills/{skill}/; dispatch_skill advertised as available")

    def test_skill_not_in_any_root_marks_unavailable(self, tmp_path: Path) -> None:
        pytest.skip("STUB: no SKILL.md anywhere → available=False + required_pack present")

    def test_skill_found_in_user_scope(self, tmp_path: Path) -> None:
        pytest.skip("STUB: skill exists in ~/.agents/skills/{skill}/SKILL.md")


class TestFSMStateMerge:
    """FSM fields from _EventBridge are present in workspace_status() result."""

    def test_fsm_fields_present_in_result(self) -> None:
        pytest.skip("STUB: result must contain current_state, gate_pending, gate, gate_question, review_findings")

    def test_gate_pending_true_when_bridge_says_gate(self) -> None:
        pytest.skip('STUB: bridge.get_fsm_state() gate_pending=True → result["gate_pending"] True')
