"""Roster check: the shipped skill text names `workspace-status` as repair only.

Two layers. The retired-token, description and phrase checks are the contract.
The sentence pin is design: it keeps a status question from being routed to
`workspace-status` in the skill text that sends readers there.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS = REPO_ROOT / "packs" / "core" / ".apm" / "skills"

RETIRED_TOKENS = (
    "workspace-status status",
    "workspace-status reconcile",
    "workspace-status explain",
    "selected-membership",
    "retirement-candidates",
    "repair-rollback",
    "--migration-selection",
    "prune --select",
)
RETIRED_DESCRIPTION_WORDS = (
    "orient",
    "what's ready",
    "session start",
    "show the queue",
    "prune",
)
PIN_WORDS = (
    "status",
    "queue",
    "orient",
    "orientation",
    "ready",
    "next",
    "eligibility",
    "reconciliation",
    "backlog",
)

OWN_SKILL = SKILLS / "workspace-status" / "SKILL.md"
OWN_MUTATE = SKILLS / "workspace-status" / "references" / "mutate.md"
OTHER_MARKDOWN = (
    SKILLS / "work-loop" / "SKILL.md",
    SKILLS / "work-intake" / "SKILL.md",
    SKILLS / "navigate-intents" / "SKILL.md",
    SKILLS / "close-work" / "SKILL.md",
    SKILLS / "intake-intent" / "SKILL.md",
    SKILLS / "author-delivery-brief" / "SKILL.md",
    SKILLS / "new-spec" / "references" / "spec-and-plan-contract.md",
)
LISTED_MARKDOWN = (OWN_SKILL, OWN_MUTATE, *OTHER_MARKDOWN)


def _collapse(text: str) -> str:
    return " ".join(text.split())


def _json_strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _json_strings(item)


def retired_tokens_in(text: str) -> list[str]:
    collapsed = _collapse(text)
    return [token for token in RETIRED_TOKENS if token in collapsed]


def eval_json_files() -> list[Path]:
    return sorted(SKILLS.glob("*/evals/*.json"))


_BOUNDARY_LINE = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_NAME = re.compile(r"(?<![A-Za-z0-9_-])workspace-status(?![A-Za-z0-9_-])")


def sentences(text: str) -> list[str]:
    """Split raw text at sentence ends, blank lines, headings and list items."""
    chunks: list[list[str]] = [[]]
    for line in text.splitlines():
        if not line.strip() or _BOUNDARY_LINE.match(line):
            chunks.append([])
        if line.strip():
            chunks[-1].append(line)
    found: list[str] = []
    for chunk in chunks:
        for part in _SENTENCE_END.split("\n".join(chunk)):
            collapsed = _collapse(part)
            if collapsed:
                found.append(collapsed)
    return found


def status_routing_sentences(text: str) -> list[str]:
    """Return sentences naming `workspace-status` beside a listed word."""
    words = re.compile(
        r"(?<![A-Za-z0-9_-])(?:" + "|".join(PIN_WORDS) + r")(?![A-Za-z0-9_-])",
        re.IGNORECASE,
    )
    return [s for s in sentences(text) if _NAME.search(s) and words.search(s)]


def description_of(skill_md: str) -> str:
    match = re.search(r"^description:\s*(.+)$", skill_md, flags=re.MULTILINE)
    assert match, "SKILL.md carries no description line"
    return match.group(1)


@pytest.mark.parametrize("path", LISTED_MARKDOWN, ids=lambda p: str(p.relative_to(SKILLS)))
def test_no_retired_token_in_markdown(path: Path) -> None:
    assert retired_tokens_in(path.read_text(encoding="utf-8")) == []


def test_no_retired_token_in_any_eval_string() -> None:
    files = eval_json_files()
    assert files, "no eval JSON found"
    offenders = [
        (str(path.relative_to(SKILLS)), token)
        for path in files
        for value in _json_strings(json.loads(path.read_text(encoding="utf-8")))
        for token in retired_tokens_in(value)
    ]
    assert offenders == []


def test_description_names_no_orientation_phrase() -> None:
    description = _collapse(description_of(OWN_SKILL.read_text(encoding="utf-8"))).lower()
    assert [w for w in RETIRED_DESCRIPTION_WORDS if w in description] == []


def test_work_loop_names_the_captured_listing() -> None:
    assert "dispatch.py --captured" in _collapse(
        (SKILLS / "work-loop" / "SKILL.md").read_text(encoding="utf-8")
    )


def test_work_intake_routes_status_to_navigate_intents() -> None:
    assert "Route status directly to `navigate-intents`" in _collapse(
        (SKILLS / "work-intake" / "SKILL.md").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("path", OTHER_MARKDOWN, ids=lambda p: str(p.relative_to(SKILLS)))
def test_no_sentence_routes_a_status_question_to_workspace_status(path: Path) -> None:
    assert status_routing_sentences(path.read_text(encoding="utf-8")) == []


# The checks above must fail on the text they replace.


def test_token_check_fails_on_a_base_sentence() -> None:
    base = "Run `workspace-status\nreconcile` to list stale entries."
    assert retired_tokens_in(base) == ["workspace-status reconcile"]
    assert retired_tokens_in("Run `prune --select docs/x`.") == ["prune --select"]


def test_description_check_fails_on_a_base_description() -> None:
    base = "description: Use this skill to orient at session start."
    assert "orient" in description_of(base).lower()


def test_pin_fails_on_base_sentences() -> None:
    assert status_routing_sentences("Run `workspace-status`\nto see open backlog items.")
    assert status_routing_sentences("- Route status directly to `workspace-status`.")
    assert status_routing_sentences("`workspace-status` reconciliation matches it.")


def test_pin_passes_repair_sentences_and_joined_words() -> None:
    assert not status_routing_sentences("Send it to the `workspace-status` `intent-brief-drop` repair.")
    assert not status_routing_sentences("Use `workspace-status` for the next-step list. Status is elsewhere.")
    assert not status_routing_sentences("Use workspace-status-extra for queue order.")
    assert not status_routing_sentences("- Repair with `workspace-status`.\n- The queue is elsewhere.")
