"""Construction tests for the captured-item file reader and listing.

Spec: docs/specs/captured-item-files/spec.md (AC-0001, AC-0002, AC-0003,
AC-0004, AC-0041, AC-0005, AC-0006, AC-0014, AC-0015). Verification mode: TDD.

Each test plants one case in a ``tmp_path`` repository and asserts the one
outcome it expects.
"""
from __future__ import annotations

import importlib.util
import json
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


# Dispatch `--captured` output (AC-0002, AC-0006) ------------------------------

_DISPATCH = _SCRIPTS.parents[1] / "work-loop/scripts/dispatch.py"


def _status(root: Path) -> dict:
    done = subprocess.run(
        [sys.executable, "-I", str(_DISPATCH), "--captured", "--root", str(root)],
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


def test_dispatch_emits_the_captured_object(tmp_path: Path) -> None:
    _write(tmp_path, f"{DIR}/one.md", _record(OPEN, KIND))
    _write(tmp_path, f"{DIR}/bad.md", _record(OPEN))
    _workspace(tmp_path)
    captured = _status(tmp_path)["captured"]
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
    assert broken["decision"]["findings"][0]["code"] == "invalid_workspace"
    assert broken["captured"] == expected


def test_captured_object_is_empty_for_an_absent_directory(tmp_path: Path) -> None:
    _workspace(tmp_path)
    assert _status(tmp_path)["captured"] == {"items": [], "findings": []}
