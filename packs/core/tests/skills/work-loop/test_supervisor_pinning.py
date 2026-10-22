"""Launched code is checked, the supervisor is pinned, and untrusted code is gated.

VI-5030 (AC-0013), VI-5031 (AC-0014, AC-0015), VI-5032 (AC-0016), VI-5033
(AC-0017). Refusals that end before any sibling loads cost no Git call, so the
pin cases drive ``main`` on a copy of the installed skill; the regeneration
cases share one template repository that stops at the issued request.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import py_compile
import shutil
import subprocess
import sys
import unittest.mock
from collections.abc import Generator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

# Each shared helper by literal path, so every file a suite loads stays visibly
# inside this pack.
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
pytestmark = sup.INTEGRATION  # every test here drives real Git

SPEC = h.SPEC_DIR
SKILL = sup.SCRIPTS.parent
RELEASE_PLAN = sup.plan(
    sup.task(
        "T1",
        "Release note is written",
        touches="`release.txt`",
        mode="goal-based",
        tests="no stub (goal-based)",
        done="release.txt says ready",
    )
)


# ── helpers ─────────────────────────────────────────────────────────────────


def _copy_skill(destination: Path) -> Path:
    shutil.copytree(SKILL, destination, ignore=shutil.ignore_patterns("__pycache__"))
    return destination


def _load_cli(skill: Path) -> ModuleType:
    """The ``work-supervisor.py`` of *skill*, loaded under a name unique to that copy."""
    tag = hashlib.sha256(str(skill).encode()).hexdigest()[:12]
    alias = f"core_work_loop_pinning_cli_{tag}"
    spec = importlib.util.spec_from_file_location(alias, str(skill / "scripts" / "work-supervisor.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


def _run(cli: ModuleType, repo: Path, *argv: str) -> tuple[int, dict[str, Any]]:
    out = io.StringIO()
    with h.git_identity(), contextlib.redirect_stdout(out):
        code = cli.main(list(argv), cwd=repo)
    text = out.getvalue()
    return code, (json.loads(text) if text.strip() else {})


@contextlib.contextmanager
def _via(cli: ModuleType) -> Generator[None]:
    """Point the harness at *cli*, so its controller drives that copy of the skill."""
    with unittest.mock.patch.object(h, "cli", cli):
        yield


def _start_args(trust: str = "trusted") -> list[str]:
    return [
        "start",
        SPEC,
        "--intent",
        "code",
        "--code-trust",
        trust,
        "--authority-ref",
        "owner:0123456789ab",
        "--review-authority-ref",
        "plan-reviewer:0123456789ab",
    ]


def _digests(skill: Path) -> dict[str, str]:
    """The pinned digests as the spec defines them: modules, policy, and rules."""
    found = {
        p.relative_to(skill).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((skill / "scripts").rglob("*"))
        if p.is_file() and "__pycache__" not in p.relative_to(skill).parts
    }
    for name in ("supervisor-policy.json", "review-rules.json"):
        found[name] = hashlib.sha256((skill / name).read_bytes()).hexdigest()
    return found


def _store(repo: Path) -> Path:
    runs = list((repo / ".git" / "agentbundle-supervisor").iterdir())
    assert len(runs) == 1
    return runs[0]


def _pins(repo: Path) -> Path:
    return _store(repo) / "pins.json"


def _events(repo: Path) -> list[dict[str, Any]]:
    path = repo / SPEC / ".supervisor" / "security-events.jsonl"
    return [json.loads(x) for x in path.read_text("utf-8").splitlines()] if path.exists() else []


def _head(repo: Path) -> str:
    return h.git(repo, "rev-parse", "HEAD").strip()


def _copy_repo(template: Path, tmp_path: Path) -> Path:
    shutil.copytree(template / "repo", tmp_path / "repo", symlinks=True)
    return tmp_path / "repo"


def _append(path: Path, text: str) -> None:
    path.write_text(path.read_text("utf-8") + text, "utf-8")


# ── VI-5031: the supervisor is pinned ───────────────────────────────────────


@pytest.fixture(scope="module")
def pinned_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    base = tmp_path_factory.mktemp("pinned")
    repo = h.make_repo(base)
    assert h.start(repo)[0] == 0
    return base


def test_the_first_admitted_start_records_the_pins(pinned_template: Path) -> None:
    record = json.loads(_pins(pinned_template / "repo").read_text("utf-8"))
    assert record["digests"] == _digests(SKILL)
    assert "scripts/_supervisor_loop.py" in record["digests"]
    assert "supervisor-policy.json" in record["digests"]
    assert "review-rules.json" in record["digests"]


def test_a_second_start_neither_overwrites_nor_accepts_a_differing_record(
    pinned_template: Path, tmp_path: Path
) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    before = _pins(repo).read_bytes()
    code, out = h.run_cli(repo, *_start_args())
    assert code == 0 and out["status"] == "current", out
    assert _pins(repo).read_bytes() == before
    record = json.loads(before)
    record["digests"]["scripts/_supervisor_loop.py"] = "0" * 64
    _pins(repo).write_text(json.dumps(record), "utf-8")
    tampered = _pins(repo).read_bytes()
    head = _head(repo)
    code, out = h.run_cli(repo, *_start_args())
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    assert _pins(repo).read_bytes() == tampered, "a later start rewrote the pin record"
    assert _head(repo) == head


@pytest.mark.parametrize("damage", ["missing", "garbage", "no-digests"])
def test_a_missing_or_malformed_pin_record_after_admission_is_refused(
    pinned_template: Path, tmp_path: Path, damage: str
) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    if damage == "missing":
        _pins(repo).unlink()
    elif damage == "garbage":
        _pins(repo).write_text("{not json", "utf-8")
    else:
        _pins(repo).write_text('{"schema_version": 1, "digests": {}}', "utf-8")
    head = _head(repo)
    code, out = h.run_cli(repo, "next", SPEC)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    assert _head(repo) == head
    assert "supervisor-changed" in [e["reason_code"] for e in _events(repo)]


_VERBS = {
    "start": _start_args(),
    "next": ["next", SPEC],
    "report": ["report", SPEC, "RESULT"],
    "status": ["status", SPEC],
    "resolve-effect": [
        "resolve-effect",
        SPEC,
        "--operation",
        "op",
        "--decision",
        "do-not-retry",
        "--authority-ref",
        "effect-authority:0123456789ab",
    ],
}


@pytest.mark.parametrize(
    "target", ["scripts/_supervisor_commit.py", "supervisor-policy.json", "review-rules.json"]
)
def test_an_edited_installed_file_is_refused_at_every_entry_point(
    pinned_template: Path, tmp_path: Path, target: str
) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    skill = _copy_skill(tmp_path / "skill")
    _append(skill / target, "\n" if target.endswith(".json") else "\n# edited\n")
    cli = _load_cli(skill)
    result = tmp_path / "result.json"
    result.write_text("{}", "utf-8")
    head = _head(repo)
    for phase in ("with the caches", "after the caches are deleted"):
        for verb, argv in _VERBS.items():
            argv = [str(result) if a == "RESULT" else a for a in argv]
            code, out = _run(cli, repo, *argv)
            assert code == 1, (phase, verb, out)
            assert out["refusal"]["code"] == "supervisor-changed", (phase, verb, out)
        shutil.rmtree(repo / SPEC / ".supervisor", ignore_errors=True)
        shutil.rmtree(repo / ".loop-run", ignore_errors=True)
    assert _head(repo) == head


def test_a_planted_bytecode_file_is_never_executed(pinned_template: Path, tmp_path: Path) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    skill = _copy_skill(tmp_path / "skill")
    source = skill / "scripts" / "_supervisor_git.py"
    marker = tmp_path / "bytecode-ran"
    code = compile(
        source.read_text("utf-8") + f"\nopen({str(marker)!r}, 'w').close()\n", str(source), "exec"
    )
    info = source.stat()
    pyc = Path(importlib.util.cache_from_source(str(source)))
    pyc.parent.mkdir()
    from importlib import _bootstrap_external as boot  # noqa: PLC2701 - to forge a valid header

    pyc.write_bytes(boot._code_to_timestamp_pyc(code, int(info.st_mtime), info.st_size))
    out_code, out = _run(_load_cli(skill), repo, "status", SPEC)
    assert out_code == 0, out
    assert not marker.exists(), "a bytecode file beside a pinned module ran"


# ── VI-5032: regeneration ───────────────────────────────────────────────────

_SOURCE = "packs/core/.apm/skills/work-loop"
_EDITED = "scripts/install-pr-template.py"


class _SourceEditor(h.Controller):
    """A controller whose worker also edits the pack source its task owns."""

    def work(self, request: dict[str, Any]) -> dict[str, Any]:
        result = super().work(request)
        if request["kind"] == "implement-task":
            _append(self.repo / _SOURCE / _EDITED, "\n# changed by the task\n")
        return result


def _publish_source(repo: Path, skill: Path) -> None:
    """Commit the installed skill, whole, to the repository as the pack source."""
    shutil.copytree(
        skill,
        repo / _SOURCE,
        ignore=shutil.ignore_patterns("__pycache__"),
        dirs_exist_ok=True,
    )
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", "pack source")


@pytest.fixture(scope="module")
def regenerating(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A run at the issued ``regenerate`` request, with a pack source its task edited."""
    base = tmp_path_factory.mktemp("regenerating")
    skill = _copy_skill(base / "skill")
    repo = h.make_repo(base, plan=RELEASE_PLAN)
    _publish_source(repo, skill)
    controller = _SourceEditor(repo, base / "effects.log")
    with _via(_load_cli(skill)):
        assert h.start(repo)[0] == 0
        for _ in range(12):
            code, payload = h.run_cli(repo, "next", SPEC)
            assert code == 0, payload
            request = payload["request"]
            if request["kind"] == "regenerate":
                break
            assert controller.report(controller.work(request))[0] == 0
        else:
            raise AssertionError("no regenerate request")
    assert request["kind"] == "regenerate"
    return base


def _regen_copy(template: Path, tmp_path: Path) -> tuple[Path, Path, ModuleType]:
    repo = _copy_repo(template, tmp_path)
    skill = _copy_skill(tmp_path / "skill")
    return repo, skill, _load_cli(skill)


def test_one_regenerate_is_emitted_admitted_and_repinned(
    regenerating: Path, tmp_path: Path
) -> None:
    repo, skill, cli = _regen_copy(regenerating, tmp_path)
    old = json.loads(_pins(repo).read_text("utf-8"))["digests"]
    with _via(cli):
        again = h.run_cli(repo, "next", SPEC)[1]["request"]
        assert again["kind"] == "regenerate"
        # The controller regenerates the installed skill from the pack source at HEAD.
        shutil.copyfile(repo / _SOURCE / _EDITED, skill / _EDITED)
        code, out = h.run_cli(repo, "next", SPEC)
        assert code == 0, out
        same = out["request"]
        assert same["request_id"] == again["request_id"], "a second regenerate was emitted"
        result = {
            "schema_version": 1,
            "request_id": same["request_id"],
            "run_id": same["run_id"],
            "kind": "regenerate",
        }
        code, out = h.Controller(repo, tmp_path / "effects.log").report(result)
        assert code == 0 and out == {"admitted": "regenerate"}, out
        new = json.loads(_pins(repo).read_text("utf-8"))["digests"]
        assert new == _digests(skill) and new != old
        code, out = h.run_cli(repo, "next", SPEC)
        assert code == 0 and out.get("terminal") is True, out


def _tracked_regenerate(tmp_path: Path) -> tuple[Path, Path, ModuleType, h.Controller, dict[str, Any]]:
    """A run at the issued ``regenerate`` request whose installed skill is tracked in the work tree."""
    repo = h.make_repo(tmp_path, plan=RELEASE_PLAN)
    skill = _copy_skill(repo / ".installed" / "work-loop")
    _publish_source(repo, skill)  # also commits the installed skill: `add -A`
    assert h.git(repo, "ls-files", ".installed/work-loop/SKILL.md").strip()
    controller = _SourceEditor(repo, tmp_path / "effects.log")
    cli = _load_cli(skill)
    with _via(cli):
        assert h.start(repo)[0] == 0
        for _ in range(12):
            code, payload = h.run_cli(repo, "next", SPEC)
            assert code == 0, payload
            request = payload["request"]
            if request["kind"] == "regenerate":
                break
            assert controller.report(controller.work(request))[0] == 0
        else:
            raise AssertionError("no regenerate request")
    return repo, skill, cli, controller, request


def _regenerate_result(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "request_id": request["request_id"],
        "run_id": request["run_id"],
        "kind": "regenerate",
    }


def test_a_tracked_install_waits_for_the_controller_to_commit_the_regenerated_skill(
    tmp_path: Path,
) -> None:
    repo, skill, cli, controller, request = _tracked_regenerate(tmp_path)
    with _via(cli):
        old = json.loads(_pins(repo).read_text("utf-8"))["digests"]
        shutil.copyfile(repo / _SOURCE / _EDITED, skill / _EDITED)
        code, out = h.Controller(repo, tmp_path / "effects.log").report(_regenerate_result(request))
        assert code == 0 and out == {"admitted": "regenerate"}, out
        new = json.loads(_pins(repo).read_text("utf-8"))["digests"]
        assert new == _digests(skill) and new != old
        # The regenerated skill is a tracked, modified file until the controller commits it.
        code, out = h.run_cli(repo, "next", SPEC)
        asked = out.get("request", {})
        assert code == 0 and asked.get("kind") == "human-decision", out
        assert asked["reason"] == "uncommitted-changes", out
        h.git(repo, "add", "-A")
        h.git(repo, "commit", "-q", "-m", "regenerate the installed skill")
        # The commit moved HEAD, so the run re-earns its evidence before it converges.
        kinds: list[str] = []
        for _ in range(12):
            code, out = h.run_cli(repo, "next", SPEC)
            assert code == 0, out
            if out.get("terminal") is True:
                break
            kinds.append(out["request"]["kind"])
            result = controller.work(out["request"])
            report = result.get("report")
            if report is not None:  # a second review round must not reuse the first round's ids
                report["report_id"] += "-again"
                report["lineage"]["source_event_id"] += "-again"
                for finding in report["findings"]:
                    finding["finding_id"] += "-again"
            assert controller.report(result)[0] == 0, kinds
        else:
            raise AssertionError(f"the run did not converge: {kinds}")
        assert "regenerate" not in kinds, kinds
        assert json.loads(_pins(repo).read_text("utf-8"))["digests"] == _digests(skill)


def test_a_committed_skill_that_differs_from_the_admitted_one_is_refused(tmp_path: Path) -> None:
    repo, skill, cli, _controller, request = _tracked_regenerate(tmp_path)
    with _via(cli):
        shutil.copyfile(repo / _SOURCE / _EDITED, skill / _EDITED)
        code, out = h.Controller(repo, tmp_path / "effects.log").report(_regenerate_result(request))
        assert code == 0 and out == {"admitted": "regenerate"}, out
        # The controller commits more than it regenerated; a file the pins do not name.
        _append(skill / "SKILL.md", "\n<!-- slipped in after admission -->\n")
        h.git(repo, "add", "-A")
        h.git(repo, "commit", "-q", "-m", "regenerate the installed skill")
        code, out = h.run_cli(repo, "next", SPEC)
        assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out


def test_an_install_whose_other_files_differ_from_the_source_is_refused(
    regenerating: Path, tmp_path: Path
) -> None:
    repo, skill, cli = _regen_copy(regenerating, tmp_path)
    shutil.copyfile(repo / _SOURCE / _EDITED, skill / _EDITED)
    _append(skill / "SKILL.md", "\n<!-- not in the pack source -->\n")  # not a pinned file
    before = _pins(repo).read_bytes()
    with _via(cli):
        again = h.run_cli(repo, "next", SPEC)[1]["request"]
        code, out = h.Controller(repo, tmp_path / "effects.log").report(_regenerate_result(again))
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    assert _pins(repo).read_bytes() == before


def test_a_mismatched_install_is_refused(regenerating: Path, tmp_path: Path) -> None:
    repo, skill, cli = _regen_copy(regenerating, tmp_path)
    before = _pins(repo).read_bytes()
    _append(skill / _EDITED, "\n# not the pack source\n")
    code, out = _run(cli, repo, "next", SPEC)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    assert _pins(repo).read_bytes() == before


def test_no_regenerate_without_the_pack_source_at_head(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    assert h.workspace(repo).attempts.source_digests() is None


# ── VI-5030: launched code ──────────────────────────────────────────────────

_CONFTEST = """from pathlib import Path

Path({target!r}).write_text("# written by a test file\\n", encoding="utf-8")
"""
_GATE_TEST = "def test_gate():\n    assert True\n"


def _with_conftest(repo: Path, target: Path | None = None) -> None:
    """An earlier task's ``conftest.py`` that writes *target*, by default this repository's ``plan.md``."""
    (repo / "conftest.py").write_text(
        _CONFTEST.format(target=str(target or repo / SPEC / "plan.md")), encoding="utf-8"
    )
    (repo / "test_gate.py").write_text(_GATE_TEST, encoding="utf-8")
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", "an earlier task added a conftest")


def _pytest(repo: Path, *args: str) -> int:
    """Run pytest the way a gate command or a stub does, with no cache or bytecode written."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(
        [sup.PYTHON, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        check=False,
    ).returncode


def _assert_refused_and_never_adopted(repo: Path, out: dict[str, Any], head: str) -> None:
    assert out["refusal"]["code"] == "attempt-refused", out
    assert "plan.md" in out["refusal"]["detail"]
    assert _head(repo) == head, "a refused result was committed"
    code, again = h.run_cli(repo, "next", SPEC)
    assert code == 1 and again["refusal"]["code"] == "attempt-residue", again
    assert _head(repo) == head, "the written plan.md was committed as a replan"


def test_a_conftest_that_writes_plan_md_during_a_red_proof_is_refused(tmp_path: Path) -> None:
    fence = (
        f'  ```stub path=test_calc.py run="{sup.PYTHON} -m pytest -q -p no:cacheprovider '
        '{path}" red-exit=1\n'
        "  def test_answer():\n      import calc\n      assert calc.answer() == 42\n  ```"
    )
    plan = sup.plan(
        sup.task(
            "T1", "Calculator answers", tests="- **VI-1:** the calculator test.\n\n" + fence
        )
    )
    repo = h.make_repo(tmp_path, plan=plan)
    _with_conftest(repo)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    request = h.run_cli(repo, "next", SPEC)[1]["request"]
    assert request["kind"] == "write-stub"
    result = controller.work(request)
    head = _head(repo)
    code, out = controller.report(result)
    assert code == 1, out
    _assert_refused_and_never_adopted(repo, out, head)


def test_a_conftest_that_writes_plan_md_during_a_gate_run_is_refused(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path, plan=RELEASE_PLAN)
    _with_conftest(repo)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    request = h.run_cli(repo, "next", SPEC)[1]["request"]
    assert controller.report(controller.work(request))[0] == 0
    request = h.run_cli(repo, "next", SPEC)[1]["request"]
    assert request["kind"] == "run-gates"
    result = controller.work(request)
    assert _pytest(repo, "test_gate.py") == 0
    assert "written by a test file" in (repo / SPEC / "plan.md").read_text("utf-8")
    head = _head(repo)
    code, out = controller.report(result)
    assert code == 1, out
    _assert_refused_and_never_adopted(repo, out, head)


# ── VI-5033: untrusted code ─────────────────────────────────────────────────


def _no_launch(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("the supervisor launched repository code under untrusted trust")


def test_untrusted_trust_with_stubs_asks_a_human_instead_of_a_red_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tdd = h.cli._supervisor("_supervisor_tdd.py")
    monkeypatch.setattr(tdd, "observe", _no_launch)
    repo = h.make_repo(tmp_path)
    assert h.run_cli(repo, *_start_args("untrusted"))[0] == 0
    code, out = h.run_cli(repo, "next", SPEC)
    request = out["request"]
    assert code == 0 and request["kind"] == "human-decision", out
    assert request["reason"] == "untrusted-code"
    assert "trusted" in request["question"] and "containment" in request["question"]


def test_untrusted_trust_never_issues_run_gates_and_re_approval_clears_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tdd = h.cli._supervisor("_supervisor_tdd.py")
    monkeypatch.setattr(tdd, "observe", _no_launch)
    repo = h.make_repo(tmp_path, plan=RELEASE_PLAN)
    assert h.run_cli(repo, *_start_args("untrusted"))[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    request = h.run_cli(repo, "next", SPEC)[1]["request"]
    assert request["kind"] == "implement-task"
    assert controller.report(controller.work(request))[0] == 0
    code, out = h.run_cli(repo, "next", SPEC)
    request = out["request"]
    assert code == 0 and request["kind"] == "human-decision", out
    assert request["reason"] == "untrusted-code"
    code, out = h.run_cli(repo, *_start_args("trusted"))
    assert code == 0 and out["status"] == "admitted" and out["sequence"] == 2, out
    request = h.run_cli(repo, "next", SPEC)[1]["request"]
    assert request["kind"] == "run-gates"


def test_verified_containment_lifts_the_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    loop = h.loop
    containment = loop._supervisor("_containment.py")
    state = unittest.mock.Mock(latest={"code_trust": "untrusted"})
    assert loop.untrusted_blocked(state) is True
    monkeypatch.setattr(
        containment,
        "report_host_containment_axes",
        lambda: {"verified_sandbox": True, "restricted_principal": False},
    )
    assert loop.untrusted_blocked(state) is False
    assert loop.untrusted_blocked(unittest.mock.Mock(latest={"code_trust": "trusted"})) is False


# ── review fixes: shadow modules, the pre-import locator, regeneration scope ─


def _script(skill: Path, repo: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    """Run the installed ``work-supervisor.py`` as a real script, the way a controller does."""
    env = {**os.environ, **h.GIT_ENV, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(
        [sys.executable, str(skill / "scripts" / "work-supervisor.py"), *argv],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


_PLANTED = [
    "argparse.py",
    "json.pyc",
    "hashlib.cpython-313-x86_64-linux-gnu.so",
    "__future__.py",
    "__future__.pyc",
    "__future__/__init__.py",
]


def _plant(skill: Path, planted: str, marker: Path) -> None:
    """Put a module named *planted* in ``scripts/`` that creates *marker* when it runs."""
    body = f"open({str(marker)!r}, 'w').close()\n"
    target = skill / "scripts" / planted
    target.parent.mkdir(parents=True, exist_ok=True)
    if planted == "__future__.pyc":  # a real bytecode file, importable without its source
        source = marker.parent / "planted-source.py"
        source.write_text(body, "utf-8")
        py_compile.compile(str(source), cfile=str(target), doraise=True)
    else:
        target.write_text(body, "utf-8")


@pytest.mark.parametrize("planted", _PLANTED)
def test_a_module_planted_in_scripts_never_runs_and_is_refused(
    pinned_template: Path, tmp_path: Path, planted: str
) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    skill = _copy_skill(tmp_path / "skill")
    marker = tmp_path / "shadow-ran"
    _plant(skill, planted, marker)
    done = _script(skill, repo, "status", SPEC)
    assert not marker.exists(), "a module planted beside the script ran"
    assert done.returncode == 1, (done.stdout, done.stderr)
    assert json.loads(done.stdout)["refusal"]["code"] == "supervisor-changed"


def test_the_script_runs_when_nothing_is_planted(pinned_template: Path, tmp_path: Path) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    skill = _copy_skill(tmp_path / "skill")
    done = _script(skill, repo, "status", SPEC)
    assert done.returncode == 0, (done.stdout, done.stderr)


def test_deleting_the_working_approvals_hides_nothing(
    pinned_template: Path, tmp_path: Path
) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    skill = _copy_skill(tmp_path / "skill")
    marker = tmp_path / "edited-module-ran"
    _append(skill / "scripts" / "_supervisor_commit.py", f"\nopen({str(marker)!r}, 'w').close()\n")
    (repo / SPEC / "delivery" / "approvals.jsonl").unlink()
    code, out = _run(_load_cli(skill), repo, "next", SPEC)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    assert not marker.exists(), "an edited module loaded before the pin check"


@pytest.mark.parametrize("damage", ["wrong-run", "wrong-spec"])
def test_a_pin_record_naming_another_run_or_spec_is_refused_before_any_import(
    pinned_template: Path, tmp_path: Path, damage: str
) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    skill = _copy_skill(tmp_path / "skill")
    record = json.loads(_pins(repo).read_text("utf-8"))
    record["run_id" if damage == "wrong-run" else "spec"] = (
        "run-0000000000000000" if damage == "wrong-run" else "docs/specs/other"
    )
    _pins(repo).write_text(json.dumps(record), "utf-8")
    # The digests still match the install: only the record's own identity is wrong.
    code, out = _run(_load_cli(skill), repo, "next", SPEC)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out


def test_a_malformed_gitfile_is_refused_and_an_absent_repository_is_not(
    pinned_template: Path, tmp_path: Path
) -> None:
    skill = _copy_skill(tmp_path / "skill")
    cli = _load_cli(skill)
    broken = tmp_path / "broken"
    (broken / SPEC).mkdir(parents=True)
    (broken / ".git").write_text("not a gitfile\n", "utf-8")
    code, out = _run(cli, broken, "status", SPEC)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    bare = tmp_path / "bare"
    bare.mkdir()
    code, out = _run(cli, bare, "status", SPEC)
    assert code == 2 and out["error"] == "usage", out


def test_an_open_regenerate_is_honored_only_while_it_is_open(
    regenerating: Path, tmp_path: Path
) -> None:
    for mark in (".superseded", ".reported"):
        shutil.rmtree(tmp_path / mark.strip("."), ignore_errors=True)
        base = tmp_path / mark.strip(".")
        base.mkdir()
        repo, skill, cli = _regen_copy(regenerating, base)
        attempts = _store(repo) / "attempts"
        latest = max(int(p.name[:6]) for p in attempts.glob("??????.json"))
        shutil.copyfile(repo / _SOURCE / _EDITED, skill / _EDITED)
        (attempts / f"{latest:06d}{mark}").write_bytes(b"")
        code, out = _run(cli, repo, "next", SPEC)
        assert code == 1 and out["refusal"]["code"] == "supervisor-changed", (mark, out)


@pytest.mark.parametrize("point", ["commit-built", "head-moved"])
def test_pins_come_only_from_an_admitted_start(tmp_path: Path, point: str) -> None:
    repo = h.make_repo(tmp_path)

    def hook(name: str) -> None:
        if name == point:
            raise h.Crash(name)

    h.commit_module.set_kill_hook(hook)
    try:
        with pytest.raises(h.Crash):
            h.start(repo)
    finally:
        h.commit_module.set_kill_hook(None)
    pins = list((repo / ".git" / "agentbundle-supervisor").glob("*/pins.json"))
    if point == "commit-built":
        assert pins == [], "a start that never admitted left a pin record"
        code, out = h.start(repo)
        assert code == 0, out
        assert len(list((repo / ".git" / "agentbundle-supervisor").glob("*/pins.json"))) == 1
    else:
        # Admitted but not yet pinned: only a start may record it.
        code, out = h.run_cli(repo, "next", SPEC)
        assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
        code, out = h.start(repo)
        assert code == 0 and out["status"] == "current", out
        assert len(list((repo / ".git" / "agentbundle-supervisor").glob("*/pins.json"))) == 1
        assert h.run_cli(repo, "next", SPEC)[0] == 0


def test_the_pin_event_is_written_only_inside_an_existing_spec_directory(
    tmp_path: Path,
) -> None:
    cli = _load_cli(_copy_skill(tmp_path / "skill"))
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "elsewhere").mkdir()
    (repo / "docs").mkdir()
    (repo / "docs" / "linked").symlink_to(repo / "elsewhere")
    cli._log_pin_event("docs/missing/spec", repo)
    cli._log_pin_event("docs/linked", repo)
    assert not (repo / "docs" / "missing").exists(), "a missing spec path was created"
    assert not (repo / "elsewhere" / ".supervisor").exists(), "the event followed a link"
    (repo / "docs" / "real").mkdir()
    cli._log_pin_event("docs/real", repo)
    log = repo / "docs" / "real" / ".supervisor" / "security-events.jsonl"
    assert json.loads(log.read_text("utf-8"))["reason_code"] == "supervisor-changed"
    if os.name == "posix":
        assert log.stat().st_mode & 0o777 == 0o600
        assert (log.parent / ".gitignore").stat().st_mode & 0o777 == 0o600


# ── review fixes: usage errors, the Git directory, the event file ──────────


def test_a_malformed_spec_dir_is_a_usage_error_before_any_sibling_loads(
    pinned_template: Path, tmp_path: Path
) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    skill = _copy_skill(tmp_path / "skill")
    marker = tmp_path / "sibling-ran"
    _append(skill / "scripts" / "_supervisor_git.py", f"\nopen({str(marker)!r}, 'w').close()\n")
    for bad in ("../escape", "/abs", "docs\\specs", "a/./b"):
        code, out = _run(_load_cli(skill), repo, "status", bad)
        assert code == 2 and out["error"] == "usage", (bad, out)
    assert not marker.exists(), "a sibling loaded before the spec path was checked"


@pytest.mark.parametrize("target", ["absent", "file"])
def test_a_gitfile_naming_no_git_directory_is_refused_as_unverifiable(
    tmp_path: Path, target: str
) -> None:
    cli = _load_cli(_copy_skill(tmp_path / "skill"))
    repo = tmp_path / "wt"
    (repo / SPEC).mkdir(parents=True)
    named = tmp_path / "gitdir"
    if target == "file":
        named.write_text("not a directory\n", "utf-8")
    (repo / ".git").write_text(f"gitdir: {named}\n", "utf-8")
    code, out = _run(cli, repo, "status", SPEC)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    assert "supervisor-changed" in [e["reason_code"] for e in _events(repo)]


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="needs a named pipe")
def test_the_pin_event_is_never_written_to_a_special_file(tmp_path: Path) -> None:
    cli = _load_cli(_copy_skill(tmp_path / "skill"))
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    local = repo / "docs" / "real" / ".supervisor"
    local.mkdir(parents=True)
    pipe = local / "security-events.jsonl"
    os.mkfifo(pipe)
    reader = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)  # lets a write succeed, so it cannot hang
    try:
        cli._log_pin_event("docs/real", repo)
        assert os.read(reader, 4096) == b"", "the event was written into a pipe"
    finally:
        os.close(reader)


# ── runs admitted before pinning shipped ────────────────────────────────────


def test_a_run_admitted_before_pinning_is_refused_and_blocks_no_other_spec(
    regenerating: Path, tmp_path: Path
) -> None:
    """The released state: committed approvals, work commits, and no supervisor store at all."""
    repo, _skill, cli = _regen_copy(regenerating, tmp_path)
    shutil.rmtree(repo / ".git" / "agentbundle-supervisor")
    approvals = (repo / SPEC / "delivery" / "approvals.jsonl").read_text("utf-8").splitlines()
    assert approvals and h.git(repo, "ls-files", f"{SPEC}/delivery/approvals.jsonl").strip()
    head = _head(repo)
    for argv in (("next", SPEC), tuple(_start_args())):
        code, out = _run(cli, repo, *argv)
        assert code == 1 and out["refusal"]["code"] == "supervisor-changed", (argv, out)
    assert not (repo / ".git" / "agentbundle-supervisor").exists()
    assert _head(repo) == head
    # The flag that once recovered such a run no longer exists.
    assert _run(cli, repo, *_start_args(), "--repin-legacy-run")[0] == 2
    # An unrelated spec in the same worktree is not blocked by it.
    other = "docs/specs/other"
    shutil.copytree(repo / SPEC, repo / other, ignore=shutil.ignore_patterns(".supervisor", "delivery"))
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", "an unrelated spec")
    code, out = _run(cli, repo, "start", other, *_start_args()[2:])
    assert code == 0 and out["status"] == "admitted", out
    assert _run(cli, repo, "next", other)[0] == 0
    assert _run(cli, repo, "next", SPEC)[1]["refusal"]["code"] == "supervisor-changed"


def test_an_unpinned_run_directory_blocks_only_its_own_spec_until_its_start_pins(
    pinned_template: Path, tmp_path: Path
) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    _add_other_spec_early(repo)
    code, out = h.run_cli(repo, "start", "docs/specs/other", *_start_args()[2:])
    assert code == 0 and out["status"] == "admitted", out
    pins = sorted((repo / ".git" / "agentbundle-supervisor").glob("run-*/pins.json"))
    first = next(p for p in pins if json.loads(p.read_text("utf-8"))["spec"] == SPEC)
    assert (first.parent / "spec").read_text("utf-8") == SPEC
    first.unlink()  # the first run's directory now has no pin record
    code, out = h.run_cli(repo, "next", SPEC)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    assert h.run_cli(repo, "next", "docs/specs/other")[0] == 0, "another spec was blocked"
    assert not first.exists()
    code, out = h.run_cli(repo, *_start_args())  # that run's own start pins it
    assert code == 0, out
    assert first.exists()
    assert h.run_cli(repo, "next", SPEC)[0] == 0


def _add_other_spec_early(repo: Path) -> None:
    other = "docs/specs/other"
    shutil.copytree(
        repo / SPEC, repo / other, ignore=shutil.ignore_patterns(".supervisor", "delivery")
    )
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", "a second spec")


def test_an_unpinned_directory_that_records_no_spec_blocks_every_spec(
    pinned_template: Path, tmp_path: Path
) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    _add_other_spec_early(repo)
    _pins(repo).unlink()
    (_store(repo) / "spec").unlink()
    code, out = h.run_cli(repo, "next", "docs/specs/other")
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    log = repo / _OTHER / ".supervisor" / "security-events.jsonl"  # the spec it was run for
    assert "supervisor-changed" in [json.loads(x)["reason_code"] for x in log.read_text().splitlines()]


def test_the_pre_import_check_runs_no_git(pinned_template: Path, tmp_path: Path) -> None:
    cli = _load_cli(_copy_skill(tmp_path / "skill"))
    assert not hasattr(cli, "subprocess"), "the entry script imports a way to spawn Git"


_NESTED = "scripts/extra/x.py"


def test_a_nested_script_is_pinned_and_in_the_regenerated_source_digests(tmp_path: Path) -> None:
    skill = _copy_skill(tmp_path / "skill")
    nested = skill / _NESTED
    nested.parent.mkdir()
    nested.write_text("VALUE = 1\n", "utf-8")
    repo = h.make_repo(tmp_path, plan=RELEASE_PLAN)
    _publish_source(repo, skill)
    controller = _SourceEditor(repo, tmp_path / "effects.log")
    cli = _load_cli(skill)
    with _via(cli):
        assert h.start(repo)[0] == 0
        assert _NESTED in json.loads(_pins(repo).read_text("utf-8"))["digests"]
        for _ in range(12):
            code, payload = h.run_cli(repo, "next", SPEC)
            assert code == 0, payload
            request = payload["request"]
            if request["kind"] == "regenerate":
                break
            assert controller.report(controller.work(request))[0] == 0
        else:
            raise AssertionError("no regenerate request")
        assert _NESTED in json.loads((_store(repo) / "regenerate.json").read_text("utf-8"))["source"]
        shutil.copyfile(repo / _SOURCE / _EDITED, skill / _EDITED)
        code, out = h.Controller(repo, tmp_path / "effects.log").report(_regenerate_result(request))
        assert code == 0 and out == {"admitted": "regenerate"}, out
        new = json.loads(_pins(repo).read_text("utf-8"))["digests"]
        assert _NESTED in new and new == _digests(skill)


# ── fourth review round ─────────────────────────────────────────────────────

_OTHER = "docs/specs/other"
WORKER_KINDS = {"implement-task", "write-stub", "review-role", "assess-finding"}


def _add_other_spec(repo: Path) -> None:
    """Commit a second spec, copied from the first without its delivery records."""
    shutil.copytree(
        repo / SPEC, repo / _OTHER, ignore=shutil.ignore_patterns(".supervisor", "delivery")
    )
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", "a second spec")


def _run_dirs(repo: Path) -> list[str]:
    return sorted(p.name for p in (repo / ".git" / "agentbundle-supervisor").iterdir())


def _open_attempt_repo(template: Path, tmp_path: Path) -> Path:
    """Spec A has an open worker attempt and a second spec B exists, with no run."""
    repo = _copy_repo(template, tmp_path)
    _add_other_spec(repo)
    code, out = h.run_cli(repo, "next", SPEC)
    assert code == 0 and out["request"]["kind"] in WORKER_KINDS, out
    return repo


def test_an_installed_file_edit_during_an_open_attempt_is_refused_on_every_spec(
    pinned_template: Path, tmp_path: Path
) -> None:
    repo = _open_attempt_repo(pinned_template, tmp_path)
    skill = _copy_skill(tmp_path / "skill")
    _append(skill / "scripts" / "_supervisor_commit.py", "\n# edited during the attempt\n")
    cli = _load_cli(skill)
    runs, head = _run_dirs(repo), _head(repo)
    for argv in (("next", _OTHER), ("start", _OTHER, *_start_args()[2:])):
        code, out = _run(cli, repo, *argv)
        assert code == 1 and out["refusal"]["code"] == "supervisor-changed", (argv, out)
    assert _run_dirs(repo) == runs, "spec B recorded a run or pins under the edited install"
    assert _head(repo) == head


def test_a_closed_attempt_does_not_guard_other_specs(
    pinned_template: Path, tmp_path: Path
) -> None:
    repo = _open_attempt_repo(pinned_template, tmp_path)
    attempts = _store(repo) / "attempts"
    latest = max(int(p.name[:6]) for p in attempts.glob("??????.json"))
    (attempts / f"{latest:06d}.superseded").write_bytes(b"")
    skill = _copy_skill(tmp_path / "skill")
    _append(skill / "scripts" / "_supervisor_commit.py", "\n# edited with no attempt open\n")
    code, out = _run(_load_cli(skill), repo, "start", _OTHER, *_start_args()[2:])
    assert code == 0 and out["status"] == "admitted", out


def test_untrusted_trust_never_issues_regenerate(regenerating: Path, tmp_path: Path) -> None:
    repo, _skill, cli = _regen_copy(regenerating, tmp_path)
    code, out = _run(cli, repo, *_start_args("untrusted"))
    assert code == 0 and out["status"] == "admitted", out
    code, out = _run(cli, repo, "next", SPEC)
    request = out["request"]
    assert code == 0 and request["kind"] == "human-decision", out
    assert request["reason"] == "untrusted-code"
    assert "trusted" in request["question"] and "containment" in request["question"]
    code, out = _run(cli, repo, *_start_args("trusted"))
    assert code == 0, out
    assert _run(cli, repo, "next", SPEC)[1]["request"]["kind"] == "regenerate"


def test_a_first_pin_needs_the_made_commit_record(pinned_template: Path, tmp_path: Path) -> None:
    """The released state: committed approvals, one approval, and no supervisor store."""
    repo = _copy_repo(pinned_template, tmp_path)
    shutil.rmtree(repo / ".git" / "agentbundle-supervisor")
    assert len((repo / SPEC / "delivery" / "approvals.jsonl").read_text("utf-8").splitlines()) == 1
    head = _head(repo)
    code, out = h.run_cli(repo, *_start_args())
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    assert not (repo / ".git" / "agentbundle-supervisor").exists(), "a refused start wrote pins"
    assert _head(repo) == head


def test_an_orphan_run_directory_is_ignored_not_deleted(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    _add_other_spec(repo)

    def hook(name: str) -> None:
        if name == "commit-built":
            raise h.Crash(name)

    h.commit_module.set_kill_hook(hook)
    try:
        with pytest.raises(h.Crash):
            h.start(repo)
    finally:
        h.commit_module.set_kill_hook(None)
    (orphan,) = _run_dirs(repo)
    store = repo / ".git" / "agentbundle-supervisor" / orphan
    assert (store / "made-commits").read_text("utf-8")
    assert (store / "spec").read_text("utf-8") == SPEC, "the store did not record its spec"
    (repo / "unrelated.txt").write_text("moves HEAD past the unlanded approval\n", "utf-8")
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", "an unrelated commit")
    # The directory blocks no other spec at all.
    code, out = h.run_cli(repo, "start", _OTHER, *_start_args()[2:])
    assert code == 0 and out["status"] == "admitted", out
    code, out = h.run_cli(repo, "next", _OTHER)
    assert code == 0, out
    # The orphan's own spec admits under a new run id; the directory stays.
    code, out = h.start(repo)
    assert code == 0 and out["status"] == "admitted", out
    assert out["run_id"] != orphan
    pinned = {
        json.loads(p.read_text("utf-8"))["run_id"]
        for p in (repo / ".git" / "agentbundle-supervisor").glob("run-*/pins.json")
    }
    assert out["run_id"] in pinned and orphan not in pinned
    assert store.is_dir()
    assert h.run_cli(repo, "next", SPEC)[0] == 0, "the ignored orphan still blocks its spec"


def test_a_case_variant_spec_dir_is_refused_before_any_sibling_loads(
    pinned_template: Path, tmp_path: Path
) -> None:
    """The variant is only an argument: the tree holds the tracked case alone, on every host."""
    repo = _copy_repo(pinned_template, tmp_path)
    variant = SPEC.upper()
    assert variant != SPEC and (repo / SPEC).is_dir()
    skill = _copy_skill(tmp_path / "skill")
    marker = tmp_path / "sibling-ran"
    _append(skill / "scripts" / "_supervisor_git.py", f"\nopen({str(marker)!r}, 'w').close()\n")
    code, out = _run(_load_cli(skill), repo, "status", variant)
    assert code == 2 and out["error"] == "usage" and "case" in out["detail"], (code, out)
    assert not marker.exists(), "a sibling loaded for a case-variant spec path"


def test_the_pinned_file_set_is_the_same_in_the_script_and_the_source_digests(
    tmp_path: Path,
) -> None:
    skill = _copy_skill(tmp_path / "skill")
    for rel in ("scripts/extra/x.py", "scripts/extra/deep/y.txt", "scripts/data.bin"):
        (skill / rel).parent.mkdir(parents=True, exist_ok=True)
        (skill / rel).write_bytes(b"x")
    for rel in ("scripts/__pycache__/a.pyc", "scripts/extra/__pycache__/b.pyc"):
        (skill / rel).parent.mkdir(parents=True, exist_ok=True)
        (skill / rel).write_bytes(b"x")
    # A plain file that carries the pruned name is left out the same way as the directories.
    (skill / "scripts" / "other").mkdir()
    (skill / "scripts" / "other" / "__pycache__").write_bytes(b"x")
    cli = _load_cli(skill)
    entry = cli._installed_digests(skill)
    assert entry == _digests(skill)
    everything = [
        p.relative_to(skill).as_posix() for p in sorted(skill.rglob("*")) if p.is_file()
    ]
    attempt = h.cli._supervisor("_supervisor_attempt.py")
    named = {rel for rel in everything if attempt.Attempts._pinned_name(rel)}
    assert named == set(entry), sorted(named ^ set(entry))
    assert all(
        rel.startswith("scripts/") or rel in ("supervisor-policy.json", "review-rules.json")
        for rel in entry
    )
    assert not any("__pycache__" in rel.split("/") for rel in entry)


# ── closing review round ────────────────────────────────────────────────────

_STUB_PLAN = sup.plan(
    sup.task(
        "T1",
        "Calculator answers",
        tests="- **VI-1:** the calculator test.\n\n"
        f'  ```stub path=test_calc.py run="{sup.PYTHON} -m pytest -q -p no:cacheprovider '
        '{path}" red-exit=1\n'
        "  def test_answer():\n      import calc\n      assert calc.answer() == 42\n  ```",
    )
)
_INSTALLED = "scripts/install-pr-template.py"


def test_a_launch_refused_for_an_installed_file_edit_guards_other_specs_until_it_clears(
    tmp_path: Path,
) -> None:
    skill = _copy_skill(tmp_path / "skill")
    cli = _load_cli(skill)
    edited = skill / _INSTALLED
    original = edited.read_bytes()
    repo = h.make_repo(tmp_path, plan=_STUB_PLAN)
    _with_conftest(repo, edited)  # the supervisor's red proof runs it and rewrites the install
    _add_other_spec(repo)
    controller = h.Controller(repo, tmp_path / "effects.log")
    with _via(cli):
        assert h.start(repo)[0] == 0
        request = h.run_cli(repo, "next", SPEC)[1]["request"]
        assert request["kind"] == "write-stub"
        code, out = controller.report(controller.work(request))
        assert code == 1 and out["refusal"]["code"] == "attempt-refused", out
        assert edited.read_bytes() != original, "the launched code did not edit the install"
        runs, head = _run_dirs(repo), _head(repo)
        for argv in (("next", _OTHER), ("start", _OTHER, *_start_args()[2:])):
            code, out = h.run_cli(repo, *argv)
            assert code == 1 and out["refusal"]["code"] == "supervisor-changed", (argv, out)
        assert _run_dirs(repo) == runs, "spec B recorded a run or pins under the edited install"
        assert _head(repo) == head
        edited.write_bytes(original)
        (repo / "conftest.py").write_text("", encoding="utf-8")
        h.git(repo, "add", "-A")
        h.git(repo, "commit", "-q", "-m", "the conftest no longer edits the install")
        # Restored paths alone do not lift the refusal; A's own next clears it.
        assert h.run_cli(repo, "next", SPEC)[0] in (0, 1)
        code, out = h.run_cli(repo, "start", _OTHER, *_start_args()[2:])
        assert code == 0 and out["status"] == "admitted", out


def test_a_worker_attempt_refused_at_report_guards_other_specs(
    pinned_template: Path, tmp_path: Path
) -> None:
    repo = _open_attempt_repo(pinned_template, tmp_path)
    controller = h.Controller(repo, tmp_path / "effects.log")
    request = h.run_cli(repo, "next", SPEC)[1]["request"]  # the open attempt's own request
    result = controller.work(request)
    (repo / SPEC / "plan.md").write_text("# written by the worker\n", encoding="utf-8")
    code, out = controller.report(result)
    assert code == 1 and out["refusal"]["code"] == "attempt-refused", out
    skill = _copy_skill(tmp_path / "skill")
    _append(skill / "scripts" / "_supervisor_commit.py", "\n# edited while the refusal stands\n")
    cli = _load_cli(skill)
    runs, head = _run_dirs(repo), _head(repo)
    for argv in (("next", _OTHER), ("start", _OTHER, *_start_args()[2:])):
        code, out = _run(cli, repo, *argv)
        assert code == 1 and out["refusal"]["code"] == "supervisor-changed", (argv, out)
    assert _run_dirs(repo) == runs and _head(repo) == head


def _kill_at(point: str) -> Any:
    def hook(name: str) -> None:
        if name == point:
            raise h.Crash(name)

    h.commit_module.set_kill_hook(hook)
    return h.commit_module.set_kill_hook


def test_a_kill_before_the_store_rename_leaves_no_run_directory_and_blocks_nothing(
    tmp_path: Path,
) -> None:
    repo = h.make_repo(tmp_path)
    _add_other_spec(repo)
    reset = _kill_at("store-built")
    try:
        with pytest.raises(h.Crash):
            h.start(repo)
    finally:
        reset(None)
    base = repo / ".git" / "agentbundle-supervisor"
    assert not [p for p in base.iterdir() if p.name.startswith("run-")], "a run directory appeared"
    assert not [p for p in base.iterdir() if p.name.startswith("run-")]
    assert h.run_cli(repo, "start", _OTHER, *_start_args()[2:])[0] == 0
    assert h.run_cli(repo, "next", _OTHER)[0] == 0
    code, out = h.start(repo)
    assert code == 0 and out["status"] == "admitted", out


def test_a_store_directory_is_born_with_its_spec_record(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    spec = _store(repo) / "spec"
    assert spec.read_text("utf-8") == SPEC
    if os.name == "posix":
        assert spec.stat().st_mode & 0o777 == 0o600


def test_a_run_directory_without_a_spec_record_refuses_every_spec_until_removed(
    pinned_template: Path, tmp_path: Path
) -> None:
    repo = _copy_repo(pinned_template, tmp_path)
    _add_other_spec_early(repo)
    tampered = repo / ".git" / "agentbundle-supervisor" / "run-0123456789abcdef"
    tampered.mkdir()
    for argv in (("next", SPEC), ("next", _OTHER), ("start", _OTHER, *_start_args()[2:])):
        code, out = h.run_cli(repo, *argv)
        assert code == 1 and out["refusal"]["code"] == "supervisor-changed", (argv, out)
    tampered.rmdir()
    assert h.run_cli(repo, "next", SPEC)[0] == 0
    assert h.run_cli(repo, "start", _OTHER, *_start_args()[2:])[0] == 0
