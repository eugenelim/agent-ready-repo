"""T12: the independent reviewer can see the page.

This is the gap the intent named and the original spec scoped out — "The
reviewer cannot cover it. `frontend-reviewer` reads the diff. Nothing in a diff
shows one element covering another." Everything else this delivery shipped made
the *authoring* agent look at its own work. Until the reviewer is seeded with
the captures, the independent check is still blind, and the step is self-review.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from frontend_engineering_rendered_page_rules import PACK_ROOT, severity_by_class, read_rules

REVIEWER = PACK_ROOT / ".apm" / "agents" / "frontend-reviewer.md"
# The work-loop dispatch line lives in the core pack's source, not in the
# `.claude/` projection, which is regenerated from it.
WORK_LOOP = PACK_ROOT.parent / "core" / ".apm" / "skills" / "work-loop" / "SKILL.md"


@pytest.fixture(scope="module")
def reviewer() -> str:
    return REVIEWER.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def work_loop() -> str:
    return WORK_LOOP.read_text(encoding="utf-8")


def _frontmatter(text: str) -> str:
    return text.split("---", 2)[1]


def _normalized(text: str) -> str:
    return " ".join(text.split())


def test_the_reviewer_is_seeded_with_the_capture_set(reviewer: str) -> None:
    """Verifies: `frontend-reviewer` is seeded with the capture set and the
    recorded observations for the surface under review."""
    seed = reviewer.split("## Reviewer independence", 1)[1].split("\n## ", 1)[0]
    seed = _normalized(seed)
    assert "inspection observations" in seed, (
        "the seed contract does not name the observations field"
    )
    assert "capture set" in seed, "the seed contract does not name the capture set"
    assert "open them" in seed or "Look at the captures" in seed, (
        "the reviewer is handed captures but never told to open them"
    )


def test_the_reviewer_carries_a_reader_visible_layout_lens(reviewer: str) -> None:
    """Verifies: the reviewer carries a lens for reader-visible layout failure
    whose severity comes from the pack's finding-class mapping."""
    assert "### Lens 6 — Reader-visible layout failure" in reviewer
    assert "## What you review — the six lenses" in reviewer, (
        "the lens count in the heading was not updated with the new lens"
    )
    lens = reviewer.split("### Lens 6", 1)[1].split("\n## ", 1)[0]
    normalized = _normalized(lens)
    assert "rendered-page-inspection.md" in normalized, (
        "Lens 6 does not point at the shipped finding-class table"
    )
    assert "most severe" in normalized, (
        "Lens 6 does not carry the multi-class precedence rule, so the reviewer "
        "and the step could assign different severities to one failure"
    )


def test_the_lens_names_failures_the_class_table_actually_declares(
    reviewer: str,
) -> None:
    """The lens must describe the same failures the pack classifies, or the
    reviewer's findings cannot be mapped onto the step's severities."""
    lens = _normalized(reviewer.split("### Lens 6", 1)[1].split("\n## ", 1)[0]).lower()
    described = severity_by_class(read_rules())
    # Each of these classes' plain-language failure should be recognisable in
    # the lens. Checked by the distinguishing phrase, not the class slug, since
    # the lens is written for a human reviewer.
    for phrase in ("covering another", "cut off at the top", "outside the container",
                   "too small to hit", "cannot be read"):
        assert phrase in lens, f"Lens 6 does not describe {phrase!r}"
    assert "occlusion" in described and "clipped-at-rest-top" in described


def test_the_lens_requires_the_scroll_position(reviewer: str) -> None:
    """`clipped-at-rest-top` is the one class that cannot be judged from the
    image alone. A reviewer that ignores the recorded state will misclassify it
    exactly as a judge would."""
    lens = _normalized(reviewer.split("### Lens 6", 1)[1].split("\n## ", 1)[0])
    assert "scroll position" in lens.lower()
    assert "at-rest" in lens


def test_the_reviewer_can_capture_a_page_itself(reviewer: str) -> None:
    """Verifies: `frontend-reviewer` can capture a rendered page itself rather
    than relying only on captures the author supplied.

    Without this the reviewer inherits whatever blind spot the author's capture
    step had — it can only see the states the author chose to show it.
    """
    tools = re.search(r"^tools:\s*(.+)$", _frontmatter(reviewer), re.MULTILINE)
    assert tools, "the reviewer declares no tools"
    declared = {t.strip() for t in tools.group(1).split(",")}
    assert "Bash" in declared, f"the reviewer cannot drive a browser; tools are {declared}"
    assert {"Read", "Grep", "Glob"} <= declared, "the reviewer lost a reading tool"


def test_the_reviewer_states_it_does_not_write_to_the_repository(
    reviewer: str,
) -> None:
    """Verifies: shipped reviewer content states the reviewer does not write to
    the repository under review.

    This is the mitigation for giving a reviewer Bash. It is a stated
    constraint, not an enforced one, and the ledger records that.
    """
    normalized = _normalized(reviewer)
    assert "do not write to the repository under review" in normalized.lower()
    for forbidden in ("edit", "stage", "commit", "install"):
        assert forbidden in normalized.lower(), (
            f"the no-write constraint does not name {forbidden!r} among what is "
            f"out of bounds"
        )


def test_the_work_loop_passes_the_captures_to_the_reviewer(work_loop: str) -> None:
    """Verifies: the work-loop's dispatch line passes the capture set, not only
    the diff and the manifest state.

    Without this the seed contract is aspirational — the reviewer would document
    an input nobody hands it.
    """
    line = next(
        (ln for ln in work_loop.splitlines()
         if ln.startswith("- **`frontend-reviewer`**")),
        None,
    )
    assert line is not None, "the frontend-reviewer dispatch line is gone"
    assert "capture set" in line, (
        "the dispatch line does not pass the capture set, so the reviewer's seed "
        "contract cannot be satisfied"
    )
    assert "observations" in line
    assert "reader-visible layout failure" in line, (
        "the dispatch line's lens summary omits the new lens"
    )


def test_the_dispatch_line_is_edited_at_its_source_not_its_projection() -> None:
    """`.apm/` is the source of truth. If the projection has drifted from the
    source, self-host has not been run and the installed adapters carry the old
    dispatch line."""
    projection = PACK_ROOT.parent.parent / ".claude" / "skills" / "work-loop" / "SKILL.md"
    if not projection.exists():
        pytest.skip("work-loop is not projected into this repository")
    assert projection.read_text(encoding="utf-8") == WORK_LOOP.read_text(encoding="utf-8"), (
        "the work-loop projection differs from its .apm/ source — run "
        "`catalogue self-host --write`"
    )
