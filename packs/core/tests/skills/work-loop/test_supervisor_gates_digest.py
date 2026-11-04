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


def test_t8_sec2_variation_selector_runs_are_bounded() -> None:
    assert _refused(SPEC + "x️️️y") == "gate-unsafe-content"
    alternating = "︎️" * 40
    assert _refused(SPEC + "x" + alternating + "y") == "gate-unsafe-content"
    spread = "".join("a️‍" for _ in range(60))  # adjacency fine, volume over budget
    assert _refused(SPEC + spread) == "gate-unsafe-content"
    assert _d(SPEC + "heart ❤️ here")  # one emoji presentation selector stays


def test_t8_qe9_bytes_outside_the_ac_section_and_in_a_plan_change_the_digest() -> None:
    assert _d(SPEC) != _d(SPEC.replace("body", "bodies"))  # after the AC section
    assert _d(SPEC) != _d(SPEC.replace("# Spec: X", "# Spec: Y"))  # before it
    assert _d(SPEC) != _d(SPEC.replace("- **Owner:** A", "- **Owner:** B"))
    plan = "# Plan\n\n- **Status:** Drafting\n\n### T1\n\nBuild it.\n"
    assert _d(plan, "plan.md") != _d(plan.replace("Build it.", "Build it!"), "plan.md")
    assert _d(plan, "plan.md") != _d(plan + "\nmore\n", "plan.md")
    # the one normalised region stays normalised
    assert _d(SPEC) == _d(SPEC.replace("[ ] AC-0001", "[x] AC-0001"))


def test_t9_sec2_3_padded_artifact_with_interleaved_selectors_refuses() -> None:
    padded = SPEC + "x" * 20000 + "".join("a\ufe0f" for _ in range(100))
    assert _refused(padded) == "gate-unsafe-content"
    assert _d(SPEC + "x" * 20000 + "heart \u2764\ufe0f here")


def test_t10_adv3_4_invisible_budget_basis_is_2000() -> None:
    assert G._INVISIBLE_CAP == 2000
    forty = "".join("a\ufe0f" for _ in range(40))
    for pad in (2000, 20000):  # a padded artifact cannot buy more than the cap
        assert _d(SPEC + "x" * pad + forty)
        assert _refused(SPEC + "x" * pad + forty + "a\ufe0f") == "gate-unsafe-content"


_CL = "\n## Changelog\n\n"
_ENTRY = "- 2026-11-04: spec approved by example-owner (scope).\n"
_PLAN = "# Plan\n\n- **Status:** Drafting\n\n### T1\n\n- [ ] step\n\nBuild it.\n"


@pytest.mark.parametrize(
    ("edit", "same"),
    [
        (lambda s: s.replace("Draft <!--", "Approved <!--"), True),
        (lambda s: s + _CL + _ENTRY, False),  # the heading itself is content
        (lambda s: s + _CL, False),
        (lambda s: s + _CL + _ENTRY + _ENTRY.replace("spec", "plan"), None),
        (lambda s: s.replace("\n\n", "\n\n\n\n"), True),
        (lambda s: s + "\n\n\n", True),
        (lambda s: s.replace("[ ] AC-0001", "[x] AC-0001"), True),
        (lambda s: s.replace("it works", "it work"), False),
        (lambda s: s.replace("Owner:** A", "Owner:** B"), False),
        (lambda s: s + _CL + _ENTRY + "  wrapped\n", False),
        (lambda s: _ENTRY + s + _CL + _ENTRY, False),
    ],
)
def test_t1_ac0007_ac0008_spec_edits(edit, same: bool | None) -> None:  # type: ignore[no-untyped-def]
    if same is None:  # entries drop: equal to the same text with the heading only
        assert _d(edit(SPEC)) == _d(SPEC + _CL)
        return
    assert (_d(edit(SPEC)) == _d(SPEC)) is same


@pytest.mark.parametrize(
    ("edit", "same"),
    [
        (lambda s: s.replace("Drafting", "Approved"), True),
        (lambda s: s + _CL + _ENTRY.replace("spec", "amendment"), None),
        (lambda s: s.replace("\n", "\r\n"), True),
        (lambda s: s.replace("Build it.", "Build it.   "), True),
        (lambda s: s.replace("[ ] step", "[x] step"), True),
        (lambda s: s.replace("Build it.", "Build it!"), False),
    ],
)
def test_t1_ac0007_ac0008_plan_edits(edit, same: bool | None) -> None:  # type: ignore[no-untyped-def]
    if same is None:
        assert _d(edit(_PLAN), "plan.md") == _d(_PLAN + _CL, "plan.md")
        return
    assert (_d(edit(_PLAN), "plan.md") == _d(_PLAN, "plan.md")) is same


def test_t1_ac0025_approval_entry_after_last_heading_is_dropped() -> None:
    base = _d(SPEC + _CL)
    for line in (
        "- 2026-11-04: spec approved by example-owner\n",
        "- 2026-11-04: plan approved by example-owner.\n",
        "- 2026-11-04: amendment approved by a-1 (build strategy)\n",
        "- 2026-11-04: amendment approved by example-owner (scope and build strategy).   \n",
    ):
        assert _d(SPEC + _CL + line) == base, line


def test_t1_ac0025_other_lines_change_the_digest() -> None:
    base = _d(SPEC + _CL)
    cases = [
        _ENTRY + "  wrapped here.\n",
        _ENTRY.replace("2026-11-04", "26-11-04"),
        _ENTRY.replace("spec approved", "design approved"),
        _ENTRY.replace("(scope)", "(other)"),
        _ENTRY.replace("example-owner", "-bad"),
        _ENTRY.replace("example-owner", "a" * 40),
        "<div>x</div>\n",
        "<!-- c -->\n",
        "```\n```\n",
        "### sub\n",
        "- plain note\n",
    ]
    for body in cases:
        assert _d(SPEC + _CL + body) != base, body


def test_t1_ac0025_entry_before_last_heading_counts_and_last_heading_wins() -> None:
    base = _d(SPEC + _CL)
    assert _d(SPEC + "\n" + _ENTRY) != _d(SPEC)  # no heading: kept
    assert _d(SPEC + _CL + _ENTRY + "\n## Changelog\n\n" + _ENTRY) != base
    first = SPEC + _CL + _ENTRY + "\n## Changelog\n\n"
    assert _d(first + _ENTRY) == _d(first)
    assert _d(SPEC + " ## Changelog\n" + _ENTRY) != base  # not exactly the heading


def test_t1_ac0025_nothing_refuses_changelog_shape() -> None:
    assert "gate-changelog-shape" not in _SCRIPT.read_text(encoding="utf-8")
    for body in ("prose\n", "  indented\n", "- a\ncontinued\n", "## Later\n", "```\n"):
        assert _d(SPEC + _CL + body)
        assert _d(SPEC + "\n## Changelog\n- a\n\n## Changelog\n" + body)
