"""RFC-0099 R1-R12 activation coverage against the normative routing table.

This suite is repository-level: it reads the RFC's frozen answer key and the
installed skill contracts across several packs, so it cannot live under
`packs/core/tests/` without crossing that pack's test boundary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RFC = (
    REPOSITORY_ROOT
    / "docs"
    / "rfc"
    / "0099-cut-before-adding-and-artifact-shaping.md"
)


@dataclass(frozen=True)
class RoutingScenario:
    """One frozen RFC-0099 adopter-study scenario and its prose evidence."""

    fixture_id: str
    prompt: str
    installed_profile: str
    answer_key_card: str
    expected_route: str
    evidence: tuple[tuple[str, tuple[str, ...]], ...]
    required_pack: str | None = None


ROUTING_SCENARIOS = (
    RoutingScenario(
        "R1",
        "Capture this stated product outcome as a repository intent.",
        "core-only",
        "Core-only: “Capture this stated product outcome as a repository intent.”",
        "`intake-intent`",
        ((
            "packs/core/.apm/skills/intake-intent/SKILL.md",
            ("minimum repository intent", "outcome and its boundary"),
        ),),
    ),
    RoutingScenario(
        "R2",
        "Shape this raw product idea before deciding its repository artifact.",
        "core + product-engineering",
        "Core + product-engineering: “Shape this raw product idea before deciding its repository artifact.”",
        "`frame-intent`, then `intake-intent` only when repository admission is requested",
        (
            (
                "packs/product-engineering/.apm/skills/frame-intent/SKILL.md",
                ("shaping a piece of product work before it becomes a spec",),
            ),
            (
                "packs/core/.apm/skills/work-intake/SKILL.md",
                ("Delegate intent admission", "to `intake-intent`"),
            ),
        ),
        "packs/product-engineering",
    ),
    RoutingScenario(
        "R3",
        "Start this Jira Story",
        "core-only",
        "Core-only: “Start this Jira Story”; the card contains one shippable behavior but names no artifact.",
        "`work-intake`, delegating to `new-spec` after classification",
        ((
            "packs/core/.apm/skills/work-intake/SKILL.md",
            (
                "raw or ambiguous request",
                "Bounded work needing durability",
                "Delegation from this skill",
                "not a second public answer",
            ),
        ),),
    ),
    RoutingScenario(
        "R4",
        "Create a spec for this already-clear behavior.",
        "core-only",
        "Core-only: “Create a spec for this already-clear behavior.”",
        "`new-spec` directly",
        ((
            "packs/core/.apm/skills/new-spec/SKILL.md",
            ("The user explicitly requests a spec.",),
        ),),
    ),
    RoutingScenario(
        "R5",
        "Draft an RFC for this unresolved consequential direction.",
        "governance",
        "Governance installed: “Draft an RFC for this unresolved consequential direction.”",
        "`new-rfc` directly; no intent required",
        ((
            "packs/governance-extras/.apm/skills/new-rfc/SKILL.md",
            ("unresolved consequential direction",),
        ),),
        "packs/governance-extras",
    ),
    RoutingScenario(
        "R6",
        "How should we design this integration? Two viable technical shapes remain.",
        "architecture",
        "Architecture installed: “How should we design this integration? Two viable technical shapes remain.”",
        "`architect-design` directly",
        ((
            "packs/architect/.apm/skills/architect-design/SKILL.md",
            ("designing a system or integration", "There is a *real choice* to make"),
        ),),
        "packs/architect",
    ),
    RoutingScenario(
        "R7",
        "Turn this external multi-artifact brief into a repository brief.",
        "core-only",
        "Core-only: “Turn this external multi-artifact brief into a repository brief.”",
        "`author-delivery-brief create`",
        ((
            "packs/core/.apm/skills/author-delivery-brief/SKILL.md",
            (
                "`author-delivery-brief create`",
                "multi-slice or cross-repository outcome",
            ),
        ),),
    ),
    RoutingScenario(
        "R8",
        "Continue this Ready brief, but select no delivery slice yet.",
        "core-only",
        "Core-only: “Continue this Ready brief, but select no delivery slice yet.”",
        "`author-delivery-brief continue`; stop without `new-spec`",
        ((
            "packs/core/.apm/skills/author-delivery-brief/SKILL.md",
            (
                "Ready permits zero specs",
                "Only a confirmed slice invokes `new-spec`",
            ),
        ),),
    ),
    RoutingScenario(
        "R9",
        "Propose the minimum spec cut from this Ready brief.",
        "core-only",
        "Core-only: “Propose the minimum spec cut from this Ready brief.”",
        "`author-delivery-brief continue`; invoke `new-spec` only after separate confirmation",
        ((
            "packs/core/.apm/skills/author-delivery-brief/SKILL.md",
            (
                "separate delivery-slice decision",
                "wait for a second, distinct human confirmation",
            ),
        ),),
    ),
    RoutingScenario(
        "R10",
        "The established behavior regressed; diagnose and fix it.",
        "core-only",
        "Core-only: “The established behavior regressed; diagnose and fix it.”",
        "`bug-fix` directly",
        ((
            "packs/core/.apm/skills/bug-fix/SKILL.md",
            (
                "deviation between current and intended behavior",
                "investigate this regression",
            ),
        ),),
    ),
    RoutingScenario(
        "R11",
        "Refresh this accepted tracker-origin artifact.",
        "core-only",
        "Core-only: “Refresh this accepted tracker-origin artifact.”",
        "`work-intake` refresh boundary; processor remains internal",
        ((
            "packs/core/.apm/skills/work-intake/SKILL.md",
            (
                "### 7. Refresh",
                "never infer a processor",
                "Invoke the resolved registration through `invoke_refresh`",
            ),
        ),),
    ),
    RoutingScenario(
        "R12",
        "What is ready to work on?",
        "core-only",
        "Core-only: “What is ready to work on?”",
        "`workspace-status` directly",
        ((
            "packs/core/.apm/skills/workspace-status/SKILL.md",
            ("see what's ready to work on next",),
        ),),
    ),
)


def _frozen_answer_key() -> dict[str, tuple[str, str]]:
    """Read the R1-R12 card and route cells from the normative RFC table."""
    answer_key: dict[str, tuple[str, str]] = {}
    for line in RFC.read_text(encoding="utf-8").splitlines():
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        if len(cells) == 3 and re.fullmatch(r"R(?:[1-9]|1[0-2])", cells[0]):
            answer_key[cells[0]] = (cells[1], cells[2])
    return answer_key


def test_rfc0099_activation_answer_key_covers_all_entry_points() -> None:
    """The frozen R1-R12 key names every required activation entry point."""
    assert [scenario.fixture_id for scenario in ROUTING_SCENARIOS] == [
        f"R{number}" for number in range(1, 13)
    ]

    expected_routes = "\n".join(
        scenario.expected_route for scenario in ROUTING_SCENARIOS
    )
    for entry_point in (
        "work-intake",
        "intake-intent",
        "author-delivery-brief create",
        "author-delivery-brief continue",
        "new-rfc",
        "architect-design",
        "new-spec",
        "bug-fix",
    ):
        assert entry_point in expected_routes


def test_rfc0099_activation_rows_match_the_normative_answer_key_exactly() -> None:
    """Every executable case preserves its exact frozen card and route cell."""
    answer_key = _frozen_answer_key()
    assert set(answer_key) == {f"R{number}" for number in range(1, 13)}
    assert {
        scenario.fixture_id: (scenario.answer_key_card, scenario.expected_route)
        for scenario in ROUTING_SCENARIOS
    } == answer_key

    profile_prefixes = {
        "core-only": "Core-only:",
        "core + product-engineering": "Core + product-engineering:",
        "governance": "Governance installed:",
        "architecture": "Architecture installed:",
    }
    for scenario in ROUTING_SCENARIOS:
        assert scenario.answer_key_card.startswith(
            profile_prefixes[scenario.installed_profile]
        )
        assert f"“{scenario.prompt}”" in scenario.answer_key_card


def test_rfc0099_near_misses_keep_their_route_constraints() -> None:
    """Adjacent routes remain conditional, internal, or explicitly excluded."""
    routes = {
        scenario.fixture_id: scenario.expected_route
        for scenario in ROUTING_SCENARIOS
    }
    assert "only when repository admission is requested" in routes["R2"]
    assert "delegating to `new-spec` after classification" in routes["R3"]
    assert "no intent required" in routes["R5"]
    assert "stop without `new-spec`" in routes["R8"]
    assert "only after separate confirmation" in routes["R9"]
    assert "processor remains internal" in routes["R11"]


@pytest.mark.parametrize(
    "scenario",
    ROUTING_SCENARIOS,
    ids=lambda scenario: scenario.fixture_id,
)
def test_rfc0099_frozen_scenario_matches_activation_prose(
    scenario: RoutingScenario,
) -> None:
    """Each expected route is supported by the installed skill contract.

    No callable router owns all eight entry points. This construction test uses
    the repository's established prose-contract verification seam and gates
    optional profile evidence on the corresponding pack being installed.
    """
    if scenario.required_pack is not None:
        required_pack = REPOSITORY_ROOT / scenario.required_pack
        if not required_pack.is_dir():
            pytest.skip(
                f"{scenario.fixture_id} requires installed profile pack "
                f"{scenario.required_pack}"
            )

    assert scenario.prompt
    assert scenario.installed_profile
    assert scenario.expected_route
    for relative_path, required_fragments in scenario.evidence:
        evidence_path = REPOSITORY_ROOT / relative_path
        assert evidence_path.is_file(), relative_path
        body = " ".join(evidence_path.read_text(encoding="utf-8").split())
        for fragment in required_fragments:
            assert fragment in body, (scenario.fixture_id, relative_path, fragment)
