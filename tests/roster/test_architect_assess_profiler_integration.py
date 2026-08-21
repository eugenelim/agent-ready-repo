"""Repository integration checks for the architect assessment profiler."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPO_ROOT / "packs" / "architect"
SCRIPT_PATH = PACK_ROOT / ".apm" / "skills" / "architect-assess" / "scripts" / "profile_repo.py"
FILE_SAFETY_PATH = (
    REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "catalogue_tooling" / "file_safety.py"
)


def _load(path: Path, name: str) -> ModuleType:
    """Load a module from a repository path without package installation."""

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_fallback_read_contract_matches_catalogue_helper_for_core_cases(
    tmp_path: Path,
) -> None:
    """Projected installs retain the catalogue helper's confinement behavior."""

    profiler = _load(SCRIPT_PATH, "architect_profile_repo_integration_test")
    profiler.catalogue_read_confined_regular_file = None
    profiler.catalogue_validate_confined_directory = None
    file_safety = _load(FILE_SAFETY_PATH, "agentbundle_file_safety_integration_test")
    target = tmp_path / "repo"
    target.mkdir()
    regular = target / "regular.py"
    regular.write_text("import os\n", encoding="utf-8")
    entry = profiler.Entry(regular, "regular.py", regular.stat().st_size)
    assert profiler._safe_read(target, entry, 100) == file_safety.read_confined_regular_file(
        target, regular, max_bytes=100
    )

    outside = tmp_path / "outside.py"
    outside.write_text("import sys\n", encoding="utf-8")
    link = target / "link.py"
    link.symlink_to(outside)
    unsafe_entry = profiler.Entry(link, "link.py", outside.stat().st_size)
    with pytest.raises(profiler.ProfileError):
        profiler._safe_read(target, unsafe_entry, 100)
    with pytest.raises(file_safety.UnsafeContentError):
        file_safety.read_confined_regular_file(target, link, max_bytes=100)
