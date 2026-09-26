"""Shipped pack content this slice creates or edits carries no internal citation.

`packs/AGENTS.md` confines shipped pack content to portable guidance: no ADR or
RFC number, no acceptance-criterion identifier, and no repository-only path in a
`SKILL.md` or any other file a pack ships. `packs/AGENTS.local.md` publishes the
pattern; this test is what runs it, because no existing lint does —
`tools/lint-guides-no-repo-only-refs.py` defaults its root to `guides/`.

Scope is the three shipped trees this slice creates or edits, and the pass
condition is zero matches. Zero tolerance is admissible because all three
measured zero before this test existed; a hit is therefore this slice's.

`packs/atlassian/tests/**` is deliberately outside the scan. Tests are not
projected into installed adapters, so they are not shipped pack content, and the
pack's suites carry such citations on purpose — the stub contract mandates the
`# STUB: AC<n>` marker form, and the sibling bridge test cites ADR-0126 D4 to say
what it is asserting. Widening the scan over them would force stripping markers
another contract requires.

Tests are not shipped pack content, so the citations above are in scope here and
would not be in a `SKILL.md`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[2]

# The three shipped trees this slice creates or edits. `pack.toml` is a file
# rather than a tree and is scanned as itself.
SCANNED_PATHS = (
    PACK_ROOT / ".apm" / "skills" / "jira-epic-outcome-view",
    PACK_ROOT / ".apm" / "skills" / "flow-metrics",
    PACK_ROOT / "pack.toml",
)

# The pattern `packs/AGENTS.local.md` publishes for this rule, unchanged. An
# IETF RFC number never starts with `0`, unlike this catalogue's zero-padded
# identifiers, so the leading zero is what keeps an external citation out.
CITATION_PATTERN = re.compile(
    r"\b(RFC|ADR)-0[0-9]{3}\b"
    r"|\bAC-?[0-9]+[a-z]?(\([a-z]\))?\b"
    r"|docs/(specs|rfc|adr|contracts)/[a-z0-9]"
)

# Compiled bytecode is build output, not shipped content, and reading it as
# text would manufacture matches out of binary noise.
SKIPPED_DIRECTORY_NAMES = frozenset({"__pycache__"})


def _scanned_files() -> list[Path]:
    """Every regular file under the scanned paths, bytecode caches excluded."""
    files: list[Path] = []
    for target in SCANNED_PATHS:
        if target.is_file():
            files.append(target)
            continue
        for path in sorted(target.rglob("*")):
            if not path.is_file():
                continue
            if SKIPPED_DIRECTORY_NAMES.intersection(path.parts):
                continue
            files.append(path)
    return files


def _citations_in(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return [match.group(0) for match in CITATION_PATTERN.finditer(text)]


def test_the_pattern_matches_the_citation_forms_it_is_meant_to_catch() -> None:
    """A positive control. Without it a pattern that stopped matching would
    make every assertion below pass while enforcing nothing."""
    for sample in (
        "see " + "ADR-" + "0126 D4",
        "see " + "RFC-" + "0082",
        "satisfies " + "AC" + "44",
        "satisfies " + "AC-" + "44a",
        "recorded in " + "docs/" + "specs/jira-epic-outcome-view/spec.md",
    ):
        assert CITATION_PATTERN.search(sample), f"pattern no longer matches: {sample}"

    assert not CITATION_PATTERN.search("RFC 7231 defines the method semantics")
    assert not CITATION_PATTERN.search("the AC power supply")


def test_the_scan_reaches_all_three_shipped_trees() -> None:
    """A guard against a vacuous pass: an empty file list asserts nothing."""
    for target in SCANNED_PATHS:
        assert target.exists(), f"scanned path is missing: {target}"

    files = _scanned_files()
    assert files, "the citation scan found no files to read"

    roots = {
        target
        for target in SCANNED_PATHS
        if any(path == target or target in path.parents for path in files)
    }
    assert roots == set(SCANNED_PATHS), f"trees contributing no file: {set(SCANNED_PATHS) - roots}"


@pytest.mark.parametrize("path", _scanned_files(), ids=lambda p: str(p.relative_to(PACK_ROOT)))
def test_shipped_file_carries_no_internal_citation(path: Path) -> None:
    """Zero tolerance. All three trees measured zero, so any hit is new."""
    found = _citations_in(path)

    assert found == [], f"{path.relative_to(PACK_ROOT)} cites internal records: {found}"
