"""Construction tests for the `captured-entry-drop` repair step.

Spec: docs/specs/last-registry-entries/spec.md (AC-0001, AC-0002, AC-0003,
AC-0005). Verification mode: TDD.

Each test plants a repository under ``tmp_path`` and runs ``repair-plan`` and
``repair-apply`` in process through the script's ``main``.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

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
    "workspace_status_captured_entry_drop", _SKILLS / "workspace-status/scripts/workspace_status.py"
)
DISPATCH = _load("dispatch_captured_entry_drop", _SKILLS / "work-loop/scripts/dispatch.py")

PLAN = ".workspace-repair-plan.json"
DROP = "captured-entry-drop"
CAPTURED = "docs/product/captured"
NOTES = "docs/product/notes"


def record(status: str = "Open", kind: str = "defect") -> str:
    """A readable captured-item file."""
    return f"# Item\n\n- **Status:** {status}\n- **Kind:** {kind}\n"


def member(path: str, kind: str = "defect") -> str:
    return (
        f'{{path = "{path}", kind = "{kind}", source = {{mode = "repo-origin"}}, '
        'summary = "fixture", needs = []}'
    )


def slug_only(slug: str) -> str:
    return f'{{slug = "{slug}", summary = "legacy"}}'


def workspace_text(
    *,
    open_: list[str] | None = None,
    backlog: list[str] | None = None,
    active: list[str] | None = None,
) -> str:
    def rows(values: list[str] | None) -> str:
        return "[\n" + "".join(f"  {v},  # keep\n" for v in values or []) + "]"

    return (
        "# fixture header comment\n"
        f"[backlog]\nopen = {rows(open_)}\nclosed = []\n\n"
        '["ini-001"]\nname = "Fixture"\nstatus = "active"\nmilestone = "m1"\n\n'
        '["ini-001".work]\nqueue = []\nactive = []\nshipped = []\n\n'
        f'["ini-001".shaping_queue]\nactive = {rows(active)}\nbacklog = {rows(backlog)}\n'
    )


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_repo(root: Path, files: dict[str, str] | None = None, **registry: Any) -> Path:
    write(root, "workspace.toml", workspace_text(**registry))
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


def drops(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [op for op in data["automatic_operations"] if op["operation_type"] == DROP]


def to_file_ops(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [op for op in data["automatic_operations"] if op["operation_type"] == "captured-to-file"]


def manual(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in data["manual_findings"] if f.get("finding_type") == 8]


def registry_text(root: Path) -> str:
    return (root / "workspace.toml").read_text(encoding="utf-8")


def captured_bytes(root: Path) -> dict[str, bytes]:
    base = root / CAPTURED
    return {p.name: p.read_bytes() for p in sorted(base.glob("*")) if p.is_file()} if base.is_dir() else {}


def rewrite_plan(root: Path, change: Callable[[dict[str, Any]], None]) -> None:
    data = json.loads((root / PLAN).read_text(encoding="utf-8"))
    change(data)
    data["plan_id"] = WS._recompute_plan_id(data)
    (root / PLAN).write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── AC-0001: readable captured files ─────────────────────────────────────────


def test_readable_captured_membership_gets_one_drop(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/d1.md"
    repo = make_repo(tmp_path, {path: record()}, open_=[member(path)])
    before = registry_text(repo)
    data = plan(repo, capsys)
    assert registry_text(repo) == before
    [op] = drops(data)
    assert op["path"] == path and op["file_path"] == path
    assert op["file_sha256"] == sha(record())
    assert op["entry_locator"] == {"ini_slug": "", "collection": "backlog.open", "index": 0}
    assert len(op["registry_fingerprint"]) == 64
    assert manual(data) == []


def test_membership_in_a_shaping_queue_is_planned(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/s1.md"
    repo = make_repo(tmp_path, {path: record(kind="intent")}, backlog=[member(path, "intent")])
    [op] = drops(plan(repo, capsys))
    assert op["entry_locator"] == {
        "ini_slug": "ini-001", "collection": "shaping_queue.backlog", "index": 0,
    }


def test_slug_only_entries_with_a_file_are_planned_in_backlog_and_queues(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(
        tmp_path,
        {f"{CAPTURED}/{s}.md": record() for s in ("a-one", "b-two", "c-three")},
        open_=[slug_only("a-one")],
        backlog=[slug_only("b-two")],
        active=[slug_only("c-three")],
    )
    data = plan(repo, capsys)
    assert {op["slug"] for op in drops(data)} == {"a-one", "b-two", "c-three"}
    assert to_file_ops(data) == [] and manual(data) == []
    for op in drops(data):
        assert op["file_sha256"] == sha(record())
        assert op["file_path"] == f"{CAPTURED}/{op['slug']}.md"


# ── AC-0002: everything else is a manual item ────────────────────────────────


def test_missing_file_is_a_manual_item_and_keeps_its_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/gone.md"
    repo = make_repo(tmp_path, open_=[member(path)])
    data = plan(repo, capsys)
    assert drops(data) == []
    [item] = manual(data)
    assert item["reason"] == "path-missing"
    assert item["entry_locator"] == {"ini_slug": "", "collection": "backlog.open", "index": 0}
    before = registry_text(repo)
    code, _ = apply(repo, capsys)
    assert code == 0 and registry_text(repo) == before


def test_symlinked_file_is_file_linked(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = f"{CAPTURED}/ln.md"
    repo = make_repo(tmp_path, {"docs/product/notes/real.md": record()}, open_=[member(path)])
    (repo / CAPTURED).mkdir(parents=True)
    (repo / path).symlink_to(repo / "docs/product/notes/real.md")
    data = plan(repo, capsys)
    assert drops(data) == []
    assert [i["reason"] for i in manual(data)] == ["file-linked"]


def test_hard_linked_file_is_file_linked(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/hl.md"
    repo = make_repo(tmp_path, {path: record(), "docs/product/notes/twin.md": ""}, open_=[member(path)])
    (repo / "docs/product/notes/twin.md").unlink()
    os.link(repo / path, repo / "docs/product/notes/twin.md")
    assert [i["reason"] for i in manual(plan(repo, capsys))] == ["file-linked"]


def test_non_utf8_file_is_unreadable_and_bad_record_is_invalid(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad, odd = f"{CAPTURED}/bad.md", f"{CAPTURED}/odd.md"
    repo = make_repo(tmp_path, {odd: "# Odd\n\nno header fields\n"}, open_=[member(bad), member(odd)])
    (repo / bad).write_bytes(b"\xff\xfe\x00")
    data = plan(repo, capsys)
    assert drops(data) == []
    assert sorted(i["reason"] for i in manual(data)) == ["file-unreadable", "record-invalid"]


def test_slug_only_entry_whose_file_cannot_be_read_gets_one_manual_item(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(
        tmp_path, {f"{CAPTURED}/odd-one.md": "# Odd\n\nnothing\n"}, open_=[slug_only("odd-one")]
    )
    data = plan(repo, capsys)
    assert drops(data) == []
    items = [
        f for f in data["manual_findings"]
        if f.get("list_name") == "backlog.open" and f.get("finding_type") in (5, 8)
    ]
    assert len(items) == 1


# ── AC-0003: apply ───────────────────────────────────────────────────────────


def test_apply_removes_only_the_planned_entries_and_writes_no_captured_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/d1.md"
    repo = make_repo(
        tmp_path,
        {path: record(), f"{CAPTURED}/s-one.md": record()},
        open_=[member(f"{CAPTURED}/gone.md"), member(path), slug_only("s-one")],
    )
    files = captured_bytes(repo)
    plan(repo, capsys)
    before = registry_text(repo)
    code, result = apply(repo, capsys)
    assert code == 0, result
    after = registry_text(repo)
    assert path not in after and "s-one" not in after
    assert f"{CAPTURED}/gone.md" in after
    # Every line outside the two removed entries survives, comments included.
    kept = [ln for ln in before.splitlines() if path not in ln and "s-one" not in ln]
    assert after.splitlines() == kept
    assert captured_bytes(repo) == files


def test_apply_refuses_when_the_captured_file_changed_after_the_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/d1.md"
    repo = make_repo(tmp_path, {path: record()}, open_=[member(path)])
    plan(repo, capsys)
    (repo / path).write_text(record(status="Closed"), encoding="utf-8")
    changed = captured_bytes(repo)
    before = registry_text(repo)
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert [i["applied"] for i in result["per_operation"]] == [False]
    assert registry_text(repo) == before and captured_bytes(repo) == changed


def test_apply_refuses_when_the_entry_differs_from_the_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/d1.md"
    repo = make_repo(tmp_path, {path: record()}, open_=[member(path)])
    plan(repo, capsys)
    rewrite_plan(repo, lambda d: [op.update(registry_fingerprint="0" * 64) for op in d["automatic_operations"]])
    before = registry_text(repo)
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert [i["reason"] for i in result["per_operation"]] == ["entry_locator_mismatch"]
    assert registry_text(repo) == before


def test_apply_refuses_a_slug_only_drop_whose_file_is_gone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, {f"{CAPTURED}/a-one.md": record()}, open_=[slug_only("a-one")])
    plan(repo, capsys)
    (repo / CAPTURED / "a-one.md").unlink()
    before = registry_text(repo)
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert [i["applied"] for i in result["per_operation"]] == [False]
    assert registry_text(repo) == before


# ── AC-0001, AC-0003, AC-0005: a plan that also holds captured-to-file ───────


def backed_repo(root: Path) -> Path:
    src = f"{NOTES}/d1.md"
    return make_repo(
        root,
        {src: "# A note\n", f"{CAPTURED}/there.md": record()},
        open_=[member(src), slug_only("fresh-one"), slug_only("there")],
        backlog=[slug_only("fresh-two")],
    )


def test_plan_backs_drops_with_the_captured_to_file_records(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = backed_repo(tmp_path)
    data = plan(repo, capsys)
    writes = {op["record_path"]: op for op in to_file_ops(data)}
    assert set(writes) == {f"{CAPTURED}/{s}.md" for s in ("d1", "fresh-one", "fresh-two")}
    assert len(drops(data)) == 4
    for op in drops(data):
        record_path = op["file_path"]
        if record_path in writes:
            assert op["file_sha256"] == sha(writes[record_path]["record_text"])
    assert manual(data) == []


def test_one_apply_leaves_nothing_for_the_next_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = backed_repo(tmp_path)
    data = plan(repo, capsys)
    expected = {op["record_path"]: op["record_text"] for op in to_file_ops(data)}
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert all(item["applied"] for item in result["per_operation"]), result
    text = registry_text(repo)
    assert "d1" not in text and "fresh" not in text and '"there"' not in text
    for record_path, body in expected.items():
        assert (repo / record_path).read_text(encoding="utf-8") == body
    after = plan(repo, capsys)
    assert drops(after) == [] and to_file_ops(after) == [] and manual(after) == []


def test_a_backed_drop_whose_file_bytes_differ_is_refused_and_keeps_its_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, open_=[slug_only("fresh-one")])
    plan(repo, capsys)
    rewrite_plan(repo, lambda d: [
        op.update(file_sha256="0" * 64) for op in d["automatic_operations"] if op["operation_type"] == DROP
    ])
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert "fresh-one" in registry_text(repo)
    assert (repo / CAPTURED / "fresh-one.md").is_file()
    assert [i["applied"] for i in result["per_operation"]].count(False) == 1


# ── dispatch ─────────────────────────────────────────────────────────────────


def test_dispatch_output_is_identical_across_apply(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/d1.md"
    repo = make_repo(tmp_path, {path: record()}, open_=[member(path)], active=[slug_only("a-one")])
    write(repo, f"{CAPTURED}/a-one.md", record())
    plan(repo, capsys)

    def stdout() -> str:
        capsys.readouterr()
        DISPATCH.main(["--root", str(repo)])
        data = json.loads(capsys.readouterr().out)
        return json.dumps({k: data[k] for k in ("ready", "active", "blocked", "decision")})

    before = stdout()
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert path not in registry_text(repo)
    assert stdout() == before
