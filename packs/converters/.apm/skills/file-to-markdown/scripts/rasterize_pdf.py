#!/usr/bin/env python3
"""
rasterize_pdf.py — render a scanned / image-only PDF's pages to PNGs so the
in-session model can read them (Tier 1, agent-vision).

This is the concrete path the Tier-0 floor's sparse-text escalation
(``escalation-target: 1-agent-vision``) points at: when ``convert.py`` finds a PDF
has little or no digital text layer, the agent runs this script to render each
page, reads the page images, and reconciles them through the general
(``text-table``) strategy.

Dependency posture (load-bearing):
  * The rasterizer is **``pdf2image``** — MIT-licensed. It wraps a **system
    Poppler** binary (``pdftoppm`` / ``pdftocairo``) invoked as a *separate
    process*: Poppler is GPL, but separate-process invocation carries no licence
    propagation to this MIT Python dependency. ``pymupdf`` is deliberately **not**
    used — it is AGPL.
  * It is resolved **pip-on-demand via ``--check``** (a pinned floor version in
    ``PIP_INSTALL``), never auto-installed, and it is **not** a hard ``pack.toml``
    dep. Because it resolves at runtime it sits outside lockfile SCA — the pin and
    this note are the compensating control.
  * When the library or its Poppler backend is absent this script exits with a
    clear, actionable, **no-crash** message. Retaining the already-written Tier-0
    ``.md`` is the *agent's* responsibility (per SKILL.md), not this script's — a
    standalone script has no access to ``convert.py``'s result.

No network egress. No installed OCR/ML model — the "vision" is the agent's own
in-session read of the rendered image, done after this script runs.

Usage:
    python scripts/rasterize_pdf.py --input scan.pdf --output-dir work/
    python scripts/rasterize_pdf.py --check          # probe pdf2image

Output (on success): page PNGs (``page-0001.png`` …) + ``detail_manifest.json``
in the output dir, ready for the text-table read + ``reconcile.py``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NamedTuple

import safe_io

PIP_INSTALL = "python -m pip install 'pdf2image>=1.17.0'"  # MIT; needs system poppler

# Multi-axis rasterization ceiling — resource-exhaustion bounds. Calibrated for
# rasterization cost, which is far higher than reading a PDF's text layer, so the
# page cap is deliberately LOW (hundreds), NOT convert.py's MAX_PDF_PAGES = 5000.
MAX_RASTER_PAGES = 200                         # coarse page cap
RENDER_DPI = 150                               # capped DPI
MAX_TOTAL_OUTPUT_BYTES = 500 * 1024 * 1024     # cumulative rendered-PNG byte cap
# Per-page pixel cap. PDF *page dimensions* are attacker-controlled (a page can
# be hundreds of inches), so a capped DPI alone does NOT bound per-page pixels —
# Poppler renders in a subprocess, so Pillow's own decompression-bomb guard never
# fires here. This is the dimension axis. 100 MP admits large-format (A0-ish)
# pages while refusing the pathological hundreds-of-inches case.
MAX_PAGE_PIXELS = 100_000_000


class RasterizeResult(NamedTuple):
    status: str                 # "ok" | "unavailable" | "refused"
    message: str
    manifest_path: Path | None = None
    page_paths: tuple[Path, ...] = ()


def _lib_available(name: str = "pdf2image") -> bool:
    import importlib.util

    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return name in sys.modules


def cmd_check(names: list[str]) -> int:
    """Probe pdf2image; exit 0 if present, 2 if absent (mirrors convert.py)."""
    targets = names or ["pdf2image"]
    missing = False
    for name in targets:
        present = _lib_available(name)
        print(f"{name}: {'present' if present else 'absent'}")
        if not present:
            missing = True
            print(f"  install: {PIP_INSTALL}  (also needs a system poppler: "
                  f"pdftoppm/pdftocairo)", file=sys.stderr)
    return 2 if missing else 0


def _page_count(pdf_path: Path) -> int:
    import pdf2image

    info = pdf2image.pdfinfo_from_path(str(pdf_path))
    return int(info.get("Pages", 0))


def _cleanup(paths: list[Path]) -> None:
    """Remove partial page PNGs written before a mid-render ceiling refusal, so a
    retry against the same work dir doesn't start dirty."""
    for p in paths:
        try:
            p.unlink()
        except OSError:
            pass


def rasterize(
    pdf_path: Path,
    output_dir: Path,
    *,
    output_root: Path | None = None,
    dpi: int = RENDER_DPI,
    max_pages: int = MAX_RASTER_PAGES,
    max_total_bytes: int = MAX_TOTAL_OUTPUT_BYTES,
    max_page_pixels: int = MAX_PAGE_PIXELS,
) -> RasterizeResult:
    """Render each page of ``pdf_path`` to a PNG under a confined work dir.

    Bounds on three axes (AC10): a capped render DPI (``dpi`` — bounds per-page
    pixels), a cumulative output-byte ceiling across pages, and a coarse page cap.
    Degrades honestly (``status="unavailable"``, no crash) when pdf2image / Poppler
    is absent."""
    dpi = min(dpi, RENDER_DPI)   # the per-page-pixel ceiling lives here, not in the CLI
    if not _lib_available("pdf2image"):
        return RasterizeResult(
            "unavailable",
            "Tier-1 PDF rasterization needs `pdf2image` (MIT) + a system poppler, "
            f"which is not installed. Install it (`{PIP_INSTALL}`, plus poppler) to "
            "read a scanned PDF via agent-vision, or keep the Tier-0 output and "
            "review it. (The agent retains the Tier-0 .md; this step is skipped.)",
        )

    import pdf2image

    # Confine the work dir under a caller-controlled root (default: its own
    # parent). Page images and the manifest are written only inside it.
    root = output_root if output_root is not None else output_dir.parent
    try:
        out_dir = safe_io.confine(output_dir, root)
    except ValueError as exc:
        return RasterizeResult("refused", f"output dir confinement: {exc}")
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        n_pages = _page_count(pdf_path)
    except Exception as exc:  # PDFInfoNotInstalledError / PopplerNotInstalledError / …
        return RasterizeResult(
            "unavailable",
            f"could not read the PDF with pdf2image/poppler ({exc}). Confirm poppler "
            f"is installed (`{PIP_INSTALL}`, plus a system poppler). The agent "
            "retains the Tier-0 output.",
        )

    if n_pages > max_pages:
        return RasterizeResult(
            "refused",
            f"PDF has {n_pages} pages, over the {max_pages}-page rasterization "
            f"ceiling; refusing to rasterize unbounded — split the PDF or raise "
            f"the cap deliberately. Flagged requires-review.",
        )

    tiles: list[dict] = []
    page_paths: list[Path] = []
    total_bytes = 0
    for i in range(1, n_pages + 1):
        images = pdf2image.convert_from_path(
            str(pdf_path), dpi=dpi, first_page=i, last_page=i, fmt="png",
        )
        if not images:
            continue
        img = images[0]
        w, h = img.size
        # Per-page pixel ceiling — the dimension axis. Checked before saving so a
        # pathological page neither lands on disk nor accumulates.
        if w * h > max_page_pixels:
            _cleanup(page_paths)
            return RasterizeResult(
                "refused",
                f"page {i} renders to {w}x{h} = {w * h} px, over the "
                f"{max_page_pixels}-px per-page ceiling; refusing (pathological "
                f"page dimensions). Flagged requires-review.",
            )
        fname = f"page-{i:04d}.png"                 # generated, never from input
        dest = safe_io.confine(out_dir / fname, out_dir)
        img.save(str(dest), format="PNG")
        size = dest.stat().st_size
        total_bytes += size
        if total_bytes > max_total_bytes:
            _cleanup(page_paths + [dest])
            return RasterizeResult(
                "refused",
                f"cumulative rendered output exceeds the {max_total_bytes}-byte "
                f"ceiling at page {i}; refusing to rasterize unbounded (pages may "
                f"be pathologically large). Flagged requires-review.",
            )
        page_paths.append(dest)
        tiles.append({
            "filename": fname,
            "tile_id": f"page-{i:04d}",
            "page": i,
            "row": 0,
            "col": 0,
            "crop_box": {"x": 0, "y": 0, "w": int(w), "h": int(h)},
            "source": "rasterized_pdf",
        })

    manifest = {
        "mode": "rasterized-pdf",
        "source_pdf": str(pdf_path),
        "dpi": dpi,
        "total_pages": n_pages,
        "tiles": tiles,
    }
    manifest_path = safe_io.confine(out_dir / "detail_manifest.json", out_dir)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return RasterizeResult("ok", f"rasterized {len(page_paths)} page(s)",
                           manifest_path, tuple(page_paths))


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "--check":
        return cmd_check(args[1:])

    p = argparse.ArgumentParser(
        prog="rasterize_pdf.py",
        description="Render a scanned/image-only PDF's pages to PNGs for the "
                    "Tier-1 agent-vision (text-table) read.",
    )
    p.add_argument("--input", type=Path, required=True, help="PDF to rasterize.")
    p.add_argument("--output-dir", type=Path, required=True,
                   help="Work dir for the page PNGs + manifest.")
    p.add_argument("--output-root", type=Path, default=None,
                   help="Confinement root for the work dir (default: its parent).")
    p.add_argument("--dpi", type=int, default=RENDER_DPI,
                   help=f"Render DPI (default/capped {RENDER_DPI}).")
    a = p.parse_args(args)

    if not a.input.exists():
        print(f"ERROR: File not found: {a.input}", file=sys.stderr)
        return 1

    res = rasterize(a.input, a.output_dir, output_root=a.output_root, dpi=a.dpi)
    if res.status == "ok":
        print(f"MANIFEST: {res.manifest_path}")
        print(f"PAGES: {len(res.page_paths)}")
        print("Read each page image with the `text-table` strategy, then run "
              "reconcile.py --strategy text-table.")
        return 0
    if res.status == "unavailable":
        print(f"WARNING: {res.message}", file=sys.stderr)
        return 3
    print(f"ERROR: {res.message}", file=sys.stderr)      # refused (ceiling)
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
