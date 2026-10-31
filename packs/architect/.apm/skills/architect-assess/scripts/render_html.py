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
import unicodedata
from pathlib import Path
from typing import Any, NamedTuple

RENDERER_VERSION = "2"
REPORT_ID = "report"
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_EXISTING_OUTPUT_BYTES = 16 * 1024 * 1024
MAX_ASSET_BYTES = 64 * 1024
MERMAID_VERSION = "12.2.0"
MERMAID_URL = f"https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.min.js"
MERMAID_SRI = "sha384-8xUhuLNMjW/cI2Dacg3DR4WliYznvIg0LVG1stctThKD/YVrJFI9TNCFxft5NYgp"
ASSET_DIR = Path(__file__).resolve().parent / "report_assets"
ASSET_NAMES = ("view-base.css", "report.css")
FORBIDDEN_ASSET_TEXT = ("</style", "<!--", "url(", "@import")
SCRIPT_NAME = "diagrams.js"
FORBIDDEN_SCRIPT_TEXT = ("</script", "<!--", "\r")
DIAGRAM_KEYWORDS = (
    "flowchart",
    "graph",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram-v2",
    "erDiagram",
)
DIAGRAM_MAX_BYTES = 50_000
DIAGRAM_DRAW_LIMIT = 20
DIAGRAM_STATEMENT_START = ("click", "link", "callback")
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
DIAGRAM_LABEL_DRAWN = "Diagram source (not drawn yet)"
DIAGRAM_LABEL_UNSAFE = "Diagram source (not drawn: unsafe)"
DIAGRAM_LABEL_LIMIT = "Diagram source (not drawn: limit)"
DIAGRAMS_NOTE = (
    f"Diagrams are drawn by Mermaid {MERMAID_VERSION}, loaded from cdn.jsdelivr.net. "
    "Opening this report sends your IP address, the time, and your browser details to that "
    "host, and the report's web address if it is served from a web host; no report text is sent."
)

# Every line the script prints comes from this fixed set (plus a canonical
# heading from ORIENTATION), never from the source or the path.
TOKEN_OK = "render_html: ok"
TOKEN_USAGE = "render_html: usage: render_html.py <effort-dir> [--diagrams]"
TOKEN_UNSAFE_PATH = "render_html: refused: unsafe or missing path"
TOKEN_SOURCE_LARGE = "render_html: refused: source over the size cap"
TOKEN_NOT_UTF8 = "render_html: refused: source is not valid UTF-8"
TOKEN_EVIDENCE = "render_html: refused: evidence class outside the allowed set"
TOKEN_PROVENANCE = "render_html: refused: no usable Sources checked table in"
TOKEN_OUTPUT_LARGE = "render_html: refused: rendered page over the size cap"
TOKEN_ASSET_MISSING = "render_html: failed: stylesheet asset missing"
TOKEN_ASSET_LARGE = "render_html: failed: stylesheet asset over the size cap"
TOKEN_ASSET_NOT_UTF8 = "render_html: failed: stylesheet asset is not valid UTF-8"
TOKEN_ASSET_FORBIDDEN = "render_html: failed: stylesheet asset holds forbidden text"
TOKEN_SCRIPT_MISSING = "render_html: failed: script asset missing or unsafe"
TOKEN_SCRIPT_LARGE = "render_html: failed: script asset over the size cap"
TOKEN_SCRIPT_UNREADABLE = "render_html: failed: script asset unreadable"
TOKEN_SCRIPT_FORBIDDEN = "render_html: failed: script asset holds forbidden text"
TOKEN_HOST = "render_html: refused: host lacks descriptor walking:"
TOKEN_INTERNAL = "render_html: failed: internal error"


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


_FENCE = re.compile(r"^([ \t]*)(`{3,})([^`]*)$")
_ULI = re.compile(r"^\s*[-*]\s+(.*)$")
_OLI = re.compile(r"^\s*\d+\.\s+(.*)$")
_HR = re.compile(r"^\s*-{3,}\s*$")
_SEPARATOR_CELL = re.compile(r":?-{3,}:?")
# Each alternative stops at the next delimiter it excludes (a backtick, an asterisk, a
# bracket, or a parenthesis), so no start position rescans text an earlier one scanned
# and parsing stays linear in the source size at any span length.
_INLINE = re.compile(
    r"(`[^`\n]+`)|(\*\*[^*\n]+\*\*)"
    r"|(\[[^\[\]\n]+\]\((?:[^()\n]++|\([^()\n]*+\))*+\))|(\*[^*\n]+\*)"
)

_HELPER: Any = None


def _esc(text: str) -> str:
    """Escape *text* for an HTML text node or a double-quoted attribute."""
    return html.escape(text, quote=True)


def _safe_link(label: str, target: str) -> bool:
    """Return True when a link may become an anchor.

    The target, trimmed and lowercased, begins `https:`, `http:`, or `#`; it holds no
    interior whitespace; and neither the text nor the target holds a character of Unicode
    general category Cc or Cf (control, bidi, and other format characters).
    """
    if any(unicodedata.category(char) in ("Cc", "Cf") for char in label + target):
        return False
    cleaned = target.strip()
    if any(char.isspace() for char in cleaned):
        return False
    return cleaned.lower().startswith(("https:", "http:", "#"))


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
            if _safe_link(label, target):
                out.append(f'<a href="{_esc(target.strip())}">{_esc(label)}</a>')
            else:
                out.append(_esc(token))
        else:
            out.append(f"<em>{_esc(token[1:-1])}</em>")
        position = match.end()
    out.append(_esc(text[position:]))
    return "".join(out)


def _plain_text(text: str) -> str:
    """Reduce inline Markdown to the text inside it: `See [docs](https://x)` gives `See docs`."""
    out: list[str] = []
    position = 0
    for match in _INLINE.finditer(text):
        out.append(text[position : match.start()])
        token = match.group(0)
        if match.group(3):
            out.append(token[1 : token.index("](")])
        elif match.group(2):
            out.append(token[2:-2])
        else:
            out.append(token[1:-1])
        position = match.end()
    out.append(text[position:])
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
            indent, marker, info = len(fence.group(1)), fence.group(2), fence.group(3)
            body: list[str] = []
            i += 1
            while i < len(lines) and not (
                lines[i].strip().startswith(marker) and set(lines[i].strip()) == {"`"}
            ):
                body.append(lines[i][min(indent, len(lines[i]) - len(lines[i].lstrip(" \t"))) :])
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
                    elif (
                        lines[i].startswith((" ", "\t"))
                        and lines[i].strip()
                        and parts
                        and not _FENCE.match(lines[i])
                    ):
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


def _title_index(blocks: list[Block]) -> int | None:
    """Return the index of the title heading: the first heading block, if it is level 1."""
    for index, block in enumerate(blocks):
        if block.kind == "h":
            return index if block.level == 1 else None
    return None


def _orientation_ranges(blocks: list[Block], title: int | None) -> list[tuple[int, int, str]]:
    """Return (start, end, canonical heading) for every orientation subsection.

    One rule everywhere: a subsection starts at its heading and ends at the next heading
    whose level is at or above its own. A single pass with a stack keeps this linear.
    """
    ends: dict[int, int] = {}
    open_headings: list[int] = []
    for index, block in enumerate(blocks):
        if block.kind != "h" or index == title:
            continue
        while open_headings and blocks[open_headings[-1]].level >= block.level:
            ends[open_headings.pop()] = index
        open_headings.append(index)
    for index in open_headings:
        ends[index] = len(blocks)
    return [
        (index, ends[index], ORIENTATION[blocks[index].text.strip().lower()])
        for index in sorted(ends)
        if blocks[index].text.strip().lower() in ORIENTATION
    ]


def _scopes(blocks: list[Block], title: int | None) -> list[tuple[str, str | None]]:
    """Return (section, orientation) for every block; the one scope rule for the page.

    `section` is the lowercased text of the last non-title heading at level 1 or 2.
    `orientation` is the canonical name of the innermost open orientation subsection.
    """
    orientation: list[str | None] = [None] * len(blocks)
    for start, end, canonical in _orientation_ranges(blocks, title):
        for index in range(start, end):
            orientation[index] = canonical.lower()
    section = ""
    scopes: list[tuple[str, str | None]] = []
    for index, block in enumerate(blocks):
        if block.kind == "h" and index != title and block.level <= 2:
            section = block.text.strip().lower()
        scopes.append((section, orientation[index]))
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


def _check_orientation(blocks: list[Block], title: int | None) -> None:
    """Refuse an orientation subsection that lacks a usable, valid Sources checked table.

    A heading counts at any level, with closing `#` marks ignored and the title excluded.
    Every labeled table with the Sources checked header is validated, and the last block of
    the subsection must be one with at least one data row.
    """
    for start, end, canonical in _orientation_ranges(blocks, title):
        section = blocks[start + 1 : end]
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


def _table(block: Block, sources: bool, heat: bool, counts: dict[str, int]) -> str:
    """Render a table, adding evidence marks or heat classes by header text."""
    header = list(block.header)
    heat_columns = {i for i, name in enumerate(header) if heat and name in HEAT_COLUMNS}
    parts = ["<table><thead><tr>"]
    parts += [f"<th>{_inline(name)}</th>" for name in header]
    parts.append("</tr></thead><tbody>")
    for row in block.rows:
        parts.append("<tr>")
        for i, cell in enumerate(row):
            value = cell.strip().lower()
            if sources and i == 2 and value in EVIDENCE_CLASSES:
                counts[value] += 1
                parts.append(f'<td><span class="mark ev-{value}">{_inline(cell)}</span></td>')
                continue
            css = ""
            if i in heat_columns and value in HEAT_VALUES:
                css = f' class="heat-{value}"'
            parts.append(f"<td{css}>{_inline(cell)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _scroll_wrap(content: str, nearest_heading: str, kind: str = "table") -> str:
    """Wrap a table or source block in a keyboard-scrollable region named for its heading."""
    word = "Table" if kind == "table" else "Source"
    label = f"{word}: {nearest_heading}" if nearest_heading else word
    return (
        f'<div class="{kind}-scroll" role="region" tabindex="0" '
        f'aria-label="{_esc(label)}">{content}</div>'
    )


class RailItem(NamedTuple):
    """One contents link: the target id, the heading's plain text, and whether it is nested."""

    slug: str
    text: str
    nested: bool


_LINK_STYLE = re.compile(r"linkStyle(?![A-Za-z0-9_])")


def diagram_drawable(text: str) -> bool:
    """Whether a Mermaid fence is safe to hand to the drawing script.

    The text must equal what a browser reads back from the emitted element, so any
    character an HTML parser drops or rewrites, and any Unicode space the Mermaid lexer
    would skip, is refused rather than normalised.
    """
    if len(text.encode("utf-8")) > DIAGRAM_MAX_BYTES:
        return False
    for char in text:
        if char in " \t\n":
            continue
        if char.isspace() or char == "\ufeff" or unicodedata.category(char) == "Cc":
            return False
    first = next((line for line in text.split("\n") if line.strip(" \t")), "")
    if not first.strip(" \t").startswith(DIAGRAM_KEYWORDS):
        return False
    if "%%{" in text:
        return False
    for line in text.split("\n"):
        for statement in line.split(";"):
            lowered = statement.strip(" \t").lower()
            if lowered.startswith(DIAGRAM_STATEMENT_START) and not _LINK_STYLE.match(
                statement.strip(" \t")
            ):
                return False
    return True


def _body(
    blocks: list[Block],
    scopes: list[tuple[str, str | None]],
    title_at: int | None,
    diagrams: bool = False,
) -> tuple[str, str, list[RailItem], dict[str, int]]:
    """Render blocks to document sections.

    Returns (title, html, rail items, evidence counts). The title is the first heading
    block, when that block is level 1. Every other level-1 or level-2 heading starts a
    section that carries the heading's id; blocks before the first one form a leading section.
    """
    title = "Architecture assessment"
    out: list[str] = []
    lead: list[str] = []
    used: set[str] = {REPORT_ID}
    counters: dict[str, int] = {}
    counts = dict.fromkeys(EVIDENCE_CLASSES, 0)
    rail: list[RailItem] = []
    started = False
    nearest = ""
    drawn = 0
    previous: Block | None = None

    def emit(markup: str) -> None:
        (out if started else lead).append(markup)

    for index, (block, (section, orientation)) in enumerate(zip(blocks, scopes, strict=True)):
        if block.kind == "h":
            nearest = _plain_text(block.text)
            if index == title_at:
                title = block.text
                previous = block
                continue
            slug = _slug(block.text, used, counters)
            is_orientation = block.text.strip().lower() in ORIENTATION
            if block.level <= 2:
                if started:
                    out.append("</div></section>")
                elif lead:
                    out.append(
                        '<section class="doc-section"><div class="doc-body">'
                        + "\n".join(lead)
                        + "</div></section>"
                    )
                started = True
                out.append(
                    f'<section class="doc-section" id="{slug}">'
                    f'<h2 class="margin-head">{_inline(block.text)}</h2><div class="doc-body">'
                )
            else:
                level = min(block.level, 6)
                emit(f'<h{level} id="{slug}">{_inline(block.text)}</h{level}>')
            if block.level <= 2 or is_orientation:
                rail.append(RailItem(slug, nearest, is_orientation and block.level > 2))
        elif block.kind == "p":
            if previous is not None and _is_sources_label(block):
                emit(f'<p class="part-head">{_inline(block.text)}</p>')
            elif section == "assessment charter":
                lines = "<br>".join(_inline(line) for line in block.text.split("\n"))
                emit(f"<p>{lines}</p>")
            else:
                emit(f"<p>{_inline(block.text.replace(chr(10), ' '))}</p>")
        elif block.kind in ("ul", "ol"):
            items = "".join(f"<li>{_inline(item)}</li>" for item in block.items)
            emit(f"<{block.kind}>{items}</{block.kind}>")
        elif block.kind == "table":
            sources = (
                orientation is not None
                and list(block.header) == SOURCES_HEADER
                and previous is not None
                and _is_sources_label(previous)
            )
            table = _table(block, sources, section == "attention heat map", counts)
            emit(_scroll_wrap(table, nearest))
        elif block.kind == "code":
            code = _scroll_wrap(f"<pre><code>{_esc(block.text)}</code></pre>", nearest, "source")
            if block.header and block.header[0].lower().split(None, 1)[:1] == ["mermaid"]:
                css_class, label = "diagram", DIAGRAM_LABEL
                if diagrams:
                    if not diagram_drawable(block.text):
                        label = DIAGRAM_LABEL_UNSAFE
                    elif drawn >= DIAGRAM_DRAW_LIMIT:
                        label = DIAGRAM_LABEL_LIMIT
                    else:
                        drawn += 1
                        css_class, label = "diagram diagram-drawn", DIAGRAM_LABEL_DRAWN
                emit(
                    f'<div class="{css_class}">'
                    f'<p class="diagram-label">{label}</p>{code}</div>'
                )
            else:
                emit(code)
        elif block.kind == "hr":
            emit("<hr>")
        previous = block
    if started:
        out.append("</div></section>")
    elif lead:
        out.append(
            '<section class="doc-section"><div class="doc-body">'
            + "\n".join(lead)
            + "</div></section>"
        )
    return title, "\n".join(out), rail, counts


class AssetError(Exception):
    """A stylesheet asset the renderer will not inline; carries its fixed stderr token."""

    def __init__(self, line: str) -> None:
        super().__init__(line)
        self.line = line


def load_stylesheet(helper: Any) -> str:
    """Return the base stylesheet, one newline, then the report layout file.

    Each asset is read through the confinement helper with a byte cap and refused before
    inlining when missing, too large, not UTF-8, or holding text that could end the style
    element or fetch a resource.
    """
    root = ASSET_DIR.parent
    texts: list[str] = []
    for name in ASSET_NAMES:
        try:
            data = helper.read_confined_regular_file(
                root, ASSET_DIR / name, max_bytes=MAX_ASSET_BYTES
            )
        except helper.BoundExceeded as error:
            raise AssetError(TOKEN_ASSET_LARGE) from error
        except (helper.UnsafeContentError, OSError) as error:
            raise AssetError(TOKEN_ASSET_MISSING) from error
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise AssetError(TOKEN_ASSET_NOT_UTF8) from error
        lowered = text.lower()
        if any(forbidden in lowered for forbidden in FORBIDDEN_ASSET_TEXT):
            raise AssetError(TOKEN_ASSET_FORBIDDEN)
        texts.append(text)
    return "\n".join(texts)


def load_script(helper: Any) -> str:
    """Return the diagrams script text, refused when missing, large, unreadable, or unsafe.

    The text is hashed for the policy and inlined, so it may not hold text that could end
    the script element, open a comment, or change under the parser's newline handling.
    """
    root = ASSET_DIR.parent
    try:
        data = helper.read_confined_regular_file(
            root, ASSET_DIR / SCRIPT_NAME, max_bytes=MAX_ASSET_BYTES
        )
    except helper.BoundExceeded as error:
        raise AssetError(TOKEN_SCRIPT_LARGE) from error
    except (helper.UnsafeContentError, OSError) as error:
        raise AssetError(TOKEN_SCRIPT_MISSING) from error
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AssetError(TOKEN_SCRIPT_UNREADABLE) from error
    lowered = text.lower()
    if any(forbidden in lowered for forbidden in FORBIDDEN_SCRIPT_TEXT):
        raise AssetError(TOKEN_SCRIPT_FORBIDDEN)
    return text


def _rail_links(rail: list[RailItem]) -> str:
    """Return the list items of the contents links."""
    return "".join(
        f'<li><a class="question-link{" rail-sub" if item.nested else ""}" '
        f'href="#{item.slug}">{_esc(item.text)}</a></li>'
        for item in rail
    )


def render(
    source: str, effort_name: str, today: str, css: str | None = None, script: str | None = None
) -> str:
    """Return the full HTML document for *source*, or raise Refusal.

    A *script* (the diagrams script text) turns on diagrams mode: eligible Mermaid fences are
    marked, two script elements are added after ``main``, and the policy names them.
    """
    if css is None:
        css = load_stylesheet(_load_helper())
    blocks = parse(source)
    title_at = _title_index(blocks)
    _check_orientation(blocks, title_at)
    scopes = _scopes(blocks, title_at)
    title, body, rail, counts = _body(blocks, scopes, title_at, script is not None)
    digest = base64.b64encode(hashlib.sha256(css.encode("utf-8")).digest()).decode()
    script_src = ""
    if script is not None:
        script_digest = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode()
        script_src = f"script-src 'sha256-{script_digest}' {MERMAID_URL}; "
    policy = (
        f"default-src 'none'; {script_src}style-src 'sha256-{digest}'; "
        "base-uri 'none'; form-action 'none'"
    )
    confirmed = _charter_checkpoint_confirmed(blocks, scopes)
    banner = "" if confirmed else f'<div class="alert banner-unconfirmed">{BANNER_TEXT}</div>'
    state = (
        '<span class="mark" data-mark="approved"><span class="mark-g" aria-hidden="true">'
        "\u25c6</span> Confirmed</span>"
        if confirmed
        else '<span class="mark" data-mark="draft"><span class="mark-g" aria-hidden="true">'
        "\u25c7</span> Unconfirmed</span>"
    )
    tally = "Sources: " + ", ".join(f"{counts[name]} {name}" for name in EVIDENCE_CLASSES)
    meta = (
        f'<p class="meta">Source: {_esc(effort_name)}/{SOURCE_NAME} \u00b7 '
        f"Generated {_esc(today)} UTC \u00b7 Renderer version {RENDERER_VERSION} \u00b7 "
        f"{state} \u00b7 {tally}</p>"
    )
    notice = f'<div class="note notice-untrusted">{NOTICE_TEXT}</div>'
    if script is not None:
        notice += f'\n<div class="note notice-diagrams">{DIAGRAMS_NOTE}</div>'
    scripts = (
        ""
        if script is None
        else (
            f'<script src="{MERMAID_URL}" integrity="{MERMAID_SRI}" crossorigin="anonymous" '
            f'referrerpolicy="no-referrer" defer></script><script>{script}</script>'
        )
    )
    links = _rail_links(rail)
    nav = (
        '<nav class="rail" aria-label="Report sections"><details class="key">'
        f"<summary>Contents ({len(rail)} sections)</summary>"
        f'<ul class="rail-list plain">{links}</ul></details>'
        f'<ul class="rail-wide plain">{links}</ul></nav>'
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        f'<meta http-equiv="Content-Security-Policy" content="{policy}">'
        f"<title>{_esc(title)}</title><style>{css}</style></head>\n"
        f'<body><a class="skip-link" href="#{REPORT_ID}">Skip to report</a>'
        f'<header class="page-header"><h1 class="page-title">{_esc(title)}</h1>{meta}</header>\n'
        f"{banner}\n{notice}\n{nav}\n"
        f'<main id="{REPORT_ID}">\n{body}\n</main>{scripts}</body></html>\n'
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
    """Load the co-located confinement helper by path under a private name, once."""
    global _HELPER
    if _HELPER is not None:
        return _HELPER
    path = Path(__file__).with_name("file_safety.py")
    inspected = os.lstat(path)
    if not stat.S_ISREG(inspected.st_mode):
        raise ImportError("helper is not a regular file")
    spec = importlib.util.spec_from_file_location("architect_assess_render_html_file_safety", path)
    if spec is None or spec.loader is None:
        raise ImportError("helper cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _HELPER = module
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
    if len(argv) not in (1, 2) or (len(argv) == 2 and argv[1] != "--diagrams"):
        print(TOKEN_USAGE, file=sys.stderr)
        return 2
    diagrams = len(argv) == 2
    missing = _missing_capability()
    if missing is not None:
        print(f"{TOKEN_HOST} {missing}", file=sys.stderr)
        return 3
    if not _supplied_path_is_safe(argv[0]):
        print(TOKEN_UNSAFE_PATH, file=sys.stderr)
        return 3
    helper = _load_helper()
    try:
        css = load_stylesheet(helper)
        script = load_script(helper) if diagrams else None
    except AssetError as error:
        print(error.line, file=sys.stderr)
        return 3
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
        page = render(source, root.name, today, css, script)
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
