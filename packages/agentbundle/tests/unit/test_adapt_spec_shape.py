"""T7: spec-shape tests for docs/specs/adapt-to-project/spec.md.

Four construction tests verify that the adapt-to-project spec carries
the AC16-mandated AC24/AC25/AC26 entries and Changelog line added by
docs/specs/claude-plugins-install-route/spec.md.

AC16 (claude-plugins-install-route spec): ``adapt-to-project/spec.md``
Acceptance Criteria gains three new entries (AC24 read-side fallback,
AC25 proactive cache-scan idempotence, AC26 stale-entry drop-on-read).

Tests use anchored regex patterns so each assertion fires on an
unchecked-checkbox AC entry at the start of a line, not on a stray
occurrence elsewhere in the document.
"""

from __future__ import annotations

import re
from pathlib import Path

# Repo-relative anchor: this file lives at
# packages/agentbundle/tests/unit/test_adapt_spec_shape.py
_REPO_ROOT = Path(__file__).resolve().parents[4]
_SPEC = (
    _REPO_ROOT
    / "docs"
    / "specs"
    / "adapt-to-project"
    / "spec.md"
)


def _body() -> str:
    assert _SPEC.exists(), f"adapt-to-project spec not found at {_SPEC}"
    return _SPEC.read_text(encoding="utf-8")


def test_adapt_spec_has_ac24_read_side_fallback() -> None:
    """AC16: adapt-to-project spec carries an AC24 unchecked-checkbox entry.

    Anchored regex: asserts a line starting with ``- [ ] **AC24`` so the
    string must appear as an unchecked AC checkbox at the start of a line.
    """
    body = _body()
    pattern = r"^- \[ \] \*\*AC24"
    assert re.search(pattern, body, re.MULTILINE), (
        "docs/specs/adapt-to-project/spec.md Acceptance Criteria must contain "
        "an unchecked checkbox entry for AC24 (read-side fallback contract). "
        f"Pattern: {pattern!r}"
    )


def test_adapt_spec_has_ac25_proactive_cache_scan_idempotence() -> None:
    """AC16: adapt-to-project spec carries an AC25 unchecked-checkbox entry.

    Anchored regex: asserts a line starting with ``- [ ] **AC25`` so the
    string must appear as an unchecked AC checkbox at the start of a line.
    """
    body = _body()
    pattern = r"^- \[ \] \*\*AC25"
    assert re.search(pattern, body, re.MULTILINE), (
        "docs/specs/adapt-to-project/spec.md Acceptance Criteria must contain "
        "an unchecked checkbox entry for AC25 (proactive cache-scan idempotence). "
        f"Pattern: {pattern!r}"
    )


def test_adapt_spec_has_ac26_stale_entry_drop_on_read() -> None:
    """AC16: adapt-to-project spec carries an AC26 unchecked-checkbox entry.

    Anchored regex: asserts a line starting with ``- [ ] **AC26`` so the
    string must appear as an unchecked AC checkbox at the start of a line.
    """
    body = _body()
    pattern = r"^- \[ \] \*\*AC26"
    assert re.search(pattern, body, re.MULTILINE), (
        "docs/specs/adapt-to-project/spec.md Acceptance Criteria must contain "
        "an unchecked checkbox entry for AC26 (stale-entry drop-on-read). "
        f"Pattern: {pattern!r}"
    )


def test_adapt_spec_changelog_names_this_spec() -> None:
    """AC16: adapt-to-project spec Changelog contains a dated line naming this spec.

    Anchored regex: asserts a Changelog bullet of the form
    ``- 2026-<MM>-<DD>: ...claude-plugins-install-route...``
    so the reference must appear in a dated changelog entry, not anywhere
    in the document.
    """
    body = _body()
    pattern = r"^- 2026-\d{2}-\d{2}:.*claude-plugins-install-route"
    assert re.search(pattern, body, re.MULTILINE), (
        "docs/specs/adapt-to-project/spec.md Changelog must contain a dated "
        "bullet that references 'claude-plugins-install-route'. "
        f"Pattern: {pattern!r}"
    )
