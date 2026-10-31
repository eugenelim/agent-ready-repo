#!/usr/bin/env python3
"""Render a saved architecture assessment to one self-contained HTML file.

``render_html.py <effort-dir>`` reads ``<effort-dir>/assessment.md`` and writes
``<effort-dir>/assessment.html``. The page runs no script and loads nothing from
a network. Every byte of the source is untrusted text: the renderer escapes it,
emits only a closed set of elements and attributes, and prints only fixed
tokens to stdout and stderr. Exit codes: 0 success, 2 refused report or usage,
3 confinement or environment failure.
"""

import base64
import datetime
import hashlib
import html
import importlib.util
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any, NamedTuple

RENDERER_VERSION = "1"
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_EXISTING_OUTPUT_BYTES = 16 * 1024 * 1024
SOURCE_NAME = "assessment.md"
OUTPUT_NAME = "assessment.html"

ORIENTATION = {
    "overall architecture": "Overall architecture",
    "architecture by subsystem": "Architecture by subsystem",
    "physical architecture": "Physical architecture",
}
SOURCES_HEADER = ["Source", "Locator", "Evidence class", "Limit"]
EVIDENCE_CLASSES = ("observed", "inferred", "reported", "unknown")
HEAT_COLUMNS = (
    "Consequence",
    "Pressure",
    "Concentration / coupling",
    "Verification weakness",
    "Ops/data/security exposure",
)
HEAT_VALUES = ("low", "medium", "high", "unknown")

BANNER_TEXT = "Map and hotspot set not user-confirmed"
NOTICE_TEXT = "Unverified: built from repository text and model analysis; not redacted"
DIAGRAM_LABEL = "Diagram source (not rendered)"

# Every line the script prints comes from this fixed set (plus a canonical
# heading from ORIENTATION), never from the source or the path.
TOKEN_OK = "render_html: ok"
TOKEN_USAGE = "render_html: usage: render_html.py <effort-dir>"
TOKEN_UNSAFE_PATH = "render_html: refused: unsafe or missing path"
TOKEN_SOURCE_LARGE = "render_html: refused: source over the size cap"
TOKEN_NOT_UTF8 = "render_html: refused: source is not valid UTF-8"
TOKEN_EVIDENCE = "render_html: refused: evidence class outside the allowed set"
TOKEN_PROVENANCE = "render_html: refused: no usable Sources checked table in"
TOKEN_OUTPUT_LARGE = "render_html: refused: rendered page over the size cap"
TOKEN_HOST = "render_html: refused: host lacks descriptor walking:"
TOKEN_INTERNAL = "render_html: failed: internal error"

CSS = """
body{font:16px/1.5 system-ui,sans-serif;margin:0;color:#1b1f24;background:#fff}
main{max-width:70rem;margin:0 auto;padding:1.5rem}
h1,h2,h3{line-height:1.25}
h2{border-bottom:1px solid #c9d1d9;padding-bottom:.25rem;margin-top:2rem}
table{border-collapse:collapse;margin:1rem 0;width:100%}
th,td{border:1px solid #c9d1d9;padding:.35rem .6rem;text-align:left;vertical-align:top}
th{background:#f3f5f7}
pre{background:#f3f5f7;padding:.75rem;overflow:auto;border-radius:4px}
code{font-family:ui-monospace,monospace;font-size:.92em}
.meta{color:#4a5560;font-size:.9rem}
a{color:#0969da}
.banner-unconfirmed{border:2px solid #9a6700;background:#fff8c5;padding:.75rem 1rem;
margin:1rem 0;font-weight:600}
.notice-untrusted{border:1px solid #6e7781;background:#f3f5f7;padding:.75rem 1rem;margin:1rem 0}
.diagram-label{font-weight:600;margin-bottom:0}
.ev-observed{border-left:.5rem solid #1a7f37}
.ev-inferred{border-left:.5rem solid #9a6700}
.ev-reported{border-left:.5rem solid #0969da}
.ev-unknown{border-left:.5rem solid #6e7781}
.heat-low{background:#dafbe1}
.heat-medium{background:#fff8c5}
.heat-high{background:#ffebe9;font-weight:600}
.heat-unknown{background:#eaeef2;font-style:italic}
@media (prefers-color-scheme:dark){
body{background:#0d1117;color:#e6edf3}
th,pre,.notice-untrusted{background:#161b22}
th,td,h2,.notice-untrusted{border-color:#30363d}
.banner-unconfirmed{background:#3b2e00;border-color:#d29922;color:#f0e6c0}
a{color:#58a6ff}
.heat-low{background:#12301c}
.heat-medium{background:#3b2e00}
.heat-high{background:#4a1d1d}
.heat-unknown{background:#21262d}
}
"""


class Refusal(Exception):
    """A report the renderer will not render; carries the stderr line and exit code."""

    def __init__(self, line: str, code: int = 2) -> None:
        super().__init__(line)
        self.line = line
        self.code = code


class Block(NamedTuple):
    """One parsed Markdown block."""

    kind: str  # h, p, ul, ol, table, code, hr
    level: int = 0
    text: str = ""
    items: tuple[str, ...] = ()
    header: tuple[str, ...] = ()
    rows: tuple[tuple[str, ...], ...] = ()


_FENCE = re.compile(r"^( {0,3})(`{3,})([^`]*)$")
_ULI = re.compile(r"^\s*[-*]\s+(.*)$")
_OLI = re.compile(r"^\s*\d+\.\s+(.*)$")
_HR = re.compile(r"^\s*-{3,}\s*$")
_SEPARATOR_CELL = re.compile(r":?-{3,}:?")
# Each alternative stops at the next delimiter it excludes (a backtick, an asterisk, a
# bracket, or a parenthesis), so no start position rescans text an earlier one scanned
# and parsing stays linear in the source size at any span length.
_INLINE = re.compile(
    r"(`[^`\n]+`)|(\*\*[^*\n]+\*\*)"
    r"|(\[[^\[\]\n]+\]\((?:[^()\n]|\([^()\n]*\))*\))|(\*[^*\n]+\*)"
)
_CONTROL = re.compile(r"[\x00-\x20\x7f]")
_FORMAT_CHARS = re.compile("[\u061c\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff]")


def _esc(text: str) -> str:
    """Escape *text* for an HTML text node or a double-quoted attribute."""
    return html.escape(text, quote=True)


def _safe_target(target: str) -> bool:
    """Return True for an https, http, or in-document link with no whitespace."""
    cleaned = target.strip()
    lowered = cleaned.lower()
    if _CONTROL.search(cleaned):
        return False
    return lowered.startswith(("https:", "http:", "#"))


def _inline(text: str) -> str:
    """Render the bounded inline subset; everything else is escaped text."""
    out: list[str] = []
    position = 0
    for match in _INLINE.finditer(text):
        out.append(_esc(text[position : match.start()]))
        token = match.group(0)
        if match.group(1):
            out.append(f"<code>{_esc(token[1:-1])}</code>")
        elif match.group(2):
            out.append(f"<strong>{_esc(token[2:-2])}</strong>")
        elif match.group(3):
            split = token.index("](")
            label, target = token[1:split], token[split + 2 : -1]
            if _safe_target(target) and not _FORMAT_CHARS.search(token):
                out.append(f'<a href="{_esc(target.strip())}">{_esc(label)}</a>')
            else:
                out.append(_esc(token))
        else:
            out.append(f"<em>{_esc(token[1:-1])}</em>")
        position = match.end()
    out.append(_esc(text[position:]))
    return "".join(out)


def _cells(line: str) -> tuple[str, ...]:
    """Split a Markdown table row into trimmed cells."""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return tuple(cell.strip() for cell in stripped.split("|"))


def _heading(line: str) -> tuple[int, str] | None:
    """Return (level, text) for an ATX heading line, or None; linear in the line."""
    level = len(line) - len(line.lstrip("#"))
    if not 1 <= level <= 6 or len(line) == level or line[level] not in " \t":
        return None
    text = line[level:].strip()
    closing = text.rstrip("#")
    if closing != text and (not closing or closing[-1] in " \t"):
        text = closing.rstrip()
    return (level, text) if text else None


def _is_separator(line: str) -> bool:
    """Return True for a table separator row such as `| --- | :-: |`."""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells = [cell.strip() for cell in stripped.split("|")]
    return bool(cells) and all(_SEPARATOR_CELL.fullmatch(cell) for cell in cells)


def _starts_block(line: str, next_line: str | None) -> bool:
    """Return True when *line* begins a non-paragraph block."""
    if _FENCE.match(line) or _heading(line) or _ULI.match(line):
        return True
    if _OLI.match(line) or _HR.match(line):
        return True
    return line.lstrip().startswith("|") and next_line is not None and _is_separator(next_line)


def parse(source: str) -> list[Block]:
    """Parse the supported Markdown subset into blocks."""
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[Block] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        following = lines[i + 1] if i + 1 < len(lines) else None
        fence = _FENCE.match(line)
        if fence:
            marker, info = fence.group(2), fence.group(3)
            body: list[str] = []
            i += 1
            while i < len(lines) and not (
                lines[i].strip().startswith(marker) and set(lines[i].strip()) == {"`"}
            ):
                body.append(lines[i])
                i += 1
            i += 1
            blocks.append(Block("code", text="\n".join(body), header=(info.strip(),)))
            continue
        heading = _heading(line)
        if heading:
            blocks.append(Block("h", level=heading[0], text=heading[1]))
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        if _HR.match(line):
            blocks.append(Block("hr"))
            i += 1
            continue
        if line.lstrip().startswith("|") and following and _is_separator(following):
            header = _cells(line)
            rows: list[tuple[str, ...]] = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            blocks.append(Block("table", header=header, rows=tuple(rows)))
            continue
        for pattern, kind in ((_ULI, "ul"), (_OLI, "ol")):
            if pattern.match(line):
                parts: list[list[str]] = []
                while i < len(lines):
                    item = pattern.match(lines[i])
                    if item:
                        parts.append([item.group(1)])
                    elif lines[i].startswith((" ", "\t")) and lines[i].strip() and parts:
                        parts[-1].append(lines[i].strip())
                    else:
                        break
                    i += 1
                blocks.append(Block(kind, items=tuple(" ".join(part) for part in parts)))
                break
        else:
            paragraph = [line.strip()]
            i += 1
            while i < len(lines) and lines[i].strip():
                after = lines[i + 1] if i + 1 < len(lines) else None
                if _starts_block(lines[i], after):
                    break
                paragraph.append(lines[i].strip())
                i += 1
            blocks.append(Block("p", text="\n".join(paragraph)))
    return blocks


def _scopes(blocks: list[Block]) -> list[tuple[str, str | None]]:
    """Return (section, orientation) for every block; the one scope rule for the page.

    `section` is the lowercased text of the last heading at level 1 or 2 (the first level-1
    heading is the title and starts no section). `orientation` is the orientation subsection
    that is open: one ends at the next heading whose level is at or above its own.
    """
    section, orientation, open_level = "", None, 0
    seen_title = False
    scopes: list[tuple[str, str | None]] = []
    for block in blocks:
        if block.kind == "h":
            name = block.text.strip().lower()
            if block.level == 1 and not seen_title:
                seen_title = True
            elif block.level <= 2:
                section = name
                orientation, open_level = (name, block.level) if name in ORIENTATION else (None, 0)
            elif name in ORIENTATION:
                orientation, open_level = name, block.level
            elif orientation is not None and block.level <= open_level:
                orientation = None
        scopes.append((section, orientation))
    return scopes


def _charter_checkpoint_confirmed(
    blocks: list[Block], scopes: list[tuple[str, str | None]]
) -> bool:
    """Return True only when the charter holds exactly one `Checkpoints: confirmed`.

    Reads the parsed paragraph blocks of the `## Assessment charter` section, so a fenced
    block can never stand in for, or hide, the real charter line.
    """
    values: list[str] = []
    for block, (section, _) in zip(blocks, scopes, strict=True):
        if section == "assessment charter" and block.kind == "p":
            for line in block.text.split("\n"):
                if line.startswith("Checkpoints:"):
                    values.append(line[len("Checkpoints:") :].strip())
    return values == ["confirmed"]


def _is_sources_label(block: Block) -> bool:
    """Return True for the `Sources checked:` label paragraph."""
    return block.kind == "p" and block.text.strip() == "Sources checked:"


def _check_evidence_classes(table: Block) -> None:
    """Refuse a Sources checked table with an evidence class outside the closed set."""
    for row in table.rows:
        evidence = row[2].strip().lower() if len(row) > 2 else ""
        if evidence not in EVIDENCE_CLASSES:
            raise Refusal(TOKEN_EVIDENCE)


def _check_orientation(blocks: list[Block]) -> None:
    """Refuse an orientation subsection that lacks a usable, valid Sources checked table.

    A heading counts at any level, with closing `#` marks ignored and the title excluded. Every
    labeled table with the Sources checked header is validated, and the last block of
    the subsection must be one with at least one data row.
    """
    seen_title = False
    for index, block in enumerate(blocks):
        canonical = None
        if block.kind == "h":
            if block.level == 1 and not seen_title:
                seen_title = True
            else:
                canonical = ORIENTATION.get(block.text.strip().lower())
        if canonical is None:
            continue
        end = index + 1
        while end < len(blocks) and not (
            blocks[end].kind == "h" and blocks[end].level <= block.level
        ):
            end += 1
        section = blocks[index + 1 : end]
        refusal = Refusal(f"{TOKEN_PROVENANCE} {canonical}")
        if len(section) < 2 or section[-1].kind != "table" or not _is_sources_label(section[-2]):
            raise refusal
        if list(section[-1].header) != SOURCES_HEADER or not section[-1].rows:
            raise refusal
        for position, candidate in enumerate(section):
            if (
                candidate.kind == "table"
                and position > 0
                and _is_sources_label(section[position - 1])
                and list(candidate.header) == SOURCES_HEADER
            ):
                _check_evidence_classes(candidate)


def _slug(text: str, used: set[str], counters: dict[str, int]) -> str:
    """Return a unique ASCII anchor id for a heading, in amortized constant time."""
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"
    candidate, number = base, counters.get(base, 1)
    while candidate in used:
        number += 1
        candidate = f"{base}-{number}"
    counters[base] = number
    used.add(candidate)
    return candidate


def _table(block: Block, sources: bool, heat: bool) -> str:
    """Render a table, adding evidence or heat classes by header text."""
    header = list(block.header)
    heat_columns = {i for i, name in enumerate(header) if heat and name in HEAT_COLUMNS}
    parts = ["<table><thead><tr>"]
    parts += [f"<th>{_inline(name)}</th>" for name in header]
    parts.append("</tr></thead><tbody>")
    for row in block.rows:
        parts.append("<tr>")
        for i, cell in enumerate(row):
            value = cell.strip().lower()
            css = ""
            if sources and i == 2 and value in EVIDENCE_CLASSES:
                css = f' class="ev-{value}"'
            elif i in heat_columns and value in HEAT_VALUES:
                css = f' class="heat-{value}"'
            parts.append(f"<td{css}>{_inline(cell)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _body(blocks: list[Block], scopes: list[tuple[str, str | None]]) -> tuple[str, str]:
    """Render blocks to HTML; return (title, html) with the first H1 as the title."""
    title = "Architecture assessment"
    out: list[str] = []
    used: set[str] = set()
    counters: dict[str, int] = {}
    seen_title = False
    previous: Block | None = None
    for block, (section, orientation) in zip(blocks, scopes, strict=True):
        if block.kind == "h":
            if block.level == 1 and not seen_title:
                title, seen_title = block.text, True
                previous = block
                continue
            level = min(block.level, 6)
            slug = _slug(block.text, used, counters)
            out.append(f'<h{level} id="{slug}">{_inline(block.text)}</h{level}>')
        elif block.kind == "p":
            if section == "assessment charter":
                lines = "<br>".join(_inline(line) for line in block.text.split("\n"))
                out.append(f"<p>{lines}</p>")
            else:
                out.append(f"<p>{_inline(block.text.replace(chr(10), ' '))}</p>")
        elif block.kind in ("ul", "ol"):
            items = "".join(f"<li>{_inline(item)}</li>" for item in block.items)
            out.append(f"<{block.kind}>{items}</{block.kind}>")
        elif block.kind == "table":
            sources = (
                orientation is not None
                and list(block.header) == SOURCES_HEADER
                and previous is not None
                and _is_sources_label(previous)
            )
            out.append(_table(block, sources, section == "attention heat map"))
        elif block.kind == "code":
            code = f"<pre><code>{_esc(block.text)}</code></pre>"
            if block.header and block.header[0].lower().split(None, 1)[:1] == ["mermaid"]:
                out.append(
                    '<div class="diagram">'
                    f'<p class="diagram-label">{DIAGRAM_LABEL}</p>{code}</div>'
                )
            else:
                out.append(code)
        elif block.kind == "hr":
            out.append("<hr>")
        previous = block
    return title, "\n".join(out)


def render(source: str, effort_name: str, today: str) -> str:
    """Return the full HTML document for *source*, or raise Refusal."""
    blocks = parse(source)
    _check_orientation(blocks)
    scopes = _scopes(blocks)
    title, body = _body(blocks, scopes)
    digest = base64.b64encode(hashlib.sha256(CSS.encode("utf-8")).digest()).decode()
    policy = (
        f"default-src 'none'; style-src 'sha256-{digest}'; base-uri 'none'; form-action 'none'"
    )
    banner = ""
    if not _charter_checkpoint_confirmed(blocks, scopes):
        banner = f'<div class="banner-unconfirmed">{BANNER_TEXT}</div>'
    meta = (
        f'<p class="meta">Source: {_esc(effort_name)}/{SOURCE_NAME} · '
        f"Generated {_esc(today)} UTC · Renderer version {RENDERER_VERSION}</p>"
    )
    notice = f'<div class="notice-untrusted">{NOTICE_TEXT}</div>'
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        f'<meta http-equiv="Content-Security-Policy" content="{policy}">'
        f"<title>{_esc(title)}</title><style>{CSS}</style></head>\n"
        f"<body><main><h1>{_esc(title)}</h1>\n{meta}\n{banner}\n{notice}\n"
        f"{body}\n</main></body></html>\n"
    )


def _utf8_streams() -> None:
    """Switch stdout and stderr to UTF-8 before anything is printed."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _missing_capability() -> str | None:
    """Return the name of the first missing descriptor-walking capability."""
    checks = (
        ("open", os.open in os.supports_dir_fd),
        ("stat", os.stat in os.supports_dir_fd),
        ("rename", os.rename in os.supports_dir_fd),
        ("follow-symlinks", os.stat in os.supports_follow_symlinks),
        ("O_DIRECTORY", hasattr(os, "O_DIRECTORY")),
        ("O_NOFOLLOW", hasattr(os, "O_NOFOLLOW")),
    )
    for name, present in checks:
        if not present:
            return name
    return None


def _load_helper() -> Any:
    """Load the co-located confinement helper by path under a private name."""
    path = Path(__file__).with_name("file_safety.py")
    inspected = os.lstat(path)
    if not stat.S_ISREG(inspected.st_mode):
        raise ImportError("helper is not a regular file")
    spec = importlib.util.spec_from_file_location("architect_assess_render_html_file_safety", path)
    if spec is None or spec.loader is None:
        raise ImportError("helper cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _supplied_path_is_safe(supplied: str) -> bool:
    """Return True when no component of the path as supplied is a symlink or `..`."""
    path = Path(supplied)
    if ".." in path.parts:
        return False
    current = Path(path.anchor) if path.anchor else Path()
    for part in path.parts[1:] if path.anchor else path.parts:
        current = current / part
        try:
            inspected = os.lstat(current)
        except OSError:
            return False
        if stat.S_ISLNK(inspected.st_mode):
            return False
    return stat.S_ISDIR(os.lstat(path).st_mode)


def _run(argv: list[str]) -> int:
    """Render the report named by *argv*; return the exit code."""
    if len(argv) != 1:
        print(TOKEN_USAGE, file=sys.stderr)
        return 2
    missing = _missing_capability()
    if missing is not None:
        print(f"{TOKEN_HOST} {missing}", file=sys.stderr)
        return 3
    if not _supplied_path_is_safe(argv[0]):
        print(TOKEN_UNSAFE_PATH, file=sys.stderr)
        return 3
    helper = _load_helper()
    root = Path(argv[0]).absolute()
    try:
        data = helper.read_confined_regular_file(
            root, root / SOURCE_NAME, max_bytes=MAX_SOURCE_BYTES
        )
    except helper.BoundExceeded:
        print(TOKEN_SOURCE_LARGE, file=sys.stderr)
        return 2
    except (helper.UnsafeContentError, OSError):
        print(TOKEN_UNSAFE_PATH, file=sys.stderr)
        return 3
    try:
        source = data.decode("utf-8")
    except UnicodeDecodeError:
        print(TOKEN_NOT_UTF8, file=sys.stderr)
        return 2
    today = datetime.datetime.now(datetime.UTC).date().isoformat()
    try:
        page = render(source, root.name, today)
    except Refusal as refusal:
        print(refusal.line, file=sys.stderr)
        return refusal.code
    encoded = page.encode("utf-8")
    if len(encoded) > MAX_EXISTING_OUTPUT_BYTES:
        print(TOKEN_OUTPUT_LARGE, file=sys.stderr)
        return 2
    destination = root / OUTPUT_NAME
    try:
        existing = None
        if os.path.lexists(destination):
            if stat.S_ISLNK(os.lstat(destination).st_mode):
                print(TOKEN_UNSAFE_PATH, file=sys.stderr)
                return 3
            if os.lstat(destination).st_size > MAX_EXISTING_OUTPUT_BYTES:
                print(TOKEN_UNSAFE_PATH, file=sys.stderr)
                return 3
            existing = helper.sha256_confined_regular_file(root, destination)
        helper.write_confined_regular_file(root, destination, encoded, expect_sha256=existing)
    except (helper.UnsafeContentError, OSError):
        print(TOKEN_UNSAFE_PATH, file=sys.stderr)
        return 3
    print(TOKEN_OK)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point; every exit is 0, 2, or 3 and prints only fixed tokens."""
    _utf8_streams()
    try:
        return _run(list(sys.argv[1:] if argv is None else argv))
    except Exception:  # noqa: BLE001 - a fixed token must replace any traceback
        print(TOKEN_INTERNAL, file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
