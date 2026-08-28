"""PLAN-time contract stubs for sealed-baseline replacement."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import uuid
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
ENGINE = SKILL_DIR / "scripts" / "loop-engine.py"
COHORT = SKILL_DIR / "scripts" / "loop-cohort.py"
RECORD = SKILL_DIR / "scripts" / "resolve-vs-surface.py"


def load_module(path: Path, name: str):
    """Load an executable loop surface without duplicating its contract."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_engine_has_one_owner_authorized_replacement_event() -> None:
    """Current and already-drifted plans share one guarded park route."""
    # STUB: AC1
    engine = load_module(ENGINE, "core_work_loop_baseline_replacement_engine")
    event = "baseline-replacement-required"
    for state in ("CODE-IMPLEMENTATION", "CODE-VERIFICATION", "CODE-REVIEW"):
        assert engine._CODE_TRANSITIONS[(state, event)] == "SPEC-PLAN-DRAFTING"
    assert all(key[1] != event for key in engine._SPEC_PLAN_TRANSITIONS)


def test_cohort_exposes_replacement_and_task_evidence_contracts(tmp_path: Path) -> None:
    """The executable parser admits only the two planned mutation surfaces."""
    # STUB: AC2
    # STUB: AC3
    cohort = load_module(COHORT, "core_work_loop_baseline_replacement_cohort")
    run_id = str(uuid.uuid4())
    invalidate = cohort.build_parser().parse_args(
        [
            "invalidate-baseline",
            str(tmp_path),
            "--expect-run-id",
            run_id,
            "--expect-transition-sequence",
            "1",
        ]
    )
    complete = cohort.build_parser().parse_args(
        ["task", "complete", str(tmp_path), "T1", "--expect-run-id", run_id]
    )
    assert invalidate.func is cohort.cmd_invalidate_baseline
    assert complete.func is cohort.cmd_task_complete


def test_run_record_helper_creates_the_ignored_record(tmp_path: Path) -> None:
    """The run record has an executable owner outside pinned artifacts."""
    # STUB: AC6
    # STUB: AC7
    run_id = str(uuid.uuid4())
    result = subprocess.run(
        [sys.executable, str(RECORD), "open", str(tmp_path), "--run-id", run_id],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    path = tmp_path / ".context" / "work-loop" / run_id / "resolve-vs-surface.md"
    assert path.is_file()
