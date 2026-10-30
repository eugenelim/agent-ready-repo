"""The work-loop skill text asks for one capture at each retained gate, in order.

A synthetic run follows the skill's G-plan step as written: it reads the ordered
actions out of `SKILL.md`, performs each capture through the producer profile
against real gate artifacts, and checks that project-knowledge accepts each one
exactly as the profile's own fixtures require. The capture gates are the only ones
the skill names, and each is requested once: `spec-approved` before `start`, and
`plan-locked` at `start`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from knowledge_test_support import (
    PACK_ROOT,
    initialize_empty_v1_repo,
    load_knowledge_store_module,
    load_project_knowledge_module,
)
from test_work_loop_producer_profile import (
    _capture_args,
    _events,
    _run_main,
    _semantic_input,
    _write_gate_artifacts,
)

SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
GATE_ARTIFACT = {
    "spec-approved": "docs/specs/example/spec.md",
    "plan-locked": "docs/specs/example/plan.md",
}


def _step_12() -> str:
    """The G-plan step, up to its project-knowledge subsection."""
    text = SKILL.read_text(encoding="utf-8")
    start = text.index("12. **Full mode:** the **G-plan sequence**")
    return text[start : text.index("### Project-knowledge integration", start)]


def _ordered_actions(step: str) -> list[str]:
    """The step's numbered sub-actions: a capture gate by name, or `start`."""
    actions: list[str] = []
    for item in re.split(r"\n    \d\. ", step)[1:]:
        capture = re.match(r"Request the `([a-z-]+)` capture", item)
        if capture:
            actions.append(f"capture:{capture.group(1)}")
        elif "work-supervisor.py' start" in item:
            actions.append("start")
    return actions


def test_the_skill_asks_for_each_retained_capture_once_around_start() -> None:
    assert _ordered_actions(_step_12()) == [
        "capture:spec-approved",
        "start",
        "capture:plan-locked",
    ]


def test_the_skill_names_no_other_capture_gate() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert set(re.findall(r"--semantic-gate[ =]([\w-]+)", text)) <= set(GATE_ARTIFACT)
    section = text.split("### Project-knowledge integration", 1)[1].split("For durable work", 1)[0]
    assert section.count("`spec-approved`") == 1 and section.count("`plan-locked`") == 1


def test_a_synthetic_run_requests_one_capture_per_gate_and_each_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = initialize_empty_v1_repo(tmp_path, load_knowledge_store_module())
    _write_gate_artifacts(repo)
    module = load_project_knowledge_module()
    performed: list[str] = []
    for action in _ordered_actions(_step_12()):
        if not action.startswith("capture:"):
            performed.append(action)  # `start` is the supervisor's, not a capture
            continue
        gate = action.removeprefix("capture:")
        assert _run_main(
            module, monkeypatch, _capture_args(repo, gate, GATE_ARTIFACT[gate]), _semantic_input()
        ) == 0, gate
        performed.append(gate)

    assert performed == ["spec-approved", "start", "plan-locked"]
    assert len(_events(repo)) == 2
