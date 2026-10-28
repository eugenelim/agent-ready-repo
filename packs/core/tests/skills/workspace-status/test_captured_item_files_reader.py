"""Construction tests for the captured-item file reader and listing.

Spec: docs/specs/captured-item-files/spec.md (AC-0001, AC-0002, AC-0003,
AC-0004, AC-0041, AC-0005, AC-0006, AC-0014, AC-0015). Verification mode: TDD.

Each test plants one case in a ``tmp_path`` repository and asserts the one
outcome it expects.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPTS = (
    Path(__file__).resolve().parents[3] / ".apm/skills/workspace-status/scripts"
)
_MODULE_NAME = "workspace_status_engine_captured_item_files_reader"


def _load_engine() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        _MODULE_NAME, _SCRIPTS / "workspace_status_engine.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(_MODULE_NAME, None)
    return module


ENGINE = _load_engine()
DIR = "docs/product/captured"


def _record(*fields: str, body: str = "") -> str:
    lines = "\n".join(fields)
    return f"# Item\n\n{lines}\n{body}"


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _failing(*fields: str, body: str = "") -> str | None:
    return ENGINE.parse_captured_item(_record(*fields, body=body))[1]


OPEN = "- **Status:** Open"
KIND = "- **Kind:** defect"


# AC-0001 ------------------------------------------------------------------


def test_minimal_record_is_valid() -> None:
    fields, failing = ENGINE.parse_captured_item(_record(OPEN, KIND))
    assert failing is None
    assert fields == {
        "status": "Open", "kind": "defect", "type": None, "resolution": None,
        "parent_intent": None, "detail": None,
    }


def test_full_record_is_valid() -> None:
    fields, failing = ENGINE.parse_captured_item(_record(
        "- **Status:** Closed", "- **Kind:** defect", "- **Type:** shape",
        "- **Resolution:** fixed", "- **Parent intent:** `intent:growth`",
        "- **Detail:** docs/specs/x/notes/n.md", "- **Depends on:** spec:x",
        body="\n## Summary\n\ntext\n",
    ))
    assert failing is None
    assert fields == {
        "status": "Closed", "kind": "defect", "type": "shape",
        "resolution": "fixed", "parent_intent": "intent:growth",
        "detail": "docs/specs/x/notes/n.md",
    }


@pytest.mark.parametrize("name,line", [("Status", OPEN), ("Kind", KIND)])
def test_required_field_missing_or_repeated(name: str, line: str) -> None:
    others = [x for x in (OPEN, KIND) if x != line]
    assert _failing(*others) == name
    assert _failing(OPEN, KIND, line) == name


@pytest.mark.parametrize("name,line,good", [
    ("Type", "- **Type:** shape", "- **Type:** research"),
    ("Parent intent", "- **Parent intent:** intent:a", "- **Parent intent:** intent:b"),
    ("Detail", "- **Detail:** a/b.md", "- **Detail:** c/d.md"),
])
def test_optional_field_repeated(name: str, line: str, good: str) -> None:
    assert _failing(OPEN, KIND, line, good) == name


def test_resolution_repeated() -> None:
    assert _failing(
        "- **Status:** Closed", KIND, "- **Resolution:** fixed", "- **Resolution:** declined"
    ) == "Resolution"


@pytest.mark.parametrize("line,name", [
    ("- **Status:** Draft", "Status"),
    ("- **Status:**", "Status"),
])
def test_status_out_of_set(line: str, name: str) -> None:
    assert _failing(line, KIND) == name


def test_kind_out_of_set() -> None:
    assert _failing(OPEN, "- **Kind:** spec") == "Kind"


def test_type_out_of_set() -> None:
    assert _failing(OPEN, KIND, "- **Type:** signalx") == "Type"


@pytest.mark.parametrize("value", ["shape", "research", "strategy", "design", "signal"])
def test_every_shaping_type_is_valid(value: str) -> None:
    assert _failing(OPEN, KIND, f"- **Type:** {value}") is None


def test_resolution_on_open_defect_is_invalid() -> None:
    assert _failing(OPEN, KIND, "- **Resolution:** fixed") == "Resolution"


def test_resolution_missing_on_closed_defect_is_invalid() -> None:
    assert _failing("- **Status:** Closed", KIND) == "Resolution"


def test_resolution_out_of_set() -> None:
    assert _failing("- **Status:** Closed", KIND, "- **Resolution:** wontfix") == "Resolution"


@pytest.mark.parametrize("kind", ["design", "research", "intent"])
def test_resolution_on_closed_non_defect_is_valid(kind: str) -> None:
    assert _failing(
        "- **Status:** Closed", f"- **Kind:** {kind}", "- **Resolution:** fixed"
    ) is None


@pytest.mark.parametrize("kind", ["design", "research", "intent"])
def test_closed_non_defect_needs_a_resolution(kind: str) -> None:
    assert _failing("- **Status:** Closed", f"- **Kind:** {kind}") == "Resolution"


@pytest.mark.parametrize("kind", ["design", "research", "intent"])
def test_resolution_on_open_non_defect_is_invalid(kind: str) -> None:
    """Regression pin: this case is already invalid for a defect, and for these kinds."""
    assert _failing(
        OPEN, f"- **Kind:** {kind}", "- **Resolution:** fixed"
    ) == "Resolution"


@pytest.mark.parametrize("value", [
    "spec:some-spec", "brief:b", "intent", "intent:Bad", "docs/x.md",
])
def test_parent_intent_must_be_an_intent_typed_reference(value: str) -> None:
    assert _failing(OPEN, KIND, f"- **Parent intent:** {value}") == "Parent intent"


@pytest.mark.parametrize("kind", ["intent", "outcome", "opportunity", "capability"])
def test_parent_intent_kinds(kind: str) -> None:
    assert _failing(OPEN, KIND, f"- **Parent intent:** {kind}:a-b") is None


@pytest.mark.parametrize("value", [
    "docs/../x.md", "../x.md", "docs/specs/a/spec.md", "docs/product/briefs/b.md",
    "docs/product/intents/i.md", "bad name.md", "/abs.md",
])
def test_detail_must_be_a_captured_item_reference(value: str) -> None:
    assert _failing(OPEN, KIND, f"- **Detail:** {value}") == "Detail"


def test_first_failing_field_follows_the_listed_order() -> None:
    assert _failing(
        "- **Status:** Draft", "- **Kind:** spec", "- **Detail:** ../x"
    ) == "Status"
    assert _failing(OPEN, "- **Kind:** spec", "- **Type:** nope") == "Kind"
    assert _failing(OPEN, KIND, "- **Type:** nope", "- **Detail:** ../x") == "Type"


def test_field_value_hides_a_trailing_comment_and_one_pair_of_backticks() -> None:
    fields, failing = ENGINE.parse_captured_item(_record(
        "- **Status:** `Open` <!-- note -->", "- **Kind:** `defect`",
    ))
    assert failing is None and fields is not None and fields["status"] == "Open"
    assert _failing("- **Status:** ``Open``", KIND) == "Status"


def test_comment_hidden_field_does_not_count() -> None:
    text = _record(OPEN, KIND, "<!--", "- **Type:** bogus", "-->")
    assert ENGINE.parse_captured_item(text)[1] is None
    assert _failing(OPEN, KIND, "<!-- - **Kind:** design -->") is None


def test_fence_hidden_field_does_not_count() -> None:
    assert _failing(OPEN, KIND, "```", "- **Status:** Closed", "```") is None
    assert _failing(KIND, "```", "- **Status:** Open", "```") == "Status"


def test_field_under_a_heading_does_not_count() -> None:
    body = "\n## Summary\n\n- **Type:** strategy\n- **Status:** Closed\n"
    fields, failing = ENGINE.parse_captured_item(_record(OPEN, KIND, body=body))
    assert failing is None and fields is not None
    assert fields["type"] is None and fields["status"] == "Open"


# Listing -------------------------------------------------------------------


def _list(root: Path, cooled: frozenset[Path] = frozenset()):
    return ENGINE.list_captured_items(root, cooled)


def test_absent_directory_lists_nothing(tmp_path: Path) -> None:
    listing = _list(tmp_path)
    assert listing.items == [] and listing.findings == ()
    _write(tmp_path, "docs/product/other.md", "x")
    listing = _list(tmp_path)
    assert listing.items == [] and listing.findings == ()


def test_valid_entry_has_the_full_shape(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/one.md", _record(
        OPEN, "- **Kind:** intent", "- **Type:** strategy",
        "- **Parent intent:** outcome:growth", "- **Detail:** a/b.md",
    ))
    _write(tmp_path, f"{DIR}/plain.md", _record(OPEN, KIND))
    listing = _list(tmp_path)
    assert listing.findings == ()
    assert listing.items == [
        {
            "path": f"{DIR}/one.md", "slug": "one", "status": "Open",
            "kind": "intent", "type": "strategy", "routes_to": "frame-situation",
            "resolution": None, "parent_intent": "outcome:growth", "detail": "a/b.md",
        },
        {
            "path": f"{DIR}/plain.md", "slug": "plain", "status": "Open",
            "kind": "defect", "type": None, "routes_to": None,
            "resolution": None, "parent_intent": None, "detail": None,
        },
    ]


def test_routes_to_follows_each_shaping_type(tmp_path: Path) -> None:
    expected = {
        "shape": "intent", "research": "desk-research-project-start",
        "strategy": "frame-situation", "design": "experience-status",
        "signal": "(signal — no action)",
    }
    for shaping in expected:
        _write(tmp_path, f"{DIR}/{shaping}.md", _record(OPEN, KIND, f"- **Type:** {shaping}"))
    routes = {i["slug"]: i["routes_to"] for i in _list(tmp_path).items}
    assert routes == expected


def test_items_are_sorted_by_path(tmp_path: Path) -> None:
    for name in ("zeta", "alpha", "mid-1"):
        _write(tmp_path, f"{DIR}/{name}.md", _record(OPEN, KIND))
    assert [i["slug"] for i in _list(tmp_path).items] == ["alpha", "mid-1", "zeta"]


def test_other_names_are_ignored(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/ok.md", _record(OPEN, KIND))
    for name in ("README.md", "Bad_Name.md", "-lead.md", "note.txt", "a.b.md", "x.MD"):
        _write(tmp_path, f"{DIR}/{name}", "not a record")
    listing = _list(tmp_path)
    assert [i["slug"] for i in listing.items] == ["ok"]
    assert listing.findings == ()


def test_invalid_entry_is_marked_invalid(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/bad.md", _record(OPEN, "- **Kind:** nope"))
    listing = _list(tmp_path)
    assert listing.items == [{"path": f"{DIR}/bad.md", "slug": "bad", "invalid": True}]
    [finding] = listing.findings
    assert (finding.code, finding.path, finding.detail) == (
        "invalid_captured_item", f"{DIR}/bad.md", "Kind",
    )
    assert "named field" in finding.next_action


def test_cooled_unreadable_entry_is_listed_cooled_with_no_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, f"{DIR}/cool.md", _record(OPEN, KIND))
    cooled = frozenset({(tmp_path / DIR / "cool.md").resolve()})
    opened: list[object] = []
    real_open = os.open
    monkeypatch.setattr(os, "open", lambda *a, **k: (opened.append(a[0]), real_open(*a, **k))[1])
    listing = _list(tmp_path, cooled)
    assert opened == []
    assert listing.items == [{"path": f"{DIR}/cool.md", "slug": "cool", "cooled": True}]
    assert listing.findings == ()


def test_cooled_entry_with_unreadable_mode_is_still_cooled(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/cool.md", _record(OPEN, KIND))
    target = tmp_path / DIR / "cool.md"
    target.chmod(0)
    try:
        listing = _list(tmp_path, frozenset({target.resolve()}))
    finally:
        target.chmod(0o644)
    assert listing.items == [{"path": f"{DIR}/cool.md", "slug": "cool", "cooled": True}]


def test_symlinked_entry_is_unreadable(tmp_path: Path) -> None:
    _write(tmp_path, "outside/real.md", _record(OPEN, KIND))
    (tmp_path / DIR).mkdir(parents=True)
    Path(tmp_path / DIR / "link.md").symlink_to(tmp_path / "outside/real.md")
    listing = _list(tmp_path)
    assert listing.items == [{"path": f"{DIR}/link.md", "slug": "link", "unreadable": True}]
    [finding] = listing.findings
    assert (finding.code, finding.path) == ("unreadable_artifact", f"{DIR}/link.md")


def test_hard_linked_entry_is_unreadable(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/one.md", _record(OPEN, KIND))
    os.link(tmp_path / DIR / "one.md", tmp_path / DIR / "two.md")
    listing = _list(tmp_path)
    assert all(i.get("unreadable") is True for i in listing.items)
    assert {f.path for f in listing.findings} == {f"{DIR}/one.md", f"{DIR}/two.md"}


def test_directory_named_like_a_record_is_unreadable(tmp_path: Path) -> None:
    (tmp_path / DIR / "dir.md").mkdir(parents=True)
    listing = _list(tmp_path)
    assert listing.items == [{"path": f"{DIR}/dir.md", "slug": "dir", "unreadable": True}]
    assert [f.code for f in listing.findings] == ["unreadable_artifact"]


def test_non_utf8_entry_is_unreadable(tmp_path: Path) -> None:
    (tmp_path / DIR).mkdir(parents=True)
    (tmp_path / DIR / "raw.md").write_bytes(b"\xff\xfe- **Status:** Open")
    assert _list(tmp_path).items == [
        {"path": f"{DIR}/raw.md", "slug": "raw", "unreadable": True}
    ]


def test_entry_swapped_for_a_link_between_check_and_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, f"{DIR}/swap.md", _record(OPEN, KIND))
    _write(tmp_path, "outside/real.md", _record(OPEN, KIND))
    real_confine = ENGINE.confine_migration_path

    def swapping(root: Path, rel: str, **kwargs: object):
        resolved = real_confine(root, rel, **kwargs)
        if rel == f"{DIR}/swap.md" and kwargs.get("require_file"):
            (root / rel).unlink()
            Path(root / rel).symlink_to(root / "outside/real.md")
        return resolved

    monkeypatch.setattr(ENGINE, "confine_migration_path", swapping)
    assert _list(tmp_path).items == [
        {"path": f"{DIR}/swap.md", "slug": "swap", "unreadable": True}
    ]


def test_symlinked_captured_directory(tmp_path: Path) -> None:
    _write(tmp_path, "elsewhere/a.md", _record(OPEN, KIND))
    (tmp_path / "docs/product").mkdir(parents=True)
    Path(tmp_path / DIR).symlink_to(tmp_path / "elsewhere")
    listing = _list(tmp_path)
    assert listing.items == []
    [finding] = listing.findings
    assert (finding.code, finding.path) == ("unreadable_artifact", DIR)


def test_symlinked_product_directory(tmp_path: Path) -> None:
    _write(tmp_path, "elsewhere/captured/a.md", _record(OPEN, KIND))
    (tmp_path / "docs").mkdir()
    Path(tmp_path / "docs/product").symlink_to(tmp_path / "elsewhere")
    listing = _list(tmp_path)
    assert listing.items == []
    assert [(f.code, f.path) for f in listing.findings] == [("unreadable_artifact", DIR)]


def test_captured_path_that_is_a_file_is_unreadable(tmp_path: Path) -> None:
    _write(tmp_path, DIR, "a file")
    listing = _list(tmp_path)
    assert listing.items == []
    assert [(f.code, f.path) for f in listing.findings] == [("unreadable_artifact", DIR)]


def test_unlistable_directory(tmp_path: Path) -> None:
    (tmp_path / DIR).mkdir(parents=True)
    (tmp_path / DIR).chmod(0)
    try:
        if os.access(tmp_path / DIR, os.R_OK):
            pytest.skip("directory permissions are not enforced")
        listing = _list(tmp_path)
    finally:
        (tmp_path / DIR).chmod(0o755)
    assert listing.items == []
    assert [(f.code, f.path) for f in listing.findings] == [("unreadable_artifact", DIR)]


def test_finding_echo_withholds_an_overlong_path(tmp_path: Path) -> None:
    name = "a" * 210
    _write(tmp_path, f"{DIR}/{name}.md", _record(OPEN, "- **Kind:** nope"))
    [finding] = _list(tmp_path).findings
    assert finding.path == ""


# Status output (AC-0002, AC-0006) --------------------------------------------


def _status(root: Path, mode: str = "status") -> dict:
    done = subprocess.run(
        [sys.executable, "-I", str(_SCRIPTS / "workspace_status.py"), mode, "--root", str(root)],
        capture_output=True, text=True, check=False,
    )
    return json.loads(done.stdout)


def _workspace(root: Path, *entries: str) -> None:
    body = ", ".join(entries)
    (root / "workspace.toml").write_text(
        '["ini-001"]\nname = "n"\nstatus = "active"\nmilestone = "m"\n\n'
        '["ini-001".work]\nqueue = []\nactive = []\nshipped = []\n\n'
        '["ini-001".shaping_queue]\nactive = []\nbacklog = []\n\n'
        '["ini-001".brief_queue]\ndraft = []\nready = []\nexecuting = []\n'
        'shipped = []\nwithdrawn = []\ncancelled = []\n\n'
        f"[backlog]\nopen = [{body}]\nclosed = []\n",
        encoding="utf-8",
    )


def test_status_and_reconcile_emit_the_captured_object(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/one.md", _record(OPEN, KIND))
    _write(tmp_path, f"{DIR}/bad.md", _record(OPEN))
    _workspace(tmp_path)
    for mode in ("status", "reconcile"):
        captured = _status(tmp_path, mode)["captured"]
        assert [i["slug"] for i in captured["items"]] == ["bad", "one"]
        assert captured["items"][0] == {"path": f"{DIR}/bad.md", "slug": "bad", "invalid": True}
        [finding] = captured["findings"]
        assert finding["code"] == "invalid_captured_item"
        assert finding["path"] == f"{DIR}/bad.md"
        assert finding["field"] == "Kind"


def test_captured_object_is_the_same_under_two_registries(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/one.md", _record(OPEN, KIND))
    _write(tmp_path, f"{DIR}/odd.md", _record(OPEN, "- **Kind:** nope"))
    _workspace(tmp_path)
    first = _status(tmp_path)["captured"]
    entry = (
        f'{{path = "{DIR}/one.md", kind = "defect", source = {{mode = "repo-origin"}}, '
        'summary = "s", needs = []}'
    )
    _workspace(tmp_path, entry, '{path = "docs/missing.md", kind = "defect"}')
    assert _status(tmp_path)["captured"] == first


def test_captured_object_survives_a_failed_reconciliation(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/one.md", _record(OPEN, KIND))
    _workspace(tmp_path)
    expected = _status(tmp_path)["captured"]
    (tmp_path / "workspace.toml").write_text("not = [valid\n", encoding="utf-8")
    broken = _status(tmp_path)
    assert broken["canonical"]["findings"][0]["code"] == "invalid_workspace"
    assert broken["captured"] == expected


def test_captured_object_is_empty_for_an_absent_directory(tmp_path: Path) -> None:
    _workspace(tmp_path)
    assert _status(tmp_path)["captured"] == {"items": [], "findings": []}


# AC-0014, AC-0015: the shaping-item guard ----------------------------------

_NO_COOLED: frozenset[Path] = frozenset()


def _guard(root: Path, slug: str, cooled: frozenset[Path] = _NO_COOLED):
    return ENGINE.check_shaping_guard(root, slug, cooled)


@pytest.mark.parametrize(
    ("shaping_type", "skill"),
    [
        ("shape", "intent"),
        ("research", "desk-research-project-start"),
        ("strategy", "frame-situation"),
        ("design", "experience-status"),
        ("signal", "(signal — no action)"),
    ],
)
def test_guard_routes_each_shaping_type(
    tmp_path: Path, shaping_type: str, skill: str
) -> None:
    _write(tmp_path, f"{DIR}/item.md", _record(OPEN, KIND, f"- **Type:** {shaping_type}"))
    assert _guard(tmp_path, "item") == skill


def test_guard_ignores_a_record_with_no_type(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/item.md", _record(OPEN, KIND))
    assert _guard(tmp_path, "item") is None


def test_guard_refuses_an_invalid_record_with_its_finding(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/item.md", _record(OPEN, KIND, "- **Type:** bogus"))
    refusal = _guard(tmp_path, "item")
    assert isinstance(refusal, ENGINE.ShapingGuardRefusal)
    finding = refusal.finding
    assert (finding.code, finding.path) == ("invalid_captured_item", f"{DIR}/item.md")
    assert finding == ENGINE.read_captured_item(tmp_path, "item.md", _NO_COOLED)[1]


def test_guard_refuses_an_unreadable_record_with_its_finding(tmp_path: Path) -> None:
    target = tmp_path / "elsewhere.md"
    target.write_text(_record(OPEN, KIND, "- **Type:** shape"), encoding="utf-8")
    (tmp_path / DIR).mkdir(parents=True)
    (tmp_path / DIR / "item.md").symlink_to(target)
    refusal = _guard(tmp_path, "item")
    assert isinstance(refusal, ENGINE.ShapingGuardRefusal)
    assert (refusal.finding.code, refusal.finding.path) == (
        "unreadable_artifact", f"{DIR}/item.md",
    )


def test_guard_ignores_a_cooled_record(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/item.md", _record(OPEN, KIND, "- **Type:** shape"))
    cooled = frozenset({(tmp_path / DIR / "item.md").resolve()})
    assert _guard(tmp_path, "item", cooled) is None


def test_guard_ignores_a_missing_file(tmp_path: Path) -> None:
    assert _guard(tmp_path, "item") is None


@pytest.mark.parametrize("slug", ["../x", "Bad_Name", "", "a/b", "-x"])
def test_guard_opens_no_file_for_a_slug_outside_the_grammar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, slug: str
) -> None:
    _write(tmp_path, f"{DIR}/item.md", _record(OPEN, KIND, "- **Type:** shape"))
    opened: list[object] = []
    real_open = os.open
    monkeypatch.setattr(
        os, "open", lambda *a, **k: (opened.append(a[0]), real_open(*a, **k))[1]
    )
    assert _guard(tmp_path, slug) is None
    assert opened == []


def test_guard_does_not_match_a_registry_entry_without_a_record(
    tmp_path: Path,
) -> None:
    (tmp_path / "workspace.toml").write_text(
        '[backlog]\nopen = [{slug = "item", type = "shape"}]\n', encoding="utf-8"
    )
    assert _guard(tmp_path, "item") is None
