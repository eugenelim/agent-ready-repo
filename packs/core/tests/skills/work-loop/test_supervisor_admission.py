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


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack- and skill-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        path = Path(__file__).resolve().parent / f"{name}.py"
        spec = importlib.util.spec_from_file_location(alias, path)
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
           reviewer: str = REVIEWER) -> tuple[int, dict]:
    return h.run_cli(repo, "start", h.SPEC_DIR, "--intent", intent, "--code-trust", "untrusted",
                     "--authority-ref", authority, "--review-authority-ref", reviewer)


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


@pytest.mark.parametrize("point", ["commit-built", "head-moved", "synced"])
def test_interrupted_start_leaves_no_partial_line_and_reruns(tmp_path: Path, point: str) -> None:
    repo = h.make_repo(tmp_path)

    def hook(name: str) -> None:
        if name == point:
            raise h.Crash(name)

    h.commit_module.set_kill_hook(hook)
    try:
        with pytest.raises(h.Crash):
            _start(repo)
    finally:
        h.commit_module.set_kill_hook(None)
    for line in _approval_lines(repo):
        assert set(line) >= {"approval", "initial_plan_review", "run_id"}
    working = repo / h.SPEC_DIR / "delivery" / "approvals.jsonl"
    committed = h.workspace(repo).git.show(f"{h.SPEC_DIR}/delivery/approvals.jsonl") or b""
    assert not working.exists() or committed.startswith(working.read_bytes())
    assert not (repo / h.SPEC_DIR / ".supervisor" / "journal.jsonl").exists()
    code, out = _start(repo)
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
    for name in ("engine-state.json", "state.json"):
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
    assert not [p for p in _OPENED if p.endswith(("engine-state.json", "/state.json"))]
