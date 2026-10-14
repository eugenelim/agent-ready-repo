"""A synthetic controller for the execution supervisor suites.

Builds a throwaway repository holding the fixture spec, plan, and cited ADR,
then drives ``work-supervisor.py`` in-process through ``main(argv)``: a
synthetic worker answers task and stub requests, a synthetic effect source
records each dispatch, and a synthetic reviewer files one finding that its
assessment refutes. Kill points crash the supervisor by raising.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import supervisor_support as sup

SPEC_DIR = "docs/specs/calc"
FIXED_TIME = "2026-10-13T00:00:00Z"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "Fixture Author",
    "GIT_AUTHOR_EMAIL": "author@example.invalid",
    "GIT_COMMITTER_NAME": "Fixture Author",
    "GIT_COMMITTER_EMAIL": "author@example.invalid",
    "GIT_AUTHOR_DATE": FIXED_TIME,
    "GIT_COMMITTER_DATE": FIXED_TIME,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": os.devnull,
}

cli = sup.load("work-supervisor.py")
commit_module = cli._supervisor("_supervisor_commit.py")
admission = cli._supervisor("_supervisor_admission.py")
loop = cli._supervisor("_supervisor_loop.py")
journal = cli._supervisor("_supervisor_journal.py")
projector = cli._supervisor("_supervisor_projector.py")


class Crash(BaseException):
    """Raised at a kill point to simulate the supervisor process dying.

    A BaseException, so no handler written for real faults can absorb a kill.
    """


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env={**os.environ, **GIT_ENV},
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def make_repo(root: Path, *, plan: str = sup.PLAN, spec: str = sup.SPEC) -> Path:
    """A committed repository with the fixture spec, plan, and ADR."""
    repo = root / "repo"
    (repo / SPEC_DIR).mkdir(parents=True)
    (repo / "docs" / "adr").mkdir(parents=True)
    (repo / SPEC_DIR / "spec.md").write_text(spec, encoding="utf-8")
    (repo / SPEC_DIR / "plan.md").write_text(plan, encoding="utf-8")
    (repo / "docs" / "adr" / "0001-calculators-answer.md").write_text(sup.ADR, encoding="utf-8")
    (repo / ".gitignore").write_text("*.log\n.loop-run/\n__pycache__/\n", encoding="utf-8")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


@contextlib.contextmanager
def git_identity():  # noqa: ANN201 - context manager
    """Pin Git's identity, dates, and config for the duration of one call."""
    saved = {k: os.environ.get(k) for k in GIT_ENV}
    os.environ.update(GIT_ENV)
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_cli(repo: Path, *argv: str) -> tuple[int, dict[str, Any]]:
    """Run one verb in-process from *repo* with the fixed clock; return (exit code, JSON)."""
    out = io.StringIO()
    with git_identity(), contextlib.redirect_stdout(out):
        original = admission.CLOCK[0]
        admission.CLOCK[0] = lambda: FIXED_TIME
        try:
            code = cli.main(list(argv), cwd=repo)
        finally:
            admission.CLOCK[0] = original
    text = out.getvalue()
    return code, (json.loads(text) if text.strip() else {})


def workspace(repo: Path) -> Any:
    return admission.Workspace(repo, SPEC_DIR, clock=lambda: FIXED_TIME)


def report_review(role: str, subject: dict[str, Any], sequence: int) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "report_id": f"report-{role}-{sequence}",
        "role": role,
        "subject": subject,
        "terminal_status": "findings",
        "lineage": {
            "sequence": sequence,
            "review_policy_fingerprint": subject["review_policy_fingerprint"],
            "source_event_id": f"event-{sequence}",
            "producer": "synthetic-reviewer",
        },
        "findings": [
            {
                "schema_version": 1,
                "finding_id": "finding-1",
                "rule_ref": "AC-0001",
                "observation": "The calculator has no docstring.",
                "reachable_path": "calc.answer",
                "actual_failure": "A reader may not know what answer means.",
                "affected_acceptance_criteria": ["AC-0001"],
                "evidence_refs": ["calc.py"],
                "material": False,
            }
        ],
    }


def assessment(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "assessment_id": f"assessment-{request['finding_id']}",
        "finding_id": request["finding_id"],
        "report_id": request["report_id"],
        "review_subject_fingerprint": request["review_subject_fingerprint"],
        "assessment": "unsupported-opinion",
        "evidence_refs": ["calc.py"],
        "lineage": {"predicate_version": "v1"},
    }


class Controller:
    """Drives one run the way a trusted controller following the skill would."""

    def __init__(
        self,
        repo: Path,
        effect_log: Path,
        between: Callable[[Controller, dict[str, Any], str], None] | None = None,
        decide: Callable[[Controller, dict[str, Any]], bool] | None = None,
    ) -> None:
        self.repo = repo
        self.effect_log = effect_log
        self.between = between or (lambda c, r, phase: None)
        self.decide = decide
        self.log: list[dict[str, Any]] = []
        self.results = repo.parent / "results"
        self.results.mkdir(exist_ok=True)

    # ── the synthetic worker ───────────────────────────────────────────────

    def work(self, request: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": 1,
            "request_id": request["request_id"],
            "run_id": request["run_id"],
            "kind": request["kind"],
        }
        kind = request["kind"]
        if kind == "write-stub":
            task = self.task(request["task"]["task_id"])
            for stub in task["stubs"]:
                path = self.repo / stub["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(stub["content"].encode("utf-8"))
        elif kind == "implement-task":
            title = request["task"]["title"]
            if title.startswith("Calculator"):
                (self.repo / "calc.py").write_text(
                    "def answer():\n    return 42\n", encoding="utf-8"
                )
                passed = True
            elif title.startswith("Release"):
                (self.repo / "release.txt").write_text("ready\n", encoding="utf-8")
                passed = True
            else:
                text = "wip\n" if request["attempt"] == 1 else "done\n"
                (self.repo / "plain.txt").write_text(text, encoding="utf-8")
                passed = text == "done\n"
            (self.repo / "scratch.log").write_text("ignored noise\n", encoding="utf-8")
            result["gate"] = {"passed": passed}
        elif kind == "run-gates":
            result["gate"] = {"passed": True}
            result["criteria"] = [
                {"criterion_ref": ac, "outcome": "pass"} for ac in request["criteria"]
            ]
        elif kind == "review-role":
            sequence = int(request["request_id"].rsplit(":", 1)[1])
            result["report"] = report_review(request["role"], request["review_subject"], sequence)
        elif kind == "assess-finding":
            result["assessment"] = assessment(request)
        return result

    def task(self, task_id: str) -> dict[str, Any]:
        plan = (self.repo / SPEC_DIR / "plan.md").read_text(encoding="utf-8")
        return next(t for t in projector.project_plan(plan).tasks if t["task_id"] == task_id)

    # ── the synthetic effect source ────────────────────────────────────────

    def dispatched(self) -> list[str]:
        if not self.effect_log.exists():
            return []
        return self.effect_log.read_text(encoding="utf-8").split()

    def dispatch(self, request: dict[str, Any]) -> dict[str, Any]:
        key = request["effect"]["operation_key"]
        with self.effect_log.open("a", encoding="utf-8") as handle:
            handle.write(key + "\n")
        commit_module.kill_point("effect-dispatched")
        return {
            "schema_version": 1,
            "request_id": request["request_id"],
            "run_id": request["run_id"],
            "kind": "external-effect",
            "effect": {"outcome": "completed", "receipt_ref": f"remote:{key}"},
        }

    def query(self, request: dict[str, Any]) -> dict[str, Any]:
        key = request["effect"]["operation_key"]
        outcome = "present" if key in self.dispatched() else "absent"
        return {
            "schema_version": 1,
            "request_id": request["request_id"],
            "run_id": request["run_id"],
            "kind": "effect-query",
            "effect": {
                "outcome": outcome,
                **({"receipt_ref": f"remote:{key}"} if outcome == "present" else {}),
            },
        }

    # ── the loop ───────────────────────────────────────────────────────────

    def report(self, result: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        path = self.results / "result.json"
        path.write_text(json.dumps(result), encoding="utf-8")
        return run_cli(self.repo, "report", SPEC_DIR, str(path))

    def drive(self, limit: int = 200) -> dict[str, Any]:
        for _ in range(limit):
            code, payload = run_cli(self.repo, "next", SPEC_DIR)
            self.log.append(payload)
            if payload.get("terminal") or "refusal" in payload:
                return payload
            request = payload["request"]
            if request["kind"] == "human-decision":
                if self.decide is not None and self.decide(self, request):
                    continue
                return payload
            if request["kind"] == "external-effect":
                self.handle_effect(request)
                continue
            result = (
                self.query(request) if request["kind"] == "effect-query" else self.work(request)
            )
            self.between(self, request, "worked")
            code, admitted = self.report(result)
            if code != 0:
                return admitted
            follow = admitted.get("admitted")
            if isinstance(follow, dict) and "request" in follow:
                self.handle_effect(follow["request"])
            self.between(self, request, "reported")
        raise AssertionError("the run did not settle")

    def handle_effect(self, request: dict[str, Any]) -> None:
        result = self.dispatch(request)
        code, admitted = self.report(result)
        assert code == 0, admitted
        self.between(self, request, "reported")


def start(repo: Path, intent: str = "code") -> tuple[int, dict[str, Any]]:
    return run_cli(
        repo,
        "start",
        SPEC_DIR,
        "--intent",
        intent,
        "--code-trust",
        "trusted",
        "--authority-ref",
        "owner:0123456789ab",
        "--review-authority-ref",
        "plan-reviewer:0123456789ab",
    )
