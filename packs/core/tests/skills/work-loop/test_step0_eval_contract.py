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


def test_step0_evals_do_not_retain_superseded_messages() -> None:
    """The eval corpus must not contradict the live canonical preflight.

    Search the decoded strings, not the file bytes: this corpus mixes `\\u2014`
    escapes and literal em dashes, so a raw-text search for either form leaves
    the other as a blind spot.
    """
    payload = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    decoded = json.dumps(payload, ensure_ascii=False)

    assert "Beginning on `docs/specs/my-feature/spec.md`" not in decoded
    assert "No active spec found — run `workspace-status`" not in decoded
    assert "Step 0 reads workspace.toml only to orient" not in decoded
