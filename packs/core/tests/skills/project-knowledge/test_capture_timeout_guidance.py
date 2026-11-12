"""Pin the caller recovery budget without changing the storage contract."""

import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm/skills/project-knowledge"


def test_capture_timeout_recovery_is_bounded_and_preserves_identity() -> None:
    """Only retryable deadlines receive one visible identical resubmission."""
    text = (SKILL / "references/capture-mode.md").read_text(encoding="utf-8")
    section = text.split("## Recovering a capture timeout\n", 1)[1].split("\n## ", 1)[0]
    section = " ".join(section.split())
    for phrase in (
        "both `reason_code=deadline_exceeded` and `retryable=true`",
        "user-visible recovery", "one retry with the same request",
        "Preserve its exact bytes", "identity-bearing fields",
        "privacy attestation", "replay receipt", "If the retry fails, stop",
        "not confirmed retained", "Do not retry a non-retryable refusal",
        "a lock diagnostic", "zero internal automatic retries",
    ):
        assert phrase in section
    route = (SKILL / "SKILL.md").read_text(encoding="utf-8").split("## From a delivery candidate", 1)[0]
    assert "Recovering a capture timeout" in route


def test_timeout_evals_cover_recovery_exhaustion_and_wrong_reason() -> None:
    """The harness distinguishes success, failed recovery, and lock refusal."""
    cases = {case["id"]: case for case in json.loads((SKILL / "evals/evals.json").read_text(encoding="utf-8"))["evals"]}
    for kind in ("transient", "persistent", "non-deadline"):
        case = cases["capture-timeout-" + kind]
        assert case["assertions"]
        assert "same request" in case["expected_output"] or kind == "non-deadline"
    assert "not confirmed retained" in cases["capture-timeout-persistent"]["expected_output"]
    assert "Do not retry" in cases["capture-timeout-non-deadline"]["expected_output"]
    assert "reason_code=lock_contention" in cases["capture-timeout-non-deadline"]["prompt"]
