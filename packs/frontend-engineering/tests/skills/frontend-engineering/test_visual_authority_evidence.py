"""The manifest records which authority was used, and a reviewer can test it.

Recording the authority is what makes the claim falsifiable afterwards. Lens 7
is what actually falsifies it.
"""

from __future__ import annotations

from frontend_engineering_rendered_page_rules import manifest_fields
from frontend_engineering_visual_authority_rules import (
    PACK_ROOT,
    REVIEWER,
    SKILL,
    read,
    section,
)

FE_STATUS = PACK_ROOT / ".apm" / "skills" / "fe-status" / "SKILL.md"
RUNGS = (
    "approved-visual-target",
    "direction-and-taxonomy",
    "incumbent-system",
    "local-premise",
)


def test_the_manifest_records_which_authority_was_used() -> None:
    """The shipped field-count test derives the heading from this table, so it
    supplies the coherence consequence and nothing here repeats it."""
    fields = manifest_fields(read(SKILL))
    assert "visual authority" in fields, (
        f"the manifest cannot say which authority was used; it carries {fields}"
    )


def test_the_authority_field_names_the_rungs_it_may_record() -> None:
    """A field that accepts any prose records nothing a reviewer can test."""
    row = next(
        (line for line in read(SKILL).splitlines()
         if line.strip().startswith("| visual authority |")),
        None,
    )
    assert row is not None, (
        "the evidence manifest has no '| visual authority |' row; the field "
        "the reviewer's Lens 7 tests is the one that went missing"
    )
    missing = [rung for rung in RUNGS if rung not in row]
    assert not missing, f"the field names no vocabulary for {missing}"
    # The top rung binds composition only, so whenever it resolves two rungs
    # are in force by construction and the field must have room for both. A
    # single-value field leaves the values-rung unrecorded, and Lens 7 then
    # tests a claim the record never had space to make.
    lowered = row.lower()
    assert "composition" in lowered and "values" in lowered, (
        "the visual authority field records one rung; it must record the rung "
        "that supplied composition and the rung that supplied values"
    )


def test_the_status_skill_agrees_on_the_field_count() -> None:
    """Two always-loaded skills stating different counts ships a contradiction.

    `SKILL.md`'s own "full 12-field contract" is deliberately untouched: that is
    the page/screen contract, a different twelve.
    """
    text = read(FE_STATUS)
    fields = manifest_fields(read(SKILL))
    assert f"{len(fields)}-field record" in text, (
        f"fe-status does not describe the manifest as a {len(fields)}-field record"
    )
    assert "visual authority" in text


def test_the_reviewer_carries_a_visual_authority_lens() -> None:
    assert "### Lens 7 — Visual authority" in read(REVIEWER)


def test_the_visual_authority_lens_is_scoped_by_the_confirmation_rule() -> None:
    """Lens 7 reads the manifest — neither the diff nor the page. The shipped
    confirmation rule only named Lenses 1-5 and Lens 6, so without this a
    seventh lens could land with no scoping and produce nothing, which is the
    exact failure that once disabled Lens 6."""
    scope = section(read(REVIEWER), "Each finding must be confirmed", "### Lens 1")
    assert "Lens 7" in scope, "the per-lens confirmation rule does not mention Lens 7"
    assert "manifest" in scope.lower(), "it does not say what Lens 7 reads"
    assert "diff-confirmation" in scope, "it does not say why Lens 7 is exempt"


def test_the_lens_tests_claims_rather_than_scoring_taste() -> None:
    lens = section(read(REVIEWER), "### Lens 7", "\n## ").lower()
    assert "visual authority" in lens
    # Narrowed to the one disclaimer the lens must carry. The earlier version
    # also pinned bare tokens like "parallel", which any sentence containing
    # the word satisfies, and reds on a harmless rewording of the flag list —
    # brittle and weak at once, and no criterion asks for it.
    assert "do not score aesthetics" in lens, (
        "Lens 7 does not disclaim aesthetic scoring, which is the boundary "
        "that keeps it from becoming a taste review"
    )


def test_the_routing_description_advertises_the_new_lens() -> None:
    """The description is the shipped routing surface. Left stale it keeps
    advertising the old lens list to whatever selects this reviewer."""
    line = next(
        (entry for entry in read(REVIEWER).splitlines()
         if entry.startswith("description:")),
        None,
    )
    assert line is not None, "frontend-reviewer.md has no description frontmatter"
    assert "visual-authority" in line or "visual authority" in line
    assert len(line) <= 1024 + len("description: ")


def test_the_manifest_lists_each_held_gap_with_its_kind_and_route() -> None:
    """A held upstream gap is recorded with its axes, operation kind and route,
    so a reviewer sees the hold rather than an absence."""
    row = next(
        line for line in read(SKILL).splitlines() if line.strip().startswith("| visual authority |")
    )
    assert "every upstream gap held" in row
    for part in ("axes", "fixed operation kind", "route class only"):
        assert part in row, part
    # The route is a class, never the recorded owner or operation itself.
    assert "never into the manifest" in row
    assert "reached List" not in row
