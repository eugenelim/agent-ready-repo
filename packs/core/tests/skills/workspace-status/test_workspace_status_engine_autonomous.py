"""Tests for is_need_satisfied() autonomous-dispatch mode."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_ENGINE_PATH = (
    Path(__file__).resolve().parents[5]
    / "packs" / "core" / ".apm" / "skills" / "workspace-status" / "scripts"
    / "workspace_status_engine.py"
)


def _load_engine():
    spec = importlib.util.spec_from_file_location("workspace_status_engine", _ENGINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Register before exec_module so dataclass string-annotation lookup finds the module.
    sys.modules["workspace_status_engine"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_ini(
    slug: str = "ini-001",
    shaping_active_slugs: list[str] | None = None,
    shaping_backlog: list[tuple[str, str]] | None = None,  # (slug, type)
) -> object:
    """Build a minimal Initiative-like object for is_need_satisfied testing."""
    _load_engine()  # ensure module is registered in sys.modules

    def _entry(s, t):
        e = SimpleNamespace()
        e.slug = s
        e.entry_type = t
        return e

    active = [_entry(s, "shape") for s in (shaping_active_slugs or [])]
    backlog = [_entry(s, t) for s, t in (shaping_backlog or [])]

    shaping = SimpleNamespace(active=active, backlog=backlog)
    work = SimpleNamespace(active=[], shipped=[], queue=[])
    return SimpleNamespace(slug=slug, shaping=shaping, work=work, brief_queue=None)


class TestShapeNeedAutonomous:
    """Shape: need — absent from active AND backlog → unsatisfied when autonomous."""

    def test_shape_absent_unsatisfied_autonomous(self) -> None:
        pytest.skip(
            "STUB: a need absent from both active and backlog is "
            "unsatisfied in autonomous mode"
        )

    def test_shape_in_active_unsatisfied_both_modes(self) -> None:
        mod = _load_engine()
        ini = _make_ini(slug="ini-001", shaping_active_slugs=["my-shape"])
        # In human mode: slug in active → NOT satisfied (slug not in active_slugs = False)
        assert not mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], False)
        # In autonomous mode: same result
        assert not mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], True)

    def test_shape_in_backlog_not_active_satisfied_autonomous(self) -> None:
        mod = _load_engine()
        ini = _make_ini(
            slug="ini-001",
            shaping_active_slugs=[],
            shaping_backlog=[("my-shape", "shape")],
        )
        # Autonomous: in backlog (planned but not started) → satisfied (intentional asymmetry)
        assert mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], True)
        # Human mode: not in active → satisfied
        assert mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], False)

    def test_shape_absent_satisfied_human_mode(self) -> None:
        mod = _load_engine()
        ini = _make_ini(slug="ini-001", shaping_active_slugs=[], shaping_backlog=[])
        # Human mode: absent from active → satisfied (graduated or never existed)
        assert mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], False)

    def test_shape_absent_unsatisfied_autonomous_mode(self) -> None:
        mod = _load_engine()
        ini = _make_ini(slug="ini-001", shaping_active_slugs=[], shaping_backlog=[])
        # Autonomous mode: absent from both → unsatisfied (never planned)
        assert not mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], True)


class TestResearchNeedAutonomous:
    """Research: need — absence from backlog means satisfied in both human and autonomous mode.

    Absent = satisfied because completed research is removed from the backlog;
    there is no way to distinguish "completed" from "never planned" from backlog state alone.
    """

    def test_research_in_backlog_unsatisfied_both_modes(self) -> None:
        mod = _load_engine()
        ini = _make_ini(
            slug="ini-001",
            shaping_backlog=[("my-research", "research")],
        )
        # Both modes: in backlog as type "research" → NOT satisfied (still pending)
        assert not mod.is_need_satisfied("research:my-research", "ini-001", [ini], False)
        assert not mod.is_need_satisfied("research:my-research", "ini-001", [ini], True)

    def test_research_absent_satisfied_both_modes(self) -> None:
        mod = _load_engine()
        ini = _make_ini(slug="ini-001", shaping_backlog=[])
        # Both modes: not in backlog → satisfied (completed or never needed).
        # autonomous_dispatch does NOT change research semantics — absent means completed.
        assert mod.is_need_satisfied("research:my-research", "ini-001", [ini], False)
        assert mod.is_need_satisfied("research:my-research", "ini-001", [ini], True)

    def test_research_wrong_type_in_backlog_does_not_block(self) -> None:
        mod = _load_engine()
        ini = _make_ini(
            slug="ini-001",
            shaping_backlog=[("my-research", "shape")],  # same slug, but type=shape not research
        )
        # Both modes: entry exists but type != "research" → NOT in research_slugs → satisfied
        assert mod.is_need_satisfied("research:my-research", "ini-001", [ini], False)
        assert mod.is_need_satisfied("research:my-research", "ini-001", [ini], True)
