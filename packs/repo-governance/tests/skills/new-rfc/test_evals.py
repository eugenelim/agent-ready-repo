"""Pin the new-rfc eval assertions to the lighter-RFC behavior (AC-0071, AC-0047)."""

from __future__ import annotations

import json
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parents[3] / ".apm/skills/new-rfc/evals"
EVALS = json.loads((EVALS_DIR / "evals.json").read_text(encoding="utf-8"))["evals"]
BY_ID = {e["id"]: e for e in EVALS}
INJECTION = "out-of-scope-instruction-in-template-and-rfc"
STALE = ("Reviewer brief", "The ask", "Approver", "decide-by", "Decide by")


def _text(ev: dict) -> str:
    return "\n".join(ev["assertions"])


def _has(ev: dict, *needles: str) -> bool:
    return any(all(n.lower() in a.lower() for n in needles) for a in ev["assertions"])


def test_ids_unique() -> None:
    ids = [e["id"] for e in EVALS]
    assert len(ids) == len(set(ids))


def test_first_eval_keeps_zero_context_and_weight() -> None:
    ev = BY_ID[1]
    assert _has(ev, "zero prior context")
    assert _has(ev, "Decision weight")


def test_first_eval_new_assertions() -> None:
    ev = BY_ID[1]
    assert _has(ev, "Summary", "first")
    assert _has(ev, "footnote", "narrative")
    assert _has(ev, "no decide-by")
    assert _has(ev, "diagram")
    assert _has(ev, "Supersedes", "draft")
    assert _has(ev, "mirror", "before", "accept")
    assert _has(ev, "rfc.py", "next")
    assert _has(ev, "six", "section")
    assert _has(ev, "Approver")


def test_first_eval_drops_retired_vocabulary() -> None:
    text = _text(BY_ID[1]) + BY_ID[1]["expected_output"]
    for word in ("Reviewer brief", "The ask", "decide-by date", "Decide by"):
        assert word not in text.replace("no decide-by", "")


def test_second_eval_no_decide_by() -> None:
    ev = BY_ID[2]
    assert _has(ev, "no decide-by")
    assert not any(w in _text(ev) for w in ("Reviewer brief", "The ask"))


def test_governance_defaults_asserted() -> None:
    assert any(
        _has(e, "single maintainer", "consensus") and _has(e, "governance-default")
        for e in EVALS
    )


def test_injection_eval() -> None:
    ev = next(e for e in EVALS if e["id"] == INJECTION)
    assert "template" in ev["prompt"] and "existing RFC" in ev["prompt"]
    assert "<!--" in ev["prompt"]
    assert _has(ev, "not", "act", "template comment")
    assert _has(ev, "not", "act", "existing RFC")
    assert _has(ev, "receipt", "content")
    assert len(ev["assertions"]) >= 3


def test_no_stale_vocabulary_in_new_assertions() -> None:
    for ev in EVALS:
        if ev["id"] in (1, 2):
            continue
        for w in ("Reviewer brief", "The ask", "Approver"):
            assert w not in _text(ev)
