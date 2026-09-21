"""The system-shape routing axis, and the region that carries it.

The axis is a marker-delimited region inside Stage 0's concept step, read
beside the workload-class axis it sits next to. It is located by HTML-comment
markers, not by a heading or a step number, for the same reason the scope
stage in `test_design_scope_routing.py` is: a positional delimiter moves
whenever the procedure is renumbered, and every assertion then runs against
the wrong span instead of failing.

The five content assertions read the sliced region only, and `_region()`
refuses a file missing either marker rather than widening. The two that
discharge AC-0089 read the whole file by design: counting occurrences is what
detects a duplicated marker, which a slice cannot see. A
whole-file search is what would let the region be deleted while prose
elsewhere kept the check green — the ordering and single-occurrence
assertions are what make the rest mean anything: without them, a second
region could satisfy the text checks while the routed one was gone.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "architect-design" / "SKILL.md"

SCOPE_END = "<!-- scope-determination:end -->"
TEMPLATE_SELECTION = "<!-- template-selection:start"
EVALS = PACK_ROOT / ".apm" / "skills" / "architect-design" / "evals" / "evals.json"
# AC-0090 names the source tree; the skill descends the projected copy. Both
# are checked, because each alone has a blind spot: source only passes on a
# path the agent cannot open, and projection only passes when the source
# concept is deleted and the projection lags.
CONCEPTS = PACK_ROOT / "okf" / "architecture-lenses" / "concepts"
PROJECTED = (
    PACK_ROOT / ".apm" / "skills" / "architecture-lenses-reference"
    / "references" / "okf" / "concepts"
)
SHAPE_START = "<!-- shape-axis:start"
SHAPE_END = "<!-- shape-axis:end -->"
SHAPE_EVAL_ID = 13


def _region() -> str:
    """Return the shape-axis region, whitespace-normalized.

    Slicing between the two shape-axis markers — rather than searching the
    whole file — is what stops the region being deleted while unrelated
    prose keeps a substring check green.

    Both markers are required explicitly. `str.split` on an absent separator
    returns the whole remainder, so slicing alone would silently widen the
    region to end-of-file when only the end marker is deleted, and the five
    content assertions would then pass against the rest of the file. The two
    AC-0089 tests do not call this helper; they read the whole file, because
    counting occurrences is what detects a duplicated marker.
    """
    text = SKILL.read_text(encoding="utf-8")
    if SHAPE_START not in text or SHAPE_END not in text:
        raise AssertionError("shape-axis region is missing a marker")
    after_start = text.split(SHAPE_START, 1)[1]
    # The start marker is an unterminated prefix, so the span after it opens
    # inside the anchor comment. Dropping through that comment's own `-->` is
    # what stops a token written into the anchor discharging a content
    # criterion the region body never states.
    if "-->" not in after_start:
        raise AssertionError("shape-axis start marker is unterminated")
    body = after_start.split("-->", 1)[1].split(SHAPE_END, 1)[0]
    return " ".join(body.split())


# STUB: AC-0089
def test_the_shape_axis_is_anchored_by_one_start_and_one_end_marker() -> None:
    """AC-0089: exactly one of each marker, so a duplicate cannot hide a moved region."""
    text = SKILL.read_text(encoding="utf-8")
    assert text.count(SHAPE_START) == 1
    assert text.count(SHAPE_END) == 1


# STUB: AC-0089
def test_the_shape_axis_sits_between_scope_determination_and_template_selection() -> None:
    """AC-0089: the region opens after scope resolves and closes before the template loads."""
    text = SKILL.read_text(encoding="utf-8")
    scope_end = text.index(SCOPE_END)
    shape_start = text.index(SHAPE_START)
    shape_end = text.index(SHAPE_END)
    template_selection = text.index(TEMPLATE_SELECTION)
    assert scope_end < shape_start, "shape axis opens before scope determination ends"
    assert shape_start < shape_end, "shape-axis end precedes its own start"
    assert shape_end < template_selection, "shape axis closes after template selection begins"


def _shape_concepts(root: Path) -> set[str]:
    """Return the `system-shapes/<name>.md` paths one corpus tree ships."""
    return {
        f"system-shapes/{path.name}"
        for path in (root / "system-shapes").glob("*.md")
        if path.stem != "index"
    }


# STUB: AC-0084
def test_the_shape_axis_cites_the_system_shapes_index_as_its_descent_path() -> None:
    """AC-0084: the axis descends the generated system-shapes index, not a hand-listed set."""
    assert "concepts/system-shapes/index.md" in _region()


# STUB: AC-0085
def test_a_shape_concept_is_selected_only_on_an_open_decision() -> None:
    """AC-0085: the trigger is an open decision of the proposed design, not a vocabulary match."""
    region = _region()
    # The whole clause, because each token alone survives its own negation:
    # "never on an open decision" keeps `open decision`.
    assert "selected only when such an open decision exists" in region
    assert "coordination mechanism" in region


# STUB: AC-0086
def test_several_open_decisions_load_every_matching_shape() -> None:
    """AC-0086: an open decision in each of several shapes loads all of them, not just one."""
    region = _region()
    assert "in each of several shapes loads every one of them" in region


# STUB: AC-0087
def test_a_selected_shape_concept_loads_whole_with_no_tier_selection() -> None:
    """AC-0087: unlike the workload axis beside it, a selected shape has no tier to pick."""
    region = _region()
    # One contiguous phrase, not two tokens. "does not load whole" would drop
    # the `s`, but "no tier selection" survives any negation of the sentence
    # around it, so the two are pinned together as the clause that states the
    # rule.
    assert "loads whole \u2014 no tier selection" in region


# STUB: AC-0088
def test_the_receipt_records_no_shape_lens_selected_when_none_apply() -> None:
    """AC-0088: the working receipt names this outcome when no shape carries an open decision."""
    region = _region()
    # The inversion "never record `no shape lens selected`" keeps the token,
    # so the trigger clause is pinned with it.
    assert "When no shape carries an open decision, record" in region
    assert "`no shape lens selected`" in region


# STUB: AC-0090
def test_the_eval_case_exercises_the_shape_axis() -> None:
    evals = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    by_id = {case["id"]: case for case in evals}
    # By id, not by scanning for a substring: a later case that also names a
    # shape path would silently re-point every assertion below at the wrong
    # case while this one rotted unchecked.
    assert SHAPE_EVAL_ID in by_id, f"eval case {SHAPE_EVAL_ID} is missing"
    expected = by_id[SHAPE_EVAL_ID]["expected_output"]
    assert "shape axis" in expected
    assert "open decision" in expected
    paths = re.findall(r"system-shapes/[\w-]+\.md", expected)
    assert paths, "expected output names no system-shapes concept path"
    # One path that exists, as AC-0090 requires — not every path. The
    # region's own descent path `system-shapes/index.md` matches the pattern
    # and is projection-only, so an expected output naming it beside a real
    # concept still conforms, and requiring all would red that case. The
    # resulting looseness — a hallucinated path beside a real one passes — is
    # recorded in the spec's Testing Strategy.
    #
    # Membership against name sets from constant-anchored globs, never
    # `CONCEPTS / p`: joining a Path to a variable segment is what
    # `tools/lint-pack-test-boundary.py` reads as a pack test reaching above
    # its own pack, and it reds the docs workflow on any `packs/**` change.
    assert set(paths) & _shape_concepts(CONCEPTS), (
        f"no named concept path exists under the source corpus: {sorted(paths)}"
    )
    assert set(paths) & _shape_concepts(PROJECTED), (
        f"no named concept path exists in the projected corpus: {sorted(paths)}"
    )


def test_the_skill_does_not_enumerate_the_shape_names() -> None:
    """The generated index owns the shape list; a second copy in the skill drifts.

    The spec carries this as an Agent Rule and nothing mechanical enforced it,
    so a later edit inlining the six names would pass every other check here.
    Names are read off the corpus rather than listed, so a seventh shape is
    covered the day it ships.
    """
    stems = sorted(
        path.stem
        for path in (CONCEPTS / "system-shapes").glob("*.md")
        if path.stem != "index"
    )
    assert stems, "no shape concepts found; the corpus path is wrong"
    # Stems alone miss the likelier breach: pasting the index's own link
    # titles, none of which contains its stem.
    index = (PROJECTED / "system-shapes" / "index.md").read_text(encoding="utf-8")
    titles = re.findall(r"^- \[([^\]]+)\]", index, re.M)
    assert len(titles) == len(stems), (titles, stems)
    text = SKILL.read_text(encoding="utf-8")
    inlined = [name for name in stems + titles if name in text]
    assert not inlined, f"skill enumerates shape names the index owns: {inlined}"
