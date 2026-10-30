"""A plan-resident consumer map is disposable: losing it cannot move the verdict.

new-spec's shared-substrate preservation reference keeps the consumer map in the
plan's `## Design (LLD)`, never in `spec.md`. This pins what that rule relies on,
through the supervisor: after a full run, deleting or rebuilding the map in the
plan's design leaves the criteria evidence and readiness exactly as they were,
and the same map written into the spec's protected scope text is refused and
commits nothing.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack- and skill-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _helper("supervisor_harness")
sup = _helper("supervisor_support")

pytestmark = sup.INTEGRATION

SPEC = h.SPEC_DIR
MAP_HEADER = "| Class | Consumer evidence | Criterion or gap |\n| --- | --- | --- |\n"
MAP_ROWS = (
    "| selection and resolution | src/consumers.py:4 | AC-0001 |",
    "| default search | src/consumers.py:9 | AC-0002 |",
    "| lifecycle and cleanup | src/lifecycle.py:9 | AC-0002 |",
)


def _map(rows: tuple[str, ...]) -> str:
    return MAP_HEADER + "\n".join(rows) + "\n"


def _plan_with(map_text: str) -> str:
    design = "## Design (LLD)\n\n" + map_text + "\n" if map_text else "## Design (LLD)\n\nnone\n\n"
    return sup.PLAN.replace("## Tasks", design + "## Tasks", 1)


def _facts(repo: Path) -> dict[str, Any]:
    """What a verdict rests on: readiness, per-criterion outcomes, tasks, and the evidence bytes."""
    code, status = h.run_cli(repo, "status", SPEC, "--json")
    assert code == 0, status
    return {
        "readiness": status["readiness"],
        "tasks": [(t["title"], t["complete"]) for t in status["tasks"]],
        "evidence": h.workspace(repo).evidence_bytes(),
    }


def _replan(repo: Path, text: str) -> None:
    (repo / SPEC / "plan.md").write_text(text, "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0, payload
    assert payload.get("terminal") is True, payload


def _ops(repo: Path) -> list[str]:
    ws = h.workspace(repo)
    return [c.operation for c in ws.git.supervisor_commits(ws.approvals()[0]["run_id"])]


def test_deleting_or_rebuilding_the_plan_map_leaves_evidence_and_readiness_unchanged(
        tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path, plan=_plan_with(_map(MAP_ROWS)))
    assert h.start(repo)[0] == 0
    assert h.Controller(repo, tmp_path / "effects.log").drive().get("terminal")
    bound = _facts(repo)
    assert bound["readiness"]["ready"] is True
    assert set(bound["readiness"]["criteria"].values()) == {"supported"}

    _replan(repo, _plan_with(""))
    assert _facts(repo) == bound
    _replan(repo, _plan_with(_map(tuple(reversed(MAP_ROWS)))))
    assert _facts(repo) == bound
    assert _ops(repo)[-2:] == ["replan", "replan"]


def test_the_same_map_in_the_spec_is_refused_and_commits_nothing(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path, plan=_plan_with(""))
    assert h.start(repo)[0] == 0
    assert h.Controller(repo, tmp_path / "effects.log").drive().get("terminal")
    bound = _facts(repo)
    head = h.git(repo, "rev-parse", "HEAD")
    spec_path = repo / SPEC / "spec.md"
    spec_path.write_text(
        spec_path.read_text("utf-8").replace(
            "Only the calculator; no user interface.",
            "Only the calculator; no user interface.\n\n" + _map(MAP_ROWS),
            1,
        ),
        "utf-8",
    )

    code, refused = h.run_cli(repo, "next", SPEC)

    assert code == 1 and refused["refusal"]["code"] == "scope-changed", refused
    assert h.git(repo, "rev-parse", "HEAD") == head
    assert "replan" not in _ops(repo)
    assert h.workspace(repo).evidence_bytes() == bound["evidence"]
    _, status = h.run_cli(repo, "status", SPEC, "--json")
    assert status["refusal"]["code"] == "scope-changed", status
