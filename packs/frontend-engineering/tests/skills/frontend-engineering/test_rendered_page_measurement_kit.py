"""Contract tests for the measurement kit and for what shipped content may say.

The kit exists because the false-positive rate does not transfer between viewer
configurations, so the pack ships fixtures and a procedure rather than a number.
These tests hold that line from both ends: the procedure has to name real,
present, non-empty fixture sets and the denominator it divides by, and no shipped
pack content may state a rate or name anything that only exists in the
repository the pack is developed in.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from frontend_engineering_rendered_page_rules import PACK_ROOT, severity_by_class, read_rules

SKILL_DIR = PACK_ROOT / ".apm" / "skills" / "frontend-engineering"
MEASUREMENT = SKILL_DIR / "references" / "rendered-page-measurement.md"
FIXTURES = SKILL_DIR / "references" / "inspection-fixtures"

# Everything under `.apm/` is projected into an adopter's environment. Tests and
# pack documentation are not, so the reach of the two prohibition checks below
# is exactly this.
SHIPPED_ROOT = PACK_ROOT / ".apm"


@pytest.fixture(scope="module")
def procedure() -> str:
    return MEASUREMENT.read_text(encoding="utf-8")


def _named_fixtures(procedure_markdown: str, kind: str) -> list[str]:
    """Fixture filenames the procedure names under its `defect` or `clean` heading."""
    heading = {
        "defect": "### Defect fixtures",
        "clean": "### Known-clean fixtures",
    }[kind]
    assert heading in procedure_markdown, f"the procedure has no {heading!r} section"
    section = procedure_markdown.split(heading, 1)[1].split("\n## ", 1)[0]
    section = section.split("\n### ", 1)[0]
    return re.findall(r"([A-Za-z0-9._-]+\.html)", section)


def _meta(fixture: Path, name: str) -> str | None:
    text = fixture.read_text(encoding="utf-8")
    match = re.search(
        rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"', text
    )
    return match.group(1) if match else None


# ── the fixtures the procedure names are really there ───────────────────────

def test_every_defect_fixture_named_is_present(procedure: str) -> None:
    """Verifies: the pack ships every defect fixture the measurement procedure
    names."""
    named = _named_fixtures(procedure, "defect")
    assert named, "the procedure names no defect fixtures"
    for name in named:
        assert (FIXTURES / name).is_file(), f"{name} is named but not shipped"


def test_every_known_clean_fixture_named_is_present(procedure: str) -> None:
    """Verifies: the pack ships every known-clean fixture the measurement
    procedure names."""
    named = _named_fixtures(procedure, "clean")
    assert named, "the procedure names no known-clean fixtures"
    for name in named:
        assert (FIXTURES / name).is_file(), f"{name} is named but not shipped"


def test_the_procedure_names_a_non_empty_defect_set(procedure: str) -> None:
    """Verifies: the procedure names a non-empty set of defect fixtures.

    Without this, a delivery shipping zero fixtures satisfies every other
    measurement criterion before any work has happened.
    """
    assert len(_named_fixtures(procedure, "defect")) > 0


def test_the_procedure_names_a_non_empty_known_clean_set(procedure: str) -> None:
    """Verifies: the procedure names a non-empty set of known-clean fixtures."""
    assert len(_named_fixtures(procedure, "clean")) > 0


@pytest.mark.parametrize("kind", ["defect", "clean"])
def test_a_procedure_naming_an_empty_set_fails(procedure: str, kind: str) -> None:
    """The mutation behind the two checks above: emptying either set must fail,
    or 'non-empty' is a claim nothing tests."""
    heading = {
        "defect": "### Defect fixtures — 4",
        "clean": "### Known-clean fixtures — 4",
    }[kind]
    assert heading in procedure
    body_start = procedure.index(heading)
    next_heading = procedure.index("\n## ", body_start)
    emptied = procedure[:body_start] + heading + "\n\nNone.\n" + procedure[next_heading:]
    assert _named_fixtures(emptied, kind) == [], (
        "the emptied procedure still appears to name fixtures"
    )


# ── every shipped fixture is accounted for, in both directions ──────────────

def test_every_shipped_fixture_is_named_by_the_procedure(procedure: str) -> None:
    """The reverse of the two presence checks. A fixture shipped but not named is
    dead weight an adopter measures over without meaning to."""
    named = set(_named_fixtures(procedure, "defect")) | set(
        _named_fixtures(procedure, "clean")
    )
    shipped = {p.name for p in FIXTURES.glob("*.html")}
    assert shipped == named, (
        f"shipped but unnamed: {sorted(shipped - named)}; "
        f"named but unshipped: {sorted(named - shipped)}"
    )


def test_each_defect_fixture_declares_a_real_finding_class(procedure: str) -> None:
    """A defect fixture's recorded defect has to be a class the severity mapping
    knows, or step 3 of the procedure cannot be carried out against it."""
    classes = severity_by_class(read_rules())
    for name in _named_fixtures(procedure, "defect"):
        fixture = FIXTURES / name
        assert _meta(fixture, "inspection-fixture") == "defect"
        declared = _meta(fixture, "inspection-fixture-class")
        assert declared in classes, (
            f"{name} declares class {declared!r}, which is not in the severity mapping"
        )
        described = _meta(fixture, "inspection-fixture-defect")
        assert described and len(described) > 20, (
            f"{name} does not describe its recorded defect in words"
        )


def test_each_clean_fixture_declares_itself_clean(procedure: str) -> None:
    for name in _named_fixtures(procedure, "clean"):
        fixture = FIXTURES / name
        assert _meta(fixture, "inspection-fixture") == "clean"
        assert _meta(fixture, "inspection-fixture-defect") == "none"


def test_the_procedure_names_its_known_clean_input_set(procedure: str) -> None:
    """Verifies: the procedure names the known-clean input set the
    false-positive rate is measured over."""
    normalized = " ".join(procedure.split())
    assert "input set the false-positive rate is measured over" in normalized
    assert _named_fixtures(procedure, "clean")


# ── the denominator ─────────────────────────────────────────────────────────

def test_the_procedure_names_the_denominator(procedure: str) -> None:
    """Verifies: the procedure names the denominator the rate is computed from.

    A rate measured over defect fixtures too answers a different question than
    the criterion asks, so the procedure has to say which set it divides by.
    """
    normalized = " ".join(procedure.split())
    assert "known-clean fixtures measured" in normalized
    assert "The denominator is the number of known-clean fixtures you measured" in (
        normalized
    )
    assert "not the total number of fixtures" in normalized


def test_the_stated_denominator_equals_the_known_clean_count(procedure: str) -> None:
    """Verifies: the false-positive denominator the procedure states equals the
    number of known-clean fixtures it measured."""
    clean = _named_fixtures(procedure, "clean")
    normalized = " ".join(procedure.split())

    match = re.search(
        r"if you ran the shipped set unchanged", normalized, re.IGNORECASE
    )
    assert match, "the procedure does not state the shipped-set denominator"
    stated = re.search(
        r"\*\*(\d+)\*\* if you ran the shipped set unchanged", normalized
    )
    assert stated, "the shipped-set denominator is not stated as a number"
    assert int(stated.group(1)) == len(clean), (
        f"the procedure states a denominator of {stated.group(1)} but names "
        f"{len(clean)} known-clean fixtures"
    )


def test_the_capture_arithmetic_is_right(procedure: str) -> None:
    """The procedure does the multiplication for the reader, so it has to be
    true. It is an upper bound, not an exact count: a fixture that does not
    scroll at a height produces fewer captures, which the live run measured."""
    total = len(_named_fixtures(procedure, "defect")) + len(
        _named_fixtures(procedure, "clean")
    )
    normalized = " ".join(procedure.split())
    assert f"at most {total} fixtures × 4 = {total * 4} captures" in normalized, (
        f"the procedure's capture arithmetic does not match {total} shipped fixtures"
    )
    assert "page-scrollable: no" in normalized, (
        "the procedure does not tell the reader why a fixture may produce fewer"
    )


# ── the complete procedure ships ────────────────────────────────────────────

def test_the_complete_procedure_is_in_shipped_pack_content(procedure: str) -> None:
    """Verifies: the pack states a procedure by which an adopter measures the
    false-positive rate in their own environment — in shipped content, not only
    in a guide or a ledger."""
    assert MEASUREMENT.is_file()
    assert SHIPPED_ROOT in MEASUREMENT.parents, (
        "the procedure does not live under the pack's runtime export boundary"
    )
    for step in ("Capture every fixture", "Judge each capture", "Compute the rate"):
        assert step in procedure, f"the procedure is missing its {step!r} step"
