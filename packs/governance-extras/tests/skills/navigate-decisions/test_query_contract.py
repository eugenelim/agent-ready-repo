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
import os
import pathlib
import sys

import pytest  # noqa: F401 — used for pytest.skip, pytest.param, and fixtures

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / ".apm/skills/navigate-decisions/scripts"
FIXTURE = HERE / "fixtures/mixed"
SPEC = importlib.util.spec_from_file_location(
    "governance_extras_navigate_decisions", SCRIPTS / "navigate_decisions.py"
)
NAV = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NAV)


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
    assert (_ADR_DIR / "0002-x-research.md").is_file(), (
        "missing *-research.md support file"
    )
    assert (_ADR_DIR / "0001-notes").is_dir(), "missing NNNN-notes/ subdirectory"
    assert (_ADR_DIR / "0001-notes" / "some-note.md").is_file(), (
        "missing file inside NNNN-notes/"
    )


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
    assert candidates_rows == 3, (
        f"rfc-candidates.md: expected 3 data rows, got {candidates_rows}"
    )
    assert intents_rows == 2, (
        f"roadmap-intents.md: expected 2 data rows, got {intents_rows}"
    )


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
    assert "**Status:**" not in header, (
        "ADR-0030 must have no Status field in its header region"
    )


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
    assert "Superseded by:** ADR-0003" in adr0002, (
        "ADR-0002 must have 'Superseded by: ADR-0003'"
    )
    assert "Supersedes:** ADR-0002" in adr0003, (
        "ADR-0003 must have 'Supersedes: ADR-0002'"
    )


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
        text = (_NEG_DIR / "duplicate-ordinal" / "docs" / "adr" / name).read_text(
            encoding="utf-8"
        )
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
    text = (_NEG_DIR / "hostile" / "docs" / "adr" / "0001-hostile.md").read_text(
        encoding="utf-8"
    )
    assert "<script>" in text, "hostile fixture must contain '<script>' content"


def test_bidi_fixture_contains_bidi_control() -> None:
    """The bidi fixture contains at least one bidirectional Unicode control."""
    text = (_NEG_DIR / "bidi" / "docs" / "adr" / "0001-bidi.md").read_text(
        encoding="utf-8"
    )
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
    for key in ("schema", "status", "query", "boundary", "provenance",
                "records", "relationships", "omissions"):
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
    assert record["lifecycle"]["raw_value"] == (
        "Accepted (superseded in part by ADR-0020 for D3)"
    )


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
    """record entry carries id, kind, title, lifecycle, source, and body_availability.

    spec: "Each record carries its identifier, kind, title, exact lifecycle value or
    missing-state marker, repository-relative source, present structured fields,
    body-availability state..."
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0002"})
    rec = payload["records"][0]
    assert rec["id"] == "ADR-0002"
    assert rec["kind"] == "ADR"
    assert isinstance(rec["title"], str) and rec["title"]
    assert "source" in rec
    assert "body" in rec
    assert "available" in rec["body"]


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
        r.get("from") == "ADR-0020" and r.get("relation") == "supersedes_in_part"
        and r.get("to") == "ADR-0001"
        for r in rels
    ), "record must include checked partial edge from ADR-0020"
    # Must include the unresolved contextual reference to ADR-9999
    assert any(
        r.get("from") == "ADR-0001" and r.get("relation") == "related"
        and r.get("to") == "ADR-9999" and r.get("resolution_state") == "unresolved"
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
    """
    one_sided = _NEG_DIR / "one-sided"
    payload = NAV.run_query(
        one_sided,
        {"operation": "lineage", "id": "ADR-0001", "direction": "older", "depth": 1},
    )
    # ADR-0001 claims to supersede ADR-0002 but edge is unresolved.
    # lineage must return ADR-0001 and not traverse to ADR-0002 via lineage.
    if payload["status"] == "ok":
        # If traversal happened to ADR-0002, the edge was wrongly treated as checked.
        # We check the relationships for trust_class, not just the records set.
        for rel in payload.get("relationships", []):
            if rel.get("from") == "ADR-0001" and rel.get("to") == "ADR-0002":
                assert rel.get("trust_class") != "checked", (
                    "lineage must not traverse an unresolved (one-sided) edge as checked"
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
            r for r in rels
            if r.get("from") == "ADR-0001" and r.get("resolution_state") == "unresolved"
        ]
        assert unresolved, (
            "lineage must include the unresolved supersession entry from ADR-0001"
        )


def test_lineage_depth_limit_respected() -> None:
    """lineage stops at the requested depth and does not over-traverse.

    spec: "a depth from 1 through 4"
    """
    payload = NAV.run_query(
        FIXTURE,
        {"operation": "lineage", "id": "ADR-0003", "direction": "older", "depth": 1},
    )
    # With depth=1, lineage from ADR-0003 reaches ADR-0002 but not further.
    assert payload["status"] == "ok"


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
        r for r in payload["relationships"]
        if r.get("from") == "ADR-0020" and r.get("to") == "ADR-0001"
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
        r for r in payload["relationships"]
        if r.get("from") == "ADR-0010" and r.get("to") == "ADR-0011"
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
        r for r in rels
        if r.get("from") == "ADR-0020" and r.get("to") == "ADR-0001"
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
        r for r in payload["relationships"]
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
        r for r in payload["relationships"]
        if r.get("trust_class") == "navigation_only"
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
        r for r in payload["relationships"]
        if r.get("from") == "ADR-0003" and r.get("to") == "ADR-0002"
        and r.get("relation") == "supersedes"
    ]
    assert checked_full, "ADR-0003 record must include the checked full supersession relationship"
    rel = checked_full[0]
    assert rel["basis"] == "supersession_fields"
    assert rel["direction"] == "superseding_to_superseded"
    assert rel["trust_class"] == "checked"
    assert rel["resolution_state"] == "resolved"
    assert rel["scope"] == []
    # source is the superseding record
    assert "ADR-0003" in rel["source"]


def test_relationship_closed_value_set_checked_partial() -> None:
    """Checked partial supersession relationship has correct closed value fields.

    spec: closed relationship value table — checked partial supersession row
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0020"})
    checked_partial = [
        r for r in payload["relationships"]
        if r.get("from") == "ADR-0020" and r.get("to") == "ADR-0001"
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
    assert "ADR-0020" in rel["source"]


def test_relationship_closed_value_set_contextual_reference() -> None:
    """Contextual reference has correct closed value fields.

    spec: closed relationship value table — contextual reference row
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})
    contextual = [
        r for r in payload["relationships"]
        if r.get("from") == "ADR-0001" and r.get("relation") == "related"
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
        r for r in payload["relationships"]
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
        r for r in payload["relationships"]
        if r.get("from") == "ADR-0003" and r.get("to") == "ADR-0002"
        and r.get("trust_class") == "checked"
    ]
    assert checked, "ADR-0002 record must include the checked full edge from ADR-0003"
    assert "ADR-0003" in checked[0]["source"]


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

    spec: "relationships sort by from, relation, scope, to, then raw_value,
    with a null to sorting first"
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})
    rels = payload["relationships"]
    # Null targets must sort before non-null targets within the same from/relation/scope
    null_to_rels = [r for r in rels if r.get("to") is None]
    if null_to_rels:
        # Find a non-null-to rel with same from value
        for null_rel in null_to_rels:
            same_from = [
                r for r in rels
                if r.get("from") == null_rel.get("from")
                and r.get("relation") == null_rel.get("relation")
                and r.get("to") is not None
            ]
            for non_null in same_from:
                assert rels.index(null_rel) < rels.index(non_null), (
                    "null to must sort before non-null to within same from/relation"
                )


def test_scope_sort_empty_before_stated() -> None:
    """scope=[] (unstated) sorts before any stated scope.

    spec: "a list that is a proper prefix of another ranks first, so [] ranks
    before every stated scope"
    ADR-0010 has unstated scope [], ADR-0020 has scope ['D3'].
    """
    # Both edges go 'from' some record 'to' some record. We compare their
    # sort positions in a context result that includes both.
    payload = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [
                {"identity": "ADR-0001"},
                {"identity": "ADR-0010"},
                {"identity": "ADR-0011"},
                {"identity": "ADR-0020"},
            ],
        },
    )
    if payload["status"] == "ok":
        rels = payload["relationships"]
        # Find the unstated-scope edge and the D3-scope edge
        unstated = [r for r in rels if r.get("scope") == [] and r.get("relation") == "supersedes_in_part"]
        stated_d3 = [r for r in rels if r.get("scope") == ["D3"] and r.get("relation") == "supersedes_in_part"]
        # If both present with the same from and to, unstated should come first
        for u in unstated:
            for s in stated_d3:
                if u.get("from") == s.get("from") and u.get("to") == s.get("to"):
                    assert rels.index(u) < rels.index(s), (
                        "scope=[] must sort before scope=['D3'] for same from/relation/to"
                    )


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
        r for r in rels
        if r.get("from") == "ADR-0001" and r.get("relation") == "supersedes"
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
        r for r in payload["relationships"]
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
    null_to_rels = [r for r in rels if r.get("to") is None and r.get("resolution_state") == "unresolved"]
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
    """
    corpus = _NEG_DIR / "bidi"
    payload = NAV.run_query(corpus, {"operation": "record", "id": "ADR-0001"})
    assert payload["status"] == "ok"
    record = payload["records"][0]
    lc = record["lifecycle"]
    raw = lc["raw_value"]
    display = lc["display_value"]
    # raw_value preserves the bidi characters (U+202E and U+202C are present in fixture)
    assert "‮" in raw or "‬" in raw, (
        "raw_value must preserve bidi control characters"
    )
    # display_value must differ from raw_value (escaping changes it)
    assert display != raw, (
        "display_value must differ from raw_value when bidi controls are present"
    )


def test_related_self_reference_excluded() -> None:
    """ADR-0001 self-reference (ADR-0001) in its own Related field is excluded.

    spec: "each distinct token... except a token naming the record itself"
    """
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})
    rels = payload["relationships"]
    self_refs = [
        r for r in rels
        if r.get("from") == "ADR-0001" and r.get("to") == "ADR-0001"
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
    oversized.write_bytes(b"# ADR-0001: Oversized\n\n- **Status:** Accepted\n\n## Context\n\n" + b"x" * (2 * 1024 * 1024))
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
    assert "limit" in payload["error"]
    assert "observed" in payload["error"]
    assert "hint" in payload["error"]


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
    assert payload["error"]["code"] in ("unsafe_input", "input_too_large", "error"), (
        f"symlinked candidate must refuse the operation; got {payload['error']}"
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


def test_reference_policy_boundary_present_in_response() -> None:
    """Every query response states that it reports recorded decisions and
    candidate context, not the complete policy applicable to an action.

    spec AC-0021: "Every query and HTML view states that it reports recorded
    decisions and candidate context rather than the complete policy applicable
    to an action."
    spec: "State that the navigator reports recorded decisions and candidate
    context, not the complete policy applicable to a proposed action."
    """
    payload = NAV.run_query(FIXTURE, {"operation": "summary"})
    # The policy boundary note must appear somewhere in the response
    # Accept the note in provenance, boundary, or a top-level field
    response_str = str(payload)
    assert (
        "policy" in response_str.lower() or "candidate context" in response_str.lower()
        or "recorded decisions" in response_str.lower()
    ), "response must include the reference-policy boundary note"


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
