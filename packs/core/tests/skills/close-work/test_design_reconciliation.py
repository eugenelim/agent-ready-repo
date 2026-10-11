"""Design reconciliation in close-work step 4 stays Core-only.

Covers AC-0012, AC-0013 (eval id) and the Core README phrase of AC-0014 of
``docs/specs/architect-shaping-reach/``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CORE = Path(__file__).resolve().parents[3]
SKILL_DIR = CORE / ".apm" / "skills" / "close-work"
SKILL = SKILL_DIR / "SKILL.md"
EVALS = SKILL_DIR / "evals" / "evals.json"
README = CORE / "README.md"
FORBIDDEN = re.compile(r"\barchitect\b|architect-", re.IGNORECASE)


def _collapse(text: str) -> str:
    """Collapse every whitespace run to one space."""
    return " ".join(text.split())


def _step4() -> str:
    """Return the whitespace-collapsed text of numbered step 4."""
    match = re.search(r"^4\. .*?(?=^5\. )", SKILL.read_text(), re.S | re.M)
    assert match, "step 4 not found"
    return _collapse(match.group(0))


def test_step4_offers_reconciliation_under_confirmation() -> None:
    """Step 4 carries the reconciliation offer and its guards."""
    step = _step4()
    for phrase in (
        "`architecture-design`",
        "offer to reconcile it into the resolved `current-architecture` surface",
        "Apply it only under step 7's confirmation",
        "never overwrite a current-architecture source without per-file acceptance",
    ):
        assert phrase in step, phrase


def test_core_files_never_name_the_architect_pack() -> None:
    """No line of the three Core files matches the forbidden pattern."""
    for path in (SKILL, EVALS, README):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            assert not FORBIDDEN.search(line), f"{path.name}:{number}"


def test_eval_case_exists() -> None:
    """The reconcile-implemented-design eval case is present."""
    cases = json.loads(EVALS.read_text())["evals"]
    assert "reconcile-implemented-design" in [c.get("id") for c in cases]


def test_readme_names_reconciliation() -> None:
    """The Core README states the behaviour."""
    phrase = "reconcile an implemented future-state design into current architecture"
    assert phrase in _collapse(README.read_text())
