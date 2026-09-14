"""Every distributed package is in the mypy gate's argument list.

`tools/lint-mypy.py` passes `TYPED_PACKAGES` as positional arguments, which
override the `files` setting in `pyproject.toml`. A package missing from the
list is silently unchecked: the gate still prints `Success`, just about fewer
files. `jsonl-otlp-exporter` shipped that way and nothing reported it -- the
count in the output was the only evidence, and a count nobody reads is not a
control.
"""

from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGES = REPO_ROOT / "packages"


def _typed_packages() -> list[str]:
    spec = importlib.util.spec_from_file_location("lint_mypy", REPO_ROOT / "tools" / "lint-mypy.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.TYPED_PACKAGES)


def _distributed_import_packages() -> set[str]:
    """The import package each distribution declares, from its own manifest.

    A distribution is a directory with a `pyproject.toml`, and its import
    package is `[project] name` with dashes normalised to underscores.
    `packages/_example/` has no manifest -- it is a documentation template with
    no Python in it -- so the same rule that includes the others excludes it.

    Taking the name from the manifest rather than from "every directory holding
    an `__init__.py`" matters: the filesystem rule also returns
    `packages/agentbundle/tests`, which is a published tree but is not the
    distribution's import package, and excluding it would mean this test
    carrying a hard-coded directory name it has to keep remembering.
    """
    found: set[str] = set()
    for pyproject in sorted(PACKAGES.glob("*/pyproject.toml")):
        raw = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        import_name = raw["project"]["name"].replace("-", "_")
        target = pyproject.parent / import_name
        assert target.is_dir(), (
            f"{pyproject} declares `{raw['project']['name']}` but there is no "
            f"{target.relative_to(REPO_ROOT)} directory; the layout convention moved"
        )
        found.add(str(target.relative_to(REPO_ROOT)))
    return found


def test_every_distributed_package_is_type_checked():
    missing = _distributed_import_packages() - set(_typed_packages())
    assert not missing, (
        "these import packages ship but mypy never sees them, because "
        f"TYPED_PACKAGES overrides the config's file set: {sorted(missing)}"
    )


def test_every_listed_path_still_exists():
    """A renamed package would otherwise make mypy fail on a missing path, or
    -- worse, if mypy tolerated it -- check nothing under that name."""
    for entry in _typed_packages():
        assert (REPO_ROOT / entry).is_dir(), f"TYPED_PACKAGES names a path that is gone: {entry}"


def test_the_guard_can_fail():
    """The discovery half is what breaks first if the layout convention moves."""
    assert _distributed_import_packages(), "no distribution was discovered; the glob is wrong"
