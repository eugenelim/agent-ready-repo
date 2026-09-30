import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "causal_runner",
    ROOT / "causal_runner.py",
)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def test_causal_design_compiles_exact_shared_panel() -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-causal-design.json")
    compiled = runner.compile_assignments(design)

    assert compiled["study_id"] == "codex-collaboration-r1"
    assert compiled["study_ceiling"] == 600
    assert compiled["maximum_used"] == 566
    assert compiled["shared_plan_authors"] == 18
    assert compiled["shared_build_panel"] == 90
    assert compiled["blind_adjudication_starts"] == {"run-1": 12, "run-7": 12}
    assert all(not item["released"] for item in compiled["holdout_assignments"])


def test_seed_changes_order_not_counts() -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-causal-design.json")
    changed = dict(design)
    changed["seed"] = "codex-collaboration-r1-v2"

    first = runner.compile_assignments(design)
    second = runner.compile_assignments(changed)

    assert first["maximum_used"] == second["maximum_used"] == 566
    assert first["shared_build_panel"] == second["shared_build_panel"] == 90
    assert first["assignment_digest"] != second["assignment_digest"]


def test_phase_receipts_reject_gaps_duplicates_and_reordering(tmp_path: Path) -> None:
    ledger = runner.PhaseLedger(tmp_path / "progress.jsonl")
    with pytest.raises(runner.ReceiptError):
        ledger.append("slot-1", "phase-launched")

    ledger.append("slot-1", "assignment-frozen")
    with pytest.raises(runner.ReceiptError):
        ledger.append("slot-1", "assignment-frozen")
    with pytest.raises(runner.ReceiptError):
        ledger.append("slot-1", "phase-terminal")


def test_provider_outputs_cannot_overwrite_legacy_records(tmp_path: Path) -> None:
    with pytest.raises(runner.PolicyError):
        runner.provider_output_path(tmp_path / "results.json")
    with pytest.raises(runner.PolicyError):
        runner.provider_output_path(tmp_path / "summary.json")
    assert runner.provider_output_path(tmp_path / "codex-collaboration-results.json")


def test_unavailable_telemetry_is_required_for_terminal_reports(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-causal-design.json")
    compiled = runner.compile_assignments(design)
    runner._write_json_atomic(tmp_path / "compiled-assignments.json", compiled)
    slot_id = compiled["assignments"][0]["slot_id"]
    runner.prepare_slot(tmp_path, slot_id)
    runner.record_launch(tmp_path, slot_id, "agent-dry-run")
    bad_report = tmp_path / "bad-report.json"
    bad_report.write_text(
        json.dumps(
            {
                "slot_id": slot_id,
                "status": "passed",
                "summary": "done",
                "deviations": [],
                "telemetry": {"provider_tokens": 7},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(runner.SchemaError):
        runner.ingest_terminal(tmp_path, slot_id, bad_report)


def test_candidate_commands_fail_closed_without_execution(tmp_path: Path) -> None:
    (tmp_path / "candidate").mkdir()
    command = {
        "argv": ["python3", "-c", "print('never')"],
        "cwd": "candidate",
        "env": {"API_TOKEN": "secret"},
        "timeout_seconds": 120,
        "max_output_bytes": 100,
        "network": "denied",
        "egress": "denied",
        "read_roots": ["candidate"],
        "write_roots": ["candidate"],
        "process_tree_cleanup": True,
    }

    record = runner.execute_candidate_command(command, run_dir=tmp_path)

    assert record.status == "non-executed"
    assert "environment" in record.note


def test_raw_artifacts_quarantine_suspected_material(tmp_path: Path) -> None:
    result = runner.retain_raw_artifact(tmp_path, "worker-output.txt", b"token=abcd")

    assert result["status"] == "quarantined"
    assert result["retained"] is False
    assert not (tmp_path / "raw" / "worker-output.txt").exists()


def test_cli_dry_run_lifecycle_without_model_spawn(tmp_path: Path) -> None:
    design_path = ROOT / "fixtures" / "valid-causal-design.json"
    design = runner.load_design(design_path)
    compiled = runner.compile_assignments(design)
    slot_id = compiled["assignments"][0]["slot_id"]
    run_dir = tmp_path / "run"

    assert runner.main(["compile-assignments", "--design", str(design_path), "--run-dir", str(run_dir)]) == 0
    assert runner.main(["prepare-slot", "--run-dir", str(run_dir), "--slot", slot_id]) == 0
    assert runner.main(
        [
            "record-launch",
            "--run-dir",
            str(run_dir),
            "--slot",
            slot_id,
            "--agent-id",
            "agent-dry-run",
        ]
    ) == 0
    report = tmp_path / "terminal.json"
    report.write_text(
        json.dumps(
            {
                "slot_id": slot_id,
                "status": "passed",
                "summary": "simulated terminal receipt",
                "deviations": [],
                "telemetry": runner.unavailable_telemetry(),
            }
        ),
        encoding="utf-8",
    )
    assert runner.main(
        [
            "ingest-terminal",
            "--run-dir",
            str(run_dir),
            "--slot",
            slot_id,
            "--report",
            str(report),
        ]
    ) == 0
    assert runner.main(["grade-slot", "--run-dir", str(run_dir), "--slot", slot_id]) == 0
    output = tmp_path / "codex-collaboration-summary.json"
    assert runner.main(["summarize", "--run-dir", str(run_dir), "--output", str(output)]) == 0

    summary = json.loads(output.read_text(encoding="utf-8"))
    assert summary["slots_terminal"] == 1
    assert summary["grades"] == 1
