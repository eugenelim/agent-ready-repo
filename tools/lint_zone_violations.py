#!/usr/bin/env python3
"""
lint_zone_violations.py — scan web/src/ for raw color values used outside
token-definition :root {} blocks.

Flagged patterns (CSS property values, outside :root{}):
  - Bare hex literals: #RGB, #RRGGBB, #RRGGBBAA
  - rgba() calls

Exclusions:
  (a) CSS block comment lines (line starts with /* after stripping whitespace)
  (b) Line-leading // comments (JS/TS comments in Astro frontmatter are always
      line-leading, so a line-leading test is sufficient and avoids per-file
      fence-state tracking)
  (c) :root {} token-definition blocks — boolean toggle, not a depth counter;
      assumes flat, single-line-brace :root blocks (current tokens.css shape:
      two single-line { openings, no nested braces)
  (d) SVG attribute lines (fill=, stroke=, xmlns=, viewBox=, etc.)

Exit 0 = clean, 1 = violations found; prints file:line: <value> per hit.
Usage: python tools/lint_zone_violations.py [path]   (default: web/src/)
"""

import os
import re
import sys

HEX_RE = re.compile(r'#[0-9a-fA-F]{3,8}\b')
RGBA_RE = re.compile(r'\brgba\s*\([^)]*\)')

# SVG attribute keywords — presence means the line is an attribute line, not CSS
SVG_ATTR_KEYWORDS = (
    'fill=', 'stroke=', 'xmlns=', 'viewBox=',
    'x1=', 'y1=', 'x2=', 'y2=',
)


def _violations_in_line(line: str) -> list[str]:
    """Return list of raw color values (hex or rgba) found in the line."""
    found = []
    for m in HEX_RE.finditer(line):
        found.append(m.group())
    for m in RGBA_RE.finditer(line):
        found.append(m.group())
    return found


def lint_file(path: str) -> list[tuple[int, str]]:
    """Return (1-based line number, matched value) violations for the file."""
    violations: list[tuple[int, str]] = []
    inside_root = False  # True while inside a :root {} token block
    with open(path, encoding='utf-8', errors='replace') as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip('\n')
            stripped = line.strip()

            # Blank lines
            if not stripped:
                continue

            # (a) CSS block comment lines
            if stripped.startswith('/*'):
                continue

            # (b) Line-leading // comments (JS/TS in Astro frontmatter)
            if stripped.startswith('//'):
                continue

            # :root { — enters token-definition block (flat-brace assumption)
            if ':root' in line and '{' in line:
                inside_root = True
                continue

            # } — exits the current :root block
            if inside_root and '}' in line:
                inside_root = False
                continue

            # (c) Inside :root {} — token definitions are exempt
            if inside_root:
                continue

            # (d) SVG attribute lines
            if any(kw in line for kw in SVG_ATTR_KEYWORDS):
                continue

            # Check for raw color values
            for val in _violations_in_line(line):
                violations.append((lineno, val))

    return violations


def main() -> int:
    scan_root = sys.argv[1] if len(sys.argv) > 1 else 'web/src/'
    total = 0
    for dirpath, _dirs, filenames in os.walk(scan_root):
        for fname in sorted(filenames):
            if not (fname.endswith('.astro') or fname.endswith('.css')):
                continue
            fpath = os.path.join(dirpath, fname)
            for lineno, val in lint_file(fpath):
                print(f'{fpath}:{lineno}: {val}')
                total += 1
    return 1 if total > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
