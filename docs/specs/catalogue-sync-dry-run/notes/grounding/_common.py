"""Shared confined reads and failure handling for the § Grounding derivations."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
PACKAGE_ROOT = REPO_ROOT / "packages" / "agentbundle"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from agentbundle.catalogue_tooling.file_safety import (  # noqa: E402
    list_confined_regular_files,
    read_confined_regular_file,
    validate_confined_directory,
)


def read_text(relative: str) -> str:
    """Return a UTF-8 repository file through the blessed confinement helper."""
    path = REPO_ROOT / relative
    return read_confined_regular_file(REPO_ROOT, path).decode("utf-8")


def files_under(relative: str) -> list[Path]:
    """Return confined regular files below a repository directory."""
    directory = REPO_ROOT / relative
    validate_confined_directory(REPO_ROOT, directory)
    return list_confined_regular_files(REPO_ROOT, directory)


def fail(reason: str) -> int:
    """Write the required one-line diagnostic and return a failing status."""
    print(reason, file=sys.stderr)
    return 1
