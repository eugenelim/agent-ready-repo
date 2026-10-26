"""Construction tests for the `needs-to-header` repair.

Spec: docs/specs/depends-on-headers/spec.md (AC-0009, AC-0010, AC-0011, AC-0019,
AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0028, AC-0029,
AC-0030, AC-0031). Verification mode: TDD.

Each test builds a fixture repository under ``tmp_path`` and runs ``repair-plan``
and ``repair-apply`` in process through the script's ``main``.
"""
from __future__ import annotations

import difflib
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / ".apm/skills/workspace-status/scripts/workspace_status.py"
)
_MODULE_NAME = "workspace_status_depends_on_headers_repair"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


WS = _load()
PLAN = ".workspace-repair-plan.json"
WAITER = "docs/specs/waiter/spec.md"
PEER = "docs/specs/peer/spec.md"
OTHER = "docs/specs/other/spec.md"
BRIEFS = "docs/product/briefs"
INTENTS = "docs/product/intents"
COMPLETION = {
    "delivery_id": "d-1",
    "outcome": "completed",
    "completion_event": "merge",
    "evidence_ref": "pr:812",
}


# ── Fixture helpers ──────────────────────────────────────────────────────────


def entry(path: str, kind: str = "spec", needs: str = "[]") -> str:
    return (
        f'{{path = "{path}", kind = "{kind}", source = {{mode = "repo-origin"}}, '
        f'summary = "fixture", needs = {needs}}}'
    )


def local(kind: str, path: str, receipt: dict[str, str] | None = None) -> str:
    text = f'{{type = "local", kind = "{kind}", path = "{path}"'
    if receipt is not None:
        rendered = ", ".join(f'{k} = "{v}"' for k, v in receipt.items())
        text += f", receipt = {{{rendered}}}"
    return text + "}"


def cross(
    path: str,
    containing: str | None = None,
    receipt_id: str = "remote-prereq",
    revision: str = "remote-rev-9",
) -> str:
    return (
        f'{{type = "cross-repo", kind = "spec", path = "{path}", '
        f'containing_brief = "{containing or path}", receipt_id = "{receipt_id}", '
        f'accepted_revision = "{revision}"}}'
    )


def needs(*edges: str) -> str:
    return "[" + ", ".join(edges) + "]"


def spec_text(slug: str, status: str = "Approved", extra: str = "") -> str:
    return (
        f"# Spec: {slug}\n\n- **Status:** {status}\n- **Brief:** none\n{extra}\n"
        "## Outcome\n\nbody\n"
    )


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def workspace_text(
    queue: list[str], *, shipped: list[str] | None = None, extra: str = ""
) -> str:
    return (
        '["ini-001"]\nname = "Fixture"\nstatus = "active"\nmilestone = "m1"\n\n'
        '["ini-001".work]\n'
        f"queue = [{', '.join(queue)}]\nactive = []\n"
        f"shipped = [{', '.join(shipped or [])}]\n\n"
        '["ini-001".shaping_queue]\nactive = []\nbacklog = []\n'
        + extra
    )


def make_repo(
    root: Path,
    queue: list[str],
    files: dict[str, str] | None = None,
    *,
    shipped: list[str] | None = None,
    extra: str = "",
) -> Path:
    write(root, "workspace.toml", workspace_text(queue, shipped=shipped, extra=extra))
    for rel, text in (files or {}).items():
        write(root, rel, text)
    write(root, "AGENTS.md", "# Agents\n")
    return root


def basic_files() -> dict[str, str]:
    return {
        WAITER: spec_text("waiter"),
        PEER: spec_text("peer"),
        OTHER: spec_text("other"),
    }


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


def plan_file(root: Path) -> dict[str, Any]:
    return json.loads((root / PLAN).read_text(encoding="utf-8"))


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and not p.is_symlink() and p.name != PLAN
    }


def needs_ops(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        op for op in data["automatic_operations"]
        if op["operation_type"] in ("needs-to-header", "needs-drop-cooled")
    ]


def needs_findings(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in data["manual_findings"] if f["finding_type"] == 4]


def lifecycle_record(delivery_id: str, locator: str) -> str:
    return json.dumps(
        {
            "schema": "delivery-lifecycle-record.v1",
            "delivery_id": delivery_id,
            "locator": locator,
            "aliases": [],
            "fingerprint": "sha256:" + "0" * 64,
            "disposition": "cool-30-days",
            "post_closeout_result": "Cooling",
            "completion_event": "merge",
            "completion_evidence_ref": "commit:" + "1" * 40,
            "completed_on": "2026-01-01",
            "timezone": "Asia/Singapore",
            "review_on": "2026-01-31",
            "authority": {n: {"status": "confirmed"} for n in ("source", "write", "delete")},
            "confirmation_proof": "sha256:" + "2" * 64,
        }
    )


def simple_repo(root: Path, edge: str, files: dict[str, str] | None = None) -> Path:
    return make_repo(
        root, [entry(WAITER, needs=needs(edge))], {**basic_files(), **(files or {})}
    )


def recompute(root: Path, data: dict[str, Any]) -> None:
    data["plan_id"] = WS._recompute_plan_id(data)
    (root / PLAN).write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


# ── AC-0009, AC-0019, AC-0031: the operation and the plan file ───────────────


def test_operation_fields_and_plan_writes_only_its_plan_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = simple_repo(tmp_path, local("spec", PEER, COMPLETION))
    before = snapshot(repo)
    data = plan(repo, capsys)
    assert snapshot(repo) == before
    [op] = needs_ops(data)
    assert set(op) == {
        "operation_type", "waiting_path", "waiting_sha256",
        "registry_edges", "depends_on_items", "receipt_items",
    }
    assert op["operation_type"] == "needs-to-header"
    assert op["waiting_path"] == WAITER
    assert op["waiting_sha256"] == hashlib.sha256((repo / WAITER).read_bytes()).hexdigest()
    assert op["depends_on_items"] == ["spec:peer"]
    assert op["receipt_items"] == ["spec:peer completion d-1 completed merge pr:812"]
    assert op["registry_edges"] == [
        {
            "waiting_path": WAITER,
            "reference": "spec:peer",
            "receipt": ["completion", "d-1", "completed", "merge", "pr:812"],
        }
    ]
    assert plan_file(repo)["automatic_operations"] == data["automatic_operations"]


def test_intent_and_brief_targets_become_typed_references(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    files = {
        f"{INTENTS}/growth.md": "# Intent\n\n- **Slug:** growth\n- **Kind:** outcome\n",
        f"{BRIEFS}/handover.md": "# Brief\n\n- **Slug:** partner-handover\n- **Status:** Ready\n",
        "docs/product/notes/d1.md": "# Defect\n\n- **Kind:** defect\n",
    }
    edges = needs(
        local("intent", f"{INTENTS}/growth.md"),
        local("brief", f"{BRIEFS}/handover.md"),
        local("defect", "docs/product/notes/d1.md"),
        local("spec", PEER),
    )
    repo = make_repo(tmp_path, [entry(WAITER, needs=edges)], {**basic_files(), **files})
    [op] = needs_ops(plan(repo, capsys))
    assert op["depends_on_items"] == [
        "outcome:growth", "brief:partner-handover", "docs/product/notes/d1.md", "spec:peer",
    ]


# ── AC-0021, AC-0006: a cooled membership is never opened ────────────────────


def cooled_repo(root: Path) -> Path:
    edges = needs(local("spec", PEER))
    repo = make_repo(
        root,
        [entry(WAITER, needs=edges), entry(OTHER, needs=needs(local("spec", PEER)))],
        basic_files(),
    )
    write(repo, "docs/lifecycle/cooled.json", lifecycle_record("cooled", WAITER))
    return repo


def test_cooled_membership_drops_needs_without_opening_the_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = cooled_repo(tmp_path)
    (repo / WAITER).chmod(0)
    try:
        data = plan(repo, capsys)
    finally:
        (repo / WAITER).chmod(0o644)
    ops = {op["waiting_path"]: op for op in needs_ops(data)}
    drop = ops[WAITER]
    assert drop["operation_type"] == "needs-drop-cooled"
    assert "waiting_sha256" not in drop
    assert drop["dropped_cooled"] == [
        {"waiting_path": WAITER, "reference": "spec:peer", "receipt": None}
    ]
    assert ops[OTHER]["operation_type"] == "needs-to-header"


# ── AC-0029: a failed workspace yields only its cause ────────────────────────


def test_canonical_failure_yields_no_operation_and_no_needs_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    refusable = local("brief", f"{BRIEFS}/missing.md")
    repo = make_repo(
        tmp_path,
        [entry(WAITER, needs=needs(refusable))],
        basic_files(),
        extra='\n["ini-bad-slug"]\nname = "Bad"\nstatus = "active"\n',
    )
    data = plan(repo, capsys)
    codes = {f["code"] for f in data["canonical"]["findings"]}
    assert "invalid_workspace" in codes
    assert needs_ops(data) == [] and needs_findings(data) == []


# ── AC-0020: refusals ────────────────────────────────────────────────────────

LONG = "x" * 150


@pytest.mark.parametrize(
    ("case", "edge", "files", "reason"),
    [
        (
            "tombstoned-intent",
            local("intent", f"{INTENTS}/old.md"),
            {f"{INTENTS}/old.md": "# I\n\n- **Slug:** old\n- **Tombstone:** retired\n"},
            "intent-target-unusable",
        ),
        (
            "intent-without-slug",
            local("intent", f"{INTENTS}/bare.md"),
            {f"{INTENTS}/bare.md": "# I\n\n- **Kind:** outcome\n"},
            "intent-target-unusable",
        ),
        ("missing-intent", local("intent", f"{INTENTS}/gone.md"), {}, "missing-intent-target"),
        ("missing-brief", local("brief", f"{BRIEFS}/gone.md"), {}, "missing-brief-target"),
        (
            "kind-mismatch",
            local("design", "docs/product/notes/d.md"),
            {"docs/product/notes/d.md": "# D\n\n- **Kind:** defect\n"},
            "kind-mismatch",
        ),
        (
            "cross-repo-path",
            cross(f"{BRIEFS}/one.md", f"{BRIEFS}/two.md"),
            {
                f"{BRIEFS}/one.md": "# B\n\n- **Slug:** one\n",
                f"{BRIEFS}/two.md": "# B\n\n- **Slug:** two\n",
            },
            "cross-repo-path-mismatch",
        ),
        (
            "captured-receipt",
            local("defect", "docs/product/notes/d.md", COMPLETION),
            {"docs/product/notes/d.md": "# D\n\n- **Kind:** defect\n"},
            "captured-item-receipt",
        ),
        (
            "receipt-off-grammar",
            local("spec", PEER, {**COMPLETION, "outcome": "completed now"}),
            {},
            "receipt-off-grammar",
        ),
        (
            "coordination-off-grammar",
            cross(f"{BRIEFS}/one.md", receipt_id="bad id"),
            {f"{BRIEFS}/one.md": "# B\n\n- **Slug:** one\n"},
            "receipt-off-grammar",
        ),
        (
            "comma-path",
            local("defect", "docs/product/notes/a,b.md"),
            {"docs/product/notes/a,b.md": "# D\n\n- **Kind:** defect\n"},
            "edge-not-expressible",
        ),
        (
            "space-path",
            local("defect", "docs/product/notes/a b.md"),
            {"docs/product/notes/a b.md": "# D\n\n- **Kind:** defect\n"},
            "edge-not-expressible",
        ),
    ],
)
def test_unexpressible_edge_is_a_manual_finding_with_no_operation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    case: str,
    edge: str,
    files: dict[str, str],
    reason: str,
) -> None:
    repo = simple_repo(tmp_path, edge, files)
    data = plan(repo, capsys)
    assert needs_ops(data) == []
    [finding] = needs_findings(data)
    assert finding["reason"] == reason, case
    assert finding["spec_path"] == WAITER
    assert finding["edge"]["waiting_path"] == WAITER


def test_control_character_waiting_path_gets_no_operation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = 'docs/specs/w\\u0001/spec.md'
    repo = make_repo(tmp_path, [entry(bad, needs=needs(local("spec", PEER)))], basic_files())
    data = plan(repo, capsys)
    assert needs_ops(data) == []


def test_symlinked_waiting_item_is_refused_at_plan_time(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = simple_repo(tmp_path, local("spec", PEER))
    real = repo / "elsewhere.md"
    real.write_text((repo / WAITER).read_text(encoding="utf-8"), encoding="utf-8")
    (repo / WAITER).unlink()
    (repo / WAITER).symlink_to(real)
    data = plan(repo, capsys)
    assert needs_ops(data) == []
    [finding] = needs_findings(data)
    assert finding["reason"] == "waiting-item-unreadable"


def test_multi_linked_waiting_item_is_refused_at_plan_time(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = simple_repo(tmp_path, local("spec", PEER))
    os.link(repo / WAITER, repo / "alias.md")
    data = plan(repo, capsys)
    assert needs_ops(data) == []
    assert [f["reason"] for f in needs_findings(data)] == ["waiting-item-unreadable"]


# ── AC-0010, AC-0022, AC-0023: apply ─────────────────────────────────────────


def test_mixed_plan_is_built_validated_and_applied_by_type(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    shipped = "docs/specs/done/spec.md"
    repo = make_repo(
        tmp_path,
        [
            entry(shipped),
            entry(WAITER, needs=needs(local("spec", PEER))),
            entry(OTHER, needs=needs(local("spec", PEER))),
        ],
        {
            **basic_files(),
            shipped: spec_text("done", "Shipped"),
            "docs/specs/done/plan.md": "# Plan: done\n",
        },
    )
    write(repo, "docs/lifecycle/cooled.json", lifecycle_record("cooled", OTHER))
    data = plan(repo, capsys)
    kinds = [op["operation_type"] for op in data["automatic_operations"]]
    assert sorted(kinds) == ["needs-drop-cooled", "needs-to-header", "queue-to-shipped"]
    assert WS._validate_plan_structure(plan_file(repo)) is None
    code, result = apply(repo, capsys)
    assert code == 0 and result["operations_applied"] == 3, result
    assert all(item["applied"] for item in result["per_operation"])
    text = (repo / "workspace.toml").read_text(encoding="utf-8")
    assert "needs = [{" not in text
    assert "- **Depends on:** spec:peer" in (repo / WAITER).read_text(encoding="utf-8")
    assert (repo / OTHER).read_bytes() == spec_text("other").encode()


def test_apply_changes_only_the_needs_arrays_and_the_added_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    edge_a = local("spec", PEER, COMPLETION)
    edge_b = local("spec", OTHER)
    repo = make_repo(
        tmp_path,
        [entry(WAITER, needs=needs(edge_a, edge_b))],
        basic_files(),
        extra="\n# trailing comment\n",
    )
    original = (repo / "workspace.toml").read_text(encoding="utf-8")
    waiter_before = (repo / WAITER).read_text(encoding="utf-8")
    plan(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 0 and result["edges_equal"] is True, result
    assert (repo / "workspace.toml").read_text(encoding="utf-8") == original.replace(
        needs(edge_a, edge_b), "[]"
    )
    old_lines = waiter_before.splitlines(keepends=True)
    new_lines = (repo / WAITER).read_text(encoding="utf-8").splitlines(keepends=True)
    opcodes = difflib.SequenceMatcher(a=old_lines, b=new_lines).get_opcodes()
    assert {tag for tag, *_ in opcodes} == {"equal", "insert"}
    added = [line for line in new_lines if line not in old_lines]
    assert added == [
        "- **Depends on:** spec:peer, spec:other\n",
        "- **Dependency receipts:** spec:peer completion d-1 completed merge pr:812\n",
    ]


def test_existing_header_items_are_extended_not_repeated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    waiter = spec_text(
        "waiter",
        extra="- **Depends on:** spec:peer <!-- keep -->\n- **Owner:** someone\n",
    )
    repo = make_repo(
        tmp_path,
        [entry(WAITER, needs=needs(local("spec", PEER), local("spec", OTHER)))],
        {**basic_files(), WAITER: waiter},
    )
    plan(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 0 and result["edges_equal"] is True, result
    text = (repo / WAITER).read_text(encoding="utf-8")
    assert "- **Depends on:** spec:peer, spec:other <!-- keep -->\n" in text
    assert text.count("spec:peer") == 1 and text.count("spec:other") == 1


def test_spec_edge_appears_verbatim_in_every_edge_list(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    waiter = spec_text("waiter", extra="- **Depends on:** spec:peer\n")
    repo = make_repo(
        tmp_path,
        [entry(WAITER, needs=needs(local("spec", PEER))), entry(OTHER, needs=needs(local("spec", PEER)))],
        {**basic_files(), WAITER: waiter},
    )
    write(repo, "docs/lifecycle/cooled.json", lifecycle_record("cooled", OTHER))
    plan(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 0, result
    edge = {"waiting_path": WAITER, "reference": "spec:peer", "receipt": None}
    assert result["header_edges_before"] == [edge]
    assert result["registry_edges"] == [edge]
    assert result["header_edges_after"] == [edge]
    assert result["dropped_cooled"] == [{**edge, "waiting_path": OTHER}]
    assert result["edges_equal"] is True


def test_refusal_after_the_waiting_file_changes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = simple_repo(tmp_path, local("spec", PEER))
    plan(repo, capsys)
    with (repo / WAITER).open("a", encoding="utf-8") as handle:
        handle.write("changed\n")
    workspace_before = (repo / "workspace.toml").read_bytes()
    waiter_before = (repo / WAITER).read_bytes()
    code, result = apply(repo, capsys)
    assert code == 0 and result["operations_applied"] == 0
    assert result["per_operation"][0]["reason"] == "waiting_item_changed"
    assert (repo / "workspace.toml").read_bytes() == workspace_before
    assert (repo / WAITER).read_bytes() == waiter_before


def test_cooled_operation_is_refused_when_the_record_is_gone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = cooled_repo(tmp_path)
    plan(repo, capsys)
    (repo / "docs/lifecycle/cooled.json").unlink()
    workspace_before = (repo / "workspace.toml").read_bytes()
    _code, result = apply(repo, capsys)
    reasons = {item["path"]: item.get("reason") for item in result["per_operation"]}
    assert reasons[WAITER] == "no_longer_cooled"
    assert result["per_operation"][0]["applied"] is False
    waiter_entry_kept = "needs = [{" in (repo / "workspace.toml").read_text(encoding="utf-8")
    assert waiter_entry_kept
    assert workspace_before != (repo / "workspace.toml").read_bytes()  # OTHER migrated
    assert (repo / "workspace.toml").read_text(encoding="utf-8").count("needs = [{") == 1


def test_plan_edited_to_another_path_or_items_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = simple_repo(tmp_path, local("spec", PEER))
    plan(repo, capsys)
    agents_before = (repo / "AGENTS.md").read_bytes()
    data = plan_file(repo)
    data["automatic_operations"][0]["waiting_path"] = "AGENTS.md"
    recompute(repo, data)
    _code, result = apply(repo, capsys)
    assert result["per_operation"][0]["reason"] == "waiting_path_not_membership"
    assert (repo / "AGENTS.md").read_bytes() == agents_before

    plan(repo, capsys)
    data = plan_file(repo)
    data["automatic_operations"][0]["depends_on_items"].append("spec:extra")
    recompute(repo, data)
    waiter_before = (repo / WAITER).read_bytes()
    _code, result = apply(repo, capsys)
    assert result["per_operation"][0]["reason"] == "items_changed"
    assert (repo / WAITER).read_bytes() == waiter_before
    assert "needs = [{" in (repo / "workspace.toml").read_text(encoding="utf-8")


def test_waiting_file_replaced_by_a_symlink_after_plan_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = simple_repo(tmp_path, local("spec", PEER))
    plan(repo, capsys)
    copy = repo / "copy.md"
    copy.write_text((repo / WAITER).read_text(encoding="utf-8"), encoding="utf-8")
    (repo / WAITER).unlink()
    (repo / WAITER).symlink_to(copy)
    copy_before = copy.read_bytes()
    _code, result = apply(repo, capsys)
    assert result["per_operation"][0] == {
        "path": WAITER, "applied": False, "reason": "unsafe_waiting_path",
    }
    assert copy.read_bytes() == copy_before


# ── AC-0024: an interrupted apply ────────────────────────────────────────────


def test_interrupted_apply_then_clean_rerun_holds_each_item_once(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    second = "docs/specs/second/spec.md"
    repo = make_repo(
        tmp_path,
        [
            entry(WAITER, needs=needs(local("spec", PEER))),
            entry(second, needs=needs(local("spec", OTHER))),
        ],
        {**basic_files(), second: spec_text("second")},
    )
    plan(repo, capsys)
    workspace_before = (repo / "workspace.toml").read_bytes()
    original = WS._replace_waiting_file
    calls: list[str] = []

    def interrupted(root: Path, rel: str, sha: str, data: bytes) -> None:
        if calls:
            raise KeyboardInterrupt
        calls.append(rel)
        original(root, rel, sha, data)

    monkeypatch.setattr(WS, "_replace_waiting_file", interrupted)
    with pytest.raises(KeyboardInterrupt):
        apply(repo, capsys)
    monkeypatch.setattr(WS, "_replace_waiting_file", original)
    assert (repo / "workspace.toml").read_bytes() == workspace_before
    assert not (repo / ".workspace-repair.lock").exists()

    plan(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 0 and result["operations_applied"] == 2 and result["edges_equal"] is True
    assert (repo / WAITER).read_text(encoding="utf-8").count("spec:peer") == 1
    assert (repo / second).read_text(encoding="utf-8").count("spec:other") == 1
    assert "needs = [{" not in (repo / "workspace.toml").read_text(encoding="utf-8")


# ── AC-0011: the edge comparison ─────────────────────────────────────────────


def test_edges_are_unequal_when_a_reader_refused_item_is_planted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    waiter = spec_text("waiter", extra="- **Depends on:** the auth rework\n")
    repo = make_repo(
        tmp_path,
        [entry(WAITER, needs=needs(local("spec", PEER)))],
        {**basic_files(), WAITER: waiter},
    )
    plan(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 1
    assert result["edges_equal"] is False
    assert "needs = [{" in (repo / "workspace.toml").read_text(encoding="utf-8")


# ── AC-0028: echoed values ───────────────────────────────────────────────────


def test_oversized_and_control_character_items_are_echoed_without_content(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    oversized = "docs/notes/" + "/".join(["a" * 60] * 5)
    controlled = "spec:ctl\x01"
    receipt = "completion d-1 completed merge pr:812"
    waiter = spec_text(
        "waiter",
        extra=(
            f"- **Depends on:** {oversized}, {controlled}\n"
            f"- **Dependency receipts:** {oversized} {receipt}, {controlled} {receipt}\n"
        ),
    )
    repo = make_repo(
        tmp_path,
        [entry(WAITER, needs=needs(local("spec", PEER)))],
        {**basic_files(), WAITER: waiter},
    )
    plan(repo, capsys)
    _code, result = apply(repo, capsys)
    before = result["header_edges_before"]
    tokens = receipt.split()
    assert {"waiting_path": WAITER, "reference": "", "receipt": tokens} in before
    assert sum(edge["reference"] == "" for edge in before) == 2
    assert all(edge["waiting_path"] == WAITER for edge in before)
    assert oversized not in json.dumps(result)
    assert "\x01" not in json.dumps(result, ensure_ascii=False)


def test_plan_stdout_withholds_a_part_that_fails_while_the_file_keeps_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    oversized = "docs/product/notes/" + "/".join(["a" * 60] * 5) + ".md"
    repo = make_repo(
        tmp_path,
        [entry(WAITER, needs=needs(local("defect", oversized)))],
        {**basic_files(), oversized: "# D\n\n- **Kind:** defect\n"},
    )
    data = plan(repo, capsys)
    [op] = needs_ops(data)
    assert op["depends_on_items"] == [""]
    assert op["registry_edges"][0]["reference"] == ""
    assert op["registry_edges"][0]["waiting_path"] == WAITER
    assert plan_file(repo)["automatic_operations"][0]["depends_on_items"] == [oversized]


def test_long_coordination_receipt_is_carried_whole_and_migrated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    receipt_id, revision = "r" * 200, "v" * 200
    files = {f"{BRIEFS}/one.md": "# B\n\n- **Slug:** one\n- **Status:** Ready\n"}
    repo = simple_repo(
        tmp_path, cross(f"{BRIEFS}/one.md", receipt_id=receipt_id, revision=revision), files
    )
    data = plan(repo, capsys)
    line = f"brief:one coordination spec {receipt_id} {revision}"
    assert len(line) > 200
    assert plan_file(repo)["automatic_operations"][0]["receipt_items"] == [line]
    [echoed] = needs_ops(data)[0]["registry_edges"]
    assert echoed["receipt"] == ["coordination", "spec", receipt_id, revision]
    code, result = apply(repo, capsys)
    assert code == 0 and result["edges_equal"] is True, result
    assert line in (repo / WAITER).read_text(encoding="utf-8")
