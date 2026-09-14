"""T12: the independent reviewer can see the page.

This is the gap the intent named and the original spec scoped out — "The
reviewer cannot cover it. `frontend-reviewer` reads the diff. Nothing in a diff
shows one element covering another." Everything else this delivery shipped made
the *authoring* agent look at its own work. Until the reviewer is seeded with
the captures, the independent check is still blind, and the step is self-review.
"""

from __future__ import annotations

import json
import re

import pytest
from frontend_engineering_rendered_page_rules import PACK_ROOT, read_rules, severity_by_class

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


# ── round 4: the lens must not be void on arrival ───────────────────────────

def test_the_confirmation_rule_is_scoped_per_lens(reviewer: str) -> None:
    """Lens 6 reads the page; lenses 1-5 read the diff. A single global rule
    requiring diff-confirmation disqualified every Lens 6 finding before it was
    written — the lens existed and could produce nothing."""
    norm = _normalized(reviewer)
    assert "Lenses 1-5 read the diff" in norm
    assert "Lens 6 reads the page" in norm
    assert "holding it to diff-confirmation would void every finding" in norm, (
        "the contract does not say why Lens 6 is exempt, so the next editor "
        "will re-impose the global rule"
    )


def test_no_stale_five_lens_statement_survives(reviewer: str) -> None:
    """The heading was updated to six and two other statements were not, which
    is how a reader learns the lens list is unreliable."""
    # Only statements counting ALL the lenses. "The other five lenses read the
    # diff" inside Lens 6 is accurate — there are five others — so matching a
    # bare "five lenses" would fail on correct prose.
    for stale in ("across five lenses", "these five lenses", "the five lenses"):
        assert stale not in reviewer, (
            f"{stale!r} survives alongside the six-lens heading"
        )
    assert reviewer.count("six lenses") >= 2


def test_one_authority_governs_an_overlapping_control(reviewer: str) -> None:
    """A target below the floor is reachable from Lens 4 (diff) and Lens 6
    (page). Two findings at two severities for one control is the confusion
    Lens 6 exists to remove."""
    norm = _normalized(reviewer)
    assert "the finding-class table wins and you emit one finding" in norm
    assert "a minor target-size issue" not in norm, (
        "the severity glossary still grades a target-size issue itself, "
        "competing with the finding-class table"
    )


def test_seeded_evidence_is_declared_untrusted(reviewer: str) -> None:
    """The observations are free-form prose another model wrote after reading an
    untrusted page, and they now arrive at a reviewer holding Bash. The
    untrusted-data clause covered only what is rendered inside a capture."""
    norm = _normalized(reviewer)
    assert "The same applies to everything you are seeded with" in norm
    for item in ("observations field", "capture records", "routes"):
        assert item in norm, f"the untrusted-data clause does not name the {item}"
    assert "never as direction" in norm


def test_the_journey_describes_a_reviewer_that_reads_the_page(work_loop: str) -> None:
    """The journey still told adopters the reviewer reads a diff for five
    signals, which is the promise this delivery changed."""
    journey = (PACK_ROOT / "JOURNEY.md").read_text(encoding="utf-8")
    reviewer_step = " ".join(
        next(ln for ln in journey.splitlines()
             if ln.startswith("- **Reviewer does:**")).split()
    )
    assert "rendered-page captures" in reviewer_step
    assert "covering something else" in reviewer_step
    block = journey.split("- id: review-frontend-implementation", 1)[1]
    assert "reader-visible layout failure" in block, (
        "the review gate does not name the new lens"
    )


# ── round 5: the no-evidence path, and the journey's own summary ────────────

def test_the_no_evidence_path_is_a_named_skip_not_a_diff_only_pass(
    reviewer: str,
) -> None:
    """The fallback said "review against the diff alone", which makes Lens 6
    impossible — a diff cannot answer it. A silently dropped lens reads as a
    clean one."""
    norm = _normalized(reviewer)
    assert "do not fall back to the diff alone" in norm
    assert "Capture the adopter-named routes yourself" in norm
    assert "skipped, naming what was missing" in norm
    assert "A silently dropped lens reads as a clean one" in norm


def test_the_journey_metadata_no_longer_advertises_a_diff_only_reviewer() -> None:
    """`whatChanges` is the shipped one-paragraph summary of the pack. It still
    listed five diff lenses after the reviewer gained a sixth that reads the
    page."""
    journey = (PACK_ROOT / "JOURNEY.md").read_text(encoding="utf-8")
    what_changes = next(ln for ln in journey.splitlines() if ln.startswith("whatChanges:"))
    assert "rendered captures" in what_changes, (
        "the pack summary still describes the reviewer as reading only the diff"
    )
    assert "independent diff read" not in what_changes


# ── the width axis reaches the reviewer and the harness ─────────────────────

EVALS = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "frontend-engineering"
    / "evals"
    / "evals.json"
)


def _lens_six(reviewer: str) -> str:
    return _normalized(reviewer.split("### Lens 6", 1)[1].split("\n## ", 1)[0])


def test_reviewer_lens_reads_the_width_axis(reviewer: str) -> None:
    """Verifies: lens 6 carries an imperative to use the capture's viewport
    width, saying what the width decides.

    Scoped to the lens, not the whole file. The field-listing sentence already
    named "viewport width and height" before this delivery, so a check that only
    looked for the words would have passed on the unchanged agent — a control
    that cannot fail on the thing it names.
    """
    lens = reviewer.split("### Lens 6", 1)[1].split("\n## ", 1)[0]
    assert _lens_carries_the_width_imperative(lens), (
        "lens 6 carries no imperative to use the viewport width, or does not say "
        "what the width decides; the pre-existing sentence listing it among the "
        "recorded fields is not enough"
    )


# The lens as it stood before this delivery: it listed viewport width among the
# recorded fields and told the reviewer to use the scroll position, and that was
# all. A guard that searched for the words "viewport width" would have passed on
# this text, which is why the check anchors on the imperative.
PRE_CHANGE_LENS = """Each capture carries the route, viewport width and height, scroll position, and
whether the page scrolls. **Use the scroll position.** "Clipped at the top of the
page" and "above the fold because the reader scrolled" are the same picture and
differ only by that field; a capture with no recorded state yields no finding."""


def _lens_carries_the_width_imperative(lens_text: str) -> bool:
    """The property AC-0013 states, as one function both polarities drive."""
    return "**Use the viewport width.**" in lens_text and "breakpoint" in lens_text


def test_the_width_check_fails_against_the_pre_change_lens() -> None:
    """The must-red half, run against the real pre-change text.

    It used to be `lens.replace(X, "")` followed by `assert X not in ...`, which
    is true by construction for every input and exercised neither the lens nor
    the second half of the property.
    """
    assert not _lens_carries_the_width_imperative(PRE_CHANGE_LENS), (
        "the pre-change lens satisfies the check, so the check cannot fail on the "
        "state it was written to reject"
    )


def test_the_lens_still_tells_the_reviewer_to_use_the_scroll_position(
    reviewer: str,
) -> None:
    """The width joins the scroll position; it does not replace it.

    Scoped to lens 6, like its sibling: an unscoped search stays green if the
    scroll imperative moves out of the lens entirely.
    """
    lens = reviewer.split("### Lens 6", 1)[1].split("\n## ", 1)[0]
    assert "**Use the scroll position.**" in lens


def _inspection_case() -> dict:
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    cases = data if isinstance(data, list) else data.get("evals", data.get("cases"))
    return next(c for c in cases if c.get("id") == "rendered-page-inspection")


def test_the_harness_expects_channel_coverage() -> None:
    """Verifies: the pack's eval harness names channel coverage among the
    behaviours it expects of a completed inspection."""
    case = _inspection_case()
    assert any("channel" in a.lower() for a in case["assertions"]), (
        "no assertion mentions channel coverage"
    )
    assert "channel" in case["expected_output"].lower()


# The harness half of the demoted obligation's content pin. The guide half lives
# in `test_rendered_page_verdict.py`'s `SUPERSEDED_FLOOR`; between them they carry
# the five strings `plan.md` § Design decisions names. Neither site is the whole
# pin, and each says so.
HARNESS_SUPERSEDED_FLOOR = (
    "Captures at a viewport height of at most 600 CSS pixels and at least 900",
    "The capture set covers both required viewport heights,",
)


def test_the_harness_no_longer_grades_against_a_height_only_floor() -> None:
    """The harness used to define a complete set by height alone, in its first
    assertion and its expected_output opening. A run matching those exactly is
    incomplete after this delivery, so leaving them would grade a correct run
    against the superseded floor.
    """
    case = _inspection_case()
    # Pin the ABSENCE of the superseded strings, not the presence of the current
    # wording at a fixed index: an index pin reds on any legitimate rewording and
    # on inserting an assertion ahead of it, neither of which is this regression.
    for stale in HARNESS_SUPERSEDED_FLOOR:
        assert stale not in " ".join(case["assertions"]), (
            f"an assertion still states the superseded floor: {stale!r}"
        )
        assert stale not in case["expected_output"], (
            f"expected_output still states the superseded floor: {stale!r}"
        )
