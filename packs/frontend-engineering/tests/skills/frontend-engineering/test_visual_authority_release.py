"""Slice 1 ships as a coherent, independently installable release.

The pack stays independently installable: these are the checks that would red
if a later change made another pack required, or if the installed first-run
prompt kept describing a pre-flight that no longer exists.
"""

from __future__ import annotations

import json
import tomllib

import pytest
from frontend_engineering_visual_authority_rules import PACK_ROOT, SKILL_DIR

PACK_TOML = PACK_ROOT / "pack.toml"
PLUGIN_JSON = PACK_ROOT / ".claude-plugin" / "plugin.json"
JOURNEY = PACK_ROOT / "JOURNEY.md"
EVALS = SKILL_DIR / "evals" / "evals.json"

SLICE_ONE_CASES = (
    "visual-authority-approved-target",
    "visual-authority-direction-only",
    "visual-authority-incumbent",
    "visual-authority-standalone",
    "visual-authority-non-visual",
    "visual-authority-no-browser",
)
REMOVED_STEP_WORDING = ("aesthetic reference", "seed token block", "token seed block")


def _pack() -> dict:
    return tomllib.loads(PACK_TOML.read_text(encoding="utf-8"))


def test_the_pack_declares_no_required_dependency_on_another_pack() -> None:
    """A regression guard, not a new property: this already held. It exists
    because the coupling this slice risks is semantic, and a later edit that
    promoted the recommendation to a requirement would otherwise be silent."""
    deps = _pack().get("pack", {}).get("dependencies", {})
    assert not deps.get("required"), (
        f"frontend-engineering now requires another pack: {deps.get('required')}"
    )


def test_the_journey_declares_no_prerequisite_pack() -> None:
    assert "prerequisitePacks: []" in JOURNEY.read_text(encoding="utf-8")


@pytest.mark.parametrize("field", ["starter-prompt", "expected-result"])
def test_the_first_value_strings_describe_the_shipped_preflight(field: str) -> None:
    """These are the installed first-run strings. Left stale they walk a new
    adopter through two steps the pack no longer has."""
    value = _pack()["pack"]["first-value"][field].lower()
    stale = [w for w in REMOVED_STEP_WORDING if w in value]
    assert not stale, f"{field} still names removed pre-flight steps: {stale}"
    assert "visual authority" in value or "visual-authority" in value


@pytest.mark.parametrize("case_id", SLICE_ONE_CASES)
def test_the_control_flow_case_ships(case_id: str) -> None:
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    case = next((e for e in data["evals"] if e["id"] == case_id), None)
    assert case is not None, f"{case_id} is not in the eval harness"
    assert case["prompt"].strip() and case["expected_output"].strip()
    assert case["assertions"], f"{case_id} asserts nothing"


def test_eval_ids_stay_unique() -> None:
    ids = [e["id"] for e in json.loads(EVALS.read_text(encoding="utf-8"))["evals"]]
    assert len(ids) == len(set(ids)), "duplicate eval id"


def test_the_pack_and_plugin_versions_match_and_moved() -> None:
    version = _pack()["pack"]["version"]
    assert version == json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]
    assert version == "0.3.4", (
        f"slice 1 ships at 0.3.4 per the spec; pack.toml carries {version!r}"
    )
