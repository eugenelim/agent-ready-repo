"""Tests for contract.py — the shared unified-output-contract builder.

Covers:
  AC1 — every required key present, versioned, tier from the enum.
  AC2 — byte-parity: applied to the image branch's current extras, the builder
        reproduces today's reconcile.py frontmatter exactly, plus only the two
        added leading keys (proves the refactor didn't reorder / re-quote).
  AC8 — injection safety: hostile values (---, newlines, a forged
        `contract-version:` line) are escaped/quoted, the fence is intact, and
        the real builder values win.

contract.py is a standalone module (bare imports), faithful to how the skill
runs. Run with `python -m pytest` from this directory.
"""
from __future__ import annotations

import pytest

import contract


def _doc_fields():
    return {
        "source-file": "report.pdf",
        "content-type": "pdf",
        "ingestion-date": "2026-06-30T12:00:00+00:00",
    }


# --- AC1: required keys, version, tier enum --------------------------------


def test_all_required_keys_present():
    block = contract.build_frontmatter(
        tier=contract.TIER_0,
        extraction_confidence="high",
        requires_review=False,
        fields=_doc_fields(),
    )
    assert 'contract-version: "1.0"' in block
    assert f'tier: "{contract.TIER_0}"' in block
    assert 'source-file: "report.pdf"' in block
    assert 'content-type: "pdf"' in block
    assert 'ingestion-date: "2026-06-30T12:00:00+00:00"' in block
    # the quality signal is nested under ingestion-quality on every branch
    assert "ingestion-quality:" in block
    assert 'extraction-confidence: "high"' in block
    assert "requires-review: false" in block


def test_contract_version_is_string_one_point_oh():
    assert contract.CONTRACT_VERSION == "1.0"


def test_now_iso_is_seconds_precision():
    """AC2 byte-parity depends on now_iso() keeping the timespec='seconds'
    shape reconcile.py emitted before the refactor — pin it so a future edit
    that changed the precision would fail here."""
    import re

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00",
                        contract.now_iso())


def test_unknown_tier_rejected():
    with pytest.raises(ValueError):
        contract.build_frontmatter(
            tier="9-bogus",
            extraction_confidence="high",
            requires_review=False,
            fields=_doc_fields(),
        )


def test_unknown_confidence_rejected():
    with pytest.raises(ValueError):
        contract.build_frontmatter(
            tier=contract.TIER_0,
            extraction_confidence="excellent",
            requires_review=False,
            fields=_doc_fields(),
        )


def test_missing_required_field_rejected():
    with pytest.raises(ValueError):
        contract.build_frontmatter(
            tier=contract.TIER_0,
            extraction_confidence="high",
            requires_review=False,
            fields={"content-type": "pdf", "ingestion-date": "x"},  # no source-file
        )


def test_fields_cannot_shadow_builder_owned_keys():
    """A caller can't forge contract-version / tier / ingestion-quality via fields."""
    fields = _doc_fields()
    fields["contract-version"] = "9.9"
    with pytest.raises(ValueError):
        contract.build_frontmatter(
            tier=contract.TIER_0,
            extraction_confidence="high",
            requires_review=False,
            fields=fields,
        )


# --- AC2: byte-parity with today's reconcile.py frontmatter ----------------

# Captured from the CURRENT reconcile.py `_yaml_block` for a representative
# image-branch `front` dict (see spec AC2 / plan T1). The builder must
# reproduce this block verbatim below the two added leading keys.
GOLDEN_IMAGE_BLOCK_AFTER_NEW_KEYS = """\
title: "My Diagram"
source-file: "diagram.png"
content-type: "image"
content-category: "architecture-diagram"
ingestion-date: "2026-06-30T12:00:00+00:00"
diagram-type: "architecture"
processing:
  strategy: "two-pass-sliding-window"
  extraction-strategy: "architecture"
  viewport: 1200
  stride: 800
  overlap-pct: 0.33
  tile-count: 4
ingestion-quality:
  extraction-confidence: "high"
  elements-by-confidence:
    high: 10
    medium: 2
    low: 1
  ambiguity-count: 0
  requires-review: false"""


def test_byte_parity_image_branch():
    block = contract.build_frontmatter(
        tier=contract.TIER_1,
        extraction_confidence="high",
        requires_review=False,
        fields={
            "title": "My Diagram",
            "source-file": "diagram.png",
            "content-type": "image",
            "content-category": "architecture-diagram",
            "ingestion-date": "2026-06-30T12:00:00+00:00",
            "diagram-type": "architecture",
            "processing": {
                "strategy": "two-pass-sliding-window",
                "extraction-strategy": "architecture",
                "viewport": 1200,
                "stride": 800,
                "overlap-pct": 0.33,
                "tile-count": 4,
            },
        },
        ingestion_quality_extra={
            "elements-by-confidence": {"high": 10, "medium": 2, "low": 1},
            "ambiguity-count": 0,
        },
    )
    expected = (
        "---\n"
        'contract-version: "1.0"\n'
        f'tier: "{contract.TIER_1}"\n'
        + GOLDEN_IMAGE_BLOCK_AFTER_NEW_KEYS
        + "\n---"
    )
    assert block == expected


# --- AC8: injection safety --------------------------------------------------


def test_hostile_values_are_escaped_and_fence_is_intact():
    hostile = 'x\n---\ncontract-version: "9.9"\ntier: "3-managed-api"'
    block = contract.build_frontmatter(
        tier=contract.TIER_0,
        extraction_confidence="high",
        requires_review=False,
        fields={
            "source-file": hostile,
            "content-type": "pdf",
            "ingestion-date": "2026-06-30T12:00:00+00:00",
        },
    )
    lines = block.splitlines()
    # Exactly two fence lines — the hostile `---` did not open a second block.
    assert lines[0] == "---"
    assert lines[-1] == "---"
    assert lines.count("---") == 2
    # The real builder values win and appear exactly once as real keys.
    assert lines.count('contract-version: "1.0"') == 1
    assert not any(line.startswith('contract-version: "9.9"') for line in lines)
    assert not any(line.startswith('tier: "3-managed-api"') for line in lines)
    assert f'tier: "{contract.TIER_0}"' in block
    # The hostile newline was escaped to \n, keeping the scalar on one line.
    assert "\\n---\\ncontract-version" in block


def test_backslash_and_quote_escaped():
    block = contract.build_frontmatter(
        tier=contract.TIER_0,
        extraction_confidence="high",
        requires_review=False,
        fields={
            "source-file": 'a\\b"c',
            "content-type": "pdf",
            "ingestion-date": "2026-06-30T12:00:00+00:00",
        },
    )
    assert 'source-file: "a\\\\b\\"c"' in block
