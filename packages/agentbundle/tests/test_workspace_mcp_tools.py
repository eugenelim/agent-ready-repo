"""Tests for _WorkspaceStatusTool — pack-presence filter, slug safety, FSM merging."""
from __future__ import annotations

from pathlib import Path

import pytest


class TestWorkspaceStatusSlugSafety:
    """Unsafe slugs are filtered before returning (AC10)."""

    def test_unsafe_slug_dot_filtered(self) -> None:
        pytest.skip('STUB: AC10 — an entry with slug="." must not appear in the output')

    def test_unsafe_slug_dotdot_filtered(self) -> None:
        pytest.skip('STUB: AC10 — slug=".." filtered')

    def test_unsafe_slug_leading_dash_filtered(self) -> None:
        pytest.skip('STUB: AC10 — slug="-bad" filtered')

    def test_safe_slug_passes(self) -> None:
        pytest.skip('STUB: AC10 — normal slug "my-feature.v2" passes')


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
