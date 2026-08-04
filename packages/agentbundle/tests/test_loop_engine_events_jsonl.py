"""Tests for loop-engine events.jsonl outbox protocol (AC0, AC0a)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts"
)
_LOOP_ENGINE = _SCRIPTS / "loop-engine.py"
_LOOP_COHORT = _SCRIPTS / "loop-cohort.py"


def _run(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8",
        cwd=str(cwd),
    )


def _init_git_repo(tmp_path: Path) -> Path:
    """Initialize a minimal git repo at tmp_path; return repo root."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    for cmd in (
        ["git", "config", "user.email", "test@example.com"],
        ["git", "config", "user.name", "Test"],
    ):
        subprocess.run(cmd, check=True, capture_output=True, cwd=str(tmp_path))
    return tmp_path


def _make_spec_dir(repo: Path, name: str = "test-spec") -> Path:
    spec_dir = repo / "docs" / "specs" / name
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text("- **Status:** Approved\n")
    (spec_dir / "plan.md").write_text("- **Status:** Approved\n")
    return spec_dir


def _engine_init(repo: Path, spec_dir: Path) -> str:
    """Run loop-engine init + loop-cohort init; return run_id."""
    r = _run(_LOOP_ENGINE, "init", str(spec_dir), "--mode", "code", "--json", cwd=repo)
    assert r.returncode == 0, r.stderr
    run_id = json.loads(r.stdout.strip())["run_id"]
    r = _run(_LOOP_COHORT, "init", str(spec_dir), "--run-id", run_id, cwd=repo)
    assert r.returncode == 0, r.stderr
    return run_id


class TestOutboxInit:
    """cmd_init creates .loop-run/ + empty events.jsonl + gitignore entry (AC0)."""

    def test_events_jsonl_created_empty(self, tmp_path: pytest.TempDir) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        jsonl = repo / ".loop-run" / "events.jsonl"
        assert jsonl.exists(), "events.jsonl must be created by cmd_init"
        assert jsonl.read_text() == "", "events.jsonl must start empty (no header line)"

    def test_gitignore_entry_added(self, tmp_path: pytest.TempDir) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        lines = (repo / ".gitignore").read_text().splitlines()
        assert ".loop-run/" in lines

    def test_gitignore_not_duplicated_on_second_init(self, tmp_path: pytest.TempDir) -> None:
        repo = _init_git_repo(tmp_path)
        (repo / ".gitignore").write_text(".loop-run/\n")
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        lines = (repo / ".gitignore").read_text().splitlines()
        assert lines.count(".loop-run/") == 1


class TestOutboxTransition:
    """Outbox write protocol: pending → state → jsonl → delete pending (AC0)."""

    def test_transition_appends_event_line(self, tmp_path: pytest.TempDir) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        r = _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        assert r.returncode == 0, r.stderr
        jsonl = repo / ".loop-run" / "events.jsonl"
        lines = [ln for ln in jsonl.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["from"] == "SPEC-PLAN-DRAFTING"
        assert event["event"] == "spec-ready"
        assert event["to"] == "SPEC-PLAN-REVIEW"
        assert event["seq"] == 1
        for key in ("run_id", "spec", "at"):
            assert key in event, f"missing required key: {key!r}"

    def test_event_schema_field_names(self, tmp_path: pytest.TempDir) -> None:
        """Event fields must be seq/run_id/spec/from/event/to/at (design.md:317)."""
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        jsonl = repo / ".loop-run" / "events.jsonl"
        event = json.loads(jsonl.read_text().strip())
        required_keys = {"seq", "run_id", "spec", "from", "event", "to", "at"}
        forbidden_aliases = {"to_state", "from_state", "timestamp"}
        assert set(event.keys()) >= required_keys
        assert not (set(event.keys()) & forbidden_aliases), (
            f"event uses forbidden alias(es): {set(event.keys()) & forbidden_aliases}"
        )

    def test_no_pending_file_after_successful_transition(self, tmp_path: pytest.TempDir) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        assert not (repo / ".loop-run" / "events.pending").exists()

    def test_multiple_transitions_append_in_order(self, tmp_path: pytest.TempDir) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "reviewers-clean", cwd=repo)
        jsonl = repo / ".loop-run" / "events.jsonl"
        lines = [json.loads(ln) for ln in jsonl.read_text().splitlines() if ln.strip()]
        assert len(lines) == 2
        assert lines[0]["seq"] == 1
        assert lines[1]["seq"] == 2
        assert lines[1]["from"] == "SPEC-PLAN-REVIEW"


class TestOutboxReset:
    """cmd_reset removes .loop-run/ (AC0)."""

    def test_loop_run_removed_on_reset(self, tmp_path: pytest.TempDir) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        assert (repo / ".loop-run").exists()
        r = _run(_LOOP_ENGINE, "reset", str(spec_dir), cwd=repo)
        assert r.returncode == 0, r.stderr
        assert not (repo / ".loop-run").exists()


class TestOutboxRecovery:
    """Outbox recovery: replay/discard stale events.pending (AC0a)."""

    def test_outbox_recovery_replay_when_to_matches_state(self) -> None:
        pytest.skip("STUB: AC0a")

    def test_outbox_recovery_discard_when_to_mismatches_state(self) -> None:
        pytest.skip("STUB: AC0a")

    def test_cmd_transition_recovers_stale_pending_before_new_transition(self) -> None:
        pytest.skip("STUB: AC0a (crash-then-next-transition: pending from prior crash must be replayed/discarded at top of next cmd_transition, not lost)")

    def test_cmd_transition_recovers_foreign_spec_pending_before_writing_own(self) -> None:
        pytest.skip("STUB: AC0a (cross-spec: crash on spec-A then transition on spec-B must recover spec-A's pending against spec-A's engine-state.json before writing spec-B's new pending event — skipping leaves spec-A's event silently lost to the step-2 overwrite)")

    def test_io_failure_does_not_abort_transition(self) -> None:
        pytest.skip("STUB: AC0 graceful-degradation — monkeypatch events.jsonl append to raise PermissionError; assert engine-state.json write still succeeds and a warning is emitted")
