"""The permutation corpus: concurrent runs end where the sequential run ends.

Four schedules (three independent attempts, a read-after-write that reprojects, a floor task
between held results, a conflict that reprojects) each run once sequentially and, under each
concurrent mode, once per forced completion order of the attempts one batch holds. Every
concurrent run must reach the sequential run's product tree and the same verdict for each
criterion in ``acceptance-verdict.v1``. Raw files that embed run and step ids are never compared.

Completion order is forced by fixture coordination and observed in the journal, which carries
one ``settled`` line per attempt in the order the attempts finished (see ``permutation_corpus``);
each run's order is asserted before the run is compared with the sequential reference.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_CORPUS = Path(__file__).resolve().parent / "permutation_corpus.py"


def _corpus() -> ModuleType:
    alias = "core_work_loop_permutation_corpus"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _CORPUS)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


pc = _corpus()
ls = pc.ls
harness = pc.harness
integ = ls.cli._supervisor("_supervisor_integration.py")
pytestmark = pc.sup.INTEGRATION


class Corpus:
    """Every corpus run, kept by key, with the run count and wall time."""

    def __init__(self) -> None:
        self.runs: list[tuple[Any, str, str, tuple[str, ...] | None, Any]] = []
        self.seconds = 0.0
        self.isolation: Any = None

    def reference(self, schedule: Any, mode: str) -> Any:
        """The sequential run of the plan *mode* runs: same plan, same repository, same run id."""
        wanted = pc.plan_of(schedule.tasks(mode))
        (found,) = [
            run for s, m, pm, _o, run in self.runs
            if s is schedule and m == pc.SEQUENTIAL and pc.plan_of(schedule.tasks(pm)) == wanted
        ]
        return found


def compare(run: Any, reference: Any) -> list[str]:
    """What differs between a run and the sequential reference, by name."""
    found = []
    if run.run_id() != reference.run_id():
        found.append("run id")
    if run.product_tree() != reference.product_tree():
        found.append("product tree")
    if run.outcomes() != reference.outcomes():
        found.append("criterion outcomes")
    return found


@pytest.fixture(scope="module")
def corpus(tmp_path_factory: pytest.TempPathFactory) -> Any:
    out = Corpus()
    root = tmp_path_factory.mktemp("corpus")
    isolation = pc.Isolation(root)
    out.isolation = isolation
    started = time.monotonic()
    with pytest.MonkeyPatch.context() as monkeypatch:
        isolation.apply(monkeypatch)
        # Before the first run: no pi on the PATH every subprocess gets, and Git still resolves.
        isolation.assert_clean()
        assert ls.cli._supervisor("_supervisor_git.py")._inherited_env()["PATH"] == isolation.path
        for schedule, mode, plan_mode, order, run in pc.all_runs(root, monkeypatch, isolation):
            out.runs.append((schedule, mode, plan_mode, order, run))
    out.seconds = time.monotonic() - started
    return out


@pytest.fixture(autouse=True)
def _clean_hooks() -> Any:
    yield
    ls.clear_kill_hook()
    integ.INTEGRATE_IN_COMPLETION_ORDER = False


def concurrent(corpus: Any) -> list[tuple[Any, str, str, tuple[str, ...], Any]]:
    return [r for r in corpus.runs if r[1] != pc.SEQUENTIAL]


# ── bounds and environment (AC-0061, AC-0062) ───────────────────────────────


def test_the_corpus_holds_at_most_six_schedules_of_at_most_three_attempts(corpus: Any) -> None:
    names = [s.name for s in pc.SCHEDULES]
    assert len(names) <= pc.MAX_SCHEDULES
    assert {"independent", "read-after-write", "floor-between", "conflict"} <= set(names)
    for schedule in pc.SCHEDULES:
        for mode in pc.MODES:
            assert 1 <= len(schedule.group(mode)) <= pc.MAX_ATTEMPTS
            assert len(schedule.tasks(mode)) <= pc.MAX_ATTEMPTS
    worst = pc.MAX_SCHEDULES * (len(pc.MODES) + len(pc.MODES) * 6)
    assert len(corpus.runs) <= worst
    print(f"corpus: {len(corpus.runs)} runs in {corpus.seconds:.1f}s (worst case {worst})")


def test_every_corpus_subprocess_ran_isolated_with_no_pi_on_its_path(corpus: Any) -> None:
    isolation = corpus.isolation
    assert isolation.INTERPRETER_FLAG == "-I"
    assert isolation.path == str(isolation.bin) and not (isolation.bin / "pi").exists()
    launched = 0
    for _schedule, _mode, _pm, _order, run in corpus.runs:
        launcher = run.env.launcher.read_text(encoding="utf-8").splitlines()[0]
        assert launcher.endswith(" -I"), launcher
        seen = run.env.log / "env.json"
        if not seen.exists():
            continue  # a sequential run starts no launcher
        record = json.loads(seen.read_text("utf-8"))
        assert record["isolated"] == 1
        assert record["env"]["PATH"] == isolation.path
        launched += 1
    assert launched == len(concurrent(corpus))


# ── completion order and the comparison (AC-0059) ───────────────────────────


def test_each_forced_completion_order_is_the_order_the_journal_records(corpus: Any) -> None:
    seen = set()
    for schedule, mode, _pm, order, run in concurrent(corpus):
        assert run.completed[: len(order)] == list(order), (schedule.name, mode)
        assert run.controller.batches[0] == list(schedule.group(mode)), (schedule.name, mode)
        seen.add((schedule.name, mode, order))
    # Every permutation of each batch ran, under each concurrent mode.
    for schedule in pc.SCHEDULES:
        for mode in pc.MODES:
            for order in pc.orders(schedule, mode):
                assert (schedule.name, mode, order) in seen


def test_the_allowlisted_read_after_write_keeps_its_two_tasks_in_separate_batches(
    corpus: Any,
) -> None:
    """Under ``enforced-allowlist`` the declared read meets at admission: two batches, one order."""
    schedule, mode = pc.READ_AFTER_WRITE, "enforced-allowlist"
    assert pc.orders(schedule, mode) == [("calculator-answers",)]
    runs = [r for s, m, _pm, _o, r in concurrent(corpus) if s is schedule and m == mode]
    assert len(runs) == 1
    (run,) = runs
    assert run.controller.batches[:2] == [["calculator-answers"], ["derived-file-is-written"]]
    assert run.completed == ["calculator-answers", "derived-file-is-written"]
    assert not any(line.get("reprojected") for line in run.journal())


def test_every_concurrent_run_matches_the_sequential_run(corpus: Any) -> None:
    for schedule, mode, _pm, order, run in concurrent(corpus):
        # The forced order is asserted from the journal before the run is compared.
        assert run.completed[: len(order)] == list(order), (schedule.name, mode, order)
        reference = corpus.reference(schedule, mode)
        assert compare(run, reference) == [], (schedule.name, mode, order)
        assert run.outcomes() and set(run.outcomes().values()) == {"supported"}


def test_a_sequential_run_issues_no_concurrent_request(corpus: Any) -> None:
    for _schedule, mode, _pm, _order, run in corpus.runs:
        if mode == pc.SEQUENTIAL:
            assert not run.controller.batches and not run.records("held")


def test_reprojecting_schedules_reproject_and_the_others_do_not(corpus: Any) -> None:
    for schedule, mode, _pm, order, run in concurrent(corpus):
        conflicts = [
            line for line in run.journal()
            if line.get("outcome") == "conflict" and line.get("reprojected") is True
        ]
        assert bool(conflicts) == schedule.reprojects(mode), (schedule.name, mode, order)
        # Every task landed once, whatever the batch did first.
        assert sorted(run.landed()) == sorted(
            i.slug for i in schedule.tasks(mode) if i.reads is not None
        )


def test_the_floor_task_runs_on_the_floor_between_the_concurrent_ones(corpus: Any) -> None:
    for schedule, _mode, _pm, _order, run in concurrent(corpus):
        if schedule.name == "floor-between":
            reasons = [line.get("floor_reason") for line in run.journal()]
            assert "reads-missing" in reasons


# ── the must-red mutant (AC-0060) ───────────────────────────────────────────


def test_integrating_in_completion_order_fails_the_read_after_write_comparison(
    corpus: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    schedule = pc.READ_AFTER_WRITE
    mode = "complete-trace"
    reference = corpus.reference(schedule, mode)
    order = ("derived-file-is-written", "calculator-answers")  # the reader finishes first
    sound = pc.run_schedule(schedule, mode, order, tmp_path / "sound", monkeypatch, corpus.isolation)
    assert compare(sound, reference) == []
    monkeypatch.setattr(integ, "INTEGRATE_IN_COMPLETION_ORDER", True)
    mutant = pc.run_schedule(
        schedule, mode, order, tmp_path / "mutant", monkeypatch, corpus.isolation
    )
    assert mutant.completed[:2] == list(order)
    assert "product tree" in compare(mutant, reference)
    assert mutant.landed() == list(order)  # it landed in completion order
