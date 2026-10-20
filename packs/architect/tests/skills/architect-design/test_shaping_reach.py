"""How architect-design's output reaches shaping, specs, and current architecture.

architect-design checks for a reference architecture and routes its creation
to Core's producers instead of drafting one; a saved design is future-state and
is reconciled into current architecture after the change ships. DESIGN.md must
describe only the routes a downstream reader actually consumes.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
DESIGN_SKILL = PACK_ROOT / ".apm/skills/architect-design"
SKILL = DESIGN_SKILL / "SKILL.md"
EVALS = DESIGN_SKILL / "evals/evals.json"
DESIGN_MD = PACK_ROOT / "DESIGN.md"
README = PACK_ROOT / "README.md"


def _flat(text: str) -> str:
    """Collapse every whitespace run to one space."""
    return " ".join(text.split())


def _procedure_step(number: int) -> str:
    """Return one numbered top-level step of the architect-design procedure."""
    text = SKILL.read_text(encoding="utf-8").split("\n## Procedure\n", 1)[1]
    match = re.search(
        rf"^{number}\. (?P<body>.*?)(?=^{number + 1}\. |^## )",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing procedure step {number}"
    return _flat(match.group("body"))


def _design_section(title: str) -> str:
    """Return one level-three section of DESIGN.md, whitespace-collapsed."""
    text = DESIGN_MD.read_text(encoding="utf-8")
    match = re.search(
        rf"^### {re.escape(title)}\n(?P<body>.*?)(?=^##+ |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"DESIGN.md: missing section {title!r}"
    return _flat(match.group("body"))


def test_step_two_checks_and_routes_the_reference_architecture() -> None:
    step = _procedure_step(2)
    for phrase in (
        "reference architecture",
        "State what you found",
        "`adapt-to-project`",
        "`init-project`",
        "available-skills roster",
        "Never draft",
        "single codebase",
        "Solution reference mode",
    ):
        assert phrase in step, phrase
    assert "state the absence in the concept and continue" in step


def test_step_eight_marks_a_saved_design_as_future_state() -> None:
    step = _procedure_step(8)
    assert "A saved design is future-state." in step
    assert "reconcile it into `current-architecture`" in step


def test_design_md_reference_architecture_routes_to_core_producers() -> None:
    section = _design_section("Reference architecture")
    assert "`adapt-to-project`" in section
    assert "`init-project`" in section
    assert "offers to establish one at the adopter-selected" not in section
    assert "solution reference mode" in section.lower()


def test_design_md_downstream_names_only_consumed_routes() -> None:
    section = _design_section("Downstream: core")
    assert "reads it to orient" not in section
    for phrase in (
        "`intent decompose`",
        "design context",
        "`current-architecture`",
        "`AGENTS.md` maps",
        "only orders work",
        "second architecture authority",
    ):
        assert phrase in section, phrase


def test_manifest_declares_the_core_reference_architecture_handoff() -> None:
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    [entry] = [
        item
        for item in manifest["pack"]["integrations"]
        if item["id"] == "core-reference-architecture-handoff"
    ]
    assert entry["pack"] == "core"
    assert entry["kind"] == "handoff"
    assert entry["consumers"] == ["skill:architect-design"]
    assert entry["providers"] == ["skill:adapt-to-project", "skill:init-project"]
    assert "states the absence" in entry["fallback"]
    assert "single codebase" in entry["purpose"]


def test_readme_states_the_reference_architecture_offer() -> None:
    readme = _flat(README.read_text(encoding="utf-8"))
    assert "offers Core's `adapt-to-project` or `init-project`" in readme


def test_no_reference_architecture_eval_exists() -> None:
    cases = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    assert any(case["id"] == "no-reference-architecture" for case in cases)


TEMPLATE = DESIGN_SKILL / "assets/solution-reference.md"
TEMPLATE_HEADINGS = [
    "Scope",
    "System context",
    "Component landscape",
    "Domain boundaries",
    "Shared contracts",
    "Cross-cutting standards",
    "Conformance",
    "Coordination constraints",
    "Open questions",
]


def _solution_reference_section() -> str:
    """Return the body of SKILL.md's Solution reference mode section."""
    text = SKILL.read_text(encoding="utf-8")
    match = re.search(
        r"^## Solution reference mode\n(?P<body>.*?)(?=^## )",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match, "SKILL.md: missing '## Solution reference mode'"
    return _flat(match.group("body"))


def _template_sections(text: str) -> dict[str, str]:
    """Map each level-two heading of the template to its body, in order."""
    parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
    return dict(zip(parts[1::2], parts[2::2], strict=True))


def test_solution_reference_mode_section_states_its_contract() -> None:
    section = _solution_reference_section()
    for phrase in (
        "coordinating repo",
        "no app code",
        "`adapt-to-project`",
        "`init-project`",
        "`assets/solution-reference.md`",
        "`current-architecture`",
        "not `architecture-design`",
        "real-choice check and Stage 0 do not apply",
        "per-section confirmation",
        "per-file acceptance",
        "as data",
        "rather than inventing one",
        "backward-compatible contracts and expand-then-contract changes",
    ):
        assert phrase in section, phrase
    skill = _flat(SKILL.read_text(encoding="utf-8"))
    assert skill.index("## Solution reference mode") < skill.index(
        "## Anti-patterns to refuse"
    )
    assert skill.index("## Procedure") < skill.index("## Solution reference mode")


def test_solution_reference_template_headings_and_diagrams() -> None:
    sections = _template_sections(TEMPLATE.read_text(encoding="utf-8"))
    assert list(sections) == TEMPLATE_HEADINGS
    for title in ("System context", "Component landscape"):
        assert re.search(r"^```mermaid\n", sections[title], re.MULTILINE), title
    # The pack draws C4 views as plain flowcharts, never C4Context or C4Container.
    for title in ("System context", "Component landscape"):
        assert "flowchart" in sections[title]
        assert "C4Context" not in sections[title]


def test_solution_reference_template_check_fails_on_mutation() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    swapped = text.replace("## Scope", "## Temp").replace(
        "## System context", "## Scope"
    ).replace("## Temp", "## System context")
    assert list(_template_sections(swapped)) != TEMPLATE_HEADINGS
    stripped = text.replace("```mermaid", "```text")
    assert "```mermaid" not in _template_sections(stripped)["System context"]
