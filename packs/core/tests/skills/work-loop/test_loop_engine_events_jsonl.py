"""Tests for loop-engine events.jsonl outbox protocol."""
from __future__ import annotations

import importlib.util
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

# Loaded under a pack- and skill-qualified name so a sibling skill's module of
# the same stem cannot bind first. Driving the CLI cannot reach the
# best-effort guards below it: every path that would make the cohort file
# unreadable also fails the run_id preflight, so the transition never gets far
# enough to build a line. These contracts need the functions directly.
_spec = importlib.util.spec_from_file_location(
    "core_work_loop_loop_engine_events_under_test", _LOOP_ENGINE
)
le = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(le)


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
        """Each budget field must carry its OWN value, not merely a matching one.

        The template ships `0, 5, 0, 5`, so comparing each field against the
        cohort file passes under any permutation that maps 0 to 0 and 5 to 5 —
        a swap of the implementation and review counters would go unnoticed.
        These four values are pairwise distinct so only the correct wiring
        passes.
        """
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        distinct = {
            "implementation_retry_count": 1,
            "max_implementation_retries": 7,
            "review_retry_count": 2,
            "max_review_retries": 9,
        }
        assert len(set(distinct.values())) == 4, "the fixture must stay pairwise distinct"
        cohort_path = spec_dir / "state.json"
        cohort = json.loads(cohort_path.read_text())
        cohort.update(distinct)
        cohort_path.write_text(json.dumps(cohort))

        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        assert self._events(repo)[0]["budgets"] == distinct

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


class TestPhaseDurationArithmetic:
    """`_phase_duration_s` directly — an end-to-end run cannot reach these branches.

    Two transitions land in the same second, so an assertion on a live run
    holds whether or not the clamp and the parse guard exist.
    """

    def test_it_counts_whole_seconds(self) -> None:
        assert le._phase_duration_s("2026-01-01T00:00:00Z", "2026-01-01T00:00:42Z") == 42

    def test_a_backwards_clock_step_clamps_to_zero(self) -> None:
        """Without the clamp this returns -42, which sums as a real measurement."""
        assert le._phase_duration_s("2026-01-01T00:00:42Z", "2026-01-01T00:00:00Z") == 0

    @pytest.mark.parametrize(
        "started", ["", "not-a-time", "2026-01-01 00:00:00", "2026-01-01T00:00:00+00:00"]
    )
    def test_an_unparseable_start_yields_none_not_an_exception(self, started: str) -> None:
        assert le._phase_duration_s(started, "2026-01-01T00:00:42Z") is None

    def test_an_absent_start_yields_none(self) -> None:
        assert le._phase_duration_s(None, "2026-01-01T00:00:42Z") is None

    def test_an_unparseable_end_yields_none(self) -> None:
        assert le._phase_duration_s("2026-01-01T00:00:00Z", "garbage") is None


class TestBestEffortReadsCannotCostATransition:
    """`_budget_snapshot` must absorb every unreadable-cohort shape.

    The line is built before the write path's own guard, so anything raising
    here would abort a transition that previously succeeded.
    """

    def _all_none(self, snapshot: dict) -> None:
        assert set(snapshot) == set(le._BUDGET_FIELDS), "every key must still be present"
        assert all(v is None for v in snapshot.values()), snapshot

    def test_an_absent_cohort_file(self, tmp_path: pytest.TempDir) -> None:
        self._all_none(le._budget_snapshot(tmp_path))

    def test_a_directory_where_the_cohort_file_belongs(
        self, tmp_path: pytest.TempDir
    ) -> None:
        (tmp_path / "state.json").mkdir()
        self._all_none(le._budget_snapshot(tmp_path))

    def test_a_symlinked_cohort_file(self, tmp_path: pytest.TempDir) -> None:
        real = tmp_path / "elsewhere.json"
        real.write_text(json.dumps({"review_retry_count": 3}))
        (tmp_path / "state.json").symlink_to(real)
        self._all_none(le._budget_snapshot(tmp_path))

    @pytest.mark.parametrize("body", ["", "{", "null", "[]", '"a string"', "\x00\xff"])
    def test_unusable_cohort_content(self, tmp_path: pytest.TempDir, body: str) -> None:
        (tmp_path / "state.json").write_text(body, errors="ignore")
        self._all_none(le._budget_snapshot(tmp_path))

    @pytest.mark.parametrize("value", ["5", 5.0, True, None, [], {}])
    def test_a_non_integer_counter_is_dropped_not_coerced(
        self, tmp_path: pytest.TempDir, value: object
    ) -> None:
        """`True` is an int in Python; reporting it as a count would be nonsense."""
        (tmp_path / "state.json").write_text(
            json.dumps({"review_retry_count": value, "max_review_retries": 5})
        )
        snapshot = le._budget_snapshot(tmp_path)
        assert snapshot["review_retry_count"] is None
        assert snapshot["max_review_retries"] == 5

    def test_lifecycle_fields_never_raise_on_a_hostile_cohort(
        self, tmp_path: pytest.TempDir
    ) -> None:
        (tmp_path / "state.json").mkdir()
        fields = le._lifecycle_fields(
            tmp_path, {"last_transition_at": "garbage"}, "2026-01-01T00:00:00Z",
            event="findings-remain", next_state="SPEC-PLAN-DRAFTING", waived=False,
        )
        assert fields["phase_s"] is None
        assert fields["result"] == "failure"


class TestGateOutcome:
    """`result` says what a gate decided, and nothing about attempt counts.

    How many attempts a run has taken comes from counting the events; a
    per-line count would be a second home for a fact this log already answers.
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

    def _at_review_cap(self, repo: Path, spec_dir: Path) -> None:
        cohort_path = spec_dir / "state.json"
        cohort = json.loads(cohort_path.read_text())
        cohort["review_retry_count"] = cohort["max_review_retries"]
        cohort_path.write_text(json.dumps(cohort))
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)

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
