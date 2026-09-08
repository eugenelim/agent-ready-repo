"""Construction checks for the sequential implementer dispatch contract."""

from __future__ import annotations

from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
IMPLEMENTER = PACK_ROOT / ".apm" / "agents" / "implementer.md"


def _execute_section() -> str:
    """Return the EXECUTE section without adjacent phase rules."""
    text = SKILL.read_text(encoding="utf-8")
    return text.split("## Step 2. EXECUTE", 1)[1].split("## Step 3. GATES", 1)[0]


def test_execute_declares_complete_sequential_dispatch() -> None:
    """A schedule task gets one bounded implementer dispatch, never fan-out."""
    execute = _execute_section()
    for literal in (
        "implementer",
        "loop-cohort schedule",
        "once per plan task",
        "one implementer at a time",
    ):
        assert literal in execute, literal


def test_conditional_routing_inlines_the_only_external_executor_craft() -> None:
    """The dispatch brief carries external frontend craft or its named fallback."""
    routing = SKILL.read_text(encoding="utf-8").split(
        "## Conditional-reference routing", 1
    )[1]
    expected_row = (
        "| HTML/CSS/JS primary output | "
        "Inline `frontend-engineering` craft into the implementer dispatch brief "
        "when that pack is installed; when it is absent, record the named skip and "
        "continue without that craft. |"
    )
    assert expected_row in routing
    assert routing.count("implementer dispatch brief") >= 1


def test_implementer_contract_admits_both_roots_and_one_owner_each() -> None:
    """Controller and implementer commit in exactly their assigned root."""
    text = IMPLEMENTER.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    assert "supervisor mode" not in frontmatter
    assert "multiple tasks declaring" not in frontmatter
    # Couple owner to root. Four independent whole-file substring checks would
    # pass with the two owners swapped, or with a third root added.
    envelope = text.split("## Operating envelope", 1)[1].split("<!--", 1)[0]
    bullets = [b for b in envelope.split("\n- **") if "execution root" in b]
    assert len(bullets) == 2, f"expected exactly two execution roots, got {len(bullets)}"
    primary = next(b for b in bullets if b.startswith("Primary working tree:"))
    worktree = next(b for b in bullets if b.startswith("Already-created worktree:"))
    assert "the controller is the commit owner" in primary
    assert "you are its commit owner" not in primary
    assert "you are its commit owner" in worktree
    assert "the controller is the commit owner" not in worktree
    assert ".worktrees/<task-id>/" not in text
    assert "inside the worktree" not in text


def test_implementer_requires_inlined_craft_and_a_complete_brief() -> None:
    """The agent never self-discovers craft or starts from an incomplete brief."""
    # Flatten whitespace: the source wraps these phrases across lines, and a
    # raw substring match would pin the line-break position rather than the rule.
    text = " ".join(IMPLEMENTER.read_text(encoding="utf-8").split())
    assert "Every predicate-fired craft source the orchestrator inlined" in text
    assert "do **not** load the source skill yourself" in text
    refusal = (
        "Refuse the brief before the first implementation write if it omits "
        "the task body, execution root, spec path, plan path, or verification mode."
    )
    assert refusal in text


def test_existing_lifecycle_pointer_count_is_preserved() -> None:
    """The dispatch addition cannot displace the linked amendment contract."""
    assert SKILL.read_text(encoding="utf-8").count(
        "references/delivery-contract-lifecycle.md"
    ) >= 3
