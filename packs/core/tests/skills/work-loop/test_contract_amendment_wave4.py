"""The controlled amendment contract the skill states, and the eval that teaches it.

The run-level behavior (a new approval pair, completed tasks staying complete) is
the supervisor's and is covered by its own suites.
"""

from __future__ import annotations

import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "work-loop"


def test_workflow_and_eval_require_normal_reapproval_and_no_automatic_narrowing() -> None:
    lifecycle = SKILL_ROOT / "references/delivery-contract-lifecycle.md"
    skill = " ".join(
        (
            (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
            + lifecycle.read_text(encoding="utf-8")
        ).split()
    )
    for phrase in (
        "## Controlled full-mode contract amendment",
        "explicit scope-owner authority",
        "materialize the separated follow-on through `work-intake`",
        "Then amend the protected sections",
        "appends a new approval pair under the",
        "Completed tasks stay complete",
        "a new unfinished task to run",
        "session end, retry cap, stasis, or model judgment never invokes this transition",
    ):
        assert phrase in skill

    evals = json.loads(
        (SKILL_ROOT / "evals/evals.json").read_text(encoding="utf-8")
    )["evals"]
    case = {item["id"]: item for item in evals}[
        "wave4-contract-amendment-preserves-completed-work"
    ]
    assert "owner's authority and the follow-on's stable reference" in case["expected_output"]
    assert "appends a new approval pair under the same run" in case["expected_output"]
    assert "cannot invoke it automatically" in case["expected_output"]
