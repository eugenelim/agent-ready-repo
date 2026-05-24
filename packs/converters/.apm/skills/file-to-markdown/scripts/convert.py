#!/usr/bin/env python3
"""
convert.py — Convert documents and images to Markdown using Docling.

Supports: PDF, DOCX, PPTX, XLSX, XLS, PNG, JPG, JPEG, TIFF, BMP, WEBP, GIF

Usage:
    python scripts/convert.py <file> [file2 ...]

Output:
    <input-basename>.md written to the same directory as the input file.

Stdout markers (for agent parsing):
    OUTPUT: <path>   — path to the written Markdown file
    LINES: <n>       — line count of the output
    WORDS: <n>       — word count of the output
    WARNING: <msg>   — non-fatal issue

Errors go to stderr; exit code 1 on failure.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SUPPORTED = {".pdf", ".docx", ".pptx", ".xlsx", ".xls",
             ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".gif"}

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".gif"}

# Images wider or taller than this are pre-scaled before Docling processes them.
MAX_IMAGE_DIM = 4000


def prescale_image(input_path: Path, tmp_dir: str) -> Path:
    """Return a pre-scaled copy of the image if it exceeds MAX_IMAGE_DIM, else the original."""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None  # disable decompression bomb check for the resize step

    with Image.open(input_path) as img:
        w, h = img.size
        if max(w, h) <= MAX_IMAGE_DIM:
            return input_path

        scale = MAX_IMAGE_DIM / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        scaled = img.resize((new_w, new_h), Image.LANCZOS)
        out_path = Path(tmp_dir) / (input_path.stem + "_scaled.png")
        scaled.save(str(out_path), format="PNG")
        return out_path


def convert_file(input_path: Path) -> None:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        print(
            "ERROR: docling is not installed. Run:\n"
            "  pip install docling\n"
            "  uv pip install docling",
            file=sys.stderr,
        )
        sys.exit(1)

    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if input_path.suffix.lower() not in SUPPORTED:
        print(
            f"ERROR: Unsupported file type '{input_path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED))}",
            file=sys.stderr,
        )
        sys.exit(1)

    is_image = input_path.suffix.lower() in IMAGE_EXTS
    tmp_dir = None
    convert_path = input_path

    if is_image:
        tmp_dir = tempfile.mkdtemp()
        convert_path = prescale_image(input_path, tmp_dir)
        if convert_path != input_path:
            from PIL import Image
            with Image.open(input_path) as img:
                orig_w, orig_h = img.size
            with Image.open(convert_path) as img:
                scaled_w, scaled_h = img.size
            print(f"WARNING: image pre-scaled from {orig_w}×{orig_h} to {scaled_w}×{scaled_h} before OCR")

    try:
        converter = DocumentConverter()
        result = converter.convert(str(convert_path))
        markdown = result.document.export_to_markdown()
    finally:
        if tmp_dir:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)

    output_path = input_path.with_suffix(".md")
    output_path.write_text(markdown, encoding="utf-8")

    lines = len(markdown.splitlines())
    words = len(markdown.split())
    print(f"OUTPUT: {output_path}")
    print(f"LINES: {lines}")
    print(f"WORDS: {words}")

    if words < 20:
        print(
            "WARNING: very little text extracted — the file may be image-based "
            "or contain mostly non-text content"
        )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: convert.py <file> [file2 ...]", file=sys.stderr)
        sys.exit(1)

    for arg in sys.argv[1:]:
        try:
            convert_file(Path(arg))
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
