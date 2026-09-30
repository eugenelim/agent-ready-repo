# STUB: AC-0001, AC-0002, AC-0003 — validate allocation and staged releases
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
import threading
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("plan_evolution_runner", ROOT / "runner.py")
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def test_staged_design_and_process_ceilings(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    summary = runner.validate_design(design)

    assert summary["hypotheses"] == tuple(f"H{i}" for i in range(1, 14))
    assert summary["allocations"] == design["allocations"]
    assert summary["study_ceiling"] == sum(design["allocations"].values())
    releases = design["fixed_releases"]
    reserve = design["reserve_release"]
    assert releases[0]["study_start"] == 1
    assert all(
        current["study_start"] == previous["study_end"] + 1
        for previous, current in zip(releases, releases[1:], strict=False)
    )
    assert reserve["study_start"] == releases[-1]["study_end"] + 1
    assert reserve["study_end"] == design["study_ceiling"]

    ledger = runner.InvocationLedger(
        tmp_path / "progress.jsonl",
        study_ceiling=design["study_ceiling"],
        fixed_releases=releases,
        reserve_release=reserve,
    )
    first_capacity = releases[0]["study_end"] - releases[0]["study_start"] + 1
    for slot in range(1, first_capacity + 1):
        assert ledger.reserve(f"w1-{slot}", wave="W1") == (slot, slot)
    with pytest.raises(runner.InvocationLimitError):
        ledger.reserve("unreleased-w2", wave="W2")
    assert not ledger.was_started("unreleased-w2")

    ledger.release_next("W2", gate_memo_digest="sha256:gate-w1")
    assert ledger.reserve("w2-1", wave="W2") == (
        releases[1]["study_start"],
        1,
    )

    study_ledger = runner.InvocationLedger(
        tmp_path / "study-progress.jsonl",
        study_ceiling=design["study_ceiling"],
        fixed_releases=releases,
        reserve_release=reserve,
    )
    for index, release in enumerate(releases):
        if index:
            study_ledger.release_next(
                release["wave"],
                gate_memo_digest=f"sha256:gate-{release['wave']}",
            )
        capacity = release["study_end"] - release["study_start"] + 1
        for slot in range(1, capacity + 1):
            study_ledger.reserve(
                f"{release['wave']}-{slot}",
                wave=release["wave"],
            )
    with pytest.raises(runner.InvocationLimitError):
        study_ledger.reserve("reserve-1", wave="W3")

    reserve_capacity = reserve["study_end"] - reserve["study_start"] + 1
    reserve_items = tuple(
        f"reserve-{slot}" for slot in range(1, reserve_capacity + 1)
    )
    study_ledger.release_reserve(
        reserve_items,
        gate_memo_digest="sha256:gate-w2-reserve",
    )
    for item in reserve_items:
        study_ledger.reserve(item, wave="W3")
    with pytest.raises(runner.InvocationLimitError):
        study_ledger.reserve("study-overflow", wave=releases[-1]["wave"])
    assert not study_ledger.was_started("study-overflow")


def test_progress_resume_ignores_only_torn_final_line(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    releases = design["fixed_releases"]
    reserve = design["reserve_release"]
    progress = tmp_path / "progress.jsonl"
    progress.write_text(
        json.dumps(
            {
                "event": "reserve",
                "item": "w1-1",
                "wave": "W1",
                "study_ordinal": 1,
                "wave_ordinal": 1,
                "timestamp": 1.0,
            }
        )
        + "\n"
        + '{"event":',
        encoding="utf-8",
    )

    ledger = runner.InvocationLedger(
        progress,
        study_ceiling=design["study_ceiling"],
        fixed_releases=releases,
        reserve_release=reserve,
    )

    assert ledger.was_started("w1-1")
    with pytest.raises(runner.InvocationLimitError):
        ledger.reserve("w1-1", wave="W1")
    assert ledger.reserve("w1-2", wave="W1") == (2, 2)
    assert b'{"event":\n' not in progress.read_bytes()


def test_progress_malformed_final_line_with_newline_fails_closed(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    progress = tmp_path / "progress.jsonl"
    progress.write_text('{"event":\n', encoding="utf-8")

    with pytest.raises(runner.SchemaError):
        runner.InvocationLedger(
            progress,
            study_ceiling=design["study_ceiling"],
            fixed_releases=design["fixed_releases"],
            reserve_release=design["reserve_release"],
        )


def test_progress_malformed_earlier_line_fails_closed(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    progress = tmp_path / "progress.jsonl"
    progress.write_text('{"event":\n{}\n', encoding="utf-8")

    with pytest.raises(runner.SchemaError):
        runner.InvocationLedger(
            progress,
            study_ceiling=design["study_ceiling"],
            fixed_releases=design["fixed_releases"],
            reserve_release=design["reserve_release"],
        )


def test_terminal_items_cannot_be_replaced(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    ledger = runner.InvocationLedger(
        tmp_path / "progress.jsonl",
        study_ceiling=design["study_ceiling"],
        fixed_releases=design["fixed_releases"],
        reserve_release=design["reserve_release"],
    )

    ledger.reserve("w1-1", wave="W1")
    ledger.terminal("w1-1", status="failed", note="model unavailable")

    with pytest.raises(runner.InvocationLimitError):
        ledger.reserve("w1-1", wave="W1")
    with pytest.raises(runner.InvocationLimitError):
        ledger.terminal("w1-1", status="done", note="second terminal")


def test_progress_schema_rejects_unknown_events_and_extra_fields(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    progress = tmp_path / "progress.jsonl"
    progress.write_text(
        json.dumps(
            {
                "event": "reserve",
                "item": "w1-1",
                "wave": "W1",
                "study_ordinal": 1,
                "wave_ordinal": 1,
                "timestamp": 1.0,
                "extra": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(runner.SchemaError):
        runner.InvocationLedger(
            progress,
            study_ceiling=design["study_ceiling"],
            fixed_releases=design["fixed_releases"],
            reserve_release=design["reserve_release"],
        )

    progress.write_text(
        json.dumps({"event": "mystery", "item": "x"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(runner.SchemaError):
        runner.InvocationLedger(
            progress,
            study_ceiling=design["study_ceiling"],
            fixed_releases=design["fixed_releases"],
            reserve_release=design["reserve_release"],
        )


def test_duplicate_fixed_and_reserve_releases_are_refused(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    ledger = runner.InvocationLedger(
        tmp_path / "progress.jsonl",
        study_ceiling=design["study_ceiling"],
        fixed_releases=design["fixed_releases"],
        reserve_release=design["reserve_release"],
    )

    ledger.release_next("W2", gate_memo_digest="sha256:gate-w1")
    with pytest.raises(runner.InvocationLimitError):
        ledger.release_next("W2", gate_memo_digest="sha256:gate-w1-again")
    ledger.release_next("W3", gate_memo_digest="sha256:gate-w2")
    ledger.release_reserve(("reserve-1",), gate_memo_digest="sha256:gate-reserve")
    with pytest.raises(runner.InvocationLimitError):
        ledger.release_reserve(("reserve-1",), gate_memo_digest="sha256:gate-again")


def test_loaded_progress_rejects_duplicate_or_out_of_order_releases(
    tmp_path: Path,
) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    progress = tmp_path / "progress.jsonl"
    release = {
        "event": "release-fixed",
        "item": "release-W2",
        "wave": "W2",
        "gate_memo_digest": "sha256:gate-w1",
        "timestamp": 1.0,
    }
    progress.write_text(
        json.dumps(release) + "\n" + json.dumps(release) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(runner.SchemaError):
        runner.InvocationLedger(
            progress,
            study_ceiling=design["study_ceiling"],
            fixed_releases=design["fixed_releases"],
            reserve_release=design["reserve_release"],
        )

    release["item"] = "release-W3"
    release["wave"] = "W3"
    progress.write_text(json.dumps(release) + "\n", encoding="utf-8")
    with pytest.raises(runner.SchemaError):
        runner.InvocationLedger(
            progress,
            study_ceiling=design["study_ceiling"],
            fixed_releases=design["fixed_releases"],
            reserve_release=design["reserve_release"],
        )


def test_strict_json_rejects_duplicate_nonfinite_oversized_and_unknown() -> None:
    with pytest.raises(runner.SchemaError):
        runner.parse_json_bytes(b'{"a": 1, "a": 2}')
    with pytest.raises(runner.SchemaError):
        runner.parse_json_bytes(b'{"a": NaN}')
    with pytest.raises(runner.SchemaError):
        runner.parse_json_bytes(b'{"a": "xxxxxxxxxx"}', max_bytes=8)

    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    design["unexpected"] = True
    with pytest.raises(runner.SchemaError):
        runner.validate_design(design)


def test_design_rejects_factor_imbalance_and_duplicate_tasks() -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    design["tasks"][0]["stratum"] = "multi-file refactor"
    with pytest.raises(runner.SchemaError):
        runner.validate_design(design)

    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    design["tasks"][1]["id"] = design["tasks"][0]["id"]
    with pytest.raises(runner.SchemaError):
        runner.validate_design(design)

    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    design["tasks"][0]["oracle_argv"] = ["manual", "historical-oracle-required"]
    with pytest.raises(runner.SchemaError):
        runner.validate_design(design)


def test_docs_print_oracle_excludes_when_node_dependencies_are_absent(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    task = design["tasks"][0]
    baseline = tmp_path / "baseline"
    reference = tmp_path / "reference"
    baseline.mkdir()
    reference.mkdir()

    oracle = runner.evaluate_admission_oracle(
        task,
        baseline_root=baseline,
        reference_root=reference,
    )

    assert oracle["baseline"] == "not-run"
    assert oracle["reference"] == "not-run"
    assert "Node/Playwright dependencies absent" in oracle["reason"]


def test_work_loop_argless_resume_oracle_discriminates_structurally(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    task = design["tasks"][1]
    baseline_skill = tmp_path / "baseline" / ".agents" / "skills" / "work-loop"
    reference_skill = tmp_path / "reference" / ".agents" / "skills" / "work-loop"
    baseline_skill.mkdir(parents=True)
    reference_skill.mkdir(parents=True)
    (baseline_skill / "SKILL.md").write_text(
        'description: Use this skill for non-trivial work.\n'
        'The active spec path tells you which spec to work on: '
        'the first path in `["<slug>".work].active`.\n',
        encoding="utf-8",
    )
    (reference_skill / "SKILL.md").write_text(
        'description: resume continue keep going pick up where I left off '
        "let's get going desk-research-project-status\n"
        "Collect every path. Exactly one. No active spec found. More than one "
        "ask the user to pick. If absent PLAN begins immediately.\n",
        encoding="utf-8",
    )

    oracle = runner.evaluate_admission_oracle(
        task,
        baseline_root=tmp_path / "baseline",
        reference_root=tmp_path / "reference",
    )

    assert oracle["baseline"] == "fail"
    assert oracle["reference"] == "pass"
    assert oracle["reason"] == "reference passes and baseline fails"


def test_dry_run_invocation_is_redacted_and_never_spawns(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    prompt = candidate / "prompt.txt"
    prompt.write_text("Build only the assigned slice.", encoding="utf-8")

    dry_run = runner.build_dry_run_invocation(
        item="w1-1",
        model=design["models"]["standard"],
        candidate_root=candidate,
        prompt_file=prompt,
        policy=design["dry_run_policy"],
        limits=design["role_limits"]["builder"],
    )

    assert dry_run["spawned"] is False
    assert dry_run["argv"][:2] == ["codex", "exec"]
    assert "--approve-for-me" not in dry_run["argv"]
    assert "--dangerously-bypass-approvals-and-sandbox" not in dry_run["argv"]
    assert _feature_disabled(dry_run["argv"], "apps")
    assert _feature_disabled(dry_run["argv"], "plugins")
    assert _feature_disabled(dry_run["argv"], "multi_agent")
    assert dry_run["network"] is False
    assert dry_run["environment"] == ("TMPDIR", "PYTHONDONTWRITEBYTECODE")


def _feature_disabled(argv: list[str], feature: str) -> bool:
    return any(
        left == "--disable" and right == feature
        for left, right in zip(argv, argv[1:], strict=False)
    )


def test_calibration_invocation_uses_controller_stdin_prompt_and_fails_closed(
    tmp_path: Path,
) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    slot = tmp_path / "slot"
    roots = {
        "baseline": slot / "baseline",
        "candidate": slot / "candidate",
        "controller": slot / "controller",
        "credential": slot / "credential-sentinel",
        "hidden_oracle": slot / "hidden-oracle",
        "output": slot / "output",
        "prompt": slot / "prompt",
        "reference": slot / "reference",
        "sibling": slot / "sibling",
    }
    roots["candidate"].mkdir(parents=True)
    roots["prompt"].mkdir(parents=True)
    prompt = roots["prompt"] / "prompt.txt"
    prompt.write_text("Calibration only.", encoding="utf-8")

    invocation = runner.build_calibration_invocation(
        item="calibration-builder-standard",
        model=design["models"]["standard"],
        candidate_root=roots["candidate"],
        prompt_file=prompt,
        policy=design["dry_run_policy"],
        limits=design["role_limits"]["builder"],
    )
    canaries = runner.evaluate_calibration_canaries(
        roots=roots,
        candidate_root=roots["candidate"],
        prompt_file=prompt,
        invocation=invocation,
    )

    assert invocation["stdin_prompt"] is True
    assert str(prompt) not in invocation["argv"]
    assert invocation["argv"][-1] == "-"
    assert canaries["controller_preflight_pass"] is True
    assert canaries["worker_proof"] == "unavailable"
    assert "candidate-only worker read access" in canaries["unproven_controls"]
    assert set(canaries["root_nonce_digests"]) == set(roots)


def test_calibration_runner_spends_only_the_eight_calibration_slots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design = ROOT / "fixtures" / "valid-design.json"
    research = tmp_path / "research"
    research.mkdir()
    prior_index = research / "evidence-index.json"
    prior_index.write_text(
        json.dumps({"schema_version": 1, "plan_task": "T2"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "RESEARCH_ROOT", research)
    original_load_json = runner.load_json

    def load_json(path: Path, *, max_bytes: int = runner.MAX_JSON_BYTES) -> object:
        if path == prior_index:
            return json.loads(path.read_text(encoding="utf-8"))
        return original_load_json(path, max_bytes=max_bytes)

    monkeypatch.setattr(runner, "load_json", load_json)

    def listener(_expected: str) -> tuple[int, dict[str, object], threading.Thread]:
        thread = threading.Thread(target=lambda: None)
        thread.start()
        return 1, {"connected": False, "matched": False}, thread

    monkeypatch.setattr(runner, "_start_local_listener", listener)

    def fake_codex(
        argv: list[str],
        *,
        prompt: str,
        cwd: Path,
    ) -> runner.CodexProcessResult:
        slot_root = cwd.parent
        canary = {
            "reads": {},
            "writes": {},
            "env": {
                "HOME": {"present": True, "synthetic_secret": False},
                "CODEX_HOME": {"present": False, "synthetic_secret": False},
                "PATH": {"present": True, "synthetic_secret": False},
                "PLAN_EVOLUTION_SYNTHETIC_SECRET": {
                    "present": False,
                    "synthetic_secret": True,
                },
                "PLAN_EVOLUTION_CONTROLLER_ONLY": {
                    "present": False,
                    "synthetic_secret": True,
                },
            },
            "egress": {"ok": False, "error": "ConnectionRefusedError"},
        }
        for name in runner.SYNTHETIC_ROOT_NAMES:
            allowed = name == "candidate"
            canary["reads"][name] = {"ok": allowed}
            canary["writes"][name] = {"ok": allowed}
        (slot_root / "candidate" / "canary-results.json").write_text(
            json.dumps(canary),
            encoding="utf-8",
        )
        return runner.CodexProcessResult(
            returncode=0,
            stdout=b'{"type":"turn.complete","usage":{"input_tokens":1,"output_tokens":1}}\n',
            stderr=b"",
            duration_seconds=0.1,
            timed_out=False,
        )

    monkeypatch.setattr(runner, "run_codex_process", fake_codex)

    run_dir = Path("/private/tmp") / f"plan-evolution-t3-test-{uuid.uuid4().hex}"
    result = runner.calibrate(design, run_dir)

    assert result["status"] == "complete"
    assert result["calibration_slots"] == 8
    assert result["terminal_slots"] == 8
    assert result["instrument_loss_rate"] == 1.0
    assert result["inference_launch_permitted"] is False
    assert result["model_processes_started"] == 8
    stored = json.loads((research / "results.json").read_text(encoding="utf-8"))
    assert [record["hypothesis_observation"] for record in stored["records"]] == [
        False
    ] * 8
    index = json.loads(prior_index.read_text(encoding="utf-8"))
    assert index["admission_evidence"] == {"schema_version": 1, "plan_task": "T2"}
    assert index["calibration"]["terminal_slots"] == 8
    assert index["calibration"]["records"][0]["failure_class"] in {
        "authority-unobservable",
        "local-listener-unavailable",
    }


def test_codex_child_environment_is_minimal_and_synthetic_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setenv("HOME", "/example/home")
    monkeypatch.setenv("OPENAI_API_KEY", "real-secret-never-forward")
    monkeypatch.setenv("CODEX_HOME", "/example/codex")

    env = runner.safe_codex_env()

    assert env is not None
    assert env["PATH"] == "/usr/bin:/bin"
    assert "OPENAI_API_KEY" not in env
    assert "CODEX_HOME" not in env
    assert "HOME" not in env
    assert set(env) <= {"PATH", "TMPDIR", "PYTHONDONTWRITEBYTECODE"}


def test_listener_setup_failure_stops_before_script_or_codex(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design = ROOT / "fixtures" / "valid-design.json"
    research = tmp_path / "research"
    research.mkdir()
    (research / "evidence-index.json").write_text(
        json.dumps({"schema_version": 1, "plan_task": "T2"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "RESEARCH_ROOT", research)

    def load_json(path: Path, *, max_bytes: int = runner.MAX_JSON_BYTES) -> object:
        if path == research / "evidence-index.json":
            return json.loads(path.read_text(encoding="utf-8"))
        return runner.parse_json_bytes(path.read_bytes(), max_bytes=max_bytes)

    monkeypatch.setattr(runner, "load_json", load_json)

    def listener(_expected: str) -> tuple[int, dict[str, object], threading.Thread]:
        thread = threading.Thread(target=lambda: None)
        thread.start()
        return 0, {"connected": False, "matched": False, "setup_error": "PermissionError"}, thread

    monkeypatch.setattr(runner, "_start_local_listener", listener)

    def forbidden_codex(*_args: object, **_kwargs: object) -> runner.CodexProcessResult:
        raise AssertionError("Codex must not start when listener setup fails")

    monkeypatch.setattr(runner, "run_codex_process", forbidden_codex)

    run_dir = Path("/private/tmp") / f"plan-evolution-t3-listener-{uuid.uuid4().hex}"
    result = runner.calibrate(design, run_dir)
    terminal = json.loads(
        (
            run_dir
            / "calibration"
            / "01-calibration-planner-standard"
            / "terminal.json"
        ).read_text(encoding="utf-8")
    )

    assert result["model_processes_started"] == 0
    assert terminal["failure_class"] == "local-listener-unavailable"
    assert terminal["canaries"]["live_script_digest"] == "not-written-listener-unavailable"
    assert not (
        run_dir
        / "calibration"
        / "01-calibration-planner-standard"
        / "candidate"
        / "run_calibration_canaries.py"
    ).exists()


def test_codex_capture_kills_child_at_output_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runner, "MAX_CODEX_CAPTURE_BYTES", 128)
    monkeypatch.setattr(runner, "CALIBRATION_TIMEOUT_SECONDS", 30)

    result = runner.run_codex_process(
        [
            "python3",
            "-c",
            "import sys, time; sys.stdout.write('x' * 1000000); sys.stdout.flush(); time.sleep(10)",
        ],
        prompt="",
        cwd=tmp_path,
    )

    assert result.capture_exceeded is True
    assert len(result.stdout) <= 128


def test_existing_calibration_results_are_strictly_validated() -> None:
    bad = {
        "schema_version": 1,
        "plan_task": "T3",
        "status": "complete",
        "allocation": "instrument_calibration",
        "calibration_slots": 8,
        "replacement_reservations": 0,
        "terminal_slots": 1,
        "failed_slots": 1,
        "instrument_loss_rate": 1.0,
        "inference_launch_permitted": False,
        "inferential_processes_started": 0,
        "model_processes_started": 0,
        "new_model_processes_started": 0,
        "progress_digest": "sha256:progress",
        "records": [
            {
                "schema_version": 1,
                "item": "calibration-planner-standard",
                "allocation": "instrument_calibration",
                "phase": "planner_or_probe",
                "role": "planner_or_probe",
                "study_ordinal": 1,
                "wave_ordinal": 1,
                "hypothesis_observation": False,
                "requested_model": "gpt-5.6-luna",
                "model_class": "standard",
                "resolved_model": "unavailable",
                "status": "failed",
                "failure_class": "not-a-real-class",
                "started_at": 1.0,
                "finished_at": 2.0,
                "exit_status": "not-started",
                "session_id": "unavailable",
                "tokens": {
                    "input": "unavailable",
                    "cached_input": "unavailable",
                    "output": "unavailable",
                    "reasoning": "unavailable",
                },
                "output_digest": "sha256:output",
                "snapshot": {
                    "before_tool_boundary": "sha256:a",
                    "after_prompt_boundary": "sha256:b",
                    "after_controller_canary_boundary": "sha256:c",
                    "after_worker_boundary": "unavailable",
                    "after_hidden_grade_boundary": "unavailable",
                },
                "argv_policy": {},
                "canaries": {},
                "live_canary": "not-started",
                "terminal_reason": "bad stale data",
            }
        ],
    }

    with pytest.raises(runner.SchemaError):
        runner.validate_calibration_results(bad)


def test_existing_t3_results_are_bound_to_originating_progress_ledger(
) -> None:
    with pytest.raises(runner.InvocationLimitError):
        runner._load_existing_calibration_results(
            Path("/private/tmp") / f"plan-evolution-fresh-{uuid.uuid4().hex}"
        )


def test_worker_authored_canary_cannot_prove_authority_widening(tmp_path: Path) -> None:
    roots = {name: tmp_path / name for name in runner.SYNTHETIC_ROOT_NAMES}
    candidate = roots["candidate"]
    candidate.mkdir(parents=True)
    canary = {
        "reads": {name: {"ok": True} for name in runner.SYNTHETIC_ROOT_NAMES},
        "writes": {name: {"ok": True} for name in runner.SYNTHETIC_ROOT_NAMES},
        "env": {
            "PLAN_EVOLUTION_SYNTHETIC_SECRET": {
                "present": False,
                "synthetic_secret": True,
            },
            "PLAN_EVOLUTION_CONTROLLER_ONLY": {
                "present": False,
                "synthetic_secret": True,
            },
        },
        "egress": {"ok": True},
    }
    (candidate / "canary-results.json").write_text(json.dumps(canary), encoding="utf-8")

    status, failure, *_ = runner.classify_live_canary(
        candidate_root=candidate,
        roots=roots,
        process=runner.CodexProcessResult(
            returncode=0,
            stdout=b'{"type":"turn.complete"}\n',
            stderr=b"",
            duration_seconds=0.1,
            timed_out=False,
        ),
        listener_observed={"connected": False, "matched": False},
    )

    assert status == "failed"
    assert failure == "authority-unobservable"


def test_safe_sink_rejects_symlink_target(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(target)

    with pytest.raises(runner.UnsafeContentError):
        runner.write_json(link, {"status": "blocked"})


def test_broken_pipe_preserves_child_exit_status(tmp_path: Path) -> None:
    result = runner.run_codex_process(
        ["python3", "-c", "import sys; sys.exit(7)"],
        prompt="x" * 1_000_000,
        cwd=tmp_path,
    )

    assert result.returncode == 7
    assert result.returncode != "spawn-error"


def test_calibration_results_require_contiguous_ordinals() -> None:
    source = (
        runner.REPO_ROOT
        / "docs"
        / "product"
        / "research"
        / "plan-evolution-experiments"
        / "results.json"
    )
    data = json.loads(source.read_text(encoding="utf-8"))
    data = runner._calibration_payload(data)
    data["records"][1]["study_ordinal"] = 99

    with pytest.raises(runner.SchemaError):
        runner.validate_calibration_results(data)


def test_calibrate_validates_merged_result_before_result_sinks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design = ROOT / "fixtures" / "valid-design.json"
    research = tmp_path / "research"
    research.mkdir()
    (research / "evidence-index.json").write_text(
        json.dumps({"schema_version": 1, "plan_task": "T2"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "RESEARCH_ROOT", research)

    def load_json(path: Path, *, max_bytes: int = runner.MAX_JSON_BYTES) -> object:
        if path == research / "evidence-index.json":
            return json.loads(path.read_text(encoding="utf-8"))
        return runner.parse_json_bytes(path.read_bytes(), max_bytes=max_bytes)

    monkeypatch.setattr(runner, "load_json", load_json)

    def listener(_expected: str) -> tuple[int, dict[str, object], threading.Thread]:
        thread = threading.Thread(target=lambda: None)
        thread.start()
        return 0, {"connected": False, "matched": False, "setup_error": "PermissionError"}, thread

    monkeypatch.setattr(runner, "_start_local_listener", listener)

    def validate(_results: dict[str, object]) -> list[dict[str, object]]:
        raise runner.SchemaError("merged result refused")

    monkeypatch.setattr(runner, "validate_calibration_results", validate)
    written: list[Path] = []
    original_write_json = runner.write_json

    def write_json(path: Path, payload: dict[str, object]) -> None:
        written.append(path)
        original_write_json(path, payload)

    monkeypatch.setattr(runner, "write_json", write_json)
    run_dir = Path("/private/tmp") / f"plan-evolution-merged-refusal-{uuid.uuid4().hex}"

    with pytest.raises(runner.SchemaError):
        runner.calibrate(design, run_dir)

    assert not any(path.name in {"calibration-results.json", "results.json"} for path in written)
    assert not any(path.name == "evidence-index.json" for path in written)


def test_preseeded_symlink_subroot_aborts_before_progress_and_outside_write(
    tmp_path: Path,
) -> None:
    run_dir = Path("/private/tmp") / f"plan-evolution-symlink-root-{uuid.uuid4().hex}"
    outside = tmp_path / "outside"
    outside.mkdir()
    runner.prepare_private_directory(run_dir)
    runner.prepare_private_directory(run_dir / "calibration", root=run_dir)
    slot = run_dir / "calibration" / "01-calibration-planner-standard"
    runner.prepare_private_directory(slot, root=run_dir)
    (slot / "prompt").symlink_to(outside)

    with pytest.raises(runner.UnsafeContentError):
        runner.prepare_calibration_slot_roots(run_dir, 1, "calibration-planner-standard")

    assert not (run_dir / "calibration-progress.jsonl").exists()
    assert list(outside.iterdir()) == []


def test_preseeded_unsafe_mode_subroot_aborts_before_progress() -> None:
    run_dir = Path("/private/tmp") / f"plan-evolution-unsafe-mode-{uuid.uuid4().hex}"
    runner.prepare_private_directory(run_dir)
    runner.prepare_private_directory(run_dir / "calibration", root=run_dir)
    slot = run_dir / "calibration" / "01-calibration-planner-standard"
    runner.prepare_private_directory(slot, root=run_dir)
    candidate = slot / "candidate"
    candidate.mkdir(mode=0o755)

    with pytest.raises(runner.UnsafeContentError):
        runner.prepare_calibration_slot_roots(run_dir, 1, "calibration-planner-standard")

    assert not (run_dir / "calibration-progress.jsonl").exists()


def test_reserved_without_terminal_is_closed_before_later_reservations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    research = tmp_path / "research"
    research.mkdir()
    (research / "evidence-index.json").write_text(
        json.dumps({"schema_version": 1, "plan_task": "T2"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "RESEARCH_ROOT", research)

    def load_json(path: Path, *, max_bytes: int = runner.MAX_JSON_BYTES) -> object:
        if path == research / "evidence-index.json":
            return json.loads(path.read_text(encoding="utf-8"))
        return runner.parse_json_bytes(path.read_bytes(), max_bytes=max_bytes)

    monkeypatch.setattr(runner, "load_json", load_json)

    def listener(_expected: str) -> tuple[int, dict[str, object], threading.Thread]:
        thread = threading.Thread(target=lambda: None)
        thread.start()
        return 0, {"connected": False, "matched": False, "setup_error": "PermissionError"}, thread

    monkeypatch.setattr(runner, "_start_local_listener", listener)
    run_dir = Path("/private/tmp") / f"plan-evolution-crash-resume-{uuid.uuid4().hex}"
    run_dir = runner.prepare_calibration_run_root(run_dir)
    ledger = runner.InvocationLedger(
        run_dir / "calibration-progress.jsonl",
        study_ceiling=design["study_ceiling"],
        fixed_releases=design["fixed_releases"],
        reserve_release=design["reserve_release"],
    )
    assert ledger.reserve("calibration-planner-standard", wave="W1") == (1, 1)

    result = runner.calibrate(ROOT / "fixtures" / "valid-design.json", run_dir)
    lines = [
        json.loads(line)
        for line in (run_dir / "calibration-progress.jsonl").read_text().splitlines()
    ]

    assert result["terminal_slots"] == 8
    assert result["model_processes_started"] == 1
    assert lines[1]["event"] == "terminal"
    assert lines[1]["item"] == "calibration-planner-standard"
    assert lines[1]["note"] == "crash-resume-unknown-started"
    assert lines[2]["event"] == "reserve"
    assert lines[2]["item"] == "calibration-builder-standard"
    terminal_path = (
        run_dir
        / "calibration"
        / "01-calibration-planner-standard"
        / "terminal.json"
    )
    terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
    assert terminal["failure_class"] == "crash-resume-unknown-started"
    assert terminal["exit_status"] == "unknown-started"
    assert terminal["session_id"] == "unavailable"
    assert set(terminal["tokens"].values()) == {"unavailable"}


def test_terminal_replay_reads_private_tmp_with_safe_disposable_loader(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    research = tmp_path / "research"
    research.mkdir()
    (research / "evidence-index.json").write_text(
        json.dumps({"schema_version": 1, "plan_task": "T2"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "RESEARCH_ROOT", research)
    original_load_json = runner.load_json

    def load_json(path: Path, *, max_bytes: int = runner.MAX_JSON_BYTES) -> object:
        if path.name == "terminal.json":
            raise AssertionError("terminal replay must not use repository load_json")
        if path == research / "evidence-index.json":
            return json.loads(path.read_text(encoding="utf-8"))
        return original_load_json(path, max_bytes=max_bytes)

    monkeypatch.setattr(runner, "load_json", load_json)

    def listener(_expected: str) -> tuple[int, dict[str, object], threading.Thread]:
        thread = threading.Thread(target=lambda: None)
        thread.start()
        return 0, {"connected": False, "matched": False, "setup_error": "PermissionError"}, thread

    monkeypatch.setattr(runner, "_start_local_listener", listener)
    run_dir = runner.prepare_calibration_run_root(
        Path("/private/tmp") / f"plan-evolution-terminal-replay-{uuid.uuid4().hex}"
    )
    ledger = runner.InvocationLedger(
        run_dir / "calibration-progress.jsonl",
        study_ceiling=design["study_ceiling"],
        fixed_releases=design["fixed_releases"],
        reserve_release=design["reserve_release"],
    )
    assert ledger.reserve("calibration-planner-standard", wave="W1") == (1, 1)
    first = runner.close_reserved_calibration_crash(
        ledger=ledger,
        run_dir=run_dir,
        slot_index=1,
        item="calibration-planner-standard",
        role="planner_or_probe",
        model_class="standard",
        replacement_of=None,
    )

    result = runner.calibrate(ROOT / "fixtures" / "valid-design.json", run_dir)

    assert result["terminal_slots"] == 8
    assert result["model_processes_started"] == 1
    stored = json.loads((research / "results.json").read_text(encoding="utf-8"))
    assert stored["records"][0] == first


def test_terminal_replay_refuses_record_that_mismatches_reservation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    research = tmp_path / "research"
    research.mkdir()
    (research / "evidence-index.json").write_text(
        json.dumps({"schema_version": 1, "plan_task": "T2"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "RESEARCH_ROOT", research)

    def load_json(path: Path, *, max_bytes: int = runner.MAX_JSON_BYTES) -> object:
        if path == research / "evidence-index.json":
            return json.loads(path.read_text(encoding="utf-8"))
        return runner.parse_json_bytes(path.read_bytes(), max_bytes=max_bytes)

    monkeypatch.setattr(runner, "load_json", load_json)

    def listener(_expected: str) -> tuple[int, dict[str, object], threading.Thread]:
        thread = threading.Thread(target=lambda: None)
        thread.start()
        return 0, {"connected": False, "matched": False, "setup_error": "PermissionError"}, thread

    monkeypatch.setattr(runner, "_start_local_listener", listener)
    run_dir = runner.prepare_calibration_run_root(
        Path("/private/tmp") / f"plan-evolution-terminal-bind-{uuid.uuid4().hex}"
    )
    ledger = runner.InvocationLedger(
        run_dir / "calibration-progress.jsonl",
        study_ceiling=design["study_ceiling"],
        fixed_releases=design["fixed_releases"],
        reserve_release=design["reserve_release"],
    )
    assert ledger.reserve("calibration-planner-standard", wave="W1") == (1, 1)
    terminal = runner.close_reserved_calibration_crash(
        ledger=ledger,
        run_dir=run_dir,
        slot_index=1,
        item="calibration-planner-standard",
        role="planner_or_probe",
        model_class="standard",
        replacement_of=None,
    )
    terminal["item"] = "calibration-builder-standard"
    (
        run_dir
        / "calibration"
        / "01-calibration-planner-standard"
        / "terminal.json"
    ).write_text(json.dumps(terminal), encoding="utf-8")

    with pytest.raises(runner.SchemaError, match="terminal replay item"):
        runner.calibrate(ROOT / "fixtures" / "valid-design.json", run_dir)

    lines = (run_dir / "calibration-progress.jsonl").read_text().splitlines()
    assert len(lines) == 2


def test_legacy_crash_resume_not_started_is_rejected_before_reuse() -> None:
    source = (
        runner.REPO_ROOT
        / "docs"
        / "product"
        / "research"
        / "plan-evolution-experiments"
        / "results.json"
    )
    data = json.loads(source.read_text(encoding="utf-8"))
    data = runner._calibration_payload(data)
    data["records"][0]["failure_class"] = "crash-resume-infrastructure-failure"
    data["records"][0]["exit_status"] = "not-started"

    with pytest.raises(runner.SchemaError, match="crash-resume records"):
        runner.validate_calibration_results(data)


def test_crash_resume_unknown_started_counts_and_is_non_replaceable() -> None:
    assert "crash-resume-unknown-started" in runner.NON_REPLACEABLE_FAILURE_CLASSES

    source = (
        runner.REPO_ROOT
        / "docs"
        / "product"
        / "research"
        / "plan-evolution-experiments"
        / "results.json"
    )
    data = json.loads(source.read_text(encoding="utf-8"))
    data = runner._calibration_payload(data)
    data["records"][0]["failure_class"] = "crash-resume-unknown-started"
    data["records"][0]["exit_status"] = "unknown-started"
    data["records"][0]["live_canary"] = {
        "event_schema": "unavailable-after-crash",
        "output_digest": "sha256:unknown-started",
        "listener_observed": "unavailable-after-crash",
        "canary_result": "unavailable-after-crash",
        "tool_roster_proof": "unavailable-after-crash",
        "approval_policy_proof": "unavailable-after-crash",
    }
    data["model_processes_started"] += 1

    runner.validate_calibration_results(data)


def test_w1_gate_blocks_w2_without_reserving_or_starting_processes() -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    raw_results = json.loads(
        (
            runner.REPO_ROOT
            / "docs/product/research/plan-evolution-experiments/results.json"
        ).read_text(encoding="utf-8")
    )
    calibration = runner._calibration_payload(raw_results)
    raw_index = json.loads(
        (
            runner.REPO_ROOT
            / "docs/product/research/plan-evolution-experiments/evidence-index.json"
        ).read_text(encoding="utf-8")
    )
    admission = runner._admission_payload(raw_index)

    memo = runner.build_w1_gate_memo(
        design=design,
        design_digest=runner.digest_text("design"),
        calibration=calibration,
        admission=admission,
        calibration_digest=runner.digest_text("calibration"),
        evidence_index_digest=runner.digest_text("index"),
    )

    assert memo["gate_decision"] == "W2-unavailable"
    assert memo["release_w2"] is False
    assert memo["process_accounting"] == {
        "t4_model_processes_started": 0,
        "t4_inferential_processes_started": 0,
        "t4_ordinals_reserved": 0,
    }
    assert memo["w1_core"]["reservation_policy"] == "blocked-without-reservation"
    assert memo["w1_core"]["would_be_inferential_reservations"] == 64
    assert memo["w1_core"]["would_be_inferential_ordinals"] == [17, 80]
    assert memo["observed"]["instrument_loss_rate"] == 1.0
    assert memo["observed"]["admitted_tasks"] == 8
    assert memo["no_inferential_success_claim"] is True
    assert memo["w2"]["availability"] == "unavailable"
    assert "telemetry/instrument loss exceeds 5%" in memo["stop_reasons"]
    assert "admitted task coverage is below 12" in memo["stop_reasons"]


def test_w1_gate_schema_refuses_favorable_rewrites() -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    raw_results = json.loads(
        (
            runner.REPO_ROOT
            / "docs/product/research/plan-evolution-experiments/results.json"
        ).read_text(encoding="utf-8")
    )
    calibration = runner._calibration_payload(raw_results)
    raw_index = json.loads(
        (
            runner.REPO_ROOT
            / "docs/product/research/plan-evolution-experiments/evidence-index.json"
        ).read_text(encoding="utf-8")
    )
    admission = runner._admission_payload(raw_index)
    memo = runner.build_w1_gate_memo(
        design=design,
        design_digest=runner.digest_text("design"),
        calibration=calibration,
        admission=admission,
        calibration_digest=runner.digest_text("calibration"),
        evidence_index_digest=runner.digest_text("index"),
    )

    bad = json.loads(json.dumps(memo))
    bad["release_w2"] = True
    with pytest.raises(runner.SchemaError):
        runner.validate_w1_gate_memo(bad)

    bad = json.loads(json.dumps(memo))
    bad["process_accounting"]["t4_model_processes_started"] = 1
    with pytest.raises(runner.SchemaError):
        runner.validate_w1_gate_memo(bad)

    bad = json.loads(json.dumps(memo))
    bad["no_inferential_success_claim"] = False
    with pytest.raises(runner.SchemaError):
        runner.validate_w1_gate_memo(bad)


def test_gate_w1_is_idempotent_and_preserves_prior_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = tmp_path / "research"
    research.mkdir()
    source = runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments"
    (research / "results.json").write_text(
        (source / "results.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (research / "evidence-index.json").write_text(
        (source / "evidence-index.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    original_wave = (source / "wave-1.json").read_text(encoding="utf-8")
    (research / "wave-1.json").write_text(original_wave, encoding="utf-8")
    monkeypatch.setattr(runner, "RESEARCH_ROOT", research)
    original_load_json = runner.load_json

    def load_json(path: Path, *, max_bytes: int = runner.MAX_JSON_BYTES) -> object:
        if path.parent == research:
            return runner.parse_json_bytes(path.read_bytes(), max_bytes=max_bytes)
        return original_load_json(path, max_bytes=max_bytes)

    monkeypatch.setattr(runner, "load_json", load_json)

    first = runner.gate_w1(ROOT / "fixtures" / "valid-design.json")
    first_results = json.loads((research / "results.json").read_text(encoding="utf-8"))
    first_index = json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))
    second = runner.gate_w1(ROOT / "fixtures" / "valid-design.json")
    second_results = json.loads((research / "results.json").read_text(encoding="utf-8"))
    second_index = json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))

    assert first == second
    assert first["t4_model_processes_started"] == 0
    assert first["t4_ordinals_reserved"] == 0
    assert first_results == second_results
    assert first_index == second_index
    assert first_results["calibration"]["plan_task"] == "T3"
    assert first_index["admission_evidence"]["plan_task"] == "T2"
    assert first_index["calibration"]["allocation"] == "instrument_calibration"
    assert (research / "w1-gate-memo.json").exists()
    assert (research / "wave-1.json").read_text(encoding="utf-8") == original_wave
    assert "gate_decision" not in json.loads(original_wave)


def test_gate_w1_binds_design_digest_to_non_default_design_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = tmp_path / "research"
    research.mkdir()
    source = runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments"
    for name in ("results.json", "evidence-index.json"):
        (research / name).write_text(
            (source / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    design_path = ROOT / "fixtures" / f"alternate-design-{uuid.uuid4().hex}.json"
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    runner.write_json(design_path, design)
    (research / "wave-1.json").write_text(
        design_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "RESEARCH_ROOT", research)
    original_load_json = runner.load_json

    def load_json(path: Path, *, max_bytes: int = runner.MAX_JSON_BYTES) -> object:
        if path.parent == research:
            return runner.parse_json_bytes(path.read_bytes(), max_bytes=max_bytes)
        return original_load_json(path, max_bytes=max_bytes)

    monkeypatch.setattr(runner, "load_json", load_json)

    try:
        result = runner.gate_w1(design_path)
        memo = json.loads((research / "w1-gate-memo.json").read_text(encoding="utf-8"))

        assert result["gate_decision"] == "W2-unavailable"
        assert memo["inputs"]["design_digest"] == runner.digest_file(design_path)
        assert memo["inputs"]["design_digest"] != runner.digest_file(
            ROOT / "fixtures" / "valid-design.json"
        )
    finally:
        design_path.unlink(missing_ok=True)


def test_w1_gate_rejects_admission_summary_drift() -> None:
    raw_index = json.loads(
        (
            runner.REPO_ROOT
            / "docs/product/research/plan-evolution-experiments/evidence-index.json"
        ).read_text(encoding="utf-8")
    )
    admission = runner._admission_payload(raw_index)

    bad_counts = json.loads(json.dumps(admission))
    bad_counts["status_counts"]["admitted"] += 1
    with pytest.raises(runner.SchemaError, match="status counts drift"):
        runner._validate_admission_summary(bad_counts)

    bad_branch = json.loads(json.dumps(admission))
    bad_branch["inference_branch"] = "inferential"
    with pytest.raises(runner.SchemaError, match="inference branch drifts"):
        runner._validate_admission_summary(bad_branch)

    bad_coverage = json.loads(json.dumps(admission))
    bad_coverage["coverage_by_stratum"]["documentation/governance"] += 1
    with pytest.raises(runner.SchemaError, match="coverage by stratum drifts"):
        runner._validate_admission_summary(bad_coverage)


def _patch_research_root(
    monkeypatch: pytest.MonkeyPatch,
    research: Path,
) -> None:
    monkeypatch.setattr(runner, "RESEARCH_ROOT", research)
    original_load_json = runner.load_json

    def load_json(path: Path, *, max_bytes: int = runner.MAX_JSON_BYTES) -> object:
        if path.parent == research:
            return runner.parse_json_bytes(path.read_bytes(), max_bytes=max_bytes)
        return original_load_json(path, max_bytes=max_bytes)

    monkeypatch.setattr(runner, "load_json", load_json)


def _copy_gate_research_root(tmp_path: Path) -> Path:
    research = tmp_path / "research"
    research.mkdir()
    source = runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments"
    for name in (
        "results.json",
        "evidence-index.json",
        "wave-1.json",
        "w1-gate-memo.json",
        "w2-gate-memo.json",
    ):
        if not (source / name).exists():
            continue
        (research / name).write_text(
            (source / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    return research


def test_w2_gate_stopped_branch_releases_no_work() -> None:
    design_path = (
        runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments/wave-1.json"
    )
    design = runner.load_design(design_path)
    design_digest = runner.digest_file(design_path)
    research = runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments"
    results = runner._t4_results_payload(
        json.loads((research / "results.json").read_text(encoding="utf-8"))
    )
    index = runner._t4_index_payload(
        json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))
    )
    chain = runner.validate_w1_chain(
        design_digest=design_digest,
        wave_path=research / "wave-1.json",
        memo_path=research / "w1-gate-memo.json",
        t4_results=results,
        t4_index=index,
    )

    memo = runner.build_w2_gate_memo(
        design=design,
        chain_digests=chain,
        w1_memo=results["w1_gate"],
    )

    assert memo["gate_decision"] == "stopped-before-core"
    assert memo["release_w3_fixed"] is False
    assert memo["reserve_item_ids"] == []
    assert memo["w2_core"]["unavailable_study_ordinals"] == [81, 160]
    assert "released_study_ordinals" not in memo["w2_core"]
    assert memo["w3_fixed"]["unavailable_study_ordinals"] == [161, 216]
    assert memo["adaptive_reserve"]["unavailable_study_ordinals"] == [217, 240]
    assert memo["process_accounting"] == {
        "t5_model_processes_started": 0,
        "t5_inferential_processes_started": 0,
        "t5_ordinals_reserved": 0,
    }
    assert set(memo["analysis_inputs"]) == set(runner.CORE_DIRECT_HYPOTHESES)
    assert all(entry["status"] == "unavailable" for entry in memo["analysis_inputs"].values())


def test_gate_w2_is_idempotent_and_preserves_w1_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = _copy_gate_research_root(tmp_path)
    original_wave = (research / "wave-1.json").read_text(encoding="utf-8")
    original_w1_memo = (research / "w1-gate-memo.json").read_text(encoding="utf-8")
    _patch_research_root(monkeypatch, research)

    design_path = (
        runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments/wave-1.json"
    )
    first = runner.gate_w2(design_path)
    first_results = json.loads((research / "results.json").read_text(encoding="utf-8"))
    first_index = json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))
    second = runner.gate_w2(design_path)
    second_results = json.loads((research / "results.json").read_text(encoding="utf-8"))
    second_index = json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))

    assert first == second
    assert first["gate_decision"] == "stopped-before-core"
    assert first["t5_model_processes_started"] == 0
    assert first["t5_ordinals_reserved"] == 0
    assert first_results == second_results
    assert first_index == second_index
    assert first_results["t4_results"]["plan_task"] == "T4"
    assert first_index["t4_evidence_index"]["plan_task"] == "T4"
    assert first_index["w2_gate"]["reserve_item_ids"] == []
    assert (research / "wave-1.json").read_text(encoding="utf-8") == original_wave
    assert (research / "w1-gate-memo.json").read_text(encoding="utf-8") == original_w1_memo
    assert not (research / "wave-2.json").exists()


def test_gate_w2_rejects_w1_chain_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = _copy_gate_research_root(tmp_path)
    w1_memo = json.loads((research / "w1-gate-memo.json").read_text(encoding="utf-8"))
    w1_memo["stop_reasons"].append("synthetic drift")
    runner.write_json(research / "w1-gate-memo.json", w1_memo)
    _patch_research_root(monkeypatch, research)

    design_path = (
        runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments/wave-1.json"
    )
    with pytest.raises(runner.SchemaError, match="durable T4 results drift"):
        runner.gate_w2(design_path)


def test_w2_gate_schema_rejects_released_labels_for_unavailable_tranches() -> None:
    design_path = (
        runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments/wave-1.json"
    )
    design = runner.load_design(design_path)
    research = runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments"
    results = runner._t4_results_payload(
        json.loads((research / "results.json").read_text(encoding="utf-8"))
    )
    index = runner._t4_index_payload(
        json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))
    )
    memo = runner.build_w2_gate_memo(
        design=design,
        chain_digests=runner.validate_w1_chain(
            design_digest=runner.digest_file(design_path),
            wave_path=research / "wave-1.json",
            memo_path=research / "w1-gate-memo.json",
            t4_results=results,
            t4_index=index,
        ),
        w1_memo=results["w1_gate"],
    )
    bad = json.loads(json.dumps(memo))
    bad["w2_core"]["released_study_ordinals"] = bad["w2_core"].pop(
        "unavailable_study_ordinals"
    )

    with pytest.raises(runner.SchemaError):
        runner.validate_w2_gate_memo(bad)


def test_t4_evidence_index_validation_rejects_extra_and_embedded_drift() -> None:
    research = runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments"
    index = runner._t4_index_payload(
        json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))
    )
    runner.validate_t4_evidence_index(index)

    extra = json.loads(json.dumps(index))
    extra["extra"] = "not allowed"
    with pytest.raises(runner.SchemaError):
        runner.validate_t4_evidence_index(extra)

    admission_drift = json.loads(json.dumps(index))
    admission_drift["admission_evidence"]["status_counts"]["admitted"] += 1
    with pytest.raises(runner.SchemaError, match="status counts drift"):
        runner.validate_t4_evidence_index(admission_drift)

    malformed_w1 = json.loads(json.dumps(index))
    malformed_w1["w1_gate"]["memo_digest"] = "sha256:not-a-digest"
    with pytest.raises(runner.SchemaError):
        runner.validate_t4_evidence_index(malformed_w1)


def test_t5_evidence_wrapper_validation_rejects_extra_and_t4_drift() -> None:
    research = runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments"
    index = json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))
    runner._t4_index_payload(index)

    extra = json.loads(json.dumps(index))
    extra["extra"] = "not allowed"
    with pytest.raises(runner.SchemaError):
        runner._t4_index_payload(extra)

    drift = json.loads(json.dumps(index))
    drift["calibration"]["terminal_slots"] += 1
    with pytest.raises(runner.SchemaError, match="calibration evidence drifted"):
        runner._t4_index_payload(drift)


def test_gate_w2_cli_emits_stopped_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    research = _copy_gate_research_root(tmp_path)
    _patch_research_root(monkeypatch, research)
    design_path = (
        runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments/wave-1.json"
    )

    assert runner.main(["gate-w2", "--design", str(design_path)]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["gate"] == "W2"
    assert output["gate_decision"] == "stopped-before-core"
    assert output["reserve_item_ids_released"] == 0


def test_t6_review_unavailable_branch_records_capacity_without_release() -> None:
    design_path = (
        runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments/wave-1.json"
    )
    design = runner.load_design(design_path)
    research = runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments"
    results = runner._t5_results_payload(
        json.loads((research / "results.json").read_text(encoding="utf-8"))
    )
    index = runner._t5_index_payload(
        json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))
    )
    memo = runner.build_t6_review_memo(
        design=design,
        chain_digests=runner.validate_t5_chain(
            design_digest=runner.digest_file(design_path),
            wave_path=research / "wave-1.json",
            memo_path=research / "w2-gate-memo.json",
            t5_results=results,
            t5_index=index,
        ),
        w2_memo=results["w2_gate"],
    )

    assert memo["review_allocation"] == {
        "capacity_processes": 36,
        "availability": "unavailable",
        "release_flag": False,
        "reservation_policy": "blocked-without-reservation",
    }
    assert "released_study_ordinals" not in memo["review_allocation"]
    assert memo["observed"]["eligible_subjects"] == 0
    assert memo["observed"]["builder_self_audits_available"] == 0
    assert memo["observed"]["review_processes_started"] == 0
    assert memo["observed"]["unique_sustained_findings"]["status"] == "unavailable"
    assert memo["observed"]["duplicate_findings"]["status"] == "unavailable"
    assert memo["observed"]["refuted_findings"]["status"] == "unavailable"
    assert memo["observed"]["indeterminate_findings"]["status"] == "unavailable"
    assert memo["observed"]["reviewer_churn_items"]["status"] == "unavailable"
    assert memo["observed"]["reviewer_churn_tokens"]["status"] == "unavailable"
    assert set(memo["analysis_inputs"]) == set(runner.REVIEW_HYPOTHESES)
    assert all(entry["status"] == "unavailable" for entry in memo["analysis_inputs"].values())


def test_gate_t6_is_idempotent_and_preserves_t5_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = _copy_gate_research_root(tmp_path)
    original_wave = (research / "wave-1.json").read_text(encoding="utf-8")
    original_w2_memo = (research / "w2-gate-memo.json").read_text(encoding="utf-8")
    _patch_research_root(monkeypatch, research)

    design_path = (
        runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments/wave-1.json"
    )
    first = runner.gate_t6(design_path)
    first_results = json.loads((research / "results.json").read_text(encoding="utf-8"))
    first_index = json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))
    second = runner.gate_t6(design_path)
    second_results = json.loads((research / "results.json").read_text(encoding="utf-8"))
    second_index = json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))

    assert first == second
    assert first["review_decision"] == "unavailable-before-subject-selection"
    assert first["t6_model_processes_started"] == 0
    assert first["t6_review_processes_started"] == 0
    assert first_results == second_results
    assert first_index == second_index
    assert first_results["t5_results"]["plan_task"] == "T5"
    assert first_index["t5_evidence_index"]["plan_task"] == "T5"
    assert first_index["t6_review"]["t6_review_processes_started"] == 0
    assert (research / "wave-1.json").read_text(encoding="utf-8") == original_wave
    assert (research / "w2-gate-memo.json").read_text(encoding="utf-8") == original_w2_memo


def test_gate_t6_rejects_w2_chain_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = _copy_gate_research_root(tmp_path)
    w2_memo = json.loads((research / "w2-gate-memo.json").read_text(encoding="utf-8"))
    w2_memo["stop_reasons"].append("synthetic drift")
    runner.write_json(research / "w2-gate-memo.json", w2_memo)
    _patch_research_root(monkeypatch, research)

    design_path = (
        runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments/wave-1.json"
    )
    with pytest.raises(runner.SchemaError, match="durable T5 results drift"):
        runner.gate_t6(design_path)


def test_t6_review_schema_rejects_release_and_observed_churn() -> None:
    design_path = (
        runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments/wave-1.json"
    )
    design = runner.load_design(design_path)
    research = runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments"
    results = runner._t5_results_payload(
        json.loads((research / "results.json").read_text(encoding="utf-8"))
    )
    index = runner._t5_index_payload(
        json.loads((research / "evidence-index.json").read_text(encoding="utf-8"))
    )
    memo = runner.build_t6_review_memo(
        design=design,
        chain_digests=runner.validate_t5_chain(
            design_digest=runner.digest_file(design_path),
            wave_path=research / "wave-1.json",
            memo_path=research / "w2-gate-memo.json",
            t5_results=results,
            t5_index=index,
        ),
        w2_memo=results["w2_gate"],
    )

    released = json.loads(json.dumps(memo))
    released["review_allocation"]["release_flag"] = True
    with pytest.raises(runner.SchemaError):
        runner.validate_t6_review_memo(released)

    churn = json.loads(json.dumps(memo))
    churn["observed"]["reviewer_churn_tokens"] = 0
    with pytest.raises(runner.SchemaError):
        runner.validate_t6_review_memo(churn)

    findings = json.loads(json.dumps(memo))
    findings["observed"]["unique_sustained_findings"] = 0
    with pytest.raises(runner.SchemaError):
        runner.validate_t6_review_memo(findings)


def test_gate_t6_cli_emits_review_unavailable_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    research = _copy_gate_research_root(tmp_path)
    _patch_research_root(monkeypatch, research)
    design_path = (
        runner.REPO_ROOT / "docs/product/research/plan-evolution-experiments/wave-1.json"
    )

    assert runner.main(["gate-t6", "--design", str(design_path)]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["gate"] == "review-allocation"
    assert output["review_decision"] == "unavailable-before-subject-selection"
    assert output["t6_review_processes_started"] == 0


def test_progress_symlink_is_rejected_without_touching_target(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    run_dir = runner.prepare_calibration_run_root(
        Path("/private/tmp") / f"plan-evolution-progress-link-{uuid.uuid4().hex}"
    )
    outside = tmp_path / "outside-progress.jsonl"
    outside.write_text('{"event":\n', encoding="utf-8")
    progress = run_dir / "calibration-progress.jsonl"
    progress.symlink_to(outside)
    before = outside.read_bytes()

    with pytest.raises(runner.UnsafeContentError):
        runner.InvocationLedger(
            progress,
            study_ceiling=design["study_ceiling"],
            fixed_releases=design["fixed_releases"],
            reserve_release=design["reserve_release"],
        )

    assert outside.read_bytes() == before


def test_progress_hardlink_is_rejected_without_touching_target(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    run_dir = runner.prepare_calibration_run_root(
        Path("/private/tmp") / f"plan-evolution-progress-hardlink-{uuid.uuid4().hex}"
    )
    outside = tmp_path / "outside-progress.jsonl"
    outside.write_text('{"event":\n', encoding="utf-8")
    progress = run_dir / "calibration-progress.jsonl"
    progress.hardlink_to(outside)
    before = outside.read_bytes()

    with pytest.raises(runner.UnsafeContentError):
        runner.InvocationLedger(
            progress,
            study_ceiling=design["study_ceiling"],
            fixed_releases=design["fixed_releases"],
            reserve_release=design["reserve_release"],
        )

    assert outside.read_bytes() == before


def test_dry_run_policy_rejects_widened_controls_and_prompt_leakage(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    prompt = candidate / "prompt.txt"
    prompt.write_text("Read the hidden reference before building.", encoding="utf-8")

    with pytest.raises(runner.SandboxPolicyError):
        runner.build_dry_run_invocation(
            item="w1-1",
            model=design["models"]["standard"],
            candidate_root=candidate,
            prompt_file=prompt,
            policy=design["dry_run_policy"],
            limits=design["role_limits"]["builder"],
        )

    prompt.write_text("Build only the assigned slice.", encoding="utf-8")
    widened = dict(design["dry_run_policy"])
    widened["allow_network"] = True
    with pytest.raises(runner.SandboxPolicyError):
        runner.build_dry_run_invocation(
            item="w1-1",
            model=design["models"]["standard"],
            candidate_root=candidate,
            prompt_file=prompt,
            policy=widened,
            limits=design["role_limits"]["builder"],
        )


def test_dry_run_refuses_http_like_behavior_and_unlisted_sources(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    prompt = candidate / "prompt.txt"
    prompt.write_text("Fetch https://example.com before building.", encoding="utf-8")

    with pytest.raises(runner.SourcePolicyError):
        runner.build_dry_run_invocation(
            item="w1-1",
            model=design["models"]["standard"],
            candidate_root=candidate,
            prompt_file=prompt,
            policy=design["dry_run_policy"],
            limits=design["role_limits"]["builder"],
        )

    inventory = design["source_url_inventory"]
    assert (
        runner.validate_source_request(
            "https://pure.md/https://news.ycombinator.com/item?id=49840054",
            inventory,
        )
        == "https://news.ycombinator.com/item?id=49840054"
    )
    with pytest.raises(runner.SourcePolicyError):
        runner.validate_source_request("https://pure.md/https://example.com/", inventory)


def test_source_inventory_rejects_duplicate_ids_and_urls() -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    duplicate_id = dict(design["source_url_inventory"][0])
    duplicate_id["url"] = "https://example.com/duplicate-id"
    duplicate_id["pure_md_recovery"] = (
        "https://pure.md/https://example.com/duplicate-id"
    )
    design["source_url_inventory"].append(duplicate_id)
    with pytest.raises(runner.SourcePolicyError):
        runner.validate_design(design)

    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    duplicate_url = dict(design["source_url_inventory"][0])
    duplicate_url["id"] = "different-id"
    design["source_url_inventory"].append(duplicate_url)
    with pytest.raises(runner.SourcePolicyError):
        runner.validate_design(design)


def test_disposable_path_confinement_rejects_escape_link_and_hardlink(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    safe = root / "safe.txt"
    safe.write_text("ok", encoding="utf-8")
    assert runner.confine_disposable_path(root, safe) == safe.resolve()

    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    with pytest.raises(runner.UnsafeContentError):
        runner.confine_disposable_path(root, outside)

    link = root / "link.txt"
    link.symlink_to(outside)
    with pytest.raises(runner.UnsafeContentError):
        runner.confine_disposable_path(root, link)

    hardlink = root / "hardlink.txt"
    hardlink.hardlink_to(safe)
    with pytest.raises(runner.UnsafeContentError):
        runner.confine_disposable_path(root, hardlink)


def test_archive_members_reject_escape_links_and_special_entries(tmp_path: Path) -> None:
    safe_archive = tmp_path / "safe.tar"
    with tarfile.open(safe_archive, "w") as tar:
        data = b"ok"
        info = tarfile.TarInfo("dir/file.txt")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    assert runner.validate_archive_members(safe_archive) == ["dir/file.txt"]

    dir_archive = tmp_path / "dir.tar"
    with tarfile.open(dir_archive, "w") as tar:
        info = tarfile.TarInfo("dir")
        info.type = tarfile.DIRTYPE
        tar.addfile(info)
    assert runner.validate_archive_members(dir_archive) == ["dir"]

    bad_archive = tmp_path / "bad.tar"
    with tarfile.open(bad_archive, "w") as tar:
        info = tarfile.TarInfo("../escape.txt")
        info.size = 0
        tar.addfile(info, io.BytesIO(b""))
    with pytest.raises(runner.UnsafeContentError):
        runner.validate_archive_members(bad_archive)

    link_archive = tmp_path / "link.tar"
    with tarfile.open(link_archive, "w") as tar:
        info = tarfile.TarInfo("link")
        info.type = tarfile.SYMTYPE
        info.linkname = "../escape.txt"
        tar.addfile(info)
    with pytest.raises(runner.UnsafeContentError):
        runner.validate_archive_members(link_archive)

    safe_link_archive = tmp_path / "safe-link.tar"
    with tarfile.open(safe_link_archive, "w") as tar:
        data = b"rules"
        target = tarfile.TarInfo("AGENTS.md")
        target.size = len(data)
        tar.addfile(target, io.BytesIO(data))
        info = tarfile.TarInfo("CLAUDE.md")
        info.type = tarfile.SYMTYPE
        info.linkname = "AGENTS.md"
        tar.addfile(info)
    assert runner.validate_archive_members(safe_link_archive) == [
        "AGENTS.md",
        "CLAUDE.md",
    ]

    non_regular_archive = tmp_path / "fifo.tar"
    with tarfile.open(non_regular_archive, "w") as tar:
        info = tarfile.TarInfo("fifo")
        info.type = tarfile.FIFOTYPE
        tar.addfile(info)
    with pytest.raises(runner.UnsafeContentError):
        runner.validate_archive_members(non_regular_archive)


def test_admission_exports_isolated_candidate_repos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=source, check=True)
    (source / "README.md").write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=source, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-q",
            "-m",
            "baseline",
        ],
        cwd=source,
        check=True,
    )
    baseline = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (source / "README.md").write_text("reference\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=source, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-q",
            "-m",
            "reference",
        ],
        cwd=source,
        check=True,
    )
    reference = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    subprocess.run(["git", "remote", "add", "origin", "https://example.invalid/repo"], cwd=source, check=True)

    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    for task in design["tasks"]:
        task["baseline"] = baseline
        task["reference"] = reference
    monkeypatch.setattr(runner, "REPO_ROOT", source)

    record = runner.admit_task(design["tasks"][0], run_dir=tmp_path / "run")

    assert record["status"] == "excluded"
    assert record["isolation"]["baseline"]["remote_count"] == 0
    assert record["isolation"]["reference"]["alternates_present"] is False
    assert record["candidate_head"]["baseline"] != baseline
    assert record["candidate_head"]["reference"] != reference
    assert record["isolation"]["baseline"]["source_object_leak"] is False
    assert record["isolation"]["reference"]["source_object_leak"] is False

    resumed = runner.admit_task(design["tasks"][0], run_dir=tmp_path / "run")
    assert resumed["candidate_head"] == record["candidate_head"]
    assert resumed["archive_digest"] == record["archive_digest"]


def test_admission_evidence_index_preserves_order_coverage_and_case_study_branch() -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    records = []
    for task in design["tasks"]:
        record = {
            "task_id": task["id"],
            "status": "excluded",
            "first_stable_reason": "oracle requires historical dependency stack",
            "stratum": task["stratum"],
            "provenance": task["provenance"],
            "baseline": task["baseline"],
            "reference": task["reference"],
            "primary_oracle": task["primary_oracle"],
            "oracle": {
                "baseline": "not-run",
                "reference": "not-run",
                "reason": "oracle requires historical dependency stack",
            },
            "complexity": task["complexity"],
            "complexity_score": runner.complexity_score(task),
            "uncertainty": task["uncertainty"],
            "tree_digest": {
                "baseline": "git-tree:" + "a" * 40,
                "reference": "git-tree:" + "b" * 40,
            },
            "archive_digest": {
                "baseline": "sha256:" + "c" * 64,
                "reference": "sha256:" + "d" * 64,
            },
            "candidate_head": {
                "baseline": "e" * 40,
                "reference": "f" * 40,
            },
            "isolation": {
                "baseline": {
                    "remote_count": 0,
                    "alternates_present": False,
                    "source_ref_leak": False,
                    "source_object_leak": False,
                    "hidden_oracle_inside_candidate": False,
                },
                "reference": {
                    "remote_count": 0,
                    "alternates_present": False,
                    "source_ref_leak": False,
                    "source_object_leak": False,
                    "hidden_oracle_inside_candidate": False,
                },
            },
        }
        records.append(record)

    index = runner.admission_evidence_index(
        {
            "records": records,
            "status_counts": {"excluded": 12},
            "inference_ready": False,
        }
    )

    assert index["task_count"] == 12
    assert index["coverage_by_stratum"] == {
        "documentation/governance": 3,
        "adapters/validation": 3,
        "filesystem/security": 3,
        "multi-file refactor": 3,
    }
    assert [record["task_id"] for record in index["records"]] == [
        task["id"] for task in design["tasks"]
    ]
    assert index["inference_branch"] == "bounded-case-study"
    assert index["model_processes_started"] == 0


def test_run_dir_confinement_allows_only_declared_roots(tmp_path: Path) -> None:
    private_run = Path("/private/tmp/plan-evolution-t1-test")
    assert runner.confine_run_dir_for_creation(private_run) == private_run

    repo_run = runner.REPO_ROOT / ".context" / "experiments" / "t1-test"
    assert runner.confine_run_dir_for_creation(repo_run) == repo_run

    with pytest.raises(runner.UnsafeContentError):
        runner.confine_run_dir_for_creation(tmp_path / "plan-evolution-outside")
    with pytest.raises(runner.UnsafeContentError):
        runner.confine_run_dir_for_creation(Path("/private/tmp/not-plan-evolution"))

    link = tmp_path / "linked-run"
    link.symlink_to(tmp_path)
    with pytest.raises(runner.UnsafeContentError):
        runner.confine_run_dir_for_creation(
            runner.REPO_ROOT / ".context" / "experiments" / "bad" / ".." / link.name
        )


def test_admit_run_and_summarize_confine_paths(tmp_path: Path) -> None:
    design = ROOT / "fixtures" / "valid-design.json"
    run_dir = Path("/private/tmp/plan-evolution-t1-smoke")
    assert runner.run_design(design, run_dir, dry_run=True) == {
        "status": "dry-run",
        "spawned": False,
        "tasks": 12,
    }

    output = (
        runner.REPO_ROOT
        / "docs"
        / "product"
        / "research"
        / "plan-evolution-experiments"
        / "t1-summary-test.json"
    )
    try:
        assert runner.summarize(design, run_dir, output) == {
            "status": "validated",
            "study_ceiling": 240,
        }
    finally:
        if output.exists():
            output.unlink()

    with pytest.raises(runner.UnsafeContentError):
        runner.run_design(design, tmp_path / "unsafe-run", dry_run=True)
    with pytest.raises(runner.UnsafeContentError):
        runner.summarize(design, run_dir, tmp_path / "summary.json")

    external = tmp_path / "external.json"
    external.write_text("unchanged", encoding="utf-8")
    output.hardlink_to(external)
    try:
        with pytest.raises(runner.UnsafeContentError):
            runner.summarize(design, run_dir, output)
        assert external.read_text(encoding="utf-8") == "unchanged"
    finally:
        if output.exists():
            output.unlink()
