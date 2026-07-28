"""Unit tests for agentbundle.catalogue_tooling.build.

Tests _validate_recipe_path and build_catalogue.

Note on a known import-aliasing quirk: ``import agentbundle.build.main as _build_main``
inside build_catalogue resolves to the ``main`` *function* defined in
``agentbundle/build/__init__.py``, not the ``main.py`` submodule, because
``__init__.py`` overwrites the submodule binding with the function definition.
The build module is available as the *module* via
``sys.modules['agentbundle.build.main']``.  Fixtures below account for this.
"""

from __future__ import annotations

import importlib
from unittest.mock import patch

import pytest
from agentbundle.catalogue_tooling.build import _validate_recipe_path, build_catalogue
from agentbundle.catalogue_tooling.results import BuildResult

# ---------------------------------------------------------------------------
# _validate_recipe_path
# ---------------------------------------------------------------------------


def test_validate_recipe_path_empty(tmp_path):
    """Empty string recipe path raises ValueError."""
    with pytest.raises(ValueError, match="empty"):
        _validate_recipe_path(tmp_path, "")


def test_validate_recipe_path_absolute(tmp_path):
    """Absolute path raises ValueError."""
    with pytest.raises(ValueError, match="absolute"):
        _validate_recipe_path(tmp_path, "/etc/foo.toml")


def test_validate_recipe_path_dotdot(tmp_path):
    """Path with traversal (..) raises ValueError."""
    with pytest.raises(ValueError, match="traversal|outside"):
        _validate_recipe_path(tmp_path, "../../escape.toml")


def test_validate_recipe_path_valid(tmp_path):
    """A well-formed relative path within root raises no error."""
    # recipes/foo.toml resolves inside tmp_path — should be accepted
    _validate_recipe_path(tmp_path, "recipes/foo.toml")


# ---------------------------------------------------------------------------
# build_catalogue — shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def build_main_module(monkeypatch):
    """Return the agentbundle.build.main *module* with required attributes set.

    build_catalogue binds ``import agentbundle.build.main as _build_main`` to
    the *function* from __init__.py (because __init__.py redefines ``main``
    after the submodule import).  That function object is then accessed for
    ``_DIST_BRANCH`` and ``_MARKETPLACE_DESCRIPTION``.  We set those
    attributes on the function so the call path does not raise AttributeError.

    The actual ``cmd_build`` lives on the *module* (in sys.modules), so we
    return the module for callers that need to patch ``cmd_build``.
    """
    import agentbundle.build

    main_fn = agentbundle.build.main  # the function, not the module
    monkeypatch.setattr(main_fn, "_DIST_BRANCH", "test-branch", raising=False)
    monkeypatch.setattr(main_fn, "_MARKETPLACE_DESCRIPTION", "", raising=False)

    return importlib.import_module("agentbundle.build.main")


# ---------------------------------------------------------------------------
# build_catalogue
# ---------------------------------------------------------------------------


def test_build_catalogue_no_catalogue_toml(tmp_path, build_main_module):
    """No catalogue.toml present: ok reflects cmd_build exit code; command is set."""
    with patch.object(build_main_module, "cmd_build", return_value=1):
        result = build_catalogue(tmp_path)

    assert result.ok is False
    assert result.command == "catalogue build"


def test_build_catalogue_delegates(tmp_path, build_main_module):
    """build_catalogue delegates to cmd_build and returns a BuildResult."""
    with patch.object(build_main_module, "cmd_build", return_value=0) as mock_cmd:
        result = build_catalogue(tmp_path)

    assert isinstance(result, BuildResult)
    mock_cmd.assert_called_once()
