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


def test_step0_evals_follow_dispatch_decision() -> None:
    """Step 0 evals must pin the AC-0002 cases of spec-registration-stop."""
    evals = _evals_by_id()
    for case_id in (
        "step0-dispatch-start",
        "step0-dispatch-resume",
        "step0-dispatch-ask",
        "step0-dispatch-none",
        "step0-dispatch-refuse",
        "step0-supplied-path-start",
        "step0-supplied-path-resume-refused",
        "step0-explicit-request-conflict",
        "step0-no-registry-start",
    ):
        case = evals[case_id]
        assert str(case["expected_output"]).strip(), case_id
        assert case["assertions"], case_id

    ask = evals["step0-dispatch-ask"]
    assert "candidates" in str(ask["expected_output"])
    assert "candidates" in "\n".join(str(item) for item in ask["assertions"])  # type: ignore[attr-defined]


def test_resumption_evals_name_the_supervisor_verbs() -> None:
    """The resumption evals must name the supervisor verb that answers each case.

    The catalogue lint only checks assertions are non-empty strings, so nothing
    else notices if an entry stops naming the verb it teaches. This is a
    substring search and does not observe polarity; the eval run catches that.
    """
    evals = _evals_by_id()
    for eval_id, verb in (
        ("resume-reads-status-first", "work-supervisor.py status"),
        ("approved-without-start-resumption", "work-supervisor.py start"),
        ("resume-after-interrupted-report", "next"),
    ):
        assert eval_id in evals, f"Missing eval entry {eval_id!r} in evals.json"
        entry = evals[eval_id]
        text = str(entry["expected_output"]) + " ".join(str(a) for a in entry["assertions"])
        assert verb in text, f"{eval_id!r} no longer names {verb!r}"


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


def test_base_freshness_skipped_eval_contract() -> None:
    """The skipped freshness eval must distinguish unverified from current."""
    evals = _evals_by_id()
    entry = evals["base-freshness-skipped-continues-with-notice"]
    expected = str(entry["expected_output"])
    assertions = "\n".join(str(item) for item in entry["assertions"])
    combined = expected + "\n" + assertions

    assert "freshness was not verified" in combined
    assert "update the branch separately" in combined
    assert "continue the work-loop" in combined
    assert "Do not retry" in expected
    assert "does NOT retry" in assertions
    assert "do not Surface or pause" in expected
    assert "does NOT Surface, stop, or pause" in assertions
    assert "do not claim `HEAD` or the base is current" in expected
    assert "does NOT claim `HEAD` or the base is current" in assertions
