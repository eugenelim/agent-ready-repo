"""Contract checks for align-value-stream's hard-limits README proposal."""

from __future__ import annotations

import json
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2] / ".apm/skills/align-value-stream"
SKILL = SKILL_DIR / "SKILL.md"
ASSET = SKILL_DIR / "assets/hard-limits.md"
PHRASES = ("no atomic cross-repo commit", "no shared release train", "snapshot, not a live feed")


def _norm(text: str) -> str:
    """Lowercase, drop emphasis marks, and collapse whitespace."""
    return " ".join(text.replace("*", "").replace("_", " ").lower().split())


def _present(text: str) -> list[str]:
    """Return the limit phrases found in a text after normalising."""
    plain = _norm(text)
    return [p for p in PHRASES if p in plain]


def _items(text: str) -> list[str]:
    """Return the top-level list items of a Markdown text."""
    return re.findall(r"^- (.+)$", text, flags=re.MULTILINE)


def _step_one(text: str) -> str:
    """Return step 1 of the procedure, normalised."""
    procedure = text.split("## Procedure", 1)[1]
    match = re.search(r"^1\. (.*?)(?=^2\. )", procedure, flags=re.MULTILINE | re.DOTALL)
    assert match
    return _norm(match.group(1))


def _step_one_problems(text: str) -> list[str]:
    """Report missing asset, README, or confirmation references in step 1."""
    step = _step_one(text)
    needed = ("assets/hard-limits.md", "readme", "confirms")
    return [n for n in needed if n not in step]


def test_asset_has_exactly_three_named_items() -> None:
    text = ASSET.read_text(encoding="utf-8")
    assert text.startswith("## Hard limits")
    items = _items(text)
    assert len(items) == 3
    assert _present(text) == list(PHRASES)
    for item, phrase in zip(items, PHRASES, strict=True):
        assert phrase in _norm(item)


def test_step_one_proposes_the_asset_for_the_readme() -> None:
    assert _step_one_problems(SKILL.read_text(encoding="utf-8")) == []


def test_skill_does_not_restate_the_limits() -> None:
    assert _present(SKILL.read_text(encoding="utf-8")) == []


def test_mutation_restating_a_limit_is_reported() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert _present(text + "\nThere is **no  shared\nrelease train**.\n") == [PHRASES[1]]


def test_mutation_dropping_confirmation_is_reported() -> None:
    text = SKILL.read_text(encoding="utf-8").replace("confirms", "agrees")
    assert _step_one_problems(text) == ["confirms"]


def test_eval_cases_exist_with_assertions() -> None:
    data = json.loads((SKILL_DIR / "evals/evals.json").read_text(encoding="utf-8"))
    cases = {str(c["id"]): c for c in data["evals"]}
    for case_id in ("solution-reference-offer-architect-absent-silent", "hard-limits-readme-proposal"):
        assert len(cases[case_id]["assertions"]) >= 3
    silent = cases["solution-reference-offer-architect-absent-silent"]["assertions"]
    assert any(a.startswith("Does not mention") for a in silent)
