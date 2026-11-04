"""T1 unit tests: gate digest (AC-0007, AC-0008, AC-0025, AC-0039 digest half)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "work-loop" / "scripts" / "_supervisor_gates.py"
)


def _load() -> ModuleType:
    alias = "core_work_loop_supervisor_gates_digest_t1"
    spec = importlib.util.spec_from_file_location(alias, str(_SCRIPT))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


G = _load()

SPEC = (
    "# Spec: X\n\n- **Status:** Draft <!-- Draft | Approved -->\n- **Owner:** A\n\n"
    "## Acceptance criteria\n\n- [ ] AC-0001: it works\n\n## Notes\n\nbody\n"
)


def _d(text: str | bytes, name: str = "spec.md") -> str:
    return G.gate_digest(text, name=name)


def _refused(text: str | bytes) -> str:
    with pytest.raises(G.GateDigestRefused) as ei:
        _d(text)
    return str(ei.value.code)


def test_t1_status_token_change_same_digest() -> None:
    assert _d(SPEC) == _d(SPEC.replace("Draft <!--", "Approved <!--"))


def test_t1_changelog_lines_do_not_change_digest() -> None:
    base = _d(SPEC)
    one = SPEC + "\n## Changelog\n\n- 2026: added\n"
    two = SPEC + "\n## Changelog\n\n- 2026: added\n- 2027: more\n<!-- c -->\n"
    assert _d(one) == base == _d(two)


def test_t1_crlf_and_trailing_whitespace_same_digest() -> None:
    assert _d(SPEC.replace("\n", "\r\n")) == _d(SPEC)
    assert _d(SPEC.replace("works\n", "works   \n")) == _d(SPEC)
    assert _d(SPEC.encode()) == _d(SPEC)


def test_t1_body_change_differs() -> None:
    assert _d(SPEC) != _d(SPEC.replace("it works", "it work"))


def test_t1_plan_name_hashes_whole_text() -> None:
    base = SPEC + "\n- [ ] T1 outside the AC section\n"
    checked = base.replace("T1", "T1x").replace("[ ] T1x", "[x] T1x")
    plain = base.replace("T1", "T1x")
    assert _d(plain, "plan.md") == _d(checked, "plan.md")
    assert _d(plain, "spec.md") != _d(checked, "spec.md")  # name selects the canonicaliser mode


def test_t1_changelog_shape_refusals() -> None:
    assert _refused(SPEC + "\n## Changelog\n\n- a\n\n## Changelog\n\n- b\n") == "gate-changelog-shape"
    assert _refused(SPEC + "\n## Changelog\n\n- a\n\n## Later\n") == "gate-changelog-shape"
    assert _refused(SPEC + "\n## Changelog\n\nprose line\n") == "gate-changelog-shape"


def test_t1_changelog_in_fence_is_not_heading() -> None:
    fenced = SPEC + "\n```\n## Changelog\nprose\n```\n"
    assert _d(fenced) != _d(SPEC)  # content kept, no refusal
    tilde = SPEC + "\n~~~\n## Changelog\nprose\n~~~\n"
    assert _d(tilde)


def test_t1_indented_continuation_keeps_digest() -> None:
    cl = SPEC + "\n## Changelog\n\n- a\n  continued\n"
    assert _d(cl) == _d(SPEC)


@pytest.mark.parametrize(
    "bad",
    [
        b"\xff\xfe bad",
        "a\x1b[31mred",
        "a\rb",
        "a\x7fb",
        "a\x85b",
        "a\u202eb",
        "a\u200bb",
        "a\U000e0041b",
        "a\ufe00b",
        "a\u180bb",
        "a\u2028b",
        "a\ufff9b",
    ],
)
def test_t1_unsafe_content_refused(bad: str | bytes) -> None:
    prefix: str | bytes = SPEC.encode() if isinstance(bad, bytes) else SPEC
    assert _refused(prefix + bad) == "gate-unsafe-content"


def test_t1_tab_and_crlf_keep_digest() -> None:
    tabbed = SPEC.replace("body", "a\tb")
    assert _d(tabbed.replace("\n", "\r\n")) == _d(tabbed)
