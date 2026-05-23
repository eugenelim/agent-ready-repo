"""T8: integration tests for ``agentbundle list-packs``.

Coverage:
  - Happy path: fixture catalogue with two packs (alpha, beta) lists both rows
    with name, version, description present in stdout.
  - Local absolute path form works.
  - Local relative path form (resolved relative to cwd) works.
  - Unreachable git URL exits non-zero with stderr.
"""

from __future__ import annotations

import os
import types
import urllib.error
from pathlib import Path
from unittest import mock

import pytest

# Fixture catalogue: tests/fixtures/list_packs/catalogue/
FIXTURE_CATALOGUE = (
    Path(__file__).parent.parent / "fixtures" / "list_packs" / "catalogue"
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _args(catalogue: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(catalogue=catalogue)


def _run(catalogue: str) -> int:
    from agentbundle.commands.list_packs import run
    return run(_args(catalogue))


# ---------------------------------------------------------------------------
# 1. Happy path — absolute path, two packs listed
# ---------------------------------------------------------------------------

def test_happy_path_absolute_lists_both_packs(capsys):
    """list-packs against the fixture catalogue exits 0 and prints alpha + beta."""
    rc = _run(str(FIXTURE_CATALOGUE))
    assert rc == 0, "exit code should be 0 for a valid catalogue"

    out = capsys.readouterr().out
    assert "alpha" in out, "alpha pack should appear in output"
    assert "beta" in out, "beta pack should appear in output"
    # Version and description columns.
    assert "0.1.0" in out
    assert "0.2.0" in out
    assert "Alpha fixture pack" in out
    assert "Beta fixture pack" in out


# ---------------------------------------------------------------------------
# 2. Rows are stable — alpha sorts before beta
# ---------------------------------------------------------------------------

def test_output_is_stable_sorted(capsys):
    """Packs must appear in deterministic (alphabetical) order."""
    rc = _run(str(FIXTURE_CATALOGUE))
    assert rc == 0
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.strip()]
    # Skip header and separator; first data row is alpha.
    data_lines = [l for l in lines if not l.startswith("NAME") and not l.startswith("-")]
    assert data_lines[0].startswith("alpha"), "alpha should come before beta"
    assert data_lines[1].startswith("beta"), "beta should be second"


# ---------------------------------------------------------------------------
# 3. Local relative path form
# ---------------------------------------------------------------------------

def test_local_relative_path(capsys, tmp_path, monkeypatch):
    """A relative path (resolved from cwd) should work."""
    monkeypatch.chdir(FIXTURE_CATALOGUE.parent.parent)  # tests/fixtures/
    rc = _run("list_packs/catalogue")
    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


# ---------------------------------------------------------------------------
# 4. Unreachable git URL → exit non-zero + stderr
# ---------------------------------------------------------------------------

def test_unreachable_git_url_exits_nonzero(capsys):
    """An unreachable git+https:// URL should exit 1 with a message on stderr."""
    def _raise(url, **kwargs):
        raise urllib.error.URLError("Name or service not known")

    with mock.patch("urllib.request.urlopen", side_effect=_raise):
        rc = _run("git+https://github.com/owner/unreachable-repo@v1.0")

    assert rc != 0, "should exit non-zero for unreachable URL"
    err = capsys.readouterr().err
    assert err.strip(), "stderr should contain an error message"


# ---------------------------------------------------------------------------
# 5. Dependencies column shows beta's dep on alpha
# ---------------------------------------------------------------------------

def test_beta_dependency_shown(capsys):
    """beta's dependency on alpha should appear in the dependencies column."""
    rc = _run(str(FIXTURE_CATALOGUE))
    assert rc == 0
    out = capsys.readouterr().out
    # Find the beta row and check it mentions alpha.
    beta_lines = [l for l in out.splitlines() if l.strip().startswith("beta")]
    assert beta_lines, "beta row must be present"
    assert "alpha" in beta_lines[0], "beta's dep on alpha must appear in the row"
