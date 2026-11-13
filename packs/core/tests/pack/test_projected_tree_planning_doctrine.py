"""Pin compiled-corpus planning at its owner and its PLAN route."""

from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[2]
WORK_LOOP = PACK_ROOT / ".apm" / "skills" / "work-loop"
RULES = (
    "guards reading the projection",
    "guards reading authored sources",
    "paths each guard opens",
    "recompile and re-measurement",
    "the task that makes the last authored edit",
    "before its gates",
    "Every earlier task",
    "before its own gates",
    "compilation cannot always wait",
)


@pytest.mark.parametrize("phrase", RULES)
def test_compiled_corpus_rule(phrase: str) -> None:
    """Each load-bearing clause lives in the canonical planning section."""
    text = (WORK_LOOP / "references" / "delivery-contract-lifecycle.md").read_text(encoding="utf-8")
    section = text.split("## Planning a compiled corpus\n", 1)[1].split("\n## ", 1)[0]
    assert phrase in " ".join(section.split())


def test_plan_loads_the_rule_before_task_authoring() -> None:
    """The planner reaches the owner from PLAN, rather than from completion."""
    text = (WORK_LOOP / "SKILL.md").read_text(encoding="utf-8")
    plan = text.split("## Step 1. PLAN\n", 1)[1].split("## Step 2.", 1)[0]
    assert "Before writing tasks over a compiled corpus" in plan
    assert "references/delivery-contract-lifecycle.md#planning-a-compiled-corpus" in plan
