"""Construction tests for the `captured-entry-drop` repair step.

Spec: docs/specs/last-registry-entries/spec.md (AC-0001, AC-0002, AC-0003,
AC-0005, AC-0022). Verification mode: TDD.

Each test plants a repository under ``tmp_path`` and runs ``repair-plan`` and
``repair-apply`` in process through the script's ``main``.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tomllib
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
NEEDS = "needs-to-header"
BRIEFS = "docs/product/briefs"
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


def slug_needs(slug: str, needs: str | list[str]) -> str:
    """A slug-only entry carrying legacy `needs`: one string or an array."""
    value = json.dumps(needs)
    return f'{{slug = "{slug}", summary = "legacy", needs = {value}}}'


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


def needs_ops(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [op for op in data["automatic_operations"] if op["operation_type"] == NEEDS]


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
    assert [i["reason"] for i in result["per_operation"]] == ["record-invalid"]
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
    assert [i["reason"] for i in result["per_operation"]] == ["path-missing"]
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
    assert [i.get("reason") for i in result["per_operation"]] == [None, "captured_file_changed"]


def test_backed_drop_apply_leaves_workspace_toml_at_its_exact_expected_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, open_=[slug_only("fresh-one")])
    plan(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert registry_text(repo) == workspace_text()


def test_membership_whose_needs_cannot_move_gets_no_drop_and_one_manual_item(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/d1.md"
    planted = member(path).replace("needs = []", 'needs = [{type = "local", path = "docs/product/briefs/nope.md", kind = "brief"}]')
    repo = make_repo(tmp_path, {path: record()}, open_=[planted])
    first = plan(repo, capsys)
    assert not [op for op in first["automatic_operations"] if op["operation_type"] in (DROP, NEEDS)]
    manual_before = [f["finding_id"] for f in first["manual_findings"]]
    assert len(manual_before) == 1
    [item] = first["manual_findings"]
    assert item["finding_type"] == 4
    assert item["reason"] == "missing-brief-target"
    assert item["spec_path"] == path
    again = plan(repo, capsys)
    assert [f["finding_id"] for f in again["manual_findings"]] == manual_before
    assert again["automatic_operations"] == first["automatic_operations"]


def test_apply_refuses_a_file_edited_after_the_plan_that_still_parses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/d1.md"
    repo = make_repo(tmp_path, {path: record()}, open_=[member(path)])
    plan(repo, capsys)
    edited = record(status="Closed") + "- **Resolution:** fixed\n"
    (repo / path).write_text(edited, encoding="utf-8")
    before = registry_text(repo)
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert [i["reason"] for i in result["per_operation"]] == ["captured_file_changed"]
    assert registry_text(repo) == before and captured_bytes(repo) == {"d1.md": edited.encode("utf-8")}


def test_membership_whose_needs_a_same_plan_header_move_covers_is_dropped_in_one_apply(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/d1.md"
    peer = "docs/specs/peer/spec.md"
    planted = member(path).replace(
        "needs = []", f'needs = [{{type = "local", kind = "spec", path = "{peer}"}}]'
    )
    spec = "# Spec: peer\n\n- **Status:** Approved\n- **Brief:** none\n\n## Outcome\n\nbody\n"
    repo = make_repo(tmp_path, {path: record(), peer: spec}, open_=[planted], active=[member(peer, "spec")])
    data = plan(repo, capsys)
    assert [op["waiting_path"] for op in needs_ops(data)] == [path]
    assert [op["path"] for op in drops(data)] == [path]
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert all(item["applied"] for item in result["per_operation"]), result
    assert path not in registry_text(repo)
    assert "spec:peer" in (repo / path).read_text(encoding="utf-8")
    after = plan(repo, capsys)
    assert after["automatic_operations"] == [] and after["manual_findings"] == []


# ── dispatch ─────────────────────────────────────────────────────────────────


def dispatch_stdout(root: Path, capsys: pytest.CaptureFixture[str]) -> str:
    capsys.readouterr()
    DISPATCH.main(["--root", str(root)])
    return capsys.readouterr().out


def _holds_entry(value: Any) -> bool:
    """True when a TOML value holds an element of an array, at any depth."""
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return any(_holds_entry(item) for item in value.values())
    return False


def assert_dispatch_after_apply(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Assert AC-0030 for dispatch run after a ``repair-apply --yes``.

    A ``workspace.toml`` that still holds an entry gets the ``unmigrated_workspace``
    refusal; otherwise the output is byte-identical to dispatch on the same tree with
    ``workspace.toml`` removed. These fixtures plant workspaces dispatch accepts, so
    the ``invalid_workspace`` refusal is itself a failure here.
    """
    after = dispatch_stdout(root, capsys)
    workspace = root / "workspace.toml"
    document = tomllib.loads(workspace.read_text(encoding="utf-8"))
    if any(_holds_entry(v) for k, v in document.items() if k != "authorization"):
        data = json.loads(after)
        assert [f["code"] for f in data["decision"]["findings"]] == ["unmigrated_workspace"]
        assert data["decision"]["action"] == "refuse"
        assert data["ready"] == data["active"] == data["blocked"] == []
        return
    held = workspace.read_bytes()
    workspace.unlink()
    try:
        bare = dispatch_stdout(root, capsys)
    finally:
        workspace.write_bytes(held)
    assert after == bare


def test_dispatch_output_is_identical_across_apply(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{CAPTURED}/d1.md"
    repo = make_repo(tmp_path, {path: record()}, open_=[member(path)], active=[slug_only("a-one")])
    write(repo, f"{CAPTURED}/a-one.md", record())
    plan(repo, capsys)

    code, result = apply(repo, capsys)
    assert code == 0, result
    assert path not in registry_text(repo)
    assert_dispatch_after_apply(repo, capsys)


# ── AC-0022: legacy needs move to the captured file, then the entry drops ────


def header_record(*lines: str) -> str:
    return "# Item\n\n- **Status:** Open\n- **Kind:** defect\n" + "".join(f"{ln}\n" for ln in lines)


def all_manual(data: dict[str, Any]) -> list[dict[str, Any]]:
    return data["manual_findings"]


@pytest.mark.parametrize(
    ("need", "reference"),
    [
        ("work:spec/alpha-one", "spec:alpha-one"),
        ("ini-001:work:spec/alpha-one", "spec:alpha-one"),
        (f"brief:{BRIEFS}/b-one.md", "brief:b-one"),
        ("backlog:other-item", f"{CAPTURED}/other-item.md"),
    ],
)
def test_each_legacy_form_moves_to_the_header_then_the_entry_drops(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], need: str, reference: str
) -> None:
    repo = make_repo(
        tmp_path,
        {f"{CAPTURED}/w-one.md": record(), f"{BRIEFS}/b-one.md": "# Brief\n\n- **Status:** Ready\n"},
        open_=[slug_needs("w-one", need)],
    )
    data = plan(repo, capsys)
    [move] = needs_ops(data)
    [drop] = drops(data)
    assert manual(data) == []
    assert move["waiting_path"] == f"{CAPTURED}/w-one.md"
    assert move["depends_on_items"] == [reference]
    assert move["waiting_sha256"] == sha(record()) == drop["file_sha256"]
    assert move["entry_locator"] == drop["entry_locator"]
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert all(item["applied"] for item in result["per_operation"]), result
    assert (repo / CAPTURED / "w-one.md").read_text(encoding="utf-8") == (
        record() + f"- **Depends on:** {reference}\n"
    )
    assert "w-one" not in registry_text(repo)
    after = plan(repo, capsys)
    assert needs_ops(after) == [] and drops(after) == [] and all_manual(after) == []


def test_an_array_of_legacy_needs_is_added_in_order(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(
        tmp_path,
        {f"{CAPTURED}/w-two.md": record()},
        backlog=[slug_needs("w-two", ["work:spec/one", "ini-002:work:spec/two", "backlog:three", "work:spec/one"])],
    )
    [move] = needs_ops(plan(repo, capsys))
    assert move["depends_on_items"] == ["spec:one", "spec:two", f"{CAPTURED}/three.md"]
    code, result = apply(repo, capsys)
    assert code == 0, result
    text = (repo / CAPTURED / "w-two.md").read_text(encoding="utf-8")
    assert text.endswith(f"- **Depends on:** spec:one, spec:two, {CAPTURED}/three.md\n")
    assert "w-two" not in registry_text(repo)


def test_a_brief_reference_uses_the_slug_field_not_the_file_stem(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(
        tmp_path,
        {f"{CAPTURED}/w-three.md": record(), f"{BRIEFS}/stem-name.md": "# B\n\n- **Slug:** real-slug\n"},
        active=[slug_needs("w-three", f"brief:{BRIEFS}/stem-name.md")],
    )
    [move] = needs_ops(plan(repo, capsys))
    assert move["depends_on_items"] == ["brief:real-slug"]
    apply(repo, capsys)
    assert "- **Depends on:** brief:real-slug\n" in (repo / CAPTURED / "w-three.md").read_text(encoding="utf-8")


def test_a_brief_with_no_indexed_slug_is_one_manual_item_and_keeps_the_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(
        tmp_path,
        {f"{CAPTURED}/w-four.md": record()},
        open_=[slug_needs("w-four", f"brief:{BRIEFS}/missing.md")],
    )
    data = plan(repo, capsys)
    assert needs_ops(data) == [] and drops(data) == []
    assert [i["reason"] for i in all_manual(data)] == ["need-no-typed-reference"]
    assert all_manual(data)[0]["entry_locator"] == {"ini_slug": "", "collection": "backlog.open", "index": 0}
    before, files = registry_text(repo), captured_bytes(repo)
    code, _ = apply(repo, capsys)
    assert code == 0 and registry_text(repo) == before and captured_bytes(repo) == files


def test_a_header_that_already_holds_the_reference_gets_no_duplicate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    held = header_record("- **Depends on:** spec:one")
    repo = make_repo(
        tmp_path, {f"{CAPTURED}/w-five.md": held}, open_=[slug_needs("w-five", "work:spec/one")]
    )
    assert len(needs_ops(plan(repo, capsys))) == 1
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert (repo / CAPTURED / "w-five.md").read_text(encoding="utf-8") == held
    assert "w-five" not in registry_text(repo)


def test_a_wrapped_depends_on_line_is_one_manual_item_and_keeps_the_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    wrapped = header_record("- **Depends on:** spec:one,", "  spec:two")
    repo = make_repo(
        tmp_path, {f"{CAPTURED}/w-six.md": wrapped},
        open_=[slug_needs("w-six", "work:spec/three")],
    )
    data = plan(repo, capsys)
    assert needs_ops(data) == [] and drops(data) == []
    assert [i["reason"] for i in all_manual(data)] == ["header-not-writable"]
    before = registry_text(repo)
    apply(repo, capsys)
    assert registry_text(repo) == before
    assert (repo / CAPTURED / "w-six.md").read_text(encoding="utf-8") == wrapped


def test_a_non_legacy_need_is_exactly_one_manual_item_and_keeps_the_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(
        tmp_path,
        {f"{CAPTURED}/w-seven.md": record()},
        open_=[slug_needs("w-seven", ["work:spec/one", "intent:somewhere"])],
    )
    data = plan(repo, capsys)
    assert needs_ops(data) == [] and drops(data) == []
    assert [i["reason"] for i in all_manual(data)] == ["need-not-legacy"]
    before = registry_text(repo)
    apply(repo, capsys)
    assert registry_text(repo) == before


def test_legacy_needs_on_an_entry_the_same_plan_writes_a_file_for_settle_in_one_apply(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, open_=[slug_needs("fresh-need", "work:spec/one")])
    data = plan(repo, capsys)
    [write_op] = to_file_ops(data)
    [move] = needs_ops(data)
    [drop] = drops(data)
    assert move["waiting_sha256"] == drop["file_sha256"] == sha(write_op["record_text"])
    assert all_manual(data) == []
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert all(item["applied"] for item in result["per_operation"]), result
    text = (repo / CAPTURED / "fresh-need.md").read_text(encoding="utf-8")
    assert text.startswith(write_op["record_text"].split("\n## Summary")[0].rstrip("\n"))
    assert "- **Depends on:** spec:one\n" in text
    assert "fresh-need" not in registry_text(repo)
    after = plan(repo, capsys)
    assert needs_ops(after) == [] and drops(after) == [] and to_file_ops(after) == []
    assert all_manual(after) == []


def test_apply_refuses_the_move_and_the_drop_when_the_file_changed_after_the_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(
        tmp_path, {f"{CAPTURED}/w-eight.md": record()}, open_=[slug_needs("w-eight", "work:spec/one")]
    )
    plan(repo, capsys)
    (repo / CAPTURED / "w-eight.md").write_text(record(status="Closed"), encoding="utf-8")
    changed, before = captured_bytes(repo), registry_text(repo)
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert [i["reason"] for i in result["per_operation"]] == ["record-invalid"]
    assert captured_bytes(repo) == changed and registry_text(repo) == before
