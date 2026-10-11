"""Contract checks for the optional architect offers in product-engineering.

Every architect offer must be conditional on the roster check and followed, in
the same paragraph, by one silent clause. The pack never depends on, names the
absence of, or asks the user to install the architect pack.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILLS = PACK_ROOT / ".apm/skills"
SILENT = (
    "If it is not in the roster, continue with this skill's own behaviour and "
    "say nothing about it: no mention, no note, and no error."
)
OFFER_SKILLS = (
    "frame-domain",
    "frame-intent",
    "de-risk-intent",
    "decompose-intent",
    "map-capabilities",
)
FORBIDDEN = ("install architect", "install the architect", "architect is not installed")


def _flat(text: str) -> str:
    """Collapse all whitespace runs to single spaces."""
    return " ".join(text.split())


def _skill(name: str) -> str:
    """Return one skill's SKILL.md with whitespace collapsed."""
    return _flat((SKILLS / name / "SKILL.md").read_text(encoding="utf-8"))


def _paragraphs(text: str) -> list[str]:
    """Split Markdown on blank lines into whitespace-collapsed paragraphs."""
    return [_flat(p) for p in re.split(r"\n\s*\n", text) if p.strip()]


def _is_offer(paragraph: str) -> bool:
    """Return True when a paragraph names an architect skill with a roster check."""
    names = "`architect-design`" in paragraph or "`architect-assess`" in paragraph
    return names and "roster" in paragraph


def _offer_problems(name: str, text: str) -> list[str]:
    """Report offers lacking the silent clause, or a skill with no offer."""
    offers = [p for p in _paragraphs(text) if _is_offer(p)]
    problems = [f"{name}: offer lacks silent clause: {p[:60]}" for p in offers if SILENT not in p]
    if not offers:
        problems.append(f"{name}: no architect offer paragraph")
    return problems


def _eval_cases(skill: str) -> dict[str, dict]:
    """Return a skill's eval cases keyed by string id."""
    path = SKILLS / skill / "evals/evals.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(c["id"]): c for c in data["evals"]}


def test_frame_domain_reuses_then_offers_then_extracts() -> None:
    text = _skill("frame-domain")
    for phrase in (
        "current-architecture",
        "`architect-assess`",
        "available-skills roster",
        "Current-system extraction",
        "`decision-archaeology` + current-system extraction",
        "`architect-assess` is an offer, not a grounding dependency: its absence is never named in *Residual assumptions*.",
    ):
        assert phrase in text
    assert "architecture extraction" not in text.lower()
    tail = _paragraphs((SKILLS / "frame-domain/SKILL.md").read_text(encoding="utf-8"))
    degrade = next(p for p in tail if p.startswith("`architect-assess` is an offer"))
    assert "roster" not in degrade


def test_frame_intent_parks_system_shape_questions() -> None:
    text = _skill("frame-intent")
    for phrase in (
        "## System-shape questions",
        "open design question",
        "solution-independent",
        "`architect-design`",
        "`application/system`",
        "`subsystem`",
        "`architecture change`",
    ):
        assert phrase in text
    refs = _flat((SKILLS / "frame-intent/references/knowledge-surfaces.md").read_text(encoding="utf-8"))
    assert "hand it to the architect lens" not in refs
    assert "§ System-shape questions" in refs


def test_de_risk_intent_grounds_feasibility() -> None:
    text = _skill("de-risk-intent")
    for phrase in ("feasibility", "current-architecture artifact", "`architect-assess`", "cheap probe"):
        assert phrase in text


def test_option_skills_carry_feasibility_and_no_architect_skill() -> None:
    explore = _skill("explore-options")
    diverge = _skill("diverge-solutions")
    assert "feasibility: <optional" in explore
    assert "optional feasibility note citing it" in diverge
    assert "Trade-offs, Feasibility (optional)" in diverge
    for text in (explore, diverge):
        assert "architect-" not in text


def test_decompose_and_map_capabilities_offers() -> None:
    text = _skill("decompose-intent")
    for phrase in (
        "subsystem boundaries",
        "Boundaries inform dependencies; the cut stays by shippability, never by component.",
        "`architect-design`",
        "`subsystem` or `application/system` scope",
        "carry its locator in the delivery contract's design context",
        "delivery brief's design artifacts",
    ):
        assert phrase in text
    assert "5. **Rank the children" in text and "6. **Project onto a tracker" in text
    mapping = _skill("map-capabilities")
    assert "`architect-design`" in mapping and "`application/system` scope for the Build capabilities" in mapping


def test_every_offer_carries_the_silent_clause() -> None:
    for name in OFFER_SKILLS:
        text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        assert _offer_problems(name, text) == []


def test_mutation_dropping_the_clause_is_reported() -> None:
    text = (SKILLS / "decompose-intent/SKILL.md").read_text(encoding="utf-8")
    paragraphs = _paragraphs(text)
    index = next(i for i, p in enumerate(paragraphs) if _is_offer(p))
    paragraphs[index] = paragraphs[index].replace(SILENT, "")
    assert _offer_problems("decompose-intent", "\n\n".join(paragraphs))


def test_no_install_or_absence_phrases_under_apm() -> None:
    for path in (PACK_ROOT / ".apm").rglob("*"):
        if path.is_file():
            body = _flat(path.read_text(encoding="utf-8", errors="ignore")).lower()
            for phrase in FORBIDDEN:
                assert phrase not in body, f"{path}: {phrase}"


def test_manifest_declares_optional_architect_integrations() -> None:
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    pack = manifest["pack"]
    assert "architect" not in pack.get("dependencies", {})
    mine = [i for i in pack["integrations"] if i["pack"] == "architect"]
    providers = {p for i in mine for p in i["providers"]}
    assert {"skill:architect-design", "skill:architect-assess"} <= providers
    for integration in mine:
        assert "say nothing about it" in integration["fallback"]


def test_eval_ids_and_silent_assertions() -> None:
    expected = {
        "frame-domain": ("architect-installed-current-state", "architect-absent-silent"),
        "frame-intent": ("system-shape-question-architect-installed", "system-shape-question-architect-absent"),
        "de-risk-intent": ("feasibility-architect-absent-silent",),
        "decompose-intent": ("architect-absent-silent",),
    }
    for skill, ids in expected.items():
        cases = _eval_cases(skill)
        for case_id in ids:
            assert case_id in cases, f"{skill}: missing {case_id}"
            if case_id.endswith(("-absent", "-absent-silent")):
                assert any("Does not mention" in a for a in cases[case_id]["assertions"])


def test_readme_states_the_optional_behaviour() -> None:
    readme = _flat((PACK_ROOT / "README.md").read_text(encoding="utf-8"))
    assert "When the `architect` pack is installed" in readme
    assert "Without it, they say nothing about it." in readme
