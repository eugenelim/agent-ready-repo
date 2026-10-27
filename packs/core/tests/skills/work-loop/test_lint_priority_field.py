"""Construction tests for the Priority header field reader and lint.

Drives the production CLI through ``main(argv)`` in-process over ``tmp_path``
trees.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "work-loop" / "scripts" / "lint-priority-field.py"
)


def _load() -> ModuleType:
    name = "core_work_loop_lint_priority_field"
    spec = importlib.util.spec_from_file_location(name, _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev
    return mod


lint = _load()

INTENT = "docs/product/intents/a.md"
BRIEF = "docs/product/briefs/b.md"
CAPTURED = "docs/product/captured/c.md"
SPEC = "docs/specs/foo/spec.md"
CARRIERS = (INTENT, BRIEF, CAPTURED, SPEC)


def _doc(*lines: str) -> str:
    return "# Title\n\n" + "\n".join(lines) + "\n\n## Body\n\ntext\n"


def _write(root: Path, rel: str, text: str | bytes) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text, encoding="utf-8")
    return path


def _run(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = lint.main(["--root", str(root)])
    out = capsys.readouterr()
    return code, out.out, out.err


# --- AC-0001 / AC-0003: the reader -----------------------------------------


@pytest.mark.parametrize("value", lint.PRIORITY_VALUES)
def test_read_priority_returns_each_value(value: str) -> None:
    assert lint.read_priority(_doc(f"- **Priority:** {value}")) == value


def test_value_set_and_order() -> None:
    assert lint.PRIORITY_VALUES == ("urgent", "high", "medium", "low")


@pytest.mark.parametrize("rel", CARRIERS)
@pytest.mark.parametrize("value", lint.PRIORITY_VALUES)
def test_each_value_valid_on_each_carrier(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], rel: str, value: str
) -> None:
    _write(tmp_path, rel, _doc(f"- **Priority:** {value}"))
    assert _run(tmp_path, capsys) == (0, "", "")


@pytest.mark.parametrize(
    "text",
    [
        _doc("- **Status:** Draft"),
        _doc("- **Priority:**"),
        _doc("- **Priority:** <!-- none yet -->"),
        _doc("- **Priority:** ``"),
    ],
)
def test_absent_or_empty_is_none(text: str) -> None:
    assert lint.read_priority(text) is None


def test_line_after_heading_is_ignored() -> None:
    text = "# T\n\n## Body\n\n- **Priority:** bogus\n"
    assert lint.read_priority(text) is None


@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_line_inside_preamble_fence_is_ignored(fence: str) -> None:
    text = f"# T\n\n{fence}\n- **Priority:** bogus\n## not a heading\n{fence}\n- **Priority:** low\n"
    assert lint.read_priority(text) == "low"


def test_commented_line_is_hidden() -> None:
    text = "# T\n\n<!--\n- **Priority:** bogus\n-->\n- **Priority:** high\n"
    assert lint.read_priority(text) == "high"


def test_backticks_and_trailing_comment_stripped() -> None:
    assert lint.read_priority(_doc("- **Priority:** `urgent` <!-- note -->")) == "urgent"
    assert lint.read_priority(_doc("- **Priority:** low <!-- note -->")) == "low"


@pytest.mark.parametrize("value", ["High", "p1", "none", "urgent high", "``urgent``"])
def test_invalid_values_raise(value: str) -> None:
    with pytest.raises(lint.PriorityError) as info:
        lint.read_priority(_doc(f"- **Priority:** {value}"))
    assert info.value.code == "invalid_priority"


@pytest.mark.parametrize(
    "lines",
    [
        ("- **Priority:** low", "- **Priority:** high"),
        ("- **Priority:** low", "- **Priority:** low"),
        ("- **Priority:** low", "- **Priority:** bogus"),
        ("- **Priority:** bogus", "- **Priority:**"),
    ],
)
def test_duplicate_raises(lines: tuple[str, ...]) -> None:
    with pytest.raises(lint.PriorityError) as info:
        lint.read_priority(_doc(*lines))
    assert info.value.code == "duplicate_priority"


def test_cli_calls_reader_once_per_carrier(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    for rel in CARRIERS:
        _write(tmp_path, rel, _doc("- **Priority:** low"))
    calls: list[str] = []
    real: Callable[[str], str | None] = lint.read_priority

    def spy(text: str) -> str | None:
        calls.append(text)
        return real(text)

    monkeypatch.setattr(lint, "read_priority", spy)
    assert _run(tmp_path, capsys)[0] == 0
    assert len(calls) == len(CARRIERS)


# --- AC-0001: names that are not read --------------------------------------


@pytest.mark.parametrize(
    "rel",
    [
        "docs/product/intents/_draft.md",
        "docs/product/briefs/_draft.md",
        "docs/product/captured/Draft.md",
        "docs/product/captured/_c.md",
        "docs/product/captured/sub/ok.md",
        "docs/product/intents/sub/ok.md",
        "docs/specs/foo_bar/spec.md",
        "docs/specs/foo/notes.md",
        "docs/specs/foo/notes/spec.md",
    ],
)
def test_unadmitted_names_are_ignored(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], rel: str
) -> None:
    _write(tmp_path, rel, _doc("- **Priority:** bogus"))
    assert _run(tmp_path, capsys) == (0, "", "")


# --- AC-0002: violations ---------------------------------------------------


def test_violations_print_sorted_one_line_each(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(tmp_path, SPEC, _doc("- **Priority:** bogus"))
    _write(tmp_path, INTENT, _doc("- **Priority:** low", "- **Priority:** bogus"))
    _write(tmp_path, CAPTURED, _doc("- **Priority:** high"))
    code, out, err = _run(tmp_path, capsys)
    assert code == 1
    assert err == ""
    assert out.splitlines() == [
        f"{INTENT}: duplicate_priority",
        f"{SPEC}: invalid_priority",
    ]
    assert "bogus" not in out


def test_clean_tree_prints_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(tmp_path, INTENT, _doc("- **Status:** Draft"))
    assert _run(tmp_path, capsys) == (0, "", "")


# --- AC-0004: refusals -----------------------------------------------------


def test_symlinked_file_refuses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write(tmp_path, "elsewhere.md", _doc("- **Priority:** low"))
    (tmp_path / "docs/product/intents").mkdir(parents=True)
    (tmp_path / INTENT).symlink_to(target)
    code, out, err = _run(tmp_path, capsys)
    assert (code, out) == (2, "")
    assert err == "unsafe-artifact: docs/product/intents\n"


def test_symlinked_carrier_directory_refuses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "real").mkdir()
    (tmp_path / "docs/product").mkdir(parents=True)
    (tmp_path / "docs/product/captured").symlink_to(tmp_path / "real")
    code, out, err = _run(tmp_path, capsys)
    assert (code, out) == (2, "")
    assert err == "unsafe-artifact: docs/product/captured\n"


def test_link_inside_a_spec_directory_is_never_reached(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(tmp_path, SPEC, _doc("- **Priority:** high"))
    notes = tmp_path / SPEC.rsplit("/", 1)[0] / "notes"
    notes.mkdir()
    (notes / "link.md").symlink_to(tmp_path / SPEC)
    _write(tmp_path, "docs/specs/README.md", "not a spec directory")
    assert _run(tmp_path, capsys) == (0, "", "")


def test_symlinked_spec_file_refuses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write(tmp_path, "elsewhere.md", _doc("- **Priority:** low"))
    (tmp_path / "docs/specs/linked").mkdir(parents=True)
    (tmp_path / "docs/specs/linked/spec.md").symlink_to(target)
    code, out, err = _run(tmp_path, capsys)
    assert (code, out) == (2, "")
    assert err == "unsafe-artifact: docs/specs/linked/spec.md\n"


def test_non_utf8_refuses(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path, SPEC, b"# T\n\n- **Priority:** \xff\n")
    code, out, err = _run(tmp_path, capsys)
    assert (code, out) == (2, "")
    assert err == f"invalid-utf8: {SPEC}\n"


def test_oversized_file_refuses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lint, "MAX_ARTIFACT_BYTES", 10)
    _write(tmp_path, BRIEF, _doc("- **Priority:** low"))
    code, out, err = _run(tmp_path, capsys)
    assert (code, out) == (2, "")
    assert err == f"resource-limit: {BRIEF}\n"


def test_file_count_bound_refuses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lint, "MAX_FILES", 1)
    _write(tmp_path, "docs/product/intents/a.md", _doc("- **Status:** x"))
    _write(tmp_path, "docs/product/intents/b.md", _doc("- **Status:** x"))
    code, out, err = _run(tmp_path, capsys)
    assert (code, out) == (2, "")
    assert err == "resource-limit: docs/product/intents\n"


def test_refusal_after_violation_leaves_stdout_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, INTENT, _doc("- **Priority:** bogus"))
    target = _write(tmp_path, "elsewhere.md", _doc("- **Status:** x"))
    (tmp_path / "docs/product/briefs").mkdir(parents=True)
    (tmp_path / BRIEF).symlink_to(target)
    raised: list[str] = []
    real: Callable[[str], str | None] = lint.read_priority

    def spy(text: str) -> str | None:
        try:
            return real(text)
        except lint.PriorityError as exc:
            raised.append(exc.code)
            raise

    monkeypatch.setattr(lint, "read_priority", spy)
    code, out, err = _run(tmp_path, capsys)
    assert raised == ["invalid_priority"]
    assert (code, out) == (2, "")
    assert err == "unsafe-artifact: docs/product/briefs\n"


def test_absent_carrier_directories_are_not_a_refusal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(tmp_path, capsys) == (0, "", "")
