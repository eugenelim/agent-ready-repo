"""Render Mermaid diagrams embedded in a Markdown file to images.

Walks the input Markdown for ``` ```mermaid ``` fenced blocks, calls
the Mermaid CLI (``mmdc``) to render each one to PNG (or SVG), and
writes a rewritten Markdown file where every fence has been replaced
by an image reference. The original input file is not modified.

Invocation examples:

    python scripts/render_mermaid.py --check
    python scripts/render_mermaid.py --input report.md
    python scripts/render_mermaid.py --input arch.md --output-dir ./out --format svg --theme forest

Exit codes:
- 0  success (or check passed)
- 2  user action required (mmdc missing, input missing, bad args)
- 1  one or more diagrams failed to render

Design adapted from SpillwaveSolutions' mastering-confluence-agent-skill
(MIT-licensed); reshaped for the markdown-walk + rewrite use case
(theirs is single-file or extract-only).
"""
from __future__ import annotations

import argparse
import logging
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

log = logging.getLogger("mermaid_renderer")

EXIT_OK = 0
EXIT_USER_ACTION = 2
EXIT_PARTIAL = 1

# Captures the body of a ```mermaid fenced block. Group 1 = whitespace
# trailing the language tag (info string); Group 2 = the diagram source.
_MERMAID_FENCE_RE = re.compile(
    r"^```mermaid[ \t]*\n(.*?)\n```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)

VALID_FORMATS = ("png", "svg")
VALID_THEMES = ("default", "forest", "dark", "neutral")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--check", action="store_true",
                        help="Verify mmdc is on PATH; exit 0 or 2")
    parser.add_argument("--input", help="Source Markdown file")
    parser.add_argument("--output-dir", type=Path, default=Path("./mermaid-out"),
                        help="Output directory for images and rewritten Markdown (default: ./mermaid-out)")
    parser.add_argument("--format", choices=VALID_FORMATS, default="png",
                        help="Output image format (default: png)")
    parser.add_argument("--theme", choices=VALID_THEMES, default="default",
                        help="Mermaid theme (default: default)")
    parser.add_argument("--background", default="white",
                        help="Background colour (e.g. white, transparent, #f0f0f0)")
    parser.add_argument("--prefix", default="mermaid",
                        help="Output filename prefix (default: mermaid)")
    parser.add_argument("--width", type=int, help="Output width in pixels")
    parser.add_argument("--height", type=int, help="Output height in pixels")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    return parser.parse_args(argv)


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def check_mmdc() -> bool:
    """Return True if `mmdc` is callable on PATH."""
    if shutil.which("mmdc") is None:
        return False
    try:
        result = subprocess.run(
            ["mmdc", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def extract_mermaid_blocks(markdown_text: str) -> list[str]:
    """Return diagram sources in document order."""
    return [m.group(1) for m in _MERMAID_FENCE_RE.finditer(markdown_text)]


def render_one(
    *,
    diagram_source: str,
    output_path: Path,
    format: str,
    theme: str,
    background: str,
    width: int | None,
    height: int | None,
) -> tuple[bool, str]:
    """Render a single diagram. Returns (ok, stderr)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".mmd", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(diagram_source)
        tmp_path = Path(fh.name)
    try:
        cmd = [
            "mmdc",
            "-i", str(tmp_path),
            "-o", str(output_path),
            "-t", theme,
            "-b", background,
            "-e", format,
        ]
        if width:
            cmd.extend(["-w", str(width)])
        if height:
            cmd.extend(["-H", str(height)])
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return False, result.stderr.strip() or result.stdout.strip()
        return True, ""
    finally:
        tmp_path.unlink(missing_ok=True)


def rewrite_markdown(
    markdown_text: str,
    successes: dict[int, str],
) -> str:
    """Replace each ```mermaid fence with an image ref when its index is in `successes`.

    `successes` maps zero-based block index → image filename (basename).
    Blocks not in the map are left intact (they failed to render or
    were intentionally skipped).
    """
    counter = {"i": 0}

    def sub(match: re.Match[str]) -> str:
        idx = counter["i"]
        counter["i"] += 1
        filename = successes.get(idx)
        if filename is None:
            return match.group(0)
        return f"![{filename}]({filename})"

    return _MERMAID_FENCE_RE.sub(sub, markdown_text)


def _check(args: argparse.Namespace) -> int:
    if check_mmdc():
        print("OK: mmdc is on PATH")
        return EXIT_OK
    print(
        "NEED-INPUT: mmdc not found on PATH. Install with: "
        "`npm install -g @mermaid-js/mermaid-cli`",
        file=sys.stderr,
    )
    return EXIT_USER_ACTION


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _configure_logging(args.verbose)

    if args.check:
        return _check(args)

    if not check_mmdc():
        print(
            "NEED-INPUT: mmdc not found on PATH. Install with: "
            "`npm install -g @mermaid-js/mermaid-cli`",
            file=sys.stderr,
        )
        return EXIT_USER_ACTION

    if not args.input:
        print("ERROR: --input is required", file=sys.stderr)
        return EXIT_USER_ACTION

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return EXIT_USER_ACTION

    # The rewritten Markdown is named after the input basename and
    # dropped in --output-dir. Refuse when that resolves back onto the
    # input — silent overwrite breaks the "original is not modified"
    # promise.
    rewritten_target = (args.output_dir / input_path.name).resolve()
    if rewritten_target == input_path.resolve():
        print(
            f"ERROR: --output-dir {args.output_dir} would overwrite the "
            f"input file {input_path}. Pick a different output directory.",
            file=sys.stderr,
        )
        return EXIT_USER_ACTION

    markdown_text = input_path.read_text(encoding="utf-8")
    blocks = extract_mermaid_blocks(markdown_text)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    successes: dict[int, str] = {}
    failures: list[int] = []
    for i, source in enumerate(blocks):
        filename = f"{args.prefix}-{i + 1}.{args.format}"
        out_path = args.output_dir / filename
        ok, err = render_one(
            diagram_source=source,
            output_path=out_path,
            format=args.format,
            theme=args.theme,
            background=args.background,
            width=args.width,
            height=args.height,
        )
        if ok:
            successes[i] = filename
            log.info("rendered %s", filename)
        else:
            failures.append(i)
            err_path = args.output_dir / f"{args.prefix}-{i + 1}.error.txt"
            err_path.write_text(err + "\n", encoding="utf-8")
            log.warning("diagram %d failed: %s", i + 1, err[:200])

    rewritten = rewrite_markdown(markdown_text, successes)
    out_md = args.output_dir / input_path.name
    out_md.write_text(rewritten, encoding="utf-8")

    print(f"OUTPUT_DIR: {args.output_dir.resolve()}")
    print(f"REWRITTEN: {out_md.resolve()}")
    print(f"DIAGRAMS: {len(blocks)}")
    if failures:
        print(f"FAILED: {len(failures)}", file=sys.stderr)
        return EXIT_PARTIAL
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
