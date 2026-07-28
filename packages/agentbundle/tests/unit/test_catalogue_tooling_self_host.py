"""Unit tests for agentbundle.catalogue_tooling.self_host.

Tests check_self_host and write_self_host.
"""

from __future__ import annotations

from unittest.mock import patch

from agentbundle.catalogue_tooling.results import SelfHostResult
from agentbundle.catalogue_tooling.self_host import check_self_host, write_self_host

# Canonical patch target: run_self_host is imported lazily inside each
# function via ``from agentbundle.build.self_host import run_self_host``.
# Patching the module-level attribute on the source module is the correct
# approach; the lazy from-import picks up the patched object each call.
_RUN_SELF_HOST = "agentbundle.build.self_host.run_self_host"


# ---------------------------------------------------------------------------
# check_self_host
# ---------------------------------------------------------------------------


def test_check_self_host_no_catalogue_toml(tmp_path):
    """No catalogue.toml: check_self_host returns SelfHostResult with ok=False."""
    with patch(_RUN_SELF_HOST, return_value=1):
        result = check_self_host(tmp_path)

    assert isinstance(result, SelfHostResult)
    assert result.ok is False


def test_check_delegates_to_run_self_host(tmp_path):
    """check_self_host calls run_self_host with dry_run=True and force=False."""
    with patch(_RUN_SELF_HOST, return_value=0) as mock_run:
        check_self_host(tmp_path)

    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs.get("dry_run") is True
    assert kwargs.get("force") is False


# ---------------------------------------------------------------------------
# write_self_host
# ---------------------------------------------------------------------------


def test_write_self_host_no_catalogue_toml(tmp_path):
    """No catalogue.toml: write_self_host returns SelfHostResult with ok=False."""
    with patch(_RUN_SELF_HOST, return_value=1):
        result = write_self_host(tmp_path)

    assert isinstance(result, SelfHostResult)
    assert result.ok is False


def test_write_delegates_to_run_self_host(tmp_path):
    """write_self_host calls run_self_host with dry_run=False."""
    with patch(_RUN_SELF_HOST, return_value=0) as mock_run:
        write_self_host(tmp_path)

    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs.get("dry_run") is False


def test_write_force_propagated(tmp_path):
    """write_self_host(root, force=True) passes force=True to run_self_host."""
    with patch(_RUN_SELF_HOST, return_value=0) as mock_run:
        write_self_host(tmp_path, force=True)

    _, kwargs = mock_run.call_args
    assert kwargs.get("force") is True
