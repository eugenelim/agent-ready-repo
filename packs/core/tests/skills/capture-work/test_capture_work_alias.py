"""Compatibility checks for the deprecated capture-work surface."""

from __future__ import annotations

import re
from pathlib import Path

_PACK_ROOT = Path(__file__).resolve().parents[3]
_CAPTURE_PATH = _PACK_ROOT / ".apm" / "skills" / "capture-work" / "SKILL.md"
_INTAKE_PATH = _PACK_ROOT / ".apm" / "skills" / "work-intake" / "SKILL.md"


def _body(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(body: str) -> str:
    match = re.match(r"---\n(.*?)\n---\n", body, flags=re.DOTALL)
    assert match is not None
    return match.group(1)


def _allowed_tools(body: str) -> set[str]:
    frontmatter = _frontmatter(body)
    match = re.search(r"^allowed-tools:\s*(.+)$", frontmatter, flags=re.MULTILINE)
    assert match is not None
    return set(match.group(1).split())


def _metadata_boundaries(body: str) -> set[str]:
    frontmatter = _frontmatter(body)
    boundaries: set[str] = set()
    in_boundaries = False
    for line in frontmatter.splitlines():
        if line == "  boundaries:":
            in_boundaries = True
            continue
        if in_boundaries:
            if line.startswith("    - "):
                boundaries.add(line.removeprefix("    - "))
                continue
            if line and not line.startswith(" "):
                break
    return boundaries


def test_alias_forwards_equivalent_intake() -> None:
    body = _body(_CAPTURE_PATH)
    assert "Compatibility alias for `work-intake`" in body
    assert "same normalized intake envelope" in body
    assert "`action: remember`" in body
    assert "Invoke `work-intake`" in body
    assert "Return the `work-intake` result unchanged" in body


def test_alias_emits_deprecation_and_writes_no_legacy_state() -> None:
    body = _body(_CAPTURE_PATH)
    assert "`capture-work` is deprecated" in body
    assert "canonical intake contract" in body
    assert "Do not edit storage directly from this alias" in body
    forbidden = (
        "[build]",
        "[shape]",
        "tomlkit",
        "comment-preserving",
        "destination map",
        "legacy persistence path here.",
    )
    for phrase in forbidden:
        assert phrase not in body


def test_alias_has_no_independent_classifier_or_direct_writer() -> None:
    body = _body(_CAPTURE_PATH)
    normalized_body = " ".join(body.split())
    assert "no independent routing" in body
    assert "no independent routing,\nclassification, or storage behavior" in body
    assert "Do not maintain a separate classifier" in body
    assert "all artifact and workspace mutations belong to `work-intake`" in normalized_body
    assert "workspace.toml" not in body
    assert "Append " not in body


def test_alias_declares_no_broader_surface_than_work_intake() -> None:
    capture = _body(_CAPTURE_PATH)
    intake = _body(_INTAKE_PATH)
    assert _metadata_boundaries(capture) <= _metadata_boundaries(intake)
    assert _allowed_tools(capture) <= _allowed_tools(intake)
