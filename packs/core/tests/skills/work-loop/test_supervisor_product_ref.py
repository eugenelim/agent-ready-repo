"""The product ref: the run's result held in a protected Git ref.

VI-0511, VI-0512, VI-0513, VI-0514, VI-0516, VI-0518 and VI-0519 (the product-ref
contract), over real Git repositories driven through ``work-supervisor.py``.
Each test names the criterion it proves.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
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

pytestmark = sup.INTEGRATION

REPO_ROOT = Path(__file__).resolve().parents[5]
OWNER = "owner:0123456789ab"


# ── helpers ─────────────────────────────────────────────────────────────────


def git_ok(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env={**os.environ, **h.GIT_ENV},
        capture_output=True,
        text=True,
        check=False,
    )


def rev(repo: Path, name: str) -> str:
    done = git_ok(repo, "rev-parse", "--verify", "-q", name)
    return done.stdout.strip() if done.returncode == 0 else ""


def store_dir(repo: Path) -> Path:
    git_dir = Path(h.git(repo, "rev-parse", "--absolute-git-dir").strip())
    runs = [p for p in (git_dir / "agentbundle-supervisor").iterdir() if p.name.startswith("run-")]
    assert len(runs) == 1, runs
    return runs[0]


def record(repo: Path) -> dict[str, Any]:
    return json.loads((store_dir(repo) / "product-ref").read_text("utf-8"))  # type: ignore[no-any-return]


def ref_name(repo: Path) -> str:
    return str(record(repo)["name"])


def manifest(repo: Path, revision: str) -> dict[str, str]:
    out = h.git(repo, "ls-tree", "-r", revision)
    pairs = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        pairs[path] = meta.split()[2]
    return {p: o for p, o in pairs.items() if not p.startswith(h.SPEC_DIR + "/")}


def working_manifest(repo: Path) -> dict[str, str]:
    paths = [p for p in h.git(repo, "ls-files").splitlines() if not p.startswith(h.SPEC_DIR + "/")]
    return {p: h.git(repo, "hash-object", p).strip() for p in paths if (repo / p).exists()}


def assert_parity(repo: Path) -> None:
    name = ref_name(repo)
    assert rev(repo, name) == rev(repo, "HEAD")
    assert manifest(repo, "HEAD") == manifest(repo, name) == working_manifest(repo)


def started(tmp: Path) -> Path:
    repo = h.make_repo(tmp)
    code, out = h.start(repo)
    assert code == 0, out
    return repo


def advance(
    repo: Path, ctl: h.Controller, until: Callable[[dict[str, Any]], bool], *, after: bool = True
) -> dict[str, Any]:
    """Run ``next``, worker, ``report`` until a request matching *until*.

    With *after*, return once that request's result is reported (no attempt open);
    otherwise return the request itself, issued and open.
    """
    for _ in range(100):
        code, payload = h.run_cli(repo, "next", h.SPEC_DIR)
        assert code == 0, payload
        request = payload["request"]
        if until(request) and not after:
            return request  # type: ignore[no-any-return]
        if request["kind"] == "external-effect":
            ctl.handle_effect(request)
            continue
        result = ctl.query(request) if request["kind"] == "effect-query" else ctl.work(request)
        code, admitted = ctl.report(result)
        assert code == 0, admitted
        if until(request):
            return request  # type: ignore[no-any-return]
    raise AssertionError("the run did not reach the request")


def calc_implement(request: dict[str, Any]) -> bool:
    return request["kind"] == "implement-task" and request["task"]["title"].startswith("Calc")


def controller(repo: Path, tmp: Path, **kw: Any) -> h.Controller:
    return h.Controller(repo, tmp / "effects.log", **kw)


def decision_result(request: dict[str, Any], commit: str, role: str = OWNER) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "request_id": request["request_id"],
        "run_id": request["run_id"],
        "kind": "human-decision",
        "decision": {"decision": "adopt-history", "authority_ref": role, "commit": commit},
    }


def next_ok(repo: Path) -> dict[str, Any]:
    code, payload = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 0, payload
    return payload


def next_refusal(repo: Path) -> dict[str, Any]:
    code, payload = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 1, payload
    return payload["refusal"]  # type: ignore[no-any-return]


def security_lines(repo: Path) -> list[dict[str, Any]]:
    path = repo / h.SPEC_DIR / ".supervisor" / "security-events.jsonl"
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]


def foreign_commit(repo: Path, name: str = "OTHER.md", text: str = "foreign\n") -> str:
    (repo / name).parent.mkdir(parents=True, exist_ok=True)
    (repo / name).write_text(text, **h._LF)
    h.git(repo, "add", name)
    h.git(repo, "commit", "-q", "-m", f"foreign change to {name}")
    return rev(repo, "HEAD")


def make_legacy(repo: Path) -> None:
    """The state of a run admitted before the product ref shipped: no recorded ref."""
    name = ref_name(repo)
    h.git(repo, "update-ref", "-d", name)
    (store_dir(repo) / "product-ref").unlink()


# ── VI-0511: AC-0001, AC-0002 ───────────────────────────────────────────────


def test_start_creates_the_product_ref_at_the_approval_commit(tmp_path: Path) -> None:
    repo = started(tmp_path)
    name = ref_name(repo)
    assert name.startswith("refs/agentbundle/delivery/run-")
    assert name.endswith("/product")
    assert rev(repo, name) == rev(repo, "HEAD")
    assert record(repo)["recorded"] == rev(repo, "HEAD")
    assert h.git(repo, "symbolic-ref", "HEAD").strip() == "refs/heads/main"
    assert f"Supervisor-Product-Ref: {name}" in h.git(repo, "log", "-1", "--format=%B")


def test_every_step_moves_both_refs_and_keeps_head_on_its_branch(tmp_path: Path) -> None:
    repo = started(tmp_path)
    checked: list[str] = []

    def between(c: h.Controller, request: dict[str, Any], phase: str) -> None:
        if phase == "reported":
            assert_parity(repo)
            assert h.git(repo, "symbolic-ref", "HEAD").strip() == "refs/heads/main"
            checked.append(request["kind"])

    assert controller(repo, tmp_path, between=between).drive().get("terminal")
    assert len(checked) >= 8
    assert_parity(repo)


def test_two_worktrees_and_a_readmission_name_different_refs(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    wt = tmp_path / "wt"
    h.git(repo, "worktree", "add", "-q", "-b", "other", str(wt))
    assert h.start(repo)[0] == 0
    assert h.start(wt)[0] == 0
    first, second = ref_name(repo), ref_name(wt)
    assert first != second
    assert first.split("/")[3] == second.split("/")[3]  # one spec and commit, one run id
    # A run re-admitted after its store is retired draws a fresh name.
    h.git(repo, "reset", "-q", "--hard", "HEAD~1")
    shutil.rmtree(Path(h.git(repo, "rev-parse", "--absolute-git-dir").strip())
                  / "agentbundle-supervisor")
    assert h.start(repo)[0] == 0
    assert ref_name(repo) not in (first, second)


# ── VI-0512: AC-0003, AC-0004 ───────────────────────────────────────────────


def test_a_moved_product_ref_refuses_with_integration_conflict(tmp_path: Path) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    request = advance(repo, ctl, calc_implement, after=False)
    name = ref_name(repo)
    source = rev(repo, name)
    result = ctl.work(request)
    tree = h.git(repo, "rev-parse", "HEAD^{tree}").strip()
    child = h.git(repo, "commit-tree", tree, "-p", source, "-m", "racing writer").strip()
    delivery = {p.name: p.read_bytes() for p in (repo / h.SPEC_DIR / "delivery").iterdir()}
    index = h.git(repo, "ls-files", "-s")
    moved: list[bool] = []

    def hook() -> None:
        if not moved:
            moved.append(True)
            h.git(repo, "update-ref", name, child)

    h.commit_module.set_update_hook(hook)
    try:
        code, payload = ctl.report(result)
    finally:
        h.commit_module.set_update_hook(None)
    assert code == 1 and payload["refusal"]["code"] == "integration-conflict", payload
    assert rev(repo, "HEAD") == source
    assert rev(repo, name) == child
    assert h.git(repo, "ls-files", "-s") == index
    assert delivery == {p.name: p.read_bytes() for p in (repo / h.SPEC_DIR / "delivery").iterdir()}
    kept = (repo / "calc.py").read_bytes()
    # The attempt stands as residue until the ref is restored.
    assert next_refusal(repo)["code"] == "attempt-residue"
    h.git(repo, "update-ref", name, source)
    again = next_ok(repo)["request"]
    assert again["request_id"] == request["request_id"]
    assert (repo / "calc.py").read_bytes() == kept
    code, admitted = ctl.report(ctl.work(again))
    assert code == 0, admitted
    assert h.git(repo, "show", "HEAD:calc.py").encode() == kept
    assert_parity(repo)


# ── VI-0513: AC-0005, AC-0006, AC-0022 ──────────────────────────────────────


def _hostile(repo: Path, name: str) -> None:
    """A loose ref holding text a worker chose, which a refusal must never echo."""
    ref = Path(h.git(repo, "rev-parse", "--git-common-dir").strip())
    ref = (repo / ref if not ref.is_absolute() else ref).joinpath(*name.split("/"))
    ref.write_text("ref: refs/heads/evil\x1b[31mred\n", "utf-8")


def _duplicate_packed(repo: Path, name: str) -> None:
    h.git(repo, "pack-refs", "--all", "--prune")
    packed = repo / ".git" / "packed-refs"
    lines = packed.read_text("utf-8").splitlines()
    at = next(i for i, x in enumerate(lines) if x.endswith(name))
    lines.insert(at, lines[at])  # adjacent, so the file stays sorted for Git
    packed.write_text("\n".join(lines) + "\n", "utf-8")


def _diverge_cases(repo: Path, name: str, older: str) -> dict[str, Callable[[], None]]:
    tree = h.git(repo, "rev-parse", "HEAD^{tree}").strip()
    return {
        "deleted": lambda: h.git(repo, "update-ref", "-d", name),
        "symbolic": lambda: h.git(repo, "symbolic-ref", name, "refs/heads/main"),
        "rolled-back": lambda: h.git(repo, "update-ref", name, older),
        "planted": lambda: h.git(
            repo, "update-ref", name,
            h.git(repo, "commit-tree", tree, "-m",
                  f"forged\n\nSupervisor-Run: x\nSupervisor-Product-Ref: {name}").strip()),
        "hostile": lambda: _hostile(repo, name),
        "duplicate-packed": lambda: _duplicate_packed(repo, name),
    }


def _ref_and_store_snapshot(repo: Path) -> tuple[str, dict[str, bytes]]:
    refs = git_ok(repo, "for-each-ref", "--format=%(refname) %(objectname)").stdout
    store = {p.name: p.read_bytes() for p in store_dir(repo).iterdir() if p.is_file()}
    return refs + rev(repo, "HEAD"), store


def run_printed_restore(repo: Path, detail: str) -> None:
    """Run exactly the restore command a refusal prints."""
    command = detail.split("restore it with: ", 1)[1]
    assert "--no-deref" in command
    done = subprocess.run(command, shell=True, cwd=repo, env={**os.environ, **h.GIT_ENV},
                          capture_output=True, text=True, check=False)
    assert done.returncode == 0, (command, done.stderr)


def run_json(repo: Path) -> dict[str, Any]:
    return json.loads(  # type: ignore[no-any-return]
        (repo / h.SPEC_DIR / ".supervisor" / "run.json").read_text("utf-8"))


def assert_refused_shape(repo: Path, code: str) -> None:
    """``run.json`` and ``status`` both show the refusal, as the corpus checks it."""
    run = run_json(repo)
    assert run["stage"] == "awaiting-human" and run["active"] is True
    assert run["refusal"]["code"] == code
    status_code, status = h.run_cli(repo, "status", h.SPEC_DIR, "--json")
    assert status_code == 0
    assert status["refusal"]["code"] == code and status["terminal"] is False
    assert status["run"]["stage"] == "awaiting-human"


@pytest.fixture(scope="module")
def effect_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A run with no attempt open and an external-effect request issued, kept in a file."""
    base = tmp_path_factory.mktemp("effect")
    repo = started(base)
    ctl = controller(repo, base)
    for _ in range(40):
        request = next_ok(repo)["request"]
        if request["kind"] == "external-effect":
            (base / "effect-request.json").write_text(json.dumps(request), "utf-8")
            return base
        code, admitted = ctl.report(ctl.work(request))
        assert code == 0, admitted
        follow = admitted.get("admitted")
        if isinstance(follow, dict) and "request" in follow:
            (base / "effect-request.json").write_text(json.dumps(follow["request"]), "utf-8")
            return base
    raise AssertionError("no effect request")


def effect_copy(template: Path, tmp_path: Path) -> Path:
    shutil.copytree(template / "repo", tmp_path / "repo", symlinks=True)
    shutil.copyfile(template / "effect-request.json", tmp_path / "effect-request.json")
    return tmp_path / "repo"


def effect_verbs(repo: Path, tmp_path: Path) -> dict[str, Callable[[], tuple[int, dict[str, Any]]]]:
    """Every committing verb but ``next``, each with a well-formed argument for this run."""
    ctl = controller(repo, tmp_path)
    request = json.loads((repo.parent / "effect-request.json").read_text("utf-8"))
    result = tmp_path / "result.json"
    result.write_text(json.dumps(ctl.dispatch(request)), "utf-8")
    key = request["effect"]["operation_key"]
    return {
        "start": lambda: h.start(repo),
        "report": lambda: h.run_cli(repo, "report", h.SPEC_DIR, str(result)),
        "resolve-effect": lambda: h.run_cli(
            repo, "resolve-effect", h.SPEC_DIR, "--operation", key, "--decision",
            "effect-confirmed", "--authority-ref", "effect-authority:0123456789ab"),
    }


ALL_CASES = ["deleted", "symbolic", "rolled-back", "planted", "hostile", "duplicate-packed"]


@pytest.mark.parametrize("case", ALL_CASES)
def test_an_untrusted_product_ref_refuses_next_until_restored(tmp_path: Path, case: str) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    older = rev(repo, "HEAD")
    advance(repo, ctl, calc_implement)
    name, recorded = ref_name(repo), record(repo)["recorded"]
    head = rev(repo, "HEAD")
    _diverge_cases(repo, name, older)[case]()
    seen = rev(repo, name)
    before = len(security_lines(repo))
    refusal = next_refusal(repo)
    assert refusal["code"] == "product-ref-diverged" and refusal["owner"] == "controller"
    assert name in refusal["detail"] and recorded in refusal["detail"]
    assert "git update-ref" in refusal["detail"] and "None" not in refusal["detail"]
    assert "evil" not in refusal["detail"] and "\x1b" not in refusal["detail"]
    assert rev(repo, name) == seen and rev(repo, "HEAD") == head
    denied = [e for e in security_lines(repo)[before:] if e["reason_code"] == "product-ref-diverged"]
    assert denied and denied[0]["event_type"] == "supervisor-product-ref-check"
    assert_refused_shape(repo, "product-ref-diverged")
    run_printed_restore(repo, refusal["detail"])
    assert rev(repo, name) == recorded
    assert "request" in next_ok(repo)


@pytest.mark.parametrize("verb", ["start", "report", "resolve-effect"])
@pytest.mark.parametrize("case", ["deleted", "symbolic", "rolled-back", "planted"])
def test_an_untrusted_product_ref_refuses_the_other_verbs(
    effect_template: Path, tmp_path: Path, case: str, verb: str
) -> None:
    repo = effect_copy(effect_template, tmp_path)
    name, recorded = ref_name(repo), record(repo)["recorded"]
    older = h.git(repo, "rev-list", "--max-parents=0", "HEAD").strip()
    calls = effect_verbs(repo, tmp_path)
    _diverge_cases(repo, name, older)[case]()
    seen, head = rev(repo, name), rev(repo, "HEAD")
    before = len(security_lines(repo))
    code, out = calls[verb]()
    assert code == 1 and out["refusal"]["code"] == "product-ref-diverged", out
    assert name in out["refusal"]["detail"] and recorded in out["refusal"]["detail"]
    assert rev(repo, name) == seen and rev(repo, "HEAD") == head
    assert any(e["reason_code"] == "product-ref-diverged" for e in security_lines(repo)[before:])
    status_code, status = h.run_cli(repo, "status", h.SPEC_DIR, "--json")
    assert status_code == 0 and status["refusal"]["code"] == "product-ref-diverged"
    run_printed_restore(repo, out["refusal"]["detail"])
    assert rev(repo, name) == recorded
    assert calls[verb]()[0] == 0


@pytest.mark.parametrize("ref_less", [False, True])
@pytest.mark.parametrize("verb", ["start", "report", "resolve-effect", "next"])
def test_foreign_history_blocks_every_committing_verb(
    effect_template: Path, tmp_path: Path, verb: str, ref_less: bool
) -> None:
    repo = effect_copy(effect_template, tmp_path)
    calls = effect_verbs(repo, tmp_path)
    if ref_less:
        make_legacy(repo)
    top = foreign_commit(repo)
    made = (store_dir(repo) / "made-commits").read_text("utf-8")
    if verb == "next":
        request = next_ok(repo)["request"]
        assert request["reason"] == "history-adoption"
    elif verb == "start":
        code, out = h.run_cli(
            repo, "start", h.SPEC_DIR, "--intent", "code", "--code-trust", "untrusted",
            "--authority-ref", OWNER, "--review-authority-ref", "plan-reviewer:0123456789ab")
        assert code == 1 and out["refusal"]["code"] == "history-adoption-required", out
    else:
        code, out = calls[verb]()
        assert code == 1 and out["refusal"]["code"] == "history-adoption-required", out
    assert rev(repo, "HEAD") == top
    assert (store_dir(repo) / "made-commits").read_text("utf-8") == made
    if ref_less:
        assert not (store_dir(repo) / "product-ref").exists()
    else:
        assert rev(repo, ref_name(repo)) != top
    before = _ref_and_store_snapshot(repo)
    status_code, status = h.run_cli(repo, "status", h.SPEC_DIR, "--json")
    assert status_code == 0 and status["terminal"] is False
    assert status["request"]["reason"] == "history-adoption"
    assert status["request"]["head_commit"] == top
    assert status["run"]["gate_pending"] is True
    assert _ref_and_store_snapshot(repo) == before, "status changed a ref or a store file"


@pytest.mark.parametrize("verb", ["start", "report", "resolve-effect"])
def test_a_run_with_no_ref_gains_one_at_every_verb(
    effect_template: Path, tmp_path: Path, verb: str
) -> None:
    repo = effect_copy(effect_template, tmp_path)
    calls = effect_verbs(repo, tmp_path)
    make_legacy(repo)
    code, out = calls[verb]()
    assert code == 0, out
    assert rev(repo, ref_name(repo)) == record(repo)["recorded"] == rev(repo, "HEAD")
    assert_parity(repo)


def test_a_step_committed_during_a_ref_less_attempt_creates_no_ref(tmp_path: Path) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    request = advance(repo, ctl, calc_implement, after=False)
    make_legacy(repo)
    code, admitted = ctl.report(ctl.work(request))
    assert code == 0, admitted
    assert not (store_dir(repo) / "product-ref").exists()
    assert not git_ok(repo, "for-each-ref", "refs/agentbundle").stdout.strip()
    assert "request" in next_ok(repo)  # the attempt is closed now: the next verb creates it
    assert rev(repo, ref_name(repo)) == rev(repo, "HEAD")


def test_a_run_with_no_ref_gains_one_at_its_latest_made_commit(tmp_path: Path) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    make_legacy(repo)
    head = rev(repo, "HEAD")
    assert "request" in next_ok(repo)
    assert record(repo)["recorded"] == head == rev(repo, ref_name(repo))
    assert_parity(repo)


def test_a_run_with_no_ref_and_foreign_history_asks_before_adopting(tmp_path: Path) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    advance(repo, ctl, calc_implement)
    make_legacy(repo)
    top = foreign_commit(repo)
    request = next_ok(repo)["request"]
    assert request["kind"] == "human-decision" and request["reason"] == "history-adoption"
    assert request["head_commit"] == top
    assert request["changed_paths"] == ["OTHER.md"] and request["changed_path_count"] == 1
    assert request["spec_dir_changed"] is False
    assert rev(repo, "HEAD") == top
    assert not (store_dir(repo) / "product-ref").exists()
    code, admitted = ctl.report(decision_result(request, top))
    assert code == 0, admitted
    assert rev(repo, ref_name(repo)) == rev(repo, "HEAD") != top
    assert "Supervisor-Operation: reanchor" in h.git(repo, "log", "-1", "--format=%B")
    assert controller(repo, tmp_path).drive().get("terminal")


def test_foreign_history_that_touches_delivery_is_refused_adoption(tmp_path: Path) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    advance(repo, ctl, calc_implement)
    make_legacy(repo)
    top = foreign_commit(repo, f"{h.SPEC_DIR}/delivery/review-decisions.jsonl", "{}\n")
    request = next_ok(repo)["request"]
    code, payload = ctl.report(decision_result(request, top))
    assert code == 1 and payload["refusal"]["code"] == "adoption-refused"
    assert payload["refusal"]["owner"] == "controller"
    assert rev(repo, "HEAD") == top


def test_a_run_with_no_ref_reset_to_an_older_made_commit_projects_forward(tmp_path: Path) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    latest = rev(repo, "HEAD")
    make_legacy(repo)
    h.git(repo, "reset", "-q", "--hard", "HEAD~2")
    assert "request" in next_ok(repo)
    assert rev(repo, "HEAD") == latest == rev(repo, ref_name(repo))
    assert_parity(repo)


def test_a_run_with_no_ref_whose_foreign_commit_is_reset_away_gains_its_ref(
    tmp_path: Path,
) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    latest = rev(repo, "HEAD")
    make_legacy(repo)
    foreign_commit(repo)
    assert next_ok(repo)["request"]["reason"] == "history-adoption"
    h.git(repo, "reset", "-q", "--hard", latest)
    assert next_ok(repo)["request"]["kind"] != "human-decision"
    assert rev(repo, ref_name(repo)) == latest


def test_reftable_repositories_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    probe = subprocess.run(["git", "init", "-q", "--ref-format=reftable", str(tmp_path / "p")],
                           capture_output=True, check=False)
    if probe.returncode != 0:
        pytest.skip("this Git cannot create a reftable repository")
    monkeypatch.setenv("GIT_DEFAULT_REF_FORMAT", "reftable")
    repo = h.make_repo(tmp_path / "r")
    code, out = h.start(repo)
    assert code == 1 and out["refusal"]["code"] == "unsupported-ref-storage"
    assert out["refusal"]["owner"] == "owner"
    assert not git_ok(repo, "for-each-ref", "refs/agentbundle").stdout.strip()


def test_a_repository_that_gains_reftable_refuses_every_verb_but_status(tmp_path: Path) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    request = advance(repo, ctl, calc_implement, after=False)
    name = ref_name(repo)
    seen = rev(repo, name)
    path = repo / ".git" / "config"
    original = path.read_text("utf-8")
    path.write_text(original.replace("repositoryformatversion = 0",
                                      "repositoryformatversion = 1")
                    + "[extensions]\n\trefStorage = reftable\n", "utf-8")
    try:
        result = tmp_path / "result.json"
        result.write_text(json.dumps(ctl.work(request)), "utf-8")
        for argv in (("next", h.SPEC_DIR), ("report", h.SPEC_DIR, str(result)),
                     ("resolve-effect", h.SPEC_DIR, "--operation", "x", "--decision",
                      "effect-confirmed", "--authority-ref", "effect-authority:0123456789ab")):
            code, out = h.run_cli(repo, *argv)
            assert code == 1 and out["refusal"]["code"] == "unsupported-ref-storage", out
        code, out = h.run_cli(repo, "status", h.SPEC_DIR)
        assert code == 0 and out["refusal"]["code"] == "unsupported-ref-storage"
    finally:
        path.write_text(original, "utf-8")
    assert rev(repo, name) == seen


# ── VI-0514: AC-0008, AC-0009, AC-0010 ──────────────────────────────────────


@pytest.mark.parametrize("mode", ["hard", "soft", "mixed"])
def test_a_reset_two_steps_back_converges_to_the_ref(tmp_path: Path, mode: str) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    latest = rev(repo, "HEAD")
    h.git(repo, "reset", "-q", f"--{mode}", "HEAD~2")
    assert rev(repo, "HEAD") != latest
    assert "request" in next_ok(repo)
    assert rev(repo, "HEAD") == latest == rev(repo, ref_name(repo))
    assert_parity(repo)
    assert h.git(repo, "diff", "HEAD", "--stat", "--", ".", ":!.loop-run").strip() == ""


def test_a_reset_plus_an_edit_is_blocked_and_leaves_the_edit(tmp_path: Path) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    latest = rev(repo, "HEAD")
    h.git(repo, "reset", "-q", "--hard", "HEAD~2")
    (repo / "calc.py").write_text("# mine\n", **h._LF)
    index = h.git(repo, "ls-files", "-s")
    head = rev(repo, "HEAD")
    refusal = next_refusal(repo)
    assert refusal["code"] == "projection-blocked" and refusal["owner"] == "controller"
    assert "calc.py" in refusal["detail"]
    assert (repo / "calc.py").read_text("utf-8") == "# mine\n"
    assert_refused_shape(repo, "projection-blocked")
    assert h.git(repo, "ls-files", "-s") == index
    assert rev(repo, "HEAD") == head and rev(repo, ref_name(repo)) == latest


@pytest.mark.parametrize("moved", ["head", "ref"])
@pytest.mark.parametrize("attempt_open", [False, True])
def test_a_partial_transaction_completes(tmp_path: Path, moved: str, attempt_open: bool) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    if attempt_open:
        request = advance(repo, ctl, calc_implement, after=False)
        result = ctl.work(request)
    else:
        advance(repo, ctl, calc_implement)
        # A controller's edit to the spec is committed by ``next`` as a replan step.
        spec = repo / h.SPEC_DIR / "spec.md"
        spec.write_text(spec.read_text("utf-8").replace("that answers.", "that answers fast."),
                        **h._LF)
        request = None
    before_head, name = rev(repo, "HEAD"), ref_name(repo)

    def hook(point: str) -> None:
        if point == "pending-recorded":
            raise h.Crash(point)

    h.commit_module.set_kill_hook(hook)
    try:
        with pytest.raises(h.Crash):
            if request is not None:
                ctl.report(result)
            else:
                h.run_cli(repo, "next", h.SPEC_DIR)
    finally:
        h.commit_module.set_kill_hook(None)
    pending = record(repo)["pending"]
    assert pending and pending != before_head
    h.git(repo, "update-ref", "HEAD" if moved == "head" else name, pending)
    next_ok(repo)
    assert rev(repo, "HEAD") == rev(repo, name) != before_head
    assert record(repo)["pending"] is None
    assert_parity(repo)


# ── VI-0516: AC-0011, AC-0012, AC-0013, AC-0014 ─────────────────────────────


def _rebase(repo: Path) -> None:
    root = h.git(repo, "rev-list", "--max-parents=0", "HEAD").strip()
    h.git(repo, "checkout", "-q", "-b", "upstream", root)
    (repo / "UPSTREAM.md").write_text("upstream\n", **h._LF)
    h.git(repo, "add", "UPSTREAM.md")
    h.git(repo, "commit", "-q", "-m", "unrelated upstream change")
    h.git(repo, "checkout", "-q", "main")
    h.git(repo, "rebase", "-q", "upstream")


def _amend(repo: Path) -> None:
    with (repo / "calc.py").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("# edited\n")
    h.git(repo, "commit", "-q", "-a", "--amend", "--no-edit")


def _on_top(repo: Path) -> None:
    foreign_commit(repo)


@pytest.mark.parametrize("divert", [_rebase, _amend, _on_top])
def test_foreign_history_asks_then_adopts_once(tmp_path: Path, divert: Callable[[Path], None]) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    advance(repo, ctl, calc_implement)
    name = ref_name(repo)
    ref_before = rev(repo, name)
    divert(repo)
    top = rev(repo, "HEAD")
    request = next_ok(repo)["request"]
    assert request["reason"] == "history-adoption" and request["head_commit"] == top
    assert request["changed_path_count"] == len(request["changed_paths"]) >= 1
    assert rev(repo, "HEAD") == top and rev(repo, name) == ref_before
    if divert is _amend:
        assert "edited" not in h.git(repo, "show", f"{name}:calc.py")
    # Wrong commit and wrong role refuse and commit nothing.
    for bad in (decision_result(request, ref_before),
                decision_result(request, top, "plan-reviewer:0123456789ab")):
        code, payload = ctl.report(bad)
        assert code == 1 and payload["refusal"]["code"] == "adoption-refused"
        assert rev(repo, "HEAD") == top and rev(repo, name) == ref_before
    code, admitted = ctl.report(decision_result(request, top))
    assert code == 0, admitted
    assert rev(repo, name) == rev(repo, "HEAD") != top
    assert "Supervisor-Reanchor-From" in h.git(repo, "log", "-1", "--format=%B")
    assert next_ok(repo)["request"].get("reason") != "history-adoption"
    assert controller(repo, tmp_path).drive().get("terminal")


@pytest.mark.parametrize("change", ["product", "spec"])
def test_a_reanchor_that_changes_the_manifest_or_spec_discards_older_evidence(
    tmp_path: Path, change: str
) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    gates = advance(repo, ctl, lambda r: r["kind"] == "run-gates")
    if change == "product":
        _amend(repo)
    else:
        spec = repo / h.SPEC_DIR / "spec.md"
        spec.write_text(spec.read_text("utf-8").replace("that answers.", "that answers fast."),
                        **h._LF)
        h.git(repo, "commit", "-q", "-a", "-m", "controller edit")
    top = rev(repo, "HEAD")
    request = next_ok(repo)["request"]
    assert request["reason"] == "history-adoption"
    assert request["spec_dir_changed"] is (change == "spec")
    code, admitted = ctl.report(decision_result(request, top))
    assert code == 0, admitted
    again = next_ok(repo)["request"]
    assert again["kind"] == "run-gates" and again["request_id"] != gates["request_id"]


# ── VI-0518: AC-0020 ────────────────────────────────────────────────────────


@pytest.mark.parametrize("value", [None, "other"])
def test_start_refuses_an_invalid_result_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    policy = json.loads(h.admission._POLICY_PATH.read_text("utf-8"))
    assert policy["result_authority"] == "legacy-worktree"
    if value is None:
        del policy["result_authority"]
    else:
        policy["result_authority"] = value
    path = tmp_path / "supervisor-policy.json"
    path.write_text(json.dumps(policy), "utf-8")
    monkeypatch.setattr(h.admission, "_POLICY_PATH", path)
    repo = h.make_repo(tmp_path)
    code, out = h.start(repo)
    assert code == 1
    assert out["refusal"]["code"] == "invalid-policy"
    assert out["refusal"]["owner"] == "skill maintainer"


# ── VI-0519: AC-0021 ────────────────────────────────────────────────────────


def _workflow(name: str) -> str:
    path = REPO_ROOT / ".github" / "workflows" / name
    if not path.exists():
        pytest.skip("the repository's workflows are not part of this checkout")
    return path.read_text("utf-8")


def test_the_ci_jobs_list_the_product_ref_suites() -> None:
    posix = _workflow("catalogue-tooling-ci-gates.yml")
    assert "test_supervisor_product_ref.py" in posix
    windows = _workflow("build-check-windows.yml")
    job = windows.split("\n  supervisor-product-ref-windows:")[1].split("\n  build-check-windows:")[0]
    for suite in ("test_supervisor_product_ref.py", "test_supervisor_attempt.py",
                  "test_supervisor_pinning.py"):
        assert suite in job
    # The integration variable and the job's own time budget sit on the job that runs them.
    assert 'WORK_SUPERVISOR_INTEGRATION: "1"' in job
    assert "timeout-minutes:" in job
    assert "supervisor-product-ref-windows" in windows.split("\n  build-check-windows:")[1]


CORPUS = Path(__file__).resolve().parent / "test_supervisor_crash_corpus.py"


def _collect(selector: str | None) -> list[str]:
    """The corpus test ids pytest collects with *selector*, as the CI shard would."""
    ids: list[str] = []

    class Collect:
        def pytest_collection_finish(self, session: Any) -> None:
            # After ``-k`` has deselected: what the CI shard would run.
            ids.extend(item.nodeid for item in session.items)

    args = [str(CORPUS), "--collect-only", "-q", "-p", "no:cacheprovider"]
    if selector is not None:
        args += ["-k", selector]
    assert pytest.main(args, plugins=[Collect()]) in (0, 5)
    return ids


def test_the_crash_corpus_shards_are_disjoint_nonempty_and_cover_every_test() -> None:
    posix = _workflow("catalogue-tooling-ci-gates.yml")
    job = posix.split("\n  supervisor-integration:")[1].split("\n  # ── Gate B")[0]
    selectors = re.findall(r'selector: "([^"]+)"', job)
    assert len(selectors) == 3, selectors
    everything = _collect(None)
    shards = [_collect(selector) for selector in selectors]
    assert all(shards), [len(shard) for shard in shards]
    flat = [item for shard in shards for item in shard]
    assert len(flat) == len(set(flat)), "two shards run the same test"
    assert sorted(flat) == sorted(everything), "a corpus test runs in no shard"


def _refused_build(repo: Path) -> tuple[str, str]:
    """Build a step whose transaction is refused because ``HEAD`` moved under it.

    Returns the run id and the refused commit.
    """
    ws = h.workspace(repo)
    run_id = ws.approvals()[0]["run_id"]
    tree = h.git(repo, "rev-parse", "HEAD^{tree}").strip()
    base = rev(repo, "HEAD")
    other = h.git(repo, "commit-tree", tree, "-p", base, "-m", "a racing commit").strip()
    pending: list[str] = []

    def hook() -> None:
        if not pending:
            pending.append((store_dir(repo) / "pending-commit").read_text("utf-8").strip())
            h.git(repo, "update-ref", "refs/heads/main", other)

    h.commit_module.set_update_hook(hook)
    try:
        with pytest.raises(h.commit_module.SupervisorGitError):
            ws.git.build_commit(run_id=run_id, step="refused-step", operation="evidence",
                                summary="a step the race refuses")
    finally:
        h.commit_module.set_update_hook(None)
    h.git(repo, "update-ref", "refs/heads/main", base)  # the race is undone
    return run_id, pending[0]


def test_a_refused_commit_never_anchors_a_ref_less_run(tmp_path: Path) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    make_legacy(repo)
    base = rev(repo, "HEAD")
    run_id, refused = _refused_build(repo)
    assert refused not in (store_dir(repo) / "made-commits").read_text("utf-8")
    assert not (store_dir(repo) / "pending-commit").exists()
    assert refused not in h.workspace(repo).git.made_commits(run_id)
    assert "request" in next_ok(repo)  # a recovery verb: it creates the missing ref
    assert record(repo)["recorded"] == base, "the refused commit anchored the run"
    assert rev(repo, "HEAD") == base != refused
    assert rev(repo, ref_name(repo)) == base


@pytest.mark.parametrize("ref_less", [False, True])
@pytest.mark.parametrize("point", ["refs-moved", "made-recorded", "pending-recorded"])
def test_a_crash_around_the_move_converges(tmp_path: Path, ref_less: bool, point: str) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    if ref_less:
        make_legacy(repo)
    ws = h.workspace(repo)
    run_id = ws.approvals()[0]["run_id"]
    before = rev(repo, "HEAD")

    def hook(name: str) -> None:
        if name == point:
            raise h.Crash(name)

    h.commit_module.set_kill_hook(hook)
    try:
        with pytest.raises(h.Crash):
            ws.git.build_commit(run_id=run_id, step="crashed-step", operation="evidence",
                                summary="cut off")
    finally:
        h.commit_module.set_kill_hook(None)
    moved = point != "pending-recorded"
    pending_file = store_dir(repo) / "pending-commit"
    assert (rev(repo, "HEAD") != before) is moved
    assert pending_file.exists() is (point != "made-recorded")
    step = rev(repo, "HEAD") if moved else pending_file.read_text("utf-8").strip()
    # A landed step counts as the supervisor's own before it is recorded; an unlanded one never does.
    assert (step in h.workspace(repo).git.made_commits(run_id)) is moved
    assert "request" in next_ok(repo)  # reconcile settles it first
    assert not pending_file.exists()
    assert (step in (store_dir(repo) / "made-commits").read_text("utf-8").split()) is moved
    assert rev(repo, "HEAD") == (step if moved else before)
    assert_parity(repo)
