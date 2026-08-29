"""Baseline assertions for corpus admission fixtures."""

import json
from pathlib import Path

PACK = Path(__file__).resolve().parents[2]
FIXTURES = PACK / "tests" / "fixtures"


def _read_fixture(name: str) -> dict[str, object]:
    """Return one JSON fixture owned by this pack."""
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_topology_transcription_is_complete() -> None:
    """RFC-0097 D3's topology remains a complete, sourced enumeration."""
    leaves = _read_fixture("topology-leaves.json")
    names = leaves["leaves"]

    assert leaves["source_ref"] == "docs/rfc/0097-agent-skill-engineering.md:D3"
    assert leaves["expected_count"] == 36
    assert isinstance(names, list)
    assert len(names) == 36
    assert len(set(names)) == 36


def test_foundation_pins_hold_the_shipped_cases() -> None:
    """Pins reproduce every pre-change measured foundation result exactly."""
    pins = _read_fixture("foundation-retrieval-pins.json")
    results = _read_fixture("router-results.json")
    recorded = pins["pins"]
    measured = results["results"]

    assert isinstance(recorded, list)
    assert isinstance(measured, list)
    assert len(recorded) == 24
    assert all("measured_topics" in pin for pin in recorded)
    assert {pin["id"]: pin["measured_topics"] for pin in recorded} == {
        result["id"]: result["actual_topics"] for result in measured
    }
