"""The manifest records which authority was used, and a reviewer can test it.

Recording the authority is what makes the claim falsifiable afterwards. Lens 7
is what actually falsifies it.
"""

from __future__ import annotations

from frontend_engineering_rendered_page_rules import manifest_fields
from frontend_engineering_visual_authority_rules import PACK_ROOT, REVIEWER, SKILL

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
    fields = manifest_fields(SKILL.read_text(encoding="utf-8"))
    assert "visual authority" in fields, (
        f"the manifest cannot say which authority was used; it carries {fields}"
    )


def test_the_authority_field_names_the_rungs_it_may_record() -> None:
    """A field that accepts any prose records nothing a reviewer can test."""
    row = next(
        line for line in SKILL.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("| visual authority |")
    )
    missing = [rung for rung in RUNGS if rung not in row]
    assert not missing, f"the field names no vocabulary for {missing}"


def test_the_status_skill_agrees_on_the_field_count() -> None:
    """Two always-loaded skills stating different counts ships a contradiction.

    `SKILL.md`'s own "full 12-field contract" is deliberately untouched: that is
    the page/screen contract, a different twelve.
    """
    text = FE_STATUS.read_text(encoding="utf-8")
    fields = manifest_fields(SKILL.read_text(encoding="utf-8"))
    assert f"{len(fields)}-field record" in text, (
        f"fe-status does not describe the manifest as a {len(fields)}-field record"
    )
    assert "visual authority" in text


def test_the_reviewer_carries_a_visual_authority_lens() -> None:
    assert "### Lens 7 — Visual authority" in REVIEWER.read_text(encoding="utf-8")


def test_the_visual_authority_lens_is_scoped_by_the_confirmation_rule() -> None:
    """Lens 7 reads the manifest — neither the diff nor the page. The shipped
    confirmation rule only named Lenses 1-5 and Lens 6, so without this a
    seventh lens could land with no scoping and produce nothing, which is the
    exact failure that once disabled Lens 6."""
    text = REVIEWER.read_text(encoding="utf-8")
    scope = text.split("Each finding must be confirmed", 1)[1].split("### Lens 1", 1)[0]
    assert "Lens 7" in scope, "the per-lens confirmation rule does not mention Lens 7"
    assert "manifest" in scope.lower(), "it does not say what Lens 7 reads"
    assert "diff-confirmation" in scope, "it does not say why Lens 7 is exempt"


def test_the_lens_tests_claims_rather_than_scoring_taste() -> None:
    lens = REVIEWER.read_text(encoding="utf-8").split("### Lens 7", 1)[1].split("\n## ", 1)[0]
    lowered = lens.lower()
    assert "visual authority" in lowered
    assert "do not score aesthetics" in lowered, (
        "the lens does not disclaim aesthetic scoring, which is how it turns "
        "into a taste review"
    )
    for signal in ("no capture", "parallel", "absent"):
        assert signal in lowered, f"the lens does not flag the {signal!r} case"


def test_the_routing_description_advertises_the_new_lens() -> None:
    """The description is the shipped routing surface. Left stale it keeps
    advertising the old lens list to whatever selects this reviewer."""
    line = next(
        entry for entry in REVIEWER.read_text(encoding="utf-8").splitlines()
        if entry.startswith("description:")
    )
    assert "visual-authority" in line or "visual authority" in line
    assert len(line) <= 1024 + len("description: ")
