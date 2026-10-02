"""Construction tests for the repository-grounding behavior evaluations."""

import ast
import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm/skills/new-spec"
EVALS_PATH = SKILL_ROOT / "evals/evals.json"

POSITIVE_ID = "shared-substrate-change-expands-preservation-proof"
NEGATIVE_ID = "isolated-private-change-does-not-expand-preservation-proof"

POSITIVE_FILES = {
    "evals/files/shared-graph-model.py",
    "evals/files/shared-graph-consumers.py",
    "evals/files/shared-graph-builders.py",
    "evals/files/shared-graph-lifecycle.py",
    "evals/files/shared-graph-public.rs",
}
NEGATIVE_FILES = {
    "evals/files/isolated_helper.py",
    "evals/files/test_isolated_helper.py",
}
PRESERVATION_SIGNALS = (
    "ordinary calls",
    "default queries",
    "full and incremental builds",
    "invalidation bound",
    "lifecycle paths",
    "external construction or destructuring",
)


def _evals_by_id() -> dict[str, dict[str, object]]:
    """Load behavior evaluations keyed by their stable identifiers."""
    payload = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload["evals"]}


def test_shared_substrate_case_requires_repository_discovery() -> None:
    """Keep the positive case from handing its expected consumer map to the model."""
    case = _evals_by_id()[POSITIVE_ID]
    prompt = str(case["prompt"])

    assert set(case["files"]) == POSITIVE_FILES
    assert "full and incremental" not in prompt
    assert "default search" not in prompt
    assert "public resolution" not in prompt
    for signal in PRESERVATION_SIGNALS:
        assert signal in str(case["expected_output"])


def test_isolated_case_is_a_real_negative_control() -> None:
    """Keep the negative case small enough that expansion is a false positive."""
    case = _evals_by_id()[NEGATIVE_ID]
    expected = str(case["expected_output"])

    assert set(case["files"]) == NEGATIVE_FILES
    assert "do not invent" in expected
    assert "shared substrate" in expected
    assert "bounded repository-native evidence" in expected


def test_repository_grounding_fixture_files_exist_and_python_parses() -> None:
    """Keep every declared fixture present and every Python fixture syntactically valid."""
    for relative_path in POSITIVE_FILES | NEGATIVE_FILES:
        path = SKILL_ROOT / relative_path
        assert path.is_file(), relative_path
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
