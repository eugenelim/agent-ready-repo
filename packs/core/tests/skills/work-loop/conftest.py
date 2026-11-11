"""Shared pytest fixtures for the work-loop pack tests."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def tmp(tmp_path: Path) -> Path:
    """Keep the legacy descriptive fixture name while using pytest lifecycle."""
    return tmp_path


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Provide a temporary repository for CLI fixtures requiring a repo root."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True)
    return tmp_path


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Keep every ``n``th collected test when ``WORK_SUPERVISOR_SHARD`` is ``i/n``.

    A CI job that cannot fit a slow suite in its time budget runs it in parts. The
    parts are disjoint and together cover the suite by construction.
    """
    spec = os.environ.get("WORK_SUPERVISOR_SHARD", "")
    if not spec:
        return
    index, count = (int(part) for part in spec.split("/"))
    if not 0 <= index < count:
        # A shard that selects nothing would pass in silence; the index is 0-based.
        raise pytest.UsageError(f"WORK_SUPERVISOR_SHARD={spec}: need 0 <= i < n")
    kept = [item for position, item in enumerate(items) if position % count == index]
    config.hook.pytest_deselected(items=[item for item in items if item not in kept])
    items[:] = kept
