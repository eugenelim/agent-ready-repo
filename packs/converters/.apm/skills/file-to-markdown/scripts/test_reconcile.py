"""Tests for reconcile.py — the deterministic per-tile merge.

Locks the two silent-data-loss fixes:
  distinct same-(type,name) nodes with disjoint bboxes stay separate,
        while the same node seen across overlapping tiles still merges to one.
  unnamed elements are retained (not silently dropped) and rendered
        with a visible "(unlabeled)" label.

reconcile.py is a standalone script (no relative imports), so importing its
functions is faithful to how it runs; one end-to-end subprocess test also
exercises the documented `python scripts/reconcile.py` invocation.

Run with `python -m pytest` from this directory.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import contract
import reconcile

HERE = Path(__file__).resolve().parent


# Byte-parity locked to the REAL producer (reconcile.render_markdown), not
# just the builder: if render_markdown's field dict or nesting drifts, this goes
# red. The block below is today's image-branch frontmatter with only the two
# additive keys prepended.
EXPECTED_IMAGE_FRONTMATTER = """\
---
contract-version: "1.0"
tier: "1-agent-vision"
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
  requires-review: false
---"""


def test_render_markdown_frontmatter_byte_parity(monkeypatch):
    monkeypatch.setattr(contract, "now_iso", lambda: "2026-06-30T12:00:00+00:00")
    elems = (
        [reconcile.Element(type="component", name=f"h{i}", confidence="high")
         for i in range(10)]
        + [reconcile.Element(type="component", name=f"m{i}", confidence="medium")
           for i in range(2)]
        + [reconcile.Element(type="component", name="l0", confidence="low")]
    )
    md = reconcile.render_markdown(
        title="My Diagram",
        source_image="diagram.png",
        strategy="architecture",
        structural_map={"diagram_type": "architecture"},
        canonical=elems,
        ambiguities=[],
        detail_manifest={"viewport": 1200, "stride": 800, "overlap_pct": 0.33,
                         "tiles": [{}, {}, {}, {}]},
        overview_manifest=None,
    )
    # The frontmatter is the leading block up to and including the second fence.
    lines = md.splitlines()
    end = lines.index("---", 1)
    block = "\n".join(lines[: end + 1])
    assert block == EXPECTED_IMAGE_FRONTMATTER

CROP = {"x": 0, "y": 0, "w": 1200, "h": 900}


def _raw(name, bbox, crop=CROP, tile="tile_W0_R0_C0", type_="step", conf="high"):
    return (tile, crop, {"type": type_, "name": name, "bbox_in_tile": bbox,
                         "confidence": conf})


def test_distinct_same_label_nodes_are_preserved():
    """two 'Validate' steps far apart (IoU 0) must not collapse into one."""
    raw = [
        _raw("Validate", {"x": 10, "y": 10, "w": 80, "h": 40}),
        _raw("Validate", {"x": 900, "y": 700, "w": 80, "h": 40}),
    ]
    canonical, ambiguities = reconcile.reconcile_elements(raw)
    names = sorted(e.name for e in canonical)
    assert len(canonical) == 2, f"expected 2 distinct nodes, got {len(canonical)}"
    assert names == ["Validate", "Validate"]


def test_same_node_across_overlapping_tiles_still_merges():
    """regression: one node seen in two overlapping tiles → one element."""
    crop1 = {"x": 0, "y": 0, "w": 1200, "h": 900}
    crop2 = {"x": 80, "y": 0, "w": 1200, "h": 900}
    raw = [
        ("tile_A", crop1, {"type": "step", "name": "Fetch",
                           "bbox_in_tile": {"x": 100, "y": 100, "w": 80, "h": 40},
                           "confidence": "high"}),
        # global bbox identical (100,100) → IoU 1.0 → same node
        ("tile_B", crop2, {"type": "step", "name": "Fetch",
                           "bbox_in_tile": {"x": 20, "y": 100, "w": 80, "h": 40},
                           "confidence": "medium"}),
    ]
    canonical, _ = reconcile.reconcile_elements(raw)
    assert len(canonical) == 1, f"expected merge to 1, got {len(canonical)}"
    assert canonical[0].tile_sources == ["tile_A", "tile_B"]


def test_unnamed_element_is_retained():
    """an unnamed box is kept, not silently dropped."""
    raw = [_raw("", {"x": 400, "y": 400, "w": 80, "h": 40}, type_="box")]
    canonical, _ = reconcile.reconcile_elements(raw)
    assert len(canonical) == 1, "unnamed element was dropped"
    assert canonical[0].name == "", "stored name should stay faithful (empty)"


def test_zero_area_same_name_boxes_collapse():
    """Zero-area (degenerate) same-name boxes can't be spatially distinguished,
    so they collapse to one rather than rendering as duplicate rows."""
    raw = [
        _raw("Node", {"x": 100, "y": 100, "w": 0, "h": 0}),
        _raw("Node", {"x": 100, "y": 100, "w": 0, "h": 0}),
    ]
    canonical, _ = reconcile.reconcile_elements(raw)
    assert len(canonical) == 1, "zero-area same-name boxes should collapse"


def test_end_to_end_cli(tmp_path: Path):
    """+ through the documented `python scripts/reconcile.py` form."""
    manifest = {
        "source_image": "x.png", "viewport": 1200, "stride": 800,
        "overlap_pct": 0.33,
        "tiles": [{"filename": "tile_W0_R0_C0.png", "row": 0, "col": 0,
                   "crop_box": CROP}],
    }
    extractions = {
        "structural_map": {"layout": "left-to-right", "diagram_type": "process"},
        "tiles": [{"tile_id": "tile_W0_R0_C0", "elements": [
            {"type": "step", "name": "Validate",
             "bbox_in_tile": {"x": 10, "y": 10, "w": 80, "h": 40}, "confidence": "high"},
            {"type": "step", "name": "Validate",
             "bbox_in_tile": {"x": 900, "y": 700, "w": 80, "h": 40}, "confidence": "high"},
            {"type": "box", "name": "",
             "bbox_in_tile": {"x": 400, "y": 400, "w": 80, "h": 40}, "confidence": "high"},
        ]}],
    }
    man_p = tmp_path / "detail_manifest.json"
    ext_p = tmp_path / "extractions.json"
    man_p.write_text(json.dumps(manifest))
    ext_p.write_text(json.dumps(extractions))
    out_md = tmp_path / "out.md"
    out_json = tmp_path / "out.json"

    r = subprocess.run(
        [sys.executable, str(HERE / "reconcile.py"),
         "--manifest", str(man_p), "--extractions", str(ext_p),
         "--strategy", "process", "--title", "T",
         "--output-json", str(out_json), "--output-md", str(out_md)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "ELEMENTS: 3" in r.stdout, r.stdout
    md = out_md.read_text()
    assert "(unlabeled)" in md, "unnamed element not rendered"
    # The image branch now emits the unified contract: the two new keys plus
    # the pre-existing block, intact.
    assert 'contract-version: "1.0"' in md
    assert 'tier: "1-agent-vision"' in md
    assert "ingestion-quality:" in md
