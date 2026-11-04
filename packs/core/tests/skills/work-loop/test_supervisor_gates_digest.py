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


def test_t8_sec1_a_shorter_fence_line_does_not_close_a_longer_fence() -> None:
    nested = SPEC + "\n````\n```\n## Changelog\nprose\n```\n````\n"
    assert _d(nested) != _d(SPEC)  # the heading stays inside the fence: kept, no refusal
    # a closer needs no info string; a line carrying one keeps the fence open
    info = SPEC + "\n```\n```text\n## Changelog\nprose\n```\n"
    assert _d(info)
    # after the real close, a real Changelog heading counts again
    assert _d(nested + "\n## Changelog\n\n- a\n") == _d(nested)


def test_t8_adv4_an_indented_line_must_continue_a_list_item() -> None:
    assert _refused(SPEC + "\n## Changelog\n\n  indented text\n") == "gate-changelog-shape"
    assert _refused(SPEC + "\n## Changelog\n\n- a\n\nprose\n  more\n") == "gate-changelog-shape"
    assert _d(SPEC + "\n## Changelog\n\n- a\n\n  still the item\n") == _d(SPEC)


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


def test_t9_sec2_1_indented_heading_and_shallow_lines_refuse() -> None:
    # an ATX heading indented 1 to 3 spaces is the last level-two heading
    for pad in (" ", "  ", "   "):
        assert _refused(SPEC + f"\n## Changelog\n\n- a\n\n{pad}## X\n") == "gate-changelog-shape"
    # a setext underline, with or without a lazy-continuation position
    assert _refused(SPEC + "\n## Changelog\n\n- a\n---\n") == "gate-changelog-shape"
    assert _refused(SPEC + "\n## Changelog\n\n- a\n===\n") == "gate-changelog-shape"
    # a line shallower than the item's content width, after a blank line
    assert _refused(SPEC + "\n## Changelog\n\n- a\n\n x\n") == "gate-changelog-shape"
    # lines that would start a block cannot be lazy continuations
    for block in ("# h", "```", "> q", "<div>", "1. n", "* b", "- - -"):
        assert _refused(SPEC + f"\n## Changelog\n\n- a\n{block}\n") == "gate-changelog-shape"
    # a lazy continuation is refused (T10); an in-item indented line keeps the digest
    assert _refused(SPEC + "\n## Changelog\n\n- a\ncontinued\n  more\n") == "gate-changelog-shape"
    assert _d(SPEC + "\n## Changelog\n\n- a\n  continued\n  more\n") == _d(SPEC)


def test_t9_sec2_2_only_a_fence_indented_up_to_three_spaces_counts() -> None:
    indented = SPEC + "\n    ```\n## Changelog\n\n- a\n"
    assert "## Changelog" not in G._strip_changelog(indented)  # the 4-space run opens nothing
    closed = SPEC + "\n```\n    ```\n## Changelog\nprose\n```\n"
    assert _d(closed)  # a 4-space run does not close: the heading stays in the fence
    inline = SPEC + "\n``` a`b\n## Changelog\n\n- a\n"
    assert "## Changelog" not in G._strip_changelog(inline)  # not a fence: it is stripped


def test_t9_sec2_3_padded_artifact_with_interleaved_selectors_refuses() -> None:
    padded = SPEC + "x" * 20000 + "".join("a\ufe0f" for _ in range(100))
    assert _refused(padded) == "gate-unsafe-content"
    assert _d(SPEC + "x" * 20000 + "heart \u2764\ufe0f here")


_CL = "\n## Changelog\n\n"


def test_t10_adv3_1_lazy_line_refuses() -> None:
    assert _refused(SPEC + _CL + "- a\nlazy\n") == "gate-changelog-shape"
    assert _refused(SPEC + _CL + "- a\n\nlazy\n") == "gate-changelog-shape"
    assert _refused(SPEC + _CL + "- a\n x\n") == "gate-changelog-shape"
    approval = "- 2026-11-04: spec approved by eugenelim (scope).\n"
    assert _d(SPEC + _CL + approval + "  wrapped here.\n") == _d(SPEC)


def test_t10_adv3_3_content_width_is_marker_plus_spaces() -> None:
    assert _refused(SPEC + _CL + "-   foo\n\n  bar\n") == "gate-changelog-shape"
    assert _d(SPEC + _CL + "-   foo\n\n    bar\n") == _d(SPEC)
    assert _d(SPEC + _CL + "-   foo\n    bar\n- b\n  c\n") == _d(SPEC)
    assert _refused(SPEC + _CL + "- foo\n  - nested\n") == "gate-changelog-shape"


def test_t10_sec3_1_item_content_starting_a_block_refuses() -> None:
    for bad in ("- # h", "- ```", "- <div>", "- ", "- > q", "- - x", "- ---"):
        assert _refused(SPEC + _CL + bad + "\n") == "gate-changelog-shape", bad
    assert _refused(SPEC + _CL + "- a <!-- x\n\ny -->\n") == "gate-changelog-shape"
    assert _refused(SPEC + _CL + "<!-- x\n\ny -->\n- a\n") == "gate-changelog-shape"
    assert _d(SPEC + _CL + "- a <!-- x\ny -->\n<!-- c -->\n") == _d(SPEC)


def test_t10_adv3_2_fence_or_html_in_list_item_before_changelog_refuses() -> None:
    opened_at_2 = "- a\n  ```\ncode\n    ```\n"
    assert _refused(SPEC + "\n" + opened_at_2 + _CL + "- x\n") == "gate-changelog-shape"
    assert _refused(SPEC + "\n- a\n  ~~~\n" + _CL + "- x\n") == "gate-changelog-shape"
    assert _refused(SPEC + "\n- <div>\n" + _CL + "- x\n") == "gate-changelog-shape"
    assert _refused(SPEC + "\n1. a\n   <pre>\n" + _CL + "- x\n") == "gate-changelog-shape"
    # a fence in a list item that opens and closes at the scan's own reading is kept
    closed = "- a\n  ```\ncode\n  ```\n"
    assert _d(SPEC + "\n" + closed + _CL + "- x\n") == _d(SPEC + "\n" + closed)
    # without a Changelog section nothing is stripped, so the text is kept
    assert _d(SPEC + "\n" + opened_at_2)
    # a fence outside any list item still hides the heading
    assert _d(SPEC + "\n```\n## Changelog\n- x\n```\n") != _d(SPEC)


def test_t10_adv3_4_invisible_budget_basis_is_2000() -> None:
    assert G._INVISIBLE_CAP == 2000
    forty = "".join("a\ufe0f" for _ in range(40))
    for pad in (2000, 20000):  # a padded artifact cannot buy more than the cap
        assert _d(SPEC + "x" * pad + forty)
        assert _refused(SPEC + "x" * pad + forty + "a\ufe0f") == "gate-unsafe-content"


def test_t10_adv3_5_fence_comment_does_not_claim_canonicaliser_parity() -> None:
    source = _SCRIPT.read_text(encoding="utf-8")
    assert "same CommonMark rule" not in source
    assert "`_loop_guards.canonical_contract`: an opener" not in source
