"""Content pins for the parked-gate guidance in the shipped work-loop skill.

Goal-based: reads the shipped skill files by literal path; no supervisor process runs.
"""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
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
        "gate-status-mismatch", "gate-unsafe-content",
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


ENTRY_FORM = "- YYYY-MM-DD: spec|plan|amendment approved by <handle>"
PRE_EXECUTE_MD = PACK_ROOT / ".apm/skills/work-loop/references/pre-execute-review.md"
PLAN_TEMPLATE_MD = PACK_ROOT / ".apm/skills/new-spec/assets/plan.md"
GATES_PY = PACK_ROOT / ".apm/skills/work-loop/scripts/_supervisor_gates.py"


def _load_gates() -> ModuleType:
    """Load the shipped gates script by path under a unique, registered alias."""
    alias = "core_work_loop_parked_gates_guidance_t12"
    spec = importlib.util.spec_from_file_location(alias, str(GATES_PY))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


G = _load_gates()


def test_t11_reference_states_the_approval_entry_form_once() -> None:
    """AC-0021: the reference gives the one form; it has no changelog-shape row."""
    raw = SUPERVISOR_MD.read_text(encoding="utf-8")
    text = _text(SUPERVISOR_MD)
    assert text.count(ENTRY_FORM) == 1
    assert "optionally followed by ` (scope)`, ` (build strategy)` or ` (scope and build strategy)`" in text
    assert "One line, placed under the file's last `## Changelog` heading" in text
    assert "A wrapped or differently worded entry is ordinary text and changes the gate digest" in text
    assert "| `gate-changelog-shape` |" not in raw


def test_t11_other_surfaces_state_or_point_to_the_form() -> None:
    """AC-0021: SKILL.md, pre-execute-review, the template, and `gates` text point to it."""
    assert "Parked gates section of [`references/supervisor.md`]" in _text(SKILL_MD)
    assert "Parked gates section of `supervisor.md`" in _text(PRE_EXECUTE_MD)
    template = _text(PLAN_TEMPLATE_MD)
    assert "`references/supervisor.md` (Parked gates) is the one statement of it" in template
    assert "- YYYY-MM-DD: spec approved by <handle>" in template
    for gate in ("spec-approved", "plan-approved"):
        approve = G.ANSWERS[gate]["approve"]
        assert ENTRY_FORM in approve
        assert "Parked gates section of the supervisor reference" in approve


REASONS = ("`scope`", "`build strategy`", "`scope and build strategy`")


def test_t12_ac0021_pre_execute_review_and_template_state_the_parked_gate_rules() -> None:
    """AC-0021: each surface states the five rules or points to the reference's section."""
    review = _text(PRE_EXECUTE_MD)
    assert "park each gate" in review
    assert "`--approved-spec-digest` from the spec approver's own answer" in review
    assert "`--approved-plan-digest` from the plan approver's own answer" in review
    assert "one approval-entry line" in review
    assert "Dispatch no implementation work for a parked spec" in review
    assert "never treat a parked gate as approved" in review
    template = _text(PLAN_TEMPLATE_MD)
    assert "park each gate" in template
    assert "the spec digest from the spec approver's own answer" in template
    assert "the plan digest from the plan approver's own answer" in template
    assert "one approval-entry line per approval" in template
    assert "dispatch no implementation work for a parked spec" in template
    assert "never treat a parked gate as approved" in template


def test_t12_ac0021_entry_form_paraphrases_quote_the_reasons_period_and_kind() -> None:
    """AC-0021: the reference quotes the reason set, the optional period, and the kinds."""
    text = _text(SUPERVISOR_MD)
    assert "optionally followed by ` (scope)`, ` (build strategy)` or ` (scope and build strategy)`" in text
    assert "the final period is optional" in text
    assert "The kind is `spec`, `plan`, or `amendment`" in text
    for surface in (PRE_EXECUTE_MD, PLAN_TEMPLATE_MD, SKILL_MD):
        paraphrase = _text(surface)
        assert "optional scope note" not in paraphrase
        assert "and a final period" not in paraphrase
