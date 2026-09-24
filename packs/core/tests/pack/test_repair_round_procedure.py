"""Content pin for the repair-round documented procedure.

Each fenced block that fires one of the three guarded edges — gates-failed
from CODE-VERIFICATION, findings-remain from CODE-REVIEW, and blocker-applied
from CODE-HUMAN-GATE — must run wave reopen before the transition. The two
firing sites in session-resumption.md are table cells, not fenced blocks; the
invocation count below cannot see them, and they are pinned by named string
assertions instead.

Stated blind spot: a firing site added later as a table cell is caught by
neither the invocation count nor the per-site named assertions unless a new
named assertion is added here. This gap is the accepted cost of the demotion
that moved the procedure to working material; no acceptance criterion reads it,
but this suite fails when existing prose is removed.
"""

from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = PACK_ROOT / ".apm/skills/work-loop"
FULL_MODE_ENGINE = SKILL_ROOT / "references/full-mode-engine.md"
FINDING_ADJUDICATION = SKILL_ROOT / "references/finding-adjudication.md"
PRE_EXECUTE_REVIEW = SKILL_ROOT / "references/pre-execute-review.md"
SESSION_RESUMPTION = SKILL_ROOT / "references/session-resumption.md"
SKILL_MD = SKILL_ROOT / "SKILL.md"
STATE_SCHEMA = SKILL_ROOT / "references/state-schema.md"

# The three guarded edges, matched as bare event names in transition commands.
GUARDED_EDGES = ("gates-failed", "findings-remain", "blocker-applied")

REOPEN_CMD = "wave reopen"
ENGINE_TRANSITION = "loop-engine.py' transition"


def fenced_blocks(text: str) -> list[str]:
    """Return the content of every fenced code block in text."""
    return re.findall(r"```[^\n]*\n(.*?)```", text, re.DOTALL)


def block_fires_edge(block: str, edge: str) -> bool:
    """Return True when block has a non-comment line invoking loop-engine transition edge."""
    for line in block.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if ENGINE_TRANSITION in line and edge in line:
            return True
    return False


def reopen_precedes_edge(block: str, edge: str) -> bool:
    """Return True when a non-comment wave reopen appears before the edge invocation.

    Both halves apply the non-comment rule: a commented-out ``# wave reopen``
    above a transition does not satisfy the pin. The test
    ``test_commented_reopen_does_not_satisfy_the_pin`` verifies this.
    """
    # Find the edge in a non-comment transition invocation.
    edge_pos = -1
    for line in block.splitlines():
        if line.lstrip().startswith("#"):
            continue
        if ENGINE_TRANSITION in line and edge in line:
            edge_pos = block.index(line)
            break
    # Find wave reopen in a non-comment line, before the edge.
    reopen_pos = -1
    for line in block.splitlines():
        if line.lstrip().startswith("#"):
            continue
        pos = block.index(line)
        if REOPEN_CMD in line and (edge_pos == -1 or pos < edge_pos):
            reopen_pos = pos
            break
    if reopen_pos == -1 or edge_pos == -1:
        return False
    return reopen_pos < edge_pos


def test_commented_reopen_does_not_satisfy_the_pin() -> None:
    """A commented-out ``# wave reopen`` must not satisfy the reopen check.

    The content pin walks non-comment lines for the edge invocation; both halves
    apply the same rule. If the reopen half accepted comment lines, a block could
    carry ``# wave reopen`` above the transition and pass while the actual reopen
    command is absent.
    """
    block = (
        "```\n"
        "# wave reopen docs/specs/<feature> --expect-run-id $run_id\n"
        f"python '<skill-dir>/scripts/{ENGINE_TRANSITION} docs/specs/<f> gates-failed\n"
        "```\n"
    ).strip("` \n")
    assert not reopen_precedes_edge(block, "gates-failed"), (
        "a commented-out wave reopen must not satisfy the reopen-precedes-edge check"
    )


def count_invocations(files: list[Path]) -> int:
    """Count loop-engine.py transition invocations naming a guarded edge.

    Two blocks in the procedure already name a second edge in comment lines,
    so a block count stays constant when a new firing line is added inside an
    existing block. Counting invocation lines (non-comment lines where
    loop-engine.py transition <edge> appears) catches that addition; a block
    count does not.
    """
    total = 0
    pattern = re.compile(
        r"loop-engine\.py.*transition\s+\S+\s+(" + "|".join(GUARDED_EDGES) + r")"
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.lstrip().startswith("#"):
                continue
            if pattern.search(line):
                total += 1
    return total


# ---------------------------------------------------------------------------
# full-mode-engine.md per-site assertions
# ---------------------------------------------------------------------------


def test_gates_failed_block_has_reopen_first() -> None:
    """Pin wave reopen before gates-failed in the GATES wave-routing block."""
    text = FULL_MODE_ENGINE.read_text(encoding="utf-8")
    blocks = fenced_blocks(text)
    # Only blocks where gates-failed appears as an actual transition invocation.
    found = [b for b in blocks if block_fires_edge(b, "gates-failed")]
    assert found, "No fenced block with an actual gates-failed transition found"
    for block in found:
        assert reopen_precedes_edge(block, "gates-failed"), (
            "wave reopen must appear before gates-failed in the block"
        )


def test_blocker_applied_block_has_reopen_first() -> None:
    """Pin wave reopen before blocker-applied in the REVIEW changes-requested block."""
    text = FULL_MODE_ENGINE.read_text(encoding="utf-8")
    blocks = fenced_blocks(text)
    found = [b for b in blocks if block_fires_edge(b, "blocker-applied")]
    assert found, "No fenced block with an actual blocker-applied transition found"
    for block in found:
        assert reopen_precedes_edge(block, "blocker-applied"), (
            "wave reopen must appear before blocker-applied in the block"
        )


def test_specialist_findings_remain_block_has_reopen_first() -> None:
    """Pin wave reopen before findings-remain in the CODE-REVIEW specialist block."""
    text = FULL_MODE_ENGINE.read_text(encoding="utf-8")
    # Only look in the REVIEW section (after ## REVIEW).
    review_section = text[text.index("## REVIEW and the human gate"):]
    blocks = fenced_blocks(review_section)
    found = [b for b in blocks if block_fires_edge(b, "findings-remain")]
    assert found, (
        "No fenced block with an actual findings-remain transition in "
        "full-mode-engine.md REVIEW section"
    )
    for block in found:
        assert reopen_precedes_edge(block, "findings-remain"), (
            "wave reopen must appear before findings-remain in the block"
        )


def test_plan_pre_execute_block_has_no_reopen() -> None:
    """Pin no wave reopen in the PLAN pre-EXECUTE findings-remain block.

    That block fires from SPEC-PLAN-REVIEW, not CODE-REVIEW, so the guard
    does not apply.
    """
    text = FULL_MODE_ENGINE.read_text(encoding="utf-8")
    # Locate the pre-EXECUTE section (before ## GATES).
    plan_section_end = text.index("## GATES")
    plan_section = text[:plan_section_end]
    blocks = fenced_blocks(plan_section)
    for block in blocks:
        if block_fires_edge(block, "findings-remain"):
            assert REOPEN_CMD not in block, (
                "wave reopen must not appear in the pre-EXECUTE findings-remain block"
            )


# ---------------------------------------------------------------------------
# finding-adjudication.md per-site assertions
# ---------------------------------------------------------------------------


def test_finding_adjudication_blocks_carry_code_review_condition() -> None:
    """Pin the CODE-REVIEW condition comment in both finding-adjudication blocks."""
    text = FINDING_ADJUDICATION.read_text(encoding="utf-8")
    blocks = fenced_blocks(text)
    # Blocks where findings-remain is the actual transition invocation.
    reopen_blocks = [
        b for b in blocks
        if block_fires_edge(b, "findings-remain") and REOPEN_CMD in b
    ]
    assert len(reopen_blocks) == 2, (
        f"Expected 2 finding-adjudication blocks with reopen and findings-remain, "
        f"got {len(reopen_blocks)}"
    )
    for block in reopen_blocks:
        assert "CODE-REVIEW" in block, (
            "Each finding-adjudication reopen block must state the CODE-REVIEW condition"
        )
        assert reopen_precedes_edge(block, "findings-remain"), (
            "wave reopen must appear before findings-remain in the block"
        )


def test_pre_execute_review_block_has_no_reopen() -> None:
    """Pin no wave reopen in pre-execute-review.md's findings-remain block.

    That block fires from SPEC-PLAN-REVIEW, not CODE-REVIEW.
    """
    text = PRE_EXECUTE_REVIEW.read_text(encoding="utf-8")
    blocks = fenced_blocks(text)
    for block in blocks:
        if block_fires_edge(block, "findings-remain"):
            assert REOPEN_CMD not in block, (
                "wave reopen must not appear in pre-execute-review.md's block"
            )


# ---------------------------------------------------------------------------
# session-resumption.md per-site assertions (table cells, not fenced blocks)
#
# These two sites are pinned by name only. The invocation count below cannot
# see table cells; this is the pin's stated blind spot (see module docstring).
# ---------------------------------------------------------------------------


def _find_table_row(text: str, key_col: str, second_col: str) -> str:
    """Return the first table row containing both key_col and second_col."""
    for line in text.splitlines():
        if key_col in line and second_col in line:
            return line
    return ""


def test_session_resumption_wave_complete_row_carries_reopen_before_gates_failed() -> None:
    """Pin wave reopen before gates-failed in the wave-complete resumption row."""
    text = SESSION_RESUMPTION.read_text(encoding="utf-8")
    # The wave-complete row also contains CODE-VERIFICATION.
    row = _find_table_row(text, "`wave-complete`", "CODE-VERIFICATION")
    assert row, "wave-complete / CODE-VERIFICATION row not found in session-resumption.md"
    assert REOPEN_CMD in row, (
        "wave reopen must appear in the wave-complete row of session-resumption.md"
    )
    assert "gates-failed" in row, (
        "gates-failed must appear in the wave-complete row of session-resumption.md"
    )
    assert row.index(REOPEN_CMD) < row.index("gates-failed"), (
        "wave reopen must precede gates-failed in the wave-complete row"
    )


def test_session_resumption_reviewers_clean_row_carries_reopen_before_blocker_applied() -> None:
    """Pin wave reopen before blocker-applied in the reviewers-clean resumption row."""
    text = SESSION_RESUMPTION.read_text(encoding="utf-8")
    # The CODE-HUMAN-GATE reviewers-clean row contains both markers.
    row = _find_table_row(text, "`reviewers-clean`", "CODE-HUMAN-GATE")
    assert row, (
        "reviewers-clean / CODE-HUMAN-GATE row not found in session-resumption.md"
    )
    assert REOPEN_CMD in row, (
        "wave reopen must appear in the reviewers-clean row of session-resumption.md"
    )
    assert "blocker-applied" in row, (
        "blocker-applied must appear in the reviewers-clean row of session-resumption.md"
    )
    assert row.index(REOPEN_CMD) < row.index("blocker-applied"), (
        "wave reopen must precede blocker-applied in the reviewers-clean row"
    )


# ---------------------------------------------------------------------------
# SKILL.md per-site assertions
# ---------------------------------------------------------------------------


def test_skill_gates_paragraph_mentions_wave_reopen() -> None:
    """Pin wave reopen in SKILL.md's GATES wave-routing paragraph."""
    text = SKILL_MD.read_text(encoding="utf-8")
    # Find the GATES wave routing paragraph.
    gates_section = text[text.index("## Step 3. GATES"):]
    gates_paragraph = gates_section[: gates_section.index("## Step 4.")]
    assert REOPEN_CMD in gates_paragraph, (
        "SKILL.md GATES section must mention wave reopen"
    )
    assert "gates-failed" in gates_paragraph, (
        "SKILL.md GATES section must mention gates-failed"
    )


def test_skill_review_specialist_paragraph_mentions_wave_reopen() -> None:
    """Pin wave reopen in SKILL.md's REVIEW specialist-findings paragraph."""
    text = SKILL_MD.read_text(encoding="utf-8")
    # Find the paragraph about specialist findings in the REVIEW section.
    review_section = text[text.index("## Step 4. REVIEW"):]
    # Locate the specialist-findings paragraph specifically.
    assert "specialist adjudication" in review_section, (
        "SKILL.md must contain the specialist-adjudication paragraph"
    )
    specialist_para_start = review_section.index("specialist adjudication")
    specialist_para = review_section[specialist_para_start : specialist_para_start + 500]
    assert REOPEN_CMD in specialist_para, (
        "SKILL.md specialist-findings paragraph must mention wave reopen"
    )
    assert "findings-remain" in specialist_para, (
        "SKILL.md specialist-findings paragraph must mention findings-remain"
    )


# ---------------------------------------------------------------------------
# state-schema.md assertion
# ---------------------------------------------------------------------------


def test_state_schema_dispatch_receipts_describes_superseded_member() -> None:
    """Pin the superseded member description and absence rule in state-schema.md."""
    text = STATE_SCHEMA.read_text(encoding="utf-8")
    # Find the actual table row: it starts with "| `dispatch_receipts` |".
    row = _find_table_row(text, "| `dispatch_receipts` |", "receipts container")
    assert row, "dispatch_receipts table row not found in state-schema.md"
    assert "superseded" in row, (
        "dispatch_receipts row must describe the superseded member"
    )
    # The absence rule: absence means live.
    assert "Absence of `superseded` means live" in row, (
        "dispatch_receipts row must state that absence of superseded means live"
    )
    # The old unqualified statement must not remain without qualification.
    assert "Both count as accounted for" not in row, (
        "dispatch_receipts row must not state unqualified 'Both count as accounted for'"
    )


# ---------------------------------------------------------------------------
# Invocation count (fenced blocks only; table cells are excluded by design)
# ---------------------------------------------------------------------------

_PROCEDURE_FILES = [
    FULL_MODE_ENGINE,
    FINDING_ADJUDICATION,
    PRE_EXECUTE_REVIEW,
]


def test_transition_invocation_count_is_seven() -> None:
    """Assert exactly 7 loop-engine transition invocations naming a guarded edge.

    Counts non-comment invocation lines, not fenced blocks. Two blocks already
    name a second edge in comment lines; a block count stays constant when a
    new firing line is added inside one of those blocks. This count catches it.

    session-resumption.md is excluded because its two firing sites are table
    cells; the named assertions above cover them (see module docstring for the
    stated blind spot).
    """
    count = count_invocations(_PROCEDURE_FILES)
    assert count == 7, (
        f"Expected 7 loop-engine transition invocations naming a guarded edge "
        f"across procedure files, found {count}. "
        f"A new invocation must be classified (add a named per-site assertion "
        f"above and update this count)."
    )
