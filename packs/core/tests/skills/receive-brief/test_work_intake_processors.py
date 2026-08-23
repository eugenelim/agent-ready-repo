"""Construction tests for work-intake processor boundaries."""

from pathlib import Path

_SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"
_BODIES = {
    "author-brief": (_SKILLS / "author-brief" / "SKILL.md").read_text(encoding="utf-8"),
    "receive-brief": (_SKILLS / "receive-brief" / "SKILL.md").read_text(encoding="utf-8"),
    "new-spec": (_SKILLS / "new-spec" / "SKILL.md").read_text(encoding="utf-8"),
}


def test_ready_brief_without_specs() -> None:
    body = " ".join(_BODIES["receive-brief"].split())
    assert "A Ready brief with zero specs is valid and non-dispatchable." in body
    assert "Spec map" in body
    assert "may contain zero slices" in body


def test_ready_has_one_canonical_six_field_semantic_gate() -> None:
    body = _BODIES["receive-brief"]
    gate = body.split("**Canonical Ready gate**", 1)[1].split("**Write sequence**", 1)[0]
    normalized_gate = " ".join(gate.split())

    for field in (
        "**Outcome**",
        "**In scope**",
        "**Non-goals**",
        "**Constraints or appetite**",
        "**Named assumptions or risks**",
        "**Durable source provenance**",
    ):
        assert field in gate
    assert "Spec map section" not in gate
    assert "exactly these semantic fields" in normalized_gate

    trailing = body.split("## DoR gate", 1)[1]
    assert "defined only in step 4" in trailing
    assert "**Outcome**" not in trailing


def test_spec_and_plan_descriptions_and_warranted_spec_invocation() -> None:
    receive_brief = " ".join(_BODIES["receive-brief"].split())
    new_spec = " ".join(_BODIES["new-spec"].split())

    assert "a spec is the durable behavior contract for one delivery slice; and the plan is the implementation and verification strategy." in receive_brief
    assert "Even a one-day feature benefits" not in new_spec
    for condition in (
        "The user explicitly requests a spec.",
        "Full mode or durable coordination requires one.",
        "A confirmed brief slice is selected for delivery.",
        "The work needs queueing, resumption, approval persistence, or external orchestration.",
        "A durable published behavior contract is warranted.",
    ):
        assert condition in new_spec


def test_template_matches_the_ready_gate_without_a_mandatory_rabbit_hole() -> None:
    template = " ".join(
        (
            _SKILLS.parent.parent
            / "seeds"
            / "docs"
            / "product"
            / "briefs"
            / "_template.md"
        ).read_text(encoding="utf-8").split()
    )

    for heading in (
        "**Source / provenance:**",
        "## Outcome",
        "## Scope / Non-goals",
        "## Constraints / Appetite",
        "## Assumptions / Risks",
        "## Ready gaps (Draft only)",
        "## Spec map",
    ):
        assert heading in template
    for optional_heading in (
        "## Success metrics (optional)",
        "## Instrumentation (optional)",
        "## User stories (optional)",
        "## Design artifacts (optional)",
    ):
        assert optional_heading in template
    assert "At least one entry is required for the DoR gate" not in template
    assert "## Rabbit holes (optional)" in template


def test_only_confirmed_slices_materialize() -> None:
    body = _BODIES["receive-brief"]
    assert "confirmed slice" in body
    assert "new-spec" in body
    assert "ask" in body.lower() or "confirm" in body.lower()


def test_processor_boundary_metadata() -> None:
    for name in ("author-brief", "receive-brief", "new-spec"):
        body = _BODIES[name]
        assert "metadata:" in body, name
        assert "boundaries:" in body, name
        assert "allowed-tools:" in body, name
