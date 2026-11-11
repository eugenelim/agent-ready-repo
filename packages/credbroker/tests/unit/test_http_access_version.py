"""Version consistency test for credbroker 0.7.

Asserts that the pyproject.toml version, the version.py constant, and the
public credbroker.__version__ attribute all agree, and that they all name 0.7.
"""

from __future__ import annotations

from pathlib import Path

import credbroker
from credbroker.version import __version__ as version_py_version


def test_version_py_matches_public_attribute() -> None:
    """credbroker.__version__ matches version.py __version__."""
    assert credbroker.__version__ == version_py_version


def test_version_is_0_7_0() -> None:
    """credbroker.__version__ is exactly 0.7.0."""
    assert credbroker.__version__ == "0.7.0"


def test_pyproject_version_matches_version_py() -> None:
    """pyproject.toml [project].version matches version.py __version__."""
    import re

    package_root = Path(__file__).resolve().parents[2]
    pyproject = package_root / "pyproject.toml"
    assert pyproject.is_file(), f"pyproject.toml not found at {pyproject}"

    content = pyproject.read_text(encoding="utf-8")
    # Match 'version = "..."' in the [project] section.
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "Could not find version in pyproject.toml"
    pyproject_version = match.group(1)

    assert pyproject_version == version_py_version, (
        f"pyproject.toml version {pyproject_version!r} != "
        f"version.py {version_py_version!r}"
    )
