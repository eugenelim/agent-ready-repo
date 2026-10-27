"""No module that orders work reads the `Priority:` field.

Verification mode: TDD, a static guard over shipped source. The `Priority:`
reader is `lint-priority-field.py` alone; the `workspace-status`, `work-loop`,
`navigate-intents` and `close-work` scripts and the packaged engine copies must
hold no string constant that names the field or the lint.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SKILLS = _ROOT / "packs/core/.apm/skills"
_DATA = _ROOT / "packages/agentbundle/agentbundle/_data"
_SKILL_NAMES = ("workspace-status", "work-loop", "navigate-intents", "close-work")
_LINT = "lint-priority-field.py"
_FIELD = re.compile(r"\bPriority\b")


def _scoped_modules() -> list[Path]:
    """Every scoped skill script, and each packaged copy sharing its file name."""
    scripts = sorted(
        path
        for skill in _SKILL_NAMES
        for path in (_SKILLS / skill / "scripts").glob("*.py")
        if path.name != _LINT
    )
    names = {path.name for path in scripts}
    copies = sorted(path for path in _DATA.glob("*.py") if path.name in names)
    return [*scripts, *copies]


MODULES = _scoped_modules()


def _offending_constants(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and (_FIELD.search(node.value) or "lint-priority-field" in node.value)
    ]


def test_the_scope_is_not_empty_and_holds_the_engine_copy() -> None:
    assert MODULES
    assert _DATA / "workspace_status_engine.py" in MODULES
    assert _SKILLS / "workspace-status/scripts/workspace_status.py" in MODULES


@pytest.mark.parametrize("path", MODULES, ids=lambda p: str(p.relative_to(_ROOT)))
def test_no_string_constant_names_the_priority_field(path: Path) -> None:
    assert _offending_constants(path) == []


def test_the_guard_notices_a_constant_that_names_the_field(tmp_path: Path) -> None:
    probe = tmp_path / "probe.py"
    probe.write_text('FIELD = "- **Priority:**"\nLINT = "x/lint-priority-field.py"\n')
    assert len(_offending_constants(probe)) == 2
    probe.write_text('priority = "priority"\nclass PriorityClass: ...\n')
    assert _offending_constants(probe) == []
