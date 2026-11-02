"""Construction tests for the `refresh-policy-move` repair step.

Spec: docs/specs/last-registry-entries/spec.md (AC-0004, AC-0005).
Verification mode: TDD.

Each test plants a repository under ``tmp_path`` and runs ``repair-plan`` and
``repair-apply`` in process through the script's ``main``.
"""
from __future__ import annotations

import errno
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

pytest.importorskip("tomlkit")

_SKILLS = Path(__file__).resolve().parents[3] / ".apm/skills"


def _load(name: str, path: Path) -> ModuleType:
    """Load a module by file path under a unique name."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


WS = _load(
    "workspace_status_refresh_policy_move",
    _SKILLS / "workspace-status/scripts/workspace_status.py",
)

PLAN = ".workspace-repair-plan.json"
MOVE = "refresh-policy-move"
POLICY = ".work-intake.toml"
CAPTURED = "docs/product/captured"

TABLE = (
    "[authorization.refresh]\n"
    'contract_version = "refresh-authorization-policy.v1"\n'
    'draft_approver_roles = ["lead"]\n'
    'accepted_approver_roles = ["lead", "owner"]\n'
    'remote_mutation_approver_roles = ["owner"]\n'
)
BASE = "# fixture header comment\n[backlog]\nopen = []\nclosed = []\n\n"
ENTRY = 'open = [\n  {slug = "a-one", summary = "legacy"},  # keep\n]\n'


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_repo(root: Path, table: str | None = TABLE, files: dict[str, str] | None = None) -> Path:
    write(root, "workspace.toml", BASE + (table or ""))
    write(root, "AGENTS.md", "# Agents\n")
    for rel, text in (files or {}).items():
        write(root, rel, text)
    return root


def run(root: Path, capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, dict[str, Any]]:
    capsys.readouterr()
    code = WS.main([*args, "--root", str(root)])
    out = capsys.readouterr().out.strip().splitlines()
    return code, json.loads(out[-1]) if out else {}


def plan(root: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    code, data = run(root, capsys, "repair-plan")
    assert code == 0, data
    return data


def apply(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, dict[str, Any]]:
    return run(root, capsys, "repair-apply", "--yes")


def moves(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [op for op in data["automatic_operations"] if op["operation_type"] == MOVE]


def manual(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in data["manual_findings"] if f.get("finding_type") == 9]


def registry(root: Path) -> str:
    return (root / "workspace.toml").read_text(encoding="utf-8")


def policy_bytes(root: Path) -> bytes | None:
    path = root / POLICY
    return path.read_bytes() if path.exists() else None


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── AC-0004: the move ─────────────────────────────────────────────────────────


def test_table_with_no_policy_file_plans_one_move_and_apply_creates_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path)
    before = registry(repo)
    data = plan(repo, capsys)
    assert registry(repo) == before and policy_bytes(repo) is None
    [op] = moves(data)
    assert op["policy_path"] == POLICY and op["action"] == "create-and-remove"
    assert op["policy_sha256"] == sha(TABLE)
    assert manual(data) == []
    code, result = apply(repo, capsys)
    assert code == 0 and result["operations_applied"] == 1
    assert policy_bytes(repo) == TABLE.encode("utf-8")
    assert registry(repo) == BASE
    assert "authorization" not in registry(repo)


def test_no_table_plans_nothing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = make_repo(tmp_path, table=None)
    data = plan(repo, capsys)
    assert moves(data) == [] and manual(data) == []


def test_invalid_table_is_a_manual_item_and_nothing_moves(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = TABLE.replace('"refresh-authorization-policy.v1"', '"other"')
    repo = make_repo(tmp_path, bad)
    data = plan(repo, capsys)
    assert moves(data) == []
    [item] = manual(data)
    assert item["reason"] == "table-not-accepted" and item["spec_path"] == POLICY
    assert policy_bytes(repo) is None and bad in registry(repo)


def test_table_with_an_extra_key_is_a_manual_item(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, TABLE + 'extra = "x"\n')
    data = plan(repo, capsys)
    assert moves(data) == []
    assert [f["reason"] for f in manual(data)] == ["table-not-accepted"]


def test_equal_existing_policy_file_plans_a_remove_only_operation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Same table, different bytes: equality is on the parsed table.
    existing = "# policy\n" + TABLE.replace('["lead", "owner"]', '[ "lead", "owner" ]')
    repo = make_repo(tmp_path, files={POLICY: existing})
    data = plan(repo, capsys)
    [op] = moves(data)
    assert op["action"] == "remove"
    code, _result = apply(repo, capsys)
    assert code == 0
    assert policy_bytes(repo) == existing.encode("utf-8")
    assert "authorization" not in registry(repo)


def test_differing_existing_policy_file_is_manual_and_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    existing = TABLE.replace('"owner"]', '"other"]')
    repo = make_repo(tmp_path, files={POLICY: existing})
    data = plan(repo, capsys)
    assert moves(data) == []
    assert [f["reason"] for f in manual(data)] == ["policy-file-differs"]
    assert policy_bytes(repo) == existing.encode("utf-8") and TABLE in registry(repo)


@pytest.mark.parametrize("existing", ["not = [valid toml", TABLE + 'extra = "x"\n', 'other = 1\n'])
def test_existing_file_that_is_not_a_policy_file_is_never_overwritten(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], existing: str
) -> None:
    repo = make_repo(tmp_path, files={POLICY: existing})
    data = plan(repo, capsys)
    assert moves(data) == []
    assert [f["reason"] for f in manual(data)] == ["policy-file-invalid"]
    assert policy_bytes(repo) == existing.encode("utf-8") and TABLE in registry(repo)


def test_file_appearing_after_the_plan_is_not_overwritten(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path)
    plan(repo, capsys)
    stranger = 'other = "kept"\n'
    write(repo, POLICY, stranger)
    code, result = apply(repo, capsys)
    assert policy_bytes(repo) == stranger.encode("utf-8") and TABLE in registry(repo)
    assert result.get("operations_applied", 0) == 0
    assert code == 0
    assert [r["reason"] for r in result["per_operation"]] == ["policy_move_mismatch"]


def test_a_file_that_appears_between_derivation_and_write_is_refused_policy_file_exists(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo(tmp_path)
    plan(repo, capsys)
    stranger = 'other = "kept"\n'
    write(repo, POLICY, stranger)
    real_lexists = WS.os.path.lexists
    seen: list[str] = []

    def lexists(path: Any) -> bool:
        # The first look at the policy file is the apply-time re-derivation: hide it there.
        if Path(path).name == POLICY and not seen:
            seen.append(str(path))
            return False
        return real_lexists(path)

    monkeypatch.setattr(WS.os.path, "lexists", lexists)
    code, result = apply(repo, capsys)
    monkeypatch.undo()
    assert code == 0
    assert [r["reason"] for r in result["per_operation"]] == ["policy_file_exists"]
    assert policy_bytes(repo) == stranger.encode("utf-8") and TABLE in registry(repo)


def test_a_file_that_appears_after_every_pre_check_is_not_overwritten(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo(tmp_path)
    plan(repo, capsys)
    stranger = 'other = "kept"\n'
    write(repo, POLICY, stranger)
    real_lexists = WS.os.path.lexists

    def lexists(path: Any) -> bool:
        # Every pre-check sees no policy file; only the exclusive create can refuse.
        return False if Path(path).name == POLICY else real_lexists(path)

    monkeypatch.setattr(WS.os.path, "lexists", lexists)
    code, result = apply(repo, capsys)
    monkeypatch.undo()
    assert code == 0
    assert [r["reason"] for r in result["per_operation"]] == ["policy_file_exists"]
    assert policy_bytes(repo) == stranger.encode("utf-8") and TABLE in registry(repo)


def test_a_refresh_module_that_cannot_load_is_its_own_manual_reason(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo(tmp_path)
    monkeypatch.setattr(WS, "_refresh_module", lambda: None)
    data = plan(repo, capsys)
    assert moves(data) == []
    assert [f["reason"] for f in manual(data)] == ["refresh-module-unavailable"]
    assert policy_bytes(repo) is None and TABLE in registry(repo)


# ── Failure windows ───────────────────────────────────────────────────────────


def test_failed_policy_file_write_changes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo(tmp_path)
    before = registry(repo)
    plan(repo, capsys)

    def refuse(*_args: Any, **_kwargs: Any) -> None:
        raise OSError(errno.EIO, "injected")

    monkeypatch.setattr(WS.os, "link", refuse)
    code, result = apply(repo, capsys)
    monkeypatch.undo()
    assert registry(repo) == before and policy_bytes(repo) is None
    assert result.get("operations_applied", 0) == 0
    assert not [p for p in repo.iterdir() if p.name.startswith(".work-intake")]
    assert code == 0
    assert [r["reason"] for r in result["per_operation"]] == ["policy_write_failed"]


def test_failed_workspace_write_leaves_a_policy_file_the_next_plan_removes_only(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo(tmp_path)
    before = registry(repo)
    plan(repo, capsys)

    def refuse(self: Path, *_args: Any, **_kwargs: Any) -> None:
        raise OSError(errno.EIO, "injected")

    monkeypatch.setattr(Path, "replace", refuse)
    code, _result = apply(repo, capsys)
    monkeypatch.undo()
    assert code == 2
    assert policy_bytes(repo) == TABLE.encode("utf-8") and registry(repo) == before
    [op] = moves(plan(repo, capsys))
    assert op["action"] == "remove"
    code, _result = apply(repo, capsys)
    assert code == 0 and "authorization" not in registry(repo)
    assert policy_bytes(repo) == TABLE.encode("utf-8")


# ── AC-0005: one apply leaves nothing ─────────────────────────────────────────


def test_combined_with_captured_entry_drop_and_next_plan_is_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(
        tmp_path, files={f"{CAPTURED}/a-one.md": "# Item\n\n- **Status:** Open\n- **Kind:** defect\n"}
    )
    write(repo, "workspace.toml", registry(repo).replace("open = []\n", ENTRY))
    data = plan(repo, capsys)
    kinds = sorted(op["operation_type"] for op in data["automatic_operations"])
    assert kinds == ["captured-entry-drop", MOVE]
    code, result = apply(repo, capsys)
    assert code == 0 and result["operations_applied"] == 2
    again = plan(repo, capsys)
    assert again["automatic_operations"] == [] and manual(again) == []
    assert "authorization" not in registry(repo) and "a-one" not in registry(repo)
    assert "# fixture header comment" in registry(repo)


def test_next_plan_is_empty_after_apply(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path)
    plan(repo, capsys)
    code, _result = apply(repo, capsys)
    assert code == 0
    again = plan(repo, capsys)
    assert moves(again) == [] and manual(again) == []


def test_tampered_plan_with_a_bad_digest_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path)
    data = plan(repo, capsys)
    data["automatic_operations"][0]["policy_sha256"] = "z" * 64
    data["plan_id"] = WS._recompute_plan_id(data)
    (repo / PLAN).write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
    code, result = apply(repo, capsys)
    assert code == 2 and result["reason"] == "plan_invalid"
    assert policy_bytes(repo) is None
