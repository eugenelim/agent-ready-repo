"""Conditional LLD design-prompt contracts for new-spec."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
PLAN_ASSET = PACK_ROOT / ".apm/skills/new-spec/assets/plan.md"

LLD_SECTION = re.compile(
    r"^## Design \(LLD\)\n(?P<body>.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL
)
LLD_SUBSECTION = re.compile(
    r"^### (?P<title>.+?)\n(?P<body>.*?)(?=^### |^## |\Z)",
    re.MULTILINE | re.DOTALL,
)

PROMPTS = (
    (
        "State & control flow",
        re.compile(
            r"When state changes concurrently, name concurrency, consistency,\s*"
            r"locking, atomicity, and transaction boundaries\."
        ),
    ),
    (
        "Failure, edge cases & resilience",
        re.compile(
            r"When external failures are possible, name stable error classes,\s*"
            r"retryability, and external failure mapping\."
        ),
    ),
    (
        "Quality attributes (NFRs)",
        re.compile(
            r"When this feature needs operational visibility, name a concrete\s*"
            r"observability surface\."
        ),
    ),
    (
        "Data & schema",
        re.compile(
            r"When this feature migrates existing data, name backfill checkpointing,\s*"
            r"restartability, and cutover validation\."
        ),
    ),
    (
        "Interfaces & contracts",
        re.compile(
            r"When this feature crosses a boundary, name a test seam for each\s*"
            r"crossed boundary\."
        ),
    ),
)

UNCONDITIONAL_REQUIREMENT_WORDS = re.compile(
    r"\b(always|required|must|shall)\b", re.IGNORECASE
)


def _subsections(text: str) -> dict[str, str]:
    """Return the Design (LLD) sub-section bodies by title."""
    section = LLD_SECTION.search(text)
    assert section is not None
    return {
        subsection.group("title"): subsection.group("body")
        for subsection in LLD_SUBSECTION.finditer(section.group("body"))
    }


def _assert_conditional_design_prompts(text: str) -> None:
    """Assert every conditional design prompt remains in its named section."""
    subsections = _subsections(text)
    for title, prompt in PROMPTS:
        body = subsections[title]
        assert prompt.search(body) is not None, (
            f"{title} must retain its conditional design prompt"
        )
        wrong_sections = [
            other_title
            for other_title, other_body in subsections.items()
            if other_title != title and prompt.search(other_body) is not None
        ]
        assert not wrong_sections, (
            f"{title} design prompt appears outside its sub-section: "
            f"{wrong_sections}"
        )


def _matched_prompt_text(text: str, title: str, prompt: re.Pattern[str]) -> str:
    """Return the prompt text matched inside its expected LLD sub-section."""
    match = prompt.search(_subsections(text)[title])
    assert match is not None, f"{title} must retain its conditional design prompt"
    return match.group(0)


def test_lld_subsections_document_conditional_design_prompts() -> None:
    _assert_conditional_design_prompts(PLAN_ASSET.read_text(encoding="utf-8"))


@pytest.mark.parametrize("title,prompt", PROMPTS)
def test_lld_design_prompts_are_conditional(
    title: str, prompt: re.Pattern[str]
) -> None:
    prompt_text = _matched_prompt_text(
        PLAN_ASSET.read_text(encoding="utf-8"), title, prompt
    )

    assert prompt_text.startswith("When ")
    assert UNCONDITIONAL_REQUIREMENT_WORDS.search(prompt_text) is None


@pytest.mark.parametrize("title,prompt", PROMPTS)
def test_lld_conditional_design_prompts_reject_removal(
    title: str, prompt: re.Pattern[str]
) -> None:
    text = PLAN_ASSET.read_text(encoding="utf-8")
    subsection = _subsections(text)[title]
    match = prompt.search(subsection)
    assert match is not None

    start = text.index(subsection) + match.start()
    end = text.index(subsection) + match.end()
    mutated = text[:start] + text[end:]

    with pytest.raises(AssertionError, match=re.escape(title)):
        _assert_conditional_design_prompts(mutated)
