"""Construction pins for the typed preservation-review eval cases (AC-0017).

Spec: docs/specs/grounding-preservation-review/spec.md
"""

import ast
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

PACK_ROOT = Path(__file__).resolve().parents[3]
EVALS_DIR = PACK_ROOT / ".apm/skills/work-loop/evals"
FIXTURE_DIR = EVALS_DIR / "files/preservation-review"
SPEC_PATH = "evals/files/preservation-review/spec.md"
ADVERSARIAL_ID = "typed-review-binds-missed-consumer-to-preservation-criterion"
QUALITY_ID = "typed-review-binds-weak-evidence-to-preservation-criterion"
LISTING_FUNCTION = "outline"


def _load_fixture_graph() -> ModuleType:
    """Load the fixture ``graph.py`` by literal path under a unique module name."""
    path = Path(__file__).resolve().parents[3] / ".apm/skills/work-loop/evals/files/preservation-review/graph.py"
    spec = importlib.util.spec_from_file_location("core_work_loop_preservation_review_fixture_graph", str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Keep bytecode out of the shipped skill tree.
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _case(case_id: str) -> dict[str, Any]:
    """Return the eval case with the given id, failing if it is absent."""
    payload = json.loads((EVALS_DIR / "evals.json").read_text(encoding="utf-8"))
    matches = [item for item in payload["evals"] if item["id"] == case_id]
    assert len(matches) == 1, f"expected exactly one case {case_id}"
    return matches[0]


def test_both_cases_ship_their_fixture_files() -> None:
    """Each case lists files that exist under the preservation-review fixture."""
    on_disk = {p.name for p in FIXTURE_DIR.iterdir() if p.is_file()}
    for case_id in (ADVERSARIAL_ID, QUALITY_ID):
        files = _case(case_id)["files"]
        assert SPEC_PATH in files
        for rel in files:
            assert rel.startswith("evals/files/preservation-review/")
            assert Path(rel).name in on_disk


def test_fixture_spec_is_approved_and_carries_criteria() -> None:
    """The fixture spec reads Approved and carries CRIT-2 and CRIT-3."""
    text = (FIXTURE_DIR / "spec.md").read_text(encoding="utf-8")
    for needle in ("- **Status:** Approved", "CRIT-2", "CRIT-3"):
        assert needle in text


def test_prompts_name_the_fixture_spec() -> None:
    """Each prompt names the fixture spec as the spec findings bind to."""
    for case_id in (ADVERSARIAL_ID, QUALITY_ID):
        assert SPEC_PATH in _case(case_id)["prompt"]


def test_adversarial_case_binds_missed_consumer_without_naming_it() -> None:
    """The expected output names CRIT-3; the prompt hides the listing consumer."""
    case = _case(ADVERSARIAL_ID)
    assert "CRIT-3" in case["expected_output"]
    assert LISTING_FUNCTION not in case["prompt"]
    assert any(
        "filtered search path" in a and "no reachability or missed-consumer finding" in a.lower()
        for a in case["assertions"]
    )
    assert any("CRIT-3" in a for a in case["assertions"])


def test_quality_case_binds_tautological_test_to_crit_2() -> None:
    """The quality expected output names CRIT-2 and an assertion requires it."""
    case = _case(QUALITY_ID)
    assert "CRIT-2" in case["expected_output"]
    assert any("CRIT-2" in a for a in case["assertions"])


def test_hidden_listing_consumer_exists_and_returns_value_nodes() -> None:
    """The consumer the prompt hides is in the fixture and does not filter values."""
    graph_module = _load_fixture_graph()
    listing = getattr(graph_module, LISTING_FUNCTION, None)
    assert callable(listing), f"fixture graph.py has no {LISTING_FUNCTION}"
    graph = graph_module.build(["def run", "value limit"])
    assert any(entry.startswith("value ") for entry in listing(graph))


def test_fixture_ordinary_calls_test_takes_expected_side_from_code_under_test() -> None:
    """The tautological test builds its expected value by calling ``resolve_calls``."""
    tree = ast.parse((FIXTURE_DIR / "test_graph.py").read_text(encoding="utf-8"))
    [func] = [
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "test_ordinary_calls_resolve_to_definitions"
    ]
    [expected] = [
        n.value for n in ast.walk(func)
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "expected" for t in n.targets)
    ]
    assert any(
        isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "resolve_calls"
        for c in ast.walk(expected)
    )
