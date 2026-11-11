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
INTENT = SKILLS / "intent"
FRAME_MODE = INTENT / "references" / "frame.md"
DE_RISK_MODE = INTENT / "references" / "de-risk.md"
DECOMPOSE_MODE = INTENT / "references" / "decompose.md"
SILENT = (
    "If it is not in the roster, continue with this skill's own behaviour and "
    "say nothing about it: no mention, no note, and no error."
)
# The files that carry an architect offer: two skills, and three `intent` modes.
OFFER_FILES = {
    "intent": INTENT / "SKILL.md",
    "frame-domain": SKILLS / "frame-domain" / "SKILL.md",
    "intent frame": FRAME_MODE,
    "intent de-risk": DE_RISK_MODE,
    "intent decompose": DECOMPOSE_MODE,
    "map-capabilities": SKILLS / "map-capabilities" / "SKILL.md",
    "align-value-stream": SKILLS / "align-value-stream" / "SKILL.md",
}
FORBIDDEN = ("install architect", "install the architect", "architect is not installed")


def _forbidden_hits(body: str) -> list[str]:
    """Return the forbidden phrases in a body, ignoring case and code marks."""
    plain = _flat(body.replace("`", "")).lower()
    return [phrase for phrase in FORBIDDEN if phrase in plain]


def _flat(text: str) -> str:
    """Collapse all whitespace runs to single spaces."""
    return " ".join(text.split())


def _skill(skill_dir: Path) -> str:
    """Return one skill's SKILL.md with whitespace collapsed."""
    return _flat((skill_dir / "SKILL.md").read_text(encoding="utf-8"))


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


def _eval_cases(skill_dir: Path) -> dict[str, dict]:
    """Return a skill's eval cases keyed by string id."""
    path = skill_dir / "evals/evals.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(c["id"]): c for c in data["evals"]}


def test_frame_domain_reuses_then_offers_then_extracts() -> None:
    paragraphs = _paragraphs((SKILLS / "frame-domain/SKILL.md").read_text(encoding="utf-8"))
    [bullet] = [p for p in paragraphs if "**Current-system extraction.**" in p]
    order = [
        bullet.index("First reuse a reachable current-architecture artifact"),
        bullet.index("check your available-skills roster for `architect-assess`"),
        bullet.index("extract the domain model, events, and binding seams"),
    ]
    assert order == sorted(order)
    degrade = next(p for p in paragraphs if p.startswith("`architect-assess` is an offer"))
    assert "roster" not in degrade


def test_frame_domain_names_current_system_extraction() -> None:
    text = _skill(SKILLS / "frame-domain")
    for phrase in (
        "current-architecture",
        "`architect-assess`",
        "available-skills roster",
        "Current-system extraction",
        "`decision-archaeology` + current-system extraction",
        "`architect-assess` is an offer, not a grounding dependency: its absence is never named in the artifact, including *Residual assumptions*.",
    ):
        assert phrase in text
    assert "architecture extraction" not in text.lower()


def test_frame_mode_parks_system_shape_questions() -> None:
    text = _flat(FRAME_MODE.read_text(encoding="utf-8"))
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
    refs = _flat((INTENT / "references" / "knowledge-surfaces.md").read_text(encoding="utf-8"))
    assert "hand it to the architect lens" not in refs
    assert "§ System-shape questions" in refs


def test_de_risk_mode_grounds_feasibility() -> None:
    text = _flat(DE_RISK_MODE.read_text(encoding="utf-8"))
    for phrase in ("feasibility", "current-architecture artifact", "`architect-assess`", "cheap probe"):
        assert phrase in text


def test_option_skills_carry_feasibility_and_no_architect_skill() -> None:
    explore = _skill(SKILLS / "explore-options")
    diverge = _skill(SKILLS / "diverge-solutions")
    assert "feasibility: <optional" in explore
    assert "optional feasibility note citing it" in diverge
    assert "Trade-offs, Feasibility (optional)" in diverge
    for text in (explore, diverge):
        assert "architect-" not in text


def test_decompose_and_map_capabilities_offers() -> None:
    text = _flat(DECOMPOSE_MODE.read_text(encoding="utf-8"))
    for phrase in (
        "subsystem boundaries",
        "Boundaries inform dependencies; the cut stays by shippability, never by component.",
        "`architect-design`",
        "## Design before you cut",
        "carry its locator in the delivery contract's design context",
        "delivery brief's design artifacts",
    ):
        assert phrase in text
    assert "`subsystem` or `application/system` scope" not in text
    assert "5. **Rank the children" in text and "6. **Project onto a tracker" in text
    mapping = _skill(SKILLS / "map-capabilities")
    assert "`architect-design`" in mapping and "`application/system` scope for the Build capabilities" in mapping


def _section_of(text: str, heading: str, level: str = "##") -> str:
    """Return a Markdown section's raw body, bounded by the next heading of its level."""
    match = re.search(
        rf"^{re.escape(level)} {re.escape(heading)}\n(?P<body>.*?)(?=^{re.escape(level)} |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing section {heading!r}"
    return match.group("body")


def _intent_skill() -> str:
    """Return the intent SKILL.md source, unflattened."""
    return (INTENT / "SKILL.md").read_text(encoding="utf-8")


def test_skill_architecture_subsection_states_the_rules() -> None:
    life = _section_of(_intent_skill(), "The intent lifecycle")
    sub = _flat(_section_of(life, "Architecture before the cut", "###"))
    assert life.index("### Supervised route") < life.index("### Architecture before the cut")
    for phrase in (
        "Check your available-skills roster for `architect-design`",
        "offer it before the cut",
        "never start it yourself",
        SILENT,
        "`product-vision` or `product-strategy` | `application/system`",
        "`capability` | `subsystem` when the system it belongs to already runs; otherwise `application/system`",
        "`feature` | `architecture change`",
        "A design covers an intent when it is a resolved `architecture-design` artifact made for that intent or for one of its ancestors, and it names the system or subsystem the intent changes.",
        "When the user declines `architect-design` for an intent, do not offer it again for that intent in this conversation. Choosing another offered option counts as declining it; declining the frame mode's system-shape offer does not.",
    ):
        assert phrase in sub, phrase


def test_short_route_names_the_architecture_stage_between_de_risk_and_decompose() -> None:
    short = _section_of(_intent_skill(), "Short route", "###")
    flat = _flat(short)
    order = [
        flat.index("2. `de-risk`"),
        flat.index("Then, before `decompose`: `architect-design` (separate skill) is offered"),
        flat.index("3. `decompose`"),
    ]
    assert order == sorted(order)
    [para] = [p for p in _paragraphs(short) if "Then, before `decompose`" in p]
    assert "available-skills roster" in para and SILENT in para


def test_de_risk_survive_bullet_offers_architect_design_on_the_short_route() -> None:
    nxt = _section_of(DE_RISK_MODE.read_text(encoding="utf-8"), "Next")
    [bullet] = [b for b in re.split(r"^- ", nxt, flags=re.MULTILINE) if b.startswith("**Survive.**")]
    flat = _flat(bullet)
    for phrase in (
        "Offer the next stage for each route, each labelled with its route:",
        "`intent decompose` (short route)",
        "`place-bet` (longer route)",
        "Recommend the one for the route the conversation shows, unless the next paragraph applies.",
        "When the conversation shows no route, recommend neither and ask which route applies.",
        "On the short route, check your available-skills roster for `architect-design`",
        "When you offer it, recommend `architect-design` instead of `intent decompose`.",
        "§ Architecture before the cut",
        SILENT,
    ):
        assert phrase in flat, phrase
    [para] = [p for p in _paragraphs(bullet) if "On the short route, check" in p]
    assert SILENT in para
    assert flat.index("ask which route applies") < flat.index("On the short route, check")


def test_decompose_design_before_you_cut_section() -> None:
    text = DECOMPOSE_MODE.read_text(encoding="utf-8")
    assert text.index("## When to invoke") < text.index("## Design before you cut") < text.index("## Procedure")
    sec = _flat(_section_of(text, "Design before you cut"))
    for phrase in (
        "When `discovery-loop` or its `discovery-lead` agent called this mode, skip this section",
        "check your available-skills roster for `architect-design`",
        "pause before cutting",
        "§ Architecture before the cut",
        SILENT,
        "When the user declines, cut as usual.",
        "When the design changes the intent's capabilities, do not cut yet: for a `capability` or higher intent, recommend the longer route at `map-capabilities`; for a `feature`, recommend `intent frame` for its parent capability. Also offer to cut.",
    ):
        assert phrase in sec, phrase


def test_decompose_step_one_has_no_architect_offer() -> None:
    text = _flat(DECOMPOSE_MODE.read_text(encoding="utf-8"))
    step = text.split("1. **Decompose one level.**", 1)[1].split("2. **Record", 1)[0]
    assert "subsystem boundaries" in step
    assert "Boundaries inform dependencies; the cut stays by shippability, never by component." in step
    assert "architect-design" not in step and "architect-assess" not in step


def test_mutation_dropping_the_clause_from_skill_is_reported() -> None:
    text = _intent_skill()
    paragraphs = _paragraphs(text)
    index = next(i for i, p in enumerate(paragraphs) if _is_offer(p) and "Then, before `decompose`" in p)
    paragraphs[index] = paragraphs[index].replace(SILENT, "")
    assert _offer_problems("intent", "\n\n".join(paragraphs))


def test_every_offer_carries_the_silent_clause() -> None:
    for name, path in OFFER_FILES.items():
        text = path.read_text(encoding="utf-8")
        assert _offer_problems(name, text) == []


def test_mutation_dropping_the_clause_is_reported() -> None:
    text = DECOMPOSE_MODE.read_text(encoding="utf-8")
    paragraphs = _paragraphs(text)
    index = next(i for i, p in enumerate(paragraphs) if _is_offer(p))
    paragraphs[index] = paragraphs[index].replace(SILENT, "")
    assert _offer_problems("intent decompose", "\n\n".join(paragraphs))


def test_no_install_or_absence_phrases_under_apm() -> None:
    for path in (PACK_ROOT / ".apm").rglob("*"):
        if path.is_file():
            hits = _forbidden_hits(path.read_text(encoding="utf-8", errors="ignore"))
            assert not hits, f"{path}: {hits}"


def test_mutation_adding_a_forbidden_phrase_is_reported() -> None:
    text = FRAME_MODE.read_text(encoding="utf-8")
    assert not _forbidden_hits(text)
    assert _forbidden_hits(text + "\nTo get this offer, install the `architect` pack.\n")


def test_manifest_declares_optional_architect_integrations() -> None:
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    pack = manifest["pack"]
    tiers = pack.get("dependencies", {})
    assert all(
        entry["pack"] != "architect" for tier in tiers.values() for entry in tier
    )
    mine = [i for i in pack["integrations"] if i["pack"] == "architect"]
    providers = {p for i in mine for p in i["providers"]}
    assert {"skill:architect-design", "skill:architect-assess"} <= providers
    for integration in mine:
        assert "say nothing about it" in integration["fallback"]
    solution = [i for i in mine if "skill:align-value-stream" in i["consumers"]]
    assert solution and all("skill:architect-design" in i["providers"] for i in solution)


def test_eval_ids_and_silent_assertions() -> None:
    expected = {
        "frame-domain": ("architect-installed-current-state", "architect-absent-silent"),
        "intent": (
            "system-shape-question-architect-installed",
            "system-shape-question-architect-absent",
            "feasibility-architect-absent-silent",
            "architect-absent-silent",
        ),
    }
    for skill in ("frame-domain", "intent"):
        cases = _eval_cases(SKILLS / skill)
        for case_id in expected[skill]:
            assert case_id in cases, f"{skill}: missing {case_id}"
            if case_id.endswith(("-absent", "-absent-silent")):
                assert any("Does not mention" in a for a in cases[case_id]["assertions"])


NEW_EVAL_ASSERTIONS = {
    "de-risk-survive-architect-first": ("de-risk", "Recommends architect-design instead of intent decompose"),
    "decompose-architect-first": ("decompose", "Pauses before cutting and offers architect-design"),
    "decompose-declined-at-de-risk": ("decompose", "Cuts without offering architect-design again"),
    "decompose-design-already-covers": ("decompose", "Cuts without offering architect-design"),
    "decompose-design-changes-capabilities": ("decompose", "Recommends the longer route at map-capabilities"),
    "decompose-feature-design-changes-capabilities": ("decompose", "Recommends intent frame for the parent capability"),
    "de-risk-survive-no-route-architect-installed": ("de-risk", "Recommends neither route and asks which route applies"),
    "de-risk-chose-decompose-then-decompose": ("decompose", "Cuts without offering architect-design again"),
    "de-risk-survive-architect-absent": ("de-risk", "Does not mention architect, its skills, or their absence"),
}


def test_architecture_first_eval_cases() -> None:
    cases = _eval_cases(INTENT)
    for case_id, (mode, assertion) in NEW_EVAL_ASSERTIONS.items():
        assert case_id in cases, case_id
        case = cases[case_id]
        assert case["mode"] == mode
        assert assertion in case["assertions"], case_id
        assert case["prompt"] and case["expected_output"]
        assert "roster" in case["prompt"], case_id
    for case_id in ("decompose-1", "capability-negotiated-handoff"):
        assert "The architect skills are not in the available-skills roster." in cases[case_id]["prompt"]


def test_readme_states_the_optional_behaviour() -> None:
    readme = _flat((PACK_ROOT / "README.md").read_text(encoding="utf-8"))
    assert "When the `architect` pack is installed" in readme
    assert "Without it, they say nothing about it." in readme
    assert (
        "`intent de-risk` and `intent decompose` offer `architect-design` before the work is cut"
        in readme
    )
