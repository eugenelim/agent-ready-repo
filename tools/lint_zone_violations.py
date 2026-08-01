#!/usr/bin/env python3
"""Zone-violation lint.

Scans web/src/ for raw hex or rgba() values used as CSS property values
outside :root token-definition blocks.

Exit 0: clean. Exit 1: violations found (printed as file:line: <value>).
Exit 2: invalid invocation (scan root does not exist or is not a directory).

Assumptions:
- The :root exemption applies only to tokens.css, which is the canonical
  token-definition file. :root blocks in other .astro or .css files are
  NOT exempt — they should not define raw color values.
- :root blocks in tokens.css use flat single-line-brace form (two ':root {'
  openings, no nested braces). in_root_block is a boolean toggle, not a
  depth counter.
- JS/TS comments in Astro frontmatter are always line-leading (^\\s*//).
- CSS property values are on their own lines (multi-line formatting), which
  is the convention throughout web/src/. Inline rules like '.foo { color: #hex; }'
  on a single line are not detected — the codebase doesn't use this format.
- Astro frontmatter (JS/TS between --- fences) is scanned as-is. A frontmatter
  object property on its own line that happens to look like a CSS property (e.g.
  `color: "#hex",`) would be flagged. AC9 holds because web/src/ frontmatter uses
  only patterns that don't match CSS_PROP_RE (e.g. object literals starting with
  '{', or values that contain no raw hex).
"""

import re
import sys
from pathlib import Path

FILE_EXTS = {".astro", ".css"}

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,6}\b")
RGBA_RE = re.compile(r"\brgba?\s*\([^)]*\)")

TOKEN_FILE = "tokens.css"
ROOT_OPEN_RE = re.compile(r":root\b")
CSS_PROP_RE = re.compile(r"^\s*[-\w]+\s*:")
CSS_BLOCK_COMMENT_OPEN_RE = re.compile(r"^\s*/\*")
CSS_BLOCK_COMMENT_CLOSE = "*/"
JS_LINE_COMMENT_RE = re.compile(r"^\s*//")
SVG_ATTR_RE = re.compile(
    r"^\s*(?:fill|stroke|xmlns|viewBox|x|y|width|height|rx|ry|d|transform|"
    r"preserveAspectRatio)\s*="
)


def scan_file(path: Path) -> list[tuple[int, str]]:
    violations: list[tuple[int, str]] = []
    in_root_block = False  # only active for tokens.css
    in_block_comment = False
    is_token_file = path.name == TOKEN_FILE

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    for lineno, line in enumerate(lines, start=1):
        if not line.strip():
            continue

        # Multi-line CSS block comment tracking: once inside /* ... */,
        # skip all continuation lines until the closing */ is seen.
        if in_block_comment:
            if CSS_BLOCK_COMMENT_CLOSE in line:
                in_block_comment = False
            continue

        if CSS_BLOCK_COMMENT_OPEN_RE.match(line):
            if CSS_BLOCK_COMMENT_CLOSE not in line:
                in_block_comment = True
            continue

        if JS_LINE_COMMENT_RE.match(line):
            continue

        # :root block exemption — restricted to tokens.css only.
        if is_token_file:
            if ROOT_OPEN_RE.search(line) and "{" in line:
                in_root_block = True
                continue
            if in_root_block:
                if "}" in line:
                    in_root_block = False
                continue  # skip all lines inside :root (including the closing })

        if SVG_ATTR_RE.match(line):
            continue

        if not CSS_PROP_RE.match(line):
            continue

        # Extract value part (after the first colon on the line)
        colon_idx = line.index(":")
        value_part = line[colon_idx + 1 :]

        for m in HEX_RE.finditer(value_part):
            violations.append((lineno, m.group()))
        for m in RGBA_RE.finditer(value_part):
            violations.append((lineno, m.group()))

    return violations


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("web/src")

    if not root.exists() or not root.is_dir():
        print(f"error: scan root does not exist or is not a directory: {root}", file=sys.stderr)
        sys.exit(2)

    violations_found = False
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in FILE_EXTS:
            for lineno, value in scan_file(path):
                print(f"{path}:{lineno}: {value}")
                violations_found = True

    sys.exit(1 if violations_found else 0)


if __name__ == "__main__":
    main()
