"""Shared pytest fixtures for the work-loop pack tests."""

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
