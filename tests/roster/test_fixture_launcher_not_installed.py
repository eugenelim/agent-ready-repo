"""Roster test: the fixture launcher's marker reaches no file the Core pack installs.

The fixture launcher is a test fixture that simulates an attesting host. It carries a marker,
and the supervisor refuses a launcher with that marker unless a test enables an in-process
seam. This suite scans every surface the Core pack installs or builds for the marker, and
for any assignment of the two test seams other than ``False``. It reads outside the pack, so
it lives here and not in the pack's own tests.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MARKER = b"agentbundle-fixture-launcher:not-a-host"
SEAMS = ("ALLOW_FIXTURE_LAUNCHER", "INTEGRATE_IN_COMPLETION_ORDER")
# An assignment (plain, annotated, walrus, or setattr/monkeypatch) of a seam to anything but False.
_ASSIGNED = re.compile(
    rb"(?:" + b"|".join(s.encode() for s in SEAMS)
    + rb")\s*(?::\s*\w+\s*)?(?::=|=(?!=))\s*+(?!False\b)"
)
_SETATTR = re.compile(
    rb"(?:setattr|setenv)\([^)]*(?:" + b"|".join(s.encode() for s in SEAMS) + rb")"
)

# The Core pack outside its tests, and the projections `make build-self` already wrote.
SURFACES = [
    ROOT / "packs" / "core",
    ROOT / ".claude" / "skills" / "work-loop",
    ROOT / ".agents" / "skills" / "work-loop",
    ROOT / ".kiro" / "skills" / "work-loop",
    ROOT / ".github" / "skills" / "work-loop",
    ROOT / "packages" / "agentbundle" / "agentbundle" / "_data",
]
EXCLUDED = (ROOT / "packs" / "core" / "tests",)


def _files(surface: Path) -> list[Path]:
    if not surface.exists():
        return []
    found = []
    for path in sorted(surface.rglob("*")):
        if path.is_symlink() or not path.is_file() or "__pycache__" in path.parts:
            continue
        if any(excluded == path or excluded in path.parents for excluded in EXCLUDED):
            continue
        found.append(path)
    return found


def scan(files: list[Path]) -> list[str]:
    """Paths holding the marker or a seam assignment."""
    hits = []
    for path in files:
        data = path.read_bytes()
        if MARKER in data or _ASSIGNED.search(data) or _SETATTR.search(data):
            hits.append(str(path))
    return hits


@pytest.mark.parametrize("surface", SURFACES, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_installed_file_carries_the_marker_or_enables_a_seam(surface: Path) -> None:
    assert scan(_files(surface)) == []


def test_the_pack_source_surface_exists_and_is_scanned() -> None:
    files = _files(ROOT / "packs" / "core" / ".apm")
    assert any(p.name == "_supervisor_launcher.py" for p in files)


def test_the_scan_finds_a_planted_marker_and_each_seam_assignment(tmp_path: Path) -> None:
    clean = tmp_path / "clean.py"
    clean.write_text("ALLOW_FIXTURE_LAUNCHER = False\nINTEGRATE_IN_COMPLETION_ORDER: bool = False\n")
    assert scan([clean]) == []
    planted = {
        "marker.txt": MARKER.decode(),
        "assign.py": "ALLOW_FIXTURE_LAUNCHER = True\n",
        "annotated.py": "INTEGRATE_IN_COMPLETION_ORDER: bool = True\n",
        "walrus.py": "if (ALLOW_FIXTURE_LAUNCHER := 1): pass\n",
        "setattr.py": "monkeypatch.setattr(mod, 'ALLOW_FIXTURE_LAUNCHER', True)\n",
        "setenv.py": "monkeypatch.setenv('ALLOW_FIXTURE_LAUNCHER', '1')\n",
    }
    for name, text in planted.items():
        path = tmp_path / name
        path.write_text(text)
        assert scan([path]) == [str(path)], name


def test_the_fixture_launcher_carries_the_marker_and_lives_only_in_the_pack_tests() -> None:
    fixture = ROOT / "packs" / "core" / "tests" / "skills" / "work-loop" / "fixture_launcher.py"
    assert MARKER in fixture.read_bytes()
    holders = []
    for surface in SURFACES:
        holders += [p for p in _files(surface) if p.name.startswith("fixture_launcher")]
    assert holders == []
