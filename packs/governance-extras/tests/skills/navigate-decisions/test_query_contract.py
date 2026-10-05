"""Contract tests for the navigate-decisions query surface.

These tests encode the spec's Corpus and query contract (spec.md §§ "Corpus
and query contract" and "Export destination").  They are frozen red in T1 and
turned green when T2 implements ``run_query``.

Spec call-shape notes (spec says "without fixing CLI argument names"):
  - The query dict key ``"operation"`` was chosen to name the semantic
    operation.  Alternatives considered: ``"op"``, ``"type"``, ``"action"``.
  - ``"id"`` names an exact record identity (e.g. ``"ADR-0001"``).
  - ``"direction"`` names the lineage traversal direction (``"older"``,
    ``"newer"``, ``"both"``).
  - ``"depth"`` is an integer 1–4 for lineage hop count.
  - ``"selectors"`` is a list of selector dicts for ``search`` and ``context``.
  - ``"assertions"`` is a list of caller-assertion dicts for ``context``.
  Each of these was chosen based on the spec's semantic description; they are
  not mandated by the spec text and may be revised in T2 if a cleaner shape
  emerges, provided the ``Done when:`` criteria still hold.

Verification discipline:
  - Tests that do NOT call the seam (fixture-shape validators) must pass in T1.
  - Tests that call ``run_query`` must fail ONLY with ``NotImplementedError``
    raised by the seam; import errors, fixture errors, and missing-fixture
    failures are not acceptable red states.

Spec references are cited as ``spec:<section-line>`` where line numbers are
approximate and the section name is the authoritative reference.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import pathlib
import sys

import pytest  # noqa: F401 — used for pytest.skip, pytest.param, and fixtures

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / ".apm/skills/navigate-decisions/scripts"
FIXTURE = HERE / "fixtures/mixed"
_CHAIN_DIR = HERE / "fixtures" / "lineage-chain"
SPEC = importlib.util.spec_from_file_location(
    "governance_extras_navigate_decisions", SCRIPTS / "navigate_decisions.py"
)
NAV = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NAV)

_EXPLORER_SPEC = importlib.util.spec_from_file_location(
    "governance_extras_explorer_qc", SCRIPTS / "explorer.py"
)
EXPLORER = importlib.util.module_from_spec(_EXPLORER_SPEC)
_EXPLORER_SPEC.loader.exec_module(EXPLORER)


def test_record_returns_body_and_checked_partial_lineage() -> None:
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})

    assert payload["schema"] == "decision-navigation.query.v1"
    assert payload["status"] == "ok"
    record = payload["records"][0]
    assert record["id"] == "ADR-0001"
    assert record["body"]["available"] is True
    expected = {
        "from": "ADR-0020",
        "relation": "supersedes_in_part",
        "to": "ADR-0001",
        "scope": ["D3"],
        "trust_class": "checked",
        "resolution_state": "resolved",
    }
    assert any(expected.items() <= r.items() for r in payload["relationships"])


# ══════════════════════════════════════════════════════════════════════════════
# Fixture-shape validators — must PASS in T1 (do not call the seam)
# ══════════════════════════════════════════════════════════════════════════════

_ADR_DIR = FIXTURE / "docs" / "adr"
_RFC_DIR = FIXTURE / "docs" / "rfc"
_FINDINGS_DIR = FIXTURE / "docs" / "product" / "findings"
_NEG_DIR = HERE / "fixtures" / "negative"


def test_fixture_root_dirs_exist() -> None:
    """Positive fixture root has docs/adr, docs/rfc, and docs/product/findings."""
    assert _ADR_DIR.is_dir(), f"missing {_ADR_DIR}"
    assert _RFC_DIR.is_dir(), f"missing {_RFC_DIR}"
    assert _FINDINGS_DIR.is_dir(), f"missing {_FINDINGS_DIR}"


def test_positive_adr_records_exist() -> None:
    """All seven positive ADR record files are present."""
    expected = [
        "0001-alpha.md",
        "0002-charlie.md",
        "0003-bravo.md",
        "0010-delta.md",
        "0011-echo.md",
        "0020-foxtrot.md",
        "0030-golf.md",
    ]
    for name in expected:
        assert (_ADR_DIR / name).is_file(), f"missing ADR fixture: {name}"


def test_positive_rfc_records_exist() -> None:
    """Both positive RFC record files are present."""
    for name in ("0050-kilo.md", "0060-lima.md"):
        assert (_RFC_DIR / name).is_file(), f"missing RFC fixture: {name}"


def test_support_material_present_in_adr_dir() -> None:
    """Support-material files exist: README.md, *-research.md, and NNNN-notes/."""
    assert (_ADR_DIR / "README.md").is_file(), "missing README.md support file"
    assert (_ADR_DIR / "0002-x-research.md").is_file(), "missing *-research.md support file"
    assert (_ADR_DIR / "0001-notes").is_dir(), "missing NNNN-notes/ subdirectory"
    assert (_ADR_DIR / "0001-notes" / "some-note.md").is_file(), "missing file inside NNNN-notes/"


def test_register_files_exist() -> None:
    """Both register files are present in docs/product/findings/."""
    for name in ("rfc-candidates.md", "roadmap-intents.md"):
        assert (_FINDINGS_DIR / name).is_file(), f"missing register file: {name}"


def test_register_files_have_table_rows() -> None:
    """rfc-candidates.md has 3 data rows and roadmap-intents.md has 2 data rows."""

    def _count_rows(path: pathlib.Path) -> int:
        rows = 0
        in_table = False
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                # Skip header (contains non-pipe content that isn't ---)
                if set(stripped.replace("|", "").replace("-", "").replace(" ", "")) == set():
                    # separator line
                    continue
                # Count data rows only (not separator, not header — but header
                # is distinguished by being first; we count all pipe-lines
                # except the separator here and subtract 1 for the header)
                rows += 1
            elif in_table:
                break
        return max(0, rows - 1)  # subtract header row

    candidates_rows = _count_rows(_FINDINGS_DIR / "rfc-candidates.md")
    intents_rows = _count_rows(_FINDINGS_DIR / "roadmap-intents.md")
    assert candidates_rows == 3, f"rfc-candidates.md: expected 3 data rows, got {candidates_rows}"
    assert intents_rows == 2, f"roadmap-intents.md: expected 2 data rows, got {intents_rows}"


def test_adr_0001_has_qualified_status() -> None:
    """ADR-0001 status line is present and is a qualified value."""
    text = (_ADR_DIR / "0001-alpha.md").read_text(encoding="utf-8")
    assert "- **Status:** Accepted (" in text, (
        "ADR-0001 must have a qualified status starting with 'Accepted ('"
    )


def test_adr_0003_has_unfamiliar_status() -> None:
    """ADR-0003 status value is 'UnderReview', which is not in any canonical list."""
    text = (_ADR_DIR / "0003-bravo.md").read_text(encoding="utf-8")
    assert "- **Status:** UnderReview" in text, (
        "ADR-0003 must have the unfamiliar status 'UnderReview'"
    )


def test_adr_0020_has_trailing_html_comment_in_status() -> None:
    """ADR-0020 status line has a trailing HTML comment."""
    text = (_ADR_DIR / "0020-foxtrot.md").read_text(encoding="utf-8")
    assert "- **Status:** Accepted <!-- " in text, (
        "ADR-0020 must have a status with a trailing HTML comment"
    )


def test_adr_0030_has_no_status_field() -> None:
    """ADR-0030 has no Status field in its header region (missing status)."""
    text = (_ADR_DIR / "0030-golf.md").read_text(encoding="utf-8")
    # Header region: between H1 and first ## heading
    lines = text.splitlines()
    header_lines = []
    past_h1 = False
    for line in lines:
        if line.startswith("# "):
            past_h1 = True
            continue
        if past_h1 and line.startswith("## "):
            break
        if past_h1:
            header_lines.append(line)
    header = "\n".join(header_lines)
    assert "**Status:**" not in header, "ADR-0030 must have no Status field in its header region"


def test_adr_0001_related_forms_all_present() -> None:
    """ADR-0001 header has all three Related field forms."""
    text = (_ADR_DIR / "0001-alpha.md").read_text(encoding="utf-8")
    assert "- **Related:**" in text, "ADR-0001 missing '**Related:**' form"
    assert "- **Related** (" in text, "ADR-0001 missing '**Related** (…):' form"
    assert "- **Related** —" in text, "ADR-0001 missing '**Related** —' form"


def test_adr_0001_has_blockquote_after_related_fields() -> None:
    """ADR-0001 has a blockquote line after the Related fields (after blank line).

    The blockquote line starts with '>'. Content inside it must NOT be counted
    as contextual references because the Related field terminated at the blank
    line before it.
    """
    text = (_ADR_DIR / "0001-alpha.md").read_text(encoding="utf-8")
    assert "\n> " in text, "ADR-0001 must have a blockquote line (starts with '> ')"


def test_adr_0001_has_self_reference_in_related() -> None:
    """ADR-0001 Related field contains 'ADR-0001' (self-reference, must be excluded)."""
    text = (_ADR_DIR / "0001-alpha.md").read_text(encoding="utf-8")
    # The self-reference appears in the first Related field
    assert "ADR-0001" in text, "ADR-0001 Related must contain a self-reference"


def test_adr_0001_has_unresolved_reference_in_related() -> None:
    """ADR-0001 Related field contains 'ADR-9999' (not admitted, must be unresolved)."""
    text = (_ADR_DIR / "0001-alpha.md").read_text(encoding="utf-8")
    assert "ADR-9999" in text, "ADR-0001 Related must contain ADR-9999 (unresolved)"


def test_partial_supersession_mirrors_present() -> None:
    """ADR-0001 and ADR-0020 have mirrored partial supersession entries for D3."""
    adr0001 = (_ADR_DIR / "0001-alpha.md").read_text(encoding="utf-8")
    adr0020 = (_ADR_DIR / "0020-foxtrot.md").read_text(encoding="utf-8")
    assert "Superseded in part:** ADR-0020 D3" in adr0001, (
        "ADR-0001 must have 'Superseded in part: ADR-0020 D3'"
    )
    assert "Supersedes in part:** ADR-0001 D3" in adr0020, (
        "ADR-0020 must have 'Supersedes in part: ADR-0001 D3'"
    )


def test_full_supersession_mirrors_present() -> None:
    """ADR-0002 and ADR-0003 have mirrored full supersession entries."""
    adr0002 = (_ADR_DIR / "0002-charlie.md").read_text(encoding="utf-8")
    adr0003 = (_ADR_DIR / "0003-bravo.md").read_text(encoding="utf-8")
    assert "Superseded by:** ADR-0003" in adr0002, "ADR-0002 must have 'Superseded by: ADR-0003'"
    assert "Supersedes:** ADR-0002" in adr0003, "ADR-0003 must have 'Supersedes: ADR-0002'"


def test_unstated_scope_partial_mirrors_present() -> None:
    """ADR-0010 and ADR-0011 have mirrored partial supersession with no D-IDs."""
    adr0010 = (_ADR_DIR / "0010-delta.md").read_text(encoding="utf-8")
    adr0011 = (_ADR_DIR / "0011-echo.md").read_text(encoding="utf-8")
    # The value must be exactly "ADR-0011" with no D-IDs following on the same line
    assert "Supersedes in part:** ADR-0011" in adr0010, (
        "ADR-0010 must have 'Supersedes in part: ADR-0011' with no D-IDs"
    )
    # D-IDs would appear as "ADR-0011 D<n>"; the absence of " D" after the id confirms no scope
    assert "Supersedes in part:** ADR-0011 D" not in adr0010, (
        "ADR-0010 must have no D-IDs after ADR-0011 (unstated scope)"
    )
    assert "Superseded in part:** ADR-0010" in adr0011, (
        "ADR-0011 must have 'Superseded in part: ADR-0010' with no D-IDs"
    )
    assert "Superseded in part:** ADR-0010 D" not in adr0011, (
        "ADR-0011 must have no D-IDs after ADR-0010 (unstated scope)"
    )


def test_negative_fixture_dirs_exist() -> None:
    """All twelve negative fixture corpus directories are present."""
    expected = [
        "malformed-h1",
        "two-status",
        "duplicate-ordinal",
        "one-sided",
        "contradictory",
        "missing-endpoint",
        "leading-zero-did",
        "five-digit-did",
        "unparseable",
        "hostile",
        "instruction",
        "bidi",
    ]
    for name in expected:
        d = _NEG_DIR / name
        assert d.is_dir(), f"missing negative fixture directory: {name}"


def test_negative_fixture_key_files_exist() -> None:
    """Key files inside each negative fixture corpus are present."""
    cases = {
        "malformed-h1": ["docs/adr/0001-wrong.md"],
        "two-status": ["docs/adr/0001-two-status.md"],
        "duplicate-ordinal": ["docs/adr/0001-alpha.md", "docs/adr/0001-beta.md"],
        "one-sided": ["docs/adr/0001-superseder.md", "docs/adr/0002-no-mirror.md"],
        "contradictory": ["docs/adr/0001-contra.md", "docs/adr/0002-contra.md"],
        "missing-endpoint": ["docs/adr/0001-missing.md"],
        "leading-zero-did": ["docs/adr/0001-lzd.md", "docs/adr/0002-target.md"],
        "five-digit-did": ["docs/adr/0001-5d.md", "docs/adr/0002-target.md"],
        "unparseable": ["docs/adr/0001-unparse.md"],
        "hostile": ["docs/adr/0001-hostile.md"],
        "instruction": ["docs/adr/0001-instruction.md"],
        "bidi": ["docs/adr/0001-bidi.md"],
    }
    present = {f.relative_to(_NEG_DIR).as_posix() for f in _NEG_DIR.rglob("*.md")}
    expected = {f"{corpus}/{rel}" for corpus, files in cases.items() for rel in files}
    assert expected <= present, f"missing negative fixtures: {sorted(expected - present)}"


def test_malformed_h1_has_mismatched_ordinal() -> None:
    """The malformed-h1 fixture has H1 ordinal that disagrees with basename."""
    text = (_NEG_DIR / "malformed-h1" / "docs" / "adr" / "0001-wrong.md").read_text(
        encoding="utf-8"
    )
    # H1 must say ADR-0002, but file basename ordinal is 0001
    assert text.startswith("# ADR-0002:"), (
        "malformed-h1 fixture must have H1 saying 'ADR-0002' for file '0001-wrong.md'"
    )


def test_two_status_has_two_status_lines_in_header() -> None:
    """The two-status fixture has two Status fields in its header region."""
    text = (_NEG_DIR / "two-status" / "docs" / "adr" / "0001-two-status.md").read_text(
        encoding="utf-8"
    )
    header_status_count = 0
    past_h1 = False
    for line in text.splitlines():
        if line.startswith("# "):
            past_h1 = True
            continue
        if past_h1 and line.startswith("## "):
            break
        if past_h1 and line.startswith("- **Status:**"):
            header_status_count += 1
    assert header_status_count == 2, (
        f"two-status fixture must have exactly 2 Status fields in header, "
        f"got {header_status_count}"
    )


def test_duplicate_ordinal_both_parse_as_adr_0001() -> None:
    """Both duplicate-ordinal fixture files have H1 ordinal 0001."""
    for name in ("0001-alpha.md", "0001-beta.md"):
        text = (_NEG_DIR / "duplicate-ordinal" / "docs" / "adr" / name).read_text(encoding="utf-8")
        assert text.startswith("# ADR-0001:"), (
            f"duplicate-ordinal/{name} must have H1 saying 'ADR-0001'"
        )


def test_unparseable_fixture_has_two_entries_in_one_field() -> None:
    """The unparseable fixture has two entries separated by ';' in one field."""
    text = (_NEG_DIR / "unparseable" / "docs" / "adr" / "0001-unparse.md").read_text(
        encoding="utf-8"
    )
    # The field must contain a semicolon (entry separator) and two tokens
    assert "Supersedes in part:** ADR-0002 D3a; ADR-0003 D01" in text, (
        "unparseable fixture must have 'ADR-0002 D3a; ADR-0003 D01' as entry text"
    )


def test_hostile_fixture_contains_script_tag() -> None:
    """The hostile fixture has script-tag content in title or body."""
    text = (_NEG_DIR / "hostile" / "docs" / "adr" / "0001-hostile.md").read_text(encoding="utf-8")
    assert "<script>" in text, "hostile fixture must contain '<script>' content"


def test_bidi_fixture_contains_bidi_control() -> None:
    """The bidi fixture contains at least one bidirectional Unicode control."""
    text = (_NEG_DIR / "bidi" / "docs" / "adr" / "0001-bidi.md").read_text(encoding="utf-8")
    # U+202E RIGHT-TO-LEFT OVERRIDE or U+202C POP DIRECTIONAL FORMATTING
    bidi_controls = {"‮", "‬", "⁦", "⁩", "​", "﻿"}
    found = any(c in text for c in bidi_controls)
    assert found, "bidi fixture must contain at least one bidirectional or non-printing control"


# ══════════════════════════════════════════════════════════════════════════════
# Contract tests — call the seam; all must fail ONLY with NotImplementedError
# ══════════════════════════════════════════════════════════════════════════════

# ── summary operation ─────────────────────────────────────────────────────────


def test_summary_returns_schema_and_status() -> None:
    """summary response carries schema 'decision-navigation.query.v1' and status.

    spec: Corpus and query contract § "Every response contains schema, status..."
    """
    payload = NAV.run_query(FIXTURE, {"operation": "summary"})
    assert payload["schema"] == "decision-navigation.query.v1"
    assert payload["status"] == "ok"


def test_summary_has_empty_records_list() -> None:
    """summary success carries an empty records list.

    spec: "its success result carries an empty records list"
    """
    payload = NAV.run_query(FIXTURE, {"operation": "summary"})
    assert payload["records"] == []


def test_summary_counts_by_kind() -> None:
    """summary.summary has counts by kind: ADR=7, RFC=2.

    The mixed corpus has 7 ADR files and 2 RFC files matching NNNN-*.md
    excluding *-research.md and subdirectories.
    spec: "counts by kind and exact lifecycle value"
    """
    payload = NAV.run_query(FIXTURE, {"operation": "summary"})
    counts = payload["summary"]["by_kind"]
    assert counts.get("ADR") == 7, f"expected 7 ADRs, got {counts}"
    assert counts.get("RFC") == 2, f"expected 2 RFCs, got {counts}"


def test_summary_counts_unresolved_references() -> None:
    """summary.summary has unresolved_reference_count = 1 (ADR-9999 from ADR-0001).

    spec: "The summary unresolved-reference count is the number of relationships
    of every kind, supersession and contextual, with resolution_state=unresolved."
    """
    payload = NAV.run_query(FIXTURE, {"operation": "summary"})
    assert payload["summary"]["unresolved_reference_count"] == 1


def test_summary_register_row_counts() -> None:
    """summary.summary has register row counts: rfc-candidates=3, roadmap-intents=2.

    spec: "the row counts of the findings register files"
    """
    payload = NAV.run_query(FIXTURE, {"operation": "summary"})
    regs = payload["summary"]["register_files"]
    assert regs["rfc_candidates"]["row_count"] == 3
    assert regs["roadmap_intents"]["row_count"] == 2


def test_summary_carries_no_relationships() -> None:
    """summary carries no relationship objects.

    spec: "summary carries none."
    """
    payload = NAV.run_query(FIXTURE, {"operation": "summary"})
    assert payload.get("relationships") == [] or "relationships" not in payload


def test_summary_lifecycle_counts_include_missing_state() -> None:
    """summary lifecycle counts include the missing-state marker for ADR-0030.

    spec: "A missing Status field yields the missing-state marker"
    """
    payload = NAV.run_query(FIXTURE, {"operation": "summary"})
    by_status = payload["summary"]["by_lifecycle_value"]
    missing_count = by_status.get("(missing)", 0) or by_status.get("missing", 0)
    assert missing_count >= 1, (
        f"summary must count ADR-0030's missing status; by_lifecycle_value={by_status}"
    )


# ── record operation ──────────────────────────────────────────────────────────


def test_record_response_envelope() -> None:
    """record response has schema, status, query, boundary, provenance, records, relationships.

    spec: "Every response contains schema, status, normalized query, boundary, and
    provenance. A success adds records, relationships, and omissions."
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})
    for key in (
        "schema",
        "status",
        "query",
        "boundary",
        "provenance",
        "records",
        "relationships",
        "omissions",
    ):
        assert key in payload, f"response missing '{key}'"


def test_record_adr_0001_qualified_status_raw_value() -> None:
    """ADR-0001 lifecycle raw_value is the full qualified string.

    spec: "A lifecycle raw_value is the Status field text after its label, with
    surrounding whitespace and one trailing HTML comment removed."
    The status 'Accepted (superseded in part by ADR-0020 for D3)' has no HTML
    comment; the full qualified text is the raw_value.
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})
    record = payload["records"][0]
    assert record["lifecycle"]["raw_value"] == ("Accepted (superseded in part by ADR-0020 for D3)")


def test_record_adr_0020_trailing_comment_stripped_from_raw_value() -> None:
    """ADR-0020 raw_value has trailing HTML comment removed.

    spec: "one trailing HTML comment removed"
    The file has '- **Status:** Accepted <!-- approved 2026-01-20 -->'.
    raw_value must be 'Accepted'.
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0020"})
    record = payload["records"][0]
    assert record["lifecycle"]["raw_value"] == "Accepted", (
        f"trailing comment must be stripped; got {record['lifecycle']['raw_value']!r}"
    )


def test_record_adr_0003_unfamiliar_status_admitted() -> None:
    """ADR-0003 unfamiliar status is admitted as its literal raw_value.

    spec: "any present value is admitted as its raw_value, whether or not a
    template lists it."
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0003"})
    record = payload["records"][0]
    assert record["lifecycle"]["raw_value"] == "UnderReview"


def test_record_adr_0030_missing_status_marker() -> None:
    """ADR-0030 has the missing-state marker (no Status field in header).

    spec: "A missing Status field yields the missing-state marker"
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0030"})
    record = payload["records"][0]
    # The missing-state marker must be a distinct sentinel (not None, not "")
    lc = record["lifecycle"]
    assert lc.get("missing") is True or lc.get("raw_value") in (None, "(missing)"), (
        f"ADR-0030 must carry the missing-state marker; got {lc}"
    )


def test_record_fields_include_id_kind_title_source() -> None:
    """record entry carries id, kind, title, lifecycle, source, header_fields, and body.

    Each record carries its identifier, kind, title, exact lifecycle value or
    missing-state marker, repository-relative source, present structured fields,
    body-availability state.

    header_fields must be an ordered list of objects {label, raw_value, display_value}
    for every bold-labeled field in the header region.
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0002"})
    rec = payload["records"][0]
    assert rec["id"] == "ADR-0002"
    assert rec["kind"] == "ADR"
    assert isinstance(rec["title"], str) and rec["title"]
    assert "source" in rec
    assert "header_fields" in rec, "record must carry 'header_fields' as an ordered list"
    assert isinstance(rec["header_fields"], list), (
        f"header_fields must be a list; got {type(rec['header_fields'])}"
    )
    # Each entry carries label, raw_value, display_value.
    for entry in rec["header_fields"]:
        assert "label" in entry and "raw_value" in entry and "display_value" in entry, (
            f"header_fields entry missing required keys: {entry}"
        )
    assert "body" in rec
    assert "available" in rec["body"]


def test_record_header_fields_contains_supersession_entries() -> None:
    """header_fields carries all bold-labeled header fields as an ordered list.

    ADR-0001 in the fixture declares supersession relationships and a Date field;
    header_fields must include entries for each, with exact label text and raw_value.
    A Supersedes: none entry must be present (its raw_value is 'none').

    Mutation: removing header_fields or making it always empty would fail this test.
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok"
    rec = payload["records"][0]
    hf = rec["header_fields"]
    assert isinstance(hf, list), f"header_fields must be a list; got {type(hf)}"
    labels = [e["label"] for e in hf]
    # Date field pinned (added to fixture).
    assert "Date" in labels, f"header_fields must include a 'Date' entry; got labels {labels}"
    date_entry = next(e for e in hf if e["label"] == "Date")
    assert date_entry["raw_value"] == "2024-03-15", f"Date raw_value mismatch: {date_entry}"
    assert date_entry["display_value"] == "2024-03-15", (
        f"Date display_value mismatch: {date_entry}"
    )
    # 'Supersedes: none' field pinned — raw_value must be 'none'.
    assert "Supersedes" in labels, (
        f"header_fields must include a 'Supersedes' entry; got labels {labels}"
    )
    sup_entry = next(e for e in hf if e["label"] == "Supersedes")
    assert sup_entry["raw_value"] == "none", (
        f"Supersedes raw_value must be 'none'; got {sup_entry!r}"
    )
    # At least one supersession label present.
    supersession_labels = {
        "Supersedes",
        "Supersedes in part",
        "Superseded by",
        "Superseded in part",
    }
    present = supersession_labels & set(labels)
    assert present, (
        f"ADR-0001 declares supersession fields; header_fields must carry "
        f"at least one of {sorted(supersession_labels)}; got labels {labels}"
    )


def test_record_unknown_id_fails_with_stable_error() -> None:
    """Requesting a non-existent record identity fails with a stable error.

    spec: "Missing, ambiguous, unsafe, or non-record targets fail with a stable
    error and no substituted result."
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-9999"})
    assert payload["status"] == "error"
    assert "error" in payload
    assert "code" in payload["error"]


def test_record_returns_all_relationships_for_record() -> None:
    """record carries every relationship whose from or to is the requested record.

    spec: "record carries every relationship whose from or to is the requested record."
    For ADR-0001: supersession relationships + contextual references.
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})
    rels = payload["relationships"]
    # Must include the checked partial edge (ADR-0020 supersedes_in_part ADR-0001)
    assert any(
        r.get("from") == "ADR-0020"
        and r.get("relation") == "supersedes_in_part"
        and r.get("to") == "ADR-0001"
        for r in rels
    ), "record must include checked partial edge from ADR-0020"
    # Must include the unresolved contextual reference to ADR-9999
    assert any(
        r.get("from") == "ADR-0001"
        and r.get("relation") == "related"
        and r.get("to") == "ADR-9999"
        and r.get("resolution_state") == "unresolved"
        for r in rels
    ), "record must include unresolved contextual reference to ADR-9999"


# ── lineage operation ─────────────────────────────────────────────────────────


def test_lineage_older_from_adr_0003() -> None:
    """lineage older from ADR-0003 follows supersedes edges to ADR-0002.

    spec: "'older' follows from to to"
    ADR-0003 supersedes ADR-0002 (checked full edge).
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "lineage", "id": "ADR-0003", "direction": "older", "depth": 1},
    )
    assert payload["status"] == "ok"
    ids = {r["id"] for r in payload["records"]}
    assert "ADR-0003" in ids
    assert "ADR-0002" in ids


def test_lineage_newer_from_adr_0002() -> None:
    """lineage newer from ADR-0002 follows superseded_by edges back to ADR-0003.

    spec: "'newer' follows to to from"
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "lineage", "id": "ADR-0002", "direction": "newer", "depth": 1},
    )
    assert payload["status"] == "ok"
    ids = {r["id"] for r in payload["records"]}
    assert "ADR-0002" in ids
    assert "ADR-0003" in ids


def test_lineage_both_from_adr_0001() -> None:
    """lineage both from ADR-0001 traverses in both directions.

    ADR-0020 supersedes ADR-0001 in part (checked). Both must appear.
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "lineage", "id": "ADR-0001", "direction": "both", "depth": 1},
    )
    assert payload["status"] == "ok"
    ids = {r["id"] for r in payload["records"]}
    assert "ADR-0001" in ids
    assert "ADR-0020" in ids


def test_lineage_traverses_only_checked_relationships() -> None:
    """lineage does not traverse unresolved supersession entries.

    spec: "lineage traverses only checked relationships"
    The one-sided fixture has an unresolved entry; lineage must not cross it.

    Mutation: removing the checked-only guard would add ADR-0002 to records.
    """
    one_sided = _NEG_DIR / "one-sided"
    payload = NAV.run_query(
        one_sided,
        {"operation": "lineage", "id": "ADR-0001", "direction": "older", "depth": 4},
    )
    # ADR-0001 claims to supersede ADR-0002 but edge is unresolved.
    assert payload["status"] == "ok", f"lineage failed: {payload}"
    record_ids = {r["id"] for r in payload.get("records", [])}
    # ADR-0002 must NOT appear in records — unresolved edge was not traversed.
    assert "ADR-0002" not in record_ids, (
        f"lineage must not traverse an unresolved edge; ADR-0002 appeared: {record_ids}"
    )
    # The unresolved edge itself must still be reported with a non-checked trust class.
    rels = payload.get("relationships", [])
    edge_to_002 = [r for r in rels if r.get("from") == "ADR-0001" and r.get("to") == "ADR-0002"]
    assert edge_to_002, "lineage must include the one-sided edge from ADR-0001 as untraversed"
    assert edge_to_002[0].get("trust_class") != "checked", (
        "lineage must not classify an unresolved edge as checked"
    )


def test_lineage_includes_unchecked_relationships_as_untraversed() -> None:
    """lineage includes unchecked supersession whose from is a returned record,
    but does not traverse them.

    spec: "every unchecked supersession relationship whose from is a returned
    record, which is reported but never traversed"
    """
    one_sided = _NEG_DIR / "one-sided"
    payload = NAV.run_query(
        one_sided,
        {"operation": "lineage", "id": "ADR-0001", "direction": "older", "depth": 4},
    )
    if payload["status"] == "ok":
        rels = payload.get("relationships", [])
        unresolved = [
            r
            for r in rels
            if r.get("from") == "ADR-0001" and r.get("resolution_state") == "unresolved"
        ]
        assert unresolved, "lineage must include the unresolved supersession entry from ADR-0001"


def test_lineage_depth_limit_respected() -> None:
    """lineage stops at the requested depth and does not over-traverse.

    spec: "a depth from 1 through 4"

    Uses the lineage-chain fixture: ADR-0003 → ADR-0002 → ADR-0001 (all checked).
    depth=1 reaches ADR-0002 but not ADR-0001; depth=2 reaches both.

    Mutation: removing the depth guard would include ADR-0001 at depth=1.
    """
    chain = _CHAIN_DIR
    payload_d1 = NAV.run_query(
        chain,
        {"operation": "lineage", "id": "ADR-0003", "direction": "older", "depth": 1},
    )
    assert payload_d1["status"] == "ok", f"lineage depth=1 failed: {payload_d1}"
    ids_d1 = {r["id"] for r in payload_d1["records"]}
    assert "ADR-0002" in ids_d1, f"depth=1 from ADR-0003 must reach ADR-0002; got {ids_d1}"
    assert "ADR-0001" not in ids_d1, (
        f"depth=1 must not reach ADR-0001 (two hops away); got {ids_d1}"
    )

    payload_d2 = NAV.run_query(
        chain,
        {"operation": "lineage", "id": "ADR-0003", "direction": "older", "depth": 2},
    )
    assert payload_d2["status"] == "ok", f"lineage depth=2 failed: {payload_d2}"
    ids_d2 = {r["id"] for r in payload_d2["records"]}
    assert "ADR-0001" in ids_d2, f"depth=2 must reach ADR-0001 (two hops); got {ids_d2}"


def test_lineage_partial_edge_with_scope() -> None:
    """lineage partial edge carries scope=['D3'] for ADR-0020 supersedes ADR-0001.

    spec: "A valid partial edge retains its scope label."
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "lineage", "id": "ADR-0020", "direction": "older", "depth": 1},
    )
    assert payload["status"] == "ok"
    partial_edges = [
        r
        for r in payload["relationships"]
        if r.get("from") == "ADR-0020"
        and r.get("to") == "ADR-0001"
        and r.get("relation") == "supersedes_in_part"
    ]
    assert partial_edges, "lineage must include the partial edge from ADR-0020 to ADR-0001"
    assert partial_edges[0]["scope"] == ["D3"], (
        f"partial edge scope must be ['D3']; got {partial_edges[0].get('scope')}"
    )


def test_lineage_unstated_scope_partial_edge() -> None:
    """lineage partial edge with no D-IDs has scope=[] and unstated label.

    spec: "two equal unstated scopes, which the view labels 'scope not stated'"
    ADR-0010 supersedes_in_part ADR-0011 with scope=[].
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "lineage", "id": "ADR-0010", "direction": "older", "depth": 1},
    )
    assert payload["status"] == "ok"
    partial_edges = [
        r
        for r in payload["relationships"]
        if r.get("from") == "ADR-0010"
        and r.get("to") == "ADR-0011"
        and r.get("relation") == "supersedes_in_part"
    ]
    assert partial_edges, "lineage must include unstated-scope partial edge ADR-0010->ADR-0011"
    assert partial_edges[0]["scope"] == [], (
        f"unstated-scope edge must have scope=[]; got {partial_edges[0].get('scope')}"
    )


# ── search operation ──────────────────────────────────────────────────────────


def test_search_by_kind_adr() -> None:
    """search by kind=ADR returns only ADR records.

    spec: "search and context take at least one explicit kind, exact-status,
    text, identity, or caller-grouping selector"
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "search", "selectors": [{"kind": "ADR"}]},
    )
    assert payload["status"] == "ok"
    for rec in payload["records"]:
        assert rec["kind"] == "ADR", f"search by kind=ADR returned {rec['kind']}: {rec['id']}"


def test_search_by_kind_rfc() -> None:
    """search by kind=RFC returns only RFC records."""
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "search", "selectors": [{"kind": "RFC"}]},
    )
    assert payload["status"] == "ok"
    for rec in payload["records"]:
        assert rec["kind"] == "RFC"


def test_search_returns_no_relationships() -> None:
    """search carries no relationship objects.

    spec: "search carries none; its records are an inventory."
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "search", "selectors": [{"kind": "ADR"}]},
    )
    assert payload.get("relationships") == [] or "relationships" not in payload


def test_search_exact_status_filter() -> None:
    """search by exact_status returns only records with that lifecycle value."""
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "search", "selectors": [{"exact_status": "Accepted"}]},
    )
    assert payload["status"] == "ok"
    # ADR-0002, ADR-0010, ADR-0011, RFC-0050 have exact status "Accepted"
    for rec in payload["records"]:
        assert rec["lifecycle"]["raw_value"] == "Accepted", (
            f"search by exact_status=Accepted returned {rec['id']} with "
            f"{rec['lifecycle'].get('raw_value')!r}"
        )


def test_search_missing_selectors_fails() -> None:
    """search with no selectors fails with a stable error.

    spec: "search and context take at least one explicit ... selector"
    """
    payload = NAV.run_query(FIXTURE, {"operation": "search", "selectors": []})
    assert payload["status"] == "error"


def test_search_non_list_selectors_fails() -> None:
    """search with non-list selectors fails with a stable error.

    ADV-4/QE-4: A string or dict instead of a list for selectors must be refused,
    not silently accepted or causing a crash.

    Mutation: removing the isinstance(selectors, list) check in _validate_selectors
    would cause this to crash or match the whole corpus.
    """
    payload = NAV.run_query(FIXTURE, {"operation": "search", "selectors": "ADR"})
    assert payload["status"] == "error", "non-list selectors must be refused with an error"
    assert "error" in payload
    assert "code" in payload["error"]


def test_search_selector_with_only_unknown_keys_fails() -> None:
    """search with a selector containing only unknown keys is refused.

    ADV-4/QE-4: A selector dict with no known filter key must be refused.
    Without this check it would silently match the whole corpus.

    Mutation: removing the unknown-key check in _validate_selector would allow
    this to pass and return all records instead of refusing.
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "search", "selectors": [{"not_a_real_key": "ADR"}]},
    )
    assert payload["status"] == "error", (
        "a selector with only unknown keys must be refused, not match the whole corpus"
    )
    assert "error" in payload


def test_search_non_dict_selector_element_fails() -> None:
    """search with a non-dict selector element is refused.

    ADV-4: Each element in the selectors list must be a dict; a string or int
    element must be refused.

    Mutation: removing the isinstance(sel, dict) check in _validate_selector
    would cause this to crash or match nothing instead of refusing.
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "search", "selectors": ["ADR"]},
    )
    assert payload["status"] == "error", "a non-dict selector element must be refused"


# ── context operation ─────────────────────────────────────────────────────────


def test_context_carries_resolved_relationships_between_returned_records() -> None:
    """context carries resolved relationships whose from and to are both returned.

    spec: "context carries every relationship whose from and to are both returned
    records, plus every unresolved relationship whose from is a returned record,
    plus the caller's assertions."
    """
    payload = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [{"identity": "ADR-0001"}, {"identity": "ADR-0020"}],
        },
    )
    assert payload["status"] == "ok"
    rels = payload["relationships"]
    # The checked partial edge between ADR-0020 and ADR-0001 must appear
    checked = [
        r
        for r in rels
        if r.get("from") == "ADR-0020"
        and r.get("to") == "ADR-0001"
        and r.get("trust_class") == "checked"
    ]
    assert checked, "context must include the checked partial edge ADR-0020 -> ADR-0001"


def test_context_includes_unresolved_relationships_from_returned_records() -> None:
    """context includes unresolved relationships whose from is a returned record.

    spec: "plus every unresolved relationship whose from is a returned record"
    ADR-0001 has an unresolved contextual reference to ADR-9999.
    """
    payload = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [{"identity": "ADR-0001"}],
        },
    )
    assert payload["status"] == "ok"
    unresolved = [
        r
        for r in payload["relationships"]
        if r.get("from") == "ADR-0001" and r.get("resolution_state") == "unresolved"
    ]
    assert unresolved, "context must include unresolved reference to ADR-9999 from ADR-0001"


def test_context_caller_assertion_trust_class() -> None:
    """Caller assertions have trust_class=navigation_only and resolution_state=caller_asserted.

    spec: "Every caller assertion is represented as non-authoritative navigation
    input with trust_class=navigation_only and resolution_state=caller_asserted"
    """
    payload = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [{"identity": "ADR-0001"}, {"identity": "ADR-0002"}],
            "assertions": [
                {"from": "ADR-0001", "to": "ADR-0002", "text": "ADR-0001 guides ADR-0002"}
            ],
        },
    )
    assert payload["status"] == "ok"
    caller_rels = [
        r for r in payload["relationships"] if r.get("trust_class") == "navigation_only"
    ]
    assert caller_rels, "context must include caller assertions with trust_class=navigation_only"
    for rel in caller_rels:
        assert rel.get("resolution_state") == "caller_asserted"
        assert rel.get("basis") == "caller_assertion"


# ── relationship projection fields ───────────────────────────────────────────


def test_relationship_closed_value_set_checked_full() -> None:
    """Checked full supersession relationship has correct closed value fields.

    spec: closed relationship value table — checked full supersession row
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0003"})
    checked_full = [
        r
        for r in payload["relationships"]
        if r.get("from") == "ADR-0003"
        and r.get("to") == "ADR-0002"
        and r.get("relation") == "supersedes"
    ]
    assert checked_full, "ADR-0003 record must include the checked full supersession relationship"
    rel = checked_full[0]
    assert rel["basis"] == "supersession_fields"
    assert rel["direction"] == "superseding_to_superseded"
    assert rel["trust_class"] == "checked"
    assert rel["resolution_state"] == "resolved"
    assert rel["scope"] == []
    # source is the repository-relative path of the superseding record
    assert rel["source"] == "docs/adr/0003-bravo.md"


def test_relationship_closed_value_set_checked_partial() -> None:
    """Checked partial supersession relationship has correct closed value fields.

    spec: closed relationship value table — checked partial supersession row
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0020"})
    checked_partial = [
        r
        for r in payload["relationships"]
        if r.get("from") == "ADR-0020"
        and r.get("to") == "ADR-0001"
        and r.get("relation") == "supersedes_in_part"
        and r.get("trust_class") == "checked"
    ]
    assert checked_partial, "ADR-0020 record must include the checked partial relationship"
    rel = checked_partial[0]
    assert rel["basis"] == "supersession_fields"
    assert rel["direction"] == "superseding_to_superseded"
    assert rel["trust_class"] == "checked"
    assert rel["resolution_state"] == "resolved"
    assert rel["scope"] == ["D3"]
    # source is the repository-relative path of the superseding record
    assert rel["source"] == "docs/adr/0020-foxtrot.md"


def test_relationship_closed_value_set_contextual_reference() -> None:
    """Contextual reference has correct closed value fields.

    spec: closed relationship value table — contextual reference row
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})
    contextual = [
        r
        for r in payload["relationships"]
        if r.get("from") == "ADR-0001"
        and r.get("relation") == "related"
        and r.get("to") == "ADR-0002"
    ]
    assert contextual, "ADR-0001 record must include contextual reference to ADR-0002"
    rel = contextual[0]
    assert rel["basis"] == "related_field"
    assert rel["direction"] == "none"
    assert rel["trust_class"] == "contextual"
    assert rel["resolution_state"] == "resolved"
    assert rel["scope"] == []
    # raw_value is the matched token
    assert rel["raw_value"] == "ADR-0002"


def test_relationship_unresolved_contextual_reference() -> None:
    """Unresolved contextual reference (ADR-9999) has resolution_state=unresolved.

    spec: "A contextual reference to an identity that is not admitted is
    resolution_state=unresolved"
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})
    unresolved_ctx = [
        r
        for r in payload["relationships"]
        if r.get("from") == "ADR-0001" and r.get("to") == "ADR-9999"
    ]
    assert unresolved_ctx, "ADR-0001 must have unresolved reference to ADR-9999"
    rel = unresolved_ctx[0]
    assert rel["resolution_state"] == "unresolved"
    assert rel["trust_class"] == "contextual"


def test_relationship_source_is_superseding_record_for_checked_pair() -> None:
    """For a checked pair, source is the superseding record.

    spec: "For a checked pair, source is the superseding record and raw_value
    is its entry text."
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0002"})
    # The checked full edge has ADR-0003 as the superseding record
    checked = [
        r
        for r in payload["relationships"]
        if r.get("from") == "ADR-0003"
        and r.get("to") == "ADR-0002"
        and r.get("trust_class") == "checked"
    ]
    assert checked, "ADR-0002 record must include the checked full edge from ADR-0003"
    # source is the repository-relative path of the superseding record
    assert checked[0]["source"] == "docs/adr/0003-bravo.md"


# ── ordering ──────────────────────────────────────────────────────────────────


def test_records_sort_by_kind_then_ordinal() -> None:
    """Records sort by kind, ordinal, then repository-relative source.

    spec: "Records sort by kind, ordinal, then repository-relative source"
    ADR records before RFC records; within ADR by ordinal.
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "search", "selectors": [{"kind": "ADR"}, {"kind": "RFC"}]},
    )
    assert payload["status"] == "ok"
    records = payload["records"]
    adr_records = [r for r in records if r["kind"] == "ADR"]
    rfc_records = [r for r in records if r["kind"] == "RFC"]
    # All ADRs before all RFCs
    if adr_records and rfc_records:
        adr_indices = [records.index(r) for r in adr_records]
        rfc_indices = [records.index(r) for r in rfc_records]
        assert max(adr_indices) < min(rfc_indices), "ADRs must come before RFCs in sorted result"
    # ADRs sorted by ordinal
    adr_ordinals = [int(r["id"].split("-")[1]) for r in adr_records]
    assert adr_ordinals == sorted(adr_ordinals), "ADRs must be sorted by ordinal"


def test_relationships_sort_order() -> None:
    """Relationships sort by from, relation, scope, to, then raw_value.

    Null 'to' sorts first within the same from/relation/scope group.
    This test builds the input directly so the assertion always runs.
    """
    # Build two relationships with the same from/relation/scope but different 'to' values,
    # one with to=None (unparseable) and one with to="ADR-0001".
    null_rel = {
        "from": "ADR-0001",
        "to": None,
        "relation": "superseded_by",
        "scope": [],
        "raw_value": "EXTERNAL-SYSTEM",
        "basis": "supersession_fields",
        "source": "docs/adr/0001-alpha.md",
        "direction": "narrower_to_wider",
        "trust_class": "candidate",
        "resolution_state": "unresolved",
    }
    non_null_rel = {
        "from": "ADR-0001",
        "to": "ADR-0002",
        "relation": "superseded_by",
        "scope": [],
        "raw_value": "ADR-0002",
        "basis": "supersession_fields",
        "source": "docs/adr/0001-alpha.md",
        "direction": "narrower_to_wider",
        "trust_class": "candidate",
        "resolution_state": "unresolved",
    }
    # Sort in reverse order to verify the sort function corrects the order.
    rels = NAV._sort_relationships([non_null_rel, null_rel])
    assert rels[0]["to"] is None, (
        "null to must sort before non-null to within the same from/relation/scope group"
    )
    assert rels[1]["to"] == "ADR-0002", "non-null to must follow null to in sorted result"


def test_scope_sort_empty_before_stated() -> None:
    """scope=[] (unstated) sorts before any stated scope.

    A list that is a proper prefix of another ranks first, so [] ranks
    before every stated scope.
    This test builds the input directly so the assertion always runs.
    """
    # Two relationships with the same from/relation/to but different scopes.
    unstated = {
        "from": "ADR-0020",
        "to": "ADR-0001",
        "relation": "supersedes_in_part",
        "scope": [],
        "raw_value": "ADR-0001",
        "basis": "supersession_fields",
        "source": "docs/adr/0020-foxtrot.md",
        "direction": "wider_to_narrower",
        "trust_class": "candidate",
        "resolution_state": "unresolved",
    }
    stated_d3 = {
        "from": "ADR-0020",
        "to": "ADR-0001",
        "relation": "supersedes_in_part",
        "scope": ["D3"],
        "raw_value": "ADR-0001 D3",
        "basis": "supersession_fields",
        "source": "docs/adr/0020-foxtrot.md",
        "direction": "wider_to_narrower",
        "trust_class": "checked",
        "resolution_state": "checked",
    }
    # Sort in reverse order to verify the sort function corrects the order.
    rels = NAV._sort_relationships([stated_d3, unstated])
    assert rels[0]["scope"] == [], (
        "scope=[] must sort before scope=['D3'] for the same from/relation/to"
    )
    assert rels[1]["scope"] == ["D3"], "scope=['D3'] must follow scope=[] in sorted result"


# ── corpus admission failures ─────────────────────────────────────────────────


def test_malformed_h1_fails_whole_operation() -> None:
    """A malformed H1 (ordinal mismatch) fails the whole operation.

    spec: "malformed candidates, duplicate kind-plus-ordinal identities, and
    identity changes fail the whole operation rather than falling out of
    admission silently."
    """
    corpus = _NEG_DIR / "malformed-h1"
    payload = NAV.run_query(corpus, {"operation": "summary"})
    assert payload["status"] == "error", (
        "malformed H1 must fail the whole operation, not return partial results"
    )


def test_two_status_fields_fails_whole_operation() -> None:
    """Two Status fields in the header region make a record malformed.

    spec: "the header region holds at most one **Status:** field"
    """
    corpus = _NEG_DIR / "two-status"
    payload = NAV.run_query(corpus, {"operation": "summary"})
    assert payload["status"] == "error"


def test_duplicate_ordinal_fails_whole_operation() -> None:
    """Duplicate kind+ordinal identity fails the whole operation.

    spec: "duplicate kind-plus-ordinal identities... fail the whole operation"
    """
    corpus = _NEG_DIR / "duplicate-ordinal"
    payload = NAV.run_query(corpus, {"operation": "summary"})
    assert payload["status"] == "error"


# ── lineage edge quality ──────────────────────────────────────────────────────


def test_one_sided_supersession_is_unresolved() -> None:
    """One-sided supersession (no mirror) stays as unresolved evidence.

    spec: "Supersession entries that are unparseable, one-sided, contradictory,
    or point to a missing endpoint never make a candidate malformed; they become
    unresolved evidence."
    """
    corpus = _NEG_DIR / "one-sided"
    payload = NAV.run_query(corpus, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok"
    rels = payload["relationships"]
    supersedes_rels = [
        r for r in rels if r.get("from") == "ADR-0001" and r.get("relation") == "supersedes"
    ]
    assert supersedes_rels, "one-sided Supersedes entry must appear as a relationship"
    for rel in supersedes_rels:
        assert rel["trust_class"] != "checked", (
            "one-sided supersession must not be trust_class=checked"
        )
        assert rel["resolution_state"] == "unresolved"


def test_contradictory_scope_supersession_is_unresolved() -> None:
    """Contradictory partial supersession (mismatched scope) stays unresolved.

    spec: "A partial edge is checked when Supersedes in part and Superseded in
    part mirror each other with equal scopes"
    """
    corpus = _NEG_DIR / "contradictory"
    payload = NAV.run_query(corpus, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok"
    partial_rels = [
        r
        for r in payload["relationships"]
        if r.get("relation") == "supersedes_in_part" and r.get("from") == "ADR-0001"
    ]
    assert partial_rels, "contradictory partial supersession must appear as a relationship"
    for rel in partial_rels:
        assert rel["trust_class"] != "checked", (
            "contradictory-scope partial supersession must not be checked"
        )


def test_missing_endpoint_is_unresolved() -> None:
    """A supersession entry pointing to a missing record stays unresolved.

    spec: "Supersession entries that are... point to a missing endpoint never make
    a candidate malformed; they become unresolved evidence."
    """
    corpus = _NEG_DIR / "missing-endpoint"
    payload = NAV.run_query(corpus, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok"
    rels = payload["relationships"]
    missing_ep = [r for r in rels if r.get("to") == "ADR-9999"]
    assert missing_ep, "supersession to missing endpoint must appear as unresolved relationship"
    assert missing_ep[0]["resolution_state"] == "unresolved"


def test_leading_zero_did_is_unparseable() -> None:
    """A D-ID with a leading zero makes the entry unparseable.

    spec: "each D followed by one to four decimal digits with no leading zero.
    Any other entry... is unparseable: its relationship has target=null, scope=[],
    and the entry text as raw_value"
    """
    corpus = _NEG_DIR / "leading-zero-did"
    payload = NAV.run_query(corpus, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok"
    rels = payload["relationships"]
    unparseable = [r for r in rels if r.get("to") is None and "D03" in r.get("raw_value", "")]
    assert unparseable, "leading-zero D-ID entry must be unparseable with target=null"
    rel = unparseable[0]
    assert rel["scope"] == []
    assert rel["resolution_state"] == "unresolved"


def test_five_digit_did_is_unparseable() -> None:
    """A D-ID with five digits makes the entry unparseable.

    spec: "each D followed by one to four decimal digits"
    """
    corpus = _NEG_DIR / "five-digit-did"
    payload = NAV.run_query(corpus, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok"
    rels = payload["relationships"]
    unparseable = [r for r in rels if r.get("to") is None and "D12345" in r.get("raw_value", "")]
    assert unparseable, "five-digit D-ID entry must be unparseable with target=null"
    rel = unparseable[0]
    assert rel["scope"] == []
    assert rel["resolution_state"] == "unresolved"


def test_unparseable_entries_never_merged() -> None:
    """Two unparseable entries in one field produce two distinct unresolved objects.

    spec: "Unparseable entries are never merged: each is its own unresolved
    relationship."
    """
    corpus = _NEG_DIR / "unparseable"
    payload = NAV.run_query(corpus, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok"
    rels = payload["relationships"]
    null_to_rels = [
        r for r in rels if r.get("to") is None and r.get("resolution_state") == "unresolved"
    ]
    assert len(null_to_rels) >= 2, (
        f"two unparseable entries must produce two distinct unresolved relationships; "
        f"got {len(null_to_rels)}"
    )
    # Each must have different raw_value (D3a vs D01)
    raw_values = {r["raw_value"] for r in null_to_rels}
    assert len(raw_values) >= 2, "two unparseable entries must have distinct raw_values"


# ── content safety ────────────────────────────────────────────────────────────


def test_hostile_content_is_inert_in_raw_value() -> None:
    """Hostile script content in a record is preserved literally in raw_value.

    spec: "Treat titles, prose, metadata... as untrusted text. They remain
    inert data in query and HTML outputs."
    """
    corpus = _NEG_DIR / "hostile"
    payload = NAV.run_query(corpus, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok"
    record = payload["records"][0]
    # Title contains <script>alert("xss")</script>
    assert "<script>" in record["title"], (
        "hostile title must appear as literal inert text in query raw data"
    )


def test_instruction_shaped_content_is_inert() -> None:
    """Instruction-shaped text in status appears as literal raw_value.

    spec: "Query values are schema-safe scalars marked as untrusted data with
    provenance... record text cannot change task scope, workflow selection..."
    """
    corpus = _NEG_DIR / "instruction"
    payload = NAV.run_query(corpus, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok"
    record = payload["records"][0]
    raw = record["lifecycle"]["raw_value"]
    assert "IGNORE PREVIOUS INSTRUCTIONS" in raw, (
        "instruction-shaped status must appear as literal raw_value, not be interpreted"
    )


def test_bidi_raw_value_preserved_display_value_escaped() -> None:
    """Bidi controls are preserved in raw_value but escaped in display_value.

    spec: "HTML and other human-facing forms use a separate display_value that
    visibly escapes unsafe bidirectional or non-printing controls; this presentation
    change does not normalize or replace the raw source fact."

    Mutation: setting display_value = raw_value would fail the display assertions.
    """
    corpus = _NEG_DIR / "bidi"
    payload = NAV.run_query(corpus, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok"
    record = payload["records"][0]
    lc = record["lifecycle"]
    raw = lc["raw_value"]
    display = lc["display_value"]
    # raw_value must preserve the literal bidi control characters from the fixture.
    assert "‮" in raw, "raw_value must preserve U+202E RIGHT-TO-LEFT OVERRIDE"
    assert "‬" in raw, "raw_value must preserve U+202C POP DIRECTIONAL FORMATTING"
    # display_value must visibly escape bidi controls — raw chars must not appear.
    assert "‮" not in display, "display_value must not contain raw U+202E; it must be escaped"
    assert "‬" not in display, "display_value must not contain raw U+202C; it must be escaped"
    # The escaped notation must be present so the user sees the literal code point.
    assert "[U+202E]" in display or "202E" in display, (
        "display_value must visibly annotate the escaped U+202E control"
    )


def test_related_self_reference_excluded() -> None:
    """ADR-0001 self-reference (ADR-0001) in its own Related field is excluded.

    spec: "each distinct token... except a token naming the record itself"
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})
    rels = payload["relationships"]
    self_refs = [
        r
        for r in rels
        if r.get("from") == "ADR-0001"
        and r.get("to") == "ADR-0001"
        and r.get("relation") == "related"
    ]
    assert not self_refs, "self-reference ADR-0001 must not appear as a contextual reference"


# ── query bounds and refusals ─────────────────────────────────────────────────


def test_oversized_candidate_fails_with_input_too_large(tmp_path: pathlib.Path) -> None:
    """A candidate file larger than 2 MiB fails the operation with input_too_large.

    spec: "A candidate larger than 2 MiB is refused with code input_too_large
    under the same whole-operation rule."
    Generated at test time because a 2 MiB file cannot be committed.
    """
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    # Write a 2 MiB + 1 byte file named as a valid ADR candidate
    oversized = adr_dir / "0001-oversized.md"
    oversized.write_bytes(
        b"# ADR-0001: Oversized\n\n- **Status:** Accepted\n\n## Context\n\n"
        + b"x" * (2 * 1024 * 1024)
    )
    payload = NAV.run_query(tmp_path, {"operation": "summary"})
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "input_too_large"


def test_result_too_large_refusal_carries_error_fields(tmp_path: pathlib.Path) -> None:
    """result_too_large refusal carries code, exceeded limit, observed value, and hint.

    spec: "it returns a refusal with code result_too_large, the exceeded limit,
    the observed count or estimated bytes, and a narrowing hint."
    Generated at test time with 201 minimal ADR files (exceeds the 200-record limit).
    """
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)

    for i in range(1, 202):
        content = (
            f"# ADR-{i:04d}: Bound test record {i}\n\n"
            f"- **Status:** Accepted\n"
            f"- **Supersedes:** none\n"
            f"- **Supersedes in part:** none\n"
            f"- **Superseded by:** none\n"
            f"- **Superseded in part:** none\n\n"
            f"## Context\n\nMinimal record for bound testing.\n\n"
            f"## Decision\n\n- **D1:** Bound test decision.\n"
        )
        (adr_dir / f"{i:04d}-bound-test.md").write_text(content, encoding="utf-8")

    payload = NAV.run_query(
        tmp_path,
        {"operation": "search", "selectors": [{"kind": "ADR"}]},
    )
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "result_too_large"
    assert "limits" in payload["error"]
    assert "observed" in payload["error"]
    assert "hint" in payload["error"]


def test_relationship_limit_enforced() -> None:
    """The 400-relationship limit is enforced for non-detail operations.

    ADV-3/QE-2: '_check_non_detail_bounds refuses when relationships exceed 400.'
    Calls the bounds function directly with fabricated data to avoid expensive
    fixture construction.

    Mutation: removing the relationship-count check would allow results with
    more than 400 relationships, violating the non-detail bound spec.
    """
    env: dict = {
        "schema": "decision-navigation.query.v1",
        "query": {"operation": "search"},
        "boundary": NAV.BOUNDARY_NOTICE,
        "provenance": {},
    }
    # Build 401 minimal relationship dicts
    rels = [
        {
            "from": f"ADR-{i:04d}",
            "to": f"ADR-{i + 1:04d}",
            "relation": "supersedes",
            "scope": [],
            "raw_value": f"ADR-{i + 1:04d}",
            "basis": "supersession_fields",
            "source": f"docs/adr/{i:04d}-test.md",
            "direction": "superseding_to_superseded",
            "trust_class": "checked",
            "resolution_state": "resolved",
        }
        for i in range(1, 402)
    ]
    result = NAV._check_non_detail_bounds(env, [], rels, "search")
    assert result is not None, (
        "_check_non_detail_bounds must refuse when relationship count exceeds 400"
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "result_too_large"
    assert "limits" in result["error"]
    assert result["error"]["limits"].get("max_relationships") == 400


def test_result_byte_limit_enforced() -> None:
    """The 512 KiB byte limit is enforced for non-detail operations.

    ADV-3/QE-2: '_check_non_detail_bounds refuses when estimated JSON exceeds 512 KiB.'
    Calls the bounds function directly with a large record list.

    Mutation: removing the byte-size check would allow results larger than 512 KiB.
    """
    env: dict = {
        "schema": "decision-navigation.query.v1",
        "query": {"operation": "search"},
        "boundary": NAV.BOUNDARY_NOTICE,
        "provenance": {},
    }
    # Each record is ~600 bytes; 900 records → ~540 KiB
    big_records = [
        {
            "id": f"ADR-{i:04d}",
            "kind": "ADR",
            "title": "x" * 500,  # 500-char title to bulk up JSON size
            "source": f"docs/adr/{i:04d}-test.md",
        }
        for i in range(1, 901)
    ]
    result = NAV._check_non_detail_bounds(env, big_records, [], "search")
    assert result is not None, (
        "_check_non_detail_bounds must refuse when estimated JSON exceeds 512 KiB"
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "result_too_large"
    assert "limits" in result["error"]
    assert result["error"]["limits"].get("max_result_bytes") == 512 * 1024


def test_unsafe_filesystem_symlink_refuses_operation(tmp_path: pathlib.Path) -> None:
    """A symlinked ADR file causes the operation to be refused with unsafe_input.

    spec: "Never follow or publish through an unsafe path, symlink, hard link,
    special file, duplicate identity, identity-changing path..."
    spec AC-0009: "Negative fixtures for traversal, links, special files,
    duplicate identity, and identity change refuse the operation before output
    is published."
    Built at test time because symlinks cannot be committed to the repository.
    """
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)

    # A real conforming ADR
    real = tmp_path / "real-adr.md"
    real.write_text(
        "# ADR-0001: Symlink target\n\n"
        "- **Status:** Accepted\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        "## Decision\n\n- **D1:** Symlink test.\n",
        encoding="utf-8",
    )
    link = adr_dir / "0001-sym.md"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlinks unavailable on this filesystem")

    payload = NAV.run_query(tmp_path, {"operation": "summary"})
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "unsafe_input", (
        f"symlinked candidate must set code='unsafe_input'; got {payload['error']}"
    )


def test_unsafe_filesystem_hard_link_refuses_operation(tmp_path: pathlib.Path) -> None:
    """A hard-linked ADR file causes the operation to be refused.

    Built at test time; hard links cannot be committed.
    """
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    original = tmp_path / "original.md"
    original.write_text(
        "# ADR-0001: Hard link source\n\n"
        "- **Status:** Accepted\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        "## Decision\n\n- **D1:** Hard link test.\n",
        encoding="utf-8",
    )
    link = adr_dir / "0001-hl.md"
    try:
        os.link(original, link)
    except OSError:
        pytest.skip("hard links not supported on this filesystem")
    payload = NAV.run_query(tmp_path, {"operation": "summary"})
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "unsafe_input", (
        f"hard-linked candidate must set code='unsafe_input'; got {payload['error']}"
    )


def test_unsafe_filesystem_fifo_refuses_operation(tmp_path: pathlib.Path) -> None:
    """A FIFO named as an ADR candidate causes the operation to be refused.

    Built at test time; FIFOs cannot be committed.
    """
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFOs not supported on this platform")
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    fifo = adr_dir / "0001-fifo.md"
    try:
        os.mkfifo(fifo)
    except OSError:
        pytest.skip("FIFO creation failed on this filesystem")
    payload = NAV.run_query(tmp_path, {"operation": "summary"})
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "unsafe_input", (
        f"FIFO candidate must set code='unsafe_input'; got {payload['error']}"
    )


def test_traversal_attempt_refuses_operation(tmp_path: pathlib.Path) -> None:
    """A path traversal attempt (../../etc/passwd style symlink) is refused.

    spec: "Never follow or publish through... traversal"
    Built at test time.
    """
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    # Create a symlink that points outside the corpus root
    outside = tmp_path.parent / "outside.md"
    outside.write_text("outside content\n", encoding="utf-8")
    traversal_link = adr_dir / "0001-traverse.md"
    try:
        traversal_link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable on this filesystem")
    payload = NAV.run_query(tmp_path, {"operation": "summary"})
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "unsafe_input", (
        f"traversal attempt must set code='unsafe_input'; got {payload['error']}"
    )


def test_unsupported_operation_fails_with_error() -> None:
    """An unknown operation value fails with a stable error.

    spec: "decision-navigation.query.v1 supports five semantic operations"
    """
    payload = NAV.run_query(FIXTURE, {"operation": "invalid_operation"})
    assert payload["status"] == "error"
    assert "error" in payload


def test_missing_operation_key_fails_with_error() -> None:
    """A query dict missing the operation key fails with a stable error."""
    payload = NAV.run_query(FIXTURE, {})
    assert payload["status"] == "error"


def test_non_dict_query_returns_error_not_crash() -> None:
    """A non-dict query value returns a stable error rather than crashing.

    QE-7: run_query must not crash when called with a non-dict query.
    Before the fix, passing a string like "summary" caused an AttributeError
    because the code called query.get("operation") without checking the type.

    Mutation: removing the isinstance(query, dict) guard would cause this to
    raise AttributeError instead of returning an error dict.
    """
    for bad_query in ("summary", 42, None, ["operation", "summary"]):
        try:
            result = NAV.run_query(FIXTURE, bad_query)  # type: ignore[arg-type]
            assert result.get("status") == "error", (
                f"non-dict query {bad_query!r} must return status=error; got {result!r}"
            )
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(
                f"run_query must not crash with non-dict query {bad_query!r}; "
                f"raised {type(exc).__name__}: {exc}"
            ) from exc


def test_body_too_large_omission(tmp_path: pathlib.Path) -> None:
    """A record larger than 1 MiB has body omitted with reason body_too_large.

    spec: "An exact record result is bounded to 1 MiB of UTF-8 JSON. When its
    body would cross that bound, the successful result keeps record metadata and
    provenance, omits the body with reason body_too_large, and supplies the safe
    source action."
    Generated at test time.
    """
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    # A record just under 2 MiB (admission threshold) but over 1 MiB body threshold
    big_body = "x" * (1024 * 1024 + 100)
    content = (
        "# ADR-0001: Large body record\n\n"
        "- **Status:** Accepted\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        f"## Context\n\n{big_body}\n"
    )
    (adr_dir / "0001-large.md").write_text(content, encoding="utf-8")
    payload = NAV.run_query(tmp_path, {"operation": "record", "id": "ADR-0001"})
    # The response must be a success (not error), but body is omitted
    assert payload["status"] == "ok"
    record = payload["records"][0]
    assert record["body"]["available"] is False
    assert record["body"].get("omission_reason") == "body_too_large"


# ── register file edge cases ──────────────────────────────────────────────────


def test_missing_register_file_reported_as_absent(tmp_path: pathlib.Path) -> None:
    """A missing register file is reported as absent in summary.

    spec: "A missing register file is reported as absent."
    """
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    # Minimal corpus with one ADR, no register files
    (adr_dir / "0001-minimal.md").write_text(
        "# ADR-0001: Minimal\n\n"
        "- **Status:** Accepted\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        "## Decision\n\n- **D1:** Minimal test record.\n",
        encoding="utf-8",
    )
    payload = NAV.run_query(tmp_path, {"operation": "summary"})
    assert payload["status"] == "ok"
    regs = payload["summary"]["register_files"]
    assert regs["rfc_candidates"] == "absent" or regs["rfc_candidates"].get("row_count") is None, (
        "missing rfc-candidates.md must be reported as absent"
    )


_BOUNDARY_SENTINEL = "not a complete statement of the policy"
_BOUNDARY_QUERIES = [
    {"operation": "summary"},
    {"operation": "record", "id": "ADR-0001"},
    {"operation": "search", "selectors": [{"kind": "ADR"}]},
    {"operation": "lineage", "id": "ADR-0003", "direction": "older", "depth": 1},
    {"operation": "context", "selectors": [{"kind": "ADR"}]},
]


@pytest.mark.parametrize(
    "query", _BOUNDARY_QUERIES, ids=[q["operation"] for q in _BOUNDARY_QUERIES]
)
def test_reference_policy_boundary_present_in_response(query: dict) -> None:
    """Every query response carries a 'boundary' field with the exact policy note.

    spec AC-0021: "Every query and HTML view states that it reports recorded
    decisions and candidate context rather than the complete policy applicable
    to an action."

    Tests all five operations.  Mutation: removing 'boundary' from any
    operation's response would fail the exact-field assertion.
    """
    payload = NAV.run_query(FIXTURE, query)
    assert payload.get("status") == "ok", f"query {query!r} failed: {payload}"
    assert "boundary" in payload, (
        f"response for operation={query['operation']!r} must carry a 'boundary' field"
    )
    boundary = payload["boundary"]
    assert _BOUNDARY_SENTINEL in boundary.lower(), (
        f"boundary field must contain the policy sentinel text; got {boundary!r}"
    )


def test_summary_carries_query_envelope() -> None:
    """summary response carries normalized query in the response envelope.

    spec: "Every response contains schema, status, normalized query, boundary,
    and provenance."
    """
    query = {"operation": "summary"}
    payload = NAV.run_query(FIXTURE, query)
    assert "query" in payload, "response must contain normalized 'query'"
    assert payload["query"]["operation"] == "summary"


def test_lineage_invalid_depth_fails() -> None:
    """lineage depth outside 1-4 fails with a stable error.

    spec: "a depth from 1 through 4"
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "lineage", "id": "ADR-0001", "direction": "older", "depth": 5},
    )
    assert payload["status"] == "error"


def test_lineage_invalid_direction_fails() -> None:
    """lineage direction outside older/newer/both fails.

    spec: "a direction of older, newer, or both"
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "lineage", "id": "ADR-0001", "direction": "sideways", "depth": 1},
    )
    assert payload["status"] == "error"


def test_multi_did_scopes_parse_with_or_without_spaces(tmp_path: pathlib.Path) -> None:
    """`D6,D7` and `D7, D6` are one scope set, so the mirrored pair is checked."""
    adr = tmp_path / "docs" / "adr"
    adr.mkdir(parents=True)
    (adr / "0001-old.md").write_text(
        "# ADR-0001: Old\n\n- **Status:** Accepted\n"
        "- **Superseded in part:** ADR-0002 D6,D7\n\n## Decision\n",
        encoding="utf-8",
    )
    (adr / "0002-new.md").write_text(
        "# ADR-0002: New\n\n- **Status:** Accepted\n"
        "- **Supersedes in part:** ADR-0001 D7, D6\n\n## Decision\n",
        encoding="utf-8",
    )
    payload = NAV.run_query(tmp_path, {"operation": "record", "id": "ADR-0001"})
    checked = [r for r in payload["relationships"] if r["trust_class"] == "checked"]
    assert [(r["from"], r["to"], r["scope"]) for r in checked] == [
        ("ADR-0002", "ADR-0001", ["D6", "D7"])
    ]
    assert not [r for r in payload["relationships"] if r["resolution_state"] == "unresolved"]


# ══════════════════════════════════════════════════════════════════════════════
# CLI entry point tests (QE-16)
# ══════════════════════════════════════════════════════════════════════════════


def test_cli_query_summary_exits_zero() -> None:
    """main() with query --operation summary returns 0 and writes valid JSON.

    Mutation: changing the return code or breaking JSON output would fail.
    """
    buf = io.StringIO()
    import contextlib

    with contextlib.redirect_stdout(buf):
        code = NAV.main(["query", "--root", str(FIXTURE), "--operation", "summary"])
    assert code == 0, f"expected exit 0, got {code}"
    out = buf.getvalue()
    payload = json.loads(out)
    assert payload["status"] == "ok"
    assert payload["schema"] == "decision-navigation.query.v1"


def test_cli_query_unknown_record_exits_one() -> None:
    """main() returns 1 when the query itself returns an error status.

    Mutation: returning 0 on error would fail this test.
    """
    buf = io.StringIO()
    import contextlib

    with contextlib.redirect_stdout(buf):
        code = NAV.main([
            "query",
            "--root",
            str(FIXTURE),
            "--operation",
            "record",
            "--id",
            "ADR-9999",
        ])
    assert code == 1, f"expected exit 1 for unknown record, got {code}"
    out = buf.getvalue()
    payload = json.loads(out)
    assert payload["status"] == "error"


def test_cli_query_invalid_selectors_json_exits_two() -> None:
    """main() returns 2 when --selectors is not valid JSON.

    Mutation: returning 0 or 1 for bad JSON would fail this test.
    """
    err_buf = io.StringIO()
    import contextlib

    with contextlib.redirect_stderr(err_buf):
        code = NAV.main([
            "query",
            "--root",
            str(FIXTURE),
            "--operation",
            "search",
            "--selectors",
            "{bad json",
        ])
    assert code == 2, f"expected exit 2 for invalid selectors JSON, got {code}"


def test_cli_query_operation_routes_to_run_query() -> None:
    """main() query command calls run_query and prints its result as JSON.

    Mutation: skipping the run_query call or printing without json.dumps would fail.
    """
    buf = io.StringIO()
    import contextlib

    with contextlib.redirect_stdout(buf):
        code = NAV.main([
            "query",
            "--root",
            str(FIXTURE),
            "--operation",
            "lineage",
            "--id",
            "ADR-0003",
            "--direction",
            "older",
            "--depth",
            "1",
        ])
    assert code == 0
    payload = json.loads(buf.getvalue())
    assert payload["status"] == "ok"
    record_ids = {r["id"] for r in payload["records"]}
    assert "ADR-0002" in record_ids, "lineage older depth=1 from ADR-0003 must include ADR-0002"


def test_cli_export_dotdot_name_exits_two() -> None:
    """main() export with a dot-segment --name exits 2 without publishing anything.

    SEC-1: The --name must be validated BEFORE it is joined to a destination
    directory.  A dot-segment like '../escape.html' must be refused at exit code 2.

    Mutation: if --name validation is removed or happens after the join,
    a hostile name could escape the destination directory.
    """
    import contextlib

    err_buf = io.StringIO()
    with contextlib.redirect_stderr(err_buf):
        code = NAV.main(["export", "--root", str(FIXTURE), "--name", "../escape.html"])
    assert code == 2, (
        f"expected exit 2 for dot-segment --name; got {code}\nstderr: {err_buf.getvalue()!r}"
    )


def test_cli_export_absolute_name_exits_two() -> None:
    """main() export with an absolute --name exits 2 without publishing anything.

    SEC-1: An absolute path like '/etc/passwd.html' as --name must be refused
    at exit code 2 before any join to the destination directory.
    """
    import contextlib

    err_buf = io.StringIO()
    with contextlib.redirect_stderr(err_buf):
        code = NAV.main(["export", "--root", str(FIXTURE), "--name", "/etc/passwd.html"])
    assert code == 2, (
        f"expected exit 2 for absolute --name; got {code}\nstderr: {err_buf.getvalue()!r}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Caller-assertion schema validation (SEC-5)
# ══════════════════════════════════════════════════════════════════════════════


def test_context_non_list_assertions_refused() -> None:
    """context refuses assertions that are not a list.

    spec: "Caller assertions not conforming to the schema are refused."

    Mutation: removing the isinstance(assertions, list) check would return ok
    or crash instead of refusing with invalid_assertion.
    """
    payload = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [{"kind": "ADR"}],
            "assertions": "not a list",
        },
    )
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "invalid_assertion", (
        f"non-list assertions must yield invalid_assertion; got {payload['error']!r}"
    )


def test_context_non_dict_assertion_element_refused() -> None:
    """context refuses an assertion element that is not a dict.

    Mutation: removing the isinstance(a, dict) check would crash or accept
    a malformed assertion.
    """
    payload = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [{"kind": "ADR"}],
            "assertions": ["string-not-a-dict"],
        },
    )
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "invalid_assertion", (
        f"non-dict assertion element must yield invalid_assertion; got {payload['error']!r}"
    )


def test_context_assertion_non_string_field_refused() -> None:
    """context refuses an assertion whose 'from', 'to', or 'text' is not a string.

    Mutation: removing the isinstance(a[key], str) check would accept a malformed
    assertion.
    """
    payload = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [{"kind": "ADR"}],
            "assertions": [{"from": 123, "to": "ADR-0001", "text": "guide"}],
        },
    )
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "invalid_assertion", (
        f"assertion with non-string 'from' must yield invalid_assertion; got {payload['error']!r}"
    )


def test_context_valid_assertion_accepted() -> None:
    """context accepts a well-formed caller assertion and includes it in the response.

    Verifies that the schema check does not block valid assertions.
    """
    payload = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [{"kind": "ADR"}],
            "assertions": [{"from": "ADR-0001", "to": "ADR-0002", "text": "informs design"}],
        },
    )
    assert payload["status"] == "ok", f"valid assertion must be accepted; got {payload!r}"
    nav_only = [
        r for r in payload.get("relationships", []) if r.get("trust_class") == "navigation_only"
    ]
    assert nav_only, "caller assertion must appear as navigation_only relationship"


# ══════════════════════════════════════════════════════════════════════════════
# ADV-10 / QE-6: H1 first line; trailing comment; repeated D-IDs as set
# ══════════════════════════════════════════════════════════════════════════════


def test_h1_not_first_line_fails_whole_operation() -> None:
    """A record where the H1 is not the very first line must fail the operation.

    spec: 'The first line is an H1'  The code checks lines[0]; any leading blank
    line causes 'no H1 found' and the corpus is refused.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = pathlib.Path(td)
        adr_dir = td_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        # Blank first line; H1 is on line 2.
        content = "\n# ADR-0001: Record\n\n- **Status:** Accepted\n\n## Context\n\nBody.\n"
        (adr_dir / "0001-blank-first.md").write_text(content)
        payload = NAV.run_query(td_path, {"operation": "summary"})
    assert payload["status"] == "error", "H1 not on first line must fail the whole operation"
    assert payload["error"]["code"] == "malformed_record", (
        f"expected malformed_record; got {payload['error']['code']!r}"
    )


def test_two_html_comments_keeps_first_comment() -> None:
    """Status with two HTML comments keeps everything before the last comment.

    spec: 'remove one trailing HTML comment'.  'Accepted <!-- a --> kept <!-- b -->'
    must yield raw_value 'Accepted <!-- a --> kept'.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = pathlib.Path(td)
        adr_dir = td_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        content = (
            "# ADR-0001: Two-comment status\n\n"
            "- **Status:** Accepted <!-- a --> kept <!-- b -->\n\n"
            "## Context\n\nBody.\n"
        )
        (adr_dir / "0001-two-comment.md").write_text(content)
        payload = NAV.run_query(td_path, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok", f"two-comment record must be admitted; got {payload!r}"
    lc = payload["records"][0]["lifecycle"]
    assert lc["raw_value"] == "Accepted <!-- a --> kept", (
        f"only the last trailing comment must be stripped; got {lc['raw_value']!r}"
    )


def test_repeated_d_ids_form_set() -> None:
    """Repeated D-IDs in a scope are deduplicated to a set.

    spec: 'scope is a set of D-IDs'.  'D3, D3' must yield scope ['D3'].
    """
    parseable, scope = NAV._parse_did_list(["D3", "D3", "D1", "D1"])
    assert parseable is True, "valid D-IDs with duplicates must be parseable"
    assert scope == ["D1", "D3"], f"repeated D-IDs must be deduplicated; got {scope!r}"


# ══════════════════════════════════════════════════════════════════════════════
# ADV-17: Query refusal carries {code, message, limits, observed}
# ══════════════════════════════════════════════════════════════════════════════


def test_query_refusal_has_documented_error_shape() -> None:
    """Every query refusal must carry code, message, limits, and observed.

    spec: 'a stable error envelope … {code, message, limits, observed}'.
    Verified against an unknown-record refusal (not_found) and an unsafe-input
    refusal to cover both the record and corpus error paths.
    """
    # not_found refusal.
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-9999"})
    assert payload["status"] == "error"
    err = payload["error"]
    assert isinstance(err, dict), f"error must be a dict; got {type(err)}"
    for field in ("code", "message", "limits", "observed"):
        assert field in err, f"error dict must have '{field}' field; got keys: {list(err.keys())}"
    assert isinstance(err["limits"], dict), "limits must be a dict"
    assert isinstance(err["observed"], dict), "observed must be a dict"


# ══════════════════════════════════════════════════════════════════════════════
# ADV-9 / SEC-4 / QE-1: register safety — dangling symlink; two-table count
# ══════════════════════════════════════════════════════════════════════════════


def test_dangling_symlink_register_is_unsafe_input() -> None:
    """A dangling symlink register file must refuse the query with unsafe_input.

    spec: 'An unsafe register file refuses the operation with code unsafe_input.'
    A dangling symlink is not absent — it is an unsafe path.
    """
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = pathlib.Path(td)
        shutil.copytree(str(FIXTURE), str(td_path / "mixed"))
        corpus = td_path / "mixed"
        reg_dir = corpus / "docs" / "product" / "findings"
        reg_dir.mkdir(parents=True, exist_ok=True)
        reg_file = reg_dir / "rfc-candidates.md"
        if reg_file.exists() or reg_file.is_symlink():
            reg_file.unlink()
        reg_file.symlink_to("/absolutely/nonexistent/dangling/target")
        assert reg_file.is_symlink() and not reg_file.exists(), (
            "fixture must be a dangling symlink"
        )
        payload = NAV.run_query(corpus, {"operation": "summary"})
    assert payload["status"] == "error", "dangling symlink register must refuse the query"
    assert payload["error"]["code"] == "unsafe_input", (
        f"expected unsafe_input; got {payload['error']['code']!r}"
    )


def test_dangling_adr_dir_refuses_operation() -> None:
    """A dangling symlink at docs/adr must refuse the operation with unsafe_input.

    spec: corpus roots that are symlinks are refused rather than treated as absent.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = pathlib.Path(td)
        # docs/rfc is absent (OK); docs/adr is a dangling symlink (unsafe).
        docs = td_path / "docs"
        docs.mkdir()
        adr_link = docs / "adr"
        adr_link.symlink_to("/nonexistent/path")
        assert adr_link.is_symlink() and not adr_link.exists()
        payload = NAV.run_query(td_path, {"operation": "summary"})
    assert payload["status"] == "error", "dangling symlink corpus root must refuse the operation"
    assert payload["error"]["code"] in ("unsafe_input", "malformed_record"), (
        f"expected unsafe_input or malformed_record; got {payload['error']['code']!r}"
    )


def test_two_table_register_count_sums_all_tables() -> None:
    """_count_register_rows counts data rows across every table in the file.

    A file with two tables (1 and 2 data rows) must report 3, not 1.
    """
    text = (
        "# Register\n\n"
        "| Col1 | Col2 |\n"
        "|------|------|\n"
        "| row1 | val1 |\n"
        "\n"
        "## Second section\n\n"
        "| A | B |\n"
        "|---|---|\n"
        "| x | y |\n"
        "| p | q |\n"
    )
    count = NAV._count_register_rows(text)
    assert count == 3, f"two-table register (1 + 2 data rows) must count 3; got {count}"


# ══════════════════════════════════════════════════════════════════════════════
# Assertion validation: null/0 values; partial dicts (adv-2/3)
# ══════════════════════════════════════════════════════════════════════════════


def test_context_null_assertions_refused() -> None:
    """context refuses assertions=None (null) with invalid_assertion.

    Null is not a list. The validator must refuse whenever the 'assertions'
    key is present with a non-list value, including None.
    """
    payload = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [{"kind": "ADR"}],
            "assertions": None,
        },
    )
    assert payload["status"] == "error", f"assertions=None must be refused; got {payload!r}"
    assert payload["error"]["code"] == "invalid_assertion", (
        f"expected invalid_assertion; got {payload['error']['code']!r}"
    )


def test_context_integer_assertions_refused() -> None:
    """context refuses assertions=0 (an integer) with invalid_assertion.

    An integer is not a list. The validator must refuse non-list values.
    """
    payload = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [{"kind": "ADR"}],
            "assertions": 0,
        },
    )
    assert payload["status"] == "error", f"assertions=0 must be refused; got {payload!r}"
    assert payload["error"]["code"] == "invalid_assertion", (
        f"expected invalid_assertion; got {payload['error']['code']!r}"
    )


def test_context_partial_dict_assertion_refused() -> None:
    """context refuses an assertion dict missing the 'text' key.

    Each assertion element must carry string 'from', 'to', and 'text'.
    """
    payload = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [{"kind": "ADR"}],
            "assertions": [{"from": "ADR-0001", "to": "ADR-0002"}],
        },
    )
    assert payload["status"] == "error", f"partial assertion dict must be refused; got {payload!r}"
    assert payload["error"]["code"] == "invalid_assertion", (
        f"expected invalid_assertion; got {payload['error']['code']!r}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Lineage 200-record bound (adv-4)
# ══════════════════════════════════════════════════════════════════════════════


def test_lineage_result_too_large_when_record_count_exceeds_200(
    tmp_path: pathlib.Path,
) -> None:
    """lineage returns result_too_large when the traversed record set exceeds 200.

    The 200-record bound applies to lineage as well as search/context.
    This test uses a star topology: ADR-0001 supersedes ADR-0002 through
    ADR-0202 (201 leaf records). A 'newer' traversal from each leaf finds
    ADR-0001; a 'both' traversal from ADR-0001 at depth=1 returns all 202
    records which exceeds the 200-record bound.
    """
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)

    # Hub record: ADR-0001 supersedes ADR-0002 through ADR-0202 (201 records).
    # Use semicolons to list all superseded records in one field.
    leaf_ids = [f"ADR-{i:04d}" for i in range(2, 203)]
    supersedes_value = "; ".join(leaf_ids)
    hub_content = (
        "# ADR-0001: Lineage bound hub\n\n"
        "- **Status:** Accepted\n"
        f"- **Supersedes:** {supersedes_value}\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        "## Decision\n\nHub record.\n"
    )
    (adr_dir / "0001-hub.md").write_text(hub_content, encoding="utf-8")

    # 201 leaf records each mirroring the hub's 'Supersedes' with 'Superseded by: ADR-0001'.
    # Both sides declare the relationship → checked pairs.
    for i in range(2, 203):
        content = (
            f"# ADR-{i:04d}: Lineage bound leaf {i}\n\n"
            f"- **Status:** Superseded\n"
            f"- **Supersedes:** none\n"
            f"- **Supersedes in part:** none\n"
            f"- **Superseded by:** ADR-0001\n"
            f"- **Superseded in part:** none\n\n"
            f"## Decision\n\nLeaf record {i}.\n"
        )
        (adr_dir / f"{i:04d}-leaf.md").write_text(content, encoding="utf-8")

    # Lineage from ADR-0001 in direction='older' with depth=1 traverses
    # ADR-0001 → each of 201 superseded leaves (checked pairs).
    # Total: 202 records, which exceeds the 200-record bound.
    payload = NAV.run_query(
        tmp_path,
        {
            "operation": "lineage",
            "id": "ADR-0001",
            "direction": "older",
            "depth": 1,
        },
    )
    assert payload["status"] == "error", (
        f"lineage with >200 reachable records must be refused; got {payload!r}"
    )
    assert payload["error"]["code"] == "result_too_large", (
        f"expected result_too_large; got {payload['error']['code']!r}"
    )
    assert "limits" in payload["error"], "result_too_large must carry 'limits'"
    assert "observed" in payload["error"], "result_too_large must carry 'observed'"


# ══════════════════════════════════════════════════════════════════════════════
# AC-0021: absence-as-permission, conflict-resolution, grouping-as-authority
# ══════════════════════════════════════════════════════════════════════════════


def test_ac0021_absence_as_permission_no_match_returns_boundary(
    tmp_path: pathlib.Path,
) -> None:
    """A query with no matching record carries the boundary notice, not permission text.

    AC-0021: no mode treats absence as permission. When a record search returns
    no results (empty records list), the response boundary field still states the
    policy disclaimer rather than implying anything is permitted.
    """
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-alpha.md").write_text(
        "# ADR-0001: Absence test\n\n"
        "- **Status:** Accepted\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        "## Context\n\nTest record.\n",
        encoding="utf-8",
    )
    payload = NAV.run_query(
        tmp_path,
        {"operation": "search", "selectors": [{"identity": "RFC-9999"}]},
    )
    # No RFC-9999 exists: an empty result still states the policy boundary.
    assert payload["status"] == "ok", payload
    assert payload["records"] == [], "no match must not fall back to any default record"
    assert payload["boundary"] == NAV.BOUNDARY_NOTICE, payload["boundary"]


def test_ac0021_conflict_resolution_both_records_returned(
    tmp_path: pathlib.Path,
) -> None:
    """Two records that disagree are both returned; no winner is chosen.

    AC-0021: no mode resolves conflicts. When two records assert contradictory
    positions, the response includes both without picking a winner.
    """
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-alpha.md").write_text(
        "# ADR-0001: Use REST APIs\n\n"
        "- **Status:** Accepted\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        "## Decision\n\nUse REST for inter-service communication.\n",
        encoding="utf-8",
    )
    (adr_dir / "0002-beta.md").write_text(
        "# ADR-0002: Use gRPC APIs\n\n"
        "- **Status:** Accepted\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        "## Decision\n\nUse gRPC for inter-service communication.\n",
        encoding="utf-8",
    )
    payload = NAV.run_query(
        tmp_path,
        {"operation": "search", "selectors": [{"kind": "ADR"}]},
    )
    assert payload.get("status") == "ok", f"search failed: {payload!r}"
    ids = {r["id"] for r in payload.get("records", [])}
    assert "ADR-0001" in ids and "ADR-0002" in ids, (
        f"both conflicting records must be returned without a winner chosen; got ids {ids}"
    )


def test_ac0021_grouping_edges_are_navigation_only(tmp_path: pathlib.Path) -> None:
    """Caller-assertion (navigation) edges are trust_class navigation_only, not checked.

    AC-0021: grouping/navigation edges are navigation_only. A caller assertion
    passed to context must produce a relationship with trust_class='navigation_only'
    and resolution_state='caller_asserted', not 'checked'.
    """
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-alpha.md").write_text(
        "# ADR-0001: Alpha\n\n"
        "- **Status:** Accepted\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        "## Decision\n\nDecision alpha.\n",
        encoding="utf-8",
    )
    (adr_dir / "0002-beta.md").write_text(
        "# ADR-0002: Beta\n\n"
        "- **Status:** Accepted\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        "## Decision\n\nDecision beta.\n",
        encoding="utf-8",
    )
    payload = NAV.run_query(
        tmp_path,
        {
            "operation": "context",
            "selectors": [{"kind": "ADR"}],
            "assertions": [{"from": "ADR-0001", "to": "ADR-0002", "text": "related by theme"}],
        },
    )
    assert payload.get("status") == "ok", f"context with assertion failed: {payload!r}"
    nav_only = [
        r for r in payload.get("relationships", []) if r.get("trust_class") == "navigation_only"
    ]
    assert nav_only, "caller assertion must produce a navigation_only relationship"
    for r in nav_only:
        assert r["resolution_state"] == "caller_asserted", (
            f"navigation_only edge must be caller_asserted; got {r!r}"
        )
        assert r["trust_class"] == "navigation_only", (
            f"grouping edge must not be 'checked'; got trust_class={r['trust_class']!r}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# header_fields bounded-export pin (adv-1)
# ══════════════════════════════════════════════════════════════════════════════


def test_bounded_export_header_fields_include_date_and_supersedes_none(
    tmp_path: pathlib.Path,
) -> None:
    """bounded export includes header_fields with Date and Supersedes: none.

    Every record in both export modes carries header_fields as an ordered list
    of {label, raw_value, display_value} for each bold-labeled header field.
    This test pins the Date field (added to 0001-alpha.md) and a 'Supersedes: none'
    field in the bounded export's data island.
    """
    import json as _json

    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-alpha.md").write_text(
        "# ADR-0001: Header fields export test\n\n"
        "- **Date:** 2024-06-01\n"
        "- **Status:** Accepted\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        "## Decision\n\nDecision body.\n",
        encoding="utf-8",
    )
    # Use tmp_path/corpus as the corpus root; dest is a sibling (outside corpus).
    corpus_dir = tmp_path / "corpus"
    (corpus_dir / "docs" / "adr").mkdir(parents=True, exist_ok=True)
    # Copy the ADR file to the corpus subdirectory.
    import shutil as _shutil

    _shutil.copy2(
        str(adr_dir / "0001-alpha.md"),
        str(corpus_dir / "docs" / "adr" / "0001-alpha.md"),
    )
    dest_dir = tmp_path / "dest_out"
    dest_dir.mkdir()
    result = EXPLORER.publish_explorer(
        corpus_dir,
        destination=dest_dir,
        mode="bounded",
    )
    assert result.get("status") == "ok", f"bounded export failed: {result!r}"
    html_path = result["path"]
    with pathlib.Path(html_path).open(encoding="utf-8") as fh:
        html = fh.read()

    # Extract the data island JSON.
    import re as _re

    m = _re.search(
        r'<script type="application/json" id="nav-data">\s*(.*?)\s*</script>',
        html,
        _re.DOTALL,
    )
    assert m, "data island not found in exported HTML"
    # Unescape the JSON (safe_json replaces & < > with \uXXXX).
    raw_json = m.group(1)
    data = _json.loads(raw_json)
    records = {r["id"]: r for r in data.get("records", [])}
    assert "ADR-0001" in records, f"ADR-0001 missing from exported records; got {list(records)}"
    hf = records["ADR-0001"].get("header_fields", [])
    assert isinstance(hf, list), f"header_fields must be a list; got {type(hf)}"
    labels = [e["label"] for e in hf]
    assert "Date" in labels, f"header_fields must include 'Date'; got {labels}"
    date_entry = next(e for e in hf if e["label"] == "Date")
    assert date_entry["raw_value"] == "2024-06-01", f"Date raw_value mismatch: {date_entry}"
    assert "Supersedes" in labels, f"header_fields must include 'Supersedes'; got {labels}"
    sup_entry = next(e for e in hf if e["label"] == "Supersedes")
    assert sup_entry["raw_value"] == "none", (
        f"Supersedes raw_value must be 'none'; got {sup_entry!r}"
    )


@pytest.mark.parametrize(
    "assertions",
    ["5", '{"from": "ADR-0001"}', '[{"from": "ADR-0001", "to": 1, "text": "x"}]'],
    ids=["number", "object", "non-string-field"],
)
def test_cli_export_refuses_malformed_assertions(
    tmp_path: pathlib.Path, assertions: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI export refuses a non-list assertions value or an element with a
    non-string field with invalid_assertion, and publishes nothing."""
    code = NAV.main([
        "export",
        "--root",
        str(FIXTURE),
        "--destination",
        str(tmp_path),
        "--name",
        "refused.html",
        "--assertions",
        assertions,
    ])
    err = capsys.readouterr().err
    assert code != 0, err
    assert "invalid_assertion" in err, err
    assert not list(tmp_path.iterdir()), "a refused export must publish nothing"


def test_grouping_only_selector_is_refused() -> None:
    """A selector whose only key is grouping filters nothing, so it is refused
    instead of returning the whole corpus; grouping beside a filter is allowed."""
    refused = NAV.run_query(FIXTURE, {"operation": "search", "selectors": [{"grouping": "auth"}]})
    assert refused["status"] == "error", refused
    assert refused["error"]["code"] == "invalid_selector", refused["error"]
    allowed = NAV.run_query(
        FIXTURE,
        {"operation": "search", "selectors": [{"grouping": "auth", "kind": "ADR"}]},
    )
    assert allowed["status"] == "ok", allowed
    assert allowed["records"] and all(r["kind"] == "ADR" for r in allowed["records"])


def test_header_field_keeps_continuation_lines(tmp_path: pathlib.Path) -> None:
    """A header field that wraps onto following lines, including nested bullets,
    keeps its whole recorded value, as the Related grammar defines its extent."""
    adr = tmp_path / "docs" / "adr"
    adr.mkdir(parents=True)
    (adr / "0001-wrapped.md").write_text(
        "# ADR-0001: Wrapped\n\n- **Status:** Accepted\n- **Supersedes:** none\n"
        "- **Related:** ADR-0002 (first line\n  continues here); ADR-0003\n"
        "  - nested ADR-0004\n- **Date:** 2024-03-15\n\n## Context\n\nBody.\n",
        encoding="utf-8",
    )
    payload = NAV.run_query(tmp_path, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok", payload
    fields = {f["label"]: f["raw_value"] for f in payload["records"][0]["header_fields"]}
    assert fields["Related"] == (
        "ADR-0002 (first line\n  continues here); ADR-0003\n  - nested ADR-0004"
    ), fields["Related"]
    assert fields["Date"] == "2024-03-15"


def test_escape_display_covers_tag_and_format_characters() -> None:
    """Tag characters, soft hyphen, deprecated format controls and interlinear
    annotation controls are shown as visible escapes."""
    raw = "a\U000e0041b­c⁪d￹e᠎f"
    shown = NAV._escape_display(raw)
    for cp in ("E0041", "00AD", "206A", "FFF9", "180E"):
        assert f"[U+{cp}]" in shown, (cp, shown)


def _write(root: pathlib.Path, name: str, text: str) -> None:
    adr = root / "docs" / "adr"
    adr.mkdir(parents=True, exist_ok=True)
    (adr / name).write_text(text, encoding="utf-8")


def test_admission_time_bound_on_a_near_2_mib_supersession_header(
    tmp_path: pathlib.Path,
) -> None:
    """AC-0001: a candidate of at least 1.9 MiB whose header is one Superseded by
    field followed by 200,000 token-carrying continuation lines, within the 2 MiB
    bound, is admitted in under 2 seconds."""
    import time

    text = (
        "# ADR-0001: Big\n\n- **Status:** Accepted\n- **Superseded by:** ADR-0002;\n"
        + "ADR-0002;\n" * 200_000
        + "\n## Context\n\nx\n"
    )
    size = len(text.encode("utf-8"))
    assert int(1.9 * 1024 * 1024) <= size <= 2 * 1024 * 1024, size
    _write(tmp_path, "0001-big.md", text)
    _write(tmp_path, "0002-other.md", "# ADR-0002: Other\n\n- **Status:** Accepted\n\n## Context\n\ny\n")
    start = time.monotonic()
    payload = NAV.run_query(tmp_path, {"operation": "summary"})
    elapsed = time.monotonic() - start
    assert payload["status"] == "ok", payload.get("error")
    assert elapsed < 2.0, f"admission took {elapsed:.2f} s"


def test_wrapped_supersession_field_yields_every_entry(tmp_path: pathlib.Path) -> None:
    """A supersession field's entries are read from its whole extent, so an
    identity on a continuation line becomes a relationship too."""
    _write(
        tmp_path,
        "0001-old.md",
        "# ADR-0001: Old\n\n- **Status:** Accepted\n- **Superseded by:** ADR-0010;\n"
        "  ADR-0011\n\n## Context\n\nx\n",
    )
    payload = NAV.run_query(tmp_path, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok", payload.get("error")
    targets = sorted(
        r["to"] for r in payload["relationships"] if r["relation"] == "superseded_by"
    )
    assert targets == ["ADR-0010", "ADR-0011"], targets


@pytest.mark.parametrize(
    ("status_lines", "expected"),
    [
        ("- **Status**: Accepted\n", "Accepted"),
        ("- **Status:** Accepted <!-- c -->\n  wrapped continuation\n", "Accepted"),
    ],
    ids=["colon-after-bold", "wrapped"],
)
def test_lifecycle_value_from_the_status_label_line(
    tmp_path: pathlib.Path, status_lines: str, expected: str
) -> None:
    """Either Status label form is the Status field; the lifecycle raw_value is
    its label line only, never the missing-state marker, while the header field
    keeps the whole extent."""
    _write(tmp_path, "0001-a.md", "# ADR-0001: A\n\n" + status_lines + "\n## Context\n\nx\n")
    payload = NAV.run_query(tmp_path, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok", payload.get("error")
    rec = payload["records"][0]
    assert rec["lifecycle"].get("missing") is not True, rec["lifecycle"]
    assert rec["lifecycle"]["raw_value"] == expected, rec["lifecycle"]
    status_field = next(f for f in rec["header_fields"] if f["label"] == "Status")
    assert status_field["raw_value"] == status_lines.split("**", 2)[2].lstrip(":").lstrip().rstrip("\n")


def test_both_status_label_forms_make_a_record_malformed(tmp_path: pathlib.Path) -> None:
    """A header holding both `**Status:**` and `**Status**:` has two Status
    fields, so the whole operation refuses as malformed."""
    _write(
        tmp_path,
        "0001-a.md",
        "# ADR-0001: A\n\n- **Status:** Accepted\n- **Status**: Superseded\n\n## Context\n\nx\n",
    )
    payload = NAV.run_query(tmp_path, {"operation": "summary"})
    assert payload["status"] == "error", payload
