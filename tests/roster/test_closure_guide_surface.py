"""
Goal-based check for AC-0036 of the closure-eligibility-check spec.

The spec is named without its path on purpose. A `docs/specs/<slug>` literal
in a roster test declares that the test depends on that directory, and the
protected manifest must then carry it so a prune cannot remove it. This test
reads `guides/`, not the spec, so the dependency would be false.

The reader-facing guide's § Review the closeout preview names all three
verdicts and says what a human decides at each. Scoped to that section's body:
a document-wide substring check passes before any work is done.

This lives in the roster rather than beside its sibling pack test because it
reads `guides/`, which is repository content. A pack test that reaches above
its owning pack is refused by `tools/lint-pack-test-boundary.py`.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GUIDE_PATH = _REPO_ROOT / "guides" / "core" / "how-to" / "close-and-disposition-work.md"


_VERDICT_NAMES = frozenset({"refuse", "not-eligible", "eligible"})

# Patterns that match the exact verdict word, not substrings.  "refuse" must
# match the verb/noun exactly and NOT match "refused" or "refusal" (both of
# which appear in the § Closeout procedure body before T8's addition).
# "eligible" must not match "ineligible".  "not-eligible" is unique and can be
# matched as a plain substring, but we use the same regex form for consistency.
_VERDICT_PATTERNS: dict[str, re.Pattern[str]] = {
    v: re.compile(rf"\b{re.escape(v)}\b") for v in _VERDICT_NAMES
}


def _extract_section(text: str, heading: str) -> str:
    """Return the body of an H2 section (text after the heading up to the next H2)."""
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    m = pattern.search(text)
    if m is None:
        raise ValueError(f"Section '## {heading}' not found in document")
    start = m.end()
    next_h2 = re.search(r"^## ", text[start:], re.MULTILINE)
    return text[start : start + next_h2.start()] if next_h2 else text[start:]


# ---------------------------------------------------------------------------
# AC-0036 — § Review the closeout preview in the guide
# ---------------------------------------------------------------------------


def test_ac0036_review_section_names_all_three_verdicts() -> None:
    """§ Review the closeout preview names refuse, not-eligible, and eligible."""
    text = _GUIDE_PATH.read_text(encoding="utf-8")
    section = _extract_section(text, "Review the closeout preview")
    missing = {v for v in _VERDICT_NAMES if not _VERDICT_PATTERNS[v].search(section)}
    assert not missing, (
        f"§ Review the closeout preview is missing verdict name(s): {sorted(missing)}"
    )


def test_ac0036_review_section_says_what_to_decide() -> None:
    """§ Review the closeout preview describes what the human decides at each verdict."""
    text = _GUIDE_PATH.read_text(encoding="utf-8")
    section = _extract_section(text, "Review the closeout preview")
    # The guide uses "What you decide" as a table column header.
    assert "you decide" in section.lower(), (
        "§ Review the closeout preview must state what the human decides at each verdict"
    )
