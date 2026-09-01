"""Integrity contract for the maintained RFC-0099 fixture register."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
REGISTER = (
    REPOSITORY_ROOT
    / "docs"
    / "specs"
    / "rfc0099-migration-validation-record"
    / "fixture-register.md"
)
SPEC = REGISTER.with_name("spec.md")
SPECS_INDEX = REPOSITORY_ROOT / "docs" / "specs" / "README.md"
SHAPING_QA = SPEC.parent / "notes" / "shaping-efficacy-qa.md"
SHAPING_EVIDENCE = SPEC.parent / "notes" / "shaping-evidence.md"
EXPECTED_HEADER = (
    "Fixture ID",
    "Prompt or seeded defect",
    "Installed profile",
    "Exact expected result",
    "Owner",
)
EXPECTED_FAMILIES = {
    "ACT",
    "ALIAS",
    "SHAPE",
    "RFCARCH",
    "STATE",
    "CORE",
    "BOUNDARY",
}
EVIDENCE_PATH = re.compile(r"`((?:docs|packs|tests)/[^`]+)`")
EXPECTED_SHAPING_KEYS = {
    "SHAPE-UNNECESSARY-INTENT",
    "SHAPE-UNSAFE-SIMPLIFICATION",
    "SHAPE-WRAPPER-BRIEF",
    "SHAPE-SPECULATIVE-SLICES",
    "SHAPE-VAGUE-SPEC-OBJECTIVE",
    "SHAPE-MISSING-BOUNDARIES",
}


def _register_rows() -> list[tuple[str, ...]]:
    """Parse the one five-column Markdown table in the register."""
    lines = REGISTER.read_text(encoding="utf-8").splitlines()
    header_index = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("| Fixture ID |")
    )
    header = tuple(cell.strip() for cell in lines[header_index].strip("|").split("|"))
    assert header == EXPECTED_HEADER

    rows: list[tuple[str, ...]] = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        row = tuple(cell.strip() for cell in line.strip("|").split("|"))
        assert len(row) == len(EXPECTED_HEADER), row
        rows.append(row)
    return rows


def test_register_has_exact_schema_unique_ids_and_all_families() -> None:
    """Every maintained fixture row has five populated fields and an owner."""
    rows = _register_rows()
    assert rows
    assert all(all(cell for cell in row) for row in rows)

    fixture_ids = [row[0] for row in rows]
    assert len(fixture_ids) == len(set(fixture_ids))
    assert {fixture_id.split("-", 1)[0] for fixture_id in fixture_ids} == (
        EXPECTED_FAMILIES
    )
    assert {fixture_id for fixture_id in fixture_ids if fixture_id.startswith("ACT-")} == {
        f"ACT-R{number}" for number in range(1, 13)
    }
    assert {
        fixture_id for fixture_id in fixture_ids if fixture_id.startswith("SHAPE-")
    } == {
        "SHAPE-UNNECESSARY-INTENT",
        "SHAPE-UNSAFE-SIMPLIFICATION",
        "SHAPE-WRAPPER-BRIEF",
        "SHAPE-SPECULATIVE-SLICES",
        "SHAPE-VAGUE-SPEC-OBJECTIVE",
        "SHAPE-MISSING-BOUNDARIES",
    }


def test_register_evidence_paths_are_confined_regular_files() -> None:
    """Every exact result points at maintained repository evidence."""
    repository_root = REPOSITORY_ROOT.resolve()
    for fixture_id, _, _, exact_result, _ in _register_rows():
        paths = EVIDENCE_PATH.findall(exact_result)
        assert paths, fixture_id
        for relative_path in paths:
            candidate = (REPOSITORY_ROOT / relative_path).resolve()
            assert candidate.is_relative_to(repository_root), (fixture_id, relative_path)
            assert candidate.is_file(), (fixture_id, relative_path)


def test_register_discloses_late_creation_and_is_indexed() -> None:
    """The late register is explicit and its active owner keeps it discoverable."""
    register = REGISTER.read_text(encoding="utf-8")
    spec = SPEC.read_text(encoding="utf-8")
    index = SPECS_INDEX.read_text(encoding="utf-8")

    assert "**Version:** 1.0.0" in register
    assert "written after RFC-0099 acceptance" in register
    assert "required it before acceptance" in register
    assert "[`fixture-register.md`](fixture-register.md)" in spec
    assert "rfc0099-migration-validation-record/spec.md" in index


def test_shaping_keys_resolve_to_sanitized_adjudication_evidence() -> None:
    """Each stable defect key maps to a digest-bound data-only receipt."""
    qa = SHAPING_QA.read_text(encoding="utf-8")
    evidence = SHAPING_EVIDENCE.read_text(encoding="utf-8")
    assert "shaping-evidence.md" in qa
    assert "Non-authoritative evidence extract" in evidence
    assert "## Main-loop result" not in evidence
    assert "**Fix:**" not in evidence

    rows = []
    for line in evidence.splitlines():
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        if len(cells) == 7 and cells[3].startswith("`SHAPE-"):
            rows.append(cells)

    assert {row[3].strip("`") for row in rows} == EXPECTED_SHAPING_KEYS
    for _, fixture, digest, defect_key, identification, review_date, owner in rows:
        relative_path = fixture.strip("`")
        fixture_path = REPOSITORY_ROOT / relative_path
        assert fixture_path.is_file(), relative_path
        assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == digest.strip("`")
        assert defect_key.strip("`") in qa
        assert identification.startswith("`sustained`:")
        assert review_date == "2026-08-31"
        assert owner == "Core shaping-reviewer maintainers"
