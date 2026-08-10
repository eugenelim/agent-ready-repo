"""T10: shape tests for docs/specs/adapt-to-project/notes/manual-qa-matrix.md.

Construction tests verify that the manual-QA matrix carries the rows required
by AC19 of docs/specs/claude-plugins-install-route/spec.md.

AC19 originally required three rows. Row (a) — "claude-plugins install of core
at project scope" — was **retired** by that spec's 2026-08-08 erratum: `core`
declares `allowed-scopes = ["repo"]` and is no longer published to the
Claude-plugin route, so the scenario is not executable. The erratum retires the
requirement; this test does not silently drop it.

Remaining rows:
  (b) claude-plugins install of converters at user scope
  (c) proactive cache scan idempotence — marker entry present, no double-adapt

All three rows record ``verification = transcript`` (deferred per the
matrix's existing deferral pattern).
"""

from __future__ import annotations

from pathlib import Path

# Repo-relative anchor: this file lives under tests/roster/.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_MATRIX = (
    _REPO_ROOT
    / "docs"
    / "specs"
    / "adapt-to-project"
    / "notes"
    / "manual-qa-matrix.md"
)


def _body() -> str:
    assert _MATRIX.exists(), f"manual-qa-matrix not found at {_MATRIX}"
    return _MATRIX.read_text(encoding="utf-8")


def test_manual_qa_matrix_has_claude_plugins_converters_row() -> None:
    """AC19: matrix contains a row naming claude-plugins install of converters at user scope."""
    body = _body()
    assert "claude-plugins install of converters at user scope" in body, (
        "docs/specs/adapt-to-project/notes/manual-qa-matrix.md must contain a row "
        "naming 'claude-plugins install of converters at user scope'. "
        "Required by AC19 of docs/specs/claude-plugins-install-route/spec.md."
    )


def test_manual_qa_matrix_has_proactive_cache_scan_idempotence_row() -> None:
    """AC19: matrix contains a row naming proactive cache scan idempotence."""
    body = _body()
    assert "proactive cache scan idempotence — marker entry present, no double-adapt" in body, (
        "docs/specs/adapt-to-project/notes/manual-qa-matrix.md must contain a row "
        "naming 'proactive cache scan idempotence — marker entry present, no double-adapt'. "
        "Required by AC19 of docs/specs/claude-plugins-install-route/spec.md (end-to-end pin for AC25)."  # noqa: E501
    )


def test_manual_qa_matrix_new_rows_carry_verification_transcript() -> None:
    """AC19: each of the three new rows declares verification = transcript.

    For each new row, assert the ``verification = transcript`` token appears
    within the same table row (pipe-delimited line) as the row's identifying
    substring.
    """
    body = _body()

    # Row 29 (core at project scope) retired by the claude-plugins-install-route
    # spec's 2026-08-08 erratum — `core` is repo-only and no longer published to
    # the Claude-plugin route, so the scenario is not executable.
    rows_and_markers = [
        (
            "claude-plugins install of converters at user scope",
            "Row 30 (converters at user scope)",
        ),
        (
            "proactive cache scan idempotence — marker entry present, no double-adapt",
            "Row 31 (proactive cache scan idempotence)",
        ),
    ]

    for identifying_text, row_label in rows_and_markers:
        matching_lines = [
            line for line in body.splitlines() if identifying_text in line
        ]
        assert matching_lines, (
            f"{row_label}: no line in the matrix contains the identifying text "
            f"{identifying_text!r}."
        )
        for line in matching_lines:
            assert "verification = transcript" in line, (
                f"{row_label}: the row containing {identifying_text!r} must also "
                f"contain 'verification = transcript'. Got line: {line!r}"
            )
