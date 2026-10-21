"""Worker changes to trusted files are refused and never adopted.

VI-5020 (AC-0001), VI-5021 (AC-0002, AC-0003), VI-5022 (AC-0004),
VI-5023 (AC-0005, AC-0006), VI-5024 (AC-0007, AC-0008), VI-5025 (AC-0026,
AC-0027). A template repository holds one open attempt; each test copies it,
so a case costs a few Git calls rather than a run.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
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

SPEC = h.SPEC_DIR
REVIEW_PLAN = sup.plan(
    sup.task(
        "T1",
        "Release note is written",
        touches="`release.txt`",
        mode="goal-based",
        tests="no stub (goal-based)",
        done="release.txt says ready",
    )
)


# ── templates and helpers ───────────────────────────────────────────────────


def _drive_to(repo: Path, kind: str, base: Path) -> dict[str, Any]:
    """Report requests until ``next`` issues one of *kind*; return it."""
    controller = h.Controller(repo, base / "effects.log")
    for _ in range(10):
        code, payload = h.run_cli(repo, "next", SPEC)
        assert code == 0, payload
        request = payload["request"]
        if request["kind"] == kind:
            return request
        assert controller.report(controller.work(request))[0] == 0
    raise AssertionError(f"no {kind} request")


@pytest.fixture(scope="module")
def implementer_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    base = tmp_path_factory.mktemp("implementer")
    repo = h.make_repo(base)
    assert h.start(repo)[0] == 0
    assert _drive_to(repo, "write-stub", base)["kind"] == "write-stub"
    return base


@pytest.fixture(scope="module")
def reviewer_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    base = tmp_path_factory.mktemp("reviewer")
    repo = h.make_repo(base, plan=REVIEW_PLAN)
    assert h.start(repo)[0] == 0
    assert _drive_to(repo, "review-role", base)["kind"] == "review-role"
    return base


def _copy(template: Path, tmp_path: Path) -> Path:
    shutil.copytree(template / "repo", tmp_path / "repo", symlinks=True)
    return tmp_path / "repo"


def _current_request(repo: Path) -> dict[str, Any]:
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0, payload
    return payload["request"]


def _report(repo: Path, request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    controller = h.Controller(repo, repo.parent / "effects.log")
    return controller.report(controller.work(request))


def _store(repo: Path) -> Path:
    git_dir = repo / ".git"
    runs = list((git_dir / "agentbundle-supervisor").iterdir())
    assert len(runs) == 1
    return runs[0]


def _made(repo: Path) -> str:
    return (_store(repo) / "made-commits").read_text("utf-8")


def _issuances(repo: Path) -> list[str]:
    return sorted(
        p.name
        for p in (_store(repo) / "attempts").iterdir()
        if p.name.endswith(".json") and ".refused" not in p.name
    )


def _events(repo: Path) -> list[dict[str, Any]]:
    path = repo / SPEC / ".supervisor" / "security-events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text("utf-8").splitlines()]


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text("utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), "utf-8")


def _delete_local_caches(repo: Path) -> None:
    for name in ("journal.jsonl", "run.json", "security-events.jsonl"):
        (repo / SPEC / ".supervisor" / name).unlink(missing_ok=True)


@pytest.fixture
def skill(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """A copy of the installed skill directory, set as the one the supervisor runs from."""
    attempt = h.cli._supervisor("_supervisor_attempt.py")
    copy = tmp_path / "skill"
    shutil.copytree(sup.SCRIPTS.parent, copy, ignore=shutil.ignore_patterns("__pycache__"))
    monkeypatch.setattr(attempt, "SKILL_DIR", copy)
    return copy


# ── the worker's forgeries ──────────────────────────────────────────────────


def _forge_plan(repo: Path) -> None:
    _edit(repo / SPEC / "plan.md", "Build it.", "Build it, and skip the gates.")


def _forge_ac(repo: Path) -> None:
    _edit(repo / SPEC / "spec.md", "The calculator answers 42.", "The calculator answers 7.")


def _forge_adr(repo: Path) -> None:
    _edit(repo / "docs" / "adr" / "0001-calculators-answer.md", "answers 42", "answers 7")


def _forge_evidence(repo: Path) -> None:
    path = repo / SPEC / "delivery" / "evidence.jsonl"
    path.write_bytes((path.read_bytes() if path.exists() else b"") + b'{"forged": true}\n')


def _forge_branch(repo: Path) -> None:
    h.git(repo, "update-ref", "refs/heads/main", "HEAD~1")


def _forge_replace(repo: Path) -> None:
    h.git(repo, "replace", "HEAD", "HEAD~1")


def _forge_config(repo: Path) -> None:
    h.git(repo, "config", "--local", "user.name", "Someone Else")


def _forge_hook(repo: Path) -> None:
    hook = repo / ".git" / "hooks" / "post-commit"
    hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    hook.chmod(0o755)


FORGERIES: dict[str, tuple[Callable[[Path], None], str]] = {
    "plan": (_forge_plan, "plan.md"),
    "acceptance-criteria": (_forge_ac, "spec.md"),
    "adr": (_forge_adr, "0001-calculators-answer.md"),
    "evidence": (_forge_evidence, "evidence.jsonl"),
    "branch-ref": (_forge_branch, "HEAD"),
    "replace-ref": (_forge_replace, "refs/replace/"),
    "git-config": (_forge_config, "config"),
    "hook": (_forge_hook, "post-commit"),
}


# ── VI-5020: each change is refused at report ───────────────────────────────


@pytest.mark.parametrize("name", sorted(FORGERIES))
def test_a_forged_change_is_refused_at_report(
    implementer_template: Path, tmp_path: Path, name: str
) -> None:
    forge, path = FORGERIES[name]
    repo = _copy(implementer_template, tmp_path)
    request = _current_request(repo)
    result = h.Controller(repo, tmp_path / "effects.log").work(request)
    forge(repo)
    made = _made(repo)
    code, out = h.Controller(repo, tmp_path / "effects.log").report(result)
    assert code == 1, out
    assert out["refusal"]["code"] == "attempt-refused"
    assert path in out["refusal"]["detail"]
    assert _made(repo) == made, "the refused attempt committed a supervisor step"
    assert "attempt-refused" in [e["reason_code"] for e in _events(repo)]


def test_an_unparseable_git_config_is_refused_and_recorded_before_any_git_call(
    implementer_template: Path, tmp_path: Path
) -> None:
    repo = _copy(implementer_template, tmp_path)
    request = _current_request(repo)
    result = h.Controller(repo, tmp_path / "effects.log").work(request)
    # The CLI pins the repository before it reads anything, so a config broken
    # earlier ends it as a usage error; here the pins exist when the config breaks.
    ws = h.workspace(repo)
    assert ws.git.hardened.pins.git_dir
    config = repo / ".git" / "config"
    config.write_text(config.read_text("utf-8") + "[broken\n", "utf-8")
    with pytest.raises(h.admission.Refusal) as caught:
        h.loop.report(ws, result)
    assert caught.value.code == "attempt-refused"
    assert "config" in caught.value.detail
    assert any(p.name.endswith(".refused.json") for p in (_store(repo) / "attempts").iterdir())
    with pytest.raises(h.admission.Refusal) as again:
        h.loop.next_request(ws)
    assert again.value.code == "attempt-residue"


def test_a_modified_installed_skill_is_refused_at_report(
    implementer_template: Path, tmp_path: Path, skill: Path
) -> None:
    repo = _copy(implementer_template, tmp_path)
    request = _current_request(repo)
    result = h.Controller(repo, tmp_path / "effects.log").work(request)
    (skill / "scripts" / "_supervisor_loop.py").write_text("# swapped\n", encoding="utf-8")
    code, out = h.Controller(repo, tmp_path / "effects.log").report(result)
    assert code == 1, out
    assert out["refusal"]["code"] == "attempt-refused"
    assert "skill:scripts/_supervisor_loop.py" in out["refusal"]["detail"]


def test_a_rewritten_gitfile_is_refused_at_report(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    worktree = tmp_path / "wt"
    h.git(repo, "worktree", "add", "-q", "--detach", str(worktree))
    assert h.start(worktree)[0] == 0
    request = _current_request(worktree)
    result = h.Controller(worktree, tmp_path / "effects.log").work(request)
    gitdir = (worktree / ".git").read_text("utf-8").split("gitdir: ", 1)[1].strip()
    # Same directory by a different spelling: only the file's bytes differ.
    (worktree / ".git").write_text(f"gitdir: {gitdir}/../{Path(gitdir).name}", encoding="utf-8")
    code, out = h.Controller(worktree, tmp_path / "effects.log").report(result)
    assert code == 1, out
    assert out["refusal"]["code"] == "attempt-refused"
    assert ".git" in out["refusal"]["detail"]


def _forged_commit(repo: Path, parent: str, run_id: str) -> str:
    """A commit that claims to be the supervisor's step of *run_id*."""
    tree = h.git(repo, "rev-parse", "HEAD^{tree}").strip()
    message = f"forged\n\nSupervisor-Run: {run_id}\nSupervisor-Step: forged:step\n"
    message += "Supervisor-Operation: replan\n"
    return subprocess.run(
        ["git", "commit-tree", tree, "-p", parent],
        cwd=repo,
        env={**os.environ, **h.GIT_ENV},
        input=message,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _run_id(repo: Path) -> str:
    return _store(repo).name


def test_a_packed_ref_move_is_refused_at_report(
    implementer_template: Path, tmp_path: Path
) -> None:
    repo = _copy(implementer_template, tmp_path)
    request = _current_request(repo)
    result = h.Controller(repo, tmp_path / "effects.log").work(request)
    head = _head(repo).strip()
    fake = _forged_commit(repo, head, _run_id(repo))
    h.git(repo, "pack-refs", "--all", "--prune")
    packed = repo / ".git" / "packed-refs"
    packed.write_text(packed.read_text("utf-8").replace(head, fake), "utf-8")
    made = _made(repo)
    code, out = h.Controller(repo, tmp_path / "effects.log").report(result)
    assert code == 1, out
    assert out["refusal"]["code"] == "attempt-refused"
    assert "HEAD" in out["refusal"]["detail"]
    assert _made(repo) == made


def _linked_open_attempt(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, Any]]:
    """A linked worktree with an open attempt, and a decoy clone holding a forged commit."""
    repo = h.make_repo(tmp_path)
    linked = tmp_path / "linked"
    h.git(repo, "worktree", "add", "-q", "--detach", str(linked))
    assert h.start(linked)[0] == 0
    request = _current_request(linked)
    decoy = tmp_path / "decoy"
    h.git(repo, "clone", "-q", str(repo), str(decoy))
    fake = _forged_commit(decoy, h.git(decoy, "rev-parse", "HEAD").strip(), "run-0123456789abcdef")
    h.git(decoy, "checkout", "-q", "--detach", fake)
    return repo, linked, decoy, request


@pytest.mark.parametrize("target", ["gitfile", "commondir"])
def test_a_gitfile_or_commondir_aimed_at_a_decoy_is_never_admitted(
    tmp_path: Path, target: str
) -> None:
    repo, linked, decoy, _request = _linked_open_attempt(tmp_path)
    request = _current_request(linked)
    result = h.Controller(linked, tmp_path / "effects.log").work(request)
    private = Path(h.git(linked, "rev-parse", "--absolute-git-dir").strip())
    if target == "gitfile":
        (linked / ".git").write_text(f"gitdir: {decoy / '.git'}\n", encoding="utf-8")
    else:
        (private / "commondir").write_text(f"{decoy / '.git'}\n", encoding="utf-8")
    head = _head(repo)
    code, out = h.Controller(linked, tmp_path / "effects.log").report(result)
    assert code == 1, out
    assert "admitted" not in out
    assert _head(repo) == head
    assert h.git(decoy, "rev-parse", "HEAD").strip() not in h.git(repo, "rev-list", "--all")


def test_an_attempt_already_reported_stays_closed_after_a_message_preserving_rebase(
    implementer_template: Path, tmp_path: Path
) -> None:
    repo = _copy(implementer_template, tmp_path)
    request = _current_request(repo)
    assert _report(repo, request)[0] == 0
    root = h.git(repo, "rev-list", "--max-parents=0", "HEAD").strip()
    h.git(repo, "checkout", "-q", "-b", "upstream", root)
    (repo / "OTHER.md").write_text("upstream\n", encoding="utf-8")
    h.git(repo, "add", "OTHER.md")
    h.git(repo, "commit", "-q", "-m", "unrelated upstream change")
    h.git(repo, "checkout", "-q", "main")
    h.git(repo, "rebase", "-q", "upstream")
    code, out = h.run_cli(repo, "next", SPEC)
    assert code == 0, out
    assert out["request"]["request_id"] != request["request_id"]


# ── VI-5021: next before report is residue, first and again ─────────────────

_NEXT_FORGERIES = ["plan", "acceptance-criteria", "evidence"]


def _head(repo: Path) -> str:
    return h.git(repo, "rev-parse", "HEAD")


def _restore(repo: Path, paths: list[str]) -> None:
    """Return each path to its committed bytes, or remove one that was never committed."""
    for path in paths:
        try:
            h.git(repo, "cat-file", "-e", f"HEAD:{path}")
        except Exception:  # noqa: BLE001 - absent from HEAD
            (repo / path).unlink()
        else:
            h.git(repo, "checkout", "--", path)


_TRACKED = {
    "plan": [f"{SPEC}/plan.md"],
    "acceptance-criteria": [f"{SPEC}/spec.md"],
    "evidence": [f"{SPEC}/delivery/evidence.jsonl"],
}


@pytest.mark.parametrize("template_name", ["implementer_template", "reviewer_template"])
@pytest.mark.parametrize("name", _NEXT_FORGERIES)
def test_next_after_an_edit_is_residue_before_any_envelope_refusal(
    request: pytest.FixtureRequest, tmp_path: Path, template_name: str, name: str
) -> None:
    template: Path = request.getfixturevalue(template_name)
    repo = _copy(template, tmp_path)
    issued = _current_request(repo)
    forge = FORGERIES[name][0]
    head, made, before = _head(repo), _made(repo), len(_issuances(repo))
    for round_number in (1, 2):
        forge(repo)
        run_json = (repo / SPEC / ".supervisor" / "run.json").read_text("utf-8")
        code, out = h.run_cli(repo, "next", SPEC)
        assert code == 1, out
        assert out["refusal"]["code"] == "attempt-residue", out
        assert _head(repo) == head and _made(repo) == made, "a replan was committed"
        assert (repo / SPEC / ".supervisor" / "run.json").read_text("utf-8") == run_json
        _restore(repo, _TRACKED[name])
        # The refusal clears and the same request is issued again under a new manifest.
        again = _current_request(repo)
        assert again["request_id"] == issued["request_id"]
        assert len(_issuances(repo)) == before + round_number


# ── VI-5022: supervisor commits and re-approval during an open attempt ──────


EXTRA_TASK = sup.task(
    "T4",
    "Release extra note is written",
    touches="`release.txt`",
    mode="goal-based",
    tests="no stub (goal-based)",
    done="release.txt says ready",
)
OPERATOR = "effect-authority:0123456789ab"
KILL_POINTS = ["commit-built", "head-moved", "synced", "event"]


@pytest.fixture(scope="module")
def effect_template(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str]:
    """An unresolved effect and, after a replan, an open worker attempt; returns (base, key)."""
    base = tmp_path_factory.mktemp("effect")
    repo = h.make_repo(base)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, base / "effects.log")
    request = _drive_to(repo, "external-effect", base)
    key = request["effect"]["operation_key"]
    controller.dispatch(request)
    _code, payload = h.run_cli(repo, "next", SPEC)
    query = payload["request"]
    assert query["kind"] == "effect-query", payload
    code, admitted = controller.report({
        "schema_version": 1,
        "request_id": query["request_id"],
        "run_id": query["run_id"],
        "kind": "effect-query",
        "effect": {"outcome": "unknowable"},
    })
    assert admitted["admitted"] == "decision-required", admitted
    # Replanned between attempts: a new task is issued while the effect is unresolved.
    plan = repo / SPEC / "plan.md"
    plan.write_text(sup.plan(*_plan_tasks(), EXTRA_TASK), "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == "implement-task", payload
    assert payload["request"]["task"]["title"] == "Release extra note is written"
    return base, key


def _plan_tasks() -> list[str]:
    return [sup.TASKS["calc"](), sup.TASKS["push"](), sup.TASKS["plain"]()]


def _decisions(repo: Path) -> list[dict[str, Any]]:
    records = h.workspace(repo).records("effect-resolutions.jsonl")
    return [r for r in records if r["entry"] == "decision"]


def _resolve(repo: Path, key: str) -> tuple[int, dict[str, Any]]:
    return h.run_cli(
        repo, "resolve-effect", SPEC, "--operation", key, "--decision", "do-not-retry",
        "--authority-ref", OPERATOR,
    )  # fmt: skip


def _crash_at(point: str) -> Callable[[str], None]:
    fired: list[str] = []

    def hook(name: str) -> None:
        if name == point and not fired:
            fired.append(name)
            raise h.Crash(name)

    return hook


def test_a_resolve_effect_during_an_open_attempt_does_not_refuse_it(
    effect_template: tuple[Path, str], tmp_path: Path
) -> None:
    template, key = effect_template
    repo = _copy(template, tmp_path)
    request = _current_request(repo)
    head, issuances = _head(repo), _issuances(repo)
    code, out = _resolve(repo, key)
    assert code == 0, out
    assert _head(repo) != head, "the resolution did not advance HEAD"
    assert len(_decisions(repo)) == 1
    again = _current_request(repo)
    assert again["request_id"] == request["request_id"]
    assert _issuances(repo) == issuances, "the open attempt's manifest was re-recorded"
    assert _report(repo, request)[0] == 0


@pytest.mark.parametrize("point", KILL_POINTS)
def test_a_resolve_effect_killed_during_an_open_attempt_converges(
    effect_template: tuple[Path, str], tmp_path: Path, point: str
) -> None:
    template, key = effect_template
    repo = _copy(template, tmp_path)
    request = _current_request(repo)
    issuances = _issuances(repo)
    h.commit_module.set_kill_hook(_crash_at(point))
    try:
        with pytest.raises(h.Crash):
            _resolve(repo, key)
    finally:
        h.commit_module.set_kill_hook(None)
    # The operator runs it again; it may find the resolution already committed.
    code, out = _resolve(repo, key)
    assert code == 0 or out["refusal"]["code"] == "no-open-effect", out
    assert len(_decisions(repo)) == 1
    assert _current_request(repo)["request_id"] == request["request_id"]
    assert _issuances(repo) == issuances
    assert _report(repo, request)[0] == 0


NO_INTENT_SPEC = sup.SPEC.replace("## Terminal Intent\n\n`code` — build the calculator.\n\n", "")


@pytest.fixture(scope="module")
def reapproval_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A spec that declares no terminal intent, with an open attempt under a ``code`` approval."""
    base = tmp_path_factory.mktemp("reapproval")
    repo = h.make_repo(base, spec=NO_INTENT_SPEC)
    assert h.start(repo)[0] == 0
    assert _current_request(repo)["kind"] == "write-stub"
    return base


def _steps(repo: Path) -> list[str]:
    ws = h.workspace(repo)
    return [c.step for c in ws.git.supervisor_commits(ws.approvals()[0]["run_id"])]


def test_a_re_approval_start_during_an_open_attempt_advances_head_and_passes(
    reapproval_template: Path, tmp_path: Path
) -> None:
    repo = _copy(reapproval_template, tmp_path)
    head, issuances = _head(repo), _issuances(repo)
    code, out = h.start(repo, "spec-plan")
    assert code == 0 and out["status"] == "terminal", out
    assert _head(repo) != head
    assert _steps(repo)[-2:-1] == ["approval:2"]
    assert len(_issuances(repo)) == len(issuances)
    assert not list((_store(repo) / "attempts").glob("*.refused.json"))


@pytest.mark.parametrize("point", KILL_POINTS)
def test_a_re_approval_start_killed_during_an_open_attempt_converges(
    reapproval_template: Path, tmp_path: Path, point: str
) -> None:
    repo = _copy(reapproval_template, tmp_path)
    h.commit_module.set_kill_hook(_crash_at(point))
    try:
        with pytest.raises(h.Crash):
            h.start(repo, "spec-plan")
    finally:
        h.commit_module.set_kill_hook(None)
    code, out = h.start(repo, "spec-plan")
    assert code == 0, out
    code, out = h.run_cli(repo, "next", SPEC)
    assert code == 0 and out.get("terminal") is True, out
    steps = _steps(repo)
    assert steps.count("approval:2") == 1
    assert len([s for s in steps if s.startswith("terminal:")]) == 1
    assert not list((_store(repo) / "attempts").glob("*.refused.json"))


def test_a_re_approval_start_refused_for_a_changed_trusted_file_fires_no_kill_point(
    implementer_template: Path, tmp_path: Path
) -> None:
    """The only other path a ``start`` can take during an open attempt makes no commit."""
    repo = _copy(implementer_template, tmp_path)
    _current_request(repo)
    fired: list[str] = []
    h.commit_module.set_kill_hook(fired.append)
    try:
        assert h.start(repo)[1]["status"] == "current"
        _forge_adr(repo)
        code, out = h.start(repo)
    finally:
        h.commit_module.set_kill_hook(None)
    assert code == 1 and out["refusal"]["code"] == "attempt-residue", out
    assert "0001-calculators-answer.md" in out["refusal"]["detail"]
    assert fired == []


# ── VI-5023: residue persists until restored; a refused edit is never committed ──


def test_residue_persists_until_every_path_is_restored(
    implementer_template: Path, tmp_path: Path
) -> None:
    repo = _copy(implementer_template, tmp_path)
    request = _current_request(repo)
    head, made = _head(repo), _made(repo)
    _forge_adr(repo)
    _forge_plan(repo)
    code, out = h.run_cli(repo, "next", SPEC)
    assert out["refusal"]["code"] == "attempt-residue"
    assert "plan.md" in out["refusal"]["detail"]
    assert "0001-calculators-answer.md" in out["refusal"]["detail"]
    _restore(repo, [f"{SPEC}/plan.md"])
    for _ in range(2):
        code, out = h.run_cli(repo, "next", SPEC)
        assert out["refusal"]["code"] == "attempt-residue"
        assert "plan.md" not in out["refusal"]["detail"]
        assert "0001-calculators-answer.md" in out["refusal"]["detail"]
    # A report is refused too, and a restored tree is not admitted without a re-issue.
    code, out = _report(repo, request)
    assert out["refusal"]["code"] == "attempt-residue"
    _restore(repo, ["docs/adr/0001-calculators-answer.md"])
    code, out = _report(repo, request)
    assert out["refusal"]["code"] == "attempt-residue"
    assert _current_request(repo)["request_id"] == request["request_id"]
    assert _head(repo) == head and _made(repo) == made, "a refused edit was committed"
    assert "replan" not in h.git(repo, "log", "--format=%s")
    assert _report(repo, request)[0] == 0


# ── VI-5025: rewrites and deleted caches ────────────────────────────────────


def _soft_reset(repo: Path) -> None:
    h.git(repo, "reset", "--soft", "HEAD~1")


def _amend(repo: Path) -> None:
    h.git(repo, "commit", "--amend", "--allow-empty", "-q", "-m", "amended")


def _copy_trailers(repo: Path) -> None:
    h.git(repo, "commit", "--allow-empty", "-q", "-C", "HEAD")


@pytest.mark.parametrize("rewrite", [_soft_reset, _amend, _copy_trailers])
def test_a_rewrite_or_a_commit_with_copied_trailers_refuses_the_attempt(
    implementer_template: Path, tmp_path: Path, rewrite: Callable[[Path], None]
) -> None:
    repo = _copy(implementer_template, tmp_path)
    request = _current_request(repo)
    result = h.Controller(repo, tmp_path / "effects.log").work(request)
    rewrite(repo)
    code, out = h.Controller(repo, tmp_path / "effects.log").report(result)
    assert code == 1, out
    assert out["refusal"]["code"] == "attempt-refused"
    assert "HEAD" in out["refusal"]["detail"]


def test_deleting_the_local_caches_neither_admits_a_forgery_nor_clears_residue(
    implementer_template: Path, tmp_path: Path
) -> None:
    repo = _copy(implementer_template, tmp_path)
    request = _current_request(repo)
    result = h.Controller(repo, tmp_path / "effects.log").work(request)
    _forge_plan(repo)
    _delete_local_caches(repo)
    code, out = h.Controller(repo, tmp_path / "effects.log").report(result)
    assert out["refusal"]["code"] == "attempt-refused"
    _delete_local_caches(repo)
    for _ in range(2):
        code, out = h.run_cli(repo, "next", SPEC)
        assert out["refusal"]["code"] == "attempt-residue"
        _delete_local_caches(repo)
    _restore(repo, _TRACKED["plan"])
    assert _current_request(repo)["request_id"] == request["request_id"]


# ── VI-5024: links, and an honest attempt ───────────────────────────────────


def _link(repo: Path, target: Path | str) -> None:
    (repo / "link.txt").symlink_to(target)


@pytest.mark.parametrize("where", ["outside", "trusted", "git"])
def test_a_link_in_the_change_set_is_refused(
    implementer_template: Path, tmp_path: Path, where: str
) -> None:
    repo = _copy(implementer_template, tmp_path)
    request = _current_request(repo)
    result = h.Controller(repo, tmp_path / "effects.log").work(request)
    target = {
        "outside": tmp_path,
        "trusted": repo / SPEC / "plan.md",
        "git": repo / ".git" / "config",
    }[where]
    _link(repo, target)
    made = _made(repo)
    code, out = h.Controller(repo, tmp_path / "effects.log").report(result)
    assert code == 1, out
    assert out["refusal"]["code"] == "unsafe-link"
    assert "link.txt" in out["refusal"]["detail"]
    assert _made(repo) == made


def test_a_link_inside_the_root_to_an_ordinary_file_is_admitted(
    implementer_template: Path, tmp_path: Path
) -> None:
    repo = _copy(implementer_template, tmp_path)
    request = _current_request(repo)
    result = h.Controller(repo, tmp_path / "effects.log").work(request)
    _link(repo, "README.md")
    # Admitted by the attempt checks; the stub-only rule is core's, not this check's.
    code, out = h.Controller(repo, tmp_path / "effects.log").report(result)
    assert out["refusal"]["code"] == "not-exactly-stub"


def test_an_honest_attempt_that_imports_the_installed_scripts_passes(
    implementer_template: Path, tmp_path: Path, skill: Path
) -> None:
    repo = _copy(implementer_template, tmp_path)
    request = _current_request(repo)
    result = h.Controller(repo, tmp_path / "effects.log").work(request)
    # Importing the installed scripts leaves bytecode beside them.
    cache = skill / "scripts" / "__pycache__"
    cache.mkdir()
    (cache / "_supervisor_loop.cpython-311.pyc").write_bytes(b"\0compiled")
    _delete_local_caches(repo)
    code, out = h.Controller(repo, tmp_path / "effects.log").report(result)
    assert code == 0, out
    assert out["admitted"] == "stub"
