"""Construction test for shared-substrate preservation evidence evaluation."""

import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
EVALS_PATH = PACK_ROOT / ".apm/skills/work-loop/evals/evals.json"
EVAL_ID = "shared-substrate-feature-tests-do-not-prove-preservation"


def test_feature_only_evidence_cannot_complete_shared_substrate_work() -> None:
    """Keep all preservation classes in the implementation-phase evaluation."""
    payload = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    case = next(item for item in payload["evals"] if item["id"] == EVAL_ID)
    expected = case["expected_output"]

    for signal in (
        "ordinary-call isolation",
        "default-search exclusion",
        "full/incremental semantic equivalence",
        "bounded invalidation",
        "production lifecycle removal",
        "supported external compilation",
    ):
        assert signal in expected

    assert "absence of adapt-to-project or code intelligence cannot lower" in expected
    assert "feature creation tests alone" in case["assertions"][0]
