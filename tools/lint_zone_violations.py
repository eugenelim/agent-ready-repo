#!/usr/bin/env python3
"""Zone-violation lint.

Scans web/src/ for raw hex or rgba() values used as CSS property values
outside :root token-definition blocks.

Exit 0: clean. Exit 1: violations found (printed as file:line: <value>).
Exit 2: invalid invocation (scan root does not exist or is not a directory).

Assumptions:
- The :root exemption applies only to the canonical token file at
  <root>/styles/tokens.css (computed from the scan root in main). :root blocks
  in any other .astro or .css file are NOT exempt — they should not define raw
  color values. The exemption is restricted to the single canonical path, not
  any file named tokens.css.
- :root blocks in tokens.css use flat single-line-brace form (two ':root {'
  openings, no nested braces). in_root_block is a boolean toggle, not a
  depth counter.
- JS/TS comments in Astro frontmatter are always line-leading (^\\s*//).
- CSS property values may appear on continuation lines when the declaration
  spans multiple lines (e.g. background-image: followed by gradient values on
  the next lines). in_declaration tracks state through the terminating semicolon.
  Hex values are scanned per-line; rgba()/rgb() values are accumulated into
  decl_buffer and scanned against the full declaration text at close, so splits
  across lines are also detected. Inline single-line rules like
  '.foo { color: #hex; }' are not detected — the codebase doesn't use this format.
- CSS hex colors of valid lengths (3, 4, 6, 8 digits) are all matched. The regex
  uses an explicit alternation to avoid matching 5/7-digit strings.
- Inline block comments on a value line (e.g. `color: var(--x); /* old: #fff */`)
  are stripped from the value before scanning so commented-out raw values do not
  produce false positives. Unclosed /* causes truncation and enters block-comment state.
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

HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})\b")
RGBA_RE = re.compile(r"\brgba?\s*\([^)]*\)")

TOKEN_FILE = "tokens.css"
CSS_INLINE_COMMENT_RE = re.compile(r"/\*.*?\*/")
ROOT_OPEN_RE = re.compile(r":root\b")
CSS_PROP_RE = re.compile(r"^\s*[-\w]+\s*:")
CSS_BLOCK_COMMENT_OPEN_RE = re.compile(r"^\s*/\*")
CSS_BLOCK_COMMENT_CLOSE = "*/"
JS_LINE_COMMENT_RE = re.compile(r"^\s*//")
SVG_ATTR_RE = re.compile(
    r"^\s*(?:fill|stroke|xmlns|viewBox|x|y|width|height|rx|ry|d|transform|"
    r"preserveAspectRatio)\s*="
)


def _strip_inline_comment(text: str) -> tuple[str, bool]:
    """Strip closed /* ... */ comments; return (stripped_text, unclosed_comment_found)."""
    text = CSS_INLINE_COMMENT_RE.sub("", text)
    if "/*" in text:
        return text[: text.index("/*")], True
    return text, False


def scan_file(path: Path, is_token_file: bool = False) -> list[tuple[int, str]]:
    """Scan a single file for raw color values used as CSS property values."""
    violations: list[tuple[int, str]] = []
    in_root_block = False  # only active when is_token_file
    in_block_comment = False
    in_declaration = False  # True when a CSS value continues on the next line(s)
    decl_buffer = ""  # accumulated declaration value for multi-line rgba detection

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

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

        # :root block exemption — restricted to the canonical token file only.
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

        # Multi-line declaration continuation: hex is scanned per-line; rgba()/rgb()
        # values are accumulated into decl_buffer and matched against the full text
        # at close so cross-line splits (e.g. rgba(\n  0,0,0,\n  0.5\n)) are detected.
        # Inline comments are stripped before scanning so commented-out values are excluded.
        if in_declaration:
            stripped, started_comment = _strip_inline_comment(line)
            if started_comment:
                in_block_comment = True
            decl_buffer += " " + stripped.strip()
            for m in HEX_RE.finditer(stripped):
                violations.append((lineno, m.group()))
            if ";" in stripped or "{" in stripped or "}" in stripped or started_comment:
                for m in RGBA_RE.finditer(decl_buffer):
                    violations.append((lineno, m.group()))
                in_declaration = False
                decl_buffer = ""
            continue

        if not CSS_PROP_RE.match(line):
            if "{" in line or "}" in line:
                in_declaration = False
                decl_buffer = ""
            continue

        # Extract value part (after the first colon on the line); strip inline comments.
        colon_idx = line.index(":")
        value_part, started_comment = _strip_inline_comment(line[colon_idx + 1 :])
        if started_comment:
            in_block_comment = True

        for m in HEX_RE.finditer(value_part):
            violations.append((lineno, m.group()))

        if ";" in value_part or started_comment:
            # Single-line value (or comment truncated it): scan rgba immediately.
            for m in RGBA_RE.finditer(value_part):
                violations.append((lineno, m.group()))
        else:
            # Multi-line value: accumulate buffer; rgba scanned when declaration closes.
            in_declaration = True
            decl_buffer = value_part

    return violations


def main() -> None:
    """Walk the scan root and report raw color values outside the canonical token file."""
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("web/src")

    if not root.exists() or not root.is_dir():
        print(f"error: scan root does not exist or is not a directory: {root}", file=sys.stderr)
        sys.exit(2)

    # Only the canonical token file may define raw color values in :root blocks.
    canonical_token = root / "styles" / "tokens.css"

    violations_found = False
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in FILE_EXTS:
            try:
                for lineno, value in scan_file(path, is_token_file=(path == canonical_token)):
                    print(f"{path}:{lineno}: {value}")
                    violations_found = True
            except OSError as exc:
                print(f"error: cannot read {path}: {exc}", file=sys.stderr)
                sys.exit(2)

    sys.exit(1 if violations_found else 0)


if __name__ == "__main__":
    main()
