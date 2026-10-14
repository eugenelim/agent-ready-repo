"""Release view of the product changelog, across both storage forms.

New releases are recorded as fragments (or monthly bundles) under
``docs/product/``; the frozen ``changelog.md`` holds only the history before
that move. A test that asks "what is the newest release of package X" or
"does entry [X][v] exist" therefore cannot read the raw file: the newest
release may sit in a record that the raw file does not contain. This module
answers those questions from the complete view that
``tools/changelog.py`` assembles, so a release recorded in either form is seen.

Precondition: an ``origin/main`` ref must resolve, because the tool validates
fragments against ``git merge-base`` with it. The CI jobs get it from
``fetch-depth: 0``; a local checkout needs ``git fetch origin main``.

Not collected by pytest (no ``test_`` prefix); import it from a roster test.
"""

from __future__ import annotations

import importlib.util
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "docs" / "product" / "changelog.md"
FRAGMENTS = ROOT / "docs" / "product" / "changelog.d"

_MODULE_NAME = "roster_product_changelog_releases_model"


def version_tuple(version: str) -> tuple[int, ...]:
    """Order key for a dotted numeric version; non-numeric parts give ``()``."""
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return ()


def _model() -> ModuleType:
    """Load ``tools/changelog.py`` once under a name no other test uses."""
    loaded = sys.modules.get(_MODULE_NAME)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(
        _MODULE_NAME, ROOT / "tools" / "changelog.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def complete_changelog() -> str:
    """Return frozen history plus every record, as the tool renders it."""
    return _model().render_complete_changelog(baseline=BASELINE, fragments=FRAGMENTS)


@lru_cache(maxsize=1)
def _parsed_view() -> tuple[str, tuple[dict, ...], tuple]:
    text = complete_changelog()
    parsed = _model().parse_changelog_releases(text)
    return text, tuple(parsed.releases), tuple(parsed.headings)


def release_versions(
    package: str, *, include_nested: bool = False, text: str | None = None
) -> list[str]:
    """Every released version of ``package`` in either form, newest first.

    Entries nested beneath ``[Unreleased]`` are left out unless
    ``include_nested`` is set; the frozen history holds some artifacts' current
    release there, and a caller matching the heading at either level needs them.
    ``text`` reads a synthetic complete-view changelog instead of the repository's.
    """
    if text is None:
        releases = _parsed_view()[1]
    else:
        releases = tuple(_model().parse_changelog_releases(text).releases)
    found = {
        entry["version"]
        for release in releases
        if include_nested or not release["unreleased"]
        for entry in release["packages"]
        if entry["name"] == package
    }
    return sorted(found, key=version_tuple, reverse=True)


def latest_release_version(
    package: str, *, include_nested: bool = False, text: str | None = None
) -> str:
    """Highest released version of ``package`` by version tuple, or ``""``."""
    versions = release_versions(package, include_nested=include_nested, text=text)
    return versions[0] if versions else ""
