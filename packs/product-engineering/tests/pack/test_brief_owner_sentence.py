"""Brief-owner sentence and capability-map next-step contracts (AC-0008, AC-0009)."""

from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
APM = PACK_ROOT / ".apm"
SKILLS = APM / "skills"
SENTENCE = (
    "Never produce a brief: `lean-canvas` writes the one-page initiative brief "
    "and `author-delivery-brief` owns the delivery brief."
)
SENTENCE_SKILLS = (
    "frame-situation",
    "identify-opportunities",
    "diverge-solutions",
    "place-bet",
    "map-capabilities",
)
RETIRED = (
    "`place-bet` + `author-delivery-brief create`",
    "`lean-canvas` / `author-delivery-brief create` owns",
)
MAP = SKILLS / "map-capabilities"
MAPS = (
    MAP / "assets" / "capability-map-template.md",
    *sorted((MAP / "examples").glob("*/capability-map.md")),
)


def _flat(text: str) -> str:
    """Collapse presentation-only whitespace."""
    return " ".join(text.split())


def _retired_hits(files: dict[Path, str]) -> list[tuple[Path, str]]:
    """Return each (file, retired clause) pair found after whitespace collapse."""
    return [
        (path, clause)
        for path, text in files.items()
        for clause in RETIRED
        if clause in _flat(text)
    ]


def _apm_files() -> dict[Path, str]:
    """Every text file under the pack's `.apm/` tree."""
    return {
        path: path.read_text("utf-8")
        for path in sorted(APM.rglob("*"))
        if path.is_file()
    }


def _step_five() -> str:
    """The `map-capabilities` Emit step, up to the next numbered step."""
    text = (MAP / "SKILL.md").read_text("utf-8")
    return _flat(text.split("**5. Emit.**", 1)[1].split("**6.", 1)[0])


def _next_step_section(path: Path) -> str:
    """The `## Next step` section of a capability map."""
    text = path.read_text("utf-8")
    match = re.search(r"^## Next step\n(?P<body>.*?)(?=^## |\Z)", text, re.M | re.S)
    assert match, f"{path}: missing ## Next step"
    return _flat(match.group("body"))


def test_five_skills_carry_the_brief_owner_sentence() -> None:
    for name in SENTENCE_SKILLS:
        text = (SKILLS / name / "SKILL.md").read_text("utf-8")
        assert SENTENCE in _flat(text), name


def test_no_file_under_apm_keeps_a_retired_clause() -> None:
    assert _retired_hits(_apm_files()) == []


def test_mutation_that_re_adds_a_retired_clause_is_reported() -> None:
    files = _apm_files()
    victim = SKILLS / "place-bet" / "SKILL.md"
    files[victim] += "\n- Never produce a brief (`place-bet` +\n  `author-delivery-brief create` own it).\n"
    assert _retired_hits(files) == [(victim, RETIRED[0])]


def test_step_five_always_ends_with_a_next_step_section_naming_intent_decompose() -> None:
    step = _step_five()
    assert "`## Next step`" in step
    assert "`intent decompose`" in step
    assert "not detected" not in step
    assert "Next step readiness" not in step
    assert "author-delivery-brief create" not in step
    assert "lean-canvas" not in step


def test_every_capability_map_names_intent_decompose_as_the_next_step() -> None:
    assert len(MAPS) >= 3
    for path in MAPS:
        section = _next_step_section(path)
        assert "`intent decompose`" in section, path
        assert "capability-level child intent" in section, path
        assert "lean-canvas" not in section, path
        assert "author-delivery-brief create" not in section, path
        assert "Next step readiness" not in path.read_text("utf-8"), path
