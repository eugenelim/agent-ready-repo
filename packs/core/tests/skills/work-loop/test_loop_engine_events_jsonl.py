"""Tests for loop-engine events.jsonl outbox protocol."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "work-loop" / "scripts"
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
    """cmd_init creates .loop-run/ + empty events.jsonl + gitignore entry."""

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
    """Outbox write protocol: pending → state → jsonl → delete pending."""

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
    """cmd_reset removes .loop-run/."""

    def test_loop_run_removed_on_reset(self, tmp_path: pytest.TempDir) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        assert (repo / ".loop-run").exists()
        r = _run(_LOOP_ENGINE, "reset", str(spec_dir), cwd=repo)
        assert r.returncode == 0, r.stderr
        assert not (repo / ".loop-run").exists()


class TestLifecycleFields:
    """The additive fields that make phase duration, waivers, and budgets readable.

    Without these, a consumer reading only events.jsonl cannot answer how long a
    phase took, whether a retry cap was waived, or how close a run is to its
    caps — the counters live in the cohort state file and no transition moves
    them.
    """

    def _events(self, repo: Path) -> list[dict]:
        jsonl = repo / ".loop-run" / "events.jsonl"
        return [json.loads(ln) for ln in jsonl.read_text().splitlines() if ln.strip()]

    def test_first_phase_starts_at_the_run_start(self, tmp_path: pytest.TempDir) -> None:
        """`cmd_init` writes no event line, so the run start comes from engine state."""
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        engine_state = json.loads((spec_dir / "engine-state.json").read_text())
        run_started_at = engine_state["last_transition_at"]

        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        event = self._events(repo)[0]
        assert event["phase_started_at"] == run_started_at
        assert isinstance(event["phase_s"], int)
        assert event["phase_s"] >= 0

    def test_phase_started_at_chains_from_the_previous_event(
        self, tmp_path: pytest.TempDir
    ) -> None:
        """Consecutive phases must abut, or summed time-in-phase silently loses gaps."""
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "reviewers-clean", cwd=repo)
        first, second = self._events(repo)
        assert second["phase_started_at"] == first["at"]

    def test_budgets_carry_the_counters_and_their_caps(
        self, tmp_path: pytest.TempDir
    ) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        budgets = self._events(repo)[0]["budgets"]
        cohort = json.loads((spec_dir / "state.json").read_text())
        for field in (
            "implementation_retry_count",
            "max_implementation_retries",
            "review_retry_count",
            "max_review_retries",
        ):
            assert budgets[field] == cohort[field], field

    def test_waived_is_false_without_the_flag(self, tmp_path: pytest.TempDir) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "findings-remain", cwd=repo)
        assert self._events(repo)[1]["waived"] is False

    def test_waived_is_true_with_the_retry_cap_override(
        self, tmp_path: pytest.TempDir
    ) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        r = _run(
            _LOOP_ENGINE, "transition", str(spec_dir), "findings-remain",
            "--allow-retry-cap-override", cwd=repo,
        )
        assert r.returncode == 0, r.stderr
        assert self._events(repo)[1]["waived"] is True

    def test_a_missing_cohort_state_does_not_abort_the_transition(
        self, tmp_path: pytest.TempDir
    ) -> None:
        """Reading budgets is best-effort: losing it must never cost a transition."""
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        # Make the cohort state unreadable, then keep transitioning. The engine's
        # run_id preflight needs the file, so corrupt only the fields' source by
        # emptying the JSON object rather than deleting the file.
        cohort = json.loads((spec_dir / "state.json").read_text())
        cohort.pop("review_retry_count", None)
        (spec_dir / "state.json").write_text(json.dumps(cohort))
        r = _run(_LOOP_ENGINE, "transition", str(spec_dir), "reviewers-clean", cwd=repo)
        assert r.returncode == 0, r.stderr
        event = self._events(repo)[1]
        assert event["to"] == "SPEC-HUMAN-GATE"
        assert event["budgets"]["review_retry_count"] is None


class TestOutcomeAndReasonAxes:
    """`result` says what a gate decided; `retry_state` says why a failure is there.

    One field cannot carry both: the same value would have to mean "failed once,
    retrying" and "out of attempts".
    """

    def _events(self, repo: Path) -> list[dict]:
        jsonl = repo / ".loop-run" / "events.jsonl"
        return [json.loads(ln) for ln in jsonl.read_text().splitlines() if ln.strip()]

    def test_a_passing_gate_reports_success(self, tmp_path: pytest.TempDir) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "reviewers-clean", cwd=repo)
        assert self._events(repo)[1]["result"] == "success"

    def test_a_failing_gate_reports_failure(self, tmp_path: pytest.TempDir) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "findings-remain", cwd=repo)
        assert self._events(repo)[1]["result"] == "failure"

    def test_a_non_gate_transition_reports_no_result(
        self, tmp_path: pytest.TempDir
    ) -> None:
        """`spec-ready` is a handoff, not a decision — it must not claim success."""
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        assert self._events(repo)[0]["result"] is None

    def test_retry_state_is_in_progress_while_budget_remains(
        self, tmp_path: pytest.TempDir
    ) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "findings-remain", cwd=repo)
        assert self._events(repo)[1]["retry_state"] == "in_progress"

    def _at_review_cap(self, repo: Path, spec_dir: Path) -> None:
        cohort_path = spec_dir / "state.json"
        cohort = json.loads(cohort_path.read_text())
        cohort["review_retry_count"] = cohort["max_review_retries"]
        cohort_path.write_text(json.dumps(cohort))
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)

    def test_retry_state_reports_the_cap_when_a_waiver_carries_past_it(
        self, tmp_path: pytest.TempDir
    ) -> None:
        """The three axes together, on the only path that reaches the cap.

        This is the distinction a single outcome field cannot express: the gate
        failed, the budget was spent, and a human chose to continue anyway.
        """
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        self._at_review_cap(repo, spec_dir)
        r = _run(
            _LOOP_ENGINE, "transition", str(spec_dir), "findings-remain",
            "--allow-retry-cap-override", cwd=repo,
        )
        assert r.returncode == 0, r.stderr
        event = self._events(repo)[1]
        assert event["retry_state"] == "max_attempts_reached"
        assert event["waived"] is True
        # The axes stay independent: the outcome is still just "failure".
        assert event["result"] == "failure"

    def test_a_cap_reached_without_a_waiver_writes_no_line_at_all(
        self, tmp_path: pytest.TempDir
    ) -> None:
        """A known blind spot, pinned so it cannot change unnoticed.

        The retry cap is enforced by a guard that refuses the transition, and a
        refused transition writes nothing. So a run that exhausts its budget
        goes silent rather than recording why it stopped: to a reader of the
        event log alone, cap exhaustion is indistinguishable from a stall.
        Closing it means recording refusals, which is a larger change than the
        event line.
        """
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        self._at_review_cap(repo, spec_dir)
        before = len(self._events(repo))
        r = _run(_LOOP_ENGINE, "transition", str(spec_dir), "findings-remain", cwd=repo)
        assert r.returncode != 0, "the cap must refuse without a waiver"
        assert "retry cap reached" in r.stderr
        assert len(self._events(repo)) == before, "a refusal must not write an event"

    def test_a_non_retry_transition_reports_no_retry_state(
        self, tmp_path: pytest.TempDir
    ) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        assert self._events(repo)[0]["retry_state"] is None

    def test_awaiting_input_marks_arrival_at_a_human_gate(
        self, tmp_path: pytest.TempDir
    ) -> None:
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "reviewers-clean", cwd=repo)
        first, second = self._events(repo)
        assert first["awaiting_input"] is False, "review is not a human gate"
        assert second["to"] == "SPEC-HUMAN-GATE"
        assert second["awaiting_input"] is True


class TestOutboxRecovery:
    """Outbox recovery: replay/discard stale events.pending."""

    def test_outbox_recovery_replay_when_to_matches_state(self) -> None:
        pytest.skip("STUB: replay the pending event when its `to` matches state")

    def test_outbox_recovery_discard_when_to_mismatches_state(self) -> None:
        pytest.skip("STUB: discard the pending event when its `to` mismatches state")

    def test_cmd_transition_recovers_stale_pending_before_new_transition(self) -> None:
        pytest.skip("STUB: crash-then-next-transition — pending from prior crash must be replayed/discarded at top of next cmd_transition, not lost")

    def test_cmd_transition_recovers_foreign_spec_pending_before_writing_own(self) -> None:
        pytest.skip("STUB: cross-spec — crash on spec-A then transition on spec-B must recover spec-A's pending against spec-A's engine-state.json before writing spec-B's new pending event — skipping leaves spec-A's event silently lost to the step-2 overwrite")

    def test_io_failure_does_not_abort_transition(self) -> None:
        pytest.skip("STUB (graceful-degradation): monkeypatch events.jsonl append to raise PermissionError; assert engine-state.json write still succeeds and a warning is emitted")
