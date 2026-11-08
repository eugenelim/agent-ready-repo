"""The concurrency permutation corpus: four schedules driven end to end through the supervisor.

Each schedule is a plan of at most three tasks. ``run_schedule`` drives one schedule to a
terminal run under a policy (``sequential`` or one concurrent mode) and, for a concurrent mode,
a forced completion order. Completion order is forced by fixture coordination: each attempt of
the fixture launcher waits for a gate file before it sends its access line, and the corpus
creates the gate of the next attempt in the chosen order only when the supervisor has held the
previous attempt's result (the ``result-held`` kill point, seen from that attempt's thread). The
observed completion order is read from the journal, which carries one ``settled`` line per
attempt in the order the attempts finished; no timing decides anything.

Every subprocess the corpus starts runs in an environment ``Isolation`` builds: the fixture
launcher under an isolated interpreter (``-I`` in its interpreter line) with a ``PATH`` holding
no ``pi`` executable, and Git (called in this process by the supervisor and the harness) under
that same ``PATH``. The supervisor runs in this process through the harness, so nothing else
is spawned.
"""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

_SUPPORT = Path(__file__).resolve().parent / "launcher_support.py"


def _support() -> Any:
    """The shared launcher support, loaded by literal path under a pack-qualified name."""
    alias = "core_work_loop_launcher_support"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _SUPPORT)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


ls = _support()

harness = ls.harness
sup = ls.sup
SPEC_DIR = harness.SPEC_DIR
MODES = ("enforced-allowlist", "complete-trace")
SEQUENTIAL = "sequential"
CALC = "def answer():\n    return 42\n"
MAX_SCHEDULES = 6
MAX_ATTEMPTS = 3


@dataclass(frozen=True)
class Item:
    """One task of a schedule."""

    number: str
    title: str
    reads: tuple[str, ...] | None  # declared reads; None leaves the task on the floor
    writes: tuple[str, ...] | None  # declared writes; None leaves the task on the floor
    files: dict[str, Any]  # what the simulated worker writes
    trace_reads: tuple[str, ...] | None = None  # attested reads when they exceed the declared

    @property
    def slug(self) -> str:
        return "-".join(self.title.lower().split())


@dataclass(frozen=True)
class Schedule:
    """A named plan, the tasks one batch holds per mode, and how it may differ per mode."""

    name: str
    items: Any  # callable: mode -> tuple[Item, ...]
    group: Any  # callable: mode -> tuple[str, ...], the slugs the first batch names, in order
    cap: int = 3
    reprojects: Any = None  # callable: mode -> bool, whether a concurrent run must reproject

    def tasks(self, mode: str) -> tuple[Item, ...]:
        return self.items(mode)  # type: ignore[no-any-return]


def _calc(number: str = "T1") -> Item:
    return Item(number, "Calculator answers", ("README.md",), ("calc.py",), {"calc.py": CALC})


# 1. three independent attempts
INDEPENDENT = Schedule(
    "independent",
    lambda mode: (
        _calc(),
        Item("T2", "Plain note is written", ("README.md",), ("plain.txt",),
             {"plain.txt": "note\n"}),
        Item("T3", "Third file is written", ("README.md",), ("third.txt",),
             {"third.txt": "3\n"}),
    ),
    lambda mode: ("calculator-answers", "plain-note-is-written", "third-file-is-written"),
    reprojects=lambda mode: False,
)


def _read_after_write(mode: str) -> tuple[Item, ...]:
    derived = {"derived.txt": {"derive": "calc.py", "prefix": "saw:"}}
    if mode == "complete-trace":
        # Declares only README.md but reads calc.py: an undeclared read the trace reveals.
        second = Item(
            "T2", "Derived file is written", ("README.md",), ("derived.txt",), derived,
            trace_reads=("README.md", "calc.py"),
        )
    else:
        second = Item(
            "T2", "Derived file is written", ("README.md", "calc.py"), ("derived.txt",), derived
        )
    return (_calc(), second)


# 2. a read-after-write that reprojects (under a trace; a declared read is never in one batch)
READ_AFTER_WRITE = Schedule(
    "read-after-write",
    _read_after_write,
    lambda mode: (
        ("calculator-answers", "derived-file-is-written")
        if mode == "complete-trace" else ("calculator-answers",)
    ),
    cap=2,
    reprojects=lambda mode: mode == "complete-trace",
)

# 3. a floor task between held results: the middle task declares no sets, so it runs on the floor
FLOOR_BETWEEN = Schedule(
    "floor-between",
    lambda mode: (
        _calc(),
        Item("T2", "Plain note is written", None, None, {"plain.txt": "note\n"}),
        Item("T3", "Third file is written", ("README.md",), ("third.txt",), {"third.txt": "3\n"}),
    ),
    lambda mode: ("calculator-answers", "third-file-is-written"),
    cap=2,
    reprojects=lambda mode: False,
)

# 4. a conflict that reprojects: both tasks write shared.txt but declare disjoint writes
CONFLICT = Schedule(
    "conflict",
    lambda mode: (
        Item("T1", "First side is written", ("README.md",), ("one.txt",),
             {"shared.txt": "one\n", "one.txt": "1\n"}),
        Item("T2", "Second side is written", ("README.md",), ("two.txt",),
             {"shared.txt": "two\n", "two.txt": "2\n"}),
    ),
    lambda mode: ("first-side-is-written", "second-side-is-written"),
    cap=2,
    reprojects=lambda mode: True,
)

SCHEDULES = (INDEPENDENT, READ_AFTER_WRITE, FLOOR_BETWEEN, CONFLICT)
assert len(SCHEDULES) <= MAX_SCHEDULES


def derived_text(base: Path, spec: dict[str, str]) -> str:
    """What a ``derive`` entry writes: its prefix and the current text of the file it reads."""
    source = base / spec["derive"]
    seen = source.read_text(encoding="utf-8").strip() if source.exists() else "missing"
    return spec["prefix"] + seen + "\n"


def orders(schedule: Schedule, mode: str) -> list[tuple[str, ...]]:
    """Every completion order of the attempts one batch holds, as slugs."""
    return list(itertools.permutations(schedule.group(mode)))


def plan_projection(schedule: Schedule, mode: str) -> list[dict[str, Any]]:
    """The ``task-contract.v1`` record of each task the schedule's plan projects."""
    projector = harness.projector
    return [
        projector.task_contract(task)
        for task in projector.project_plan(plan_of(schedule.tasks(mode))).tasks
    ]


def plan_of(items: tuple[Item, ...]) -> str:
    def spec(item: Item) -> str:
        def quote(paths: tuple[str, ...] | None) -> str | None:
            return ", ".join(f"`{p}`" for p in paths) if paths is not None else None

        return sup.task(
            item.number, item.title, mode="goal-based", tests="no stub (goal-based)",
            touches=quote(tuple(item.files)) or "`calc.py`",
            reads=quote(item.reads), writes=quote(item.writes),
        )

    return sup.plan(*[spec(item) for item in items])


# ── the environment the corpus builds ───────────────────────────────────────


class Isolation:
    """The interpreter flag and the ``PATH`` every corpus subprocess runs under."""

    INTERPRETER_FLAG = "-I"

    def __init__(self, root: Path) -> None:
        git = shutil.which("git")
        assert git is not None, "git is required"
        self.bin = root / "corpus-bin"
        self.bin.mkdir(parents=True, exist_ok=True)
        link = self.bin / "git"
        if not link.exists():
            link.symlink_to(git)
        self.path = str(self.bin)

    def assert_clean(self) -> None:
        """No ``pi`` resolves on the corpus PATH; Git does."""
        assert shutil.which("pi", path=self.path) is None
        assert shutil.which("git", path=self.path) is not None
        assert shutil.which("pi", path=ls.launcher_module.SPAWN_PATH) is None

    def apply(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Route this process's Git calls and the launcher spawn through the corpus PATH."""
        monkeypatch.setenv("PATH", self.path)
        monkeypatch.setattr(ls.launcher_module, "SPAWN_PATH", self.path)

    def isolate_launcher(self, env: Any) -> None:
        """Rewrite the launcher's interpreter line to run isolated, and pin its new digest."""
        text = env.launcher.read_text(encoding="utf-8")
        first, rest = text.split("\n", 1)
        assert first == f"#!{sys.executable}", first
        env.launcher.write_text(
            f"{first} {self.INTERPRETER_FLAG}\n{rest}", encoding="utf-8", newline="\n"
        )
        env.sha = hashlib.sha256(env.launcher.read_bytes()).hexdigest()


# ── one run ─────────────────────────────────────────────────────────────────


def script_for(
    schedule: Schedule, mode: str, order: tuple[str, ...] | None, log: Path
) -> dict[str, Any]:
    """The fixture launcher's script: per-task writes, reads, and the forced completion order."""
    per_task: dict[str, Any] = {}
    gated = {slug: i for i, slug in enumerate(order or ())}
    for item in schedule.tasks(mode):
        entry: dict[str, Any] = {"write": item.files}
        reads = list(item.reads or ("README.md",))
        entry["reads"] = reads
        if mode == "complete-trace" and item.trace_reads is not None:
            entry["access_reads"] = [{"path": p, "kind": "file"} for p in item.trace_reads]
        if item.slug in gated:
            position = gated[item.slug]
            if position > 0:
                entry["wait_for"] = str(log / f"{position - 1}.done")
        per_task[item.slug] = entry
    return {"per_task": per_task}


class Run:
    """A finished corpus run: what the product holds, what each criterion said, what happened."""

    def __init__(self, env: Any, controller: Any, terminal: dict[str, Any]) -> None:
        self.env = env
        self.controller = controller
        self.terminal = terminal
        self.repo: Path = env.repo

    def journal(self) -> list[dict[str, Any]]:
        return ls.journal(self.repo)  # type: ignore[no-any-return]

    @property
    def completed(self) -> list[str]:
        """The task slugs in the order the journal says their attempts settled."""
        return [
            str(line["request_id"]).split(":")[1].rsplit("-", 1)[0]
            for line in self.journal()
            if line.get("kind") == "run-concurrent" and line.get("outcome") == "settled"
        ]

    def run_id(self) -> str:
        return str(self.env.store().name)

    def product_tree(self) -> str:
        """The tree id of the product, set apart from the run's own delivery and control files."""
        index = self.repo / ".git" / "corpus-index"
        env = {**os.environ, **harness.GIT_ENV, "GIT_INDEX_FILE": str(index)}

        def git(*args: str) -> str:
            return subprocess.run(
                ["git", *args], cwd=self.repo, env=env, capture_output=True, text=True, check=True
            ).stdout.strip()

        git("read-tree", "HEAD")
        git("rm", "--cached", "-r", "-q", "--ignore-unmatch", "--", f"{SPEC_DIR}/delivery")
        git("rm", "--cached", "-r", "-q", "--ignore-unmatch", "--", f"{SPEC_DIR}/.supervisor")
        tree = git("write-tree")
        index.unlink()
        return tree

    def outcomes(self) -> dict[str, str]:
        """Each criterion's verdict from ``acceptance-verdict.v1``, for the final subject."""
        ws = harness.workspace(self.repo)
        readiness = ls.cli._supervisor("_supervisor_readiness.py")
        state = harness.loop.derive(ws)
        store = ws.open_evidence()
        ids = readiness.criteria(ws)
        fingerprint = readiness.delivery_subject(ws, state)["acceptance_fingerprint"]
        verdicts = store.evaluate_verdicts(
            readiness._properties(state, ids), fingerprint, readiness.sibling("_acceptance.py")
        )
        return {
            v.get("criterion_ref", ac): v["verdict"]
            for ac, v in zip(ids, verdicts, strict=True)
        }

    def landed(self) -> list[str]:
        """The task slugs of the landed attempt commits, oldest first."""
        out = self.env.git(
            "log", "--reverse", "--format=%(trailers:key=Supervisor-Task,valueonly,unfold)",
            "-E", "--grep=^Supervisor-Attempt: ",
        )
        return [line.rsplit("-", 1)[0] for line in out.splitlines() if line.strip()]

    def records(self, kind: str) -> list[dict[str, Any]]:
        directory = self.env.store() / kind
        if not directory.is_dir():
            return []
        return [json.loads(p.read_text("utf-8")) for p in sorted(directory.glob("*.json"))]


class CorpusController(harness.Controller):
    """The synthetic controller, with the corpus's worker and the ``run-concurrent`` verb."""

    def __init__(self, env: Any, schedule: Schedule, mode: str, effect_log: Path) -> None:
        super().__init__(env.repo, effect_log)
        self.env = env
        self.items = {i.title: i for i in schedule.tasks(mode)}
        self.requests: list[dict[str, Any]] = []
        self.reported: list[dict[str, Any]] = []
        self.batches: list[list[str]] = []
        self.open_batch: list[str] = []

    def work(self, request: dict[str, Any]) -> dict[str, Any]:
        kind = request["kind"]
        if kind == "run-concurrent":
            self.open_batch = list(request["tasks"])
            code, payload = self.env.verb(request["request_id"])
            assert code == 0, payload
            self.batches.append([t.rsplit("-", 1)[0] for t in request["tasks"]])
            return {"schema_version": 1, "request_id": request["request_id"],
                    "run_id": request["run_id"], "kind": kind}
        if kind == "implement-task":
            item = self.items[request["task"]["title"]]
            for rel, text in item.files.items():
                if isinstance(text, dict):
                    text = derived_text(self.repo, text)
                (self.repo / rel).write_text(text, encoding="utf-8", newline="\n")
            return {"schema_version": 1, "request_id": request["request_id"],
                    "run_id": request["run_id"], "kind": kind, "gate": {"passed": True}}
        return super().work(request)  # type: ignore[no-any-return]

    def report(self, result: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        self.reported.append(result)
        return super().report(result)

    def drive(self, limit: int = 200) -> dict[str, Any]:
        final = super().drive(limit)
        self.requests = [p["request"] for p in self.log if "request" in p]
        return final


def run_schedule(
    schedule: Schedule, mode: str, order: tuple[str, ...] | None, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, isolation: Isolation, *, plan_mode: str | None = None,
) -> Run:
    """Drive *schedule* to a terminal run under *mode*, completing attempts in *order*.

    A ``sequential`` run takes the plan a concurrent mode would run (*plan_mode*), so its
    repository, and with it the run id, is the one its concurrent counterparts start from.
    """
    plan_mode = mode if mode != SEQUENTIAL else (plan_mode or MODES[0])
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "log").mkdir(exist_ok=True)
    isolation.apply(monkeypatch)
    items = schedule.tasks(plan_mode)
    # The log directory is made by Env itself; the script names where it will be.
    script = script_for(schedule, plan_mode, order, tmp_path / "log")
    # Env creates ``log`` and fails when it exists, so hand it a fresh parent.
    (tmp_path / "log").rmdir()
    env = ls.Env(
        tmp_path, monkeypatch, mode=SEQUENTIAL if mode == SEQUENTIAL else mode,
        plan=plan_of(items), script=script,
        policy={"max_concurrent_attempts": schedule.cap},
    )
    isolation.isolate_launcher(env)
    if mode == SEQUENTIAL:
        # A sequential run pins no launcher: the shipped mode has no use for one.
        env.named = False
    code, started = env.start()
    assert code == 0, started
    controller = CorpusController(env, schedule, plan_mode, tmp_path / "effects.log")
    gates = {slug: i for i, slug in enumerate(order or ())}

    def release_next(point: str) -> None:
        if point != "result-held":
            return
        name = threading.current_thread().name
        if name.startswith("attempt-"):
            slug = name.removeprefix("attempt-").rsplit("-", 1)[0]
        else:  # a batch of one runs on the calling thread
            (slug,) = [t.rsplit("-", 1)[0] for t in controller.open_batch]
        if slug in gates:
            (tmp_path / "log" / f"{gates[slug]}.done").write_text("done", encoding="utf-8")

    harness.commit_module.set_kill_hook(release_next)
    try:
        terminal = controller.drive()
    finally:
        ls.clear_kill_hook()
    assert terminal.get("terminal"), terminal
    return Run(env, controller, terminal)


def plan_modes(schedule: Schedule) -> list[str]:
    """One mode per distinct plan text the schedule runs under: each needs its own reference."""
    seen: dict[str, str] = {}
    for mode in MODES:
        seen.setdefault(plan_of(schedule.tasks(mode)), mode)
    return list(seen.values())


def all_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolation: Isolation,
) -> Iterator[tuple[Schedule, str, str, tuple[str, ...] | None, Run]]:
    """Every corpus run: per plan once sequential, and once per order under each mode.

    Yields ``(schedule, mode, plan_mode, order, run)``; a sequential run's *plan_mode* names the
    concurrent mode whose plan it ran.
    """
    count = 0
    for schedule in SCHEDULES:
        plans: list[tuple[str, str, tuple[str, ...] | None]] = [
            (SEQUENTIAL, pm, None) for pm in plan_modes(schedule)
        ]
        for mode in MODES:
            plans += [(mode, mode, order) for order in orders(schedule, mode)]
        for mode, pm, order in plans:
            count += 1
            label = f"{schedule.name}-{mode[:4]}-{pm[:4]}-{count}"
            yield schedule, mode, pm, order, run_schedule(
                schedule, mode, order, tmp_path / label, monkeypatch, isolation, plan_mode=pm
            )
