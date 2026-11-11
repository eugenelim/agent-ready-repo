"""Roster test: Slice 1 writer boundary registry matches delivery-content-safety.md §4.

AC-0014: the delivery-content-safety.md §4 profile matrix must name every Slice 1
durable semantic writer and replay boundary, and the code registry in
_content_safety.py must list the same set with the same profile assignments.

This test:
1. Loads SLICE_1_WRITER_BOUNDARIES from the work-loop _content_safety.py script.
2. Parses the "Slice 1 writer boundaries" table from delivery-content-safety.md §4.
3. Asserts both boundary names and profile assignments agree.

Both reads are anchored at the repo root via Path(__file__).resolve().parents[2].
A broken registry or missing matrix entry fails this test before any semantic writer
task begins.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]

_CONTENT_SAFETY_MODULE = (
    REPO_ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
    / "_content_safety.py"
)

_DELIVERY_CONTENT_SAFETY_DOC = (
    REPO_ROOT / "docs" / "architecture" / "delivery-content-safety.md"
)

# The marker that precedes the Slice 1 boundary table in the doc.
# The table follows "Slice 1 writer boundaries" in the table header row.
_TABLE_MARKER = "Slice 1 writer boundaries"

# Matches a Markdown table data row: | `boundary-name` | Profile text |
_ROW_RE = re.compile(r"\|\s*`([^`]+)`\s*\|\s*([^|]+)\s*\|")

# Maps human-readable profile names in the doc to canonical hyphenated names in code.
_PROFILE_NORMALIZE: dict[str, str] = {
    "Structured control": "structured-control",
    "structured-control": "structured-control",
    "Evidence embedded record": "evidence-embedded-record",
    "evidence-embedded-record": "evidence-embedded-record",
    "Review report": "review-report",
    "review-report": "review-report",
    "Integration diagnostic": "integration-diagnostic",
    "integration-diagnostic": "integration-diagnostic",
    "Knowledge observation": "knowledge-observation",
    "knowledge-observation": "knowledge-observation",
    "Product addition": "product-addition",
    "product-addition": "product-addition",
}


def _load_module() -> ModuleType:
    """Load _content_safety.py by path, unregistered, matching the guards pattern."""
    spec = importlib.util.spec_from_file_location("cs_roster", str(_CONTENT_SAFETY_MODULE))
    assert spec is not None and spec.loader is not None, (
        f"cannot create import spec for {_CONTENT_SAFETY_MODULE}"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _parse_slice1_boundary_table(doc_text: str) -> dict[str, str]:
    """Extract the Slice 1 boundary table from the markdown document.

    Scans for a table whose header row contains _TABLE_MARKER, then collects
    every subsequent data row until a non-table line (empty or starts with '#').

    Returns {boundary_name: normalized_profile_name}.
    """
    lines = doc_text.splitlines()
    in_table = False
    result: dict[str, str] = {}

    for line in lines:
        # Detect the table header that contains the marker.
        if _TABLE_MARKER in line and line.strip().startswith("|"):
            in_table = True
            continue  # skip the header row itself

        if not in_table:
            continue

        # Stop at a section heading or a blank line outside the table.
        stripped = line.strip()
        if stripped.startswith("#"):
            break
        if not stripped:
            break

        # Parse a data row (skip separator rows like "| --- | --- |").
        m = _ROW_RE.match(line)
        if not m:
            continue
        boundary = m.group(1).strip()
        profile_raw = m.group(2).strip()

        # Skip the separator row (cells contain only dashes)
        if re.match(r"^[-: ]+$", boundary) or re.match(r"^[-: ]+$", profile_raw):
            continue

        profile = _PROFILE_NORMALIZE.get(profile_raw)
        if profile is None:
            # Attempt case-insensitive match
            profile = _PROFILE_NORMALIZE.get(profile_raw.title())
        if profile is None:
            profile = profile_raw  # keep raw value; assertion will flag the mismatch

        result[boundary] = profile

    return result


# ── Tests ────────────────────────────────────────────────────────────────────


def test_content_safety_module_exists() -> None:
    """The _content_safety.py module exists at the expected pack path (T2 gate)."""
    assert _CONTENT_SAFETY_MODULE.is_file(), (
        f"_content_safety.py not found at {_CONTENT_SAFETY_MODULE}. "
        "Run the T2 implementation before this roster test."
    )


def test_delivery_content_safety_doc_exists() -> None:
    """delivery-content-safety.md exists at docs/architecture/ (T2 gate)."""
    assert _DELIVERY_CONTENT_SAFETY_DOC.is_file(), (
        f"delivery-content-safety.md not found at {_DELIVERY_CONTENT_SAFETY_DOC}"
    )


def test_slice1_boundary_registry_matches_doc_matrix() -> None:
    """Code registry and doc matrix name the same boundaries and profiles (AC-0014).

    Both must agree on boundary names and their assigned profiles. A missing entry
    in either direction fails this test before any semantic writer task begins.
    """
    cs = _load_module()
    registry: dict[str, str] = dict(cs.SLICE_1_WRITER_BOUNDARIES)
    assert registry, "SLICE_1_WRITER_BOUNDARIES is empty in _content_safety.py"

    doc_text = _DELIVERY_CONTENT_SAFETY_DOC.read_text(encoding="utf-8")
    doc_table = _parse_slice1_boundary_table(doc_text)

    assert doc_table, (
        f"No Slice 1 boundary table found in {_DELIVERY_CONTENT_SAFETY_DOC.name}. "
        f"The table header row must contain '{_TABLE_MARKER}'."
    )

    registry_keys = frozenset(registry)
    doc_keys = frozenset(doc_table)

    missing_from_doc = registry_keys - doc_keys
    missing_from_registry = doc_keys - registry_keys

    assert not missing_from_doc, (
        f"Boundaries in code registry but missing from doc matrix "
        f"({_DELIVERY_CONTENT_SAFETY_DOC.name}): {sorted(missing_from_doc)}"
    )
    assert not missing_from_registry, (
        f"Boundaries in doc matrix but missing from code registry "
        f"(SLICE_1_WRITER_BOUNDARIES): {sorted(missing_from_registry)}"
    )

    mismatched = {
        b: (registry[b], doc_table[b])
        for b in registry_keys & doc_keys
        if registry[b] != doc_table[b]
    }
    assert not mismatched, (
        f"Profile assignments disagree between registry and doc: {mismatched}. "
        "Update both _content_safety.py and delivery-content-safety.md to agree."
    )


def test_initial_plan_review_appears_in_both() -> None:
    """initial-plan-review.v1 appears in both the registry and the doc matrix (AC-0014)."""
    cs = _load_module()
    assert "initial-plan-review.v1" in cs.SLICE_1_WRITER_BOUNDARIES, (
        "initial-plan-review.v1 is missing from SLICE_1_WRITER_BOUNDARIES"
    )
    doc_text = _DELIVERY_CONTENT_SAFETY_DOC.read_text(encoding="utf-8")
    doc_table = _parse_slice1_boundary_table(doc_text)
    assert "initial-plan-review.v1" in doc_table, (
        "initial-plan-review.v1 is missing from the delivery-content-safety.md §4 "
        "Slice 1 boundary table"
    )
