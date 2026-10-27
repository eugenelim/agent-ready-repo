"""Every documentation surface names the `Priority:` field the same way.

Verification mode: goal-based. Each surface lists the four values in the lint's
order as one backticked run, says an item with no line has no priority, and says
the field never decides readiness, dispatch, or order of work.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_LINT = _ROOT / "packs/core/.apm/skills/work-loop/scripts/lint-priority-field.py"

_spec = importlib.util.spec_from_file_location("priority_field_doc_lint", _LINT)
assert _spec is not None and _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
PRIORITY_VALUES: tuple[str, ...] = _module.PRIORITY_VALUES

SURFACES = (
    "packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md",
    "guides/product-engineering/reference/intent-fields-and-modes.md",
    "packs/core/.apm/skills/work-intake/references/lifecycle-index.md",
    "packs/core/.apm/skills/author-delivery-brief/SKILL.md",
)
_RUN = ", ".join(f"`{value}`" for value in PRIORITY_VALUES)
_PHRASES = ("no priority", "never decides readiness, dispatch, or order of work")


def _text(relative: str) -> str:
    """Surface text with line wraps folded to single spaces."""
    return " ".join((_ROOT / relative).read_text(encoding="utf-8").split())


@pytest.mark.parametrize("surface", SURFACES)
def test_surface_names_the_values_in_order(surface: str) -> None:
    assert _RUN in _text(surface)


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("phrase", _PHRASES)
def test_surface_states_the_rule(surface: str, phrase: str) -> None:
    assert phrase in _text(surface)
