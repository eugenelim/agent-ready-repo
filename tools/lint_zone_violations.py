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
  across lines are also detected. Block comments within a multi-line declaration
  (e.g. `background: /* old */ value;`) do NOT terminate the declaration — the
  state persists through the comment so post-comment values are still scanned.
- Inline rules sharing a selector line (`.selector { property: value; }`) are
  handled by scanning the portion after `{` for property declarations. Nested
  selector levels (e.g. `@keyframes foo { from { color: #fff; } }`) are
  handled by advancing through nested `{` until a CSS property is found.
- When CSS_PROP_RE matches a line but the text after the colon contains `{`,
  the colon belongs to a selector (e.g. `a:hover {` or `body:has(#id) {`),
  not a property. The scanner redirects to inline-rule logic on the portion
  after the `{` rather than scanning the selector text for raw colors.
- When CSS_PROP_RE matches a line but the text after the colon ends with `,`,
  the line is part of a multiline selector list (e.g. `a:hover,` followed by
  `#id {`). The trailing comma is not valid CSS property syntax; skip the line
  to avoid treating the next selector as a declaration continuation.
- url(...) tokens are stripped before scanning for hex values so that SVG
  fragment references (e.g. `filter: url(#fade)`) are not reported as colors.
- Quoted CSS string literals (e.g. `content: '#abc'`) are masked before
  scanning so text inside quotes is not reported as a color value.
- Out of scope: multiline selector lists where a pseudo-class line (e.g.
  `a:hover,`) is followed by an ID-selector line (e.g. `#fade {`). CSS_PROP_RE
  would match `a:` and treat `hover,` as a declaration value; without a full
  CSS parser there is no reliable way to distinguish selector pseudo-classes
  from property values using text heuristics alone. web/src/ does not use this
  selector pattern, so no false positives occur in practice.
- CSS hex colors of valid lengths (3, 4, 6, 8 digits) are all matched. The regex
  uses an explicit alternation to avoid matching 5/7-digit strings.
- Block-comment state is resolved at the start of every line: when inside a block
  comment, code after the closing `*/` on the same line is preserved and processed
  (not discarded). Inline `/* ... */` is then stripped from the entire line before
  any further checks, so trailing comments (/* old: #fff */) and mid-line comment
  openings (.foo { /*) both enter block-comment state correctly without producing
  false positives or false negatives.
- Astro frontmatter (JS/TS between --- fences) is scanned as-is. A frontmatter
  object property on its own line that happens to look like a CSS property (e.g.
  `color: "#hex",`) would be flagged. AC9 holds because web/src/ frontmatter uses
  only patterns that don't match CSS_PROP_RE (e.g. object literals starting with
  '{', or values that contain no raw hex).
- Out of scope: HTML `style` attributes in Astro template markup
  (`<div style="color: #fff">`). Detecting these requires HTML attribute
  parsing across multiple lines, which is outside the line-by-line CSS
  scanner design. web/src/ components use CSS custom properties via class
  names, not inline style attributes.
- Out of scope: directory-enumeration PermissionError from Path.rglob().
  The scanner exits 2 on OSError *reading* a file; enumeration errors from
  rglob() are not guaranteed to surface (Python stdlib behaviour). This is
  acceptable for a developer-owned source tree where all paths are readable.
"""

import re
import sys
from pathlib import Path

FILE_EXTS = {".astro", ".css"}

HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})\b")
RGBA_RE = re.compile(r"\brgba?\s*\([^)]*\)", re.IGNORECASE)

TOKEN_FILE = "tokens.css"
CSS_INLINE_COMMENT_RE = re.compile(r"/\*.*?\*/")
URL_RE = re.compile(r"\burl\([^)]*\)", re.IGNORECASE)  # strip url(...) before scanning for hex
CSS_STRING_RE = re.compile(r"""(?:"[^"]*"|'[^']*')""")  # strip quoted strings before scanning
ROOT_OPEN_RE = re.compile(r":root\b")
CSS_PROP_RE = re.compile(r"^\s*[-\w]+\s*:")
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

        # Step 1: Resolve block-comment state. When inside a block comment, skip
        # until */ is found; preserve and process the code that follows it.
        if in_block_comment:
            close = line.find("*/")
            if close == -1:
                continue  # whole line is inside the block comment
            in_block_comment = False
            line = line[close + 2:]  # keep only the code that follows */

        # Step 2: Strip closed inline /* ... */ from the entire line; if /* remains
        # unclosed, truncate there and enter block-comment state. This handles
        # trailing comments (`color: var(--x); /* old: #fff */`) and mid-line
        # openings (`.foo { /* comment`) without false positives or false negatives.
        line, opened_block = _strip_inline_comment(line)
        if opened_block:
            in_block_comment = True

        # Step 3: Strip url(...) tokens — URL fragments like url(#id) contain
        # valid hex-looking strings that are element IDs, not color values.
        line = URL_RE.sub("url()", line)

        # Step 4: Strip quoted CSS strings — content: '#abc' or content: "rgba(0,0,0)"
        # are string literals, not color values; masking them prevents false positives.
        line = CSS_STRING_RE.sub("''", line)

        if not line.strip():
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
        if in_declaration:
            decl_buffer += " " + line.strip()
            for m in HEX_RE.finditer(line):
                violations.append((lineno, m.group()))
            # Do NOT terminate on opened_block: a block comment within a declaration
            # does not end it — the value continues after the comment closes.
            if ";" in line or "{" in line or "}" in line:
                for m in RGBA_RE.finditer(decl_buffer):
                    violations.append((lineno, m.group()))
                in_declaration = False
                decl_buffer = ""
            continue

        if not CSS_PROP_RE.match(line):
            if "{" in line or "}" in line:
                in_declaration = False
                decl_buffer = ""
                # Handle inline rules: .selector { property: value; }
                # Guard: CSS inline rules have a non-empty selector before {;
                # JSX object literals start with { (no selector), so before_brace
                # would be empty — skip those.
                if "{" in line:
                    brace_pos = line.index("{")
                    before_brace = line[:brace_pos].rstrip()
                    after_brace = line[brace_pos + 1:].lstrip()
                    # Advance through nested selector levels so that
                    # `@keyframes foo { from { color: #fff; } }` is detected.
                    while after_brace and not CSS_PROP_RE.match(after_brace):
                        if "{" not in after_brace:
                            break
                        after_brace = after_brace[after_brace.index("{") + 1:].lstrip()
                    if before_brace and CSS_PROP_RE.match(after_brace):
                        colon_idx = after_brace.index(":")
                        inline_value = after_brace[colon_idx + 1:]
                        for m in HEX_RE.finditer(inline_value):
                            violations.append((lineno, m.group()))
                        if ";" in inline_value or "}" in inline_value:
                            # Declaration terminates on this line (semicolon or
                            # closing brace — CSS permits omitting the final ;).
                            for m in RGBA_RE.finditer(inline_value):
                                violations.append((lineno, m.group()))
                        else:
                            # Value wraps to the next line; carry declaration state
                            # so continuation lines are scanned.
                            in_declaration = True
                            decl_buffer = inline_value
            continue

        # Extract value part (after the first colon on the line).
        colon_idx = line.index(":")
        value_part = line[colon_idx + 1:]

        if "{" in value_part:
            # The colon belongs to a CSS selector (e.g. `a:hover {` or
            # `body:has(#id) {`) — the text after the colon is a selector
            # continuation, not a property value. Redirect to inline-rule
            # detection on the portion after the first `{` in value_part.
            brace_pos = value_part.index("{")
            after_brace = value_part[brace_pos + 1:].lstrip()
            # Advance through nested selector levels (e.g. @keyframes { from {).
            while after_brace and not CSS_PROP_RE.match(after_brace):
                if "{" not in after_brace:
                    break
                after_brace = after_brace[after_brace.index("{") + 1:].lstrip()
            if CSS_PROP_RE.match(after_brace):
                c_idx = after_brace.index(":")
                inline_value = after_brace[c_idx + 1:]
                for m in HEX_RE.finditer(inline_value):
                    violations.append((lineno, m.group()))
                if ";" in inline_value or "}" in inline_value:
                    for m in RGBA_RE.finditer(inline_value):
                        violations.append((lineno, m.group()))
                else:
                    in_declaration = True
                    decl_buffer = inline_value
        else:
            for m in HEX_RE.finditer(value_part):
                violations.append((lineno, m.group()))

            if ";" in value_part or "}" in value_part:
                # Declaration terminates here (semicolon or closing brace — CSS
                # permits omitting the final ; before }).
                for m in RGBA_RE.finditer(value_part):
                    violations.append((lineno, m.group()))
            else:
                # Multi-line value: accumulate buffer; rgba scanned when
                # declaration closes. Block comments do not terminate the
                # declaration — in_block_comment skips comment lines and
                # in_declaration persists until a real ; or block boundary.
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
