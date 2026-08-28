"""PLAN-time contract stubs for the intake-intent admission seam."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace


CORE_SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"
GUARD = CORE_SKILLS / "work-intake" / "scripts" / "intake_guard.py"


def load_guard():
    """Load the existing renderer that the plan moves or retains by evidence."""
    spec = importlib.util.spec_from_file_location("_intake_intent_guard", GUARD)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_intake_intent_owns_minimum_repository_admission() -> None:
    """The callable renderer emits every minimum repository-intent field."""
    # STUB: AC3
    # STUB: AC7
    guard = load_guard()
    assert inspect.signature(guard.render_minimal_intent).parameters["level"].default is None
    intake = SimpleNamespace(
        content={
            "outcomes": ["Reduce avoidable artifacts; password=secret"],
            "assumptions": [],
            "named_gaps": [],
            "boundary": ["Core repository admission only"],
            "owner": ["maintainer"],
            "unresolved_questions": ["None"],
            "projection": ["spec"],
        },
        constraints={},
        source=SimpleNamespace(
            mode="repo-origin",
            locator="docs/source.md",
            revision="sha256-bytes-v1:fixture",
            tracker_profile=None,
        ),
    )
    rendered = guard.render_minimal_intent(
        intake=intake,
        title="Minimum intent",
        level=None,
    )
    for heading in (
        "## Outcome",
        "## Boundary",
        "## Owner",
        "## Unresolved questions",
        "## Projection",
        "## Source",
    ):
        assert heading in rendered
    assert "**Level:**" not in rendered
    assert "password=secret" not in rendered
