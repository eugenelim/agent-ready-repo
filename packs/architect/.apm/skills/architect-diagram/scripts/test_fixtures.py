"""Syntax validation suite for architect-diagram fixture files.

Each *.mmd file under scripts/testdata/ is parsed by mmdc (Mermaid CLI).
Confirms that every fixture the skill ships as a reference example actually
parses — a regression guard for syntax changes to the reference files.

Run: python -m pytest scripts/test_fixtures.py -v
     (from the skill directory, or prefix the path from the repo root)

Requirements: mmdc must be on PATH (npm install -g @mermaid-js/mermaid-cli).
Skips all cases when mmdc is absent.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TESTDATA = HERE / "testdata"

_MMDC = shutil.which("mmdc")

_fixtures = sorted(TESTDATA.glob("*.mmd")) if TESTDATA.is_dir() else []


@pytest.mark.skipif(_MMDC is None, reason="mmdc not in PATH")
@pytest.mark.parametrize(
    "fixture",
    _fixtures if _fixtures else [pytest.param(None, marks=pytest.mark.skip(reason="no fixtures"))],
    ids=[f.stem for f in _fixtures] if _fixtures else ["no-fixtures"],
)
def test_fixture_parses(fixture, tmp_path):
    if fixture is None:
        pytest.skip("no fixtures")
    out = tmp_path / "out.svg"
    result = subprocess.run(
        [_MMDC, "-i", str(fixture), "-o", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"{fixture.name} failed mmdc parse.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
