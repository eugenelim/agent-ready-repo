"""Corpus admission and recorded retrieval assertions."""

import json
from pathlib import Path
import re

PACK = Path(__file__).resolve().parents[2]
FIXTURES = PACK / "tests" / "fixtures"
ADMISSION = FIXTURES / "topic-admission.json"
CONCEPTS = PACK / "okf" / "agent-skill-engineering-foundation" / "concepts"
COMPILED_CONCEPTS = (
    PACK / ".apm" / "skills" / "ase-okf-reference" / "references" / "okf" / "concepts"
)
ROLE_OR_PLACEHOLDER = re.compile(
    r"^(?:[a-z][a-z0-9]*(?:-[a-z0-9]+)*-(?:reviewer|maintainer)|<[^<>]+>)$"
)
SCOPE_BOUND_STATEMENT = "It is not established beyond that population."


def test_topology_transcription_is_complete() -> None:
    """RFC-0097 D3's topology remains a complete, sourced enumeration."""
    leaves = json.loads(
        (FIXTURES / "topology-leaves.json").read_text(encoding="utf-8")
    )
    names = leaves["leaves"]

    assert leaves["source_ref"] == "docs/rfc/0097-agent-skill-engineering.md:D3"
    assert leaves["expected_count"] == 36
    assert isinstance(names, list)
    assert len(names) == 36
    assert len(set(names)) == 36


def test_foundation_pins_hold_the_shipped_cases() -> None:
    """Pins reproduce every pre-change measured foundation result exactly."""
    pins = json.loads(
        (FIXTURES / "foundation-retrieval-pins.json").read_text(encoding="utf-8")
    )
    results = json.loads(
        (FIXTURES / "router-results.json").read_text(encoding="utf-8")
    )
    recorded = pins["pins"]
    measured = results["results"]

    assert isinstance(recorded, list)
    assert isinstance(measured, list)
    assert len(recorded) == 24
    assert all("measured_topics" in pin for pin in recorded)
    assert {pin["id"]: pin["measured_topics"] for pin in recorded} == {
        result["id"]: result["actual_topics"] for result in measured
    }


def test_every_claim_group_declares_a_basis_and_its_fields() -> None:
    """Each admitted group has the evidence shape its declared basis requires."""

    record = json.loads(ADMISSION.read_text(encoding="utf-8"))
    for topic in record["topics"]:
        assert ROLE_OR_PLACEHOLDER.fullmatch(topic["reviewer"])
        assert topic["last_verified"]
        for group in topic["claim_groups"]:
            assert group["basis"] in {"doctrine", "observed-practice"}
            assert group["revalidation_trigger"]
            if group["basis"] == "observed-practice":
                observations = group["observations"]
                assert len(observations) >= 2
                assert len({Path(path).parts[1] for path in observations}) >= 2
                assert SCOPE_BOUND_STATEMENT in group["applicability_limit"]


def _collapse(text: str) -> str:
    """Return *text* with every whitespace run reduced to one space."""
    return " ".join(text.split())

def test_shipped_body_matches_the_admission_record() -> None:
    """Observed-practice limits remain portable and equal in both projections."""

    record = json.loads(ADMISSION.read_text(encoding="utf-8"))
    for topic in record["topics"]:
        authored = (CONCEPTS / f"{topic['topic']}.md").read_text(encoding="utf-8")
        compiled = (COMPILED_CONCEPTS / f"{topic['topic']}.md").read_text(
            encoding="utf-8"
        )
        assert not ROLE_OR_PLACEHOLDER.search(authored)
        assert not ROLE_OR_PLACEHOLDER.search(compiled)
        for group in topic["claim_groups"]:
            if group["basis"] != "observed-practice":
                continue
            limit = group["applicability_limit"]
            assert SCOPE_BOUND_STATEMENT in limit
            # Both projections wrap prose; the claim is about the text, not its
            # line breaks, so compare with whitespace collapsed on both sides.
            assert _collapse(limit) in _collapse(authored)
            assert _collapse(limit) in _collapse(compiled)
            for repository_marker in ("packs/", ".apm/skills/", "agent-skill-engineering"):
                assert repository_marker not in limit
