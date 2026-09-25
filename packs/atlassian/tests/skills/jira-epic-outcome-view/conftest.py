"""Shared loader for this skill's modules.

The skill is loaded under a pack-and-skill-qualified name rather than by
putting its `scripts/` directory on `sys.path`: skills are independent
and several packs ship a module of the same bare name, so a bare import
would bind whichever directory reached the path first and then cache it
for every later importer. The same rule is why this helper is named for
its pack too.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_VIEW_PKG = (
    _PACK_ROOT / ".apm" / "skills" / "jira-epic-outcome-view"
    / "scripts" / "jira_epic_outcome_view"
)
_VIEW_NAME = "atlassian_jira_epic_outcome_view"

PACK_ROOT = _PACK_ROOT


def load_view_submodule(submodule: str) -> ModuleType:
    """Load one submodule of the view package under the qualified name."""
    if _VIEW_NAME not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            _VIEW_NAME, _VIEW_PKG / "__init__.py",
            submodule_search_locations=[str(_VIEW_PKG)],
        )
        if spec is None or spec.loader is None:
            raise ModuleNotFoundError(_VIEW_NAME)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    if not submodule:
        return sys.modules[_VIEW_NAME]
    return importlib.import_module(f"{_VIEW_NAME}.{submodule}")


@pytest.fixture
def pack_root() -> Path:
    """The installed pack tree, one of the two roots a run must not change."""
    return PACK_ROOT


@pytest.fixture
def load_module():
    """Factory fixture: `load_module("view")`, `load_module("")` for the CLI."""
    return load_view_submodule
