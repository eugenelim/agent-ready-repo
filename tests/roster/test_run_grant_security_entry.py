"""Roster test: docs/architecture/security.md carries the run-grant trust-model entry."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SECURITY = ROOT / "docs/architecture/security.md"


def _entry() -> str:
    """The folded text of the run-grant section."""
    body = SECURITY.read_text(encoding="utf-8")
    parts = re.split(r"^## ", body, flags=re.MULTILINE)
    match = [p for p in parts if p.startswith(("10. A run grant", "11. A run grant"))]
    assert len(match) == 1
    return " ".join(match[0].split())


def test_entry_names_the_trust_model_and_every_unguarded_case() -> None:
    """Narrowing-only data, commit-anchored binding, guard conditions, base writer, spend."""
    e = _entry()
    for phrase in (
        "data with no authority",
        "only narrow",
        "Commit-anchored binding",
        "binds to the merged commit",
        "required check",
        "workflow the judged change cannot edit",
        "no such check runs, so nothing guards grant changes",
        "direct push or a bypassed check",
        "grant-enforcing code",
        "first adds the guard is judged by its own copy",
        "edit made after the stop",
        "edits brief, grant and record together",
        "Base-writer limit",
        "move the local base",
        "Spend is unbounded",
    ):
        assert phrase in e, phrase
