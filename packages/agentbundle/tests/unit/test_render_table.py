"""Unit tests for `commands/_common.render_table`.

The shared terminal-aware table printer behind `list-packs` / `list-profiles`.
Pins the width contract: non-TTY emits full-width untruncated columns (so piped
output stays grep/awk-stable); an interactive TTY whose width the natural table
would overflow word-wraps the flex column, keeping every physical line within
the terminal and aligning continuation lines under that column; a TTY wide
enough leaves the table unwrapped.
"""

from __future__ import annotations

import io

from agentbundle.commands._common import _MIN_WRAP_WIDTH, render_table

HEADERS = ["NAME", "VERSION", "DESCRIPTION", "DEPS"]
LONG = "Core agent-ready-repo: work-loop, new-spec and bug-fix skills for agents."
ROWS = [
    ["core", "0.4.14", LONG, "-"],
    ["research", "0.3.0", "Evidence-grounded research portable across every repo.", "core@^0.1"],
]


class _FakeTTY(io.StringIO):
    """A StringIO that claims to be an interactive terminal."""

    def isatty(self) -> bool:  # noqa: D401 - trivial
        return True


def _set_width(monkeypatch, cols: int) -> None:
    import os
    import shutil

    monkeypatch.setattr(
        shutil, "get_terminal_size", lambda fallback=(80, 24): os.terminal_size((cols, 24))
    )


# ---------------------------------------------------------------------------
# 1. Non-TTY → full content width, never wrapped, never truncated
# ---------------------------------------------------------------------------

def test_non_tty_emits_full_width_untruncated(monkeypatch):
    # Even a tiny "terminal" is irrelevant when the stream is not a TTY.
    _set_width(monkeypatch, 40)
    buf = io.StringIO()  # plain StringIO → isatty() is False
    render_table(HEADERS, ROWS, wrap_col=2, stream=buf)
    out = buf.getvalue()
    # The long description appears intact on a single line — no wrap, no ellipsis.
    assert LONG in out
    assert all(len(line) == 0 or "  " in line for line in out.splitlines())


def test_non_tty_has_no_trailing_whitespace(monkeypatch):
    _set_width(monkeypatch, 40)
    buf = io.StringIO()
    render_table(HEADERS, ROWS, wrap_col=2, stream=buf)
    for line in buf.getvalue().splitlines():
        assert line == line.rstrip(), "rows must not carry trailing whitespace"


# ---------------------------------------------------------------------------
# 2. TTY narrow → wrap the flex column, every line fits
# ---------------------------------------------------------------------------

def test_tty_narrow_wraps_within_width(monkeypatch):
    _set_width(monkeypatch, 80)
    buf = _FakeTTY()
    render_table(HEADERS, ROWS, wrap_col=2, stream=buf)
    lines = buf.getvalue().splitlines()
    assert all(len(line) <= 80 for line in lines), "no physical line may exceed the terminal"
    # The description wrapped — its text spans more than one physical line.
    assert len(lines) > 1 + 1 + len(ROWS), "wrapping should add continuation lines"


def test_tty_continuation_lines_align_under_flex_column(monkeypatch):
    _set_width(monkeypatch, 80)
    buf = _FakeTTY()
    render_table(HEADERS, ROWS, wrap_col=2, stream=buf)
    lines = buf.getvalue().splitlines()
    # Column start of DESCRIPTION = len("NAME"/"core" widths) deduced from header.
    header = lines[0]
    desc_start = header.index("DESCRIPTION")
    # A continuation line is one whose leading run is all spaces up to desc_start.
    cont = [line for line in lines if line[:desc_start].strip() == "" and line.strip()]
    assert cont, "expected at least one indented continuation line"
    for line in cont:
        assert line[:desc_start] == " " * desc_start


def test_tty_following_column_only_on_first_line(monkeypatch):
    _set_width(monkeypatch, 80)
    buf = _FakeTTY()
    render_table(HEADERS, ROWS, wrap_col=2, stream=buf)
    out = buf.getvalue()
    # The dependency token sits on a first row line, never repeated on a
    # wrapped continuation line.
    assert out.count("core@^0.1") == 1


# ---------------------------------------------------------------------------
# 3. TTY wide enough → no wrapping (byte-identical to the simple table)
# ---------------------------------------------------------------------------

def test_tty_wide_does_not_wrap(monkeypatch):
    _set_width(monkeypatch, 200)
    tty = _FakeTTY()
    render_table(HEADERS, ROWS, wrap_col=2, stream=tty)

    plain = io.StringIO()
    render_table(HEADERS, ROWS, wrap_col=2, stream=plain)
    assert tty.getvalue() == plain.getvalue()


# ---------------------------------------------------------------------------
# 4. Degenerate width → clamp to the floor, do not shred to one char per line
# ---------------------------------------------------------------------------

def test_tty_tiny_width_clamps_to_floor(monkeypatch):
    import textwrap

    _set_width(monkeypatch, 10)  # below the floor → must clamp to _MIN_WRAP_WIDTH
    buf = _FakeTTY()
    render_table(HEADERS, ROWS, wrap_col=2, stream=buf)
    lines = [line for line in buf.getvalue().splitlines() if line.strip()]

    # The description column must have been clamped to the floor, not collapsed
    # toward the 10-col terminal. On a continuation line (NAME/VERSION blank) the
    # wrapped chunk stands alone, so its width is the chunk width — the widest
    # must equal the widest chunk textwrap produces at the floor width.
    desc_start = lines[0].index("DESCRIPTION")
    cont = [line for line in lines if line[:desc_start].strip() == "" and line.strip()]
    cont_widths = [len(line.strip()) for line in cont]
    expected_max = max(len(chunk) for chunk in textwrap.wrap(LONG, _MIN_WRAP_WIDTH))
    assert max(cont_widths) == expected_max
    assert expected_max <= _MIN_WRAP_WIDTH


# ---------------------------------------------------------------------------
# 5. wrap_col=None → no wrapping even on a narrow TTY
# ---------------------------------------------------------------------------

def test_no_wrap_col_never_wraps(monkeypatch):
    _set_width(monkeypatch, 40)
    buf = _FakeTTY()
    render_table(HEADERS, ROWS, wrap_col=None, stream=buf)
    assert LONG in buf.getvalue()


# ---------------------------------------------------------------------------
# 6. Empty body → header + separator only, no crash
# ---------------------------------------------------------------------------

def test_empty_rows_prints_header_and_separator():
    buf = io.StringIO()
    render_table(HEADERS, [], wrap_col=2, stream=buf)
    lines = buf.getvalue().splitlines()
    assert lines[0].startswith("NAME")
    assert set(lines[1].replace(" ", "")) == {"-"}
    assert len(lines) == 2
