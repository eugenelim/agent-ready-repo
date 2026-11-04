"""`park`: record a waiting approval gate without touching Git or the working tree.

Each test drives the supervisor CLI on a throwaway Git repository.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

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

SPEC = sup.SPEC.replace("**Status:** Approved", "**Status:** Draft")
PLAN = sup.PLAN.replace("**Status:** Approved", "**Status:** Drafting")
NO_INTENT = "## Terminal Intent\n\n`code` — build the calculator.\n\n"
ZWSP = "​"


def _repo(tmp_path: Path, *, spec: str = SPEC, plan: str = PLAN) -> Path:
    return h.make_repo(tmp_path, spec=spec, plan=plan)


def _park(
    repo: Path,
    gate: str = "spec-approved",
    *,
    intent: str = "code",
    trust: str = "trusted",
    spec_dir: str = h.SPEC_DIR,
) -> tuple[int, dict[str, Any]]:
    return h.run_cli(
        repo, "park", spec_dir, "--gate", gate, "--intent", intent, "--code-trust", trust
    )


def _gates_dir(repo: Path) -> Path:
    return repo / ".git" / "agentbundle-supervisor" / "gates"


def _records(repo: Path) -> list[Path]:
    directory = _gates_dir(repo)
    return sorted(directory.iterdir()) if directory.is_dir() else []


def _record_name(spec_dir: str = h.SPEC_DIR) -> str:
    return hashlib.sha256(spec_dir.encode()).hexdigest()[:16] + ".json"


def _commit(repo: Path, message: str = "edit") -> None:
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", message)


def _edit(repo: Path, name: str, old: str, new: str) -> None:
    path = repo / h.SPEC_DIR / name
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new), **h._LF)


def _refused(repo: Path, code: str, *args: str, **kw: Any) -> dict[str, str]:
    before = _records(repo)
    exit_code, out = _park(repo, *args, **kw)
    assert exit_code == 1 and out["refusal"]["code"] == code, out
    assert out["refusal"]["owner"]
    assert _records(repo) == before
    return out["refusal"]


def _snapshot(repo: Path) -> dict[str, Any]:
    files = {}
    for path in sorted(repo.rglob("*")):
        rel = path.relative_to(repo).as_posix()
        if rel == ".git" or rel.startswith(".git/") or not path.is_file():
            continue
        files[rel] = path.read_bytes()
    return {
        "refs": h.git(repo, "for-each-ref"),
        "head": h.git(repo, "rev-parse", "HEAD"),
        "index": (repo / ".git" / "index").read_bytes(),
        "files": files,
    }


def _admit(repo: Path, intent: str = "code") -> None:
    code, out = h.start(repo, intent)
    assert code == 0, out


def test_t2_ac0001_park_writes_one_record(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    code, out = _park(repo)
    assert code == 0, out
    head = h.git(repo, "rev-parse", "HEAD").strip()
    assert out["status"] == "parked" and out["commit"] == head
    assert out["gate"] == "spec-approved" and out["spec_dir"] == h.SPEC_DIR
    assert out["intent"] == "code" and out["code_trust"] == "trusted"
    for key in ("spec_digest", "plan_digest"):
        assert len(out[key]) == 64
    (record,) = _records(repo)
    assert record.name == _record_name()
    body = json.loads(record.read_text(encoding="utf-8"))
    assert body == {"schema_version": 1, **{k: v for k, v in out.items() if k != "status"}}
    assert record.read_text(encoding="utf-8") == json.dumps(
        body, sort_keys=True, separators=(",", ":")
    ) + "\n"


def test_t2_ac0001_untrusted_and_spec_plan_are_recorded(tmp_path: Path) -> None:
    repo = _repo(tmp_path, spec=SPEC.replace(NO_INTENT, ""))
    code, out = _park(repo, intent="spec-plan", trust="untrusted")
    assert code == 0 and out["intent"] == "spec-plan" and out["code_trust"] == "untrusted", out


def test_t2_ac0002_park_changes_nothing_but_the_record(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "scratch.log").write_text("ignored\n", **h._LF)
    (repo / ".loop-run").mkdir()
    (repo / ".loop-run" / "x").write_text("ignored too\n", **h._LF)
    past = 1_000_000_000
    for name in ("spec.md", "plan.md"):
        os.utime(repo / h.SPEC_DIR / name, (past, past))  # stale index stat data
    before = _snapshot(repo)
    code, out = _park(repo)
    assert code == 0, out
    assert _snapshot(repo) == before
    code, out = _park(repo)  # the `current` path
    assert out["status"] == "current" and _snapshot(repo) == before
    _edit(repo, "plan.md", "Build it.", "Build it well.")
    before = _snapshot(repo)
    _refused(repo, "gate-uncommitted")
    assert _snapshot(repo) == before


def test_t2_ac0003_uncommitted_edit_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _edit(repo, "spec.md", "answers.", "answers it.")
    _refused(repo, "gate-uncommitted")


def test_t2_ac0003_staged_change_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _edit(repo, "plan.md", "Build it.", "Build it well.")
    h.git(repo, "add", "-A")  # index and working tree agree, HEAD differs
    _refused(repo, "gate-uncommitted")


def test_t2_ac0003_crlf_working_tree_of_an_lf_blob_parks(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    for name in ("spec.md", "plan.md"):
        path = repo / h.SPEC_DIR / name
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    code, out = _park(repo)
    assert code == 0 and out["status"] == "parked", out


def test_t2_ac0003_unmerged_entry_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    rel = f"{h.SPEC_DIR}/plan.md"
    blob = h.git(repo, "rev-parse", f"HEAD:{rel}").strip()
    entries = "".join(f"100644 {blob} {stage}\t{rel}\n" for stage in (1, 2, 3))
    subprocess.run(
        ["git", "update-index", "--index-info"],
        cwd=repo, input=f"0 {'0' * 40}\t{rel}\n{entries}", text=True, check=True,
        env={**os.environ, **h.GIT_ENV},
    )
    assert "\t" in h.git(repo, "ls-files", "-u")
    _refused(repo, "gate-uncommitted")


def test_t2_ac0003_missing_artifact_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / h.SPEC_DIR / "plan.md").unlink()
    _refused(repo, "gate-uncommitted")


def test_t2_ac0004_status_gates(tmp_path: Path) -> None:
    approved = _repo(tmp_path / "a", spec=sup.SPEC, plan=PLAN)
    _refused(approved, "gate-status-mismatch")
    _refused(approved, "gate-spec-changed", "plan-approved")  # statuses fit; no record yet
    draft = _repo(tmp_path / "b")
    _refused(draft, "gate-status-mismatch", "plan-approved")
    both = _repo(tmp_path / "c", spec=sup.SPEC, plan=sup.PLAN)
    _refused(both, "gate-status-mismatch", "plan-approved")
    implementing = _repo(tmp_path / "d", spec=sup.SPEC.replace("Approved", "Implementing", 1))
    _refused(implementing, "gate-status-mismatch")


def test_t2_ac0005_admitted_pair_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, spec=sup.SPEC, plan=sup.PLAN)
    _admit(repo)
    _refused(repo, "gate-already-admitted")


def _admitted_then_drafted(tmp_path: Path, spec: str = sup.SPEC) -> Path:
    """An admitted run whose spec and plan then return to Draft and Drafting."""
    repo = _repo(tmp_path, spec=spec, plan=sup.PLAN)
    _admit(repo)
    _edit(repo, "spec.md", "**Status:** Approved", "**Status:** Draft")
    _edit(repo, "plan.md", "**Status:** Approved", "**Status:** Drafting")
    _commit(repo, "back to draft")
    return repo


def test_t2_ac0005_pair_differing_in_one_value_parks(tmp_path: Path) -> None:
    repo = _admitted_then_drafted(tmp_path / "trust")
    _refused(repo, "gate-already-admitted")
    code, out = _park(repo, trust="untrusted")  # only the trust differs
    assert code == 0 and out["status"] == "parked", out

    repo = _admitted_then_drafted(tmp_path / "intent", spec=sup.SPEC.replace(NO_INTENT, ""))
    _refused(repo, "gate-already-admitted")
    code, out = _park(repo, intent="spec-plan")  # only the intent differs
    assert code == 0 and out["status"] == "parked", out

    repo = _admitted_then_drafted(tmp_path / "fingerprint")
    _edit(repo, "spec.md", "The calculator answers 42.", "The calculator answers 43.")
    _commit(repo)
    code, out = _park(repo)  # only the envelope fingerprint differs
    assert code == 0 and out["status"] == "parked", out


def test_t2_ac0006_second_park_is_current(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _, first = _park(repo)
    (record,) = _records(repo)
    before = record.read_bytes()
    code, again = _park(repo)
    assert code == 0 and again["status"] == "current", again
    assert {k: v for k, v in again.items() if k != "status"} == {
        k: v for k, v in first.items() if k != "status"
    }
    assert record.read_bytes() == before and _records(repo) == [record]


def test_t2_ac0006_a_different_value_replaces_the_record(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _park(repo)
    code, out = _park(repo, trust="untrusted")
    assert code == 0 and out["status"] == "parked", out
    (record,) = _records(repo)
    assert json.loads(record.read_text(encoding="utf-8"))["code_trust"] == "untrusted"
    code, out = _park(repo, trust="untrusted")
    assert out["status"] == "current"


def test_t2_ac0006_a_moved_commit_with_the_same_digests_stays_current(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _, first = _park(repo)
    (repo / "README.md").write_text("moved\n", **h._LF)
    _commit(repo, "unrelated")
    code, out = _park(repo)
    assert out["status"] == "current" and out["commit"] == first["commit"], out


def test_t2_ac0006_an_unreadable_recorded_commit_is_replaced(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _, first = _park(repo)
    h.git(repo, "commit", "-q", "--amend", "-m", "rewritten")
    h.git(repo, "reflog", "expire", "--expire=now", "--all")
    h.git(repo, "gc", "-q", "--prune=now")
    gone = subprocess.run(
        ["git", "cat-file", "-e", first["commit"]], cwd=repo, capture_output=True
    )
    assert gone.returncode != 0
    code, out = _park(repo)
    head = h.git(repo, "rev-parse", "HEAD").strip()
    assert code == 0 and out["status"] == "parked" and out["commit"] == head, out
    (record,) = _records(repo)
    assert json.loads(record.read_text(encoding="utf-8"))["commit"] == head


def test_t2_ac0026_no_gate_digest_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, plan=PLAN + "\n## Changelog\n\n- again\n")
    _refused(repo, "gate-changelog-shape")
    repo = _repo(tmp_path / "s", spec=SPEC + "\n## Changelog\n\n- one\n\n## Later\n\ntext\n")
    _refused(repo, "gate-changelog-shape")


def test_t2_ac0029_the_first_applicable_refusal_wins(tmp_path: Path) -> None:
    # gate-uncommitted over gate-status-mismatch
    repo = _repo(tmp_path / "a", spec=sup.SPEC)
    _edit(repo, "plan.md", "Build it.", "Build it well.")
    _refused(repo, "gate-uncommitted")
    # gate-status-mismatch over gate-unsafe-content
    repo = _repo(tmp_path / "b", spec=sup.SPEC.replace("answers.", f"answers.{ZWSP}"))
    _refused(repo, "gate-status-mismatch")
    # gate-unsafe-content over gate-changelog-shape
    plan = PLAN.replace("Build it.", f"Build it.{ZWSP}") + "\n## Changelog\n\n- again\n"
    repo = _repo(tmp_path / "c", plan=plan)
    _refused(repo, "gate-unsafe-content")
    # gate-changelog-shape over gate-spec-changed
    repo = _repo(tmp_path / "d", spec=sup.SPEC, plan=PLAN + "\n## Changelog\n\n- again\n")
    _refused(repo, "gate-changelog-shape", "plan-approved")
    # intent-mismatch over gate-uncommitted
    repo = _repo(tmp_path / "e")
    _edit(repo, "spec.md", "answers.", "answers it.")
    _refused(repo, "intent-mismatch", intent="spec-plan")
    # ambiguous-reference over intent-mismatch
    repo = _repo(tmp_path / "f", spec=SPEC + "\n## Terminal Intent\n\n`spec-plan` — again.\n")
    _refused(repo, "ambiguous-reference", intent="spec-plan")
    # gate-already-admitted over gate-status-mismatch
    repo = _repo(tmp_path / "g", spec=sup.SPEC, plan=sup.PLAN)
    _admit(repo)
    _refused(repo, "gate-already-admitted")
    # gate-unsafe-path over intent-mismatch
    repo = _repo(tmp_path / "h")
    h.git(repo, "mv", h.SPEC_DIR, "docs/specs/has space")
    h.git(repo, "commit", "-q", "-m", "move")
    _refused(repo, "gate-unsafe-path", intent="spec-plan", spec_dir="docs/specs/has space")


def test_t2_ac0030_plan_gate_carries_the_spec_digest(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _, spec_gate = _park(repo)
    _edit(repo, "spec.md", "**Status:** Draft", "**Status:** Approved")
    with (repo / h.SPEC_DIR / "spec.md").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n## Changelog\n\n- approved by the owner\n")
    _commit(repo, "spec approved")
    code, out = _park(repo, "plan-approved")
    assert code == 0 and out["status"] == "parked" and out["gate"] == "plan-approved", out
    assert out["spec_digest"] == spec_gate["spec_digest"]
    (record,) = _records(repo)
    assert json.loads(record.read_text(encoding="utf-8"))["spec_digest"] == out["spec_digest"]
    code, again = _park(repo, "plan-approved")
    assert again["status"] == "current" and again["spec_digest"] == spec_gate["spec_digest"]


def test_t2_ac0030_without_a_valid_record_or_after_a_spec_edit_refuses(tmp_path: Path) -> None:
    approved = SPEC.replace("**Status:** Draft", "**Status:** Approved")
    repo = _repo(tmp_path / "none", spec=approved)
    _refused(repo, "gate-spec-changed", "plan-approved")

    repo = _repo(tmp_path / "edit")
    _park(repo)
    (record,) = _records(repo)
    before = record.read_bytes()
    _edit(repo, "spec.md", "**Status:** Draft", "**Status:** Approved")
    _edit(repo, "spec.md", "answers 42.", "answers 43.")
    _commit(repo, "edited after the gate was parked")
    _refused(repo, "gate-spec-changed", "plan-approved")
    assert record.read_bytes() == before

    record.write_text("{not json", encoding="utf-8")
    _refused(repo, "gate-spec-changed", "plan-approved")


@pytest.mark.parametrize(
    "name",
    ["has space", "-dash", "café", "a$b", "a;b", "a'b"],
)
def test_t2_ac0032_unsafe_path_refuses(tmp_path: Path, name: str) -> None:
    repo = _repo(tmp_path)
    target = f"docs/specs/{name}"
    h.git(repo, "mv", h.SPEC_DIR, target)
    h.git(repo, "commit", "-q", "-m", "move")
    _refused(repo, "gate-unsafe-path", spec_dir=target)


def test_t2_ac0032_shared_check_rejection_is_a_usage_error(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    for bad in ("/abs/path", "docs/../docs/specs/calc", "docs\\specs", "missing/dir"):
        code, out = _park(repo, spec_dir=bad)
        assert code == 2 and out["error"] == "usage", (bad, out)
    assert _records(repo) == []


def test_t2_ac0038_terminal_intent_rules(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "none", spec=SPEC.replace(NO_INTENT, ""))
    for intent in ("code", "spec-plan"):
        code, out = _park(repo, intent=intent)
        assert code == 0 and out["intent"] == intent, out

    repo = _repo(tmp_path / "differs")
    refusal = _refused(repo, "intent-mismatch", intent="spec-plan")
    assert refusal["owner"] == "owner"

    repo = _repo(tmp_path / "two", spec=SPEC + "\n## Terminal Intent\n\n`code` — again.\n")
    refusal = _refused(repo, "ambiguous-reference")
    with pytest.raises(h.projector.ProjectionRefused) as start_would_give:
        h.projector.terminal_intent(SPEC + "\n## Terminal Intent\n\n`code` — again.\n")
    assert refusal["owner"] == start_would_give.value.owner


@pytest.mark.parametrize(
    ("artifact", "bad"),
    [("spec.md", ZWSP), ("plan.md", "‮"), ("plan.md", "\x1b[0m"), ("spec.md", " ")],
)
def test_t2_ac0039_hidden_characters_refuse(tmp_path: Path, artifact: str, bad: str) -> None:
    repo = _repo(tmp_path)
    marker = "answers." if artifact == "spec.md" else "Build it."
    _edit(repo, artifact, marker, f"{marker}{bad}")
    _commit(repo)
    _refused(repo, "gate-unsafe-content")


def test_t2_ac0039_invalid_utf8_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    path = repo / h.SPEC_DIR / "plan.md"
    path.write_bytes(path.read_bytes() + b"\xff\xfe\n")
    _commit(repo)
    _refused(repo, "gate-unsafe-content")
