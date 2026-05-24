#!/usr/bin/env python3
"""
reconcile.py — Merge per-tile agent extractions into one canonical document.

What it does (deterministic, no LLM):
    1. Reads the detail manifest produced by `split_image.py detail`
       (maps each tile_id to its crop_box in source coordinates).
    2. Reads the agent's per-tile extractions JSON (one record per tile,
       each with a list of `elements`; each element optionally carries a
       `bbox_in_tile` for spatial dedup).
    3. Translates `bbox_in_tile` → `global_bbox` using the tile's crop_box.
    4. Groups elements that are the same thing seen by multiple tiles:
         (a) same normalized (type, name) → same element
         (b) within the same type, IoU(global_bbox) > 0.5 → same element
       Picks a canonical record per group (highest confidence first; on
       tie, the tile where the element sits closest to its center).
    5. Sorts the canonical elements by layout direction:
         left-to-right → ascending global x
         top-to-bottom → ascending global y
         radial / unspecified → reading order (y, then x)
    6. Emits a merged JSON and a Markdown file with YAML frontmatter,
       built from a deterministic template.

This is geometry + bookkeeping, not reasoning. The LLM's job is to fill
in `name`, `description`, `confidence` per tile; the script handles the
N→1 collapse the SKILL.md used to spend 60 lines explaining.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- IO --------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    if not path.exists():
        sys.exit(f"ERROR: file not found: {path}")
    try:
        return json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"ERROR: {path} is not valid JSON: {exc}")


# --- Domain types ----------------------------------------------------------


@dataclass
class Element:
    type: str                              # component, event, command, entity, ...
    name: str
    description: str = ""
    confidence: str = "medium"             # high | medium | low
    tile_sources: list[str] = field(default_factory=list)
    global_bbox: dict | None = None        # {x, y, w, h} in source coords
    extra: dict = field(default_factory=dict)  # strategy-specific extras


# --- Geometry --------------------------------------------------------------


def to_global_bbox(bbox_in_tile: dict | None, crop_box: dict) -> dict | None:
    if not bbox_in_tile:
        return None
    return {
        "x": int(crop_box["x"] + bbox_in_tile.get("x", 0)),
        "y": int(crop_box["y"] + bbox_in_tile.get("y", 0)),
        "w": int(bbox_in_tile.get("w", 0)),
        "h": int(bbox_in_tile.get("h", 0)),
    }


def iou(a: dict, b: dict) -> float:
    """Intersection-over-union for two {x, y, w, h} boxes in shared coords."""
    if not a or not b:
        return 0.0
    ax1, ay1 = a["x"], a["y"]
    ax2, ay2 = a["x"] + a["w"], a["y"] + a["h"]
    bx1, by1 = b["x"], b["y"]
    bx2, by2 = b["x"] + b["w"], b["y"] + b["h"]
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    union = (a["w"] * a["h"]) + (b["w"] * b["h"]) - inter
    return inter / union if union > 0 else 0.0


def edge_distance(bbox: dict, crop: dict) -> float:
    """How central is the element within its tile? Higher = more central.
    Used as a tiebreaker so we pick the tile where the element wasn't
    bisected at an edge."""
    if not bbox:
        return 0.0
    cx = crop["x"] + crop["w"] / 2
    cy = crop["y"] + crop["h"] / 2
    ex = bbox["x"] + bbox["w"] / 2
    ey = bbox["y"] + bbox["h"] / 2
    half_w = crop["w"] / 2
    half_h = crop["h"] / 2
    if half_w == 0 or half_h == 0:
        return 0.0
    # Normalized distance from center, inverted so center→1, edges→0
    dx = abs(ex - cx) / half_w
    dy = abs(ey - cy) / half_h
    return max(0.0, 1.0 - max(dx, dy))


# --- Normalization --------------------------------------------------------


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower()).strip(" .,:;-_")


CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


def confidence_rank(c: str) -> int:
    return CONFIDENCE_RANK.get((c or "").lower(), 0)


# --- Reconciliation -------------------------------------------------------


def reconcile_elements(
    raw_elements: list[tuple[str, dict, dict]],
    iou_threshold: float = 0.5,
) -> tuple[list[Element], list[dict]]:
    """
    raw_elements: list of (tile_id, crop_box, element_dict).
    Returns (canonical_elements, ambiguities).
    """
    # Stage 1: collapse exact (type, normalized_name) duplicates first.
    by_key: dict[tuple[str, str], list[Element]] = {}
    for tile_id, crop_box, raw in raw_elements:
        e_type = (raw.get("type") or "").strip().lower() or "element"
        name = (raw.get("name") or "").strip()
        if not name:
            # Skip elements without a name — cannot dedupe sensibly
            continue
        key = (e_type, _normalize(name))
        gbbox = to_global_bbox(raw.get("bbox_in_tile"), crop_box)
        elem = Element(
            type=e_type,
            name=name,
            description=(raw.get("description") or "").strip(),
            confidence=(raw.get("confidence") or "medium").lower(),
            tile_sources=[tile_id],
            global_bbox=gbbox,
            extra={k: v for k, v in raw.items()
                   if k not in {"type", "name", "description", "confidence",
                                "bbox_in_tile"}},
        )
        by_key.setdefault(key, []).append((elem, crop_box))

    canonical: list[Element] = []
    for (e_type, _norm), group in by_key.items():
        canonical.append(_pick_canonical(group))

    # Stage 2: within the same type, merge anything with IoU > threshold.
    canonical, ambiguities = _merge_by_iou(canonical, iou_threshold)

    return canonical, ambiguities


def _pick_canonical(group: list[tuple[Element, dict]]) -> Element:
    """Group is a list of (Element, crop_box) for the same (type, name).
    Pick the canonical record:
      - highest confidence first
      - among ties, the one whose bbox sits most centrally in its tile
      - merge tile_sources from all duplicates
    """
    def score(item):
        elem, crop = item
        return (
            confidence_rank(elem.confidence),
            edge_distance(elem.global_bbox, crop),
            len(elem.description),
        )

    group_sorted = sorted(group, key=score, reverse=True)
    chosen, _ = group_sorted[0]
    chosen.tile_sources = sorted({
        t for elem, _ in group for t in elem.tile_sources
    })
    return chosen


def _merge_by_iou(
    elements: list[Element], threshold: float
) -> tuple[list[Element], list[dict]]:
    """Within the same type, merge elements with overlapping global_bboxes.
    Records remaining cross-name overlaps as ambiguities."""
    out: list[Element] = []
    ambiguities: list[dict] = []
    used = [False] * len(elements)

    # Group by type so we don't merge a "component" with an "event"
    by_type: dict[str, list[int]] = {}
    for idx, e in enumerate(elements):
        by_type.setdefault(e.type, []).append(idx)

    for e_type, idxs in by_type.items():
        for i_pos, i in enumerate(idxs):
            if used[i]:
                continue
            cluster = [i]
            for j in idxs[i_pos + 1:]:
                if used[j]:
                    continue
                a, b = elements[i].global_bbox, elements[j].global_bbox
                if a and b and iou(a, b) >= threshold:
                    cluster.append(j)
            if len(cluster) == 1:
                out.append(elements[i])
                used[i] = True
                continue
            # Merge cluster: keep highest-confidence representative,
            # merge tile_sources, record name disagreement as ambiguity.
            cluster_elems = [elements[k] for k in cluster]
            primary = max(cluster_elems,
                          key=lambda e: (confidence_rank(e.confidence),
                                         len(e.description)))
            primary.tile_sources = sorted({
                t for ce in cluster_elems for t in ce.tile_sources
            })
            other_names = [ce.name for ce in cluster_elems if ce.name != primary.name]
            if other_names:
                ambiguities.append({
                    "kind": "spatial_overlap_with_different_names",
                    "type": e_type,
                    "canonical_name": primary.name,
                    "alternate_names": other_names,
                    "global_bbox": primary.global_bbox,
                })
            out.append(primary)
            for k in cluster:
                used[k] = True

    return out, ambiguities


# --- Sorting --------------------------------------------------------------


def sort_canonical(elements: list[Element], layout: str) -> list[Element]:
    layout = (layout or "").lower()
    if layout in {"left-to-right", "lr", "horizontal"}:
        keyf = lambda e: (e.global_bbox["x"] if e.global_bbox else 0,
                          e.global_bbox["y"] if e.global_bbox else 0,
                          e.name)
    elif layout in {"top-to-bottom", "tb", "vertical"}:
        keyf = lambda e: (e.global_bbox["y"] if e.global_bbox else 0,
                          e.global_bbox["x"] if e.global_bbox else 0,
                          e.name)
    else:
        # Reading order (y, then x), and finally alphabetical for
        # elements without bboxes.
        keyf = lambda e: (
            e.global_bbox["y"] if e.global_bbox else 9_999_999,
            e.global_bbox["x"] if e.global_bbox else 9_999_999,
            e.name,
        )
    return sorted(elements, key=keyf)


# --- Markdown rendering ---------------------------------------------------

CONTENT_CATEGORY = {
    "architecture": "architecture-diagram",
    "event-storm":  "event-storming-big-picture",
    "process":      "process-diagram",
    "domain":       "domain-model",
    "conceptual":   "conceptual",
}


def render_markdown(
    *,
    title: str,
    source_image: str,
    strategy: str,
    structural_map: dict,
    canonical: list[Element],
    ambiguities: list[dict],
    detail_manifest: dict,
    overview_manifest: dict | None,
) -> str:
    layout = (structural_map or {}).get("layout") or "unspecified"
    diagram_type = (structural_map or {}).get("diagram_type") or strategy

    confidences = [e.confidence for e in canonical]
    high = sum(1 for c in confidences if c == "high")
    med = sum(1 for c in confidences if c == "medium")
    low = sum(1 for c in confidences if c == "low")

    if not canonical:
        overall_confidence = "low"
    elif high >= len(canonical) * 0.6:
        overall_confidence = "high"
    elif low > med + high:
        overall_confidence = "low"
    else:
        overall_confidence = "medium"

    front = {
        "title": title,
        "source-file": source_image,
        "content-type": "image",
        "content-category": CONTENT_CATEGORY.get(strategy, strategy),
        "ingestion-date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "diagram-type": diagram_type,
        "processing": {
            "strategy": "two-pass-sliding-window",
            "extraction-strategy": strategy,
            "viewport": detail_manifest.get("viewport"),
            "stride": detail_manifest.get("stride"),
            "overlap-pct": detail_manifest.get("overlap_pct"),
            "tile-count": len(detail_manifest.get("tiles", [])),
        },
        "ingestion-quality": {
            "extraction-confidence": overall_confidence,
            "elements-by-confidence": {"high": high, "medium": med, "low": low},
            "ambiguity-count": len(ambiguities),
            "requires-review": len(ambiguities) > 0 or not canonical,
        },
    }

    yaml = _yaml_block(front)

    # Markdown body — group by element type for readability.
    by_type: dict[str, list[Element]] = {}
    for e in canonical:
        by_type.setdefault(e.type, []).append(e)

    body_parts = [f"# {title}\n"]
    body_parts.append("## Overview\n")
    summary = (structural_map or {}).get("summary") or (
        f"Auto-extracted {len(canonical)} elements across "
        f"{len(detail_manifest.get('tiles', []))} tiles using the "
        f"`{strategy}` strategy."
    )
    body_parts.append(summary + "\n")

    body_parts.append("## Diagram Type\n")
    body_parts.append(f"{diagram_type}. Layout: {layout}.\n")

    body_parts.append("## Elements\n")
    for e_type in sorted(by_type):
        body_parts.append(f"### {e_type.title()}\n")
        body_parts.append("| # | Name | Description | Source Tiles | Confidence |")
        body_parts.append("|---|------|-------------|--------------|------------|")
        for i, e in enumerate(by_type[e_type], 1):
            tiles = ", ".join(e.tile_sources) or "-"
            body_parts.append(
                f"| {i} | {_md_escape(e.name)} | "
                f"{_md_escape(e.description)} | {tiles} | {e.confidence} |"
            )
        body_parts.append("")

    if ambiguities:
        body_parts.append("## Ambiguities and Review Items\n")
        for a in ambiguities:
            if a["kind"] == "spatial_overlap_with_different_names":
                body_parts.append(
                    f"- Spatial overlap (`{a['type']}`): kept "
                    f"`{_md_escape(a['canonical_name'])}`, also seen as "
                    + ", ".join(f"`{_md_escape(n)}`" for n in a["alternate_names"])
                    + "."
                )
        body_parts.append("")

    return yaml + "\n" + "\n".join(body_parts) + "\n"


def _yaml_block(d: dict) -> str:
    """Minimal YAML emitter for our flat-with-one-level-of-nesting frontmatter.
    No unicode quoting heroics, no anchors, no multi-line strings."""
    lines = ["---"]
    _emit(d, lines, 0)
    lines.append("---")
    return "\n".join(lines)


def _emit(d: dict, lines: list[str], indent: int) -> None:
    pad = "  " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            lines.append(f"{pad}{k}:")
            _emit(v, lines, indent + 1)
        elif isinstance(v, bool):
            lines.append(f"{pad}{k}: {'true' if v else 'false'}")
        elif v is None:
            lines.append(f"{pad}{k}: null")
        elif isinstance(v, (int, float)):
            lines.append(f"{pad}{k}: {v}")
        else:
            # Escape backslashes first so we don't double-escape the
            # backslash inserted by the quote-escape on the next line.
            s = str(v).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{pad}{k}: "{s}"')


def _md_escape(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


# --- CLI ------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(
        prog="reconcile.py",
        description="Merge per-tile image extractions into one canonical "
                    "JSON + Markdown document.",
    )
    p.add_argument("--manifest", type=Path, required=True,
                   help="detail_manifest.json from split_image.py detail.")
    p.add_argument("--extractions", type=Path, required=True,
                   help="Per-tile extractions JSON written by the agent.")
    p.add_argument("--strategy", required=True,
                   choices=("architecture", "event-storm", "process",
                            "domain", "conceptual"),
                   help="Extraction strategy used for the tile reads.")
    p.add_argument("--overview-manifest", type=Path, default=None,
                   help="Optional overview_manifest.json (informational).")
    p.add_argument("--title", default=None,
                   help="Document title. Defaults to source image basename.")
    p.add_argument("--output-json", type=Path, required=True)
    p.add_argument("--output-md", type=Path, required=True)
    p.add_argument("--iou-threshold", type=float, default=0.5,
                   help="IoU threshold for spatial dedup (default 0.5).")
    args = p.parse_args()

    detail = _load_json(args.manifest)
    extractions = _load_json(args.extractions)
    overview = _load_json(args.overview_manifest) if args.overview_manifest else None

    tiles = {t["filename"].rsplit(".", 1)[0]: t
             for t in detail.get("tiles", [])}
    # Also accept tile ids of the form "W0_R0_C0" (basename without extension)
    # or full filename.
    def resolve_tile(tile_id: str) -> dict | None:
        if tile_id in tiles:
            return tiles[tile_id]
        return tiles.get(tile_id.rsplit(".", 1)[0])

    raw_elements: list[tuple[str, dict, dict]] = []
    for rec in extractions.get("tiles", []):
        tile_id = rec.get("tile_id") or rec.get("filename") or ""
        tile = resolve_tile(tile_id)
        if not tile:
            print(f"warning: extraction references unknown tile {tile_id!r}; "
                  f"skipping", file=sys.stderr)
            continue
        for elem in rec.get("elements") or []:
            if isinstance(elem, dict):
                raw_elements.append((tile_id, tile["crop_box"], elem))

    canonical, ambiguities = reconcile_elements(
        raw_elements, iou_threshold=args.iou_threshold,
    )

    structural_map = extractions.get("structural_map") or {}
    canonical = sort_canonical(canonical, structural_map.get("layout") or "")

    source_image = detail.get("source_image", "")
    if args.title:
        title = args.title
    elif source_image:
        title = Path(source_image).stem
    else:
        title = "Diagram"

    merged = {
        "title": title,
        "source_image": source_image,
        "strategy": args.strategy,
        "structural_map": structural_map,
        "elements": [
            {
                "type": e.type,
                "name": e.name,
                "description": e.description,
                "confidence": e.confidence,
                "global_bbox": e.global_bbox,
                "tile_sources": e.tile_sources,
                **({"extra": e.extra} if e.extra else {}),
            }
            for e in canonical
        ],
        "ambiguities": ambiguities,
    }
    args.output_json.write_text(json.dumps(merged, indent=2), encoding="utf-8")

    md = render_markdown(
        title=title,
        source_image=source_image,
        strategy=args.strategy,
        structural_map=structural_map,
        canonical=canonical,
        ambiguities=ambiguities,
        detail_manifest=detail,
        overview_manifest=overview,
    )
    args.output_md.write_text(md, encoding="utf-8")

    print(f"OUTPUT_JSON: {args.output_json}")
    print(f"OUTPUT_MD: {args.output_md}")
    print(f"ELEMENTS: {len(canonical)}")
    print(f"AMBIGUITIES: {len(ambiguities)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
