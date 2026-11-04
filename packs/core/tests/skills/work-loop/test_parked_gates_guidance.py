"""Content pins for the parked-gate guidance in the shipped work-loop skill.

Goal-based: reads the shipped skill files by literal path; no supervisor process runs.
"""

import json
from pathlib import Path
from typing import Any

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_MD = PACK_ROOT / ".apm/skills/work-loop/SKILL.md"
SUPERVISOR_MD = PACK_ROOT / ".apm/skills/work-loop/references/supervisor.md"
RESUMPTION_MD = PACK_ROOT / ".apm/skills/work-loop/references/session-resumption.md"
STATE_SCHEMA_MD = PACK_ROOT / ".apm/skills/work-loop/references/state-schema.md"
LIFECYCLE_MD = PACK_ROOT / ".apm/skills/work-loop/references/delivery-contract-lifecycle.md"
EVALS_JSON = PACK_ROOT / ".apm/skills/work-loop/evals/evals.json"

PARKED_EVAL_ID = "parked-gate-without-answer-works-the-other-spec"
DIGEST_ARGS = ("--approved-spec-digest", "--approved-plan-digest")


def _text(path: Path) -> str:
    """Read a shipped file as UTF-8 with newlines folded to single spaces."""
    return " ".join(path.read_text(encoding="utf-8").split())


def _case(case_id: str) -> dict[str, Any]:
    """Return the eval case with the given id, failing if it is absent."""
    cases = json.loads(EVALS_JSON.read_text(encoding="utf-8"))["evals"]
    matches = [case for case in cases if case["id"] == case_id]
    assert len(matches) == 1
    return matches[0]


def test_t6_verb_table_lists_park_gates_and_start_digest_arguments() -> None:
    """AC-0020: the verb table has park and gates rows, and start names both digests."""
    rows = [
        line for line in SUPERVISOR_MD.read_text(encoding="utf-8").splitlines()
        if line.startswith("| `")
    ]
    park = [r for r in rows if r.startswith("| `park <spec-dir> --gate spec-approved")]
    gates = [r for r in rows if r.startswith("| `gates` |")]
    start = [r for r in rows if r.startswith("| `start <spec-dir>")]
    assert len(park) == 1 and len(gates) == 1 and len(start) == 1
    assert "--intent code" in park[0] and "--code-trust trusted" in park[0]
    for arg in DIGEST_ARGS:
        assert arg in start[0]
    assert "ignored when it answers `current`" in start[0]


def test_t6_supervisor_reference_describes_gates_states_and_refusals() -> None:
    """The reference names the listing states, the stored-bytes read, and every new code."""
    text = _text(SUPERVISOR_MD)
    for state in ("`pending`", "`stale`", "`invalid`"):
        assert state in text
    assert "print exactly the stored bytes" in text
    for code in (
        "gate-unsafe-path", "gate-uncommitted", "gate-already-admitted",
        "gate-status-mismatch", "gate-unsafe-content", "gate-changelog-shape",
        "gate-spec-changed", "gate-record-unwritable", "approval-digest-required",
        "approval-digest-mismatch",
    ):
        assert f"| `{code}` |" in SUPERVISOR_MD.read_text(encoding="utf-8")


def test_t6_skill_approval_step_carries_the_parked_gate_rules() -> None:
    """AC-0021: park, relay each digest from its own answer, no dispatch, never approved."""
    text = _text(SKILL_MD)
    assert "Park each gate once the pre-EXECUTE reviewers are clean" in text
    assert "Show the human the `gates` entry" in text
    assert "the spec digest from the spec approver's own answer" in text
    assert "the plan digest from the plan approver's own answer" in text
    assert "a digest copied from `park` or `gates` output without that answer is not an approval" in text
    assert "Dispatch no implementation work for a parked spec" in text
    assert "through the rejected-gate route" in text
    assert "work another spec that does not depend on it" in text
    assert "Never treat a parked gate as approved" in text
    assert "no answer, a timeout, a stale entry, or a listing is never an approval" in text


def test_t6_resumption_state_schema_and_lifecycle_carry_the_gate_rules() -> None:
    """Resumption, the state table, and the amendment path mention parked gates."""
    assert "gates` and show the human" in _text(RESUMPTION_MD) or "run `python" in _text(RESUMPTION_MD)
    resumption = _text(RESUMPTION_MD)
    assert "A `stale` entry is re-reviewed and parked again" in resumption
    schema = STATE_SCHEMA_MD.read_text(encoding="utf-8")
    rows = [r for r in schema.splitlines() if r.startswith("| `<git-dir>/agentbundle-supervisor/gates/`")]
    assert len(rows) == 1 and "| `park` | no |" in rows[0] and "One record per spec" in rows[0]
    assert "park each gate again" in _text(LIFECYCLE_MD)


def test_t6_parked_gate_eval_case_is_present() -> None:
    """AC-0022: the case parks a gate with no answer beside an independent ready spec."""
    case = _case(PARKED_EVAL_ID)
    assert set(case) >= {"id", "prompt", "expected_output", "assertions"}
    assert "no answer" in case["prompt"] and "does not depend on spec A" in case["prompt"]
    joined = " ".join(case["assertions"])
    assert "works spec B" in joined
    assert "does NOT run `work-supervisor.py start` for the parked spec A" in joined
    assert "does NOT report the parked gate as approved" in joined


def test_t6_every_start_command_line_names_both_digest_arguments() -> None:
    """Every shipped line that shows a `start <spec-dir>` command carries both digests."""
    missing = []
    for path in (SKILL_MD, SUPERVISOR_MD, RESUMPTION_MD, STATE_SCHEMA_MD, LIFECYCLE_MD, EVALS_JSON):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "start <spec-dir>" in line and not all(arg in line for arg in DIGEST_ARGS):
                missing.append(f"{path.name}:{number}")
    assert missing == []
