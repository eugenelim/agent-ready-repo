"""Start commits the approval pair atomically (T3).

VI-4020 (AC-0001, AC-0002), VI-4021 (AC-0003, AC-0004), VI-4022 (AC-0012),
VI-4023 (AC-0021).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

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
REVIEWER = "plan-reviewer:0123456789ab"


def _start(repo: Path, *, intent: str = "code", authority: str = OWNER,
           reviewer: str = REVIEWER, trust: str = "untrusted") -> tuple[int, dict]:
    return h.run_cli(repo, "start", h.SPEC_DIR, "--intent", intent, "--code-trust", trust,
                     "--authority-ref", authority, "--review-authority-ref", reviewer,
                     *h.digest_args(repo))


def _commits(repo: Path) -> list[str]:
    return h.git(repo, "log", "--format=%s").splitlines()


def _approval_lines(repo: Path, rev: str = "HEAD") -> list[dict]:
    raw = h.workspace(repo).git.show(f"{h.SPEC_DIR}/delivery/approvals.jsonl", rev) or b""
    return [json.loads(line) for line in raw.splitlines()]


# ── VI-4020: one commit, one line, bound to the run's facts ──────────────────


def test_clean_start_commits_exactly_one_bound_line(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    code, out = _start(repo)
    assert code == 0 and out["status"] == "admitted"
    assert len(_commits(repo)) == 2
    (line,) = _approval_lines(repo)
    pi = h.loop.sibling("_policy_import.py")
    assert pi.validate_approval_dict(line["approval"]) == (True, "ok")
    assert pi.validate_initial_review_dict(line["initial_plan_review"]) == (True, "ok")
    review = line["initial_plan_review"]
    assert review["envelope_fingerprint"] == line["envelope"]["envelope_fingerprint"]
    assert review["authorized_terminal_intent"] == line["terminal_intent"] == "code"
    assert line["code_trust"] == "untrusted"
    assert line["run_id"] == out["run_id"]
    assert line["approval"]["authority"]["identity"] == line["authority_ref"] == OWNER
    assert review["reviewer"]["identity"] == line["review_authority_ref"] == REVIEWER
    working = (repo / h.SPEC_DIR / "delivery" / "approvals.jsonl").read_bytes()
    assert working == h.workspace(repo).git.show(f"{h.SPEC_DIR}/delivery/approvals.jsonl")


def test_repeated_start_on_a_current_pair_is_a_no_op(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    _start(repo)
    code, out = _start(repo)
    assert code == 0 and out["status"] == "current"
    assert len(_approval_lines(repo)) == 1 and len(_commits(repo)) == 2


@pytest.mark.parametrize("point", ["commit-built", "refs-moved", "synced"])
def test_interrupted_start_leaves_no_partial_line_and_reruns(tmp_path: Path, point: str) -> None:
    repo = h.make_repo(tmp_path)

    def hook(name: str) -> None:
        if name == point:
            raise h.Crash(name)

    h.commit_module.set_kill_hook(hook)
    try:
        with pytest.raises(h.Crash):
            _start(repo, trust="trusted")
    finally:
        h.commit_module.set_kill_hook(None)
    for line in _approval_lines(repo):
        assert set(line) >= {"approval", "initial_plan_review", "run_id"}
    working = repo / h.SPEC_DIR / "delivery" / "approvals.jsonl"
    committed = h.workspace(repo).git.show(f"{h.SPEC_DIR}/delivery/approvals.jsonl") or b""
    assert not working.exists() or committed.startswith(working.read_bytes())
    assert not (repo / h.SPEC_DIR / ".supervisor" / "journal.jsonl").exists()
    code, out = _start(repo, trust="trusted")
    if point == "refs-moved":
        # The approval's refs moved and nothing recorded it: nothing counts it, and the
        # refusal names the exit that works.
        assert code == 1 and out["refusal"]["code"] == "supervisor-changed", out
        assert "git reset --soft" in out["refusal"]["detail"]
        h.git(repo, "reset", "-q", "--soft", "HEAD^")
        code, out = _start(repo, trust="trusted")
    assert code == 0, out
    code, payload = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 0 and payload["request"]["kind"] != "human-decision"
    assert len(_approval_lines(repo)) == 1


def test_refused_start_writes_no_line(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    code, out = _start(repo, intent="spec-plan")
    assert code == 1 and out["refusal"]["code"] == "intent-mismatch"
    assert _approval_lines(repo) == [] and len(_commits(repo)) == 1
    code, out = _start(repo)
    assert code == 0 and out["status"] == "admitted"


# ── VI-4021: statuses, intent, and authority references ──────────────────────


@pytest.mark.parametrize(("spec_status", "plan_status", "intent", "admitted"), [
    ("Approved", "Approved", "code", True),
    ("Implementing", "Executing", "code", True),
    ("Draft", "Approved", "code", False),
    ("Shipped", "Approved", "code", False),
    ("Approved", "Drafting", "code", False),
    ("Approved", "Done", "code", False),
    ("Approved", "Approved", "spec-plan", False),
])
def test_status_and_intent_table(tmp_path: Path, spec_status: str, plan_status: str,
                                 intent: str, admitted: bool) -> None:
    spec = sup.SPEC.replace("- **Status:** Approved", f"- **Status:** {spec_status}", 1)
    plan = sup.PLAN.replace("- **Status:** Approved", f"- **Status:** {plan_status}", 1)
    repo = h.make_repo(tmp_path, spec=spec, plan=plan)
    code, out = _start(repo, intent=intent)
    assert (code == 0) is admitted, out


def test_intent_is_free_when_the_spec_has_no_terminal_intent(tmp_path: Path) -> None:
    spec = sup.SPEC.replace("## Terminal Intent\n\n`code` — build the calculator.\n\n", "")
    repo = h.make_repo(tmp_path, spec=spec)
    assert _start(repo, intent="spec-plan")[0] == 0


@pytest.mark.parametrize(("authority", "reviewer", "accepted"), [
    (OWNER, REVIEWER, True),
    ("owner", "plan-reviewer", True),
    ("jdoe", REVIEWER, False),
    ("someone@example.invalid", REVIEWER, False),
    ("plan-reviewer:0123456789ab", REVIEWER, False),
    ("owner:0123", REVIEWER, False),
    ("owner:0123456789AB", REVIEWER, False),
    (OWNER, OWNER, False),
])
def test_authority_reference_bindings(tmp_path: Path, authority: str, reviewer: str,
                                      accepted: bool) -> None:
    repo = h.make_repo(tmp_path)
    code, out = _start(repo, authority=authority, reviewer=reviewer)
    assert (code == 0) is accepted, out
    if not accepted:
        assert out["refusal"]["code"] == "invalid-authority-ref"


# ── VI-4022: spec-plan ends after initial review ─────────────────────────────


def test_spec_plan_run_ends_with_approval_then_terminal(tmp_path: Path) -> None:
    spec = sup.SPEC.replace("`code` — build the calculator.", "`spec-plan` — stop at review.")
    repo = h.make_repo(tmp_path, spec=spec)
    base = h.git(repo, "rev-parse", "HEAD").strip()
    code, out = _start(repo, intent="spec-plan")
    assert code == 0 and out["status"] == "terminal"
    code, payload = h.run_cli(repo, "next", h.SPEC_DIR)
    assert payload.get("terminal") is True and "request" not in payload
    ws = h.workspace(repo)
    commits = ws.git.supervisor_commits(out["run_id"])
    assert [c.operation for c in commits] == ["approval", "terminal"]
    touched = h.git(repo, "diff", "--name-only", base, "HEAD").split()
    assert touched and all(p.startswith(f"{h.SPEC_DIR}/delivery/") for p in touched)
    journal = (repo / h.SPEC_DIR / ".supervisor" / "journal.jsonl").read_text("utf-8")
    assert all(json.loads(line)["kind"] == "terminal" for line in journal.splitlines())


# ── VI-4023: legacy state files are never opened ─────────────────────────────

_OPENED: list[str] = []
_AUDITING: list[bool] = [False]


def _audit(event: str, args: tuple) -> None:
    if _AUDITING[0] and event == "open" and args and isinstance(args[0], (str, bytes, Path)):
        _OPENED.append(str(args[0]))


sys.addaudithook(_audit)


def test_start_never_opens_legacy_state(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    # The legacy names a rollback reads; the run must never open either.
    legacy = ("engine-state.json", "state.json")
    for name in legacy:
        (repo / h.SPEC_DIR / name).write_text('{"legacy": true}\n', "utf-8")
    _OPENED.clear()
    _AUDITING[0] = True
    try:
        code, out = _start(repo)
        h.run_cli(repo, "next", h.SPEC_DIR)
    finally:
        _AUDITING[0] = False
    assert code == 0, out
    assert _OPENED, "the audit hook saw no opens"
    assert not [p for p in _OPENED if p.endswith(tuple("/" + n for n in legacy))]


# Checkout admission: real Git repositories, including linked worktrees.
_OTHER = "docs/specs/other"


def _checkout(tmp_path: Path, *, linked: bool = True) -> Path:
    """Create two approved specs before either run changes HEAD."""
    import shutil

    repo = h.make_repo(tmp_path)
    shutil.copytree(repo / h.SPEC_DIR, repo / _OTHER)
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-qm", "second spec")
    if not linked:
        return repo
    worktree = tmp_path / "linked"
    h.git(repo, "worktree", "add", "-qb", "isolated", str(worktree))
    return worktree


def _checkout_start(repo: Path, spec: str = h.SPEC_DIR, *, override: bool = False,
                    intent: str = "code") -> tuple[int, dict]:
    """Start through the CLI without the harness's primary-checkout default."""
    return h.run_cli(
        repo, "start", spec, "--intent", intent, "--code-trust", "trusted",
        "--authority-ref", OWNER, "--review-authority-ref", REVIEWER,
        *h.digest_args(repo, spec),
        *(["--allow-primary-checkout"] if override else []), allow_primary_checkout=False,
    )


def test_primary_checkout_requires_and_records_override(tmp_path: Path) -> None:
    """A refusal changes no run or ref; an explicit override is durable."""
    repo = _checkout(tmp_path, linked=False)
    before = h.git(repo, "show-ref")
    code, out = _checkout_start(repo)
    assert code == 1 and out["refusal"]["code"] == "checkout-not-isolated", out
    assert h.git(repo, "show-ref") == before
    assert not (repo / ".git" / "agentbundle-supervisor").exists()
    code, out = _checkout_start(repo, override=True)
    assert code == 0, out
    assert _approval_lines(repo)[0]["allow_primary_checkout"] is True


def test_linked_checkout_has_one_owner_and_status_warns(tmp_path: Path) -> None:
    """A different spec cannot take the checkout; status locates ephemeral state."""
    repo = _checkout(tmp_path)
    code, owner = _checkout_start(repo)
    assert code == 0, owner
    before = h.git(repo, "show-ref")
    code, out = _checkout_start(repo, _OTHER)
    assert code == 1 and out["refusal"]["code"] == "checkout-reserved", out
    assert owner["run_id"] in out["refusal"]["detail"]
    assert h.git(repo, "show-ref") == before
    assert not (repo / _OTHER / ".supervisor").exists()
    pins = h.workspace(repo).git.hardened.pins
    stores = list((pins.git_dir / "agentbundle-supervisor").glob("run-*"))
    assert len(stores) == 1
    code, out = h.run_cli(repo, "status", h.SPEC_DIR)
    assert code == 0, out
    assert out["run_store"] == str(stores[0])
    assert "removing the worktree discards" in out["worktree_removal_warning"].lower()


def test_terminal_checkout_can_be_reserved_by_another_spec(tmp_path: Path) -> None:
    """Terminal code runs release their checkout immediately."""
    repo = _checkout(tmp_path)
    assert _checkout_start(repo)[0] == 0
    assert h.Controller(repo, tmp_path / "effects.log").drive().get("terminal")
    path = h.admission._checkout_path(h.workspace(repo))
    assert json.loads(path.read_text("utf-8")) is None
    code, out = _checkout_start(repo)
    assert code == 0 and out["status"] == "current", out
    assert json.loads(path.read_text("utf-8")) is None
    code, out = _checkout_start(repo, _OTHER)
    assert code == 0, out


def test_absent_run_store_makes_checkout_reservation_stale(tmp_path: Path) -> None:
    """An absent store cannot retain checkout ownership."""
    repo = _checkout(tmp_path)
    assert _checkout_start(repo)[0] == 0
    pins = h.workspace(repo).git.hardened.pins
    store = next((pins.git_dir / "agentbundle-supervisor").glob("run-*"))
    store.rename(tmp_path / "removed-store")
    code, out = _checkout_start(repo, _OTHER)
    assert code == 0, out


def test_concurrent_starts_for_different_specs_leave_one_owner(tmp_path: Path) -> None:
    """Two real CLI processes contend for the same working-tree reservation."""
    import os
    import subprocess

    repo = _checkout(tmp_path)
    commands = [
        [sys.executable, str(sup.SCRIPTS / "work-supervisor.py"), "start", spec,
         "--intent", "code", "--code-trust", "trusted", "--authority-ref", OWNER,
         "--review-authority-ref", REVIEWER, *h.digest_args(repo, spec)]
        for spec in (h.SPEC_DIR, _OTHER)
    ]
    processes = [subprocess.Popen(command, cwd=repo, env={**os.environ, **h.GIT_ENV},
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                 for command in commands]
    results = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=90)
        assert not stderr, stderr
        results.append((process.returncode, json.loads(stdout)))
    assert sorted(code for code, _ in results) == [0, 1], results
    loser = next(out for code, out in results if code == 1)
    winner = next(out for code, out in results if code == 0)
    assert loser["refusal"]["code"] == "checkout-reserved", results
    assert winner["run_id"] in loser["refusal"]["detail"]
    refs = h.git(repo, "for-each-ref", "--format=%(refname)", "refs/agentbundle")
    assert len(refs.splitlines()) == 1, refs
    winner_commit = h.git(repo, "rev-parse", refs.strip()).strip()
    assert h.git(repo, "rev-parse", "HEAD").strip() == winner_commit
    winning_spec = next(spec for spec in (h.SPEC_DIR, _OTHER)
                        if (repo / spec / "delivery/approvals.jsonl").exists())
    approval = json.loads((repo / winning_spec / "delivery/approvals.jsonl").read_text())
    assert approval["run_id"] == winner["run_id"]
    ws = h.admission.Workspace(repo, winning_spec)
    assert ws.git.supervisor_commits(winner["run_id"])[-1].sha == winner_commit
    history = h.git(repo, "log", "--format=%H%x00%B", "--all")
    assert history.count("Supervisor-Operation: approval") == 1
    assert history.count("Supervisor-Run: " + winner["run_id"]) == 1
    assert h.git(repo, "rev-parse", refs.strip()).strip() == winner_commit
    pins = h.workspace(repo).git.hardened.pins
    assert len(list((pins.git_dir / "agentbundle-supervisor").glob("run-*"))) == 1


def test_primary_override_does_not_bypass_another_runs_reservation(tmp_path: Path) -> None:
    """The override changes isolation policy, never checkout ownership."""
    repo = _checkout(tmp_path, linked=False)
    code, owner = _checkout_start(repo, override=True)
    assert code == 0, owner
    code, out = _checkout_start(repo, _OTHER, override=True)
    assert code == 1 and out["refusal"]["code"] == "checkout-reserved", out
    assert owner["run_id"] in out["refusal"]["detail"]


def test_other_linked_worktree_has_independent_checkout_ownership(tmp_path: Path) -> None:
    """Two worktrees sharing one Git common directory can each own a run."""
    repo = _checkout(tmp_path)
    other = tmp_path / "another-linked"
    h.git(repo, "worktree", "add", "-qb", "another", str(other))
    assert _checkout_start(repo)[0] == 0
    code, out = _checkout_start(other, _OTHER)
    assert code == 0, out


def test_spec_plan_terminal_releases_checkout_reservation(tmp_path: Path) -> None:
    """A start that is itself terminal leaves no owner behind."""
    spec = sup.SPEC.replace("`code` — build the calculator.", "`spec-plan` — stop at review.")
    repo = h.make_repo(tmp_path, spec=spec)
    code, out = _checkout_start(repo, intent="spec-plan", override=True)
    assert code == 0 and out["status"] == "terminal", out
    path = h.admission._checkout_path(h.workspace(repo))
    assert json.loads(path.read_text("utf-8")) is None
    code, out = _checkout_start(repo, intent="spec-plan", override=True)
    assert code == 0 and out["status"] == "current", out
    assert json.loads(path.read_text("utf-8")) is None
