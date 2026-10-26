"""Construction tests for the `captured-to-file` repair.

Spec: docs/specs/captured-item-files/spec.md (AC-0016 to AC-0022, AC-0024 to
AC-0028, AC-0030 to AC-0032, AC-0043, AC-0046, AC-0047). Verification mode: TDD.

Each test builds a fixture repository under ``tmp_path`` and runs ``repair-plan``
and ``repair-apply`` in process through the script's ``main``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

pytest.importorskip("tomlkit")

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / ".apm/skills/workspace-status/scripts/workspace_status.py"
)
_MODULE_NAME = "workspace_status_captured_item_files_repair"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


WS = _load()
PLAN = ".workspace-repair-plan.json"
CAPTURED = "docs/product/captured"
NOTES = "docs/product/notes"
SOURCE_SHA = "a" * 64


# ── Fixture helpers ──────────────────────────────────────────────────────────


def entry(path: str, kind: str = "defect", summary: str = "fixture", needs: str = "[]") -> str:
    return (
        f'{{path = "{path}", kind = "{kind}", source = {{mode = "repo-origin"}}, '
        f"summary = {json.dumps(summary)}, needs = {needs}}}"
    )


def legacy(slug: str, **fields: str) -> str:
    rendered = ", ".join(f"{k} = {json.dumps(v)}" for k, v in fields.items())
    return f"{{slug = {json.dumps(slug)}" + (f", {rendered}" if rendered else "") + "}"


def workspace_text(
    *,
    open_: list[str] | None = None,
    closed: list[str] | None = None,
    backlog: list[str] | None = None,
    active: list[str] | None = None,
    queue: list[str] | None = None,
    extra: str = "",
) -> str:
    def rows(values: list[str] | None) -> str:
        return "[\n" + "".join(f"  {v},\n" for v in values or []) + "]"

    return (
        "# fixture header\n"
        f"[backlog]\nopen = {rows(open_)}\nclosed = {rows(closed)}\n\n"
        '["ini-001"]\nname = "Fixture"\nstatus = "active"\nmilestone = "m1"\n\n'
        f'["ini-001".work]\nqueue = {rows(queue)}\nactive = []\nshipped = []\n\n'
        f'["ini-001".shaping_queue]\nactive = {rows(active)}\nbacklog = {rows(backlog)}\n' + extra
    )


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_repo(root: Path, files: dict[str, str] | None = None, **registry: Any) -> Path:
    write(root, "workspace.toml", workspace_text(**registry))
    for rel, text in (files or {}).items():
        write(root, rel, text)
    write(root, "AGENTS.md", "# Agents\n")
    return root


def note(status: str | None = None, extra: str = "", resolution: str | None = None) -> str:
    lines = ["# A note", ""]
    if status is not None:
        lines.append(f"- **Status:** {status}")
    if resolution is not None:
        lines.append(f"- **Resolution:** {resolution}")
    if extra:
        lines.append(extra)
    return "\n".join(lines) + "\n"


def spec_text(slug: str, extra: str = "") -> str:
    return f"# Spec: {slug}\n\n- **Status:** Approved\n- **Brief:** none\n{extra}\n## Outcome\n\nbody\n"


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


def recompute(root: Path, data: dict[str, Any]) -> None:
    data["plan_id"] = WS._recompute_plan_id(data)
    (root / PLAN).write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and not p.is_symlink() and p.name != PLAN
    }


def captured_ops(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        op for op in data["automatic_operations"] if op["operation_type"] == "captured-to-file"
    ]


def captured_findings(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in data["manual_findings"] if f["finding_type"] == 5]


def by_record(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {op["record_path"]: op for op in captured_ops(data)}


def slugs(data: dict[str, Any]) -> set[str]:
    return {op["record_path"].rpartition("/")[2].removesuffix(".md") for op in captured_ops(data)}


def reasons(data: dict[str, Any]) -> list[str]:
    return [f["reason"] for f in captured_findings(data)]


def lifecycle_record(delivery_id: str, locator: str) -> str:
    return json.dumps({
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
    })


def one_defect(root: Path, summary: str = "a defect", extra: str = "", notes: str = NOTES) -> Path:
    return make_repo(
        root,
        {f"{notes}/d1.md": note(extra=extra)},
        open_=[entry(f"{notes}/d1.md", summary=summary)],
    )


# ── AC-0016, AC-0017, AC-0032: the operation and the plan file ───────────────


def test_membership_operation_fields_and_plan_leaves_every_other_byte(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(
        tmp_path,
        extra="- **Depends on:** spec:peer, docs/product/notes/other.md\n"
        "- **Dependency receipts:** spec:peer completion d-1 completed merge pr:812",
    )
    before = snapshot(repo)
    data = plan(repo, capsys)
    assert snapshot(repo) == before
    [op] = captured_ops(data)
    assert set(op) == {
        "operation_type",
        "record_path",
        "record_text",
        "entry_locator",
        "source_path",
        "source_sha256",
        "registry_fingerprint",
        "depends_on_items",
        "receipt_items",
    }
    assert op["record_path"] == f"{CAPTURED}/d1.md"
    assert op["entry_locator"] == {"collection": "backlog.open", "index": 0}
    assert op["source_path"] == f"{NOTES}/d1.md"
    assert op["source_sha256"] == hashlib.sha256((repo / NOTES / "d1.md").read_bytes()).hexdigest()
    assert len(op["registry_fingerprint"]) == 64
    assert op["depends_on_items"] == ["spec:peer", "docs/product/notes/other.md"]
    assert op["receipt_items"] == ["spec:peer completion d-1 completed merge pr:812"]
    assert plan_file(repo)["automatic_operations"] == data["automatic_operations"]
    assert data["manual_findings"] == []


def test_legacy_operation_fields(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = make_repo(tmp_path, open_=[legacy("a-legacy-thing", summary="why")])
    [op] = captured_ops(plan(repo, capsys))
    assert set(op) == {"operation_type", "record_path", "record_text", "entry_locator", "slug"}
    assert op["slug"] == "a-legacy-thing"
    assert op["record_path"] == f"{CAPTURED}/a-legacy-thing.md"
    assert op["entry_locator"] == {"collection": "backlog.open", "index": 0}


# ── AC-0018: slugs are fixed by the whole set ────────────────────────────────


def collision_repo(root: Path) -> Path:
    paths = [
        "docs/specs/a/notes/verification-ledger.md",
        "docs/specs/b/notes/verification-ledger.md",
        "docs/specs/a/notes/follow-ons.md",
        "docs/specs/b/notes/follow-ons.md",
        "docs/specs/c/notes/follow-ons.md",
        "docs/product/x/manifest.example.yaml",
        "docs/product/dir/___.md",
        "docs/product/area/legacy-thing.md",
    ]
    return make_repo(
        root,
        {p: note() for p in paths},
        open_=[entry(p) for p in paths] + [legacy("legacy-thing", summary="legacy")],
    )


def test_slug_collision_sets(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = plan(collision_repo(tmp_path), capsys)
    assert captured_findings(data) == []
    assert slugs(data) == {
        "a-verification-ledger",
        "b-verification-ledger",
        "a-follow-ons",
        "b-follow-ons",
        "c-follow-ons",
        "manifest-example",
        "dir-",
        "area-legacy-thing",
        "legacy-thing",
    }


def test_slugs_are_the_same_after_the_legacy_record_exists(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = collision_repo(tmp_path)
    first = slugs(plan(repo, capsys))
    write(
        repo,
        f"{CAPTURED}/legacy-thing.md",
        by_record(plan(repo, capsys))[f"{CAPTURED}/legacy-thing.md"]["record_text"],
    )
    second = plan(repo, capsys)
    assert captured_findings(second) == []
    assert slugs(second) == first - {"legacy-thing"}


def test_a_refused_twin_keeps_its_prefix_after_the_other_migrated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    twin_a, twin_b = "docs/specs/a/notes/x.md", "docs/specs/b/notes/x.md"
    repo = make_repo(
        tmp_path,
        {twin_a: note(), twin_b: note(status="Closed")},
        open_=[entry(twin_a), entry(twin_b)],
    )
    first = plan(repo, capsys)
    assert slugs(first) == {"a-x"}
    [finding] = captured_findings(first)
    assert (finding["reason"], finding["slug"]) == ("status-conflict", "b-x")
    code, _ = apply(repo, capsys)
    assert code == 0
    second = plan(repo, capsys)
    assert captured_ops(second) == []
    [again] = captured_findings(second)
    assert (again["reason"], again["slug"]) == ("status-conflict", "b-x")


# ── AC-0019, AC-0020: the record text ────────────────────────────────────────


def test_record_text_for_a_file_backed_defect(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(tmp_path, summary="Broken thing")
    [op] = captured_ops(plan(repo, capsys))
    assert op["record_text"] == (
        "# D1\n\n- **Status:** Open\n- **Kind:** defect\n"
        f"- **Detail:** {NOTES}/d1.md\n\n## Summary\n\nBroken thing\n"
    )


def test_record_text_copies_a_design_notes_dependency_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{NOTES}/portfolio-entry.md"
    lines = (
        "- **Depends on:** spec:peer, docs/product/notes/other.md\n"
        "- **Dependency receipts:** spec:peer completion d-1 completed merge pr:812"
    )
    repo = make_repo(
        tmp_path,
        {path: note(status="Draft", extra=lines)},
        open_=[entry(path, kind="design", summary="Question")],
    )
    [op] = captured_ops(plan(repo, capsys))
    assert op["record_text"] == (
        "# Portfolio entry\n\n- **Status:** Open\n- **Kind:** design\n"
        f"- **Detail:** {path}\n"
        "- **Depends on:** spec:peer, docs/product/notes/other.md\n"
        "- **Dependency receipts:** spec:peer completion d-1 completed merge pr:812\n"
        "\n## Summary\n\nQuestion\n"
    )


def test_record_text_for_a_legacy_entry_with_intent_and_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(
        tmp_path,
        {
            "docs/product/intents/growth.md": "# Intent\n\n- **Slug:** growth\n- **Kind:** outcome\n"
        },
        open_=[legacy("grow-more", summary="Do it.", intent="docs/product/intents/growth.md")],
    )
    [op] = captured_ops(plan(repo, capsys))
    assert op["record_text"] == (
        "# Grow more\n\n- **Status:** Open\n- **Kind:** defect\n"
        "- **Parent intent:** outcome:growth\n\n## Summary\n\nDo it.\n"
    )


def test_record_text_for_a_legacy_shape_entry_with_no_kind(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, backlog=[legacy("shape-me", type="shape")])
    [op] = captured_ops(plan(repo, capsys))
    assert (
        op["record_text"]
        == "# Shape me\n\n- **Status:** Open\n- **Kind:** intent\n- **Type:** shape\n"
    )


@pytest.mark.parametrize(
    ("type_", "kind"),
    [("shape", "intent"), ("strategy", "intent"), ("research", "research"), ("design", "design")],
)
def test_legacy_kind_follows_its_type(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], type_: str, kind: str
) -> None:
    repo = make_repo(tmp_path, open_=[legacy("an-item", type=type_)])
    [op] = captured_ops(plan(repo, capsys))
    assert f"- **Kind:** {kind}\n- **Type:** {type_}\n" in op["record_text"]


def test_record_text_for_a_closed_defect_copies_its_resolution(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{NOTES}/old.md"
    repo = make_repo(
        tmp_path,
        {path: note(status="Closed", resolution="declined")},
        closed=[entry(path, summary="Gone")],
    )
    [op] = captured_ops(plan(repo, capsys))
    assert op["record_text"] == (
        "# Old\n\n- **Status:** Closed\n- **Kind:** defect\n- **Resolution:** declined\n"
        f"- **Detail:** {path}\n\n## Summary\n\nGone\n"
    )


def test_a_summary_with_header_lines_stays_under_its_heading(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(
        tmp_path,
        open_=[legacy("sneaky", summary="text\n- **Type:** strategy\n- **Kind:** design")],
    )
    [op] = captured_ops(plan(repo, capsys))
    assert op["record_text"].endswith(
        "## Summary\n\ntext\n- **Type:** strategy\n- **Kind:** design\n"
    )
    code, _ = apply(repo, capsys)
    assert code == 0
    engine = WS._engine
    fields, failing = engine.parse_captured_item((repo / op["record_path"]).read_text())
    assert failing is None and fields is not None
    assert fields["type"] is None and fields["kind"] == "defect"
    assert engine.check_shaping_guard(repo, "sneaky", frozenset()) is None


def test_a_summary_with_a_control_character_is_a_manual_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, open_=[legacy("escapes", summary="a\x1b[31mb")])
    data = plan(repo, capsys)
    assert captured_ops(data) == []
    assert reasons(data) == ["summary-control-character"]


# ── AC-0021: one manual finding per case ─────────────────────────────────────


def refused_repo(case: str, root: Path) -> tuple[Path, str]:
    """A repository holding one entry the repair must refuse, and the reason."""
    path = f"{NOTES}/n.md"
    if case == "source-missing":
        return make_repo(root, open_=[entry(path)]), "source-missing"
    if case == "source-not-confined":
        write(root, "elsewhere.md", note())
        make_repo(root, open_=[entry(path)])
        (root / NOTES).mkdir(parents=True, exist_ok=True)
        Path(root / path).symlink_to(root / "elsewhere.md")
        return root, "source-unreadable"
    if case == "duplicate":
        return make_repo(
            root, {path: note()}, open_=[entry(path)], backlog=[entry(path, "design")]
        ), "duplicate-membership"
    if case == "dependency-needs":
        waiter = "docs/specs/w/spec.md"
        needs = f'[{{type = "local", kind = "defect", path = "{path}"}}]'
        return make_repo(
            root,
            {path: note(), waiter: spec_text("w")},
            open_=[entry(path)],
            queue=[entry(waiter, "spec", needs=needs)],
        ), "source-is-dependency-target"
    if case == "dependency-header":
        waiter = "docs/specs/w/spec.md"
        return make_repo(
            root,
            {path: note(), waiter: spec_text("w", f"- **Depends on:** {path}\n")},
            open_=[entry(path)],
            queue=[entry(waiter, "spec")],
        ), "source-is-dependency-target"
    if case == "open-defect-closed":
        return make_repo(root, {path: note("Closed")}, open_=[entry(path)]), "status-conflict"
    if case == "open-design-approved":
        return make_repo(
            root, {path: note("Approved")}, open_=[entry(path, "design")]
        ), "status-conflict"
    if case == "open-design-no-status":
        return make_repo(root, {path: note()}, open_=[entry(path, "design")]), "status-conflict"
    if case == "backlog-design-approved":
        return make_repo(
            root, {path: note("Approved")}, backlog=[entry(path, "design")]
        ), "status-conflict"
    if case == "active-intent-accepted":
        return make_repo(
            root, {path: note("Accepted")}, active=[entry(path, "intent")]
        ), "status-conflict"
    if case == "active-research-complete":
        return make_repo(
            root, {path: note("Complete")}, active=[entry(path, "research")]
        ), "status-conflict"
    if case == "closed-defect-open":
        return make_repo(root, {path: note("Open")}, closed=[entry(path)]), "status-conflict"
    if case == "closed-defect-bad-resolution":
        return make_repo(
            root, {path: note("Closed", resolution="wontfix")}, closed=[entry(path)]
        ), "status-conflict"
    if case == "slug-invalid":
        paths = ["docs/Area/a.md", "docs/Other/a.md"]
        return make_repo(
            root, {p: note() for p in paths}, open_=[entry(p) for p in paths]
        ), "slug-invalid"
    if case == "slug-collision":
        paths = ["docs/p/q/x.md", "docs/p/q/x.yaml"]
        return make_repo(
            root, {p: note() for p in paths}, open_=[entry(p) for p in paths]
        ), "slug-collision"
    if case == "deferral-anchor":
        paths = ["docs/specs/a/notes/ledger.md", "docs/specs/b/notes/ledger.md"]
        return make_repo(
            root,
            {
                **{p: note() for p in paths},
                "docs/specs/z/spec.md": spec_text("z", "- AC (deferred: ledger)\n"),
            },
            open_=[entry(p) for p in paths],
        ), "deferral-anchor"
    if case == "record-differs":
        return make_repo(
            root, {path: note(), f"{CAPTURED}/n.md": "# other\n"}, open_=[entry(path)]
        ), "record-differs"
    if case == "legacy-signal":
        return make_repo(root, backlog=[legacy("sig", type="signal")]), "legacy-kind-unassignable"
    if case == "legacy-bad-type":
        return make_repo(root, backlog=[legacy("sig", type="bogus")]), "legacy-kind-unassignable"
    if case == "intent-not-live":
        return make_repo(
            root, open_=[legacy("gap", intent="docs/product/intents/missing.md")]
        ), "intent-not-live"
    if case == "summary-control":
        return make_repo(
            root, open_=[legacy("gap", summary="a\x07b")]
        ), "summary-control-character"
    if case == "summary-c1-control":
        return make_repo(
            root, open_=[legacy("gap", summary="a\x85b")]
        ), "summary-control-character"
    if case == "read-back":
        return make_repo(root, closed=[legacy("gap")]), "record-read-back"
    raise AssertionError(case)


REFUSED_CASES = [
    "source-missing",
    "source-not-confined",
    "duplicate",
    "dependency-needs",
    "dependency-header",
    "open-defect-closed",
    "open-design-approved",
    "open-design-no-status",
    "backlog-design-approved",
    "active-intent-accepted",
    "active-research-complete",
    "closed-defect-open",
    "closed-defect-bad-resolution",
    "slug-invalid",
    "slug-collision",
    "deferral-anchor",
    "record-differs",
    "legacy-signal",
    "legacy-bad-type",
    "intent-not-live",
    "summary-control",
    "summary-c1-control",
    "read-back",
]


@pytest.mark.parametrize("case", REFUSED_CASES)
def test_each_refusal_is_one_manual_finding_with_no_operation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], case: str
) -> None:
    repo, reason = refused_repo(case, tmp_path)
    before = snapshot(repo)
    data = plan(repo, capsys)
    assert snapshot(repo) == before
    assert reason in reasons(data)
    refused = [f for f in captured_findings(data) if f["reason"] == reason]
    if case in ("duplicate", "slug-invalid", "slug-collision", "deferral-anchor"):
        assert len(refused) >= 1
    else:
        assert len(refused) == 1
    for finding in refused:
        assert finding["spec_path"] or finding["slug"]
        if finding["spec_path"]:
            assert finding["spec_path"] in {
                f"{NOTES}/n.md",
                "docs/Area/a.md",
                "docs/Other/a.md",
                "docs/p/q/x.md",
                "docs/p/q/x.yaml",
                "docs/specs/a/notes/ledger.md",
                "docs/specs/b/notes/ledger.md",
            }
    refused_paths = {f["spec_path"] for f in refused}
    assert all(op.get("source_path") not in refused_paths for op in captured_ops(data))
    if case not in ("dependency-needs", "dependency-header"):
        assert captured_ops(data) == []


def test_typed_needs_refuse_the_record_and_keep_the_needs_to_header_operation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{NOTES}/n.md"
    peer = "docs/specs/peer/spec.md"
    needs = f'[{{type = "local", kind = "spec", path = "{peer}"}}]'
    repo = make_repo(
        tmp_path,
        {path: note(), peer: spec_text("peer")},
        open_=[entry(path, needs=needs)],
        queue=[entry(peer, "spec")],
    )
    data = plan(repo, capsys)
    assert captured_ops(data) == []
    assert reasons(data) == ["typed-needs-remain"]
    kinds = [op["operation_type"] for op in data["automatic_operations"]]
    assert kinds == ["needs-to-header"]


def test_a_cooled_unmigrated_membership_gets_no_operation_and_no_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = f"{NOTES}/cooled.md"
    repo = make_repo(tmp_path, {path: note(status="Closed")}, open_=[entry(path)])
    write(repo, "docs/lifecycle/cooled.json", lifecycle_record("cooled", path))
    (repo / path).chmod(0)
    try:
        data = plan(repo, capsys)
    finally:
        (repo / path).chmod(0o644)
    assert captured_ops(data) == []
    assert captured_findings(data) == []


# ── AC-0043: a legacy entry whose slug names a record ────────────────────────


def derived_legacy_record(root: Path, capsys: pytest.CaptureFixture[str]) -> str:
    [op] = captured_ops(plan(root, capsys))
    return str(op["record_text"])


@pytest.mark.parametrize(
    "variant", ["no-type", "extra-detail", "invalid", "cut-short", "directory"]
)
def test_legacy_record_that_differs_is_a_manual_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], variant: str
) -> None:
    repo = make_repo(
        tmp_path, backlog=[legacy("shape-me", type="shape", summary="Some summary text")]
    )
    derived = derived_legacy_record(repo, capsys)
    record = repo / CAPTURED / "shape-me.md"
    record.parent.mkdir(parents=True)
    if variant == "directory":
        record.mkdir()
    else:
        text = {
            "no-type": derived.replace("- **Type:** shape\n", ""),
            "extra-detail": derived.replace(
                "\n\n## Summary", "\n- **Detail:** docs/x.md\n\n## Summary"
            ),
            "invalid": derived.replace("- **Kind:** intent\n", ""),
            "cut-short": derived[: derived.index("Some summary") + 4],
        }[variant]
        record.write_text(text, encoding="utf-8")
    data = plan(repo, capsys)
    assert captured_ops(data) == []
    [finding] = captured_findings(data)
    assert finding["reason"] == "record-differs"
    assert finding["slug"] == "shape-me"
    assert finding["record_path"] == f"{CAPTURED}/shape-me.md"


def test_an_identical_legacy_record_needs_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, backlog=[legacy("shape-me", type="shape")])
    write(repo, f"{CAPTURED}/shape-me.md", derived_legacy_record(repo, capsys))
    data = plan(repo, capsys)
    assert captured_ops(data) == [] and captured_findings(data) == []


# ── AC-0022: a failed canonical read plans nothing ───────────────────────────


def test_canonical_failure_yields_no_operation_and_no_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(
        tmp_path,
        {f"{NOTES}/d1.md": note(status="Closed"), f"{NOTES}/d2.md": note()},
        open_=[entry(f"{NOTES}/d1.md"), entry(f"{NOTES}/d2.md"), legacy("a-legacy")],
        extra='\n["ini-001".brief_queue]\ndraft = "not a list"\n',
    )
    data = plan(repo, capsys)
    assert any(
        f["code"] in ("invalid_workspace", "configuration_mismatch")
        for f in data["canonical"]["findings"]
    )
    assert captured_ops(data) == [] and captured_findings(data) == []


# ── AC-0024, AC-0025: apply ──────────────────────────────────────────────────


def mixed_repo(root: Path) -> Path:
    dep = f"{NOTES}/dep.md"
    closed = f"{NOTES}/closed.md"
    return make_repo(
        root,
        {
            f"{NOTES}/d1.md": note(extra="- **Depends on:** spec:peer"),
            dep: note(status="Draft"),
            closed: note(status="Closed", resolution="fixed"),
            "docs/specs/peer/spec.md": spec_text("peer"),
        },
        open_=[entry(f"{NOTES}/d1.md"), entry(dep, "design"), legacy("legacy-one", summary="x")],
        closed=[entry(closed)],
        queue=[entry("docs/specs/peer/spec.md", "spec")],
    )


def test_apply_writes_records_then_repoints_paths_and_nothing_else(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = mixed_repo(tmp_path)
    data = plan(repo, capsys)
    before = snapshot(repo)
    workspace_before = (repo / "workspace.toml").read_text(encoding="utf-8")
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert result["operations_applied"] == 4
    after = snapshot(repo)
    records = {op["record_path"]: op for op in captured_ops(data)}
    assert set(after) - set(before) == set(records)
    for rel, text in before.items():
        if rel != "workspace.toml":
            assert after[rel] == text, rel
    for rel, op in records.items():
        assert after[rel] == op["record_text"].encode("utf-8")
    expected = workspace_before
    for op in records.values():
        if "source_path" in op:
            expected = expected.replace(
                f'path = "{op["source_path"]}"', f'path = "{op["record_path"]}"'
            )
    assert after["workspace.toml"] == expected.encode("utf-8")
    assert not (repo / ".workspace-repair.lock").exists()
    again = plan(repo, capsys)
    assert captured_ops(again) == [] and captured_findings(again) == []


def test_apply_report_and_equal_edges_keyed_by_record_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = mixed_repo(tmp_path)
    plan(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 0 and result["captured_equal"] is True
    assert {(e["slug"], e["kind"], e["source_path"]) for e in result["captured_before"]} == {
        ("d1", "defect", f"{NOTES}/d1.md"),
        ("dep", "design", f"{NOTES}/dep.md"),
        ("closed", "defect", f"{NOTES}/closed.md"),
        ("legacy-one", "defect", None),
    }
    after = {e["slug"]: e for e in result["captured_after"]}
    assert after["closed"]["resolution"] == "fixed" and after["closed"]["status"] == "Closed"
    assert after["dep"]["detail"] == f"{NOTES}/dep.md"
    edge = {"waiting_path": f"{CAPTURED}/d1.md", "reference": "spec:peer", "receipt": None}
    assert result["header_edges_before"] == [edge]
    assert result["header_edges_after"] == [edge]


def test_apply_kept_record_directory_is_created(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(tmp_path)
    assert not (repo / "docs/product/captured").exists()
    plan(repo, capsys)
    code, _ = apply(repo, capsys)
    assert code == 0 and (repo / CAPTURED / "d1.md").is_file()


def test_every_source_file_is_byte_identical_after_apply(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = collision_repo(tmp_path)
    sources = {p: (repo / p).read_bytes() for p in snapshot(repo) if p != "workspace.toml"}
    plan(repo, capsys)
    code, _ = apply(repo, capsys)
    assert code == 0
    for rel, data in sources.items():
        assert (repo / rel).read_bytes() == data


def test_a_plan_with_needs_and_captured_operations_applies_each_by_its_own_contract(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    waiter, peer = "docs/specs/waiter/spec.md", "docs/specs/peer/spec.md"
    needs = f'[{{type = "local", kind = "spec", path = "{peer}"}}]'
    repo = make_repo(
        tmp_path,
        {waiter: spec_text("waiter"), peer: spec_text("peer"), f"{NOTES}/d1.md": note()},
        open_=[entry(f"{NOTES}/d1.md")],
        queue=[entry(waiter, "spec", needs=needs), entry(peer, "spec")],
    )
    data = plan(repo, capsys)
    kinds = sorted(op["operation_type"] for op in data["automatic_operations"])
    assert kinds == ["captured-to-file", "needs-to-header"]
    before = snapshot(repo)
    code, result = apply(repo, capsys)
    assert code == 0, result
    after = snapshot(repo)
    assert after[waiter].decode().startswith("# Spec: waiter\n\n- **Status:** Approved")
    assert "- **Depends on:** spec:peer" in after[waiter].decode()
    assert after[peer] == before[peer] and after[f"{NOTES}/d1.md"] == before[f"{NOTES}/d1.md"]
    assert set(after) - set(before) == {f"{CAPTURED}/d1.md"}
    workspace = after["workspace.toml"].decode()
    assert f'path = "{CAPTURED}/d1.md"' in workspace and "needs = []" in workspace
    assert result["edges_equal"] is True and result["captured_equal"] is True


# ── AC-0026: the plan is re-derived under the lock ───────────────────────────


def tampered(
    root: Path, capsys: pytest.CaptureFixture[str], change: Any
) -> tuple[int, dict[str, Any], dict[str, bytes]]:
    data = plan(root, capsys)
    change(data)
    recompute(root, data)
    before = snapshot(root)
    code, result = apply(root, capsys)
    assert snapshot(root) == before
    return code, result, before


def first_op(data: dict[str, Any]) -> dict[str, Any]:
    return captured_ops(data)[0]


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("source_path", f"{NOTES}/d2.md", "operation_changed"),
        ("record_path", f"{CAPTURED}/renamed.md", "operation_changed"),
        ("entry_locator", {"collection": "backlog.closed", "index": 0}, "operation_changed"),
        ("record_text", "# Replaced\n", "operation_changed"),
        ("source_sha256", SOURCE_SHA, "source_changed"),
        ("registry_fingerprint", SOURCE_SHA, "registry_changed"),
        ("depends_on_items", ["spec:other"], "operation_changed"),
    ],
)
def test_a_tampered_membership_operation_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], field: str, value: Any, reason: str
) -> None:
    repo = one_defect(tmp_path)
    write(repo, f"{NOTES}/d2.md", (repo / NOTES / "d1.md").read_text())

    def change(data: dict[str, Any]) -> None:
        first_op(data)[field] = value

    code, result, _ = tampered(repo, capsys, change)
    assert code == 0 and result["operations_applied"] == 0
    assert [(o["applied"], o["reason"]) for o in result["per_operation"]] == [(False, reason)]
    assert not (repo / CAPTURED).exists()


def test_a_tampered_slug_is_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = make_repo(tmp_path, open_=[legacy("a-legacy")])

    def change(data: dict[str, Any]) -> None:
        first_op(data)["slug"] = "another"

    code, result, _ = tampered(repo, capsys, change)
    assert code == 0
    assert [(o["applied"], o["reason"]) for o in result["per_operation"]] == [
        (False, "operation_changed")
    ]
    assert not (repo / CAPTURED).exists()


def test_a_source_changed_after_planning_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(tmp_path)
    plan(repo, capsys)
    write(repo, f"{NOTES}/d1.md", note(extra="- **Depends on:** spec:late"))
    before = snapshot(repo)
    code, result = apply(repo, capsys)
    assert code == 0
    assert [o["reason"] for o in result["per_operation"]] == ["source_changed"]
    assert snapshot(repo) == before


def test_a_registry_changed_after_planning_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(tmp_path)
    plan(repo, capsys)
    ws = repo / "workspace.toml"
    ws.write_text(ws.read_text().replace('summary = "a defect"', 'summary = "edited"'))
    before = snapshot(repo)
    code, result = apply(repo, capsys)
    assert code == 2 and result["reason"] == "fingerprint_mismatch"
    assert snapshot(repo) == before


def test_a_membership_cooled_after_planning_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(tmp_path)
    plan(repo, capsys)
    write(repo, "docs/lifecycle/cooled.json", lifecycle_record("cooled", f"{NOTES}/d1.md"))
    before = snapshot(repo)
    code, result = apply(repo, capsys)
    assert code == 0
    assert [o["reason"] for o in result["per_operation"]] == ["membership_cooled"]
    assert snapshot(repo) == before


# ── AC-0027, AC-0046, AC-0047: how a record is created ───────────────────────


def planned_one(root: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    data = plan(root, capsys)
    return first_op(data)


def refusal_reasons(result: dict[str, Any]) -> list[str]:
    return [o["reason"] for o in result["per_operation"] if not o["applied"]]


def test_an_occupied_record_path_is_refused_and_untouched(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(tmp_path)
    plan(repo, capsys)
    write(repo, f"{CAPTURED}/d1.md", "# other bytes\n")
    before = snapshot(repo)
    code, result = apply(repo, capsys)
    assert code == 0 and refusal_reasons(result) == ["record_path_occupied"]
    assert snapshot(repo) == before


def test_a_symlink_at_the_record_path_is_refused_and_not_followed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(tmp_path)
    plan(repo, capsys)
    (repo / CAPTURED).mkdir(parents=True)
    outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
    outside.write_text("untouched\n")
    Path(repo / CAPTURED / "d1.md").symlink_to(outside)
    code, result = apply(repo, capsys)
    assert code == 0 and refusal_reasons(result) == ["record_path_occupied"]
    assert outside.read_text() == "untouched\n"
    assert 'path = "docs/product/notes/d1.md"' in (repo / "workspace.toml").read_text()


def test_a_hard_linked_record_holding_the_planned_bytes_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(tmp_path)
    op = planned_one(repo, capsys)
    (repo / CAPTURED).mkdir(parents=True)
    other = tmp_path.parent / f"{tmp_path.name}-twin.md"
    other.write_text(op["record_text"])
    os.link(other, repo / CAPTURED / "d1.md")
    code, result = apply(repo, capsys)
    assert code == 0 and refusal_reasons(result) == ["record_path_occupied"]
    assert 'path = "docs/product/notes/d1.md"' in (repo / "workspace.toml").read_text()


@pytest.mark.parametrize("linked", ["docs/product", "docs/product/captured"])
def test_a_symlinked_directory_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], linked: str
) -> None:
    repo = one_defect(tmp_path / "repo", notes="docs/specs/x/notes")
    plan(repo, capsys)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    if linked == "docs/product/captured":
        (repo / "docs/product").mkdir(parents=True, exist_ok=True)
    else:
        (repo / "docs").mkdir(exist_ok=True)
    Path(repo / linked).symlink_to(elsewhere)
    code, result = apply(repo, capsys)
    assert code == 0 and refusal_reasons(result) == ["record_directory_unsafe"]
    assert list(elsewhere.iterdir()) == []
    assert 'path = "docs/specs/x/notes/d1.md"' in (repo / "workspace.toml").read_text()


def test_an_identical_confined_record_is_kept(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(tmp_path)
    op = planned_one(repo, capsys)
    write(repo, op["record_path"], op["record_text"])
    data = plan(repo, capsys)
    assert len(captured_ops(data)) == 1 and captured_findings(data) == []
    code, result = apply(repo, capsys)
    assert code == 0 and result["per_operation"][0]["record"] == "kept"
    assert 'path = "docs/product/captured/d1.md"' in (repo / "workspace.toml").read_text()
    assert result["captured_equal"] is True


# ── AC-0028: interruption and cut-short records ──────────────────────────────


def test_interrupted_apply_then_rerun_writes_the_same_records(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = mixed_repo(tmp_path)
    data = plan(repo, capsys)
    original = WS._write_record
    calls: list[str] = []

    def interrupting(root: Path, record_path: str, payload: bytes) -> str:
        if calls:
            raise KeyboardInterrupt
        calls.append(record_path)
        return str(original(root, record_path, payload))

    monkeypatch.setattr(WS, "_write_record", interrupting)
    workspace_before = (repo / "workspace.toml").read_bytes()
    with pytest.raises(KeyboardInterrupt):
        apply(repo, capsys)
    monkeypatch.undo()
    assert (repo / "workspace.toml").read_bytes() == workspace_before
    assert list((repo / CAPTURED).iterdir()) == [repo / calls[0]]
    assert not (repo / ".workspace-repair.lock").exists()
    rerun = plan(repo, capsys)
    assert {op["record_path"]: op["record_text"] for op in captured_ops(rerun)} == {
        op["record_path"]: op["record_text"] for op in captured_ops(data)
    }
    code, result = apply(repo, capsys)
    assert code == 0 and result["captured_equal"] is True
    for op in captured_ops(data):
        assert (repo / op["record_path"]).read_text() == op["record_text"]


@pytest.mark.parametrize("form", ["membership", "legacy"])
def test_a_record_cut_short_inside_its_write_is_reported_then_finishes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, form: str
) -> None:
    if form == "membership":
        repo = one_defect(tmp_path, summary="A longer summary so a half is a strict prefix")
        record = f"{CAPTURED}/d1.md"
    else:
        repo = make_repo(
            tmp_path, open_=[legacy("cut", summary="A longer summary so a half is short")]
        )
        record = f"{CAPTURED}/cut.md"
    plan(repo, capsys)

    def half(descriptor: int, payload: bytes) -> None:
        os.write(descriptor, payload[: len(payload) // 2])
        raise OSError("disk full")

    monkeypatch.setattr(WS, "_write_all", half)
    code, result = apply(repo, capsys)
    assert code == 0 and refusal_reasons(result) == ["record_write_failed"]
    monkeypatch.undo()
    assert (repo / record).stat().st_size > 0
    data = plan(repo, capsys)
    assert captured_ops(data) == []
    [finding] = captured_findings(data)
    assert finding["reason"] == "record-differs" and finding["record_path"] == record
    (repo / record).unlink()
    plan(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 0 and result["captured_equal"] is True
    assert plan(repo, capsys)["manual_findings"] == []


# ── AC-0030, AC-0031: the item comparison ────────────────────────────────────


@pytest.mark.parametrize("edit", ["field", "edge"])
def test_captured_equal_is_false_after_a_hand_edit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, edit: str
) -> None:
    repo = one_defect(tmp_path, extra="- **Depends on:** spec:peer")
    plan(repo, capsys)
    original = WS._write_record

    def editing(root: Path, record_path: str, payload: bytes) -> str:
        outcome = str(original(root, record_path, payload))
        target = root / record_path
        text = target.read_text()
        if edit == "field":
            text = text.replace("- **Kind:** defect", "- **Kind:** design")
        else:
            text = text.replace("spec:peer", "spec:other")
        target.write_text(text)
        return outcome

    monkeypatch.setattr(WS, "_write_record", editing)
    code, result = apply(repo, capsys)
    assert code == 1
    assert result["captured_equal"] is False
    if edit == "edge":
        assert result["header_edges_before"][0]["reference"] == "spec:peer"
        assert result["header_edges_after"][0]["reference"] == "spec:other"
        assert result["header_edges_after"][0]["waiting_path"] == f"{CAPTURED}/d1.md"


# ── AC-0032: the echo rule ───────────────────────────────────────────────────


def test_valid_hashes_print_in_full_and_record_text_is_one_escaped_string(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(tmp_path, summary="café\nsecond line")
    capsys.readouterr()
    assert WS.main(["repair-plan", "--root", str(repo)]) == 0
    raw = capsys.readouterr().out
    assert len(raw.strip().splitlines()) == 1
    printed = json.loads(raw)
    [op] = captured_ops(printed)
    assert op["source_sha256"] == hashlib.sha256((repo / NOTES / "d1.md").read_bytes()).hexdigest()
    assert len(op["registry_fingerprint"]) == 64
    assert "\\u00e9" in raw and "\\n" in raw and "é" not in raw
    assert op["record_text"].endswith("## Summary\n\ncafé\nsecond line\n")
    assert captured_ops(plan_file(repo))[0]["record_text"] == op["record_text"]


def test_an_oversized_slug_is_echoed_empty_while_the_plan_file_holds_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    slug = "s" * 201
    repo = make_repo(tmp_path, open_=[legacy(slug)])
    printed = plan(repo, capsys)
    [shown] = captured_ops(printed)
    assert shown["slug"] == "" and shown["record_path"] == ""
    [filed] = captured_ops(plan_file(repo))
    assert filed["slug"] == slug and filed["record_path"] == f"{CAPTURED}/{slug}.md"


def test_echo_withholds_each_off_grammar_part_and_keeps_the_valid_ones() -> None:
    op = {
        "operation_type": "captured-to-file",
        "record_path": f"{CAPTURED}/x.md",
        "record_text": "free\x1b text é",
        "entry_locator": {"collection": "backlog.open", "index": 3},
        "source_path": "docs/product/notes/bad\x1b.md",
        "source_sha256": "z" * 64,
        "registry_fingerprint": "b" * 64,
        "depends_on_items": ["spec:peer", "bad item"],
        "receipt_items": [
            "spec:peer completion d-1 completed merge pr:812",
            "spec:peer completion d-1 completed merge pr:81\x1b2",
        ],
    }
    echoed = WS._echo_captured_operation(op)
    assert echoed["source_path"] == "" and echoed["source_sha256"] == ""
    assert echoed["registry_fingerprint"] == "b" * 64
    assert echoed["depends_on_items"] == ["spec:peer", ""]
    assert echoed["receipt_items"] == [
        "spec:peer completion d-1 completed merge pr:812",
        "spec:peer completion d-1 completed merge ",
    ]
    assert echoed["record_text"] == op["record_text"]
    assert echoed["entry_locator"] == {"collection": "backlog.open", "index": 3}
    bad = {**op, "entry_locator": {"collection": "elsewhere", "index": -1}}
    assert WS._echo_captured_operation(bad)["entry_locator"] == {"collection": "", "index": 0}


def test_apply_output_echoes_only_valid_values(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    slug = "s" * 201
    repo = make_repo(tmp_path, open_=[legacy(slug)])
    plan(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 0
    assert result["per_operation"][0]["path"] == ""
    assert result["captured_before"][0]["slug"] == ""
    assert (repo / CAPTURED / f"{slug}.md").is_file()


def test_manual_findings_echo_through_the_grammar(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, open_=[legacy("Bad_Slug")])
    printed = plan(repo, capsys)
    [shown] = captured_findings(printed)
    assert shown["slug"] == "" and shown["reason"] == "slug-invalid"
    [filed] = captured_findings(plan_file(repo))
    assert filed["reason"] == "slug-invalid"


def test_malformed_captured_operations_are_rejected_at_load(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = one_defect(tmp_path)
    data = plan(repo, capsys)
    data = plan_file(repo)
    first_op(data)["record_path"] = "../outside.md"
    recompute(repo, data)
    code, result = apply(repo, capsys)
    assert code == 2 and result["reason"] == "plan_invalid"


# ── AC-0027, AC-0046, AC-0047 at the write itself ────────────────────────────

PAYLOAD = b"# Record\n\n- **Status:** Open\n- **Kind:** defect\n"


def write_record_reason(root: Path) -> str:
    with pytest.raises(WS._CapturedRefusal) as refusal:
        WS._write_record(root, f"{CAPTURED}/r.md", PAYLOAD)
    return str(refusal.value.reason)


def test_write_record_creates_exclusively_without_following_a_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_repo(tmp_path)
    seen: list[tuple[str, int, int]] = []
    real_open = os.open

    def spy(path: Any, flags: int, mode: int = 0o777, **kwargs: Any) -> int:
        seen.append((str(path), flags, mode))
        return real_open(path, flags, mode, **kwargs)

    monkeypatch.setattr(WS.os, "open", spy)
    assert WS._write_record(tmp_path, f"{CAPTURED}/r.md", PAYLOAD) == "created"
    monkeypatch.undo()
    [(path, flags, mode)] = [
        s for s in seen if s[0].endswith("captured/r.md") and s[1] & os.O_CREAT
    ]
    assert flags & os.O_EXCL and flags & os.O_CREAT and flags & os.O_NOFOLLOW
    assert flags & os.O_WRONLY and mode == 0o644
    assert (tmp_path / CAPTURED / "r.md").read_bytes() == PAYLOAD


def test_write_record_refuses_an_entry_the_exclusive_create_finds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_repo(tmp_path)
    (tmp_path / CAPTURED).mkdir(parents=True)
    real_open = os.open

    def racing(path: Any, flags: int, mode: int = 0o777, **kwargs: Any) -> int:
        if str(path).endswith("captured/r.md"):
            # Another writer wins between the check and the create, with the
            # same bytes: the create still refuses rather than keeping it.
            Path(path).write_bytes(PAYLOAD)
        return real_open(path, flags, mode, **kwargs)

    monkeypatch.setattr(WS.os, "open", racing)
    assert write_record_reason(tmp_path) == "record_path_occupied"


def test_write_record_keeps_only_an_identical_confined_file(tmp_path: Path) -> None:
    make_repo(tmp_path)
    target = tmp_path / CAPTURED / "r.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(PAYLOAD)
    assert WS._write_record(tmp_path, f"{CAPTURED}/r.md", PAYLOAD) == "kept"
    target.write_bytes(PAYLOAD + b"more\n")
    assert write_record_reason(tmp_path) == "record_path_occupied"
    assert target.read_bytes() == PAYLOAD + b"more\n"


def test_write_record_refuses_a_directory_and_a_dangling_link(tmp_path: Path) -> None:
    make_repo(tmp_path)
    target = tmp_path / CAPTURED / "r.md"
    target.mkdir(parents=True)
    assert write_record_reason(tmp_path) == "record_path_occupied"
    target.rmdir()
    Path(target).symlink_to(tmp_path / "missing-target")
    assert write_record_reason(tmp_path) == "record_path_occupied"
    assert not (tmp_path / "missing-target").exists()


@pytest.mark.parametrize("linked", ["docs", "docs/product", "docs/product/captured"])
def test_write_record_refuses_a_link_in_any_directory_segment(tmp_path: Path, linked: str) -> None:
    repo = tmp_path / "repo"
    make_repo(repo)
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / "product" / "captured").mkdir(parents=True)
    parent = repo / Path(linked).parent
    parent.mkdir(parents=True, exist_ok=True)
    target = elsewhere if linked == "docs" else elsewhere / "product" / "captured"
    Path(repo / linked).symlink_to(target)
    assert write_record_reason(repo) == "record_directory_unsafe"
    assert not any(elsewhere.rglob("r.md"))
