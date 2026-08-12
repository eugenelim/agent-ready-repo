"""Shared pytest fixtures for the work-loop pack tests."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp(tmp_path: Path) -> Path:
    """Keep the legacy descriptive fixture name while using pytest lifecycle."""
    return tmp_path
