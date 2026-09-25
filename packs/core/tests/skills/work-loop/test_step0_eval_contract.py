"""Contract checks for work-loop Step 0 behavior evals."""

from __future__ import annotations

import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
EVALS_PATH = PACK_ROOT / ".apm/skills/work-loop/evals/evals.json"


def _evals_by_id() -> dict[str, dict[str, object]]:
    """Return the work-loop behavior evals keyed by stable identifier."""
    payload = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    return {str(item["id"]): item for item in payload["evals"]}


def test_step0_evals_follow_canonical_workspace_preflight() -> None:
    """Step 0 evals must test canonical active and ready routing."""
    evals = _evals_by_id()

    resume = evals["step0-one-canonical-active-resume"]
    assert "Resuming `docs/specs/my-feature/spec.md`" in resume["expected_output"]

    ready = evals["step0-zero-active-one-canonical-ready"]
    assert "first canonical ready item" in ready["expected_output"]
    assert "Raw workspace queue membership does not authorize" in ready["expected_output"]

    empty = evals["step0-no-canonical-ready-or-active"]
    assert "No canonical ready or active spec found" in empty["expected_output"]

    multiple = evals["step0-multiple-canonical-active-specs"]
    assert "both canonical active spec paths" in multiple["expected_output"]


def test_schedule_refuses_unknown_dependency_eval_contract() -> None:
    """Eval entry for unknown-dependency refusal must name both topics in its assertions.

    The catalogue lint only checks assertions are non-empty strings, so nothing
    else notices if the entry stops mentioning refusal or the forward-reference
    contrast at all.  This check pins that both topics are mentioned; it is a
    substring search, so it does not observe polarity — an assertion could name
    refusal and still say the wrong thing about it, and that is the eval run's
    job to catch, not this one's.
    """
    import re

    evals = _evals_by_id()
    assert "schedule-refuses-unknown-dependency" in evals, (
        "Missing eval entry 'schedule-refuses-unknown-dependency' in evals.json"
    )
    entry = evals["schedule-refuses-unknown-dependency"]
    assertions: list[str] = list(entry["assertions"])  # type: ignore[arg-type]

    has_refus = any(re.search("refus", a, re.IGNORECASE) for a in assertions)
    assert has_refus, (
        "No assertion in 'schedule-refuses-unknown-dependency' matches 'refus' (case-insensitive)"
    )

    has_forward = any(re.search("forward", a, re.IGNORECASE) for a in assertions)
    assert has_forward, (
        "No assertion in 'schedule-refuses-unknown-dependency' matches 'forward' (case-insensitive)"
    )


def test_step0_evals_do_not_retain_superseded_messages() -> None:
    """The eval corpus must not contradict the live canonical preflight.

    Search the decoded strings, not the file bytes: a JSON corpus may carry either `\\u2014`
    escapes or literal em dashes, and which a writer emits is not this test's
    business, so a raw-text search for either form leaves the other as a blind
    spot.
    """
    payload = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    decoded = json.dumps(payload, ensure_ascii=False)

    assert "Beginning on `docs/specs/my-feature/spec.md`" not in decoded
    assert "No active spec found — run `workspace-status`" not in decoded
    assert "Step 0 reads workspace.toml only to orient" not in decoded
