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
        (lambda s: s.replace("\n\n", "\n\n\n\n"), False),  # no boundary line: no folding
        (lambda s: s + "\n\n\n", False),
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


_NBSP = " "
_T10_KEEP = (
    "- 2026-11-04: spec approved by example-owner",
    "- 2026-11-04: spec approved by example-owner (scope).",
    "- 2026-11-04: plan approved by example-owner (build strategy)",
    "- 2026-11-04: amendment approved by example-owner (scope and build strategy).",
)


@pytest.mark.parametrize("tail", ["", "  ", _NBSP])
@pytest.mark.parametrize("line", _T10_KEEP)
def test_t10_ac0025_entries_after_last_changelog_keep_digest(line: str, tail: str) -> None:
    assert _d(SPEC + _CL + line + tail + "\n") == _d(SPEC + _CL)


@pytest.mark.parametrize(
    "line",
    [
        "- 2026-11-04: spec approved by " + "a" * 40,
        "- 2026-11-04: spec approved by example_owner",
        "- 2026-11-04: spec reviewed by example-owner",
        "- ٢٠٢٦-11-04: spec approved by example-owner",
        "- ２０２６-11-04: spec approved by example-owner",
        "- 2026-11-04: spec approved by example-owner (scope). extra",
        "- 2026-11-04: spec approved by example-owner and more",
    ],
)
def test_t10_ac0025_non_entries_change_the_digest(line: str) -> None:
    assert _d(SPEC + _CL + line + "\n") != _d(SPEC + _CL)


def test_t10_ac0007_blank_line_folding_and_entry_placement() -> None:
    base = _d(SPEC + _CL)
    first = "- 2026-11-04: spec approved by example-owner\n"
    second = "- 2026-11-05: plan approved by example-owner\n"
    assert _d(SPEC + _CL + "\n" + first) == base  # separating blank line
    assert _d(SPEC + _CL + first + second) == base  # second after an existing one
    assert _d(SPEC + _CL + first + "\n" + second) == base
    after = SPEC + _CL + "x\n"
    assert _d(after + "\n\n\n\ny\n") == _d(after + "\ny\n")  # extra blanks fold after it


def test_t10_ac0008_removing_a_blank_line_between_paragraphs_changes_digest() -> None:
    assert _d(SPEC + "one\n\ntwo\n") != _d(SPEC + "one\ntwo\n")


def test_t11_ac0039_digest_refusal_detail_names_artifact_and_first_offending_line() -> None:
    for name, text in (("spec.md", SPEC + "\nx\u200by\n"), ("plan.md", "# P\r\nline\r\nq\u202eq\n")):
        with pytest.raises(G.GateDigestRefused) as caught:
            G.gate_digest(text, name=name)
        line = 14 if name == "spec.md" else 3
        assert caught.value.detail == f"{name} line {line} holds a hidden or control character"
    with pytest.raises(G.GateDigestRefused) as caught:
        G.gate_digest(b"a\nb\n\xff", name="plan.md")
    assert caught.value.detail == "plan.md line 3 is not valid UTF-8"


def test_t12_ac0039_budget_overrun_detail_names_the_first_selector_line() -> None:
    text = SPEC + "x" * 2000 + "a\ufe0f" * 41
    with pytest.raises(G.GateDigestRefused) as caught:
        G.gate_digest(text, name="spec.md")
    assert caught.value.detail == "spec.md line 13 holds a hidden or control character"


def test_t13_ac0039_budget_overrun_across_lines_names_the_first_selector_line() -> None:
    # SPEC is 12 lines; each filler line holds 2000/4 plain characters, selectors follow.
    filler = ("x" * 500 + "\n") * 4
    body = "".join("a\ufe0f" * 10 + "\n" for _ in range(5))
    with pytest.raises(G.GateDigestRefused) as caught:
        G.gate_digest(SPEC + filler + "plain\n" + body, name="spec.md")
    assert caught.value.detail == "spec.md line 18 holds a hidden or control character"


_ENTRY_LINE = "- 2026-11-04: spec approved by example-owner\n"
_CL_BARE = "\n## Changelog\n\n"
_FENCE = "\n```\n## Changelog\n```\n"


def test_t12_ac0007_ac0025_trailing_space_on_the_real_heading_keeps_the_digest() -> None:
    spaced = SPEC + "\n## Changelog  \n\n"
    assert _d(spaced + _ENTRY_LINE) == _d(spaced)
    assert _d(spaced + _ENTRY_LINE) == _d(SPEC + "\n## Changelog\n\n")


def test_t12_ac0025_earlier_exact_heading_in_a_fence_is_not_the_boundary() -> None:
    real = SPEC + _FENCE + "\n## Changelog \n\n"
    inside = SPEC + _FENCE.replace("```\n## Changelog\n", "```\n## Changelog\n" + _ENTRY_LINE, 1)
    assert _d(inside + "\n## Changelog \n\n") != _d(real)  # entry inside the fence counts
    assert _d(real + _ENTRY_LINE) == _d(real)  # entry under the real heading drops


def test_t12_ac0007_blank_runs_after_the_last_heading_keep_the_digest() -> None:
    folded = SPEC + _CL + "note\n\nmore\n"
    assert _d(SPEC + _CL + "note\n\n\n\nmore\n") == _d(folded)


def test_t12_ac0008_blank_count_before_the_heading_changes_the_digest() -> None:
    stub = SPEC + "\n```\na\n\nb\n```\n"
    assert _d(stub + _CL) != _d(stub.replace("a\n\nb", "a\n\n\nb") + _CL)
    assert _d(SPEC + _CL) != _d(SPEC.replace("\n\n## Notes", "\n\n\n## Notes") + _CL)


def test_t12_ac0007_ac0008_trailing_blanks_after_the_heading_equal_no_final_newline() -> None:
    assert _d(SPEC + "\n## Changelog") == _d(SPEC + "\n## Changelog\n\n\n")
    assert _d(SPEC + _CL + "x") == _d(SPEC + _CL + "x\n\n\n")
    assert _d(SPEC + _CL + "x\n\n\n") == _d(SPEC + _CL + "x\n")


def test_t12_ac0025_entry_between_two_headings_changes_the_digest() -> None:
    without = SPEC + _CL_BARE + "\n## Changelog\n\n"
    between = SPEC + _CL_BARE + _ENTRY_LINE + "\n## Changelog\n\n"
    assert _d(between) != _d(without)
    assert _d(without + _ENTRY_LINE) == _d(without)  # after the last one it drops


@pytest.mark.parametrize("handle", ["a" * 39, "Example-Owner", "9example", "Z"])
def test_t12_ac0025_boundary_handles_keep_the_digest(handle: str) -> None:
    line = f"- 2026-11-04: spec approved by {handle}\n"
    assert _d(SPEC + _CL + line) == _d(SPEC + _CL)


_T13_TASK = "\n### T9: task\n\n"
_T13_STUB = "```\nstub a\n\nstub b\n```\n"
_T13_ENTRY = "- 2026-11-04: spec approved by example-owner\n"


def _t13_plan(stub: str) -> str:
    return SPEC + _T13_TASK + "\n## Changelog\n" + stub


def test_t13_ac0025_ac0008_blank_line_inside_stub_after_changelog_changes_digest() -> None:
    base = _t13_plan(_T13_STUB)
    assert _d(base, "plan.md") != _d(base.replace("stub a\n\n", "stub a\n\n\n"), "plan.md")
    assert _d(base, "plan.md") != _d(base.replace("stub a\n\n", "stub a\n"), "plan.md")


def test_t13_ac0025_ac0008_approval_shaped_line_inside_stub_changes_digest() -> None:
    base = _t13_plan(_T13_STUB)
    edited = base.replace("stub a\n", "stub a\n" + _T13_ENTRY)
    assert _d(base, "plan.md") != _d(edited, "plan.md")


@pytest.mark.parametrize("opener", ["```", "~~~", "   ```", "\t~~~", "          ~~~"])
def test_t13_ac0025_fence_opener_ends_the_region(opener: str) -> None:
    base = SPEC + "\n## Changelog\n" + opener + "\nstub\n"
    edited = base.replace(opener + "\n", opener + "\n" + _T13_ENTRY, 1)
    assert _d(base) != _d(edited)  # the entry sits past the region end, so it counts
    plain = base.replace(opener, "```", 1)
    assert _d(plain) != _d(plain.replace("stub", "stub\n\n\nx"))


def test_t13_ac0025_heading_ends_the_region_and_later_bytes_are_kept() -> None:
    base = SPEC + "\n## Changelog\n\n## Later\n\n\nbody\n"
    assert _d(base) != _d(base.replace("\n\n\nbody", "\n\nbody"))
    assert _d(base) != _d(base.replace("## Later\n", "## Later\n" + _T13_ENTRY))
    assert _d(base) == _d(base.replace("## Changelog\n", "## Changelog\n" + _T13_ENTRY))


def test_t13_ac0007_ac0025_amendment_entry_after_history_keeps_digest() -> None:
    base = SPEC + _CL + "- 2026-11-01: earlier history note\n"
    amendment = "- 2026-11-04: amendment approved by example-owner (scope)\n"
    assert _d(base + amendment) == _d(base)
    assert _d(base + "- 2026-11-04: another history note\n") != _d(base)
