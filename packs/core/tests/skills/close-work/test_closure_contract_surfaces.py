"""
Goal-based checks for AC-0033 and AC-0036.

AC-0033: close-work/SKILL.md § Closeout procedure states the trigger, all three
         verdict names as a set, and the closure record. Scoped to that section's
         body only — the file already contains 13 occurrences of refusal and
         eligibility wording in its § Disposition contract, so a document-wide
         substring check passes before any work is done.

AC-0036: guides/core/how-to/close-and-disposition-work.md § Review the closeout
         preview names all three verdicts and says what a human decides at each.
         Scoped to that section's body only.
"""

from __future__ import annotations

import re
from pathlib import Path

# Locate repository root relative to this file:
# packs/core/tests/skills/close-work/ → packs/core/tests/skills/
#   → packs/core/tests/ → packs/core/ → packs/ → <repo-root>
_TESTS_DIR = Path(__file__).parent
_REPO_ROOT = _TESTS_DIR.parents[4]

_SKILL_PATH = _REPO_ROOT / "packs/core/.apm/skills/close-work/SKILL.md"
_GUIDE_PATH = _REPO_ROOT / "guides/core/how-to/close-and-disposition-work.md"

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
# AC-0033 — § Closeout procedure in SKILL.md
# ---------------------------------------------------------------------------


def test_ac0033_closeout_procedure_states_trigger() -> None:
    """The Closeout procedure section mentions when the closure check fires."""
    text = _SKILL_PATH.read_text(encoding="utf-8")
    section = _extract_section(text, "Closeout procedure")
    assert "terminal state" in section, (
        "§ Closeout procedure must state when the closure check fires "
        "(expected 'terminal state')"
    )


def test_ac0033_closeout_procedure_states_all_three_verdicts() -> None:
    """The Closeout procedure section names refuse, not-eligible, and eligible."""
    text = _SKILL_PATH.read_text(encoding="utf-8")
    section = _extract_section(text, "Closeout procedure")
    missing = {v for v in _VERDICT_NAMES if not _VERDICT_PATTERNS[v].search(section)}
    assert not missing, (
        f"§ Closeout procedure is missing verdict name(s): {sorted(missing)}"
    )


def test_ac0033_closeout_procedure_states_closure_record() -> None:
    """The Closeout procedure section mentions the closure record."""
    text = _SKILL_PATH.read_text(encoding="utf-8")
    section = _extract_section(text, "Closeout procedure")
    assert "closure record" in section, (
        "§ Closeout procedure must describe the closure record"
    )


def test_ac0033_scoped_to_section_not_whole_document() -> None:
    """The SKILL.md § Disposition contract is NOT the source of the verdict names.

    The spec notes that the file already carries 13 occurrences of refusal and
    eligibility wording in § Disposition contract, so a document-wide check
    would pass even with an empty Closeout procedure section. This test
    confirms the section extractor does NOT include Disposition contract text.
    """
    text = _SKILL_PATH.read_text(encoding="utf-8")
    closeout_section = _extract_section(text, "Closeout procedure")
    disposition_section = _extract_section(text, "Disposition contract")
    # The two extracted bodies must be disjoint — if Disposition content leaked
    # into the Closeout extraction, the scoping is wrong.
    assert "Eligibility now" not in closeout_section, (
        "§ Closeout procedure body must not contain § Disposition contract text "
        "(section extraction is not properly scoped)"
    )
    assert "Eligibility now" in disposition_section, (
        "Sanity: '§ Disposition contract' body should contain its own header text"
    )


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
