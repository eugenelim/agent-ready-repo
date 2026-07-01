#!/usr/bin/env python3
"""
html_md.py — an HTML → Markdown reducer built on the stdlib ``html.parser``.

This is the ``file-to-markdown`` reducer's *technique* (stdlib ``html.parser``,
no new dependency), re-implemented here rather than vendored: the floor's reducer
is an inline nested class in ``file-to-markdown/convert.py`` and it emits coarse
*text*, whereas an email body needs richer **Markdown** — headings, bold/italic,
links, lists, and tables (spec AC4). Extracting the floor's version would edit the
shipped floor skill (out of scope), so this is the skill's own module.

``convert_charrefs=True`` handles entity unescaping (``&amp;`` → ``&`` etc.) for
free. Unknown tags are dropped; ``script``/``style`` content is skipped.
"""
from __future__ import annotations

from html.parser import HTMLParser

_HEADINGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}
_BLOCK = {"p", "div", "section", "article", "blockquote", "header", "footer"}
_SKIP = {"script", "style", "head", "title"}


class _MarkdownReducer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self._skip_depth = 0
        self._list_stack: list[dict] = []      # {"type": ul|ol, "n": int}
        # Table state: rows accumulate cells; first row is treated as header.
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._pending_heading: str | None = None

    # -- helpers --
    def _emit(self, text: str) -> None:
        if self._cell is not None:
            self._cell.append(text)
        else:
            self.out.append(text)

    def _newline(self) -> None:
        if self._cell is None:
            self.out.append("\n")

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in _HEADINGS:
            self._newline()
            self._newline()
            self._pending_heading = _HEADINGS[tag]
            self._emit(_HEADINGS[tag] + " ")
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "a":
            href = dict(attrs).get("href")
            self._emit("[")
            self._link_href = href or ""
        elif tag == "br":
            self._newline()
        elif tag == "ul":
            self._list_stack.append({"type": "ul", "n": 0})
            self._newline()
        elif tag == "ol":
            self._list_stack.append({"type": "ol", "n": 0})
            self._newline()
        elif tag == "li":
            self._newline()
            indent = "  " * (len(self._list_stack) - 1)
            if self._list_stack and self._list_stack[-1]["type"] == "ol":
                self._list_stack[-1]["n"] += 1
                self._emit(f"{indent}{self._list_stack[-1]['n']}. ")
            else:
                self._emit(f"{indent}- ")
        elif tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag in _BLOCK:
            self._newline()
            self._newline()

    def handle_endtag(self, tag):
        if tag in _SKIP:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in _HEADINGS:
            self._newline()
            self._newline()
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "a":
            href = getattr(self, "_link_href", "")
            self._emit(f"]({href})")
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
            self._newline()
        elif tag in ("td", "th") and self._cell is not None:
            self._row.append("".join(self._cell).strip().replace("\n", " "))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._table is not None:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self._flush_table()
            self._table = None
        elif tag in _BLOCK:
            self._newline()

    def handle_data(self, data):
        if self._skip_depth:
            return
        if not data.strip() and self._cell is None:
            # Collapse inter-tag whitespace to a single space in flowing text.
            if self.out and not self.out[-1].endswith((" ", "\n")):
                self.out.append(" ")
            return
        self._emit(data)

    def _flush_table(self):
        rows = [r for r in self._table if r]
        if not rows:
            return
        ncol = max(len(r) for r in rows)
        self.out.append("\n")
        header = rows[0] + [""] * (ncol - len(rows[0]))
        self.out.append("| " + " | ".join(header) + " |\n")
        self.out.append("| " + " | ".join("---" for _ in header) + " |\n")
        for r in rows[1:]:
            r = r + [""] * (ncol - len(r))
            self.out.append("| " + " | ".join(r) + " |\n")
        self.out.append("\n")

    def result(self) -> str:
        text = "".join(self.out)
        # Normalise runs of blank lines and trailing spaces per line.
        lines = [ln.rstrip() for ln in text.split("\n")]
        cleaned: list[str] = []
        for ln in lines:
            if ln == "" and cleaned and cleaned[-1] == "":
                continue
            cleaned.append(ln)
        return "\n".join(cleaned).strip()


def html_to_markdown(html: str) -> str:
    """Reduce an HTML fragment/document to Markdown via stdlib ``html.parser``."""
    reducer = _MarkdownReducer()
    reducer.feed(html)
    reducer.close()
    return reducer.result()
